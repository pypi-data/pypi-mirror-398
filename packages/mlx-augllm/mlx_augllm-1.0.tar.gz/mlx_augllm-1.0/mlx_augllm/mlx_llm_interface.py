
import mlx.core as mx
import mlx_lm
import mlx_vlm
from mlx_lm.sample_utils import make_sampler
import gc
from types import SimpleNamespace

#--------------------------------------------------------------------------------------------
#
#--------------------------------------------------------------------------------------------
class MlxLLMInterface:

    def __init__(self, model_path: str, use_vision: bool = False):
        self.model_path = model_path
        self.use_vision = use_vision
        self.model = None
        self.tokenizer = None
        self.processor = None
        self._load_model()

    def _load_model(self):
        if self.use_vision:
            # VLMモード: mlx-vlmを使用
            self.model, self.processor = mlx_vlm.load(self.model_path, trust_remote_code=True)
            self.tokenizer = self.processor.tokenizer
        else:
            # LMモード: mlx-lmを使用
            self.model, self.tokenizer = mlx_lm.load(self.model_path)

    def generate(self, messages, images=None, stream=False, temp=0.7, max_tokens=8192):
        """
        常にジェネレータを返す統一インターフェース
        """
        sampler = make_sampler(temp=temp)

        # 1. プロンプトの作成
        if self.use_vision:
            prompt = self.processor.apply_chat_template(messages, add_generation_prompt=True)
        else:
            prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        # 2. 生成ロジック
        if stream:
            # --- 逐次生成 (ストリーミング) ---
            if self.use_vision and images:
                yield from mlx_vlm.stream_generate(
                    self.model, 
                    self.processor, 
                    prompt=prompt, 
                    image=images, 
                    sampler=sampler, 
                    max_tokens=max_tokens
                )
            else:
                yield from mlx_lm.stream_generate(
                    self.model, 
                    self.tokenizer, 
                    prompt=prompt, 
                    sampler=sampler, 
                    max_tokens=max_tokens
                )
        else:
            # --- 一括生成 (非ストリーミング) ---
            # mlx_lm.generate を直接呼んで効率化
            if self.use_vision and images:
                full_text = mlx_vlm.generate(
                    self.model, 
                    self.processor, 
                    prompt=prompt, 
                    image=images, 
                    sampler=sampler, 
                    max_tokens=max_tokens
                )
            else:
                full_text = mlx_lm.generate(
                    self.model, 
                    self.tokenizer, 
                    prompt=prompt, 
                    sampler=sampler, 
                    max_tokens=max_tokens
                )
            
            # ストリーミング時とインターフェースを合わせるため、.text を持つオブジェクトとして yield
            yield SimpleNamespace(text=full_text)

    def free_model(self):
        """メモリを解放する"""
        self.model = None
        self.tokenizer = None
        self.processor = None
        gc.collect()
        mx.metal.clear_cache()