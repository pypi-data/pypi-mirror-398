import copy
import time
from typing import List, Optional, Dict
from mlx_vlm.utils import load_image

# 外部モジュールのインポート
from .mlx_llm_interface import MlxLLMInterface
from .prompt_builder import PromptBuilder
from .chat_memory import ChatMemory
from .tool_handler import select_tool
from .function_calling import register_tools, generate_system_prompt

#--------------------------------------------------------------------------------------------
# ツール実行とLLM推論を制御するメインクラス
#--------------------------------------------------------------------------------------------
class MlxAugmentedLLM:
    def __init__(
            self, 
            llm_interface: MlxLLMInterface, 
            prompt_builder: PromptBuilder,
            tools: List = None, 
            selector_interface: MlxLLMInterface = None,
            memory: ChatMemory = None):
        
        self.llm = llm_interface
        self.prompt_builder = prompt_builder
        
        # ツールの登録（Toolクラスのインスタンスリストを辞書化）
        self.tool_dict = register_tools(tools) if tools else None
        
        # ツール選択用LLM (メインと別モデル、または同一インスタンス)
        self.selector_llm = selector_interface or llm_interface

        # 記憶管理クラスの保持（渡されなければデフォルトを作成）
        self.memory = self.memory = memory or ChatMemory(max_memory=5)
        
        # 最後に実行された内容のレポート用
        self.report_text = None
        self.report_images = None
        self.report_data = None

    def _fix_mojibake(self, text: str) -> str:
        """Devstralや特定の日本語モデルで発生する制御文字化けを修復"""
        try:
            # Ġ -> 半角スペース, Ċ -> 改行
            text = text.replace('Ġ', ' ').replace('Ċ', '\n')
            return text.encode('latin-1').decode('utf-8')
        except:
            return text

    def _process_few_shot_images(self, few_shot_examples: List[Dict]):
        """Few-Shot内の画像パスをPIL Imageに変換し、リストを整理して返す"""
        if not few_shot_examples:
            return [], []
        
        processed = copy.deepcopy(few_shot_examples)
        all_few_shot_pils = []
        for msg in processed:
            if "images" in msg and msg["images"]:
                paths = msg["images"] if isinstance(msg["images"], list) else [msg["images"]]
                pils = [load_image(str(p)) for p in paths]
                msg["images"] = pils  # メッセージ内部をPIL置換
                all_few_shot_pils.extend(pils)
        return processed, all_few_shot_pils

    def build_user_message(self, text: str, images: Optional[List] = None) -> Dict:
        """MLX/VLM形式のユーザーメッセージ構造を構築"""
        # 画像があり、かつVLMインターフェースが有効な場合
        if images and self.llm.use_vision:
            content = [{"type": "text", "text": text}]
            for _ in images:
                content.append({"type": "image"})
            return {"role": "user", "content": content}
        
        # テキストのみの場合
        else:
            return {"role": "user", "content": text}

    def respond(self, user_text: str, 
                user_images: List = None, 
                few_shot_examples: List = None, 
                memory: List = None, 
                context: Dict = None, 
                stream: bool = False):
        """
        ユーザー入力に対してツール実行と回答生成を行うメインメソッド
        context: ツールに渡したいシステム側の情報（ユーザー名、ID、現在時刻など）
        """
        user_images = user_images or []
        few_shot_examples = few_shot_examples or []
        memory = memory or []
        context = context or {} 
        
        # 1. ツール選択・実行フェーズ
        tool_execution_results = None
        if self.tool_dict:
            # ツール選択用システムプロンプトの作成（YAMLルール）
            tool_select_prompt = generate_system_prompt(self.tool_dict)
            tool_select_system_msg = {"role": "system", "content": tool_select_prompt}
            
            # セレクター用のユーザーメッセージ準備（セレクターがVLMなら画像も考慮）
            pil_user_images = [load_image(str(p)) for p in user_images]
            selector_user_msg = self.build_user_message(
                user_text, 
                pil_user_images if self.selector_llm.use_vision else None
            )
            
            # ツール選択と実行（修正版：contextを渡す）
            tool_execution_results = select_tool(
                selector_llm=self.selector_llm,
                tool_dict=self.tool_dict,
                system_prompt=tool_select_system_msg,
                user_message=selector_user_msg,
                context=context
            )

        # 2. ツール実行結果の集計
        tool_context_text = ""
        tool_image_paths = []
        if tool_execution_results:
            formatted_results = []
            for res in tool_execution_results:
                name = res["name"]
                data = res["result"]
                status = data.get("status", "unknown")
                msg = data.get("message", "")
                
                if status == "success":
                    formatted_results.append(f"- ツール'{name}'の結果: {msg}")
                    # ツールが新しい画像パスを返してきた場合
                    if "images" in data and data["images"]:
                        tool_image_paths.extend(data["images"])
            
            if formatted_results:
                tool_context_text = "以下の内部情報を回答に含めてください:\n" + "\n".join(formatted_results)

        # 3. 最終生成用のメッセージリスト構築
        # システムプロンプト（ツール結果をRAGコンテキストとして注入）
        system_message = self.prompt_builder.build_system_message(
            rag_context_text=tool_context_text,
            use_vision=self.llm.use_vision
        )
        
        # Few-Shotデータの画像処理
        processed_few_shots, few_shot_pils = self._process_few_shot_images(few_shot_examples)

        # 過去の記憶を Memory クラスから取得
        processed_memory, memory_pils = self.memory.get_messages(use_vision=self.llm.use_vision)
        
        # 最終的なユーザーメッセージ（ユーザー画像 + ツール画像）
        final_user_image_paths = user_images + tool_image_paths
        pil_final_user_images = [load_image(str(p)) for p in final_user_image_paths]
        user_message = self.build_user_message(user_text, pil_final_user_images)
        
        # すべてを結合
        messages = [system_message] + processed_few_shots + processed_memory + [user_message]

        # 4. 全画像リストの整理（プロンプト内での出現順序を維持）
        all_pils = []
        if self.llm.use_vision:
            # システムメッセージに画像が含まれる場合
            if "pil_images" in system_message:
                all_pils.extend(system_message["pil_images"])
            # Few-Shot内の画像
            all_pils.extend(few_shot_pils)
            # メモリ内の画像
            all_pils.extend(memory_pils)
            # ユーザーおよびツールからの画像
            all_pils.extend(pil_final_user_images)

        # 5. 回答生成フェーズ
        full_reply = ""
        generator = self.llm.generate(
            messages, 
            images=all_pils if all_pils else None, 
            stream=stream
        )

        # ストリーミング応答
        if stream:
            for response in generator:
                chunk = response.text
                # 必要に応じて文字化け修復を適用
                # if self.llm.use_vision: chunk = self._fix_mojibake(chunk)
                full_reply += chunk
                yield chunk
        
        # 一括応答
        else:
            for response in generator:
                full_reply += response.text
            # if self.llm.use_vision: full_reply = self._fix_mojibake(full_reply)
            yield full_reply
        
        # 6. 記憶の更新（Memoryクラスに委譲）
        self.memory.add(
            user_text=user_text, 
            assistant_text=full_reply, 
            user_image_paths=final_user_image_paths
        )

        # 6. 後処理：レポートの更新
        self.report_text = full_reply
        self.report_images = final_user_image_paths