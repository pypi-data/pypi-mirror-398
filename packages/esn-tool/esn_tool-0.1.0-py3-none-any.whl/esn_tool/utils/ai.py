"""
AI 客户端模块

调用 AI Chat Completions API 生成文本。
"""

from typing import Any

import httpx

from esn_tool.utils.config import get_config_value

# API 端点路径
CHAT_COMPLETIONS_PATH = "/chat/completions"

# 默认超时时间
DEFAULT_TIMEOUT = 120


class AIClient:
    """AI 客户端"""
    
    def __init__(self, model: str | None = None):
        """
        初始化 AI 客户端。
        
        配置从 esntool config 获取。
        
        Args:
            model: 模型名称，覆盖配置文件中的模型
        """
        # 从配置文件获取
        self.api_key = get_config_value("ai.api_key")
        self.base_url = get_config_value("ai.base_url")
        self.model = model or get_config_value("ai.model")
        self.timeout = DEFAULT_TIMEOUT
        
        # 验证必要配置
        if not self.api_key:
            raise ValueError(
                "未配置 API Key。请运行 'esntool config' 进行配置。"
            )
        
        if not self.base_url:
            raise ValueError(
                "未配置 Base URL。请运行 'esntool config' 进行配置。"
            )
        
        if not self.model:
            raise ValueError(
                "未配置 Model。请运行 'esntool config' 进行配置。"
            )
        
        # 确保 base_url 不以 / 结尾
        self.base_url = self.base_url.rstrip("/")
    
    def chat(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """
        发送聊天请求并获取回复。
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            
        Returns:
            AI 生成的文本
        """
        messages: list[dict[str, str]] = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "enable_thinking": False,  # 禁用深度思考
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # 拼接完整的 API URL
        url = f"{self.base_url}{CHAT_COMPLETIONS_PATH}"
        
        with httpx.Client(timeout=self.timeout) as client:
            try:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                # 尝试获取响应体中的错误信息
                try:
                    error_detail = e.response.json()
                    error_msg = error_detail.get("error", {}).get("message", str(e))
                except Exception:
                    error_msg = e.response.text or str(e)
                raise Exception(f"API 请求失败 ({e.response.status_code}): {error_msg}")
            except httpx.TimeoutException:
                raise Exception(f"请求超时 (超过 {self.timeout} 秒)")
            except Exception as e:
                raise Exception(f"请求异常: {e}")


# Git 提交信息生成的系统提示词
COMMIT_MESSAGE_SYSTEM_PROMPT = """你是一个专业的 Git 提交信息生成助手。
根据提供的 git diff 内容，生成符合 Conventional Commits 规范的提交信息。

规范格式：
<type>(<scope>): <subject>

<body>

类型说明：
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式（不影响代码运行的变动）
- refactor: 重构（既不是新增功能，也不是修改 bug）
- perf: 性能优化
- test: 测试相关
- chore: 构建过程或辅助工具的变动

要求：
1. subject 使用中文，简洁明了，不超过 50 个字符
2. 如果改动较大，添加 body 详细说明
3. 只输出提交信息，不要有其他解释
"""


def generate_commit_message(diff_content: str, client: AIClient | None = None) -> str:
    """
    根据 diff 内容生成提交信息。
    
    Args:
        diff_content: git diff 输出内容
        client: AI 客户端实例，如果为 None 则创建新实例
        
    Returns:
        生成的提交信息
    """
    if client is None:
        client = AIClient()
    
    prompt = f"请根据以下 git diff 内容生成提交信息：\n\n```diff\n{diff_content}\n```"
    
    return client.chat(
        prompt=prompt,
        system_prompt=COMMIT_MESSAGE_SYSTEM_PROMPT,
        temperature=0.3,  # 较低的温度使输出更稳定
        max_tokens=512,
    )
