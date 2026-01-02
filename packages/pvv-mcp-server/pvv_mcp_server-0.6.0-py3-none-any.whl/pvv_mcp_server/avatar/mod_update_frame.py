from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from io import BytesIO
from PIL import Image
import zipfile
import sys
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

def update_frame(self):
    """
    フレームを更新(画像合成)
    
    Args:
        self: AvatarWindowのインスタンス
    """
    if not self.zip_data:
        return
    
    # 現在のアニメタイプのダイアログを取得
    dialog = self.dialogs.get(self.anime_type)
    if not dialog:
        return
    
    try:
        dialog.update_frame()
        pixmap = dialog.get_current_pixmap()

        if not pixmap:
            logger.warning("daialog preview pixmap none.")
            return

        # 表示更新
        self.label.setPixmap(pixmap)
        self.label.adjustSize()
        self.adjustSize()
        
    except Exception as e:
        logger.warning(f"フレーム更新エラー: {e}")
    
    # アニメーションインデックス更新
    # self.anime_index += 1
    # dialog.update_frame_index()
