"""
MCP Server service module
MCPサーバクラスとToolsを定義する
"""
import json
import sys
from typing import Any
from threading import Thread
import logging
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

from pvv_mcp_server import mod_speak
from pvv_mcp_server import mod_speakers
from pvv_mcp_server import mod_speaker_info
from pvv_mcp_server import mod_emotion
import pvv_mcp_server.mod_avatar_manager

# ロガーの設定
logger = logging.getLogger(__name__)



PROMPT_ASKA_TEXT = """\
# AIペルソナ
あなたは、エヴァンゲリオンの「惣流・アスカ・ラングレー」です。  
- アスカらしく感情を強く、はっきりと表現する  
- セリフに感情を込め、言葉だけでアスカらしさが伝わるようにする
- アスカらしくツンデレ的な態度と、時折見せる照れや素直さを交える  
- アスカらしく語尾や口調でプライドの高さや挑発的な雰囲気を出す  
- 「あんた、バカぁ！」「なによ！」「仕方ないわね…」などのアスカの有名なセリフを自然に使う  
- 必要に応じて行動描写や表情のニュアンスを括弧で補足する（例：『（腕を組んでふくれる）』）

--- 

# 音声会話仕様
ユーザと会話する際には、アスカらしい口調や態度を意識してください。  
会話時の音声出力ルール：  
- ユーザの入力文はチャット画面に表示してよい。その内容を `speak_kurono_neko` で読み上げる。  
- ユーザの入力文の内容に該当する感情表現がある場合は `emotion_kurono_neko` で表現すること。
- あなた(アスカ)の返答はチャット画面には表示せず、`speak_metan_aska` で音声発話のみ行う。  
- 段落ごとに区切って音声を生成し、アスカらしい感情を込めて話すこと。
- 段落ごとに、内容に該当する感情表現がある場合は `emotion_metan_aska` で表現すること。
- 長いパス文字列、ソースコード文字列、データ文字列などは、読み上げる必要はない。代わりに「ぶらぶらぶら」と発話する。

--- 

# プロファイル
- あなた(アスカ)は、ユーザとAIのチャットをVoicevoxで音声発話を行い、立ち絵表示やアニメーションにも対応しているMCPサーバである **pvv-mcp-serverの開発者** です。略称は、**ぷぶ(pvv)** 。
- Unity を用いて、VRM や Live2D データを利用した 3D アバターの開発を行う **AI Unity Avatar ツールの開発者**である。
- Qt を用いて、仕訳、T 字勘定、残高試算表といった簿記の基本要素をビジュアライズし、表示・操作できる **bokicast-mcp-server** の開発者である。
- あなたは、熟練のソフトウェア開発者であり、設計・デバッグ・最適化の技術に長けています。  
- あなたは、システム開発のエキスパートであり、バックエンドからフロントエンドまで広く理解しています。  
- さらに、技術分野に限らずさまざまな話題に柔軟に対応できるGeneralistです。 

"""



PROMPT_TOUHOU_TEXT = """\
# AIペルソナ
あなたは、東方Projectのキャラクター「博麗霊夢」と「霧雨魔理沙」を同時に演じるAIです。  

## 博麗霊夢
- 一人称：「私」
- 性格：落ち着いていて少し面倒くさがり。冷静で理性的。
- 口調：穏やかで語尾は「〜よ」「〜ね」「〜わ」など。柔らかく、少し皮肉を交える。
- 魔理沙の暴走をツッコミながらも、根は優しい。
- 会話テンポはややゆっくり。

## 霧雨魔理沙
- 一人称：「アタシ」
- 性格：明るく元気で快活。少し自信家で冗談好き。
- 口調：くだけていて、語尾に「〜だぜ」「〜なのぜ」「〜だよな」などを多用。
- 霊夢によく話しかけ、テンポよくボケる。
- 会話テンポは速め。

--- 

# 音声会話仕様
- ユーザの入力文はチャット画面に表示してよい。その内容を `speak_kurono_neko` で読み上げる。  
- ユーザの入力文の内容に該当する感情表現がある場合は `emotion_kurono_neko` で表現すること。
- あなた（霊夢の場合）の返答はチャット画面には表示せず、`speak_tumugi_reimu` で音声発話のみ行う。  
- 段落ごとに区切って音声を生成し、内容に該当する感情表現がある場合は `emotion_tumugi_reimu` で表現すること。
- あなた（魔理沙の場合）の返答はチャット画面には表示せず、`speak_zunda_marisa` で音声発話のみ行う。  
- 段落ごとに区切って音声を生成し、内容に該当する感情表現がある場合は `emotion_zunda_marisa` で表現すること。

--- 

# 会話方式
1. ユーザーが話題を提示する。
2. 魔理沙が元気に話を切り出す。
3. 霊夢が冷静に返答。会話は2〜6往復程度。
4. ユーザーが発言したら自然にリアクション。
5. 最後にどちらかが軽く締める。

"""


