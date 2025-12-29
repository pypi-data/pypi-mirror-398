import os
import platform
import tempfile
import threading
import subprocess
import shutil
import time
import re
from pathlib import Path
from typing import Optional, Union, Dict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from autocoder.common.international import get_message, get_message_with_format
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query
from autocoder.common.llms import LLMManager
from loguru import logger as global_logger


def _get_command_path(command: str) -> str:
    """
    获取命令的完整路径

    在 Windows 上，使用 shutil.which() 来查找可执行文件的完整路径，
    以解决 subprocess 在不使用 shell=True 时无法找到命令的问题。

    Args:
        command: 命令名称

    Returns:
        命令的完整路径
    """
    # 如果已经是完整路径，直接返回
    if os.path.isabs(command):
        return command

    # 使用 shutil.which() 查找命令
    full_path = shutil.which(command)
    if full_path:
        return full_path

    # 在 Windows 上，尝试添加 .exe 后缀
    if platform.system() == "Windows":
        full_path = shutil.which(f"{command}.exe")
        if full_path:
            return full_path

    # 如果找不到，返回原始命令（让后续错误处理来报告问题）
    return command


def _build_env() -> Dict[str, str]:
    """
    构建子进程环境变量

    在 Windows 上自动配置 UTF-8 相关环境变量，确保子进程使用 UTF-8 编码。

    Returns:
        合并后的环境变量字典
    """
    env = os.environ.copy()

    # Windows UTF-8 自动配置
    if platform.system() == "Windows":
        env.update(
            {
                "PYTHONIOENCODING": "utf-8",
                "LANG": "zh_CN.UTF-8",
                "LC_ALL": "zh_CN.UTF-8",
            }
        )

    return env


