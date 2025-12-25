# mlx_augllm
MLX（Apple Silicon向け機械学習フレームワーク）を用いた、
ローカルで動作する LLM / VLM のための統一インターフェースライブラリです。

本ライブラリは以下を目的としています。
- ローカルLLM/VLMを簡単かつ一貫したAPIで扱える
- Tool Use（関数呼び出し）に対応
- 会話履歴の管理を自動化
- Apple Siliconに最適化

## インストール
```
pip install -U mlx_augllm
```
- Apple Silicon必須

## サンプル
```python
from mlx_augllm import MlxAugmentedLLM, MlxLLMInterface, PromptBuilder 

def run_test():

    # モデルの準備
    model_path = "mlx-community/gemma-3-27b-it-4bit"
    augmented_llm = MlxAugmentedLLM(
        llm_interface=MlxLLMInterface(
            model_path=model_path,
            use_vision=False,
            temp=0.7,
            top_k=50,
            top_p=0.9,
            min_p=0.05,
            max_tokens=8192
        ),
        prompt_builder=PromptBuilder(system_prompt_text="あなたは有能なアシスタントです。"),
    )

    # 実行テスト
    user_query = "トポロジー最適化について教えてください。"
    
    print(f"\nユーザーの問いかけ: {user_query}")
    print("-" * 50)
    print("AIの応答 (Streaming):")

    # respond の呼び出し (contextを渡す)
    response_generator = augmented_llm.respond(
        user_text=user_query,
        stream=True,
        temp=0.7
    )

    full_response = ""
    for chunk in response_generator:
        print(chunk, end="", flush=True)
        full_response += chunk
    
    print("\n" + "-" * 50)
    print("【内部レポート】")
    if augmented_llm.report_text:
        print(f"最終回答の文字数: {len(augmented_llm.report_text)}")

if __name__ == "__main__":
    run_test()
```