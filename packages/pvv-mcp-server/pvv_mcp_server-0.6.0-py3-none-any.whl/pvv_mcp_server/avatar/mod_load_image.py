import logging
import io
import os
import sys
from collections import defaultdict
import zipfile
import urllib.request
import base64
from pathlib import Path

# ロガーの設定
logger = logging.getLogger(__name__)


def load_image(source, speaker_id=None):
    """
    画像データを読み込む
    
    Args:
        source: 以下のいずれかの形式
            - ローカルZIPファイルパス (例: "C:\\path\\to\\file.zip")
            - URL (例: "https://example.com/avatar.zip")
            - フォルダパス (例: "C:\\path\\to\\image")
            - 文字列 ("portrait") - VOICEVOXのポートレートを使用
        speaker_id: VOICEVOXの話者ID (sourceが空文字列の場合に使用)
    
    Returns:
        dict: パーツカテゴリ別の画像データ辞書
    """
    
    parts_folder = ['後', '体', '顔', '髪', '口', '目', '眉', '服下', '服上', '全', '他']

    # 1. 空文字列 → VOICEVOXのポートレート
    if source == "portrait":
        return _load_voicevox_portrait(speaker_id)
    
    # 2. URL → ダウンロードしてZIP展開
    if source.startswith("http://") or source.startswith("https://"):
        if source.endswith(".zip"):
            return _load_zip_from_url(source, parts_folder)
    
    # 3. sourceがフォルダの場合
    if os.path.isdir(source):
        return _load_folder(source, parts_folder)
    
    # 4. ローカルZIPファイル → 既存の処理
    if source.lower().endswith(".zip"):
        return _load_local_zip(source, parts_folder)
    
    # 不明な形式
    logger.error(f"不明なsource形式: {source}")
    return _create_empty_zip_data()


def _load_folder(source, parts_folder):
    """指定フォルダ配下のPNGファイルを再帰的に読み込む"""
    
    try:
        folder_path = Path(source)
        
        if not folder_path.exists():
            logger.error(f"フォルダが存在しません: {source}")
            return _create_empty_zip_data()
        
        zip_data = defaultdict(dict)
        
        # 再帰的にPNGファイルを探索
        png_files = list(folder_path.rglob("*.png"))
        
        if not png_files:
            logger.warning(f"PNGファイルが見つかりません: {source}")
            return _create_empty_zip_data()
        
        for png_file in png_files:
            try:
                # ファイルを読み込む
                with open(png_file, "rb") as f:
                    file_content_bytes = f.read()
                
                # 親フォルダ名をカテゴリとする
                cat = png_file.parent.name
                
                # カテゴリがparts_folderに含まれていない場合は「他」
                if cat not in parts_folder:
                    cat = "他"
                
                # ファイル名
                fname = png_file.name
                
                # 登録
                zip_data[cat][fname] = file_content_bytes
                logger.info(f"読み込み: {cat}/{fname}")
                
            except Exception as e:
                logger.error(f"ファイル読み込みエラー: {png_file}, {e}")
                continue
        
        logger.info(f"フォルダからPNGファイルを読み込みました: {source}")
        return zip_data
        
    except Exception as e:
        logger.error(f"フォルダ読み込みエラー: {e}")
        return _create_empty_zip_data()


def _load_local_zip(zip_path, parts_folder):
    """ローカルZIPファイルを読み込む"""
    try:
        with open(zip_path, "rb") as f:
            zip_bytes = f.read()

        # メモリ上で展開
        zip_buffer = io.BytesIO(zip_bytes)
        zip_data = defaultdict(dict)
        with zipfile.ZipFile(zip_buffer, 'r', metadata_encoding='cp932') as zf:
            for info in zf.infolist():
                with zf.open(info) as file:
                    if not info.filename.endswith(".png"):
                        continue
                    parts = info.filename.split("/")
                    if len(parts) >= 3:
                        file_content_bytes = file.read()
                        cat = parts[-2]  # 「口」「他」などのカテゴリ
                        if cat not in parts_folder:
                            logger.info(f"ZIPファイル: {info.filename}")
                            if cat == "服下":
                                cat = "後"
                            else:
                                cat = "他"
                        fname = parts[-1]  # ファイル名
                        zip_data[cat][fname] = file_content_bytes

        logger.info(f"ローカルZIPファイルを読み込みました: {zip_path}")
        return zip_data

    except Exception as e:
        logger.error(f"ローカルZIPファイル読み込みエラー: {e}")
        return _create_empty_zip_data()


