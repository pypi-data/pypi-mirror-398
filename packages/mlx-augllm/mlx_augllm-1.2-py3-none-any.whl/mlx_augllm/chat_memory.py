import copy
import pickle
from typing import List, Dict, Tuple
from mlx_vlm.utils import load_image

#--------------------------------------------------------------------------------------------
#
#--------------------------------------------------------------------------------------------
class ChatMemory:

    def __init__(self, max_memory: int = 5):
        self.max_memory = max_memory
        self.history: List[Tuple[Dict, Dict]] = []

    def add(self, user_text: str, assistant_text: str, user_image_paths: List[str] = None):
        """新しい会話セットを追加"""
        if self.max_memory <= 0:
            return

        user_msg = {"role": "user", "content": user_text}
        if user_image_paths:
            user_msg["images"] = user_image_paths

        assistant_msg = {"role": "assistant", "content": assistant_text}
        
        self.history.append((user_msg, assistant_msg))

        # 最大数を超えたら古いものを削除
        if len(self.history) > self.max_memory:
            self.history = self.history[-self.max_memory:]

    def clear(self):
        """履歴をリセット"""
        self.history = []

    def get_messages(self, use_vision: bool = False) -> Tuple[List[Dict], List]:
        """
        LLMに渡すためのメッセージリストと、対応するPIL画像のリストを生成
        return: (flattened_messages, all_pils)
        """
        flattened = []
        all_pils = []

        for user_msg, assistant_msg in self.history:
            # ユーザーメッセージの処理
            u_msg = copy.deepcopy(user_msg)
            if use_vision and "images" in u_msg:
                paths = u_msg["images"]
                pils = [load_image(str(p)) for p in paths]
                
                # VLM形式への変換
                content = [{"type": "text", "text": u_msg["content"]}]
                for _ in pils:
                    content.append({"type": "image"})
                
                u_msg["content"] = content
                all_pils.extend(pils)
                del u_msg["images"]
            
            flattened.append(u_msg)
            flattened.append(copy.deepcopy(assistant_msg))

        return flattened, all_pils
    
    def save_to_file(self, filepath: str):
        """現在の記憶をファイルに保存"""
        with open(filepath, 'wb') as f:
            pickle.dump(self.history, f)

    def load_from_file(self, filepath: str):
        """ファイルから記憶を復元"""
        with open(filepath, 'rb') as f:
            self.history = pickle.load(f)