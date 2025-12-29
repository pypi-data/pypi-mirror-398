from __future__ import annotations

import uiautomation as uia
from ctypes import wintypes
from typing import Optional, Dict, List

from weixinauto.domain.license_manager import LicenseManager, LicenseNotActivatedError
from weixinauto.infra.uia.selectors.resolver import SelectorResolver

# 常量（给类型提示用）
MOUSE_LEFTDOWN: int
MOUSE_LEFTUP: int

FIRST_SESSION_OFFX: float
FIRST_SESSION_OFFY: float


class WeChatDriver:
    """
    微信窗口自动化驱动类：
    - 查找微信主窗口
    - 打开 / 聚焦聊天窗口
    - 向指定会话发送文本消息
    """

    ALLOWED_EXE: set[str]

    def __init__(
        self,
        weixin_name: Optional[str] = None,
        license_manager: Optional[LicenseManager] = None,
    ) -> None: ...

    # ---------- 主窗 / 句柄相关（一般用户不用） ----------

    def _ensure_licensed(self, hard: bool = False) -> bool: ...
    def _find_wechat_window(self) -> None: ...
    def _find_wechat_hwnd_fast(self) -> Optional[int]: ...
    def _find_wechat_hwnd(self) -> Optional[int]: ...
    def _focus_main(self) -> None: ...
    def _root(self) -> uia.Control: ...

    # 调试：把鼠标移动到第一个会话位置（不点击）
    def debug_move_mouse_to_first_session(
        self,
        offx: int = ...,
        offy: int = ...,
    ) -> None: ...

    # ---------- 子窗口查找 ----------

    def find_wechat_child_hwnd(
        self,
        target_title: Optional[str] = None,
    ) -> Optional[int]:
        """
        查找聊天子窗口句柄（ClassName = mmui::ChatSingleWindow）
        - target_title 为空：返回第一个聊天子窗
        - target_title 不为空：匹配标题包含该字符串的子窗
        """
        ...

    def find_wechat_child_hwnd_fast(self, target_title: str) -> Optional[int]: ...
    def find_chat_subwindow(
        self,
        title: Optional[str] = None,
        timeout_sec: float = 1.5,
    ) -> Optional[uia.Control]: ...

    # ---------- 会话列表操作 ----------

    def get_session_list(self) -> Optional[uia.Control]: ...

    def find_session_item(
        self,
        title: str,
        *,
        fuzzy: bool = False,
        timeout_sec: float = 0.3,
        max_scan: int = 40,
    ) -> Optional[uia.Control]:
        """
        在侧边会话列表中查找某一项（群名 / 聊天名）
        """
        ...

    def activate_session_item(
        self,
        item: uia.Control,
        prefer_invoke: bool = True,
        settle_ms: int = 160,
    ) -> bool: ...

    # ---------- 打开会话窗口 ----------

    def ensure_chat_window_open_fast(
        self,
        name: str,
        *,
        fuzzy: bool = False,
        main_focus_timeout: float = 0.0,
        search_enter_settle_ms: int = 120,
        list_scan_ms: int = 500,
        after_open_wait_ms: int = 500,
    ) -> bool:
        """
        极速打开指定会话的聊天子窗口：
        - 通过搜索框输入会话名称
        - 回车
        - 双击列表中的第一条会话
        """
        ...

    # 兼容接口：直接切换到某个聊天窗口（依赖窗口标题 Name）
    def switch_to_chat_window(self, recipient: str) -> bool: ...

    # ---------- 发消息接口 ----------

    def send_text_to_chat(
        self,
        chat_name: str,
        text: str,
        *,
        case_insensitive: bool = True,
        wait_child_sec: float = 1.2,
        wait_btn_sec: float = 1.2,
        strict: bool = False,
    ) -> bool:
        """
        向指定会话发送文本消息：
        1) 搜索框定位会话
        2) 进入会话
        3) 填充输入框文本
        4) 回车发送
        """
        ...
    def send_file_to_chat(
            self,
            chat_name: str,
            file_path: str,
            *,
            case_insensitive: bool = True,
            wait_child_sec: float = 1.2,
            strict: bool = False,
    ) -> bool:
    # 旧版简单接口：使用当前聊天窗口发送消息
    def send_message(self, message: str) -> bool: ...

    # ---------- 生命周期 ----------

    def shutdown(self) -> None: ...


__all__ = [
    "WeChatDriver",
    "FIRST_SESSION_OFFX",
    "FIRST_SESSION_OFFY",
]
