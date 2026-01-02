# mod_emotion.py

import requests
import sounddevice as sd
import soundfile as sf
import numpy as np
import io
import re
import time

import pvv_mcp_server.mod_avatar_manager
import logging
import sys

# ロガーの設定
logger = logging.getLogger(__name__)


def emotion(style_id: int, emotion: str) -> None:
    """
    アバターに感情表現をさせるツール。
    
    Args:
        style_id: voicevox 発話音声を指定するID(必須)
        emotion: 感情の種類を指定します。(必須)
                 以下のいずれかを指定してください。立ち絵は、平常状態です。
                 ["えがお", "びっくり", "がーん", "いかり"]
    
    Returns:
        None

    """

    try:
        logger.info(f"emotion called. {style_id}, {emotion}")
        pvv_mcp_server.mod_avatar_manager.set_anime_type(style_id, emotion)
        time.sleep(0.1)

    except Exception as e:
        logger.warning(f"emotion error {e}")
        raise Exception(f"emotion error {e}")

    finally:
        logger.info("emotion_metan_aska finalize")
        #pvv_mcp_server.mod_avatar_manager.set_anime_type(style_id, "立ち絵")
