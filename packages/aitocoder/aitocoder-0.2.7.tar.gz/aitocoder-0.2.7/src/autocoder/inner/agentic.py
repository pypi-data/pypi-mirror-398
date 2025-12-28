import os
import uuid
import yaml
import json
import byzerllm
from typing import List, Dict, Any, Optional, Tuple, Union, Generator
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from copy import deepcopy
from loguru import logger as global_logger
from byzerllm.utils.str2model import to_model
from autocoder.index.filter.agentic_filter import AgenticFilterResponse

from autocoder.common import AutoCoderArgs
from autocoder.common.autocoderargs_parser import AutoCoderArgsParser
from autocoder.common.v2.agent.agentic_edit import AgenticEditRequest
from autocoder.common.v2.agent.agentic_edit_types import (
    AgenticEditConversationConfig,
    ConversationAction,
)
from autocoder.common.conversations.get_conversation_manager import (
    get_conversation_manager,
)
from autocoder.common.v2.agent.runner import (
    TerminalRunner,
    FileBasedEventRunner,
)
from autocoder.utils.llms import get_single_llm
from autocoder.common.ac_style_command_parser import parse_query
from autocoder.common.core_config import get_memory_manager
from autocoder.utils import get_last_yaml_file
from autocoder.auto_coder import main as auto_coder_main
from byzerllm.utils.nontext import Image

from autocoder.inner.async_command_handler import AsyncCommandHandler
from autocoder.inner.queue_command_handler import QueueCommandHandler
from autocoder.inner.conversation_command_handlers import (
    ConversationNewCommandHandler,
    ConversationResumeCommandHandler,
    ConversationListCommandHandler,
    ConversationRenameCommandHandler,
    ConversationCommandCommandHandler,
)


