from PySide6.QtWidgets import QApplication, QWidget, QLabel, QDialog, QComboBox, QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtGui import QPixmap, QPainter, QImage, QShortcut, QKeySequence
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTransform
import sys
import zipfile
import io
from collections import defaultdict

import pvv_mcp_server.avatar.mod_avatar_part
import logging

# ロガーの設定
logger = logging.getLogger(__name__)


class AvatarDialog(QDialog):

    def __init__(self, parent, zip_dat, scale_percent, flip, interval, config=None):
        super().__init__(parent)
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.zip_dat = zip_dat
        self.scale = scale_percent
        self.flip = flip

        #self.setWindowTitle(f"立ち絵画像選択ダイアログ-{anime_type}")
        #self.setObjectName(f"dialog_{anime_type}")
        self.current_pixmap = None

        self.parts = ['後', '体', '顔', '髪', '口', '目', '眉', '服下', '服上', '全', '他']
        self.part_widgets = {}
        for cat in self.parts:
            file_names = list(zip_dat[cat].keys())
            conf = None
            if config and "parts" in config and cat in config["parts"]:
                conf = config["parts"][cat]
            part_widget = pvv_mcp_server.avatar.mod_avatar_part.AvatarPartWidget(cat, file_names, conf)
            self.part_widgets[cat] = part_widget

        # if config:
        #     self.load_config(config)
          
        self.setup_gui()

    #
    # GUI
    #
    def setup_gui(self):

        # ----------------------------------------------------
        # 3. 3x3 グリッドレイアウトの作成と配置
        # ----------------------------------------------------
        main_layout = QVBoxLayout(self)

        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10) # グリッド間のスペースを設定
        
        # 4x3 グリッドの配置順序を定義
        # 0 1 2
        # 3 4 5
        # 6 7 8
        # 9 10 11
        widget_keys = ['目', '眉', '顔',
                       '口',       '髪',
                       '体', '後', '服下',
                       '服上', '全', '他']
        
        for i in range(12):
            row = i // 3  # 行インデックス (0, 1, 2)
            col = i % 3   # 列インデックス (0, 1, 2)
            
            if i == 4:
                # 3x3 グリッドの中央 (インデックス 4) にラベルを配置
                self.center_label = QLabel()
                self.center_label.setAlignment(Qt.AlignCenter)
                # サイズは画像に合わせて自動調整
                self.center_label.setScaledContents(False)
                self.center_label.setStyleSheet("border: 1px solid gray;")
                
                # グリッドセル内で水平・垂直ともに中央揃え
                grid_layout.addWidget(self.center_label, row, col, Qt.AlignCenter)

            else:
                # 8つのウィジェットを中央セルを避けて配置
                # widget_keys は parts の ['後', '体', '顔', '髪', '口', '目', '眉', '他']
                
                # 中央セル (i=4) をスキップするため、ウィジェットリストのインデックスを調整
                widget_index = i
                if i > 4:
                    widget_index = i - 1
                    
                cat_key = widget_keys[widget_index]
                widget_to_add = self.part_widgets[cat_key]
                
                grid_layout.addWidget(widget_to_add, row, col)

        # 4. メインレイアウトにグリッドウィジェットを追加
        main_layout.addWidget(grid_widget)
        
        self.setLayout(main_layout)

    def closeEvent(self, event):
        """×ボタンが押された時の処理をオーバーライド"""
        # closeイベントを無視して、hideだけ実行
        event.ignore()
        self.hide()

    #
    # save/load config
    #
    def save_config(self):
        """
        ダイアログ全体の設定を辞書形式で返す
        
        Returns:
            dict: 設定辞書
        """

        config = {
            # "scale": self.scale,
            # "flip": self.flip,
            # "frame_timer_interval": self.frame_timer_interval,
            "parts": {}
        }
        
        # 各パーツの設定を収集
        for cat in self.parts:
            part_config = self.part_widgets[cat].save_config()
            config["parts"][cat] = part_config
        
        logger.info(f"save_config [AvatarDialog]: scale={self.scale}, flip={self.flip}")
        logger.info(f"  parts count: {len(config['parts'])}")
        
        return config

    def load_config(self, config):
        """
        設定辞書からダイアログ全体の設定を読み込む
        
        Args:
            config: save_config()で保存した辞書
        """
        logger.info(f"load_config [AvatarDialog]")
        
        # 各パーツの設定を読み込み
        if "parts" in config:
            for cat, part_config in config["parts"].items():
                if cat in self.part_widgets:
                    logger.info(f"  loading part: {cat}")
                    self.part_widgets[cat].load_config(part_config)
                else:
                    logger.warning(f"  unknown part: {cat}")

    #
    # setter
    #
    def set_flip(self, val):
        """左右反転を設定"""
        self.flip = val

    def set_scale(self, val):
        """スケール設定"""
        self.scale = val

    #
    # public function
    #
    def get_current_pixmap(self):
        return self.current_pixmap

    def start_oneshot(self):
        for cat in self.parts:
            self.part_widgets[cat].start_oneshot()

    def update_frame(self):
        base_image = None
        painter = None
        
        for cat in self.parts:
            png_file = self.part_widgets[cat].update()
            if png_file:
                png_dat = self.zip_dat[cat][png_file]
                
                # バイトデータからQImageを作成
                part_image = QImage()
                part_image.loadFromData(png_dat)
                
                # 最初のパーツでベース画像を作成
                if base_image is None:
                    base_width = part_image.width()
                    base_height = part_image.height()
                    base_image = QImage(base_width, base_height, QImage.Format_ARGB32)
                    base_image.fill(Qt.transparent)
                    painter = QPainter(base_image)
                
                # パーツを中央揃えで描画
                x = (base_image.width() - part_image.width()) // 2
                y = (base_image.height() - part_image.height()) // 2
                painter.drawImage(x, y, part_image)
        
        # ベース画像が作成されていればラベルに設定
        if base_image is not None and painter is not None:
            painter.end()

            pixmap_org = QPixmap.fromImage(base_image)

            if self.flip:
                transform = QTransform()
                transform.scale(-1, 1)
                pixmap_org = pixmap_org.transformed(transform)

            new_width = int(pixmap_org.width() * self.scale / 100)
            new_height = int(pixmap_org.height() * self.scale / 100)
            self.current_pixmap = pixmap_org.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.center_label.setPixmap(self.current_pixmap)



