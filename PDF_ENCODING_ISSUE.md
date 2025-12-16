# 🔍 文字化け問題の診断と対策

## 🐛 現在の状況

**ログから判明した事実:**
```
INFO:app:PDF読み込み成功: アスカデータ.pdf (全体: 1530 文字, 使用: 1530 文字)
INFO:app:PDF内容プレビュー:  ༨നϖʔδ ͕ਓΛҭͯΔ Λશ͏͢Δɻ...  ← 文字化け
INFO:app:メディアコンテキスト長: 1549 文字  ← データは取得できている
INFO:app:回答生成完了: 11 文字  ← 「資料の内容は不明です。」
```

---

## 📋 診断結果

### ✅ 正常に動作している部分
1. PDFファイルのアップロード
2. PDFからのテキスト抽出（1530文字）
3. プロンプト生成（1904文字）
4. LLMへの送信

### ❌ 問題の部分
1. **抽出されたテキストが文字化け**
   - ログ上では `༨നϖʔδ ͕ਓΛҭͯΔ` のように表示
   - これはUnicodeの問題ではなく、**PDFのフォント・エンコーディングの問題**

---

## 🔎 原因の特定

### PDFの種類による問題

| PDFの種類 | 抽出結果 | 対処法 |
|-----------|----------|--------|
| **テキスト埋め込みPDF** | ✅ 正常 | そのまま使用可能 |
| **カスタムフォントPDF** | ⚠️ 文字化け | フォント情報の解析必要 |
| **スキャンPDF（画像）** | ❌ 抽出不可 | OCR必要 |
| **暗号化PDF** | ❌ 読み取り不可 | パスワード解除必要 |

**「アスカデータ.pdf」は「カスタムフォントPDF」の可能性が高い**

---

## 🛠️ 実施した修正

### 1. ログ出力の改善

```python
# ASCII文字のみでプレビュー表示
preview = ''.join(c if ord(c) < 128 else '?' for c in txt[:200])
logger.info(f"PDF内容確認: ASCII変換後={preview}...")
logger.info(f"PDF実際の先頭20文字: {repr(txt[:20])}")
```

### 2. メディアコンテキストの確認

```python
if extra_context:
    context_preview = extra_context[:300].replace('\n', ' ')
    logger.info(f"メディアコンテキスト先頭: {repr(context_preview)}")
```

---

## 🧪 再テスト手順

### ステップ 1: サーバーの自動リロード確認

サーバーが自動的にリロードされているはずです。ログに以下が表示されているか確認：
```
WARNING:  WatchFiles detected changes in 'app.py'. Reloading...
INFO:     Application startup complete.
```

### ステップ 2: もう一度PDFアップロード

1. http://localhost:8080/docs
2. `/ask-with-media` → "Try it out"
3. 同じPDFをアップロード
4. "Execute"

### ステップ 3: 新しいログを確認

**期待されるログ:**
```
INFO:app:PDF読み込み成功: アスカデータ.pdf (全体: 1530 文字, 使用: 1530 文字)
INFO:app:PDF内容確認: ASCII変換後=?????...
INFO:app:PDF実際の先頭20文字: '༨നϖʔδ...'  ← 実際の文字コード
INFO:app:メディアコンテキスト先頭: '[PDF:アスカデータ.pdf]\n༨നϖʔδ...'
```

---

## 🔧 根本的な解決策

### 方法1: PDFの再作成（推奨）

**問題のあるPDFを修正:**
1. 元のWord/PowerPointファイルを開く
2. 「名前を付けて保存」→ PDF
3. **「フォントを埋め込む」オプションを有効化**
4. 保存したPDFを使用

### 方法2: OCR処理の導入

**必要なライブラリ:**
```bash
pip install pytesseract pdf2image
```

**実装例（将来的な改善）:**
```python
from pdf2image import convert_from_path
import pytesseract

def read_pdf_with_ocr(path: str) -> str:
    images = convert_from_path(path)
    texts = []
    for img in images:
        text = pytesseract.image_to_string(img, lang='jpn')
        texts.append(text)
    return "\n".join(texts)
```

### 方法3: 別のPDFライブラリを試す

**pdfplumber（より高度な抽出）:**
```bash
pip install pdfplumber
```

```python
import pdfplumber

def read_pdf_advanced(path: str) -> str:
    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
    return "\n".join(texts)
```

---

## 📝 暫定的な対処法

### テスト用のPDFを作成

**正しく動作するPDFの作成方法:**

1. **Wordで作成**
   ```
   1. Word文書を作成
   2. ファイル → 名前を付けて保存 → PDF
   3. オプション → 「ISO 19005-1に準拠(PDF/A)」をチェック
   4. 保存
   ```

2. **Google Docsで作成**
   ```
   1. Google Docsで文書作成
   2. ファイル → ダウンロード → PDF
   3. 自動的にテキスト埋め込みPDFが作成される
   ```

3. **テキストエディタから**
   ```
   1. テキストファイルを作成
   2. ブラウザで開く
   3. 印刷 → PDFに保存
   ```

---

## 🎯 次のステップ

### 1. 現在のPDFの文字コード確認

ログを確認して、実際に抽出されたテキストを見る：
```
INFO:app:PDF実際の先頭20文字: '...'
INFO:app:メディアコンテキスト先頭: '...'
```

### 2. 文字化けの種類を特定

- 完全に文字化け → PDFのフォント問題
- 一部文字化け → エンコーディング問題
- 全く抽出できない → スキャンPDF

### 3. 対処法の選択

| 状況 | 対処法 |
|------|--------|
| テスト環境のみ | 新しいPDFを作成 |
| 本番環境も対応 | pdfplumber に変更 |
| 画像PDF対応必須 | OCR実装 |

---

## 📊 動作確認用テストPDF

簡単なテストPDFを作成して動作確認：

1. メモ帳を開く
2. 以下を入力：
   ```
   これはテストPDFです。
   
   主な内容：
   1. RAGシステムについて
   2. PDFの読み込みテスト
   3. 文字化け対策の確認
   ```
3. 印刷 → Microsoft Print to PDF
4. `test_simple.pdf` として保存
5. このPDFをアップロードしてテスト

**期待される結果:**
```json
{
  "answer": "このPDFはRAGシステムとPDF読み込みのテストについて説明しています。"
}
```

---

もう一度テストして、新しいログを確認してください 🔍
