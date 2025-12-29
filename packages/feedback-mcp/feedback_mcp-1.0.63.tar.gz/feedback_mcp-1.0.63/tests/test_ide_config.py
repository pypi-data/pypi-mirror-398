#!/usr/bin/env python3
"""
IDE配置管理模块的单元测试
"""

import unittest
import tempfile
import json
import os
import shutil
from pathlib import Path

# 添加src-min到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src-min'))

from config.ide_config import IDEConfig


class TestIDEConfig(unittest.TestCase):
    """测试IDE配置类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / '.interactive_feedback_mcp_test'
        
        # 创建测试用的IDEConfig实例
        self.config = IDEConfig()
        self.config.config_dir = self.config_dir
        self.config.config_file = self.config_dir / 'ide_config.json'
        
        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """测试后的清理工作"""
        # 清理临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_default_config(self):
        """测试默认配置"""
        self.assertEqual(self.config.current_ide, "cursor")
        self.assertIn("cursor", self.config.supported_ides)
        self.assertIn("kiro", self.config.supported_ides)
        self.assertIn("vscode", self.config.supported_ides)
    
    def test_get_current_ide(self):
        """测试获取当前IDE"""
        current_ide = self.config.get_current_ide()
        self.assertEqual(current_ide['name'], "cursor")
        self.assertEqual(current_ide['display_name'], "Cursor")
        self.assertEqual(current_ide['command'], "cursor")
    
    def test_get_supported_ides(self):
        """测试获取支持的IDE列表"""
        ides = self.config.get_supported_ides()
        self.assertIsInstance(ides, dict)
        self.assertIn("cursor", ides)
        self.assertIn("kiro", ides)
        self.assertIn("vscode", ides)
        
        # 检查每个IDE的信息结构
        for ide_key, ide_info in ides.items():
            self.assertIn('name', ide_info)
            self.assertIn('display_name', ide_info)
            self.assertIn('command', ide_info)
            self.assertIn('description', ide_info)
            self.assertIn('available', ide_info)
            self.assertIn('current', ide_info)
    
    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        # 保存配置
        success = self.config.save_config("vscode")
        self.assertTrue(success)
        
        # 验证配置文件存在
        self.assertTrue(self.config.config_file.exists())
        
        # 重新加载配置
        loaded_ide = self.config.load_config()
        self.assertEqual(loaded_ide, "vscode")
        self.assertEqual(self.config.current_ide, "vscode")
    
    def test_invalid_ide_name(self):
        """测试无效的IDE名称"""
        success = self.config.save_config("invalid_ide")
        self.assertFalse(success)
    
    def test_is_ide_available(self):
        """测试IDE可用性检查"""
        # 测试已知命令的可用性
        self.assertIsInstance(self.config.is_ide_available("cursor"), bool)
        self.assertIsInstance(self.config.is_ide_available("kiro"), bool)
        self.assertIsInstance(self.config.is_ide_available("vscode"), bool)
        
        # 测试无效IDE
        self.assertFalse(self.config.is_ide_available("invalid_ide"))
    
    def test_config_file_corruption(self):
        """测试配置文件损坏处理"""
        # 创建损坏的配置文件
        with open(self.config.config_file, 'w') as f:
            f.write("invalid json content")
        
        # 加载配置应该回退到默认值
        loaded_ide = self.config.load_config()
        self.assertEqual(loaded_ide, "cursor")
    
    def test_reset_to_default(self):
        """测试重置为默认配置"""
        # 先保存一个非默认配置
        self.config.save_config("vscode")
        self.assertEqual(self.config.current_ide, "vscode")
        
        # 重置为默认
        success = self.config.reset_to_default()
        self.assertTrue(success)
        self.assertEqual(self.config.current_ide, "cursor")


class TestIDEUtils(unittest.TestCase):
    """测试IDE工具函数"""
    
    def test_get_ide_command(self):
        """测试获取IDE命令"""
        from ide_utils import get_ide_command
        
        self.assertEqual(get_ide_command("cursor"), "cursor")
        self.assertEqual(get_ide_command("kiro"), "kiro")
        self.assertEqual(get_ide_command("vscode"), "code")
        self.assertEqual(get_ide_command("invalid"), "cursor")  # 默认值
    
    def test_is_ide_available(self):
        """测试IDE可用性检查"""
        from ide_utils import is_ide_available
        
        # 测试已知IDE的可用性
        self.assertIsInstance(is_ide_available("cursor"), bool)
        self.assertIsInstance(is_ide_available("vscode"), bool)
        
        # 测试无效IDE
        self.assertFalse(is_ide_available("invalid_ide"))
    
    def test_get_ide_info(self):
        """测试获取IDE信息"""
        from ide_utils import get_ide_info
        
        info = get_ide_info("cursor")
        self.assertIsInstance(info, dict)
        self.assertIn('name', info)
        self.assertIn('command', info)
        self.assertIn('description', info)
        self.assertIn('available', info)


if __name__ == '__main__':
    unittest.main()