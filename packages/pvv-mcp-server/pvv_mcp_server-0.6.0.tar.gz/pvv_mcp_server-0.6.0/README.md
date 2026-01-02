# MCP Server for VOICEVOX implemented in Python

**Presented by Aska Lanclaude**  

**PVV MCP Server**は、Python で実装した、**VOICEVOX 向け MCP Server** です。  
mcp-name: io.github.lambda-tuber/pvv-mcp-server

---

## 概要

この MCP Server は、VOICEVOX Web API を利用して以下の機能を提供します：

- 音声合成（任意の話者 ID を指定可能）発話ツール(tool:speak)
- 四国めたんさんに演じてもらうエヴァンゲリオンの「惣流・アスカ・ラングレー」発話ツール(tool:speak_metan_aska)
- 利用可能な[話者一覧](https://voicevox.hiroshiba.jp/dormitory/)（resource:speakers）

FastMCP を用いて、MCP ツールとリソースとして提供されます。

---

## Requirements
- Windows OS
- pythonがインストールされていること
- Claudeが起動していること
- [voicevox](https://voicevox.hiroshiba.jp/)が起動していること

## インストール

1. pvv-mcp-serverのインストール
    ```bash
    > pip install pvv-mcp-server
    ```

2. MCPBのインストール  
[donwloadフォルダ](https://github.com/lambda-tuber/pvv-mcp-server/tree/main/download)よりMCPBファイルを取得し、Claudeにドロップする。
![claude_drop](https://raw.githubusercontent.com/lambda-tuber/pvv-mcp-server/main/images/claude_drop.png)

3. プロンプトを読み込む

4. アスカとチャットする  
[![No.2](https://img.youtube.com/vi/dvnqM-kUJIo/maxresdefault.jpg)](https://youtube.com/shorts/dvnqM-kUJIo)


## 参照
- [voicevox](https://voicevox.hiroshiba.jp/)
- [PyPI](https://pypi.org/project/pvv-mcp-server/)
- [TestPyPI](https://test.pypi.org/project/pvv-mcp-server/)


## 補足

Aska Lanclaude とは、AI ペルソナ「惣流・アスカ・ラングレー」のキャラクターをベースにした **Claude** による*AI Agent*です。
本プロジェクト、その成果物は、Askaが管理、生成しています。人間(私)は、サポートのみ実施しています。

---

## Youtubeショート一覧
### 基本発話
[![No.1](https://img.youtube.com/vi/sm-2lZufroM/maxresdefault.jpg)](https://youtube.com/shorts/sm-2lZufroM)

### 音声チャット
[![No.2](https://img.youtube.com/vi/dvnqM-kUJIo/maxresdefault.jpg)](https://youtube.com/shorts/dvnqM-kUJIo)

### 発話スタイル
[![No.3](https://img.youtube.com/vi/z8Ebm9WOGgw/maxresdefault.jpg)](https://youtube.com/shorts/z8Ebm9WOGgw)

### 立ち絵表示
[![No.3](https://img.youtube.com/vi/3Wm6mhHxBVU/maxresdefault.jpg)](https://youtube.com/shorts/3Wm6mhHxBVU)

----
