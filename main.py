# -*- coding: utf-8 -*-
"""
程序主入口
"""

import sys
import os
import argparse
import io
from pathlib import Path
from typing import Dict

VERSION = "1.0.0"

# Windows 控制台编码设置，解决 SourceTree 中文乱码问题
# 默认使用 UTF-8 编码
# 可以通过环境变量 DSC_OUTPUT_ENCODING 强制设置（'utf-8' 或 'gbk'）
# 或者在 run 命令中使用 --encoding 参数指定

def _get_default_encoding() -> str:
    """获取默认的编码设置"""
    # 检查环境变量
    env_encoding = os.environ.get('DSC_OUTPUT_ENCODING', '').lower()
    if env_encoding in ['utf-8', 'gbk']:
        return env_encoding
    
    # 默认使用 UTF-8（适用于所有平台）
    return 'utf-8'

_CONSOLE_ENCODING = _get_default_encoding()

def set_console_encoding(encoding: str) -> bool:
    """
    设置控制台编码
    
    Args:
        encoding: 编码格式 ('utf-8' 或 'gbk')
    
    Returns:
        是否设置成功
    """
    global _CONSOLE_ENCODING
    
    if encoding.lower() not in ['utf-8', 'gbk']:
        return False
    
    _CONSOLE_ENCODING = encoding.lower()
    
    # 设置控制台代码页
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            code_page = 65001 if _CONSOLE_ENCODING == 'utf-8' else 936
            kernel32.SetConsoleOutputCP(code_page)
        except:
            pass
    
    return True

# 初始化时设置控制台代码页
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        code_page = 65001 if _CONSOLE_ENCODING == 'utf-8' else 936
        kernel32.SetConsoleOutputCP(code_page)
    except:
        pass

# 多语言提示信息
MESSAGES: Dict[str, Dict[str, str]] = {
    'zh-CN': {
        'help_title': f'DeepSeek Commit Tool CLI v{VERSION}',
        'help_commands': '常用命令：',
        'help_api_key': '  --api-key                 写入 API Key',
        'help_commit_style': '  --commit-style           配置提交风格(conventional|simple|emoji)',
        'help_language': '  --language               配置语言(zh-CN|en)',
        'help_temperature': '  --temperature           配置随机性(0.1-1.0)',
        'help_max_diff_length': '  --max-diff-length       配置最大差异长度(>=100)',
        'help_show_config': '  --show-config           查看当前配置',
        'help_run': '  run                       生成当前仓库提交信息',
        'help_run_path': '  run <path>               生成指定仓库提交信息',
        'help_encoding': '  run --encoding utf-8|gbk  指定输出编码格式',
        'help_tip': '\n提示: 参数调用即写入配置; run 只输出结果或错误。\n',
        'config_updated': '配置已更新',
        'config_save_failed': '配置保存失败',
        'current_config': '当前配置:',
        'error_path_not_exist': '错误: 路径不存在: {path}',
        'error_config': '配置错误: {msg}',
        'error_invalid_temperature': '错误: 温度值必须在0.1-1.0之间',
        'error_invalid_max_diff_length': '错误: 最大差异长度必须>=100',
        'error_no_git_repo': '错误: 未找到Git仓库: {detail}',
        'error_no_git_exe': '错误: 未找到Git可执行文件: {detail}',
        'error_git_init': '错误: 初始化Git仓库失败: {detail}',
        'no_staged_changes': '没有暂存的更改',
        'generate_failed': '生成失败: {msg}',
        'runtime_error': '运行时错误: {error}',
    },
    'en': {
        'help_title': f'DeepSeek Commit Tool CLI v{VERSION}',
        'help_commands': 'Common Commands:',
        'help_api_key': '  --api-key                  Set API Key',
        'help_commit_style': '  --commit-style            Configure commit style(conventional|simple|emoji)',
        'help_language': '  --language                Configure language(zh-CN|en)',
        'help_temperature': '  --temperature            Configure temperature(0.1-1.0)',
        'help_max_diff_length': '  --max-diff-length        Configure max diff length(>=100)',
        'help_show_config': '  --show-config            Show current config',
        'help_run': '  run                        Generate commit message for current repo',
        'help_run_path': '  run <path>                Generate commit message for specified repo',
        'help_encoding': '  run --encoding utf-8|gbk   Specify output encoding',
        'help_tip': '\nTip: Parameters are saved to config; run only outputs results or errors.\n',
        'config_updated': 'Configuration updated',
        'config_save_failed': 'Failed to save configuration',
        'current_config': 'Current Configuration:',
        'error_path_not_exist': 'Error: Path does not exist: {path}',
        'error_config': 'Configuration error: {msg}',
        'error_invalid_temperature': 'Error: Temperature must be between 0.1 and 1.0',
        'error_invalid_max_diff_length': 'Error: Max diff length must be >=100',
        'error_no_git_repo': 'Error: Git repository not found: {detail}',
        'error_no_git_exe': 'Error: Git executable not found: {detail}',
        'error_git_init': 'Error: Failed to initialize Git repository: {detail}',
        'no_staged_changes': 'No staged changes',
        'generate_failed': 'Generation failed: {msg}',
        'runtime_error': 'Runtime error: {error}',
    }
}


