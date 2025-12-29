# qc-structure

**入試問題構造情報ライブラリ** - WordファイルとJSON構造データを統合処理するPythonライブラリ

[![PyPI version](https://badge.fury.io/py/qc-structure.svg)](https://badge.fury.io/py/qc-structure)
[![Python versions](https://img.shields.io/pypi/pyversions/qc-structure.svg)](https://pypi.org/project/qc-structure/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 概要

`qc-structure` は、試験問題などの構造化されたWord文書（`.docx`）を扱うためのPythonライブラリです。

外部の構造定義ファイル（`structure.json`）とWord文書を紐付け、各段落にPID（Paragraph ID）や役割（Role）などのメタデータを付与した「拡張段落オブジェクト」として操作可能にします。

### 主な機能

- Word文書の段落と、別管理の構造情報（JSON）の動的なマッピング
- PIDや階層レベル（`level`）、論理ID（`q1-1` 等）への容易なアクセス
- 表内の段落を含む、文書内の全段落の統一的な反復処理
- Word内部ID（`paraId`、`textId`）を活用した堅牢なアンカリング

## インストール

```bash
pip install qc-structure
```

## 必要要件

- Python 3.7 以上
- python-docx >= 0.8.11

## 基本的な使い方

```python
from qc_structure import load_exam_document

# パス指定
docx_path = "exam.docx"
structure_path = "structure.json"

# ドキュメントのロード
doc = load_exam_document(docx_path, structure_path)

# 段落の処理
for p in doc.paragraphs:
    # EnhancedParagraph のプロパティにアクセス
    pid_str = f"[{p.pid}]" if p.pid else "[----]"
    
    # role や id 情報があれば表示
    info = []
    if p.role: 
        info.append(f"Role={p.role}")
    if p.id:   
        info.append(f"ID={p.id}")
    
    # 元の段落のテキスト (p.text でアクセス可能)
    print(f"{pid_str} {p.text[:20]}... {' '.join(info)}")
    
    # docx.Paragraph の機能もそのまま利用可能
    # if p.style.name == 'Heading 1': ...
```

## データ構造

### structure.jsonの形式

```json
{
  "questions": [
    {
      "id": "q1",
      "role": "大問",
      "start_pid": "p0001",
      "end_pid": "p0037",
      "parent_id": null,
      "level": 0,
      "start_para_id": "1A2B3C4D",
      "start_text_id": "3DA2EBA2",
      "start_text_hash": "58110af8...",
      "header_pid": "p0001",
      "label_text": "1"
    }
  ]
}
```

マッピングは`start_para_id`（Wordの内部ID）をキーとして行われます。これにより、PIDが振り直された場合やテキストが微修正された場合でも、Wordの内部IDが維持されている限り構造とのリンクが保たれます。

## EnhancedParagraph の主なプロパティ

- `pid` (str | None): 段落ID（例: `p0001`）
- `role` (str | None): 役割（例: `大問`、`小問`）
- `id` (str | None): 論理ID（例: `q1`、`q1-1`）
- `level` (int | None): 階層レベル（0=大問、1=小問...）
- `text` (str): 段落のテキスト内容
- `structure` (dict | None): 構造データの生情報

その他多数のプロパティについては、[仕様書](仕様書_qc_core.md)を参照してください。

## ライセンス

MIT License

## 作者

kamarume

## リンク

- [PyPI](https://pypi.org/project/qc-structure/)
- [GitHub](https://github.com/kamarume/qc-structure)
- [ドキュメント](https://github.com/kamarume/qc-structure/blob/main/仕様書_qc_core.md)
