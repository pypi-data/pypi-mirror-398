"""
mod_avatar_manager.py
アバター管理モジュール（リファクタリング版）
"""

import json
import sys
import os
import logging
import atexit
import signal
from pathlib import Path
from typing import Any, Dict, Optional
from PySide6.QtCore import QMetaObject, Qt, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG

from pvv_mcp_server.mod_speaker_info import speaker_info
from pvv_mcp_server.avatar.mod_avatar import AvatarWindow

# ロガーの設定
logger = logging.getLogger(__name__)


# グローバル変数
_avatar_global_config: Optional[Dict[str, Any]] = None
_avatars_config: Optional[Dict[int, Any]] = None
_avatar_cache: Dict[int, Any] = {}
_auto_save_timer: Optional[QTimer] = None


# ==================== Public API ====================

def setup(avs: Dict[int, Any]) -> None:
    """
    アバターマネージャーの初期化
    
    Args:
        avs: アバター設定の辞書。全体設定の"avatar"配下。
            - enabled: アバター機能の有効/無効
            - target: アプリケーション名
            - avatars: style_id毎のアバター設定
            - auto_save_interval: 自動保存間隔(ミリ秒)。デフォルト5000(5秒)
    """
    global _avatar_global_config, _avatars_config
    
    _avatar_global_config = avs
    _avatars_config = avs.get("avatars", {})
    
    if _avatar_global_config.get("enabled"):
        logger.info("Avatar enabled. Creating all avatar instances...")
        _create_all_avatars()
        logger.info(f"Created {len(_avatar_cache)} avatar instance(s).")
        
        # 自動保存タイマーの開始
        _start_auto_save_timer()
    else:
        logger.info("Avatar disabled.")


def set_anime_type(style_id: int, anime_type: str) -> None:
    """
    指定されたアバターのアニメーションキーを設定
    
    Args:
        style_id: スタイルID
        anime_type: アニメーションキー（"立ち絵", "口パク"など）
    """
    if not _avatar_global_config or not _avatar_global_config.get("enabled"):
        logger.info("Avatar disabled. Skipping set_anime_type.")
        return
    
    avatar = _get_avatar(style_id)
    if avatar:
        QMetaObject.invokeMethod(avatar, "showWindow", Qt.ConnectionType.QueuedConnection)
        QMetaObject.invokeMethod(avatar, "set_anime_type", Qt.ConnectionType.QueuedConnection, Q_ARG(str, anime_type))
    else:
        logger.warning(f"Avatar not found for style_id={style_id}")


def save_all_configs() -> Dict[str, Any]:
    """
    全アバターの設定を収集して辞書形式で返す
    
    Returns:
        全アバターの設定を含む辞書
    """
    all_configs = {}
    
    for key, avatar in _avatar_cache.items():
        try:
            # AvatarWindowかどうかで分岐
            if isinstance(avatar, AvatarWindow):
                config = avatar.save_config()
                all_configs[key] = config
                logger.info(f"Saved config for avatar: {key}")
            else:
                logger.info(f"Skipping non-YMM avatar: {key}")
        except Exception as e:
            logger.error(f"Failed to save config for avatar {key}: {e}")
    
    return all_configs


def load_all_configs(all_configs: Dict[str, Any]) -> None:
    """
    全アバターに設定を読み込む
    
    Args:
        all_configs: save_all_configs()で保存した設定辞書
    """
    for key, config in all_configs.items():
        avatar = _avatar_cache.get(key)
        if avatar and isinstance(avatar, AvatarWindow):
            try:
                avatar.load_config(config)
                logger.info(f"Loaded config for avatar: {key}")
            except Exception as e:
                logger.error(f"Failed to load config for avatar {key}: {e}")
        else:
            logger.warning(f"Avatar not found or not YMM type: {key}")


# ==================== Private Functions ====================

#
# auto save
#
def _start_auto_save_timer() -> None:
    """
    自動保存タイマーを開始
    """
    global _auto_save_timer
    
    # 既にタイマーが動いていれば停止
    if _auto_save_timer:
        _auto_save_timer.stop()
    
    # 保存間隔を取得(デフォルト5秒=5000ミリ秒)
#    interval = _avatar_global_config.get("auto_save_interval", 5000)
    interval = 50000
    
    _auto_save_timer = QTimer()
    _auto_save_timer.timeout.connect(_on_auto_save)
    _auto_save_timer.start(interval)
    
    logger.info(f"Auto-save timer started. Interval: {interval}ms")


