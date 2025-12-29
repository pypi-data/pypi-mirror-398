"""
exam-qc-core: ユーティリティモジュール

Word文書の段落を再帰的に取得するユニバーサルイテレータなどを提供します。
"""

from typing import Iterator, Tuple
from docx import Document
from docx.text.paragraph import Paragraph
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table


def iter_all_paragraphs(document: Document) -> Iterator[Tuple[Paragraph, bool]]:
    """
    Word文書内の全段落（本文、表内、テキストボックス含む）を出現順に取得する。
    
    Args:
        document: python-docxのDocumentオブジェクト
        
    Yields:
        Tuple[Paragraph, bool]: (段落オブジェクト, 表内フラグ)
    """
    for element in document.element.body:
        if isinstance(element, CT_P):
            # 本文段落
            yield Paragraph(element, document), False
        elif isinstance(element, CT_Tbl):
            # 表内の段落
            table = Table(element, document)
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        yield paragraph, True


def get_para_id(paragraph: Paragraph) -> str:
    """
    段落のWord内部ID (w14:paraId) を取得する。
    
    Args:
        paragraph: 段落オブジェクト
        
    Returns:
        str: paraId（存在しない場合はNone）
    """
    from docx.oxml.ns import qn
    
    if hasattr(paragraph, '_p'):
        return paragraph._p.get(qn('w14:paraId'))
    return None
