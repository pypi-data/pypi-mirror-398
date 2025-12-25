
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
    def __init__(
        self, 
        model_path: str, 
        use_vision: bool = False, 
        temp: float = 0.0,
        top_k: int = -1, 
        top_p: float = 1.0, 
        min_p: float = 0.0, 
        max_tokens: int = 8192
    ):
        self.model_path = model_path
        self.use_vision = use_vision
        
        # サンプリングパラメータの保持
        self.temp = temp
        self.top_k = top_k
        self.top_p = top_p
        self.min_p = min_p
        self.max_tokens = max_tokens
            
        self.model = None
        self.tokenizer = None
        self.processor = None
        self.sampler = None
        
        self._load_model()

    def _load_model(self):
        # 指定されたパラメータでサンプラーを固定
        self.sampler = make_sampler(
            temp=self.temp,
            top_k=self.top_k, 
            top_p=self.top_p, 
            min_p=self.min_p
        )
        
        if self.use_vision:
            self.model, self.processor = mlx_vlm.load(self.model_path, trust_remote_code=True)
            self.tokenizer = self.processor.tokenizer
        else:
            self.model, self.tokenizer = mlx_lm.load(self.model_path)

    def generate(self, messages, images=None, stream=False):
        """
        インスタンス化時に設定された sampler と max_tokens を使用して生成。
        個別に max_tokens を指定した場合はそちらを優先。
        """

        # 1. プロンプトの作成
        if self.use_vision:
            prompt = self.processor.apply_chat_template(
                messages, 
                add_generation_prompt=True
            )
        else:
            prompt = self.tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )

        # 2. 生成ロジック
        if stream:
            if self.use_vision and images:
                yield from mlx_vlm.stream_generate(
                    self.model, 
                    self.processor, 
                    prompt=prompt, 
                    image=images, 
                    sampler=self.sampler, 
                    max_tokens=self.max_tokens
                )
            else:
                yield from mlx_lm.stream_generate(
                    self.model, 
                    self.tokenizer, 
                    prompt=prompt, 
                    sampler=self.sampler, 
                    max_tokens=self.max_tokens
                )
        else:
            if self.use_vision and images:
                full_text = mlx_vlm.generate(
                    self.model, 
                    self.processor, 
                    prompt=prompt, 
                    image=images, 
                    sampler=self.sampler, 
                    max_tokens=self.max_tokens
                )
            else:
                full_text = mlx_lm.generate(
                    self.model, 
                    self.tokenizer, 
                    prompt=prompt, 
                    sampler=self.sampler, 
                    max_tokens=self.max_tokens
                )
            yield SimpleNamespace(text=full_text)

    def free_model(self):
        self.model = None
        self.tokenizer = None
        self.processor = None
        self.sampler = None
        gc.collect()
        mx.metal.clear_cache()