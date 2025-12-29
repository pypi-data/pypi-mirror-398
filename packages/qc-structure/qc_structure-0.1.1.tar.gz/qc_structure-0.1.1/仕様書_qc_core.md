
# qc-structure 仕様書

**バージョン**: 0.1.0 (Draft)  
**最終更新ポリシー**: コードの docstring を正とする

## 1. 概要
`qc-structure` は、試験問題などの構造化された Word ドキュメント (`.docx`) を扱うための Python ライブラリです。
外部の構造定義ファイル (`structure.json`) と Word 文書を紐付け、各段落に PID (Paragraph ID) や役割 (Role) などのメタデータを付与した「拡張段落オブジェクト」として操作可能にします。

主な目的:
- Word 文書の段落と、別管理の構造情報 (JSON) の動的なマッピング
- PID や 階層レベル (`level`)、論理 ID (`q1-1` 等) への容易なアクセス
- 表内の段落を含む、文書内の全段落の統一的な反復処理

## 2. モジュール構成

| モジュール | 役割 | 主なクラス・関数 |
| :--- | :--- | :--- |
| `models` | データモデル定義 | `EnhancedParagraph` |
| `core` | コアロジック、ロード処理 | `ExamDocument`, `IDMapper`, `load_exam_document` |
| `utils` | 汎用ユーティリティ | `iter_all_paragraphs`, `get_para_id` |

---

## 3. クラス・関数詳細

### 3.1 models モジュール

#### `class EnhancedParagraph`
`python-docx` の `Paragraph` オブジェクトをラップし、構造情報を付加したクラスです。

**属性:**
- `raw` (`docx.text.paragraph.Paragraph`): 元の段落オブジェクト
- `pid` (`str | None`): 開始 PID (例: `p0001`)
- `role` (`str | None`): 役割 (例: `大問`, `小問`)
- `structure` (`dict | None`): `structure.json` からマッピングされた構造生データ

**プロパティ:**
- `id` (`str | None`): 論理 ID (例: `q1`, `q1-1`)
- `parent_id` (`str | None`): 親の論理 ID
- `level` (`int | None`): 階層レベル (0=大問, 1=小問...)
- `start_pid` (`str | None`): 開始段落ID (例: `p0001`)
- `end_pid` (`str | None`): 終了段落ID (例: `p0037`)
- `start_para_id` (`str | None`): Word内部段落ID（アンカー、例: `3BEAB26A`）
- `start_text_id` (`str | None`): Word内部テキストID（アンカー、例: `3DA2EBA2`）
- `start_text_hash` (`str | None`): テキストハッシュ値（内容変更検出用）
- `header_pid` (`str | None`): 見出し段落のPID (例: `p0001`)
- `label_text` (`str | None`): 見出しの番号ラベル (例: "1", "(1)", "A")

**メソッド:**
- 文字列化 (`str(obj)`): 人間が読みやすい要約を返します。
- `__getattr__`: 未定義の属性アクセスを `raw` (元の段落) に委譲するため、`text` や `style` などの属性に直接アクセス可能です。

---

### 3.2 core モジュール

#### `class IDMapper`
Word 内部の段落 ID (`paraId`) をキーとして、構造情報 (`structure.json`) との紐付けを管理するクラスです。

- **初期化**: `IDMapper(structure_json_path: str)`
- **メソッド**: `get_structure_by_anchor(para_id: str) -> dict`
  - `start_para_id` が一致する構造定義を返します。

#### `class ExamDocument`
Word 文書全体を管理するクラスです。初期化時に全段落をロードし、マッパーを用いて構造情報を結合します。

- **初期化**: `ExamDocument(docx_path: str, mapper: IDMapper)`
- **属性**:
  - `paragraphs` (`List[EnhancedParagraph]`): 構造情報付きの全段落リスト
  - `document` (`docx.Document`): 元の Document オブジェクト
  - `docx_path` (`str`): ファイルパス

#### `function load_exam_document`
ライブラリのエントリーポイントです。

```python
def load_exam_document(docx_path: str, structure_json_path: str) -> ExamDocument:
    ...
```

---

### 3.3 utils モジュール

#### `function iter_all_paragraphs`
Word 文書内のあらゆる場所（本文、表など）にある段落を、出現順（文書構造順）に再帰的に取得するイテレータです。

- **引数**: `document` (`docx.Document`)
- **戻り値**: `Iterator[Tuple[Paragraph, bool]]`
  - `(段落オブジェクト, 表内フラグ)` のタプルを返します。

#### `function get_para_id`
段落の XML から Word 内部 ID (`w14:paraId`) を取得します。

- **引数**: `paragraph` (`docx.text.paragraph.Paragraph`)
- **戻り値**: `str | None`

---

## 4. 使用例

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
    if p.role: info.append(f"Role={p.role}")
    if p.id:   info.append(f"ID={p.id}")
    
    # 元の段落のテキスト (p.text でアクセス可能)
    print(f"{pid_str} {p.text[:20]}... {' '.join(info)}")

    # docx.Paragraph の機能もそのまま利用可能
    # if p.style.name == 'Heading 1': ...
```

## 5. データ構造の前提

### structure.json の形式
本ライブラリは、`structure.json` が以下の形式であることを期待しています（`questions` 配列内に構造オブジェクトがフラットに格納されていること）。

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
    },
    ...
  ]
}
```

マッピングは `start_para_id` (Wordの内部ID) をキーとして行われます。これにより、PIDが振り直された場合やテキストが微修正された場合でも、Wordの内部IDが維持されている限り構造とのリンクが保たれます。
