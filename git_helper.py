"""
Git操作封装模块
提供简洁的API接口用于Git仓库操作，包括获取差异、文件列表、分支信息等。
"""

import subprocess
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import logging

# 导入配置管理器（延迟导入避免循环）
from config import get_config

logger = logging.getLogger(__name__)


class GitHelper:
    """Git操作辅助类"""
    
    def __init__(self, repo_path: Optional[str] = None):
        """
        初始化GitHelper
        
        Args:
            repo_path: Git仓库路径，如果为None则自动检测当前目录
        """
        if repo_path:
            self.repo_path = Path(repo_path).resolve()
        else:
            # 自动检测当前目录是否为Git仓库
            self.repo_path = self._find_git_repo(Path.cwd())
        
        if not self.repo_path:
            raise ValueError("未找到Git仓库，请确保在Git仓库目录中运行")
        
        self.git_exe = self.find_git_executable()
        if not self.git_exe:
            raise FileNotFoundError("未找到Git可执行文件，请确保已安装Git")
        
        logger.info(f"GitHelper初始化: 仓库路径={self.repo_path}, Git={self.git_exe}")
    
    def _find_git_repo(self, start_path: Path) -> Optional[Path]:
        """递归向上查找Git仓库根目录"""
        current = start_path.resolve()
        while current != current.parent:
            if (current / '.git').exists():
                return current
            current = current.parent
        return None
    
    @staticmethod
    def find_git_executable() -> Optional[str]:
        """
        在Windows系统中查找git.exe
        
        Returns:
            git可执行文件路径，如果未找到则返回None
        """
        # 常见路径
        common_paths = [
            r'C:\Program Files\Git\cmd\git.exe',
            r'C:\Program Files (x86)\Git\cmd\git.exe',
            r'C:\Program Files\Git\bin\git.exe',
            r'C:\Program Files (x86)\Git\bin\git.exe',
        ]
        
        # 检查PATH环境变量
        git_in_path = shutil.which('git.exe') or shutil.which('git')
        if git_in_path:
            return git_in_path
        
        # 检查常见路径
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # 尝试从注册表查找（Windows）
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\GitForWindows'
            )
            install_path = winreg.QueryValueEx(key, 'InstallPath')[0]
            git_exe = os.path.join(install_path, 'cmd', 'git.exe')
            if os.path.exists(git_exe):
                return git_exe
        except Exception:
            pass
        
        return None
    
    def _run_git_command(self, args: List[str], capture_output: bool = True) -> Tuple[bool, str]:
        """
        执行Git命令
        
        Args:
            args: Git命令参数列表
            capture_output: 是否捕获输出
            
        Returns:
            (成功标志, 输出或错误信息)
        """
        try:
            cmd = [self.git_exe] + args
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=capture_output,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                # 只记录详细错误到日志
                logger.debug(f"Git命令失败: {' '.join(cmd)}, 错误: {error_msg}")
                # 提取简洁的错误信息，避免输出大量帮助信息
                if error_msg:
                    # 查找第一个错误行（通常以 "error:" 或 "fatal:" 开头）
                    lines = error_msg.split('\n')
                    error_line = None
                    for line in lines:
                        line = line.strip()
                        if line.startswith('error:') or line.startswith('fatal:'):
                            error_line = line
                            break
                    
                    if error_line:
                        # 只返回错误行，去掉 "error:" 或 "fatal:" 前缀
                        clean_error = error_line.split(':', 1)[-1].strip()
                        if len(clean_error) > 150:
                            clean_error = clean_error[:150] + "..."
                        return False, clean_error
                    
                    # 如果没有找到标准错误格式，返回第一行非空行
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('usage:') and not line.startswith('Diff'):
                            if len(line) > 150:
                                line = line[:150] + "..."
                            return False, line
                    
                    # 最后，返回第一行
                    first_line = lines[0].strip()
                    if len(first_line) > 150:
                        first_line = first_line[:150] + "..."
                    return False, first_line
                return False, "Git命令执行失败"
        except subprocess.TimeoutExpired:
            error_msg = "Git命令执行超时"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"执行Git命令时出错: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_staged_diff(self, max_length: int = 4000) -> str:
        """
        获取暂存区的代码差异
        
        Args:
            max_length: 最大差异长度（字符数）
            
        Returns:
            差异文本
        """
        success, diff = self._run_git_command(['diff', '--cached', '--no-color'])
        if not success:
            return ""
        
        # 限制长度
        if len(diff) > max_length:
            diff = diff[:max_length] + f"\n\n... (差异过长，已截断，共{len(diff)}字符)"
        
        return diff
    
    def get_staged_files(self) -> List[str]:
        """
        获取暂存文件列表
        
        Returns:
            文件路径列表
        """
        success, output = self._run_git_command(['diff', '--cached', '--name-only'])
        if not success:
            return []
        
        files = [f.strip() for f in output.split('\n') if f.strip()]
        return files
    
    def get_current_branch(self) -> str:
        """
        获取当前分支名称
        
        Returns:
            分支名称
        """
        success, branch = self._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
        if success:
            return branch
        return "unknown"
    
    def has_staged_changes(self) -> bool:
        """
        检查是否有暂存的更改
        
        Returns:
            是否有暂存更改，如果命令执行失败或没有文件返回 False
        """
        # 直接获取暂存文件列表，更可靠
        files = self.get_staged_files()
        return len(files) > 0
    
    def get_repo_info(self) -> Dict[str, any]:
        """
        获取完整的仓库信息
        
        Returns:
            包含diff, files, branch, repo_name的字典
        """
        config = get_config()
        max_diff_length = config.get('max_diff_length', 3000)
        
        return {
            'diff': self.get_staged_diff(max_diff_length),
            'files': self.get_staged_files(),
            'branch': self.get_current_branch(),
            'repo_name': self.repo_path.name,
            'repo_path': str(self.repo_path)
        }
    
    def commit(self, message: str) -> Tuple[bool, str]:
        """
        执行Git提交
        
        Args:
            message: 提交信息
            
        Returns:
            (成功标志, 错误信息)
        """
        # 转义提交信息中的特殊字符
        message = message.replace('"', '\\"')
        
        success, output = self._run_git_command(['commit', '-m', message])
        if success:
            return True, "提交成功"
        else:
            return False, output
    
    def stage_files(self, file_paths: List[str]) -> Tuple[bool, str]:
        """
        暂存指定文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            (成功标志, 错误信息)
        """
        if not file_paths:
            return True, ""
        
        success, output = self._run_git_command(['add'] + file_paths)
        if success:
            return True, "文件已暂存"
        else:
            return False, output
    
    def unstage_files(self, file_paths: List[str]) -> Tuple[bool, str]:
        """
        取消暂存指定文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            (成功标志, 错误信息)
        """
        if not file_paths:
            return True, ""
        
        success, output = self._run_git_command(['restore', '--staged'] + file_paths)
        if success:
            return True, "文件已取消暂存"
        else:
            return False, output
    
    def get_git_status(self) -> str:
        """
        获取完整的Git状态
        
        Returns:
            状态文本
        """
        success, output = self._run_git_command(['status', '--short'])
        if success:
            return output
        return ""
    
    def get_unstaged_files(self) -> List[str]:
        """
        获取未暂存的文件列表
        
        Returns:
            文件路径列表
        """
        success, output = self._run_git_command(['diff', '--name-only'])
        if not success:
            return []
        
        files = [f.strip() for f in output.split('\n') if f.strip()]
        return files
    
    def get_untracked_files(self) -> List[str]:
        """
        获取未跟踪的文件列表
        
        Returns:
            文件路径列表
        """
        success, output = self._run_git_command(['ls-files', '--others', '--exclude-standard'])
        if not success:
            return []
        
        files = [f.strip() for f in output.split('\n') if f.strip()]
        return files
    
    def get_repo_path(self) -> str:
        """获取仓库路径"""
        return str(self.repo_path)

