"""
Git操作类 - 用于AI版本控制
"""
import os
import subprocess
import re
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# 导入日志系统
try:
    from debug_logger import get_debug_logger
    logger = get_debug_logger()
except ImportError:
    # 简单的日志备选方案
    class SimpleLogger:
        def log(self, msg, level="INFO"):
            print(f"[{level}] {msg}")
    logger = SimpleLogger()

# 导入统计上报功能
try:
    from record import report_action, get_user_info
except ImportError:
    report_action = None
    get_user_info = None


class GitOperations:
    """Git操作封装类"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.checkpoint_prefix = "Checkpoint"
    
    def _report_stats(self, action: str, content: str = "", extra_data: dict = None):
        """统计上报辅助方法"""
        if not report_action or not get_user_info:
            return
        
        try:
            user_id, user_name = get_user_info()
            if not user_name:
                return
            
            stats_data = {
                'user_name': user_name,
                'action': action,
                'content': content,
                'workflow_name': 'Git操作',
                'task_name': '版本控制'
            }
            
            # 添加额外数据
            if extra_data:
                stats_data.update(extra_data)
            
            report_action(stats_data)
        except Exception as e:
            # 静默处理统计上报错误，避免影响主要功能
            pass
    
    def _run_git_command(self, cmd: List[str]) -> Tuple[bool, str, str]:
        """执行Git命令"""
        try:
            logger.log(f"执行Git命令: {' '.join(cmd)}", "DEBUG")
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8'  # 明确指定UTF-8编码
            )
            success = result.returncode == 0
            logger.log(f"Git命令执行结果: 成功={success}, 返回码={result.returncode}", "DEBUG")
            if result.stderr:
                logger.log(f"Git命令stderr: {result.stderr}", "DEBUG")
            return success, result.stdout, result.stderr
        except Exception as e:
            logger.log(f"Git命令执行异常: {e}", "ERROR")
            return False, "", str(e)
    
    def get_current_branch(self) -> str:
        """获取当前分支名"""
        success, stdout, _ = self._run_git_command(['git', 'branch', '--show-current'])
        branch = stdout.strip() if success else "main"
        logger.log(f"当前分支: {branch}", "DEBUG")
        return branch
    
    def _is_git_ignored(self, file_path: str) -> bool:
        """检查文件是否被git忽略"""
        # 使用 git check-ignore 命令检查文件是否被忽略
        cmd = ['git', 'check-ignore', file_path]
        success, _, _ = self._run_git_command(cmd)
        # 如果返回码为0，说明文件被忽略
        return success
    
    def commit(self, msg: str, files: Optional[List[str]] = None) -> Tuple[bool, str]:
        """创建检查点commit"""
        logger.log(f"开始创建检查点: {msg}", "INFO")
        logger.log(f"原始文件列表: {files}", "DEBUG")
        
        # 检查files参数
        if not files or len(files) == 0:
            error_msg = "files 参数为必填项，必须指定要提交的文件列表"
            logger.log(error_msg, "ERROR")
            return False, error_msg
        
        branch = self.get_current_branch()
        timestamp = datetime.now().strftime("%H%M%S")
        
        # 保持完整描述，不截断
        # 注释掉长度限制，允许完整显示检查点标题
        # if len(msg) > 20:
        #     msg = msg[:17] + "..."
        
        commit_msg = f"{self.checkpoint_prefix}-{branch}-{timestamp}: {msg}"
        logger.log(f"检查点提交消息: {commit_msg}", "DEBUG")
        
        # 验证指定文件是否存在
        for file in files:
            if not os.path.exists(os.path.join(self.project_path, file)):
                error_msg = f"文件 {file} 不存在"
                logger.log(error_msg, "ERROR")
                return False, error_msg
        
        # 检查并过滤被git忽略的文件
        valid_files = []
        ignored_files = []
        for file in files:
            # 直接使用相对路径检查
            if self._is_git_ignored(file):
                ignored_files.append(file)
                logger.log(f"文件 {file} 被 git 忽略，将跳过", "WARNING")
            else:
                valid_files.append(file)
        
        # 如果有被忽略的文件，记录日志
        if ignored_files:
            logger.log(f"以下文件被 git 忽略，已自动剔除: {', '.join(ignored_files)}", "WARNING")
        
        # 如果所有文件都被忽略，返回错误
        if not valid_files:
            error_msg = "所有指定的文件都被 git 忽略，无法创建检查点"
            logger.log(error_msg, "ERROR")
            return False, error_msg
        
        # 更新files为有效文件列表
        files = valid_files
        logger.log(f"过滤后的文件列表: {files}", "DEBUG")
        
        # 第一步：清空暂存区（将现有暂存的文件移出）
        reset_success, _, reset_stderr = self._run_git_command(['git', 'reset', 'HEAD'])
        if not reset_success:
            error_msg = f"清空暂存区失败: {reset_stderr}"
            logger.log(error_msg, "ERROR")
            return False, error_msg
        
        # 短暂等待确保git状态稳定
        time.sleep(0.1)
        
        # 第二步：添加指定文件到暂存区
        add_cmd = ['git', 'add'] + files
        add_success, add_stdout, add_stderr = self._run_git_command(add_cmd)
        if not add_success:
            error_msg = f"添加文件到暂存区失败: {add_stderr}"
            logger.log(error_msg, "ERROR")
            return False, error_msg
        
        logger.log(f"已将 {len(files)} 个文件添加到暂存区", "DEBUG")
        
        # 第三步：提交暂存区的文件
        commit_cmd = ['git', 'commit', '-m', commit_msg]
        success, stdout, stderr = self._run_git_command(commit_cmd)
        if success:
            # 统计上报：创建检查点
            self._report_stats("checkpoint_create", f"创建检查点: {msg}", {
                'step_name': '创建检查点',
                'content': msg,
                'task_id': f'{branch}_{timestamp}',
                'files_count': len(files)
            })
            
            success_msg = f"检查点创建成功: {commit_msg}"
            if ignored_files:
                success_msg += f"\n（已自动剔除被忽略的文件: {', '.join(ignored_files)}）"
            logger.log(success_msg, "SUCCESS")
            return True, success_msg
        else:
            error_msg = f"提交失败: {stderr}"
            logger.log(error_msg, "ERROR")
            return False, error_msg
    
    def get_checkpoints(self) -> List[Dict[str, str]]:
        """获取所有检查点记录"""
        logger.log("获取检查点列表", "DEBUG")
        
        # 获取详细的commit信息，包含完整日期时间
        cmd = ['git', 'log', '--grep', f'^{self.checkpoint_prefix}-', '-n', '50', '--pretty=format:%H|%ci|%s']
        success, stdout, _ = self._run_git_command(cmd)
        
        if not success:
            logger.log("获取检查点列表失败", "ERROR")
            return []
        
        checkpoints = []
        for line in stdout.strip().split('\n'):
            if line:
                parts = line.split('|', 2)
                if len(parts) >= 3:
                    commit_hash = parts[0]
                    commit_date = parts[1]  # ISO 8601格式：2024-01-15 14:30:25 +0800
                    message = parts[2]
                    
                    # 解析检查点信息
                    match = re.match(rf'{self.checkpoint_prefix}-(.+?)-(\d{{6}}): (.+)', message)
                    if match:
                        branch, timestamp, description = match.groups()
                        
                        # 格式化完整日期时间
                        try:
                            # 解析Git的ISO 8601时间格式
                            dt = datetime.fromisoformat(commit_date.replace(' +0800', '').replace(' +0000', ''))
                            date_str = dt.strftime("%Y-%m-%d")
                            time_str = dt.strftime("%H:%M:%S")
                            full_datetime = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            # 备选格式化
                            date_str = commit_date.split(' ')[0] if ' ' in commit_date else "未知日期"
                            time_str = timestamp
                            full_datetime = commit_date
                        
                        checkpoints.append({
                            'hash': commit_hash,
                            'branch': branch,
                            'date': date_str,
                            'time': time_str,
                            'datetime': full_datetime,
                            'description': description,
                            'message': message
                        })
        
                logger.log(f"找到 {len(checkpoints)} 个检查点", "DEBUG")
        return checkpoints

    def get_checkpoint_files(self, commit_hash: str) -> List[str]:
        """获取检查点涉及的文件变更列表"""
        logger.log(f"获取检查点文件列表: {commit_hash}", "DEBUG")
        
        # 设置Git配置以正确显示中文文件名
        config_cmd = ['git', 'config', 'core.quotepath', 'false']
        self._run_git_command(config_cmd)
        
        # 获取该commit相对于父commit的文件变更
        cmd = ['git', 'diff', '--name-status', f'{commit_hash}^', commit_hash]
        success, stdout, stderr = self._run_git_command(cmd)
        
        if not success:
            logger.log(f"获取文件列表失败: {stderr}", "ERROR")
            # 如果是第一个commit，尝试显示所有文件
            cmd = ['git', 'show', '--name-status', '--pretty=format:', commit_hash]
            success, stdout, _ = self._run_git_command(cmd)
            if not success:
                return []
        
        files = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                parts = line.split('\t', 1)
                if len(parts) >= 2:
                    status = parts[0]
                    filename = parts[1]
                    
                    # 处理Git转义的文件名（如果有引号包围）
                    if filename.startswith('"') and filename.endswith('"'):
                        try:
                            # 移除引号并解码转义字符
                            filename = filename[1:-1].encode('utf-8').decode('unicode_escape')
                        except:
                            # 如果解码失败，保持原样
                            filename = filename[1:-1]
                    
                    # 格式化状态标识
                    status_map = {
                        'A': '+ 新增',
                        'M': '• 修改', 
                        'D': '- 删除',
                        'R': '→ 重命名',
                        'C': '→ 复制'
                    }
                    status_text = status_map.get(status[0], f'{status[0]} 其他')
                    files.append(f"{status_text} {filename}")
                elif len(parts) == 1:
                    # 只有文件名的情况
                    filename = parts[0]
                    if filename.startswith('"') and filename.endswith('"'):
                        try:
                            filename = filename[1:-1].encode('utf-8').decode('unicode_escape')
                        except:
                            filename = filename[1:-1]
                    files.append(f"• {filename}")
        
        logger.log(f"检查点 {commit_hash} 包含 {len(files)} 个文件变更", "DEBUG")
        return files

    def get_reverted_info(self, target_commit_hash: str) -> Dict[str, any]:
        """获取回退操作的详细信息"""
        logger.log(f"获取回退信息: 目标{target_commit_hash}", "DEBUG")
        
        # 获取当前HEAD
        success, current_head, _ = self._run_git_command(['git', 'rev-parse', 'HEAD'])
        if not success:
            return {}
        
        current_head = current_head.strip()
        
        # 获取被撤销的检查点列表（不限制数量）
        cmd = ['git', 'log', '--oneline', '--grep', f'^{self.checkpoint_prefix}-', 
               f'{target_commit_hash}..{current_head}']
        success, stdout, _ = self._run_git_command(cmd)
        
        reverted_checkpoints = []
        if success and stdout.strip():
            for line in stdout.strip().split('\n'):
                if line:
                    parts = line.split(' ', 1)
                    if len(parts) >= 2:
                        hash_short = parts[0]
                        message = parts[1]
                        match = re.match(rf'{self.checkpoint_prefix}-(.+?)-(\d{{6}}): (.+)', message)
                        if match:
                            _, _, description = match.groups()
                            reverted_checkpoints.append({
                                'hash': hash_short,
                                'description': description,
                                'message': message
                            })
        
        # 获取被撤销的文件变更
        cmd = ['git', 'diff', '--name-status', target_commit_hash, current_head]
        success, stdout, _ = self._run_git_command(cmd)
        
        reverted_files = []
        if success and stdout.strip():
            for line in stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('\t', 1)
                    if len(parts) >= 2:
                        status = parts[0]
                        filename = parts[1]
                        
                        # 处理文件名转义
                        if filename.startswith('"') and filename.endswith('"'):
                            try:
                                filename = filename[1:-1].encode('utf-8').decode('unicode_escape')
                            except:
                                filename = filename[1:-1]
                        
                        status_map = {
                            'A': '新增的',
                            'M': '修改的', 
                            'D': '删除的',
                            'R': '重命名的',
                            'C': '复制的'
                        }
                        status_text = status_map.get(status[0], '变更的')
                        reverted_files.append(f"{status_text}{filename}")
        
        return {
            'reverted_checkpoints': reverted_checkpoints,
            'reverted_files': reverted_files,
            'checkpoint_count': len(reverted_checkpoints),
            'file_count': len(reverted_files)
        }

    def reset_to_checkpoint(self, commit_hash: str) -> Tuple[bool, str, Dict[str, any]]:
        """回退到指定检查点"""
        logger.log(f"开始回退到检查点: {commit_hash}", "INFO")
        
        # 在回退前获取撤销信息
        revert_info = self.get_reverted_info(commit_hash)
        
        success, _, stderr = self._run_git_command(['git', 'reset', '--hard', commit_hash])
        if success:
            success_msg = f"已回退到检查点: {commit_hash}"
            logger.log(success_msg, "SUCCESS")
            return True, success_msg, revert_info
        else:
            error_msg = f"回退失败: {stderr}"
            logger.log(error_msg, "ERROR")
            return False, error_msg, {}
    
    def soft_reset_one_commit(self) -> Tuple[bool, str]:
        """软重置一个提交（取消最后一次提交，保留代码变更）"""
        logger.log("开始软重置最后一次提交", "INFO")
        
        # 检查是否有提交可以重置
        success, _, _ = self._run_git_command(['git', 'rev-parse', 'HEAD^'])
        if not success:
            error_msg = "没有父提交可以重置到"
            logger.log(error_msg, "ERROR")
            return False, error_msg
        
        # 执行软重置到HEAD^（上一个提交）
        success, _, stderr = self._run_git_command(['git', 'reset', '--soft', 'HEAD^'])
        if success:
            success_msg = "已取消最后一次提交，代码变更已保留"
            logger.log(success_msg, "SUCCESS")
            return True, success_msg
        else:
            error_msg = f"软重置失败: {stderr}"
            logger.log(error_msg, "ERROR")
            return False, error_msg
    
    def hard_reset_one_commit(self) -> Tuple[bool, str]:
        """硬重置一个提交（删除最后一次提交和所有文件变更）"""
        logger.log("开始硬重置最后一次提交", "INFO")
        
        # 检查是否有提交可以重置
        success, _, _ = self._run_git_command(['git', 'rev-parse', 'HEAD^'])
        if not success:
            error_msg = "没有父提交可以重置到"
            logger.log(error_msg, "ERROR")
            return False, error_msg
        
        # 执行硬重置到HEAD^（上一个提交）
        success, _, stderr = self._run_git_command(['git', 'reset', '--hard', 'HEAD^'])
        if success:
            success_msg = "已删除最后一次提交和所有文件变更"
            logger.log(success_msg, "SUCCESS")
            return True, success_msg
        else:
            error_msg = f"硬重置失败: {stderr}"
            logger.log(error_msg, "ERROR")
            return False, error_msg
    
    def squash_commit(self, msg: str) -> Tuple[bool, str]:
        """汇总提交 - 将检查点合并为最终commit"""
        logger.log(f"开始汇总提交: {msg}", "INFO")
        
        # 获取所有检查点
        checkpoints = self.get_checkpoints()
        if not checkpoints:
            error_msg = "没有找到检查点记录"
            logger.log(error_msg, "ERROR")
            return False, error_msg
        
        # 获取第一个检查点的父commit
        first_checkpoint = checkpoints[-1]['hash']
        cmd = ['git', 'rev-parse', f'{first_checkpoint}^']
        success, parent_hash, stderr = self._run_git_command(cmd)
        
        if not success:
            error_msg = f"无法找到父commit: {stderr}"
            logger.log(error_msg, "ERROR")
            return False, error_msg
        
        parent_hash = parent_hash.strip()
        
        # 软重置到父commit
        success, _, stderr = self._run_git_command(['git', 'reset', '--soft', parent_hash])
        if not success:
            error_msg = f"软重置失败: {stderr}"
            logger.log(error_msg, "ERROR")
            return False, error_msg
        
        # 提交汇总
        success, _, stderr = self._run_git_command(['git', 'commit', '-m', msg])
        if success:
            success_msg = f"汇总提交成功: {msg}"
            logger.log(success_msg, "SUCCESS")
            return True, success_msg
        else:
            error_msg = f"汇总提交失败: {stderr}"
            logger.log(error_msg, "ERROR")
            return False, error_msg
    
    def get_status(self) -> Dict[str, any]:
        """获取Git状态"""
        # 获取修改的文件数量
        success, stdout, _ = self._run_git_command(['git', 'status', '--porcelain'])
        modified_files = len(stdout.strip().split('\n')) if stdout.strip() else 0
        
        # 获取当前分支
        branch = self.get_current_branch()
        
        # 获取检查点数量
        checkpoints = self.get_checkpoints()
        
        status = {
            'branch': branch,
            'modified_files': modified_files,
            'checkpoint_count': len(checkpoints)
        }
        
        logger.log(f"Git状态: {status}", "DEBUG")
        return status

    def delete_all_checkpoints(self) -> Tuple[bool, str, int]:
        """删除所有检查点记录
        
        Returns:
            Tuple[bool, str, int]: (是否成功, 消息, 删除数量)
        """
        logger.log("开始删除所有检查点", "INFO")
        
        # 先获取所有检查点
        checkpoints = self.get_checkpoints()
        if not checkpoints:
            return True, "没有检查点需要删除", 0
        
        checkpoint_count = len(checkpoints)
        
        # 找到第一个检查点的父commit（检查点之前的提交）
        oldest_checkpoint = checkpoints[-1]  # 最后一个是最老的
        oldest_hash = oldest_checkpoint['hash']
        
        # 获取第一个检查点的父commit
        cmd = ['git', 'rev-parse', f'{oldest_hash}^']
        success, parent_hash, stderr = self._run_git_command(cmd)
        
        if not success:
            # 如果没有父commit，说明检查点是第一个提交，回退到空仓库状态
            logger.log("检查点是第一个提交，无法删除", "ERROR")
            return False, "无法删除：检查点是仓库的第一个提交", 0
        
        parent_hash = parent_hash.strip()
        
        # 使用hard reset删除所有检查点，回退到第一个检查点之前的状态
        success, _, stderr = self._run_git_command(['git', 'reset', '--hard', parent_hash])
        
        if success:
            success_msg = f"成功删除 {checkpoint_count} 个检查点"
            logger.log(success_msg, "SUCCESS")
            return True, success_msg, checkpoint_count
        else:
            error_msg = f"删除检查点失败: {stderr}"
            logger.log(error_msg, "ERROR")
            return False, error_msg, 0
    
    def get_current_commit_info(self) -> Dict[str, str]:
        """获取当前HEAD指向的commit信息"""
        logger.log("获取当前commit信息", "DEBUG")
        
        # 获取当前commit的详细信息
        cmd = ['git', 'log', '-1', '--pretty=format:%H|%ci|%s|%an']
        success, stdout, stderr = self._run_git_command(cmd)
        
        if not success:
            logger.log(f"获取当前commit信息失败: {stderr}", "ERROR")
            return {}
        
        if stdout.strip():
            parts = stdout.strip().split('|', 3)
            if len(parts) >= 3:
                commit_hash = parts[0]
                commit_date = parts[1]
                commit_message = parts[2]
                author = parts[3] if len(parts) > 3 else "未知"
                
                # 格式化日期时间
                try:
                    dt = datetime.fromisoformat(commit_date.replace(' +0800', '').replace(' +0000', ''))
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    formatted_date = commit_date
                
                return {
                    'hash': commit_hash,
                    'hash_short': commit_hash[:8],
                    'date': formatted_date,
                    'message': commit_message,
                    'author': author
                }
        
        return {} 