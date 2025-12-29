"""底部工具栏"""

import json
import os
from pathlib import Path

from autocoder.common.tokens import count_string_tokens


def get_bottom_toolbar_func(
    get_mode_func,
    get_human_as_model_string_func,
    get_agentic_mode_string_func,
    plugin_manager,
):
    """创建底部工具栏函数

    Args:
        get_mode_func: 获取当前模式的函数
        get_human_as_model_string_func: 获取 human_as_model 字符串的函数
        get_agentic_mode_string_func: 获取 agentic_mode 字符串的函数
        plugin_manager: 插件管理器

    Returns:
        callable: 返回工具栏内容的函数
    """

    # 缓存：(conversation_id, message_count) → tokens_k_str
    _tokens_cache = {"key": None, "value": None}

    def get_bottom_toolbar():
        mode = get_mode_func()
        human_as_model = get_human_as_model_string_func()
        agentic_mode = get_agentic_mode_string_func()
        MODES = {
            "normal": "normal",
            "auto_detect": "nature language auto detect",
            "voice_input": "voice input",
            "shell": "shell",
        }
        if mode not in MODES:
            mode = "auto_detect"
        pwd = os.getcwd()
        pwd_parts = pwd.split(os.sep)
        if len(pwd_parts) > 3:
            pwd = os.sep.join(pwd_parts[-3:])

        plugin_info = (
            f"Plugins: {len(plugin_manager.plugins)}" if plugin_manager.plugins else ""
        )

        # 获取正在运行的 async 任务数量
        async_tasks_info = ""
        try:
            from autocoder.sdk.async_runner.task_metadata import TaskMetadataManager

            async_agent_dir = Path.home() / ".auto-coder" / "async_agent"
            meta_dir = async_agent_dir / "meta"

            if meta_dir.exists():
                metadata_manager = TaskMetadataManager(str(meta_dir))
                summary = metadata_manager.get_task_summary()
                running_count = summary.get("running", 0)

                if running_count > 0:
                    async_tasks_info = f" | Async Tasks: 🔄 {running_count}"
        except Exception:
            # 静默处理异常，不影响底部工具栏的显示
            pass

        # 获取会话信息
        session_info = ""
        try:
            from autocoder.common.conversations.get_conversation_manager import (
                get_conversation_manager,
            )

            manager = get_conversation_manager()
            current_id = manager.get_current_conversation_id()

            if current_id:
                # 获取当前会话的对话数量
                message_count = manager.get_message_count(current_id)
                # 截取 ID 的前 8 位以便显示
                short_id = current_id[:8] if len(current_id) > 8 else current_id

                # 使用缓存机制避免频繁计算 token
                cache_key = (current_id, message_count)

                if _tokens_cache["key"] == cache_key:
                    # 缓存命中
                    tokens_k_str = _tokens_cache["value"]
                else:
                    # 缓存未命中，重新计算
                    messages = manager.get_messages(current_id)
                    tokens = count_string_tokens(
                        json.dumps(messages, ensure_ascii=False)
                    )
                    tokens_k_str = f"{tokens / 1000:.1f}"
                    # 更新缓存
                    _tokens_cache["key"] = cache_key
                    _tokens_cache["value"] = tokens_k_str

                session_info = (
                    f"{short_id}({message_count},{tokens_k_str}k)"
                )
            else:
                session_info = ""
        except Exception:
            # 静默处理异常，不影响底部工具栏的显示
            pass

        return f"{session_info} | PWD: {pwd} \nInput: {MODES[mode]} | Human as Model: {human_as_model} | Agentic: {agentic_mode} {async_tasks_info} | {plugin_info}"

    return get_bottom_toolbar
