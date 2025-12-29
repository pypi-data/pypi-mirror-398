"""
exam-qc-core: 基本動作確認テスト

実際のWordファイルとstructure.jsonを使って、
構造情報のマッピングが正しく動作するかを確認します。
"""

import sys
from pathlib import Path

# 親ディレクトリ（exam_qc_coreのルート）を追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# さらに親（projectsディレクトリ）を追加してexam_qc_coreとしてimport可能にする
sys.path.insert(0, str(project_root.parent))

import exam_qc_core
from exam_qc_core import load_exam_document


def test_basic_loading():
    """基本的なロード機能のテスト"""
    
    # テストデータのパス（pid_structureプロジェクトの出力を使用）
    docx_path = r"d:\hinsitu_ai\projects\pid_structure\word_files\26-2科学大問題 (1).docx"
    structure_path = r"d:\hinsitu_ai\projects\pid_structure\output_test_new\26-2科学大問題 (1)_structure.json"
    
    print("=== exam-qc-core 基本動作テスト ===\n")
    print(f"Wordファイル: {docx_path}")
    print(f"構造ファイル: {structure_path}\n")
    
    # ドキュメントロード
    print("ドキュメントをロード中...")
    doc = load_exam_document(docx_path, structure_path)
    print(f"✓ ロード完了: {len(doc.paragraphs)} 段落\n")
    
    # マッピング結果の確認
    print("=== マッピング結果 ===")
    mapped_count = 0
    role_stats = {}
    
    for p in doc.paragraphs:
        if p.role:
            mapped_count += 1
            role_stats[p.role] = role_stats.get(p.role, 0) + 1
    
    print(f"マッピング済み段落: {mapped_count}/{len(doc.paragraphs)}")
    print(f"\n役割別統計:")
    for role, count in sorted(role_stats.items()):
        print(f"  {role}: {count}件")
    
    # サンプル段落の詳細表示
    print(f"\n=== サンプル: 大問の詳細 ===")
    for p in doc.paragraphs:
        if p.role == "大問":
            print(f"PID: {p.pid}")
            print(f"Role: {p.role}")
            print(f"Text: {p.text[:50]}...")
            print(f"Structure ID: {p.structure.get('id') if p.structure else 'N/A'}")
            print(f"Anchor ID: {p.structure.get('start_para_id') if p.structure else 'N/A'}")
            print()
            break  # 最初の大問のみ表示
    
    print("✅ 基本動作テスト完了")


if __name__ == "__main__":
    try:
        test_basic_loading()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