def _on_auto_save() -> None:
    """
    自動保存タイマーのコールバック
    """
    logger.info("Auto-saving all avatar configs...")
    configs = save_all_configs()
    logger.info(f"Auto-saved {len(configs)} avatar config(s).")
    
    # ファイルに保存
    dat_file = _avatar_global_config.get("save_file", None)
    if not dat_file:
        logger.warning(f"dat_file not configured. Skipping file save.")
        return

    if not os.path.exists(dat_file):
        logger.warning(f"dat_file not exists. {dat_file}")
        return

    try:
        with open(dat_file, 'w', encoding='utf-8') as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Configs saved to: {dat_file}")
    except Exception as e:
        logger.error(f"Failed to save configs to file: {e}")


#
# avatar
#
def _create_all_avatars() -> None:
    """
    設定に登録されているすべてのアバターインスタンスを作成
    """
    if not _avatars_config:
        logger.warning("No avatars configured.")
        return
    
    for style_id, avatar_conf in _avatars_config.items():
        try:
            avatar = _get_avatar(style_id)
            if not avatar:
                _create_avatar(style_id, avatar_conf)
                logger.info(f"Created avatar for style_id={style_id}")

        except Exception as e:
            logger.error(f"Failed to create avatar for style_id={style_id}: {e}")


def _create_avatar(style_id: int, avatar_conf: Dict[str, Any]) -> AvatarWindow:
    """
    個別のアバターインスタンスを作成
    
    Args:
        style_id: スタイルID
        avatar_conf: アバター設定
    
    Returns:
        作成されたYMMAvatarWindowインスタンス
    """
    # キャッシュに登録
    # style_idが違っても、avatar_confは参照で同一の場合は、同一avatarとして扱う必要がある。
    key = json.dumps(avatar_conf, sort_keys=True)

    saved_config = _load_config()
    if saved_config:
        saved_config = saved_config.get(key)
    
    # アバターインスタンスの作成
    instance = AvatarWindow(
        style_id=style_id,
        speaker_name=avatar_conf["話者"],
        zip_path=avatar_conf["画像"],
        app_title=_avatar_global_config.get("target", "Claude"),
        anime_types=["立ち絵", "口パク", "えがお", "びっくり", "がーん", "いかり"],
        flip=avatar_conf.get("反転", False),
        scale_percent=avatar_conf.get("縮尺", 50),
        position=avatar_conf.get("位置", "right_out"),
        config=saved_config
    )
    
    # 位置更新と表示設定
    #instance.update_position()
    if avatar_conf.get("表示", False):
        instance.show()
    else:
        instance.hide()

    # キャッシュに登録
    # style_idが違っても、avatar_confは参照で同一の場合は、同一avatarとして扱う必要がある。
    _avatar_cache[key] = instance
    
    return instance

def _get_avatar(style_id: int) -> Optional[AvatarWindow]:
    """
    キャッシュからアバターインスタンスを取得
    
    Args:
        style_id: スタイルID
    
    Returns:
        AvatarWindowインスタンス、存在しない場合はNone
    """

    avatar_conf = _avatars_config.get(style_id)
    key = json.dumps(avatar_conf, sort_keys=True)
    return _avatar_cache.get(key)


def _load_config():
    """
    ファイルから設定を読み込む。
    """
    dat_file = _avatar_global_config.get("save_file")
    if not dat_file:
        logger.warning("dat_file not configured. Skipping file load.")
        return
    
    dat_path = Path(dat_file)
    if not dat_path.exists():
        logger.info(f"Config file not found: {dat_file}")
        return
    
    try:
        with open(dat_path, 'r', encoding='utf-8') as f:
            configs = json.load(f)
        
        logger.info(f"Configs loaded from: {dat_file}")
        return configs
    except Exception as e:
        logger.error(f"Failed to load configs from file: {e}")


# ==================== Test Entry Point ====================

if __name__ == "__main__":
    print("Testing mod_avatar_manager...")
    
    app = QApplication(sys.argv)

    # テスト用設定
    test_config = {
        "enabled": True,
        "target": "Claude",
        "auto_save_interval": 5000,  # 5秒ごとに自動保存
        "dat_file": "C:\\work\\lambda-tuber\\ai-trial\\mission16\\prj_dir\\dat.json",
        "avatars": {
            2: {
                "話者": "四国めたん",
                "表示": True,
                "画像": {},
                "反転": False,
                "縮尺": 50,
                "位置": "right_out"
            },
            14: {
                "話者": "冥鳴ひまり",
                "表示": True,
                "画像": "C:\\work\\lambda-tuber\\ai-trial\\mission16\\docs\\ゆっくり霊夢改.zip",
                "反転": False,
                "縮尺": 50,
                "位置": "right_out"
            }
        }
    }
    
    setup(test_config)
    set_anime_type(2, "口パク")
    
    print("Test completed. Auto-save timer is running...")

    sys.exit(app.exec())
