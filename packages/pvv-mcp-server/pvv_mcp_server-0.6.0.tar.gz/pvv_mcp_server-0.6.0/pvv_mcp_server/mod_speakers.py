"""
mod_speakers.py
VOICEVOX APIから話者一覧を取得する
"""
import requests
from typing import List, Dict, Any
import logging
import sys
import json

# ロガーの設定
logger = logging.getLogger(__name__)

_speakers_cache = None

# VOICEVOX APIのベースURL
VOICEVOX_URL = "http://localhost:50021"


#def speakers() -> List[Dict[str, Any]]:
def speakers():
    """
    VOICEVOX APIから話者一覧を取得する
    
    Returns:
        話者情報のリスト
        各話者は以下の情報を含む:
        - name: 話者名
        - speaker_uuid: 話者のUUID
        - styles: スタイル情報のリスト（各スタイルにはnameとidが含まれる）
    
    Raises:
        requests.exceptions.RequestException: API呼び出しに失敗した場合
    """
    global _speakers_cache

    if _speakers_cache:
        logger.info(f"return _speakers_cache.")
        return _speakers_cache

    logger.info(f"get speakers from voicevox.")
    endpoint = f"{VOICEVOX_URL}/speakers"
    
    response = requests.get(endpoint)
    response.raise_for_status()
    logger.info(f"encoding : {response.encoding}")
    logger.info(f"headers : {response.headers}")
    logger.info(f"content : {response.content[:100]}")
    logger.info(f"text : {response.text[:200]}")

    #_speakers_cache = json.loads(response.content.decode("utf-8"))
    _speakers_cache = response.content
    #response.encoding = "utf-8"
    #_speakers_cache = response.json()
    return _speakers_cache


if __name__ == "__main__":
    ret = speakers()
    ret = speakers()
    print(ret)

