"""
pvv-mcp-server のエントリポイント

MCPサーバを起動し、コマンドライン引数を処理する
"""

import argparse
import sys
import logging
import yaml
import os
from importlib.metadata import version, PackageNotFoundError

from pvv_mcp_server import mod_service

#
# global setting.
#
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(line_buffering=False, write_through=True)

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S',
)

#
# utility
#
def get_version():
    """
    パッケージのバージョン情報を取得する
    
    Returns:
        str: バージョン文字列
    """
    try:
        return version("pvv-mcp-server")
    except PackageNotFoundError:
        return "development"


#
# main
#
def main():
    """
    MCPサーバを起動する
    コマンドライン引数でバージョン表示・YAML読込にも対応
    """
    parser = argparse.ArgumentParser(
        description="VOICEVOX MCP Server - 音声合成機能を提供するMCPサーバ"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"pvv-mcp-server {get_version()}",
        help="バージョン情報を表示して終了"
    )
    parser.add_argument(
        "-y", "--yaml",
        type=str,
        required=True,
        help="設定用の YAML ファイルパスを指定"
    )

    args = parser.parse_args()

    if not os.path.exists(args.yaml):
        logging.error(f"YAMLファイルが存在しません。{args.yaml} {e}")
        sys.exit(1)


    try:
        config = {}
        with open(args.yaml, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        logging.info(f"YAML設定を読み込みました: {args.yaml}")

        avatar_dict = config.get("avatar", {})
        save_file = avatar_dict.get("save_file")
        if save_file == "default":
            basedir = os.path.dirname(os.path.abspath(args.yaml))
            dat_file = os.path.join(basedir, "pvv-mcp-server.avatar.json")
            config["avatar"]["save_file"] = dat_file
            logging.info(f"Avatar DATファイル: {dat_file}")

        mod_service.start(config)

    except Exception as e:
        logging.error(f"不明な例外が発生しました。{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
