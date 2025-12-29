"""
qc-structure: 入試問題構造情報ライブラリ

Wordファイルとstructure.jsonを読み込み、
各段落に構造情報（PID、Role等）を紐付けます。

使用例:
    from qc_structure import load_exam_document
    
    doc = load_exam_document("exam.docx", "exam_structure.json")
    
    for p in doc.paragraphs:
        if p.role == "大問":
            print(f"大問: {p.text[:30]}")
            print(f"  PID: {p.pid}")
            print(f"  番号: {p.structure.get('actual_number')}")
"""

from .core import load_exam_document, ExamDocument
from .models import EnhancedParagraph

__version__ = "0.1.1"

__all__ = ['load_exam_document', 'ExamDocument', 'EnhancedParagraph']
