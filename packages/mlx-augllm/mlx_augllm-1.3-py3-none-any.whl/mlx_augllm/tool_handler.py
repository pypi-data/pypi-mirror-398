
from .function_calling import extract_tool_calls_from_yaml, cast_arguments

def _get_chat_response(llm, messages):
    """
    MLX のジェネレータから一括テキストを取得し、
    旧ロジック（辞書型）と互換性のある形式に変換する内部ヘルパー
    """
    full_text = ""
    # ツール選択時は stream=False で高速に一括取得
    gen = llm.generate(messages, images=None, stream=False)
    for response in gen:
        full_text += response.text
    return {"message": {"content": full_text}}

def select_tool(selector_llm, tool_dict, system_prompt: dict, user_message: dict, context: dict = None):
    """
    selector_llm: MlxLLMInterface のインスタンス
    tool_dict: 登録済みツールの辞書
    system_prompt: ツール用システムプロンプト
    user_message: ユーザーの入力メッセージ
    context: ユーザーID、名前、現在時刻などのシステムコンテキスト
    """
    messages = [system_prompt, user_message]
    context = context or {} # Noneの場合は空辞書に初期化
    
    # 1. LLMからツール呼び出し（YAML）を取得
    response_dict = _get_chat_response(selector_llm, messages)
    response_text = response_dict["message"]["content"]

    try:
        # 2. YAMLからツール名と引数を抽出
        tool_calls = extract_tool_calls_from_yaml(response_text)
        results = []
        
        if tool_calls:
            for call in tool_calls:
                name = call["function"]["name"]
                raw_llm_args = call["function"]["arguments"]
                
                tool = tool_dict.get(name)
                if tool:
                    # A. LLMが生成した引数を、_runのシグネチャに合わせて型キャスト
                    casted_args = cast_arguments(tool._run, raw_llm_args)
                    
                    # B. システムコンテキストから、ツールが必要とする固有引数を取得
                    # (例: user_id, current_time など LLM に教えたくない/教えられない情報)
                    system_args = tool.prepare_args(context)
                    
                    # C. 引数をマージ (システム側の引数で上書きすることで安全性を確保)
                    final_args = {**casted_args, **system_args}
                    
                    print(f"🛠️ Executing tool: {name}")
                    print(f"   - LLM args: {casted_args}")
                    print(f"   - System args: {system_args}")
                    
                    # 3. 最終的な引数でツールを実行
                    res = tool.run(**final_args)
                    results.append({"name": name, "result": res})
                    
        return results

    except ValueError as e:
        # YAMLが見つからない、または解析不能な場合は通常の会話として処理
        # print(f"DEBUG: No tool calls or parsing error: {e}")
        return []