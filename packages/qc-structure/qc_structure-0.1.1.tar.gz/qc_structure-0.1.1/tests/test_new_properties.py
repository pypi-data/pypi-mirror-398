"""
exam-qc-core: 新プロパティの動作確認テスト

structure.json内の全フィールドにアクセス可能であることを確認します。
"""

import sys
from pathlib import Path

# 親ディレクトリ（exam_qc_coreのルート）を追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# さらに親（projectsディレクトリ）を追加してexam_qc_coreとしてimport可能にする
sys.path.insert(0, str(project_root.parent))

from exam_qc_core import load_exam_document


def test_new_properties():
    """新しいプロパティのテスト"""
    
    # テストデータのパス（pid_structureプロジェクトの出力を使用）
    docx_path = r"d:\hinsitu_ai\projects\pid_structure\word_files\26-2科学大問題 (1).docx"
    structure_path = r"d:\hinsitu_ai\projects\pid_structure\output_test_new\26-2科学大問題 (1)_structure.json"
    
    print("=== exam-qc-core 新プロパティテスト ===\n")
    
    # ドキュメントロード
    print("ドキュメントをロード中...")
    doc = load_exam_document(docx_path, structure_path)
    print(f"✓ ロード完了: {len(doc.paragraphs)} 段落\n")
    
    # 大問の詳細確認
    print("=== 大問の全プロパティ確認 ===")
    for p in doc.paragraphs:
        if p.role == "大問":
            print(f"PID: {p.pid}")
            print(f"Role: {p.role}")
            print(f"ID: {p.id}")
            print(f"Parent ID: {p.parent_id}")
            print(f"Level: {p.level}")
            print(f"Start PID: {p.start_pid}")
            print(f"End PID: {p.end_pid}")
            print(f"Start Para ID: {p.start_para_id}")
            print(f"Start Text ID: {p.start_text_id}")
            print(f"Start Text Hash: {p.start_text_hash[:20]}..." if p.start_text_hash else "None")
            print(f"Header PID: {p.header_pid}")
            print(f"Label Text: {p.label_text}")
            print(f"Text: {p.text[:50]}...")
            print()
            break
    
    # プロパティアクセスの確認
    print("=== プロパティアクセス確認 ===")
    test_count = 0
    for p in doc.paragraphs:
        if p.structure:
            # 各プロパティがエラーなくアクセス可能であることを確認
            _ = p.id
            _ = p.parent_id
            _ = p.level
            _ = p.start_pid
            _ = p.end_pid
            _ = p.start_para_id
            _ = p.start_text_id
            _ = p.start_text_hash
            _ = p.header_pid
            _ = p.label_text
            test_count += 1
    
    print(f"✓ {test_count} 段落で全プロパティにアクセス成功")
    
    # __str__メソッドの確認
    print("\n=== __str__ メソッド出力例 ===")
    for p in doc.paragraphs:
        if p.role == "セクション":
            print(str(p))
            break
    
    print("\n✅ 新プロパティテスト完了")


if __name__ == "__main__":
    try:
        test_new_properties()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