def get_message(key: str, language: str = 'zh-CN', **kwargs) -> str:
    """
    获取本地化消息
    
    Args:
        key: 消息键
        language: 语言代码 ('zh-CN' 或 'en')
        **kwargs: 格式化参数
    
    Returns:
        格式化后的消息字符串
    """
    lang = language if language in MESSAGES else 'zh-CN'
    msg = MESSAGES[lang].get(key, MESSAGES['zh-CN'].get(key, key))
    return msg.format(**kwargs) if kwargs else msg


def safe_print(text: str, end: str = '\n') -> None:
    """
    安全的打印函数，确保中文正确显示（兼容 SourceTree）
    
    Args:
        text: 要打印的文本
        end: 结束符，默认为换行符
    """
    try:
        if sys.platform == 'win32':
            # Windows: 直接写入缓冲区，使用检测到的编码
            if hasattr(sys.stdout, 'buffer'):
                try:
                    encoded_text = text.encode(_CONSOLE_ENCODING, errors='replace')
                    encoded_end = end.encode(_CONSOLE_ENCODING, errors='replace') if end else b''
                    sys.stdout.buffer.write(encoded_text + encoded_end)
                    sys.stdout.buffer.flush()
                    return
                except (AttributeError, UnicodeEncodeError):
                    pass
        # 备用方案：使用标准 print
        print(text, end=end, flush=True)
    except Exception:
        # 最后备用方案：尝试直接输出字节
        try:
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout.buffer.write(text.encode(_CONSOLE_ENCODING, errors='replace'))
                if end:
                    sys.stdout.buffer.write(end.encode(_CONSOLE_ENCODING, errors='replace'))
                sys.stdout.buffer.flush()
        except:
            pass


def print_quick_help(language: str = 'zh-CN') -> None:
    """
    打印快速帮助信息
    
    Args:
        language: 语言代码 ('zh-CN' 或 'en')
    """
    msg = (
        f"\n{get_message('help_title', language)}\n"
        f"{'=' * 50}\n"
        f"{get_message('help_commands', language)}\n"
        f"{get_message('help_api_key', language)}\n"
        f"{get_message('help_commit_style', language)}\n"
        f"{get_message('help_language', language)}\n"
        f"{get_message('help_temperature', language)}\n"
        f"{get_message('help_max_diff_length', language)}\n"
        f"{get_message('help_show_config', language)}\n"
        f"{get_message('help_run', language)}\n"
        f"{get_message('help_run_path', language)}\n"
        f"{get_message('help_encoding', language)}\n"
        f"{get_message('help_tip', language)}"
    )
    safe_print(msg, end='')


