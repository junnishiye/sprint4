"""Fontes portáveis para PDFs gerados com ReportLab.

Prioriza as fontes Vera fornecidas pelo próprio ReportLab (instaladas via pip),
sem depender de caminhos do Linux/Colab nem incluir fontes no repositório.
"""
from pathlib import Path
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def obter_fontes(prefixo="GWF"):
    base = Path(reportlab.__file__).resolve().parent / "fonts"
    regular = base / "Vera.ttf"
    negrito = base / "VeraBd.ttf"
    # A própria biblioteca inclui Vera.ttf/VeraBd.ttf em sua distribuição normal.
    if regular.is_file() and negrito.is_file():
        normal_nome, bold_nome = f"{prefixo}Normal", f"{prefixo}Bold"
        fontes = set(pdfmetrics.getRegisteredFontNames())
        if normal_nome not in fontes:
            pdfmetrics.registerFont(TTFont(normal_nome, str(regular)))
        if bold_nome not in fontes:
            pdfmetrics.registerFont(TTFont(bold_nome, str(negrito)))
        return normal_nome, bold_nome
    # Último recurso sempre presente no ReportLab: não interromper o PDF.
    return "Helvetica", "Helvetica-Bold"