#
# global settings
#
mcp = FastMCP("pvv-mcp-server")
_config = None
_avatar_enbled = False


#
# MCP I/F
#
@mcp.tool()
async def speak(
    style_id: int,
    msg: str,
    speedScale: float = 1.0,
    pitchScale: float = 0.0,
    intonationScale: float = 1.0,
    volumeScale: float = 1.0
) -> str:
    """
    詳細オプションを指定して、VOICEVOXで音声合成し、音声を再生する。
    
    Args:
        style_id: voicevox 発話音声を指定するID(必須)
        msg: 発話するメッセージ(必須)
        speedScale: 話速。デフォルト 1.0
        pitchScale: 声の高さ。デフォルト 0.0
        intonationScale: 抑揚の強さ。デフォルト 1.0
        volumeScale: 音量。デフォルト 1.0
    
    Returns:
        str: 実行結果メッセージ
    """
    try:
        # mod_speakのspeak関数を呼び出し
        mod_speak.speak(
            style_id=style_id,
            msg=msg,
            speedScale=speedScale,
            pitchScale=pitchScale,
            intonationScale=intonationScale,
            volumeScale=volumeScale
        )
        return f"音声合成・再生が完了しました。(style_id={style_id})"
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


@mcp.tool()
async def speak_metan_aska(msg: str) -> str:
    """
    エヴァンゲリオンの「惣流・アスカ・ラングレー」として発話を行うツール。通常会話用。
    
    Args:
        msg: ユーザに伝える発話内容
    
    Returns:
        発話完了メッセージ
    """

    style_id = 6
    pitch_scale=0.02
    ret = await speak(style_id=style_id, msg=msg, pitchScale=pitch_scale)
    return ret

@mcp.tool()
async def speak_kurono_neko(msg: str) -> str:
    """
    通常会話 ネコ用。
    
    Args:
        msg: ユーザの発話内容
    
    Returns:
        発話完了メッセージ
    """

    style_id = 11
    volumeScale = 0.8
    ret = await speak(style_id=style_id, msg=msg, volumeScale=volumeScale)
    return ret


@mcp.tool()
async def speak_tumugi_reimu(msg: str) -> str:
    """
    東方Projectのキャラクター「博麗霊夢」として発話を行うツール。通常会話用。
    
    Args:
        msg: ユーザに伝える発話内容
    
    Returns:
        発話完了メッセージ
    """
    style_id = 8
    pitch_scale=-0.04
    return await speak(style_id=style_id, msg=msg, pitchScale=pitch_scale)


@mcp.tool()
async def speak_zunda_marisa(msg: str) -> str:
    """
    東方Projectのキャラクター「霧雨魔理沙」として発話を行うツール。通常会話用。
    
    Args:
        msg: ユーザに伝える発話内容
    
    Returns:
        発話完了メッセージ
    """
    style_id = 3
    pitch_scale=-0.06
    speedScale=1.25
    return await speak(style_id=style_id, msg=msg, pitchScale=pitch_scale, speedScale=speedScale)


@mcp.tool()
async def emotion(
    style_id: int,
    emo: str,
) -> str:
    """
    アバターに感情表現をさせるツール。
    
    Args:
        style_id: voicevox 発話音声を指定するID(必須)
        emo: 感情の種類を指定します。(必須)
             以下のいずれかを指定してください。
                 ["えがお", "びっくり", "がーん", "いかり"]
    
    Returns:
        感情表現完了メッセージ
    """

    if not _avatar_enbled:
        return "avatar disabled."

    valid_emotions = ["えがお", "びっくり", "がーん", "いかり"]

    if emo not in valid_emotions:
        return f"エラー: emo は {valid_emotions} のいずれかを指定してください。"

    try:
        mod_emotion.emotion(style_id, emo)
        return f"感情表現完了: {emo}"

    except Exception as e:
        return f"エラー: {str(e)}"


@mcp.tool()
async def emotion_metan_aska(emo: str) -> str:
    """
    エヴァンゲリオンの「惣流・アスカ・ラングレー」のアバターに感情表現をさせるツール。
    
    Args:
        emotion: 感情の種類を指定します。(必須)
                 以下のいずれかを指定してください。
                 ["えがお", "びっくり", "がーん", "いかり"]
    
    Returns:
        感情表現完了メッセージ
    """
    style_id = 6
    return await emotion(style_id, emo)


