"""
DeepSeek API调用封装模块
构建提示词，调用DeepSeek API生成提交信息，处理响应和错误。
"""

import requests
import json
import time
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DeepSeekAPI:
    """DeepSeek API调用类"""
    
    def __init__(self, config_manager):
        """
        初始化DeepSeek API客户端
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.api_key = config_manager.get_api_key()
        self.base_url = config_manager.get('api_base_url', 'https://api.deepseek.com/v1/chat/completions')
        self.model = config_manager.get('model', 'deepseek-chat')
        self.timeout = 30  # 请求超时时间（秒）
        self.max_retries = 3  # 最大重试次数
    
    def build_commit_prompt(self, git_info: Dict, style: str = "conventional", language: str = "zh-CN") -> str:
        """
        构建提交信息生成的提示词
        
        Args:
            git_info: 从GitHelper获取的信息字典
            style: 提交风格 (conventional, simple, emoji)
            language: 语言 (zh-CN, en)
            
        Returns:
            构建好的提示词
        """
        diff = git_info.get('diff', '')
        files = git_info.get('files', [])
        branch = git_info.get('branch', 'unknown')
        
        # 中英文模板
        if language == 'zh-CN':
            if style == 'conventional':
                style_instruction = """
请遵循Conventional Commits规范生成提交信息：
- 格式：<type>(<scope>): <subject>
- type类型：feat(新功能)、fix(修复)、docs(文档)、style(格式)、refactor(重构)、test(测试)、chore(构建/工具)
- scope：可选，表示影响范围
- subject：简短描述，不超过50字符
- 如果需要，可以在空行后添加详细描述
"""
            elif style == 'emoji':
                style_instruction = """
请使用emoji风格的提交信息：
- ✨ 新功能
- 🐛 修复bug
- 📝 文档
- 💄 样式
- ♻️ 重构
- ✅ 测试
- 🔧 工具/构建
格式：<emoji> <简短描述>
"""
            else:  # simple
                style_instruction = "请生成简洁明了的提交信息，不超过72字符。"
            
            prompt = f"""你是一个专业的Git提交信息生成助手。请根据以下Git代码变更，生成一条专业的提交信息。

**代码差异：**
```
{diff}
```

**变更文件：**
{chr(10).join(f'- {f}' for f in files)}

**当前分支：** {branch}

**要求：**
{style_instruction}

**重要提示：**
1. 只返回提交信息文本，不要包含代码块标记（```）或其他格式
2. 提交信息应该准确反映代码变更的内容
3. 使用中文描述
4. 保持简洁专业

请直接返回提交信息："""
        
        else:  # English
            if style == 'conventional':
                style_instruction = """
Please follow Conventional Commits specification:
- Format: <type>(<scope>): <subject>
- Types: feat, fix, docs, style, refactor, test, chore
- scope: optional, indicates the scope of change
- subject: brief description, max 50 characters
- Optionally add detailed description after blank line
"""
            elif style == 'emoji':
                style_instruction = """
Please use emoji-style commit message:
- ✨ New feature
- 🐛 Bug fix
- 📝 Documentation
- 💄 Style
- ♻️ Refactor
- ✅ Test
- 🔧 Tool/Build
Format: <emoji> <brief description>
"""
            else:  # simple
                style_instruction = "Please generate a concise commit message, max 72 characters."
            
            prompt = f"""You are a professional Git commit message generator. Please generate a professional commit message based on the following Git code changes.

**Code Diff:**
```
{diff}
```

**Changed Files:**
{chr(10).join(f'- {f}' for f in files)}

**Current Branch:** {branch}

**Requirements:**
{style_instruction}

**Important:**
1. Return only the commit message text, no code block markers (```) or other formatting
2. The commit message should accurately reflect the code changes
3. Use English
4. Keep it concise and professional

