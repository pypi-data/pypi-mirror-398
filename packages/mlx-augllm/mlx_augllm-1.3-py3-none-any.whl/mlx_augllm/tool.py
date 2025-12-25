from abc import ABC, abstractmethod

class Tool(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def description(self) -> str:
        pass
    
    # 必須から任意（デフォルト実装あり）に変更すると使いやすい
    def prepare_args(self, context: dict) -> dict:
        return {}

    def run(self, **kwargs):
        # 実際にはここで prepare_args の結果と kwargs をマージする等の処理が可能
        return self._run(**kwargs)
    
    @abstractmethod
    def _run(self, **kwargs):
        """
        継承先では必ず具体的な引数を定義すること。
        例: def _run(self, query: str, limit: int = 5):
        """
        pass