def _load_zip_from_url(url, parts_folder):
    """URLからZIPファイルをダウンロードして読み込む"""
    try:
        logger.info(f"ZIPファイルをダウンロード中: {url}")

        # 日本語を含むURLを正しくエンコード
        parsed = urllib.parse.urlsplit(url)
        encoded_path = urllib.parse.quote(parsed.path)
        encoded_url = urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, encoded_path, parsed.query, parsed.fragment)
        )

        # URLからダウンロード
        with urllib.request.urlopen(encoded_url) as response:
            zip_bytes = response.read()

        logger.info(f"ダウンロード完了: {len(zip_bytes)} bytes")
        # メモリ上で展開
        zip_buffer = io.BytesIO(zip_bytes)
        zip_data = defaultdict(dict)
        with zipfile.ZipFile(zip_buffer, 'r', metadata_encoding='cp932') as zf:
            for info in zf.infolist():
                with zf.open(info) as file:
                    if not info.filename.endswith(".png"):
                        continue
                    (cat, fname) = _parse_cat_path(info.filename, parts_folder)
                    zip_data[cat][fname] = file.read()
                    # parts = info.filename.split("/")
                    # if len(parts) >= 3:
                    #     file_content_bytes = file.read()
                    #     cat = parts[-2]
                    #     if cat not in parts_folder:
                    #         if cat == "服下":
                    #             cat = "後"
                    #         else:
                    #             cat = "他"
                    #     fname = parts[-1]
                    #     zip_data[cat][fname] = file_content_bytes

        logger.info(f"URLからZIPファイルを読み込みました: {url}")
        return zip_data

    except Exception as e:
        logger.error(f"URL ZIPファイル読み込みエラー: {e}")
        return defaultdict(dict)


def _parse_cat_path(filepath: str, parts_folder):
    """
    キャラ素材パスからカテゴリとファイル名を判定して返す。
    前提：
      - カテゴリはパスの下位から第2層 or 第3層にのみ存在。
      - それ以外の階層にある場合は「他」とする。
    仕様：
      - 「服下」は「後」に変換。
      - カテゴリ直下に 00/01 フォルダがあれば、影あり／なしとして接頭辞を付ける。
    """
    #parts = filepath.replace("\\", "/").split("/")
    #parts = [p for p in parts if p]
    parts = filepath.split("/")
    filename = parts[-1]

    cat = "他"
    prefix = ""

    # 下位2層目と3層目のみチェック
    candidates = []
    if len(parts) >= 2:
        candidates.append(parts[-2])  # 下から2層目
    if len(parts) >= 3:
        candidates.append(parts[-3])  # 下から3層目

    for p in candidates:
        if p in parts_folder:
            cat = p
            # 直下のフォルダで影あり/影なし判定
            idx = parts.index(p)
            if idx + 1 < len(parts):
                if parts[idx + 1] == "00":
                    prefix = "00_"
                elif parts[idx + 1] == "01":
                    prefix = "01_"
            break

    filename = prefix + filename
    return cat, filename


def _load_voicevox_portrait(speaker_id: str):
    """VOICEVOXのポートレートを取得"""
    try:
        from pvv_mcp_server.mod_speaker_info import speaker_info
        
        if not speaker_id:
            logger.warning("speaker_idが指定されていません")
            return _create_empty_zip_data()
        
        logger.info(f"call speaker_info with {speaker_id}")
        info = speaker_info(speaker_id)
        portrait_url = info.get("portrait")
        logger.info(f"portrait_url : {portrait_url}")
        
        if not portrait_url:
            logger.warning(f"speaker_id={speaker_id}のポートレートが見つかりません")
            return _create_empty_zip_data()
        
        # URLから画像をダウンロード
        logger.info(f"ポートレートをダウンロード中: {portrait_url}")
        with urllib.request.urlopen(portrait_url) as response:
            png_bytes = response.read()
        
        zip_data = _create_empty_zip_data()
        zip_data["他"]["portrait.png"] = png_bytes
        
        logger.info(f"VOICEVOXポートレートを読み込みました: speaker_id={speaker_id}")
        return zip_data

    except Exception as e:
        logger.error(f"VOICEVOXポートレート読み込みエラー: {e}")
        return _create_empty_zip_data()


def _create_empty_zip_data():
    """空のzip_dataを作成"""
    parts_folder = ['後', '体', '顔', '髪', '口', '目', '眉', '服下', '服上', '全', '他']

    zip_data = defaultdict(dict)
    
    # 各カテゴリに空の辞書を設定
    for cat in parts_folder:
        zip_data[cat] = {}
    
    return zip_data


if __name__ == "__main__":
    # テスト1: ローカルZIP
    print("=== テスト1: ローカルZIP ===")
    zip_file = "C:\\work\\lambda-tuber\\ai-trial\\mission16\\docs\\ゆっくり霊夢改.zip"
    png_dat = load_image(zip_file)
    print(f"カテゴリ: {list(png_dat.keys())}")
    
    # テスト2: PNG
    print("\n=== テスト2: PNG ===")
    png_file = "C:\\work\\lambda-tuber\\ai-trial\\mission16\\docs\\josei_20_pw\\josei_20_a.png"
    png_dat = load_image(png_file)
    print(f"カテゴリ: {list(png_dat.keys())}")
    
    # テスト3: VOICEVOX
    #print("\n=== テスト3: VOICEVOX ===")
    #png_dat = load_image("", speaker_id="四国めたん")
    #print(f"カテゴリ: {list(png_dat.keys())}")
    
    # テスト4: URL
    print("\n=== テスト4: URL ===")
    url = "http://www.nicotalk.com/sozai/きつねゆっくり/れいむ.zip"
    url = "http://nicotalk.com/sozai/新きつねゆっくり/新まりさ.zip"
    #url = "http://nicotalk.com/sozai/新きつねゆっくり/新れいむ.zip"
    png_dat = load_image(url)
    print(f"カテゴリ: {list(png_dat.keys())}")


