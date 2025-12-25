
from .tool import Tool

# --- 1. 計算ツール (LLMからの引数のみ使用) ---
class CalculatorTool(Tool):
    def name(self): return "calculator"
    def description(self): return "2つの数値の合計を計算します。引数: a(int), b(int)"
    
    def prepare_args(self, context: dict):
        return {} # システムコンテキストは不要

    def _run(self, a: int, b: int):
        result = a + b
        return {"status": "success", "message": f"計算結果は {result} です。"}

# --- 2. ユーザー情報ツール (システムコンテキストを注入) ---
class UserGreetingTool(Tool):
    def name(self): return "get_user_greeting"
    def description(self): return "ユーザーに合わせた特別な挨拶を生成します。引数なし。"
    
    def prepare_args(self, context: dict):
        # LLMには内緒で、システム側からユーザー名を取得してツールに渡す
        return {"user_name": context.get("user_name", "ゲスト")}

    def _run(self, user_name: str):
        return {
            "status": "success", 
            "message": f"現在のユーザーは「{user_name}」さんです。親しみやすく接してください。"
        }