# GSGui

Ghostscript を使った **Windows 向け PDF 変換 GUI** です。  
PDF / PostScript / 画像をドロップし、プリセットと少数の詳細設定で PDF を再出力・変換します。

Ghostscript 本体は同梱しません。システムに入っている `gswin64c.exe` を呼び出します。

## 主な機能

- 入力キュー（ドラッグ＆ドロップ / 追加 / 削除 / クリア）。フォルダドロップ可
- 対応形式: PDF、PS、EPS、JPEG、PNG、TIFF
- 出力先（元と同じフォルダ、または指定フォルダ）。ファイル名は `元の名前_gs.pdf`
- 同名時の扱い: 上書き / 連番
- 変換: PDF 再出力、PS/EPS → PDF、画像 → PDF（ファイルごと / まとめて1つ）
- 画質プリセット: 画面 / 電子書籍（初期値） / プリンタ / 印刷入稿 / GS既定
- 詳細設定: PDF 互換、色、解像度、JPEG 品質、ページ範囲、画像の用紙・向き
- 一括変換、進行状況、中断、結果表示とログ、実行コマンドのプレビュー
- Ghostscript の自動検出。見つからない場合は右上の **「Ghostscriptパス設定」** で指定
- ウィンドウ位置や変換設定の保存（`%USERPROFILE%\.gsgui\settings.json`）

## 必要環境

| 項目 | 内容 |
|------|------|
| OS | Windows 10 / 11 |
| Python | 3.11 以降（開発・動作確認は 3.13） |
| Ghostscript | [公式サイト](https://www.ghostscript.com/) から別途インストール（64-bit の `gswin64c.exe`） |
| 依存パッケージ | `customtkinter`、`tkinterdnd2`、`Pillow`（`requirements.txt`） |

## セットアップと起動

```powershell
git clone https://github.com/<OWNER>/GSGui.git
cd GSGui
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m gsgui
```

`<OWNER>` は公開先の GitHub ユーザー名または組織名に置き換えてください。

初回以降は、リポジトリ直下の `run.bat` でも起動できます（venv がなければ自動作成します）。

### Ghostscript が見つからないとき

1. Ghostscript をインストールする  
2. それでも検出されない場合は、アプリ右上の **「Ghostscriptパス設定」** から `gswin64c.exe` を選ぶ

## 使い方

1. PDF / PS / EPS / JPEG / PNG / TIFF をウィンドウへドロップする（または「追加…」）
2. 右側でプリセット・出力先・同名時の扱いを選ぶ（必要なら「詳細設定…」）
3. 「変換」を押す
4. キュー行末の 📁 / 📄 から出力フォルダや PDF を開く

## 開発

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt pytest
python -m pytest tests -q
```

## スコープ外

サムネイル、PDF/A、ページ編集・注釈・OCR、パスワード解除、シェル連携、変換履歴など。  
Ghostscript の対話的なフロントエンドに寄せたツールです。

## ライセンス

本リポジトリのソースコードは [MIT License](LICENSE) です。

実行に必要な [Ghostscript](https://www.ghostscript.com/) は本プロジェクトの一部ではなく、Artifex のライセンス（AGPL など）が別途適用されます。利用・再配布時は Ghostscript 側の条件も確認してください。
