
import os
from huggingface_hub import try_to_load_from_cache
from huggingface_hub.utils import disable_progress_bars, enable_progress_bars

def toggle_hf_progress_bar(model_path: str):
    """
    キャッシュの有無を確認し、プログレスバーをプログラムから直接オン/オフする。
    """
    # 1. ローカルディレクトリとして存在する場合
    if os.path.isdir(model_path):
        disable_progress_bars()
        return

    # 2. Repo IDの場合、キャッシュを確認
    try:
        # config.json があるかチェック
        cached_file = try_to_load_from_cache(repo_id=model_path, filename="config.json")
        if cached_file:
            # すでにダウンロード済みなら非表示
            disable_progress_bars()
        else:
            # 新規ダウンロードが必要なら表示
            enable_progress_bars()
    except Exception:
        # 判定に失敗した場合は念のため表示（ダウンロード中かもしれないため）
        enable_progress_bars()