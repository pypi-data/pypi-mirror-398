"""
mod_update_position.py
アバターウィンドウの位置を更新するモジュール
"""

import pygetwindow as gw
import logging
import sys
import ctypes

# ロガーの設定
logger = logging.getLogger(__name__)

def get_windows_scaling() -> float:
    """
    Windows 10/11 向け DPIスケール取得関数（Per-Monitor v2対応）
    現在のモニタのスケーリング倍率（例: 1.25, 1.5）を返す
    スケーリング変更時にも自動で追従
    """
    try:
        user32 = ctypes.windll.user32
        shcore = ctypes.windll.shcore

        # Windows 10 以降: Per-Monitor v2 DPI対応
        user32.SetProcessDpiAwarenessContext(-4)  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2

        # 現在フォアグラウンドウィンドウのモニタを取得
        hwnd = user32.GetForegroundWindow()
        monitor = user32.MonitorFromWindow(hwnd, 1)  # MONITOR_DEFAULTTONEAREST

        # モニタのDPIを取得
        dpiX = ctypes.c_uint()
        dpiY = ctypes.c_uint()
        shcore.GetDpiForMonitor(monitor, 0, ctypes.byref(dpiX), ctypes.byref(dpiY))

        scale = dpiX.value / 96.0  # 96 DPI = 100%
        return scale

    except Exception as e:
        logger.warning(f"Failed to get DPI scaling: {e}")
        return 1.0
        

def update_position(self) -> None:
    """
    self.app_titleで指定されたアプリケーションウィンドウの指定位置に
    下揃えするように、self(AvatarWindow)を移動する
    
    Args:
        self: AvatarWindowのインスタンス
              - self.app_title: ターゲットアプリケーションのウィンドウタイトル
              - self.position: 表示位置 ("left_out", "left_in", "right_in", "right_out")
    
    Returns:
        None
    """
    # app_titleが存在しない場合は何もしない
    if not hasattr(self, 'app_title') or not self.app_title:
        logger.warning("app_title is not set")
        return
    
    # positionが存在しない場合はデフォルト値を設定
    if not hasattr(self, 'position'):
        self.position = "left_out"
    
    try:
        # ターゲットウィンドウを検索
        windows = gw.getWindowsWithTitle(self.app_title)
        
        if not windows:
            # self.follow_timer.stop()
            logger.warning(f"Window with title '{self.app_title}' not found")
            return
        
        # 最初に見つかったウィンドウを使用
        target_window = windows[0]
        
        # ターゲットウィンドウの位置とサイズを取得
        target_x = target_window.left
        target_y = target_window.top
        target_width = target_window.width
        target_height = target_window.height

        # DPIスケーリング取得
        scale = get_windows_scaling()

        # Qtは実ピクセル座標なので、pygetwindowの論理座標を / scale で補正
        target_x = int(target_x / scale)
        target_y = int(target_y / scale)
        target_width = int(target_width / scale)
        target_height = int(target_height / scale)

        # 自身のウィンドウサイズを取得
        avatar_width = self.width()
        avatar_height = self.height()
        
        # positionに応じて配置位置を計算
        if self.position == "left_out":
            # 左下外側（ターゲットウィンドウの左外側）
            new_x = target_x - avatar_width
            new_y = target_y + target_height - avatar_height
            
        elif self.position == "left_center":
            # 左下中央（ターゲットウィンドウの左内側）
            new_x = target_x - (avatar_width / 2)
            new_y = target_y + target_height - avatar_height

        elif self.position == "left_in":
            # 左下内側（ターゲットウィンドウの左内側）
            new_x = target_x
            new_y = target_y + target_height - avatar_height
            
        elif self.position == "right_in":
            # 右下内側（ターゲットウィンドウの右内側）
            new_x = target_x + target_width - avatar_width
            new_y = target_y + target_height - avatar_height
            
        elif self.position == "right_center":
            # 右下中央（ターゲットウィンドウの右内側）
            new_x = target_x + target_width - (avatar_width / 2)
            new_y = target_y + target_height - avatar_height

        elif self.position == "right_out":
            # 右下外側（ターゲットウィンドウの右外側）
            new_x = target_x + target_width
            new_y = target_y + target_height - avatar_height
            
        else:
            logger.warning(f"Unknown position: {self.position}")
            return
        
        # ウィンドウを移動
        self.move(int(new_x), int(new_y))
        
    except Exception as e:
        logger.warning(f"Failed to update position: {e}")
        