if __name__ == "__main__":

    zip_file = "C:\\work\\lambda-tuber\\ai-trial\\mission16\\docs\\ゆっくり霊夢改.zip"
    #zip_file = "C:\\work\\lambda-tuber\\ai-trial\\mission16\\docs\\れいむ.zip"

    zip_bytes = None
    with open(zip_file, "rb") as f:
        zip_bytes = f.read()

    # メモリ上で展開
    zip_buffer = io.BytesIO(zip_bytes)
    png_dat = defaultdict(dict)
    with zipfile.ZipFile(zip_buffer, 'r', metadata_encoding='cp932') as zf:
        for info in zf.infolist():
            #print(f"ファイル名: {info.filename}")
            with zf.open(info) as file:
                if info.filename.endswith("/"):  # フォルダはスキップ
                    continue
                parts = info.filename.split("/")
                if len(parts) >= 3:
                    file_content_bytes = file.read()
                    cat = parts[-2]  # 「口」「他」などのカテゴリ
                    fname = parts[-1]  # ファイル名
                    print(f"{parts}")
                    png_dat[cat][fname] = file_content_bytes



    app = QApplication(sys.argv)
    dialog1 = AvatarDialog(png_dat, 100, False, 100)
    dialog1.show()

    conf = dialog1.save_config()

    conf["parts"]["顔"]["base_image"] = "05a.png"
    dialog2 = AvatarDialog(png_dat, 100, False, 100, conf)
    dialog2.show()

    conf["parts"]["顔"]["base_image"] = "06b.png"
    dialog3 = AvatarDialog(png_dat, 100, False, 100)
    dialog3.load_config(conf)
    dialog3.show()

    sys.exit(app.exec())
