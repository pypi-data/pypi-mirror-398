
from typing import List, Optional, Dict, Any
from mlx_vlm.utils import load_image

class PromptBuilder:
    #--------------------------------------------------------------------------
    # 初期化
    #--------------------------------------------------------------------------
    def __init__(self, system_prompt_text: Optional[str] = None, system_prompt_images: Optional[List[str]] = None):
        """
        system_prompt_images: 画像パスのリスト
        """
        self.system_prompt_text = system_prompt_text or ""
        self.system_prompt_images = system_prompt_images or []

    #--------------------------------------------------------------------------
    # システムプロンプト・メッセージを作成する
    #--------------------------------------------------------------------------
    def build_system_message(self, rag_context_text: Optional[str] = None, use_vision: bool = False) -> Dict[str, Any]:
        """
        MLXのモデルが解釈可能なメッセージ辞書を返す
        """
        # 1. テキスト部分の組み立て
        parts = []
        if self.system_prompt_text:
            parts.append(self.system_prompt_text)
        if rag_context_text:
            parts.append(f"### 参考情報:\n{rag_context_text}")
        
        full_text = "\n\n".join(parts)

        # 2. フォーマットの分岐
        if use_vision and self.system_prompt_images:
            # --- VLM形式 (List content) ---
            content = [{"type": "text", "text": full_text}]
            
            # 画像パスをPIL Imageオブジェクトに変換して追加
            # ※際の画像データ自体は後段のgenerateで渡されるが、
            # テンプレート上のプレースホルダーとして{"type": "image"}が必要
            for _ in self.system_prompt_images:
                content.append({"type": "image"})
            
            return {
                "role": "system",
                "content": content,
                "pil_images": [load_image(p) for p in self.system_prompt_images] # 後で取り出せるように保持
            }
        else:
            # --- 通常形式 (String content) ---
            return {
                "role": "system",
                "content": full_text
            }

    #--------------------------------------------------------------------------
    # ユーティリティメソッド
    #--------------------------------------------------------------------------
    def reset(self):
        self.system_prompt_text = ""
        self.system_prompt_images = []

    def set_system_prompt(self, prompt_text: str):
        self.system_prompt_text = prompt_text

    def add_system_image(self, image_path: str):
        self.system_prompt_images.append(image_path)