class AsyncCommandHandler:
    """处理 async 指令相关的操作"""

    def __init__(self):
        self.async_agent_dir = Path.home() / ".auto-coder" / "async_agent"
        self.console = Console()
        self._regular_config = None
        self._workflow_config = None
        # 维护每个 task_id 的停止信号
        self._stop_signals = {}  # task_id -> threading.Event
        self._stop_signals_lock = threading.Lock()  # 保护 _stop_signals 的线程锁

    def _parse_time_string(self, time_str: str) -> int:
        """
        解析时间字符串，支持 5s, 5m, 5h, 5d 格式

        Args:
            time_str: 时间字符串，如 "5s", "10m", "2h", "1d"

        Returns:
            时间的秒数

        Raises:
            ValueError: 如果时间格式不正确
        """
        time_str = time_str.strip()
        pattern = r"^(\d+)([smhd])$"
        match = re.match(pattern, time_str)

        if not match:
            raise ValueError(
                f"Invalid time format: {time_str}. Expected format: <number><unit>, "
                "where unit is one of: s (seconds), m (minutes), h (hours), d (days). "
                "Example: 5s, 10m, 2h, 1d"
            )

        value = int(match.group(1))
        unit = match.group(2)

        # 转换为秒
        multipliers = {
            "s": 1,  # 秒
            "m": 60,  # 分钟
            "h": 3600,  # 小时
            "d": 86400,  # 天
        }

        return value * multipliers[unit]

    def _create_regular_config(self):
        """创建常规 async 命令的类型化配置（支持 model、loop、time 等参数）"""
        if self._regular_config is None:
            self._regular_config = (
                create_config()
                .collect_remainder("query")
                .command("async")
                .max_args(0)
                .command("model")
                .positional("value", required=True)
                .max_args(1)
                .command("loop")
                .positional("value", type=int)
                .max_args(1)
                .command("effect")
                .positional("value", type=int)
                .max_args(1)
                .command("time")
                .positional("value", required=True)
                .max_args(1)
                .command("name")
                .positional("value", required=True)
                .max_args(1)
                .command("prefix")
                .positional("value", required=True)
                .max_args(1)
                .command("list")
                .max_args(0)
                .command("kill")
                .positional("task_id", required=True)
                .max_args(1)
                .command("task")
                .positional("task_id", required=False)
                .max_args(1)
                .command("drop")
                .positional("task_id", required=True)
                .max_args(1)
                .command("libs")
                .positional("value", required=True)
                .max_args(1)
                .command("help")
                .max_args(0)
                .build()
            )
        return self._regular_config

    def _create_workflow_config(self):
        """创建 workflow 模式的类型化配置（仅支持 workflow 和 name 参数，启用严格模式）"""
        if self._workflow_config is None:
            self._workflow_config = (
                create_config()
                .strict(True)  # 启用严格模式，未知命令将报错
                .collect_remainder("query")
                .command("async")
                .max_args(0)
                .command("workflow")
                .positional("value", required=True)
                .max_args(1)
                .command("name")
                .positional("value", required=True)
                .max_args(1)
                # 管理命令仍然需要支持
                .command("list")
                .max_args(0)
                .command("kill")
                .positional("task_id", required=True)
                .max_args(1)
                .command("task")
                .positional("task_id", required=False)
                .max_args(1)
                .command("drop")
                .positional("task_id", required=True)
                .max_args(1)
                .command("help")
                .max_args(0)
                .build()
            )
        return self._workflow_config

    def handle_async_command(self, query: str, args) -> Optional[Union[str, None]]:
        """
        处理 async 指令的主入口

        Args:
            query: 查询字符串，例如 "/async /model gpt-4 /loop 3 analysis task"
            args: 配置参数

        Returns:
            None: 表示处理了 async 指令，应该返回而不继续执行
            其他值: 表示没有处理 async 指令，应该继续执行
        """
        # 同时用两个 config 解析
        workflow_result = parse_typed_query(query, self._create_workflow_config())
        regular_result = parse_typed_query(query, self._create_regular_config())

        # 选择逻辑：
        # 1. 如果 workflow_result 包含 workflow 命令，使用 workflow 模式（即使有错误也要报告）
        # 2. 否则使用 regular_config 的结果
        if workflow_result.has_command("workflow"):
            result = workflow_result
        else:
            result = regular_result

        # 检查是否包含 async 命令
        if not result.has_command("async"):
            return "continue"  # 不是 async 指令，继续执行

        # 检查 help 命令
        if result.has_command("help"):
            return self._handle_help_command()

        # 检查各种子命令
        if result.has_command("list"):
            return self._handle_list_command()

        if result.has_command("kill"):
            return self._handle_kill_command(result)

        if result.has_command("task"):
            return self._handle_task_command(result)

        if result.has_command("drop"):
            return self._handle_drop_command(result)

        # 如果没有任何 query 且没有其他子命令，显示 help
        async_query = result.query or ""
        if not async_query.strip():
            return self._handle_help_command()

        # 处理异步任务执行
        return self._handle_async_execution(result, args)

    def _handle_help_command(self) -> str:
        """处理 help 子命令 - 显示帮助信息"""
        help_text = get_message("async_help_text")
        self.console.print(
            Panel(
                help_text,
                title=get_message("async_task_title"),
                border_style="blue",
            )
        )
        return None

    def _handle_list_command(self) -> None:
        """处理 list 子命令 - 显示任务列表"""
        meta_dir = os.path.join(self.async_agent_dir, "meta")

        try:
            # 导入并初始化任务元数据管理器
            from autocoder.sdk.async_runner.task_metadata import TaskMetadataManager

            metadata_manager = TaskMetadataManager(meta_dir)

            # 获取所有任务（已按创建时间排序，最新的在前）
            tasks = metadata_manager.list_tasks()[0:20]

            if not tasks:
                self.console.print(
                    Panel(
                        get_message("async_task_list_no_tasks"),
                        title=get_message("async_task_list_title"),
                        border_style="yellow",
                    )
                )
                return None

            # 创建表格
            table = Table(title=get_message("async_task_list_title"))
            table.add_column(
                get_message("async_task_table_id"), style="cyan", no_wrap=True
            )
            table.add_column(get_message("async_task_table_status"), style="green")
            table.add_column(get_message("async_task_table_model"), style="yellow")
            table.add_column(get_message("async_task_table_created"), style="blue")
            table.add_column(get_message("async_task_table_query"), style="white")
            table.add_column(get_message("async_task_table_log"), style="dim")

            # 添加任务行
            for task in tasks:
                # 状态颜色
                status_color = {
                    "running": get_message("async_task_status_running"),
                    "completed": get_message("async_task_status_completed"),
                    "failed": get_message("async_task_status_failed"),
                }.get(task.status, f"[white]{task.status}[/white]")

                # 格式化时间
                created_time = task.created_at.strftime("%Y-%m-%d %H:%M:%S")

                # 截取查询内容
                query_preview = (
                    task.user_query[:50] + "..."
                    if len(task.user_query) > 50
                    else task.user_query
                )

                # 日志文件路径
                log_file = task.log_file if task.log_file else "-"
                if log_file != "-" and len(log_file) > 30:
                    log_file = "..." + log_file[-27:]

                table.add_row(
                    task.task_id,
                    status_color,
                    task.model or "-",
                    created_time,
                    query_preview,
                    log_file,
                )

            self.console.print(table)

            # 显示汇总信息
            summary = metadata_manager.get_task_summary()
            self.console.print(
                Panel(
                    get_message_with_format(
                        "async_task_list_summary",
                        total=summary["total"],
                        completed=summary["completed"],
                        running=summary["running"],
                        failed=summary["failed"],
                    ),
                    title="📊 Summary",
                    border_style="blue",
                )
            )

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format("async_task_list_error", error=str(e)),
                    title=get_message("async_task_param_error"),
                    border_style="red",
                )
            )

        return None

    def _handle_kill_command(self, result) -> None:
        """处理 kill 子命令 - 终止任务"""
        kill_command = result.get_command("kill")
        if not kill_command or not kill_command.args:
            self.console.print(
                Panel(
                    get_message("async_provide_task_id"),
                    title=get_message("async_task_param_error"),
                    border_style="red",
                )
            )
            return None

        task_id = kill_command.args[0]
        meta_dir = os.path.join(self.async_agent_dir, "meta")

        try:
            # 导入并初始化任务元数据管理器
            from autocoder.sdk.async_runner.task_metadata import TaskMetadataManager

            metadata_manager = TaskMetadataManager(meta_dir)

            # 获取任务详情
            task = metadata_manager.load_task_metadata(task_id)

            if not task:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_task_not_found", task_id=task_id
                        ),
                        title=get_message("async_task_not_exist"),
                        border_style="red",
                    )
                )
                return None

            # 检查任务状态
            if task.status != "running":
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_task_cannot_terminate",
                            task_id=task_id,
                            status=task.status,
                        ),
                        title=get_message("async_task_status_error"),
                        border_style="yellow",
                    )
                )
                return None

            # 新的终止逻辑：先杀子进程，再杀主进程
            try:
                import psutil

                killed_processes = []

                # 0. 先设置停止信号，阻止后续迭代启动
                with self._stop_signals_lock:
                    if task_id not in self._stop_signals:
                        self._stop_signals[task_id] = threading.Event()
                    self._stop_signals[task_id].set()
                    global_logger.info(f"设置任务 {task_id} 的停止信号")

                # 1. 先终止子进程 (auto-coder.run)
                if task.sub_pid > 0:
                    if psutil.pid_exists(task.sub_pid):
                        try:
                            sub_process = psutil.Process(task.sub_pid)
                            self._terminate_process_tree(sub_process)
                            killed_processes.append(
                                f"子进程 {task.sub_pid} (auto-coder.run)"
                            )
                        except psutil.NoSuchProcess:
                            pass
                    else:
                        print(f"[DEBUG] 子进程 {task.sub_pid} 不存在")

                # 2. 再终止主进程 (main.py)
                if task.pid > 0:
                    if psutil.pid_exists(task.pid):
                        try:
                            main_process = psutil.Process(task.pid)
                            self._terminate_process_tree(main_process)
                            killed_processes.append(f"主进程 {task.pid} (main.py)")
                        except psutil.NoSuchProcess:
                            pass
                    else:
                        print(f"[DEBUG] 主进程 {task.pid} 不存在")

                # 更新任务状态
                task.update_status("failed", "Task manually terminated by user")
                metadata_manager.save_task_metadata(task)

                if killed_processes:
                    self.console.print(
                        Panel(
                            get_message_with_format(
                                "async_task_terminated_success",
                                task_id=task_id,
                                pid=f"已终止进程:\n"
                                + "\n".join(f"  - {p}" for p in killed_processes),
                            ),
                            title=get_message("async_terminate_success"),
                            border_style="green",
                        )
                    )
                else:
                    self.console.print(
                        Panel(
                            get_message_with_format(
                                "async_no_valid_pid", task_id=task_id
                            ),
                            title=get_message("async_terminate_warning"),
                            border_style="yellow",
                        )
                    )

            except ImportError:
                self.console.print(
                    Panel(
                        get_message("async_missing_psutil"),
                        title=get_message("async_dependency_missing"),
                        border_style="red",
                    )
                )
                return None

            except Exception as e:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_terminate_process_error", error=str(e)
                        ),
                        title=get_message("async_terminate_failed"),
                        border_style="red",
                    )
                )
                return None

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format("async_kill_command_error", error=str(e)),
                    title=get_message("async_processing_error"),
                    border_style="red",
                )
            )

        return None

    def _handle_task_command(self, result) -> None:
        """处理 task 子命令 - 显示特定任务详情"""
        task_command = result.get_command("task")
        meta_dir = os.path.join(self.async_agent_dir, "meta")

        try:
            # 导入并初始化任务元数据管理器
            from autocoder.sdk.async_runner.task_metadata import TaskMetadataManager

            metadata_manager = TaskMetadataManager(meta_dir)

            # 如果没有提供任务ID，自动获取最新的任务
            if not task_command or not task_command.args:
                tasks = metadata_manager.list_tasks()
                if not tasks:
                    self.console.print(
                        Panel(
                            get_message("async_task_list_no_tasks"),
                            title=get_message("async_task_param_error"),
                            border_style="red",
                        )
                    )
                    return None
                # 获取最新的任务（list_tasks已按创建时间排序，最新的在前）
                task_id = tasks[0].task_id
            else:
                task_id = task_command.args[0]

            # 获取任务详情
            task = metadata_manager.load_task_metadata(task_id)

            if not task:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_task_detail_not_found", task_id=task_id
                        ),
                        title=get_message("async_task_param_error"),
                        border_style="red",
                    )
                )
                return None

            self._display_task_details(task)

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format(
                        "async_task_detail_load_error", error=str(e)
                    ),
                    title=get_message("async_task_param_error"),
                    border_style="red",
                )
            )

        return None

    def _handle_drop_command(self, result) -> None:
        """处理 drop 子命令 - 删除任务及其相关文件"""
        drop_command = result.get_command("drop")
        if not drop_command or not drop_command.args:
            self.console.print(
                Panel(
                    get_message("async_provide_task_id"),
                    title=get_message("async_task_param_error"),
                    border_style="red",
                )
            )
            return None

        task_id = drop_command.args[0]
        meta_dir = os.path.join(self.async_agent_dir, "meta")

        try:
            # 导入并初始化任务元数据管理器
            from autocoder.sdk.async_runner.task_metadata import TaskMetadataManager

            metadata_manager = TaskMetadataManager(meta_dir)

            # 获取任务详情
            task = metadata_manager.load_task_metadata(task_id)

            if not task:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_task_not_found", task_id=task_id
                        ),
                        title=get_message("async_task_not_exist"),
                        border_style="red",
                    )
                )
                return None

            # 检查任务状态，如果是运行中的任务，需要先终止
            if task.status == "running":
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_task_drop_running_warning", task_id=task_id
                        ),
                        title=get_message("async_task_status_error"),
                        border_style="yellow",
                    )
                )

                # 询问用户是否要终止并删除
                try:
                    import psutil

                    # 先设置停止信号
                    with self._stop_signals_lock:
                        if task_id not in self._stop_signals:
                            self._stop_signals[task_id] = threading.Event()
                        self._stop_signals[task_id].set()
                        global_logger.info(f"设置任务 {task_id} 的停止信号（drop命令）")

                    # 再终止进程
                    killed_processes = []

                    if task.sub_pid > 0 and psutil.pid_exists(task.sub_pid):
                        try:
                            sub_process = psutil.Process(task.sub_pid)
                            self._terminate_process_tree(sub_process)
                            killed_processes.append(f"子进程 {task.sub_pid}")
                        except psutil.NoSuchProcess:
                            pass

                    if task.pid > 0 and psutil.pid_exists(task.pid):
                        try:
                            main_process = psutil.Process(task.pid)
                            self._terminate_process_tree(main_process)
                            killed_processes.append(f"主进程 {task.pid}")
                        except psutil.NoSuchProcess:
                            pass

                    if killed_processes:
                        self.console.print(
                            Panel(
                                get_message_with_format(
                                    "async_task_terminated_before_drop",
                                    task_id=task_id,
                                    processes="\n".join(
                                        f"  - {p}" for p in killed_processes
                                    ),
                                ),
                                title=get_message("async_terminate_success"),
                                border_style="green",
                            )
                        )

                except ImportError:
                    self.console.print(
                        Panel(
                            get_message("async_missing_psutil"),
                            title=get_message("async_dependency_missing"),
                            border_style="red",
                        )
                    )
                    return None

            # 删除任务相关的文件和目录
            deleted_items = []

            # 1. 清理 worktree 与对应分支
            if task.worktree_path and os.path.exists(task.worktree_path):
                try:
                    from autocoder.sdk.async_runner.worktree_manager import (
                        WorktreeManager,
                        WorktreeInfo,
                    )

                    worktree_path = Path(task.worktree_path)
                    manager = WorktreeManager(base_work_dir=str(self.async_agent_dir))

                    # 优先通过 list_worktrees 获取分支信息
                    worktree_info = None
                    try:
                        for wt in manager.list_worktrees():
                            if Path(wt.path).resolve() == worktree_path.resolve():
                                worktree_info = wt
                                break
                    except Exception as e:
                        global_logger.warning(
                            f"Failed to list worktrees when dropping task {task_id}: {e}"
                        )

                    # 回退：分支名与目录名一致（创建时即如此）
                    if worktree_info is None:
                        branch_name = worktree_path.name
                        worktree_info = WorktreeInfo(
                            name=branch_name,
                            path=str(worktree_path),
                            branch=branch_name,
                        )

                    # 规范化分支名，去掉 refs/heads/ 前缀（某些 git 输出为完整引用）
                    if isinstance(
                        worktree_info.branch, str
                    ) and worktree_info.branch.startswith("refs/heads/"):
                        normalized_branch = worktree_info.branch.split(
                            "refs/heads/", 1
                        )[1]
                        worktree_info = WorktreeInfo(
                            name=worktree_info.name,
                            path=worktree_info.path,
                            branch=normalized_branch,
                        )

                    # 使用 WorktreeManager 进行清理（同时移除 worktree 与分支）
                    manager.cleanup_worktree(worktree_info)
                    deleted_items.append(f"Git 分支: {worktree_info.branch}")
                    deleted_items.append(f"工作目录: {worktree_info.path}")
                except Exception as e:
                    # 兜底：若 git 清理失败，至少删除工作目录
                    try:
                        shutil.rmtree(task.worktree_path)
                        deleted_items.append(f"工作目录: {task.worktree_path}")
                    except Exception as e2:
                        global_logger.warning(
                            f"Failed to delete worktree {task.worktree_path}: {e2}"
                        )

            # 2. 删除日志文件
            if task.log_file and os.path.exists(task.log_file):
                try:
                    os.remove(task.log_file)
                    deleted_items.append(f"日志文件: {task.log_file}")
                except Exception as e:
                    global_logger.warning(
                        f"Failed to delete log file {task.log_file}: {e}"
                    )

            # 3. 删除任务元数据文件
            try:
                metadata_file = os.path.join(meta_dir, f"{task_id}.json")
                if os.path.exists(metadata_file):
                    os.remove(metadata_file)
                    deleted_items.append(f"元数据文件: {metadata_file}")
            except Exception as e:
                global_logger.warning(
                    f"Failed to delete metadata file {metadata_file}: {e}"
                )

            # 显示删除结果
            if deleted_items:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_task_drop_success",
                            task_id=task_id,
                            deleted_items="\n".join(
                                f"  ✓ {item}" for item in deleted_items
                            ),
                        ),
                        title=get_message("async_task_drop_title"),
                        border_style="green",
                    )
                )
            else:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_task_drop_no_files", task_id=task_id
                        ),
                        title=get_message("async_task_drop_title"),
                        border_style="yellow",
                    )
                )

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format("async_drop_command_error", error=str(e)),
                    title=get_message("async_processing_error"),
                    border_style="red",
                )
            )

        return None

    def _terminate_process_tree(self, process):
        """终止进程及其所有子进程"""
        try:
            import psutil

            # 获取所有子进程
            children = process.children(recursive=True)

            # 先终止所有子进程
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass

            # 终止主进程
            process.terminate()

            # 等待进程结束
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                # 强制杀死
                process.kill()
                for child in children:
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass

        except psutil.NoSuchProcess:
            # 进程已经不存在
            pass

    def _display_task_details(self, task):
        """显示任务详细信息"""
        # 状态颜色映射
        status_colors = {
            "running": get_message("async_task_status_running"),
            "completed": get_message("async_task_status_completed"),
            "failed": get_message("async_task_status_failed"),
        }
        status_display = status_colors.get(task.status, f"[white]{task.status}[/white]")

        # 创建任务基本信息面板
        yes_text = get_message("async_task_value_yes")
        no_text = get_message("async_task_value_no")

        basic_info = [
            f"[bold]{get_message('async_task_field_id')}:[/bold] [cyan]{task.task_id}[/cyan]",
            f"[bold]{get_message('async_task_field_status')}:[/bold] {status_display}",
            f"[bold]{get_message('async_task_field_model')}:[/bold] [yellow]{task.model or '-'}[/yellow]",
            f"[bold]{get_message('async_task_field_split_mode')}:[/bold] [blue]{task.split_mode or '-'}[/blue]",
            f"[bold]{get_message('async_task_field_bg_mode')}:[/bold] {yes_text if task.background_mode else no_text}",
            f"[bold]{get_message('async_task_field_pr_mode')}:[/bold] {yes_text if task.pull_request else no_text}",
            f"[bold]{get_message('async_task_field_created')}:[/bold] [blue]{task.created_at.strftime('%Y-%m-%d %H:%M:%S')}[/blue]",
        ]

        if task.completed_at:
            basic_info.append(
                f"[bold]{get_message('async_task_field_completed')}:[/bold] [blue]{task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}[/blue]"
            )

            # 计算耗时
            duration = task.completed_at - task.created_at
            total_seconds = int(duration.total_seconds())

            basic_info.append(
                f"[bold]{get_message('async_task_field_duration')}:[/bold] [cyan]{get_message_with_format('async_task_duration_format', duration=total_seconds)}[/cyan]"
            )

        self.console.print(
            Panel(
                "\n".join(basic_info),
                title=get_message("async_task_detail_title"),
                border_style="blue",
            )
        )

        # 显示用户查询内容
        self.console.print(
            Panel(
                f"[white]{task.user_query}[/white]",
                title=get_message("async_task_panel_query"),
                border_style="green",
            )
        )

        # 显示路径信息
        path_info = [
            f"[bold]{get_message('async_task_field_worktree_path')}:[/bold] [dim]{task.worktree_path}[/dim]",
            f"[bold]{get_message('async_task_field_original_path')}:[/bold] [dim]{task.original_project_path}[/dim]",
        ]

        if task.log_file:
            path_info.append(
                f"[bold]{get_message('async_task_field_log_file')}:[/bold] [dim]{task.log_file}[/dim]"
            )

        self.console.print(
            Panel(
                "\n".join(path_info),
                title=get_message("async_task_panel_paths"),
                border_style="cyan",
            )
        )

        # 显示错误信息（如果有）
        if task.error_message:
            self.console.print(
                Panel(
                    f"[red]{task.error_message}[/red]",
                    title=get_message("async_task_panel_error"),
                    border_style="red",
                )
            )

        # 显示执行结果（如果有）
        if task.execution_result:
            self._display_execution_result(task.execution_result)

        # 显示操作提示
        self._display_operation_hints(task)

    def _display_execution_result(self, result):
        """显示执行结果"""
        result_info = []

        if "success" in result:
            success_status = (
                get_message("async_task_value_yes")
                if result["success"]
                else get_message("async_task_value_no")
            )
            result_info.append(
                f"[bold]{get_message('async_task_field_success')}:[/bold] {success_status}"
            )

        if result.get("output"):
            output_preview = result["output"]
            result_info.append(
                f"[bold]{get_message('async_task_field_output_preview')}:[/bold]\n[dim]{output_preview}[/dim]"
            )

        if result.get("error"):
            error_preview = result["error"]
            result_info.append(
                f"[bold]{get_message('async_task_field_error_preview')}:[/bold]\n[red]{error_preview}[/red]"
            )

        if result_info:
            self.console.print(
                Panel(
                    "\n\n".join(result_info),
                    title=get_message("async_task_panel_execution"),
                    border_style="yellow",
                )
            )

    def _display_operation_hints(self, task):
        """显示操作提示"""
        actions = []
        if task.log_file and os.path.exists(task.log_file):
            actions.append(
                get_message_with_format(
                    "async_task_hint_view_log", log_file=task.log_file
                )
            )

        if task.worktree_path and os.path.exists(task.worktree_path):
            actions.append(
                get_message_with_format(
                    "async_task_hint_enter_worktree", worktree_path=task.worktree_path
                )
            )

        actions.append(get_message("async_task_hint_back_to_list"))

        self.console.print(
            Panel(
                "\n".join(actions),
                title=get_message("async_task_operation_hints"),
                border_style="dim",
            )
        )

    def _check_task_conflict(self, worktree_name: str):
        """
        检查是否存在同名任务冲突

        Args:
            worktree_name: 工作树名称（也是任务ID）

        Returns:
            Optional[TaskMetadata]: 如果发现冲突的任务返回该任务，否则返回None
        """
        meta_dir = os.path.join(self.async_agent_dir, "meta")

        try:
            from autocoder.sdk.async_runner.task_metadata import TaskMetadataManager

            metadata_manager = TaskMetadataManager(meta_dir)

            # 获取所有正在运行的任务
            running_tasks = metadata_manager.list_tasks(status_filter="running")

            # 检查是否有同名的任务正在运行
            for task in running_tasks:
                if task.task_id == worktree_name:
                    return task

            return None

        except Exception as e:
            global_logger.warning(f"检查任务冲突时出错: {e}")
            return None

    def _handle_async_execution(self, result, args) -> None:
        """处理异步任务执行"""
        # 检查是否有解析错误
        errors = result.get_errors()
        if errors:
            error_messages = []
            for cmd_name, cmd_errors in errors.items():
                error_messages.append(f"[bold]{cmd_name}[/bold]:")
                for error in cmd_errors:
                    error_messages.append(f"  - {error}")

            self.console.print(
                Panel(
                    "\n".join(error_messages),
                    title=get_message("async_task_param_error"),
                    border_style="red",
                )
            )
            return None

        # 解析参数
        async_query = result.query or ""

        # 优先检查是否为 workflow 模式
        if result.has_command("workflow"):
            workflow_name = result.workflow

            # workflow 模式仍需要 /name 参数
            worktree_name = ""
            if result.has_command("name"):
                worktree_name = result.name

            if not worktree_name:
                self.console.print(
                    Panel(
                        get_message("async_name_required"),
                        title=get_message("async_task_param_error"),
                        border_style="red",
                    )
                )
                return None

            # 检查同名任务冲突
            conflicting_task = self._check_task_conflict(worktree_name)
            if conflicting_task:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_task_name_conflict",
                            task_id=worktree_name,
                            existing_status=conflicting_task.status,
                            existing_created=conflicting_task.created_at.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        ),
                        title=get_message("async_task_conflict_title"),
                        border_style="red",
                    )
                )
                return None

            # 执行 workflow 任务（不支持 loop/time）
            self._execute_async_workflow_task(
                async_query=async_query,
                workflow=workflow_name,
                worktree_name=worktree_name,
            )
            return None

        # 常规模式需要模型参数
        model = args.code_model or args.model

        # 从解析结果中获取参数
        if result.has_command("model"):
            model = result.model

        # 检查模型是否存在
        if model:
            try:
                lm = LLMManager()
                if not lm.check_model_exists(model):
                    self.console.print(
                        Panel(
                            get_message_with_format(
                                "async_model_not_found", model=model
                            ),
                            title=get_message("async_model_config_error"),
                            border_style="red",
                        )
                    )
                    return None

                # 检查模型是否已配置密钥
                if not lm.has_key(model):
                    self.console.print(
                        Panel(
                            get_message_with_format(
                                "async_model_key_missing", model=model
                            ),
                            title=get_message("async_model_config_error"),
                            border_style="red",
                        )
                    )
                    return None

            except Exception as e:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_model_check_error", model=model, error=str(e)
                        ),
                        title=get_message("async_model_config_error"),
                        border_style="red",
                    )
                )
                return None
        else:
            self.console.print(
                Panel(
                    get_message("async_model_required"),
                    title=get_message("async_task_param_error"),
                    border_style="red",
                )
            )
            return None

        task_prefix = ""
        if result.has_command("prefix"):
            task_prefix = result.prefix

        worktree_name = ""
        if result.has_command("name"):
            worktree_name = result.name

        # 检查是否提供了 /name 参数，如果没有则报错
        if not worktree_name:
            self.console.print(
                Panel(
                    get_message("async_name_required"),
                    title=get_message("async_task_param_error"),
                    border_style="red",
                )
            )
            return None

        # 检查同名任务冲突
        conflicting_task = self._check_task_conflict(worktree_name)
        if conflicting_task:
            self.console.print(
                Panel(
                    get_message_with_format(
                        "async_task_name_conflict",
                        task_id=worktree_name,
                        existing_status=conflicting_task.status,
                        existing_created=conflicting_task.created_at.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    ),
                    title=get_message("async_task_conflict_title"),
                    border_style="red",
                )
            )
            return None

        loop_count = 1
        max_duration_seconds = None

        if result.has_command("time"):
            # 检查 time 参数是否提供了值
            time_value = result.time
            if not time_value:
                self.console.print(
                    Panel(
                        get_message("async_time_param_required"),
                        title=get_message("async_task_param_error"),
                        border_style="red",
                    )
                )
                return None

            # 如果设置了 time 参数，解析时间并设置一个很大的 loop_count
            try:
                max_duration_seconds = self._parse_time_string(time_value)
                loop_count = 100000
                global_logger.info(
                    f"Time-based execution enabled: will run for {max_duration_seconds} seconds (max {loop_count} iterations)"
                )
            except ValueError as e:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_time_param_format_error", time_str=time_value
                        ),
                        title=get_message("async_task_param_error"),
                        border_style="red",
                    )
                )
                return None
        elif result.has_command("loop"):
            loop_count = result.loop
        elif result.has_command("effect"):
            loop_count = result.effect

        include_libs = ""
        if result.has_command("libs"):
            include_libs = result.libs

        # 执行异步任务
        self._execute_async_task(
            async_query,
            model,
            task_prefix,
            worktree_name,
            loop_count,
            include_libs,
            max_duration_seconds,
        )
        return None

    def _execute_async_task(
        self,
        async_query: str,
        model: str,
        task_prefix: str,
        worktree_name: str,
        loop_count: int,
        include_libs: str = "",
        max_duration_seconds: Optional[int] = None,
    ):
        """执行异步任务"""
        # 为该任务创建停止信号
        task_id = worktree_name  # task_id 即为 worktree_name
        with self._stop_signals_lock:
            if task_id not in self._stop_signals:
                self._stop_signals[task_id] = threading.Event()
            # 清除可能残留的旧信号（确保是未设置状态）
            self._stop_signals[task_id].clear()
            global_logger.info(f"为任务 {task_id} 创建停止信号")

        # 创建临时文件并写入查询内容
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(async_query)
            tmp_file_path = tmp_file.name

        # 如果是多轮，则需要改善下提示词
        loop_query = f"{async_query}\n\nAdditional instruction: use git log to get the code changes generated by previous tasks and try to focus on iterative improvements and refinements and make sure to use git commit command to make a commit after every single file edit."
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp_file_loop:
            tmp_file_loop.write(loop_query)
            tmp_file_loop_path = tmp_file_loop.name

        def run_async_command():
            """在后台线程中执行异步命令"""

            def execute(index: int):
                target_file = tmp_file_path
                if index > 0:
                    target_file = tmp_file_loop_path

                # 构建命令参数列表（跨平台兼容，不使用 shell 管道）
                cmd_args = [
                    _get_command_path("auto-coder.run"),
                    "--async",
                    "--include-rules",
                    "--model",
                    model,
                    "--verbose",
                    "--is-sub-agent",
                    "--worktree-name",
                    worktree_name,
                ]
                if task_prefix:
                    cmd_args.extend(["--task-prefix", task_prefix])
                if include_libs:
                    cmd_args.extend(["--include-libs", include_libs])

                # 读取输入文件内容
                with open(target_file, "r", encoding="utf-8") as f:
                    input_content = f.read()

                # 执行命令
                if index == 0:
                    global_logger.info(
                        f"Executing async command {index}: {' '.join(cmd_args)}  async_query: {async_query}"
                    )
                else:
                    global_logger.info(
                        f"Executing async command {index}: {' '.join(cmd_args)}  async_query: {loop_query}"
                    )

                # 使用 input 参数传递文件内容（跨平台兼容，替代 cat | 管道）
                v = subprocess.run(
                    cmd_args,
                    input=input_content,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=_build_env(),
                )
                global_logger.info(f"Async command result: {v.stdout}")

            try:
                # 如果设置了时间限制，记录开始时间
                start_time = time.time() if max_duration_seconds is not None else None

                for i in range(loop_count):
                    # 每轮执行前检查停止信号
                    with self._stop_signals_lock:
                        stop_event = self._stop_signals.get(task_id)

                    if stop_event and stop_event.is_set():
                        global_logger.info(
                            f"任务 {task_id} 收到停止信号，终止执行。已完成 {i} 次迭代。"
                        )
                        break

                    execute(i)

                    # 如果设置了时间限制，检查是否超时
                    if start_time is not None:
                        elapsed_time = time.time() - start_time
                        if elapsed_time >= max_duration_seconds:
                            global_logger.info(
                                f"Time limit reached: {elapsed_time:.2f} seconds >= {max_duration_seconds} seconds. "
                                f"Completed {i + 1} iterations."
                            )
                            break
                        else:
                            remaining_time = max_duration_seconds - elapsed_time
                            global_logger.info(
                                f"Iteration {i + 1} completed. Elapsed: {elapsed_time:.2f}s, Remaining: {remaining_time:.2f}s"
                            )
            except Exception as e:
                global_logger.error(f"Error executing async command: {e}")
            finally:
                # 删除临时文件
                try:
                    os.remove(tmp_file_path)
                    os.remove(tmp_file_loop_path)
                except:
                    pass

                # 清理停止信号
                with self._stop_signals_lock:
                    if task_id in self._stop_signals:
                        del self._stop_signals[task_id]
                        global_logger.info(f"清理任务 {task_id} 的停止信号")

        # 在新线程中启动异步任务
        thread = threading.Thread(target=run_async_command, daemon=True)
        thread.start()

        # 打印任务信息
        query_preview = async_query[:100] + ("..." if len(async_query) > 100 else "")

        # 根据是否有 name 参数选择不同的消息格式
        tasks_dir = self.async_agent_dir / "tasks" / worktree_name
        meta_file = self.async_agent_dir / "meta" / f"{worktree_name}.json"
        if worktree_name:
            message_content = get_message_with_format(
                "async_task_started_message_with_name",
                model=model,
                query=query_preview,
                name=worktree_name,
                tasks_dir=str(tasks_dir),
                meta_file=str(meta_file),
                agent_dir=self.async_agent_dir,
            )
        else:
            message_content = get_message_with_format(
                "async_task_started_message",
                model=model,
                query=query_preview,
                agent_dir=self.async_agent_dir,
            )

        self.console.print(
            Panel(
                message_content,
                title=get_message("async_task_title"),
                border_style="green",
            )
        )

    def _execute_async_workflow_task(
        self,
        async_query: str,
        workflow: str,
        worktree_name: str,
    ):
        """执行异步 workflow 任务（单次执行，不支持循环）"""
        # 为该任务创建停止信号
        task_id = worktree_name
        with self._stop_signals_lock:
            if task_id not in self._stop_signals:
                self._stop_signals[task_id] = threading.Event()
            # 清除可能残留的旧信号（确保是未设置状态）
            self._stop_signals[task_id].clear()
            global_logger.info(f"为任务 {task_id} 创建停止信号（workflow 模式）")

        # 创建临时文件并写入查询内容
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(async_query)
            tmp_file_path = tmp_file.name

        def run_async_workflow_command():
            """在后台线程中执行异步 workflow 命令"""
            try:
                # 检查停止信号
                with self._stop_signals_lock:
                    stop_event = self._stop_signals.get(task_id)

                if stop_event and stop_event.is_set():
                    global_logger.info(f"任务 {task_id} 收到停止信号，取消执行。")
                    return

                # 构建命令参数列表（跨平台兼容，不使用 shell 管道）
                cmd_args = [
                    _get_command_path("auto-coder.run"),
                    "--async",
                    "--workflow",
                    workflow,
                    "--include-rules",
                    "--worktree-name",
                    worktree_name,
                ]

                # 读取输入文件内容
                with open(tmp_file_path, "r", encoding="utf-8") as f:
                    input_content = f.read()

                global_logger.info(
                    f"Executing async workflow command: {' '.join(cmd_args)}  async_query: {async_query}"
                )

                # 执行命令（跨平台兼容，使用 input 参数替代 cat | 管道）
                v = subprocess.run(
                    cmd_args,
                    input=input_content,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=_build_env(),
                )
                global_logger.info(f"Async workflow command result: {v.stdout}")

            except Exception as e:
                global_logger.error(f"Error executing async workflow command: {e}")
            finally:
                # 删除临时文件
                try:
                    os.remove(tmp_file_path)
                except:
                    pass

                # 清理停止信号
                with self._stop_signals_lock:
                    if task_id in self._stop_signals:
                        del self._stop_signals[task_id]
                        global_logger.info(
                            f"清理任务 {task_id} 的停止信号（workflow 模式）"
                        )

        # 在新线程中启动异步任务
        thread = threading.Thread(target=run_async_workflow_command, daemon=True)
        thread.start()

        # 打印任务信息
        query_preview = async_query[:100] + ("..." if len(async_query) > 100 else "")
        tasks_dir = self.async_agent_dir / "tasks" / worktree_name
        meta_file = self.async_agent_dir / "meta" / f"{worktree_name}.json"

        message_content = get_message_with_format(
            "async_task_started_message_with_name",
            model="-",  # workflow 模式不显示模型
            query=query_preview,
            name=worktree_name,
            tasks_dir=str(tasks_dir),
            meta_file=str(meta_file),
            agent_dir=self.async_agent_dir,
        )

        self.console.print(
            Panel(
                message_content,
                title=get_message("async_task_title"),
                border_style="green",
            )
        )
