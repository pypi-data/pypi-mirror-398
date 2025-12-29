#!/usr/bin/env python3
"""
Feedback配置管理
用于管理IDE等全局配置
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


class FeedbackConfig:
    """Feedback配置管理"""

    def __init__(self, project_path: Optional[str] = None):
        """初始化配置管理器

        Args:
            project_path: 项目路径，默认为当前工作目录
        """
        if project_path:
            self.project_path = Path(project_path)
        else:
            self.project_path = Path.cwd()

        self.config_dir = self.project_path / '.claude'
        self.config_file = self.config_dir / 'feedback.config'

    def load_config(self) -> Dict[str, Any]:
        """加载配置

        Returns:
            配置字典
        """
        if not self.config_file.exists():
            return {
                "ide": None,
                "custom_ide_command": None
            }

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 确保必要的键存在
                if "ide" not in config:
                    config["ide"] = None
                if "custom_ide_command" not in config:
                    config["custom_ide_command"] = None
                return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
            return {
                "ide": None,
                "custom_ide_command": None
            }

    def save_config(self, config: Dict[str, Any]):
        """保存配置

        Args:
            config: 配置字典
        """
        try:
            # 确保目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # 写入配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving config: {e}")

    def get_ide(self) -> Optional[str]:
        """获取配置的IDE

        Returns:
            IDE名称或None
        """
        config = self.load_config()
        # 优先返回custom_ide_command，其次返回ide
        custom = config.get("custom_ide_command")
        if custom:
            return custom
        return config.get("ide")

    def set_ide(self, ide: Optional[str] = None, custom_command: Optional[str] = None):
        """设置IDE

        Args:
            ide: IDE名称（单选按钮选择的）
            custom_command: 自定义IDE命令
        """
        config = self.load_config()

        if custom_command:
            # 如果有自定义命令，优先使用
            config["custom_ide_command"] = custom_command
            config["ide"] = None
        else:
            # 否则使用预设IDE
            config["ide"] = ide
            config["custom_ide_command"] = None

        self.save_config(config)

    def clear_ide(self):
        """清除IDE配置"""
        config = self.load_config()
        config["ide"] = None
        config["custom_ide_command"] = None
        self.save_config(config)


def main():
    """命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description='管理Feedback配置')
    parser.add_argument('action', choices=['get', 'set', 'clear'],
                        help='要执行的操作')
    parser.add_argument('--project-path', help='项目路径')
    parser.add_argument('--ide', help='IDE名称')
    parser.add_argument('--custom-command', help='自定义IDE命令')

    args = parser.parse_args()

    config_manager = FeedbackConfig(args.project_path)

    if args.action == 'get':
        ide = config_manager.get_ide()
        print(ide if ide else "none")

    elif args.action == 'set':
        config_manager.set_ide(args.ide, args.custom_command)
        ide = config_manager.get_ide()
        print(f"IDE配置已设置为: {ide}")

    elif args.action == 'clear':
        config_manager.clear_ide()
        print("IDE配置已清除")


if __name__ == "__main__":
    main()
