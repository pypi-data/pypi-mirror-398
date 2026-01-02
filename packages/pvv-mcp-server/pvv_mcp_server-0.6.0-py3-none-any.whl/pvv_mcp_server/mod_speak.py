"""
mod_speak.py
VOICEVOX Web APIを使用して音声合成と再生を行うモジュール
"""

import requests
import sounddevice as sd
import soundfile as sf
import numpy as np
from typing import Optional
import io
import pvv_mcp_server.mod_avatar_manager
import logging
import sys
import re
import time

# ロガーの設定
logger = logging.getLogger(__name__)


def remove_bracket_text(text: str) -> str:
    # 丸括弧の中身を削除（全角・半角の両方対応）
    text = re.sub(r'（.*?）', '', text)  # 全角括弧
    text = re.sub(r'\(.*?\)', '', text)  # 半角括弧
    return text.strip()

def speak(
    style_id: int,
    msg: str,
    speedScale: Optional[float] = 1.0,
    pitchScale: Optional[float] = 0.0,
    intonationScale: Optional[float] = 1.0,
    volumeScale: Optional[float] = 1.0
) -> None:
    """
    VOICEVOX Web APIで音声合成し、音声を再生する
    
    Args:
        style_id: voicevox 発話音声を指定するID(必須)
        msg: 発話するメッセージ(必須)
        speedScale: 話速。デフォルト 1.0(0.5 で半分の速さ、2.0 で倍速)
        pitchScale: 声の高さ(ピッチ)。デフォルト 0.0(正規値)。±0.5 程度で自然
        intonationScale: 抑揚(イントネーション)の強さ。デフォルト 1.0
        volumeScale: 音量。デフォルト 1.0
    
    Raises:
        requests.exceptions.RequestException: API通信エラー
        Exception: 音声再生エラー
    """

    # VOICEVOX APIのエンドポイント
    BASE_URL = "http://127.0.0.1:50021"

    try:
        # 1. 音声合成用のクエリを生成
        query_params = {
            "text": remove_bracket_text(msg),
            "speaker": style_id
        }
        
        query_response = requests.post(
            f"{BASE_URL}/audio_query",
            params=query_params
        )
        query_response.raise_for_status()
        query_data = query_response.json()
        
        # 2. クエリのパラメータを調整
        query_data["speedScale"] = speedScale
        query_data["pitchScale"] = pitchScale
        query_data["intonationScale"] = intonationScale
        query_data["volumeScale"] = volumeScale

        # 3. 音声合成を実行
        synthesis_params = {
            "speaker": style_id
        }
        
        synthesis_response = requests.post(
            f"{BASE_URL}/synthesis",
            params=synthesis_params,
            json=query_data
        )
        synthesis_response.raise_for_status()
        
    except Exception as e:
        raise Exception(f"VOICEVOX API通信エラー: {e}")

    try:
        pvv_mcp_server.mod_avatar_manager.set_anime_type(style_id, "口パク")
        audio_data, samplerate = sf.read(io.BytesIO(synthesis_response.content), dtype='float32', always_2d=True)
        with sd.OutputStream(samplerate=samplerate, channels=audio_data.shape[1], dtype='float32') as stream:
            stream.write(audio_data)

    except Exception as e:
        raise Exception(f"音声再生エラー: {e}")

    finally:
        pvv_mcp_server.mod_avatar_manager.set_anime_type(style_id, "立ち絵")