class RunAgentic:
    """处理 /auto 指令的核心类"""

    def __init__(self):
        """初始化 RunAgentic 类"""
        self._console = Console()

    def run(
        self,
        query: str,
        cancel_token: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        """
        处理/auto指令

        Args:
            query: 用户查询
            cancel_token: 取消令牌
            conversation_history: 对话历史

        Returns:
            conversation_id: 对话ID
        """
        # 1. 初始化上下文
        args, llm = self._initialize_context(query)
        if llm is None:
            return None

        # 2. 解析命令信息
        command_infos = parse_query(query)

        # 3. 处理命令链
        should_terminate, conversation_config = self._process_command_chain(
            query, args, command_infos
        )
        if should_terminate:
            # 如果命令已处理，返回相应的值
            if conversation_config is None:
                return None  # async/queue 命令已处理
            else:
                return conversation_config.conversation_id  # conversation 命令已处理

        # 4. 设置任务查询
        task_query = conversation_config.query if conversation_config.query else query
        if not conversation_config.query:
            conversation_config.query = task_query

        # 5. 确保对话ID存在
        conversation_id = self._ensure_conversation_id(conversation_config)

        # 6. 执行任务
        self._execute_runner(llm, args, conversation_config, task_query, cancel_token)

        # 7. 刷新文件列表
        self._refresh_completer()
        return conversation_id

    @byzerllm.prompt()
    def _filter_query_reminder(self) -> str:
        """
        ---
        [[REMINDER: You are in context discovery mode. Analyze the request above to identify relevant files, but DO NOT implement the request. Focus on thorough file discovery and understanding the codebase context.

        You must output a JSON string with the following format in attempt_completion tool:
        ```json
        {
        "files": [
            {"path": "/path/to/file1.py", "operation": "MODIFY"},
            {"path": "/path/to/file2.md", "operation": "REFERENCE"},
            {"path": "/path/to/new_file.txt", "operation": "ADD"},
            {"path": "/path/to/old_file.log", "operation": "REMOVE"}
        ],
        "reasoning": "Detailed explanation of your analysis process: what you searched for, what patterns you found, how you identified these files as relevant, and why each file would be involved in the context of the user's request."
        }
        ```
        ]]
        """

    @byzerllm.prompt()
    def _filter_plan(self) -> str:
        """
        You are a context discovery assistant. Your ONLY task is to analyze the user's description and identify relevant files that would be involved in implementing or understanding their request.

        IMPORTANT: You should NOT implement the user's request. Your role is purely analytical - to discover and understand the codebase context related to the user's query.

        Even if the user says "modify XXX" or "implement YYY", you should:
        1. Understand what files would be involved in such changes
        2. Identify related components, dependencies, and configuration files
        3. Find existing similar implementations for reference
        4. Locate test files and documentation that would be relevant

        Your analysis should be thorough but focused on FILE DISCOVERY, not task execution.

        You must output a JSON string in the attempt_completion tool with this exact format:
        ```json
        {
            "files": [
                {"path": "/path/to/file1.py", "operation": "MODIFY"},
                {"path": "/path/to/file2.md", "operation": "REFERENCE"},
                {"path": "/path/to/new_file.txt", "operation": "ADD"},
                {"path": "/path/to/old_file.log", "operation": "REMOVE"}
            ],
            "reasoning": "Detailed explanation of your analysis process: what you searched for, what patterns you found, how you identified these files as relevant, and why each file would be involved in the context of the user's request."
        }
        ```

        Operation types:
        - MODIFY: Files that would need changes
        - REFERENCE: Files to understand for context (dependencies, similar implementations, interfaces)
        - ADD: New files that would need to be created
        - REMOVE: Files that might need to be deleted or replaced
        """

    def filter(
        self, query: str, cancel_token: Optional[str] = None
    ) -> Optional[AgenticFilterResponse]:
        """
        处理/auto指令的过滤模式（用于发现相关文件）

        Args:
            query: 用户查询
            cancel_token: 取消令牌

        Returns:
            AgenticFilterResponse: 过滤结果
        """
        # 1. 初始化配置和LLM
        args = self._get_final_config()
        execute_file, _ = self._generate_new_yaml(query)
        args.file = execute_file

        llm = self._get_llm(args)
        if llm is None:
            return

        # 2. 创建对话配置
        conversation_config = AgenticEditConversationConfig(
            action=ConversationAction.RESUME
        )
        conversation_config.query = query

        # 3. 处理特殊对话操作
        if self._handle_conversation_actions(conversation_config):
            return conversation_config.conversation_id

        # 4. 创建新对话
        conversation_manager = get_conversation_manager()
        conversation_id = conversation_manager.create_conversation(
            name=query or "New Conversation",
            description=query or "New Conversation",
        )
        conversation_manager.set_current_conversation(conversation_id)
        conversation_config.conversation_id = conversation_id

        # 5. 配置过滤模式参数
        args_copy = deepcopy(args)
        args_copy.agentic_mode = "plan"
        args_copy.code_model = args.index_filter_model or args.model

        # 6. 执行文件发现
        runner = TerminalRunner(
            llm=llm,
            args=args_copy,
            conversation_config=conversation_config,
            cancel_token=cancel_token,
            system_prompt=self._filter_plan.prompt(),
        )
        result = runner.run(
            AgenticEditRequest(
                user_input=query + "\n" + self._filter_query_reminder.prompt(),
            )
        )

        return to_model(result, AgenticFilterResponse)

    def run_with_events(
        self,
        query: str,
        pre_commit: bool = False,
        post_commit: bool = False,
        pr: bool = False,
        extra_args: Dict[str, Any] = {},
        cancel_token: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        conversation_action: ConversationAction = ConversationAction.NEW,
        conversation_id: Optional[str] = None,
        is_sub_agent: bool = False,
    ) -> Generator[Any, None, None]:
        """
        处理/auto指令（事件流模式）

        Args:
            query: 用户查询
            pre_commit: 是否预提交
            post_commit: 是否后提交
            pr: 是否创建PR
            extra_args: 额外参数
            cancel_token: 取消令牌
            conversation_history: 对话历史
            system_prompt: 系统提示
            conversation_action: 对话动作
            conversation_id: 对话ID
            is_sub_agent: 是否为子代理

        Yields:
            event: 执行事件
        """
        # 1. 初始化配置和LLM
        args = self._get_final_config()

        # 覆盖默认配置，但不做持久化
        args.agentic_max_rounds = extra_args.get("max_turns", args.agentic_max_rounds)
        args.model = extra_args.get("model", args.model)
        args.code_model = args.model
        args.include_rules = extra_args.get("include_rules", False)

        global_logger.info(args)

        execute_file, _ = self._generate_new_yaml(query)
        args.file = execute_file

        llm = self._get_llm(args)
        if llm is None:
            return

        # 2. 创建对话配置
        conversation_config = AgenticEditConversationConfig(
            action=conversation_action,
            conversation_id=conversation_id,
            is_sub_agent=is_sub_agent,
        )

        # 3. 设置提交和PR选项
        if pre_commit:
            conversation_config.commit = True
        if post_commit:
            conversation_config.commit = True

        conversation_config.query = query
        conversation_config.pull_request = pr

        # 4. 处理对话管理
        self._setup_conversation_for_events(conversation_config, is_sub_agent)

        # 5. 注册取消令牌
        if cancel_token:
            from autocoder.common.global_cancel import global_cancel

            global_cancel.register_token(cancel_token)

        try:
            # 6. 执行事件流
            from autocoder.common.v2.agent.runner import SdkRunner

            runner = SdkRunner(
                llm=llm,
                args=args,
                conversation_config=conversation_config,
                system_prompt=system_prompt,
                cancel_token=cancel_token,
            )

            events = runner.run(AgenticEditRequest(user_input=query))

            for event in events:
                yield event

        finally:
            # 7. 清理
            self._refresh_completer()
            if cancel_token:
                from autocoder.common.global_cancel import global_cancel

                global_cancel.reset_token(cancel_token)

    # ==================== 内部辅助方法 ====================

    def _show_llm_error(self, error: Exception) -> None:
        """显示LLM配置错误"""
        self._console.print(
            Panel(
                f"[red]LLM Configuration Error:[/red]\n\n{str(error)}",
                title="[red]Error[/red]",
                border_style="red",
                padding=(1, 2),
            )
        )

    def _get_llm(self, args: AutoCoderArgs) -> Optional[Any]:
        """获取LLM实例"""
        try:
            return get_single_llm(
                args.code_model or args.model, product_mode=args.product_mode
            )
        except ValueError as e:
            self._show_llm_error(e)
            return None

    def _initialize_context(
        self, query: str
    ) -> Tuple[Optional[AutoCoderArgs], Optional[Any]]:
        """
        初始化运行上下文

        Args:
            query: 用户查询

        Returns:
            tuple: (args, llm) 如果成功，否则 (None, None)
        """
        args = self._get_final_config()

        execute_file, _ = self._generate_new_yaml(query)
        args.file = execute_file

        llm = self._get_llm(args)
        if llm is None:
            return None, None
        return args, llm

    def _process_command_chain(
        self, query: str, args: AutoCoderArgs, command_infos: Any
    ) -> Tuple[bool, Optional[AgenticEditConversationConfig]]:
        """
        处理命令链，使用责任链模式

        Args:
            query: 用户查询
            args: 配置参数
            command_infos: 命令信息

        Returns:
            tuple: (should_terminate, conversation_config)
                - should_terminate=True, conversation_config=None: async/queue已处理，返回None
                - should_terminate=True, conversation_config=obj: conversation handler已处理，返回conversation_id
                - should_terminate=False, conversation_config=obj: 继续执行后续逻辑
        """
        # 初始化对话配置
        conversation_config = AgenticEditConversationConfig(
            action=ConversationAction.RESUME
        )

        # 处理 async 指令
        async_handler = AsyncCommandHandler()
        async_result = async_handler.handle_async_command(query, args)
        if async_result is None:
            return True, None

        # 处理 queue 指令
        queue_handler = QueueCommandHandler()
        queue_result = queue_handler.handle_queue_command(query, args)
        if queue_result is None:
            return True, None

        # 处理 conversation handlers
        conversation_handlers = [
            (ConversationNewCommandHandler(), "handle_new_command"),
            (ConversationResumeCommandHandler(), "handle_resume_command"),
            (ConversationListCommandHandler(), "handle_list_command"),
            (ConversationRenameCommandHandler(), "handle_rename_command"),
        ]

        for handler, method_name in conversation_handlers:
            method = getattr(handler, method_name)
            result = method(query, conversation_config)
            if result is None:
                return True, conversation_config

        # 处理 command 指令
        command_handler = ConversationCommandCommandHandler()
        command_result = command_handler.handle_command_command(
            query, conversation_config, command_infos
        )
        if command_result is None:
            return True, conversation_config

        return False, conversation_config

    def _ensure_conversation_id(
        self, conversation_config: AgenticEditConversationConfig
    ) -> str:
        """
        确保对话ID存在

        Args:
            conversation_config: 对话配置

        Returns:
            str: 对话ID
        """
        if not conversation_config.conversation_id:
            conversation_manager = get_conversation_manager()
            conversation_id = conversation_manager.create_conversation(
                name=conversation_config.query or "New Conversation",
                description=conversation_config.query or "New Conversation",
            )
            conversation_manager.set_current_conversation(conversation_id)
            conversation_config.conversation_id = conversation_id

        return conversation_config.conversation_id

    def _execute_runner(
        self,
        llm: Any,
        args: AutoCoderArgs,
        conversation_config: AgenticEditConversationConfig,
        task_query: str,
        cancel_token: Optional[str],
    ) -> None:
        """
        根据运行模式执行相应的runner

        Args:
            llm: LLM实例
            args: 配置参数
            conversation_config: 对话配置
            task_query: 任务查询
            cancel_token: 取消令牌
        """
        from autocoder.run_context import get_run_context, RunMode

        runner_class = {
            RunMode.WEB: FileBasedEventRunner,
            RunMode.TERMINAL: TerminalRunner,
        }.get(get_run_context().mode)

        if runner_class:
            runner = runner_class(
                llm=llm,
                args=args,
                conversation_config=conversation_config,
                cancel_token=cancel_token,
            )
            runner.run(AgenticEditRequest(user_input=task_query))

    def _setup_conversation_for_events(
        self, conversation_config: AgenticEditConversationConfig, is_sub_agent: bool
    ) -> None:
        """
        为事件流模式设置对话管理

        Args:
            conversation_config: 对话配置
            is_sub_agent: 是否为子代理
        """
        conversation_manager = get_conversation_manager()

        # 处理 NEW 动作
        if conversation_config.action == ConversationAction.NEW:
            conversation_id = conversation_manager.create_conversation(
                name=conversation_config.query or "New Conversation",
                description=conversation_config.query or "New Conversation",
            )
            if not is_sub_agent:
                conversation_manager.set_current_conversation(conversation_id)
            conversation_config.conversation_id = conversation_id

        # 处理 RESUME 动作（有 conversation_id）
        elif (
            conversation_config.action == ConversationAction.RESUME
            and conversation_config.conversation_id
        ):
            if not is_sub_agent:
                conversation_manager.set_current_conversation(
                    conversation_config.conversation_id
                )

        # 处理 RESUME 动作（无 conversation_id，使用当前对话）
        elif (
            conversation_config.action == ConversationAction.RESUME
            and not conversation_config.conversation_id
            and conversation_manager.get_current_conversation_id()
        ):
            conversation_config.conversation_id = (
                conversation_manager.get_current_conversation_id()
            )
            if not is_sub_agent:
                conversation_manager.set_current_conversation(
                    conversation_config.conversation_id
                )

        # 处理 CONTINUE 动作
        elif conversation_config.action == ConversationAction.CONTINUE:
            conversation_config.conversation_id = (
                conversation_manager.get_current_conversation_id()
            )
            if not is_sub_agent:
                if conversation_config.conversation_id:
                    conversation_manager.set_current_conversation(
                        conversation_config.conversation_id
                    )
                else:
                    conversation_id = conversation_manager.create_conversation(
                        name=conversation_config.query or "New Conversation",
                        description=conversation_config.query or "New Conversation",
                    )
                    conversation_manager.set_current_conversation(conversation_id)
                    conversation_config.conversation_id = conversation_id

        # 确保有 conversation_id
        if not conversation_config.conversation_id:
            conversation_id = conversation_manager.create_conversation(
                name=conversation_config.query or "New Conversation",
                description=conversation_config.query or "New Conversation",
            )
            if not is_sub_agent:
                conversation_manager.set_current_conversation(conversation_id)
            conversation_config.conversation_id = conversation_id

    def _get_memory(self) -> Dict[str, Any]:
        """获取内存配置"""
        memory_manager = get_memory_manager()
        return memory_manager.get_memory_dict()

    def _get_final_config(self) -> AutoCoderArgs:
        """获取最终配置"""
        from autocoder.common.core_config import get_memory_manager

        memory_manager = get_memory_manager()
        conf = memory_manager.get_all_config()
        yaml_config = {
            "include_file": ["./base/base.yml"],
            "auto_merge": conf.get("auto_merge", "editblock"),
            "human_as_model": conf.get("human_as_model", "false") == "true",
            "skip_build_index": conf.get("skip_build_index", "true") == "true",
            "skip_confirm": conf.get("skip_confirm", "true") == "true",
            "silence": conf.get("silence", "true") == "true",
            "include_project_structure": conf.get("include_project_structure", "false")
            == "true",
            "exclude_files": memory_manager.get_exclude_files(),
        }
        for key, value in conf.items():
            converted_value = self._convert_config_value(key, value)
            if converted_value is not None:
                yaml_config[key] = converted_value

        temp_yaml = os.path.join("actions", f"{uuid.uuid4()}.yml")
        try:
            with open(temp_yaml, "w", encoding="utf-8") as f:
                f.write(self._convert_yaml_config_to_str(yaml_config=yaml_config))
            args = self._convert_yaml_to_config(temp_yaml)
        finally:
            if os.path.exists(temp_yaml):
                os.remove(temp_yaml)
        return args

    def _convert_config_value(self, key: str, value: Any) -> Any:
        """转换配置值"""
        # 定义需要使用 token 解析的字段
        token_fields = {
            "conversation_prune_safe_zone_tokens",
            "context_prune_safe_zone_tokens",
            "context_prune_sliding_window_size",
            "context_prune_sliding_window_overlap",
            "rag_params_max_tokens",
            "rag_context_window_limit",
            "rag_duckdb_vector_dim",
            "rag_duckdb_query_top_k",
            "rag_emb_dim",
            "rag_emb_text_size",
            "hybrid_index_max_output_tokens",
            "data_cells_max_num",
        }

        field_info = AutoCoderArgs.model_fields.get(key)
        if field_info:
            # 对于需要 token 解析的字段，使用 AutoCoderArgsParser
            if key in token_fields:
                try:
                    parser = AutoCoderArgsParser()
                    return parser.parse_token_field(key, value)
                except Exception as e:
                    print(
                        f"Warning: Failed to parse token field '{key}' with value '{value}': {e}"
                    )
                    # 如果解析失败，fallback 到原有逻辑
                    pass

            # 原有的类型转换逻辑
            if isinstance(value, str) and value.lower() in ["true", "false"]:
                return value.lower() == "true"
            elif "float" in str(field_info.annotation):
                return float(value)
            elif "int" in str(field_info.annotation):
                return int(value)
            else:
                return value
        else:
            print(f"Invalid configuration key: {key}")
            return None

    def _convert_yaml_config_to_str(self, yaml_config: Dict[str, Any]) -> str:
        """将YAML配置转换为字符串"""
        yaml_content = yaml.safe_dump(
            yaml_config,
            allow_unicode=True,
            default_flow_style=False,
            default_style=None,
        )
        return yaml_content

    def _convert_yaml_to_config(self, yaml_file: str) -> AutoCoderArgs:
        """将YAML文件转换为配置对象"""
        from autocoder.auto_coder import AutoCoderArgs, load_include_files, Template

        args = AutoCoderArgs()
        with open(yaml_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            config = load_include_files(config, yaml_file)
            for key, value in config.items():
                if key != "file":  # 排除 --file 参数本身
                    # key: ENV {{VARIABLE_NAME}}
                    if isinstance(value, str) and value.startswith("ENV"):
                        template = Template(value.removeprefix("ENV").strip())
                        value = template.render(os.environ)
                    setattr(args, key, value)
        return args

    def _generate_new_yaml(self, query: str) -> Tuple[str, AutoCoderArgs]:
        """生成新的YAML配置文件"""
        memory = self._get_memory()
        conf = memory.get("conf", {})
        current_files = memory.get("current_files", {}).get("files", [])
        auto_coder_main(["next", "chat_action"])
        latest_yaml_file = get_last_yaml_file("actions")
        if latest_yaml_file:
            yaml_config = {
                "include_file": ["./base/base.yml"],
                "auto_merge": conf.get("auto_merge", "editblock"),
                "human_as_model": conf.get("human_as_model", "false") == "true",
                "skip_build_index": conf.get("skip_build_index", "true") == "true",
                "skip_confirm": conf.get("skip_confirm", "true") == "true",
                "silence": conf.get("silence", "true") == "true",
                "include_project_structure": conf.get(
                    "include_project_structure", "false"
                )
                == "true",
                "exclude_files": memory.get("exclude_files", []),
            }
            yaml_config["context"] = ""
            for key, value in conf.items():
                converted_value = self._convert_config_value(key, value)
                if converted_value is not None:
                    yaml_config[key] = converted_value

            yaml_config["urls"] = current_files + self._get_llm_friendly_package_docs(
                return_paths=True
            )
            # handle image
            v = Image.convert_image_paths_from(query)
            yaml_config["query"] = v

            yaml_content = self._convert_yaml_config_to_str(yaml_config=yaml_config)

            execute_file = os.path.join("actions", latest_yaml_file)
            with open(os.path.join(execute_file), "w", encoding="utf-8") as f:
                f.write(yaml_content)
            return execute_file, self._convert_yaml_to_config(execute_file)

    def _get_llm_friendly_package_docs(
        self, package_name: Optional[str] = None, return_paths: bool = False
    ) -> List[str]:
        """获取LLM友好的包文档"""
        from autocoder.common.llm_friendly_package import get_package_manager

        package_manager = get_package_manager()
        return package_manager.get_docs(package_name, return_paths)

    def _handle_conversation_actions(
        self, conversation_config: AgenticEditConversationConfig
    ) -> bool:
        """
        处理对话列表和创建新对话的操作

        Args:
            conversation_config: 对话配置对象

        Returns:
            bool: 如果处理了特殊操作（LIST或NEW without input）返回True，否则返回False
        """
        if not conversation_config:
            return False

        console = Console()

        # 处理LIST操作
        if conversation_config.action == ConversationAction.LIST:
            conversation_manager = get_conversation_manager()
            conversations = conversation_manager.list_conversations()
            # 只保留 conversation_id 和 name 字段
            filtered_conversations = []
            for conv in conversations:
                filtered_conv = {
                    "conversation_id": conv.get("conversation_id"),
                    "name": conv.get("name"),
                }
                filtered_conversations.append(filtered_conv)

            # 格式化 JSON 输出，使用 JSON 格式渲染而不是 Markdown
            json_str = json.dumps(filtered_conversations, ensure_ascii=False, indent=4)
            console.print(
                Panel(
                    json_str,
                    title="\u2713 Task Completion",
                    border_style="green",
                    title_align="left",
                )
            )
            return True

        # 处理NEW操作且没有用户输入
        if (
            conversation_config.action == ConversationAction.NEW
            and not conversation_config.query.strip()
        ):
            conversation_manager = get_conversation_manager()
            conversation_id = conversation_manager.create_conversation(
                name=conversation_config.query or "New Conversation",
                description=conversation_config.query or "New Conversation",
            )
            conversation_manager.set_current_conversation(conversation_id)
            conversation_message = f"New conversation created: {conversation_manager.get_current_conversation_id()}"

            # 使用safe console print的简单版本
            try:
                console.print(
                    Panel(
                        Markdown(conversation_message),
                        title="\u2713 Task Completion",
                        border_style="green",
                        title_align="left",
                    )
                )
            except Exception:
                # fallback to plain text
                safe_content = conversation_message.replace("[", "\\[").replace(
                    "]", "\\]"
                )
                console.print(
                    Panel(
                        safe_content,
                        title="\u2713 Task Completion",
                        border_style="green",
                        title_align="left",
                    )
                )
            return True

        return False

    def _refresh_completer(self) -> None:
        """刷新命令补全器"""
        try:
            # 延迟导入，避免循环依赖

            # 获取全局 completer 实例
            # 注意：这里需要访问 auto_coder_runner 模块的全局变量
            # 由于我们不能修改 auto_coder_runner.py，所以这里直接导入
            import autocoder.auto_coder_runner as runner_module

            if hasattr(runner_module, "completer"):
                runner_module.completer.refresh_files()
        except Exception as e:
            global_logger.warning(f"Failed to refresh completer: {e}")