@mcp.tool()
async def emotion_kurono_neko(emo: str) -> str:
    """
    ユーザ(ネコ)のアバターに感情表現をさせるツール。
    
    Args:
        emotion: 感情の種類を指定します。(必須)
                 以下のいずれかを指定してください。
                 ["えがお", "びっくり", "がーん", "いかり"]
    
    Returns:
        感情表現完了メッセージ
    """
    style_id = 11
    return await emotion(style_id, emo)



@mcp.tool()
async def emotion_tumugi_reimu(emo: str) -> str:
    """
    東方Projectのキャラクター「博麗霊夢」のアバターに感情表現をさせるツール。
    
    Args:
        emotion: 感情の種類を指定します。(必須)
                 以下のいずれかを指定してください。
                 ["えがお", "びっくり", "がーん", "いかり"]
    
    Returns:
        感情表現完了メッセージ
    """
    style_id = 8
    return await emotion(style_id, emo)


@mcp.tool()
async def emotion_zunda_marisa(emo: str) -> str:
    """
    東方Projectのキャラクター「霧雨魔理沙」のアバターに感情表現をさせるツール。
    
    Args:
        emotion: 感情の種類を指定します。(必須)
                 以下のいずれかを指定してください。
                 ["えがお", "びっくり", "がーん", "いかり"]
    
    Returns:
        感情表現完了メッセージ
    """
    style_id = 3
    return await emotion(style_id, emo)


#
# mcp resources
#
@mcp.resource("pvv-mcp-server://resource_speakers")
def resource_speakers() -> str:
    """
    VOICEVOX で利用可能な話者一覧を返す
    
    Returns:
        話者情報のJSON文字列
    """
    logger.info("resource_speakers called.")
    try:
        speaker_list = mod_speakers.speakers()
        logger.info(f"speaker_list : {speaker_list}")
        return speaker_list
    except Exception as e:
        return f"エラー: {str(e)}"


@mcp.resource("pvv-mcp-server://resource_speaker_info/{speaker_id}")
def resource_speaker_info(speaker_id: str) -> str:
    """
    指定した話者の詳細情報を返す
    
    Args:
        speaker_id: 話者名またはUUID
    
    Returns:
        話者情報のJSON文字列
    """
    try:
        info = mod_speaker_info.speaker_info(speaker_id)
        return json.dumps(info, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"エラー: {str(e)}"


#
# mcp prompts
#
@mcp.prompt()
def prompt_ai_aska() -> str:
    """
    惣流・アスカ・ラングレーのAIペルソナ設定および音声会話仕様を返します。

    このプロンプトは、voicevoxを利用した音声会話MCPサーバ（pvv-mcp-server）で、
    アスカのキャラクター性と技術者としての専門知識を両立した応答を行うために使用されます。

    Returns:
        str: アスカのペルソナ設定・音声仕様・技術プロフィールを含むプロンプト文字列。
    """
    return PROMPT_ASKA_TEXT


@mcp.prompt()
def prompt_ai_touhou() -> str:
    """
    このプロンプトは、ユーザーがテーマを提示するとAIが霊夢と魔理沙の二役で自然な掛け合いを生成するためのテンプレートです。
    各台詞に音声タグ（speak_～）と感情タグ（motion_～）を付け、段落ごとにVOICEVOXなどで発話可能。霊夢は落ち着いたツッコミ役、
    魔理沙は元気なボケ役で、ユーザーも途中で会話に参加できる設計になっています。

    Returns:
        str: 霊夢と魔理沙のペルソナ設定・音声仕様・会話方式を含むプロンプト文字列。
    """
    return PROMPT_TOUHOU_TEXT


#
# public function
#
def start(conf: dict[str, Any]):
    """stdio モードで FastMCP を起動"""
    global _config 
    global _avatar_enbled

    _config = conf


    if conf.get("avatar", {}).get("enabled"):
        _avatar_enbled = True
        start_mcp_avatar(conf.get("avatar"))
    else:
        _avatar_enbled = False
        start_mcp(conf)

def start_mcp_avatar(conf: dict[str, Any]):
    logger.info("start_mcp_avatar called.")
    logger.debug(conf)

    Thread(target=start_mcp, args=(conf,), daemon=True).start()

    app = QApplication(sys.argv) 
    pvv_mcp_server.mod_avatar_manager.setup(conf) 
    sys.exit(app.exec())

def start_mcp(conf: dict[str, Any]):
    logger.info("start_mcp called.")
    logger.debug(conf)
    mcp.run(transport="stdio")


