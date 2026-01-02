from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QListWidget, QListWidgetItem,
    QVBoxLayout, QHBoxLayout, QScrollArea, QCheckBox
)
from PySide6.QtWidgets import QHBoxLayout, QLabel, QRadioButton, QButtonGroup
from PySide6.QtCore import Qt
import sys
import random
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

class AvatarPartWidget(QWidget):

    def __init__(self, part_name, image_files, config=None):
        """
        Args:
            part_name: パーツ名
            image_files: 画像ファイルのリスト
            config: 初期設定辞書(Noneならデフォルト値)
        """
        super().__init__()
        self.part_name = part_name
        self.image_files = image_files
        
        # デフォルト値で初期化
        self._init_default_values()
        
        # 設定が渡されていれば適用
        if config:
            self.load_config(config)
        
        # GUI構築(設定を反映した状態で)
        self._setup_gui()

    def _init_default_values(self):
        """デフォルト値で初期化"""
        if len(self.image_files) > 0:
            self.base_image = self.image_files[0]
        else:
            self.base_image = None

        self.current_image = self.base_image
        self.selected_files = []
        self.update_idx = 0    
        self.interval = 3
        self.anime_type = "固定"
        self.is_enabled = True  # パーツの有効状態
        self.random_wait_tick = random.choice([10, 20, 30, 40, 50])
        self.random_wait_idx = 0
        self.random_anime_idx = 0
        self.loop_anime_idx = 0
        self.oneshot_idx = 0


    #
    # save/load confg
    #
    def save_config(self):
        """
        現在の設定を辞書形式で返す
        
        Returns:
            dict: 設定辞書
        """
        config = {
            "part_name": self.part_name,
            "base_image": self.base_image,
            "selected_files": self.selected_files.copy(),
            "interval": self.interval,
            "anime_type": self.anime_type,
            "is_enabled": self.is_enabled
        }
        logger.info(f"save_config [{self.part_name}]: {config}")
        return config
    
    def load_config(self, config):
        """
        設定辞書から値を読み込む
        
        Args:
            config: save_config()で保存した辞書
        """
        logger.info(f"load_config [{self.part_name}]: {config}")
        
        if "base_image" in config:
            self.base_image = config["base_image"]
            self.current_image = self.base_image
        
        if "selected_files" in config:
            self.selected_files = config["selected_files"].copy()
        
        if "interval" in config:
            self.interval = config["interval"]
        
        if "anime_type" in config:
            self.anime_type = config["anime_type"]
        
        if "is_enabled" in config:
            self.is_enabled = config["is_enabled"]
        
        # カウンタ類をリセット
        self.update_idx = 0
        self.loop_anime_idx = 0
        self.random_anime_idx = 0
        self.random_wait_idx = 0
        self.random_wait_tick = random.choice([10, 20, 30, 40, 50])
        
        # GUIが既に構築されていれば、GUIにも反映
        if hasattr(self, 'combo_base'):
            self._apply_config_to_gui()

    #
    # GUI
    #
    def _setup_gui(self):
        main_layout = QVBoxLayout(self)

        # 1段目: パーツ名
        part_name_layout = QHBoxLayout()
        part_name_layout.addWidget(QLabel("パーツ名:"))
        part_name_layout.addWidget(QLabel(self.part_name))
        part_name_layout.addStretch(1)
        main_layout.addLayout(part_name_layout)

        # 2段目: 有効／無効チェックボックス
        enabled_layout = QHBoxLayout()
        enabled_layout.addWidget(QLabel("有効／無効:"))
        self.check_enabled = QCheckBox()
        self.check_enabled.setChecked(True)
        self.check_enabled.stateChanged.connect(self._on_enabled_changed)
        enabled_layout.addWidget(self.check_enabled)
        enabled_layout.addStretch(1)
        main_layout.addLayout(enabled_layout)

        # 3段目: ベース画像
        base_layout = QHBoxLayout()
        base_layout.addWidget(QLabel("ベース画像:"))
        self.combo_base = QComboBox()
        self.combo_base.addItems(self.image_files)
        self.combo_base.currentTextChanged.connect(self._update_base_image)
        base_layout.addWidget(self.combo_base)
        base_layout.addStretch(1)
        main_layout.addLayout(base_layout)

        # 4段目: アニメ画像
        anim_layout = QHBoxLayout()
        anim_layout.addWidget(QLabel("アニメ画像:"), alignment=Qt.AlignTop)
        self.list_anim = QListWidget()
        self.list_anim.setSelectionMode(QListWidget.MultiSelection)
        for f in self.image_files:
            self.list_anim.addItem(QListWidgetItem(f))
        self.list_anim.itemSelectionChanged.connect(self._update_selected_files)
        self.list_anim.setMaximumHeight(100)
        anim_layout.addWidget(self.list_anim)
        main_layout.addLayout(anim_layout)

        # 5段目: interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("インターバル:"))
        self.combo_interval = QComboBox()
        self.combo_interval.addItems(["1", "2", "4", "8", "10","12", "14", "16", "18", "20", "22", "24", "26", "28", "30"])
        self.combo_interval.setCurrentIndex(2)
        self.combo_interval.currentTextChanged.connect(self._update_interval)
        interval_layout.addWidget(self.combo_interval)
        interval_layout.addStretch(1)
        main_layout.addLayout(interval_layout)

        # 6段目: アニメーションタイプ
        anim_type_layout = QHBoxLayout()
        anim_type_layout.addWidget(QLabel("アニメタイプ:"))

        self.radio_fixed = QRadioButton("固定")
        self.radio_loop = QRadioButton("ループ")
        self.radio_random_a = QRadioButton("ランダムA")
        self.radio_random_b = QRadioButton("ランダムB")
        self.radio_oneshot = QRadioButton("ワンショット")

        self.anim_type_group = QButtonGroup(self)
        self.anim_type_group.addButton(self.radio_fixed)
        self.anim_type_group.addButton(self.radio_loop)
        self.anim_type_group.addButton(self.radio_random_a)
        self.anim_type_group.addButton(self.radio_random_b)
        self.anim_type_group.addButton(self.radio_oneshot)
        self.anim_type_group.buttonClicked.connect(self._on_anim_type_changed)

        self.radio_fixed.setChecked(True)

        anim_type_layout.addWidget(self.radio_fixed)
        anim_type_layout.addWidget(self.radio_loop)
        anim_type_layout.addWidget(self.radio_random_a)
        anim_type_layout.addWidget(self.radio_random_b)
        anim_type_layout.addWidget(self.radio_oneshot)
        anim_type_layout.addStretch(1)

        main_layout.addLayout(anim_type_layout)
        
        # 最後に設定をGUIに反映
        self._apply_config_to_gui()

    
    def _apply_config_to_gui(self):
        """設定値をGUIウィジェットに反映"""
        logger.info(f"_apply_config_to_gui [{self.part_name}]")
        logger.info(f"  selected_files: {self.selected_files}")
        
        # 有効／無効のチェックボックス
        self.check_enabled.blockSignals(True)
        self.check_enabled.setChecked(self.is_enabled)
        self.check_enabled.blockSignals(False)
        
        # ベース画像のコンボボックス
        if self.base_image:
            index = self.combo_base.findText(self.base_image)
            if index >= 0:
                self.combo_base.setCurrentIndex(index)
        
        # アニメ画像のリスト選択
        # シグナルを一時的にブロックして、余計なイベント発火を防ぐ
        self.list_anim.blockSignals(True)
        
        # まず全選択解除
        for i in range(self.list_anim.count()):
            self.list_anim.item(i).setSelected(False)
        
        # selected_filesに含まれるものだけ選択
        for i in range(self.list_anim.count()):
            item = self.list_anim.item(i)
            if item.text() in self.selected_files:
                item.setSelected(True)
                logger.info(f"  選択: {item.text()}")
        
        # シグナルのブロックを解除
        self.list_anim.blockSignals(False)
        
        # インターバル
        index = self.combo_interval.findText(str(self.interval))
        if index >= 0:
            self.combo_interval.setCurrentIndex(index)
        
        # アニメタイプのラジオボタン
        if self.anime_type == "固定":
            self.radio_fixed.setChecked(True)
        elif self.anime_type == "ループ":
            self.radio_loop.setChecked(True)
        elif self.anime_type == "ランダムA":
            self.radio_random_a.setChecked(True)
        elif self.anime_type == "ランダムB":
            self.radio_random_b.setChecked(True)
        elif self.anime_type == "ワンショット":
            self.radio_oneshot.setChecked(True)


    #
    # gui handlers
    #
    def _on_enabled_changed(self, state):
        """有効／無効チェックボックスの状態変化ハンドラ"""
        self.is_enabled = bool(state)
        logger.info(f"is_enabled [{self.part_name}]: {self.is_enabled}")

    def _update_selected_files(self):
        self.selected_files = [item.text() for item in self.list_anim.selectedItems()]
        logger.info(f"selected_files: {self.selected_files}")

    def _update_base_image(self, text):
        self.base_image = text
        logger.info(f"base_image: {self.base_image}")

    def _update_interval(self, text):
        self.interval = int(text)
        logger.info(f"interval: {self.interval}")

    def _on_anim_type_changed(self, button):
        self.anime_type = button.text()
        logger.info(f"選択されたアニメーションタイプ: {self.anime_type}")

        # 共通のカウンタをリセット
        self.update_idx = 0
        self.loop_anime_idx = 0
        self.random_anime_idx = 0
        self.random_wait_idx = 0
        self.random_wait_tick = random.choice([10, 20, 30, 40, 50])
        self.start_oneshot()
        logger.info(f"random_wait_tick : {self.random_wait_tick}")


    #
    # animation
    #
    def start_oneshot(self):
        """外部からoneshotアニメを開始するトリガー"""
        if not self.is_enabled:
            return 

        if len(self.selected_files) > 0:
            logger.info(f"{self.part_name}: start_oneshot")
            self.oneshot_idx = 1
            

    def update(self):
        if not self.is_enabled:
            return None

        if len(self.image_files) == 0:
            return None

        if self.update_idx < self.interval:
            self.update_idx = self.update_idx + 1
            return self.current_image

        self.update_idx = 0

        if self.anime_type == "固定":
            self.current_image = self.base_image

        if self.anime_type == "ループ":
            self._update_loop()

        if self.anime_type == "ランダムA":
            self._update_random_a()

        if self.anime_type == "ランダムB":
            self._update_random_b()

        if self.anime_type == "ワンショット":
            self._update_oneshot()

        return self.current_image

    def _update_loop(self):
        self.current_image = self.selected_files[self.loop_anime_idx]
        self.loop_anime_idx = (self.loop_anime_idx + 1) % len(self.selected_files)

    def _update_random_a(self):
        """ランダムA: base画像をランダム時間表示 → アニメ画像をワンショット再生"""
        
        if self.random_anime_idx == 0:
            # 待機モード: base画像を表示
            self.current_image = self.base_image
            
            # カウントアップ
            self.random_wait_idx += 1
            
            # ランダム待機時間に達したらアニメ開始
            if self.random_wait_idx >= self.random_wait_tick:
                self.random_wait_idx = 0
                # 次のランダム待機時間を設定
                self.random_wait_tick = random.choice([10, 20, 30, 40, 50])
                logger.info(f"random_wait_tick : {self.random_wait_tick}")

                # アニメ画像が選択されていればアニメ開始
                if len(self.selected_files) > 0:
                    self.random_anime_idx = 1  # アニメ開始フラグ
        
        else:
            # アニメ再生モード
            idx = self.random_anime_idx - 1
            
            if idx < len(self.selected_files):
                self.current_image = self.selected_files[idx]
                self.random_anime_idx += 1
            else:
                # アニメ終了: 待機モードに戻る
                self.random_anime_idx = 0
                self.current_image = self.base_image
                
    def _update_random_b(self):
        """ランダムB: selected_filesからランダムに1つ選んで、ランダムな時間表示"""
        
        # カウンタをインクリメント
        self.random_wait_idx += 1
        
        # まだ待機時間に達していない場合は、現在の画像をそのまま返す
        if self.random_wait_idx < self.random_wait_tick:
            return
        
        # 待機時間に達したら、次の画像に切り替え
        self.random_wait_idx = 0
        
        # 次のランダムな待機時間を設定
        self.random_wait_tick = random.choice([10, 20, 30, 40, 50])
        logger.info(f"random_wait_tick : {self.random_wait_tick}")

        # ランダムに画像を選択
        if len(self.selected_files) > 0:
            self.current_image = random.choice(self.selected_files)
        else:
            # フォールバック
            self.current_image = self.base_image


    def _update_oneshot(self):
        """ワンショット: selected_filesを順番に表示→base_imageに戻る"""
        
        if self.oneshot_idx == 0:
            # 待機モード: base画像を表示
            self.current_image = self.base_image
        
        elif self.oneshot_idx > 0:
            # アニメ再生モード
            idx = self.oneshot_idx - 1
            
            if idx < len(self.selected_files):
                self.current_image = self.selected_files[idx]
                self.oneshot_idx += 1
            else:
                # アニメ終了: 待機モードに戻る
                self.oneshot_idx = 0
                self.current_image = self.base_image



