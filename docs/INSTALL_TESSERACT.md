# Tesseract OCRのインストール方法

## Windows環境での手順

### 1. Tesseractのインストール

1. **インストーラーをダウンロード**:
   - https://github.com/UB-Mannheim/tesseract/wiki
   - 最新版（例：tesseract-ocr-w64-setup-5.3.3.20231005.exe）をダウンロード

2. **インストール実行**:
   - ダウンロードしたexeファイルを実行
   - **重要**: インストール時に「Additional language data」で **Japanese** を選択

3. **パスを環境変数に追加**:
   ```powershell
   # PowerShellで実行
   setx PATH "$env:PATH;C:\Program Files\Tesseract-OCR"
   ```
   
   または、システム設定で手動追加:
   - `C:\Program Files\Tesseract-OCR` をPATHに追加

4. **確認**:
   ```powershell
   tesseract --version
   ```

### 2. Poppler（PDFから画像変換用）のインストール

1. **Popplerをダウンロード**:
   - https://github.com/oschwartz10612/poppler-windows/releases/
   - 最新版のZIPファイルをダウンロード（例：Release-24.08.0-0.zip）

2. **解凍して配置**:
   - 任意のフォルダに解凍（例：`C:\Program Files\poppler`）

3. **パスを環境変数に追加**:
   ```powershell
   setx PATH "$env:PATH;C:\Program Files\poppler\Library\bin"
   ```

4. **確認**:
   ```powershell
   pdftoppm -v
   ```

### 3. サーバーを再起動

```bash
python start_server.py
```

ログに以下のメッセージが表示されればOCR機能が有効です:
```
INFO:loaders:OCR機能が利用可能です（pytesseract + pdf2image）
```

## トラブルシューティング

### エラー: `TesseractNotFoundError`
- Tesseractがインストールされていないか、PATHが通っていません
- 環境変数PATHに `C:\Program Files\Tesseract-OCR` が含まれているか確認

### エラー: `Unable to get page count`
- Popplerがインストールされていないか、PATHが通っていません
- 環境変数PATHに `C:\Program Files\poppler\Library\bin` が含まれているか確認

### 日本語が認識されない
- Tesseractインストール時に日本語データ（jpn.traineddata）がインストールされているか確認
- `C:\Program Files\Tesseract-OCR\tessdata` に `jpn.traineddata` があるか確認

## 簡易テスト

```powershell
# PowerShellで実行
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
python -c "from pdf2image import convert_from_path; print('pdf2image OK')"
```
