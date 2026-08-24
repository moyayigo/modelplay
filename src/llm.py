import json
import requests
from typing import Optional, Dict, Any, List
from src.model_config import has_api_key


class LLMClient:
    """OpenAI-compatible LLM client supporting both local and remote modes"""

    def __init__(
        self,
        model: str = "llama3.2",
        api_url: str = "http://localhost:11434/v1",
        api_key: str = "",
        max_tokens: int = 4096,
        timeout: int = 120,
    ):
        self.model = model
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._has_auth = has_api_key({"api_key": api_key})
        # 保存上一次 LLM 调用的 token 使用情况（None 表示未获取或调用失败）
        self.last_usage: Optional[Dict[str, int]] = None

    @classmethod
    def from_config(cls, provider: Dict[str, Any]) -> "LLMClient":
        return cls(
            model=provider.get("model", "llama3.2"),
            api_url=provider.get("api_url", "http://localhost:11434/v1"),
            api_key=provider.get("api_key", ""),
            max_tokens=provider.get("max_tokens", 4096),
            timeout=provider.get("timeout", 120),
        )

    def _build_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._has_auth:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_messages(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        return messages

    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        messages = self._build_messages(prompt, system_prompt, history)

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
        }

        try:
            response = requests.post(
                f"{self.api_url}/chat/completions",
                json=payload,
                headers=self._build_headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            # 保存 token 使用情况（OpenAI 兼容 API 在响应中返回 usage 字段）
            usage = data.get("usage")
            if isinstance(usage, dict):
                self.last_usage = {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                }
            else:
                self.last_usage = None
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            error_body = ""
            try:
                error_body = e.response.text[:500]
            except Exception:
                pass
            auth_hint = "Check if the API Key is correct" if not self._has_auth else "Check if the API Key/ID is correct"
            return f"[LLM Error {status_code}] {auth_hint}: {error_body}"
        except requests.exceptions.ConnectionError:
            mode = "remote" if self._has_auth else "local"
            return f"[LLM Connection Error] Cannot connect to {mode} model service: {self.api_url}"
        except requests.exceptions.Timeout:
            return f"[LLM Timeout] Model response exceeded {self.timeout} seconds"
        except Exception as e:
            return f"[LLM Error] {str(e)}"