if __name__ == "__main__":
    app = QApplication(sys.argv)

    # テスト1: デフォルトで生成
    print("=== テスト1: デフォルト生成 ===")
    part_widget1 = AvatarPartWidget("目", ["01.png", "02.png", "03.png"])
    
    # テスト2: 設定を保存
    print("\n=== テスト2: 設定を保存 ===")
    config = part_widget1.save_config()
    print(f"保存された設定: {config}")
    
    # テスト3: 設定を変更
    print("\n=== テスト3: 設定を変更 ===")
    part_widget1.anime_type = "ランダムA"
    part_widget1.selected_files = ["01.png", "02.png"]
    part_widget1.interval = 5
    
    # テスト4: 変更した設定を保存
    print("\n=== テスト4: 変更後の設定を保存 ===")
    config2 = part_widget1.save_config()
    print(f"変更後の設定: {config2}")
    
    # テスト5: 設定付きで新規生成
    print("\n=== テスト5: 設定付きで生成 ===")
    preset_config = {
        "part_name": "口",
        "base_image": "02.png",
        "selected_files": ["01.png", "03.png"],
        "interval": 2,
        "anime_type": "ループ",
        "is_enabled": True
    }
    part_widget2 = AvatarPartWidget("口", ["01.png", "02.png", "03.png"], config=preset_config)
    
    part_widget1.show()

    part_widget2.show()

    sys.exit(app.exec())