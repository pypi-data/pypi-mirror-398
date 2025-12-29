import os
import json
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel
from autocoder.common import AutoCoderArgs
from loguru import logger


class RAGConfig(BaseModel):
    """RAG 配置项模型"""

    name: str
    server_name: str  # 实际的服务器地址，如 http://127.0.0.1:8107/v1
    api_key: Optional[str] = None
    description: Optional[str] = None


class RAGManager:
    """RAG 管理器，用于读取和管理 RAG 服务器配置"""

    # 默认的内置 RAG 配置名称
    CONVERSATION = "conversation"
    CODEBASE = "codebase"

    # 协议前缀
    BUILTIN_PREFIX = "builtin://"
    LOCAL_PREFIX = "local://"

    def __init__(self, args: AutoCoderArgs):
        self.args = args
        self.configs: List[RAGConfig] = []
        self._load_configs()
        self._add_default_rags()

    def _load_configs(self):
        """加载 RAG 配置，优先从项目配置，然后从全局配置"""
        # 优先读取项目级别配置
        base_path = Path(self.args.source_dir) if self.args.source_dir else Path.cwd()
        project_config_path = (
            base_path / ".auto-coder" / "auto-coder.web" / "rags" / "rags.json"
        )

        if project_config_path.exists():
            logger.info(f"正在加载项目级别 RAG 配置: {project_config_path}")
            self._load_project_config(str(project_config_path))
        else:
            logger.info("未找到项目级别 RAG 配置，尝试加载全局配置")
            # 读取全局配置（使用 pathlib 确保跨平台兼容性）
            global_config_path = Path.home() / ".auto-coder" / "keys" / "rags.json"
            if global_config_path.exists():
                logger.info(f"正在加载全局 RAG 配置: {global_config_path}")
                self._load_global_config(str(global_config_path))
            else:
                logger.warning("未找到任何 RAG 配置文件")

    def _load_project_config(self, config_path: str):
        """加载项目级别的 RAG 配置"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            if "data" in config_data and isinstance(config_data["data"], list):
                for item in config_data["data"]:
                    try:
                        rag_config = RAGConfig(
                            name=item.get("name", ""),
                            server_name=item.get("base_url", ""),
                            api_key=item.get("api_key"),
                            description=item.get("description"),
                        )
                        self.configs.append(rag_config)
                        logger.info(
                            f"已加载 RAG 配置: {rag_config.name} -> {rag_config.server_name}"
                        )
                    except Exception as e:
                        logger.error(
                            f"解析项目级别 RAG 配置项时出错: {e}, 配置项: {item}"
                        )
            else:
                logger.error(
                    f"项目级别 RAG 配置格式错误，缺少 'data' 字段或 'data' 不是列表"
                )

        except json.JSONDecodeError as e:
            logger.error(f"项目级别 RAG 配置文件 JSON 格式错误: {e}")
        except Exception as e:
            logger.error(f"读取项目级别 RAG 配置文件时出错: {e}")

    def _load_global_config(self, config_path: str):
        """加载全局级别的 RAG 配置"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            if "data" in config_data and isinstance(config_data["data"], list):
                for item in config_data["data"]:
                    try:
                        rag_config = RAGConfig(
                            name=item.get("name", ""),
                            server_name=item.get("base_url", ""),
                            api_key=item.get("api_key"),
                            description=item.get("description"),
                        )
                        self.configs.append(rag_config)
                        logger.info(
                            f"已加载 RAG 配置: {rag_config.name} -> {rag_config.server_name}"
                        )
                    except Exception as e:
                        logger.error(f"解析全局 RAG 配置项时出错: {e}, 配置项: {item}")
            else:
                logger.error(
                    f"全局 RAG 配置格式错误，缺少 'data' 字段或 'data' 不是列表"
                )

        except json.JSONDecodeError as e:
            logger.error(f"全局 RAG 配置文件 JSON 格式错误: {e}")
        except Exception as e:
            logger.error(f"读取全局 RAG 配置文件时出错: {e}")

    def get_all_configs(self) -> List[RAGConfig]:
        """获取所有 RAG 配置"""
        return self.configs

    def get_config_by_name(self, name: str) -> Optional[RAGConfig]:
        """根据名称获取特定的 RAG 配置"""
        for config in self.configs:
            if config.name == name:
                return config
        return None

    def get_server_names(self) -> List[str]:
        """获取所有服务器名称列表"""
        return [config.server_name for config in self.configs]

    def get_config_info(self) -> str:
        """获取格式化的配置信息，用于显示"""
        if not self.configs:
            return "### RAG_SERVER_LIST\n No available RAG server configurations found"

        info_lines = []
        info_lines.append("### RAG_SERVER_LIST\nAvailable RAG server configurations")

        for i, config in enumerate(self.configs, 1):
            info_lines.append(f"\n{i}. Configuration name: {config.name}")
            info_lines.append(f"   Server address: {config.server_name}")

            if config.description:
                info_lines.append(f"   Description: {config.description}")
            else:
                info_lines.append(f"   Description: None")

            if i < len(self.configs):
                info_lines.append("-" * 30)

        return "\n".join(info_lines)

    def has_configs(self) -> bool:
        """检查是否有可用的配置"""
        return len(self.configs) > 0

    def _add_default_rags(self):
        """添加默认的 RAG 配置"""
        # 添加会话知识库
        conversation_rag = RAGConfig(
            name=self.CONVERSATION,
            server_name="builtin://conversation",
            description="Knowledge base of project's historical conversations. Use _conversation_ knowledge base when you need to recall what was discussed before.",
        )
        self.configs.append(conversation_rag)
        logger.info(f"已添加默认 RAG 配置: {self.CONVERSATION}")

        # 只有配置了 codebase_rag_suffixs 才添加代码知识库
        if self.args.codebase_rag_suffixs:
            code_rag = RAGConfig(
                name=self.CODEBASE,
                server_name="builtin://codebase",
                description="Knowledge base of current project's source code. Use _codebase_ knowledge base when you want to query project code-related content.",
            )
            self.configs.append(code_rag)
            logger.info(
                f"已添加默认 RAG 配置: {self.CODEBASE} (文件后缀: {self.args.codebase_rag_suffixs})"
            )
        else:
            logger.info(f"未配置 codebase_rag_suffixs，跳过 {self.CODEBASE} RAG 的注册")

    def is_builtin_rag(self, name: str) -> bool:
        """检查是否为内置 RAG（通过名称）"""
        return name in [self.CONVERSATION, self.CODEBASE]

    def is_builtin_server(self, server_name: str) -> bool:
        """检查 server_name 是否为内置 RAG 协议"""
        return server_name.startswith(self.BUILTIN_PREFIX)

    def is_local_server(self, server_name: str) -> bool:
        """检查 server_name 是否为本地 RAG 协议"""
        return server_name.startswith(self.LOCAL_PREFIX)

    def get_local_path(self, server_name: str) -> str:
        """从 local:// 协议中提取本地路径"""
        if not self.is_local_server(server_name):
            raise ValueError(f"server_name 不是 local:// 协议: {server_name}")
        return server_name[len(self.LOCAL_PREFIX) :]

    def get_local_configs(self) -> List[RAGConfig]:
        """获取所有 local:// 协议的 RAG 配置"""
        return [c for c in self.configs if self.is_local_server(c.server_name)]

    def _get_project_config_path(self) -> Path:
        """获取项目级别配置文件路径"""
        base_path = Path(self.args.source_dir) if self.args.source_dir else Path.cwd()
        return base_path / ".auto-coder" / "auto-coder.web" / "rags" / "rags.json"

    def _load_config_file(self, config_path: Path) -> dict:
        """加载配置文件内容"""
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"data": []}

    def _save_config_file(self, config_path: Path, config_data: dict):
        """保存配置文件"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

    def add_local_rag(
        self, name: str, path: str, description: Optional[str] = None
    ) -> bool:
        """
        添加本地 RAG 配置到项目配置文件

        Args:
            name: 配置名称
            path: 本地路径
            description: 描述信息

        Returns:
            bool: 是否添加成功
        """
        config_path = self._get_project_config_path()
        config_data = self._load_config_file(config_path)

        # 检查是否已存在同名配置
        for item in config_data.get("data", []):
            if item.get("name") == name:
                logger.warning(f"已存在同名 RAG 配置: {name}")
                return False

        # 构建 server_name
        server_name = f"{self.LOCAL_PREFIX}{path}"

        # 添加新配置
        new_config = {
            "name": name,
            "base_url": server_name,
            "description": description or f"Local RAG: {path}",
        }
        config_data.setdefault("data", []).append(new_config)

        # 保存配置文件
        self._save_config_file(config_path, config_data)
        logger.info(f"已添加本地 RAG 配置: {name} -> {server_name}")

        # 更新内存中的配置
        rag_config = RAGConfig(
            name=name,
            server_name=server_name,
            description=new_config["description"],
        )
        self.configs.append(rag_config)

        return True

    def remove_local_rag(self, name: str) -> bool:
        """
        从项目配置文件中删除本地 RAG 配置

        Args:
            name: 配置名称

        Returns:
            bool: 是否删除成功
        """
        config_path = self._get_project_config_path()
        config_data = self._load_config_file(config_path)

        # 查找并删除配置
        data_list = config_data.get("data", [])
        original_len = len(data_list)

        # 只删除 local:// 协议的配置
        config_data["data"] = [
            item
            for item in data_list
            if not (
                item.get("name") == name
                and item.get("base_url", "").startswith(self.LOCAL_PREFIX)
            )
        ]

        if len(config_data["data"]) == original_len:
            logger.warning(f"未找到名为 '{name}' 的本地 RAG 配置")
            return False

        # 保存配置文件
        self._save_config_file(config_path, config_data)
        logger.info(f"已删除本地 RAG 配置: {name}")

        # 更新内存中的配置
        self.configs = [
            c
            for c in self.configs
            if not (c.name == name and self.is_local_server(c.server_name))
        ]

        return True