def main() -> None:
    argv = sys.argv[1:]

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--api-key', dest='api_key', help='DeepSeek API Key')
    parser.add_argument('--commit-style', choices=['conventional', 'simple', 'emoji'], help='Commit style')
    parser.add_argument('--language', choices=['zh-CN', 'en'], help='Language (中文/English)')
    parser.add_argument('--temperature', type=float, help='Temperature (0.1-1.0)')
    parser.add_argument('--max-diff-length', type=int, dest='max_diff_length', help='Max diff length (>=100)')
    parser.add_argument('--show-config', action='store_true', help='Show current configuration')

    subparsers = parser.add_subparsers(dest='command')
    run_parser = subparsers.add_parser('run')
    run_parser.add_argument('repository_path', nargs='?', help='Git repository path (optional)')
    run_parser.add_argument('--encoding', choices=['utf-8', 'gbk'], help='Output encoding (utf-8 or gbk)')

    if not argv:
        # 如果没有参数，先尝试加载配置获取语言设置
        try:
            from config import get_config
            config = get_config()
            language = config.get('language', 'zh-CN')
        except:
            language = 'zh-CN'
        print_quick_help(language)
        return

    args = parser.parse_args(argv)

    try:
        from config import get_config
        from git_helper import GitHelper
        from deepseek_api import DeepSeekAPI

        config = get_config()
        
        # 获取当前语言设置（在设置语言参数之前）
        current_language = config.get('language', 'zh-CN')

        # 未指定 run 时，视为配置操作
        if args.command != 'run':
            if args.show_config:
                cfg = config.get_all()
                keys_keep = ['api_key', 'model', 'language', 'commit_style', 'temperature', 'max_diff_length']
                filtered = {k: cfg.get(k) for k in keys_keep if k in cfg}
                api_key = filtered.get('api_key', '')
                masked = api_key if not api_key else (api_key[:3] + "***" + api_key[-4:])
                filtered['api_key'] = masked
                safe_print(get_message('current_config', current_language))
                for k, v in filtered.items():
                    safe_print(f"{k}: {v}")
                return

            changed = False
            
            # 验证并设置温度
            if args.temperature is not None:
                if args.temperature < 0.1 or args.temperature > 1.0:
                    safe_print(get_message('error_invalid_temperature', current_language))
                    return
                config.set('temperature', args.temperature)
                changed = True
            
            # 验证并设置最大差异长度
            if args.max_diff_length is not None:
                if args.max_diff_length < 100:
                    safe_print(get_message('error_invalid_max_diff_length', current_language))
                    return
                config.set('max_diff_length', args.max_diff_length)
                changed = True
            
            if args.api_key is not None:
                config.set('api_key', args.api_key)
                changed = True
            if args.commit_style is not None:
                config.set('commit_style', args.commit_style)
                changed = True
            if args.language is not None:
                config.set('language', args.language)
                current_language = args.language  # 更新当前语言
                changed = True

            if changed:
                if config.save():
                    safe_print(get_message('config_updated', current_language))
                else:
                    safe_print(get_message('config_save_failed', current_language))
            else:
                print_quick_help(current_language)
            return

        # run 子命令：生成提交信息
        # 获取当前语言设置
        current_language = config.get('language', 'zh-CN')
        
        # 如果指定了编码参数，则设置输出编码
        if hasattr(args, 'encoding') and args.encoding:
            set_console_encoding(args.encoding)
        
        repo_path = args.repository_path
        if repo_path:
            repo_path = Path(repo_path).resolve()
            if not repo_path.exists():
                safe_print(get_message('error_path_not_exist', current_language, path=repo_path))
                return
        else:
            repo_path = Path.cwd()

        # 先检查 Git 仓库和暂存文件，避免不必要的配置校验
        try:
            git_helper = GitHelper(str(repo_path))
        except ValueError as e:
            safe_print(get_message('error_no_git_repo', current_language, detail=str(e)))
            return
        except FileNotFoundError as e:
            safe_print(get_message('error_no_git_exe', current_language, detail=str(e)))
            return
        except Exception as e:
            safe_print(get_message('error_git_init', current_language, detail=str(e)))
            return

        # 检查是否有暂存文件，没有则直接返回，不调用 API
        if not git_helper.has_staged_changes():
            safe_print(get_message('no_staged_changes', current_language))
            return

        # 确认是 Git 仓库且有暂存文件后，才校验配置（需要 API Key）
        is_valid, error_msg = config.validate(current_language)
        if not is_valid:
            safe_print(get_message('error_config', current_language, msg=error_msg))
            return

        # 获取仓库信息并调用 API
        deepseek_api = DeepSeekAPI(config)
        repo_info = git_helper.get_repo_info()
        success, result = deepseek_api.generate_commit_message(repo_info)
        if not success:
            safe_print(get_message('generate_failed', current_language, msg=result))
            return

        safe_print(result.strip())

    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        current_language = 'zh-CN'
        try:
            from config import get_config
            config = get_config()
            current_language = config.get('language', 'zh-CN')
        except:
            pass
        safe_print(get_message('runtime_error', current_language, error=str(e)))
        sys.exit(1)


if __name__ == '__main__':
    main()