Please return the commit message directly:"""
        
        return prompt
    
    def generate_commit_message(self, git_info: Dict) -> Tuple[bool, str]:
        """
        调用DeepSeek API生成提交信息
        
        Args:
            git_info: Git仓库信息字典
            
        Returns:
            (成功标志, 提交信息或错误信息)
        """
        # 检查API Key
        self.api_key = self.config.get_api_key()
        if not self.api_key:
            return False, "API Key未设置，请在配置中设置DeepSeek API Key"
        
        # 构建提示词
        style = self.config.get('commit_style', 'conventional')
        language = self.config.get('language', 'zh-CN')
        temperature = self.config.get('temperature', 0.7)
        
        prompt = self.build_commit_prompt(git_info, style, language)
        
        # 估算token数量（粗略）
        estimated_tokens = self.estimate_tokens(prompt)
        if estimated_tokens > 8000:  # DeepSeek模型通常支持16k上下文，留出安全余量
            logger.warning(f"提示词可能过长，估算token: {estimated_tokens}")
        
        # 准备请求数据
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": 200,  # 提交信息通常不需要太长
            "stream": False
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 重试机制
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"调用DeepSeek API (尝试 {attempt + 1}/{self.max_retries})...")
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                # 检查HTTP状态码
                if response.status_code == 200:
                    result = response.json()
                    
                    # 解析响应
                    if 'choices' in result and len(result['choices']) > 0:
                        message = result['choices'][0]['message']['content'].strip()
                        
                        # 清理消息：移除可能的代码块标记
                        message = self._clean_message(message)
                        
                        logger.info("成功生成提交信息")
                        return True, message
                    else:
                        error_msg = f"API响应格式异常: {result}"
                        logger.error(error_msg)
                        return False, error_msg
                
                elif response.status_code == 401:
                    error_msg = "API Key无效或已过期，请检查配置"
                    logger.error(error_msg)
                    return False, error_msg
                
                elif response.status_code == 429:
                    error_msg = "API请求频率过高，请稍后重试"
                    logger.debug(f"{error_msg} (尝试 {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)  # 指数退避
                        continue
                    return False, error_msg
                
                elif response.status_code >= 500:
                    error_msg = f"DeepSeek API服务器错误 ({response.status_code})"
                    logger.debug(f"{error_msg} (尝试 {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return False, error_msg
                
                else:
                    try:
                        error_detail = response.json()
                        error_msg = error_detail.get('error', {}).get('message', f"API错误 ({response.status_code})")
                    except:
                        error_msg = f"API错误 ({response.status_code}): {response.text[:200]}"
                    logger.error(error_msg)
                    return False, error_msg
            
            except requests.exceptions.Timeout:
                last_error = "请求超时，请检查网络连接"
                logger.debug(f"{last_error} (尝试 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            
            except requests.exceptions.ConnectionError:
                last_error = "网络连接错误，请检查网络设置"
                logger.debug(f"{last_error} (尝试 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            
            except Exception as e:
                last_error = f"调用API时出错: {str(e)}"
                logger.debug(f"{last_error} (尝试 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
        
        return False, last_error or "未知错误"
    
    def _clean_message(self, message: str) -> str:
        """
        清理生成的提交信息，移除代码块标记等
        
        Args:
            message: 原始消息
            
        Returns:
            清理后的消息
        """
        # 移除代码块标记
        message = message.strip()
        if message.startswith('```'):
            lines = message.split('\n')
            # 移除第一行和最后一行（代码块标记）
            if len(lines) > 2:
                message = '\n'.join(lines[1:-1])
            else:
                message = message.replace('```', '').strip()
        
        # 移除多余的空白行
        lines = [line.strip() for line in message.split('\n') if line.strip()]
        message = '\n'.join(lines)
        
        return message.strip()
    
    def test_api_key(self, api_key: Optional[str] = None) -> Tuple[bool, str]:
        """
        测试API密钥是否有效
        
        Args:
            api_key: 要测试的API Key，如果为None则使用配置中的
            
        Returns:
            (是否有效, 错误信息)
        """
        test_key = api_key or self.config.get_api_key()
        if not test_key:
            return False, "API Key为空"
        
        # 使用一个简单的测试请求
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello"
                }
            ],
            "max_tokens": 10
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {test_key}"
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "API Key有效"
            elif response.status_code == 401:
                return False, "API Key无效或已过期"
            else:
                return False, f"测试失败: {response.status_code}"
        
        except requests.exceptions.Timeout:
            return False, "请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return False, "网络连接错误"
        except Exception as e:
            return False, f"测试时出错: {str(e)}"
    
    def estimate_tokens(self, text: str) -> int:
        """
        粗略估计token数量
        （简单估算：中文约1.5字符/token，英文约4字符/token）
        
        Args:
            text: 文本内容
            
        Returns:
            估算的token数量
        """
        # 简单估算：中文字符按1.5字符/token，英文按4字符/token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        estimated = int(chinese_chars / 1.5 + other_chars / 4)
        return estimated

