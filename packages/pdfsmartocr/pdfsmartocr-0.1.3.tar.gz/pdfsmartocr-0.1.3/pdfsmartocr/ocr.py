import os
import time
import tempfile
import multiprocessing as mp
from functools import partial
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader
from typing import Iterable, Union, Optional


pytesseract.pytesseract.tesseract_cmd = r"D:\Program Files\Tesseract-OCR\tesseract.exe"


def converter_pdf_para_imagens(pdf_path, pasta_temp, dpi, fmt="jpeg"):
    imgs = convert_from_path(
        pdf_path,
        dpi=dpi,
        fmt=fmt,
        output_folder=pasta_temp,
        output_file="page",
        paths_only=True
    )
    return imgs


def ocr_tesseract_pagina(img_path, lang="por"):
    try:
        return pytesseract.image_to_string(img_path, lang=lang)
    except Exception as e:
        return f"[ERRO TESSERACT {img_path}] {str(e)}"


def ocr_pdf(
    pdf_path: str,
    n_processos=None,
    dpi: int = 200,
    max_ocr_pages: int = 100
):
    """
    Executa OCR com Tesseract nas primeiras páginas e
    leitura nativa (PdfReader) nas demais.
    """
    if n_processos is None:
        n_processos = mp.cpu_count()

    pasta_temp = tempfile.mkdtemp(prefix="ocr_tess_")
    imagens = converter_pdf_para_imagens(pdf_path, pasta_temp, dpi=dpi)
    total_paginas = len(imagens)

    paginas_para_ocr = imagens[:max_ocr_pages]
    paginas_para_pdfreader = range(max_ocr_pages, total_paginas)

    t0 = time.time()
    with mp.Pool(processes=n_processos) as pool:
        resultados_ocr = pool.map(
            partial(ocr_tesseract_pagina, lang="por"),
            paginas_para_ocr
        )

    resultados_reader = []
    if paginas_para_pdfreader:
        try:
            reader = PdfReader(pdf_path)
            for i in paginas_para_pdfreader:
                try:
                    texto_pagina = reader.pages[i].extract_text()
                    if not texto_pagina:
                        texto_pagina = f"[Página {i+1}] (sem texto detectado)"
                except:
                    texto_pagina = f"[Erro ao ler página {i+1}]"
                resultados_reader.append(texto_pagina)
        except Exception as e:
            resultados_reader.append(f"[ERRO PDF READER] {str(e)}")

    tempo = time.time() - t0

    for f in imagens:
        os.remove(f)
    os.rmdir(pasta_temp)

    texto_final = "\n\n".join(resultados_ocr + resultados_reader)
    return texto_final, tempo




def _parse_paginas(
    paginas: Optional[Union[int, str, Iterable[int]]],
    total_paginas: int,
    one_based: bool = True
) -> list[int]:
    """
    Retorna lista de índices 0-based, ordenada, sem duplicatas, validada.
    Suporta:
      - int (ex: 5)
      - list/iterable de int (ex: [1,3,10])
      - string com intervalos (ex: "1-5, 9, 12-14")
      - None => vazio (nenhuma página)
    """
    if paginas is None:
        return []

    idxs: list[int] = []

    def add_index(i: int):
        j = i - 1 if one_based else i
        if 0 <= j < total_paginas:
            idxs.append(j)

    if isinstance(paginas, int):
        add_index(paginas)

    elif isinstance(paginas, str):
        s = paginas.replace(" ", "")
        if not s:
            return []
        partes = [p for p in s.split(",") if p]
        for p in partes:
            if "-" in p:
                a, b = p.split("-", 1)
                if a.isdigit() and b.isdigit():
                    a_i, b_i = int(a), int(b)
                    if a_i > b_i:
                        a_i, b_i = b_i, a_i
                    for k in range(a_i, b_i + 1):
                        add_index(k)
            else:
                if p.isdigit():
                    add_index(int(p))

    else:
        # iterable de ints
        for x in paginas:
            if isinstance(x, int):
                add_index(x)

    # ordena e remove duplicatas
    idxs = sorted(set(idxs))
    return idxs


def ocr_pdf_paginas(
    pdf_path: str,
    paginas_ocr: Optional[Union[int, str, Iterable[int]]] = None,
    n_processos: Optional[int] = None,
    dpi: int = 200,
    lang: str = "por",
    one_based: bool = True,
    ler_restante_pdfreader: bool = False,
):
    """
    Faz OCR (Tesseract) apenas nas páginas informadas em `paginas_ocr`.
    Opcionalmente, lê o restante via PdfReader.

    Retorna: (texto_final, tempo)
    """
    if n_processos is None:
        n_processos = mp.cpu_count()

    # 1) Converte PDF em imagens (para sabermos total e ter paths)
    pasta_temp = tempfile.mkdtemp(prefix="ocr_tess_")
    imagens = converter_pdf_para_imagens(pdf_path, pasta_temp, dpi=dpi)
    total_paginas = len(imagens)

    paginas_ocr_idx = _parse_paginas(paginas_ocr, total_paginas, one_based=one_based)

    t0 = time.time()

    # 2) OCR somente das páginas selecionadas
    resultados_ocr_por_pagina = {}
    if paginas_ocr_idx:
        imgs_selecionadas = [imagens[i] for i in paginas_ocr_idx]
        with mp.Pool(processes=n_processos) as pool:
            textos = pool.map(partial(ocr_tesseract_pagina, lang=lang), imgs_selecionadas)

        for i, txt in zip(paginas_ocr_idx, textos):
            resultados_ocr_por_pagina[i] = txt
    else:
        # nada selecionado
        resultados_ocr_por_pagina = {}

    # 3) (Opcional) Ler o restante com PdfReader
    resultados_reader_por_pagina = {}
    if ler_restante_pdfreader:
        try:
            reader = PdfReader(pdf_path)
            for i in range(total_paginas):
                if i in resultados_ocr_por_pagina:
                    continue
                try:
                    texto_pagina = reader.pages[i].extract_text()
                    if not texto_pagina:
                        texto_pagina = f"[Página {i+1}] (sem texto detectado)"
                except Exception:
                    texto_pagina = f"[Erro ao ler página {i+1}]"
                resultados_reader_por_pagina[i] = texto_pagina
        except Exception as e:
            # se o reader falhar, registra um erro geral
            resultados_reader_por_pagina[-1] = f"[ERRO PDF READER] {str(e)}"

    tempo = time.time() - t0

    # 4) Limpa arquivos temporários
    for f in imagens:
        try:
            os.remove(f)
        except:
            pass
    try:
        os.rmdir(pasta_temp)
    except:
        pass

    # 5) Monta saída ordenada (por página)
    blocos = []
    for i in range(total_paginas):
        if i in resultados_ocr_por_pagina:
            blocos.append(f"[OCR Página {i+1}]\n{resultados_ocr_por_pagina[i]}")
        elif i in resultados_reader_por_pagina:
            blocos.append(f"[PDFReader Página {i+1}]\n{resultados_reader_por_pagina[i]}")

    # erro geral do reader (chave -1), se existir
    if -1 in resultados_reader_por_pagina:
        blocos.append(resultados_reader_por_pagina[-1])

    texto_final = "\n\n".join(blocos)
    return texto_final, tempo