"""
exam-qc-core: データモデル

EnhancedParagraphクラスを提供します。
"""

from typing import Optional, Dict, Any
from docx.text.paragraph import Paragraph


class EnhancedParagraph:
    """
    python-docxの段落オブジェクトに構造情報を付与したラッパークラス。
    """
    
    def __init__(self, raw_paragraph: Paragraph):
        """
        初期化。
        
        Args:
            raw_paragraph: python-docxのParagraphオブジェクト
        """
        self.raw = raw_paragraph
        self.pid: Optional[str] = None
        self.role: Optional[str] = None
        self.structure: Optional[Dict[str, Any]] = None
    
    @property
    def id(self) -> Optional[str]:
        """
        構造情報からIDを取得する。
        
        Returns:
            構造ID（存在しない場合はNone）
        """
        return self.structure.get('id') if self.structure else None
    
    @property
    def parent_id(self) -> Optional[str]:
        """
        構造情報から親IDを取得する。
        
        Returns:
            親ID（存在しない場合はNone）
        """
        return self.structure.get('parent_id') if self.structure else None
    
    @property
    def level(self) -> Optional[int]:
        """
        構造情報から階層レベルを取得する。
        
        Returns:
            階層レベル（存在しない場合はNone）
        """
        return self.structure.get('level') if self.structure else None
    
    @property
    def start_para_id(self) -> Optional[str]:
        """
        構造情報からWord内部段落ID（アンカー）を取得する。
        
        Returns:
            Word内部段落ID（存在しない場合はNone）
        """
        return self.structure.get('start_para_id') if self.structure else None
    
    @property
    def start_text_id(self) -> Optional[str]:
        """
        構造情報からWord内部テキストID（アンカー）を取得する。
        
        Returns:
            Word内部テキストID（存在しない場合はNone）
        """
        return self.structure.get('start_text_id') if self.structure else None
    
    @property
    def start_text_hash(self) -> Optional[str]:
        """
        構造情報からテキストハッシュ値を取得する。
        
        Returns:
            テキストハッシュ値（存在しない場合はNone）
        """
        return self.structure.get('start_text_hash') if self.structure else None
    
    @property
    def header_pid(self) -> Optional[str]:
        """
        構造情報から見出し段落のPIDを取得する。
        
        Returns:
            見出し段落のPID（存在しない場合はNone）
        """
        return self.structure.get('header_pid') if self.structure else None
    
    @property
    def label_text(self) -> Optional[str]:
        """
        構造情報から見出しの番号ラベルテキストを取得する。
        
        Returns:
            番号ラベルテキスト（例: "1", "(1)", "A"など、存在しない場合はNone）
        """
        return self.structure.get('label_text') if self.structure else None
    
    @property
    def start_pid(self) -> Optional[str]:
        """
        構造情報から開始PIDを取得する。
        
        Returns:
            開始PID（存在しない場合はNone）
        """
        return self.structure.get('start_pid') if self.structure else None
    
    @property
    def end_pid(self) -> Optional[str]:
        """
        構造情報から終了PIDを取得する。
        
        Returns:
            終了PID（存在しない場合はNone）
        """
        return self.structure.get('end_pid') if self.structure else None
    
    def __getattr__(self, name):
        """
        未定義の属性アクセスをrawオブジェクトに委譲する。
        
        Args:
            name: 属性名
            
        Returns:
            rawオブジェクトの該当属性
        """
        return getattr(self.raw, name)
    
    def __str__(self) -> str:
        """
        人間が読みやすい文字列表現を返す。
        
        Returns:
            段落の情報を含む文字列
        """
        text_preview = self.raw.text[:50] + "..." if len(self.raw.text) > 50 else self.raw.text
        parts = [f"PID: {self.pid or 'なし'}"]
        
        if self.role:
            parts.append(f"Role: {self.role}")
        
        if self.id:
            parts.append(f"ID: {self.id}")
        
        if self.parent_id:
            parts.append(f"Parent: {self.parent_id}")
        
        if self.level is not None:
            parts.append(f"Level: {self.level}")
        
        if self.header_pid:
            parts.append(f"Header PID: {self.header_pid}")
        
        if self.label_text:
            parts.append(f"Label: {self.label_text}")
        
        parts.append(f"Text: {text_preview}")
        
        return f"EnhancedParagraph({', '.join(parts)})"
    
    def __repr__(self) -> str:
        """
        デバッグ用の文字列表現を返す。
        
        Returns:
            詳細な情報を含む文字列
        """
        return (
            f"EnhancedParagraph("
            f"pid={self.pid!r}, "
            f"role={self.role!r}, "
            f"id={self.id!r}, "
            f"parent_id={self.parent_id!r}, "
            f"level={self.level!r}, "
            f"text={self.raw.text[:30]!r}..."
            f")"
        )
