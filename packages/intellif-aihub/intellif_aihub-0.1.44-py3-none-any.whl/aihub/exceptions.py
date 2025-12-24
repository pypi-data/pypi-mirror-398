from __future__ import annotations

from typing import Any, Optional

from httpx import Response
from pydantic import ValidationError


class SDKError(Exception):
    pass


AIHUB_ERROR_CODES = {
    1: "未知的异常，请联系管理员",
    2: "无法找到当前的资源",
    3: "数据库错误",
    8: "已经存在同名的资源",
}


# --- 优化后的 APIError ---
class APIError(SDKError):
    """
    当 API 请求返回一个非 2xx 状态码时抛出。
    """

    def __init__(self, message: str, status: Optional[int] = None, detail: Any = None) -> None:
        # super().__init__(message) 依然是好的实践
        super().__init__(message)

        self.message: str = message
        self.status: Optional[int] = status
        self.detail: Any = detail

    def __str__(self) -> str:
        """
        为用户提供一个清晰的、可读的错误信息。
        """
        if self.status == 401:
            return "请检查您的凭证信息，可能已经过期。"

        # 优化：在 __str__ 中包含更多上下文
        parts = []
        if self.status:
            parts.append(f"[HTTP {self.status}]")

        parts.append(self.message)

        # 如果 detail 不是 None 且不为空，也显示它
        if self.detail:
            parts.append(f"(Detail: {self.detail})")

        return " ".join(parts)

    def __repr__(self) -> str:
        """
        为开发者提供一个明确的、用于调试的表示。
        在 Traceback 和日志中显示。
        """
        class_name = self.__class__.__name__

        # 使用 !r 来获取 message 和 detail 的 repr() 表示 (例如，为字符串添加引号)
        parts = [f"message={self.message!r}"]

        if self.status is not None:
            parts.append(f"status={self.status!r}")

        if self.detail is not None:
            parts.append(f"detail={self.detail!r}")

        return f"{class_name}({', '.join(parts)})"

    @classmethod
    def from_response(cls, response: Response) -> "APIError":
        """
        (高级优化)
        从一个 httpx.Response 对象方便地创建 APIError。
        """
        # 确保在调用此方法前，响应体已被读取
        # (例如在你的 _raise_for_status 钩子中调用了 response.read())

        try:
            # 尝试解析 JSON 作为 detail
            detail = response.json()

            # 尝试从常见的错误结构中提取 message
            # (例如 {"message": "error msg"}, {"error": "error msg"}, {"detail": "error msg"})
            if isinstance(detail, dict):
                msg = detail.get("message", detail.get("error", detail.get("detail", response.text)))
                # 如果 msg 还是一个 dict/list，就回退到用 text
                if not isinstance(msg, str):
                    msg = response.text
            else:
                msg = response.text

        except Exception:
            # 如果 JSON 解析失败，则 detail 和 message 都使用 text
            detail = response.text
            msg = response.text

        # 如果消息过长，截断它 (可选)
        if len(msg) > 200:
            msg = msg[:200] + "..."

        return cls(
            message=msg.strip() or f"API request failed",  # 确保 message 不为空
            status=response.status_code,
            detail=detail,
        )


def loc_to_dot_sep(loc: tuple[str | int, ...]) -> str:
    path = ""
    for i, x in enumerate(loc):
        if isinstance(x, str):
            if i > 0:
                path += "."
            path += x
        elif isinstance(x, int):
            path += f"[{x}]"
        else:
            raise TypeError("Unexpected type")
    return path


def convert_errors(e: ValidationError) -> list[dict[str, Any]]:
    new_errors: list[dict[str, Any]] = e.errors()
    for error in new_errors:
        error["loc"] = loc_to_dot_sep(error["loc"])
    return new_errors
