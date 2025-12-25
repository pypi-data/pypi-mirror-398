# chat_listener.pyi
# -*- coding: utf-8 -*-
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import uiautomation as uia

from weixinauto.domain.license_manager import LicenseManager, LicenseNotActivatedError
from weixinauto.infra.uia.wechat_driver import WeChatDriver

from .message import ChatMessage
from .message_extract import MessageType
from .wx_subwindow_ops import ChatSubWindowOps

OnMessage = Callable[..., None]

TARGET_WIN_WIDTH: int
FIXED_OFFX: int
FIXED_OFFY: int
PROBE_MARGIN_H: int
PROBE_MARGIN_V: int

POLL_SEC: float
OPEN_STABILIZE_TRY: int
NICK_MAX_WAIT_SEC: float
NICK_POLL_STEPS: Tuple[float, ...]

WM_KEYDOWN: int
WM_KEYUP: int
VK_RETURN: int
VK_ESCAPE: int
MOUSEEVENTF_LEFTDOWN: int
MOUSEEVENTF_LEFTUP: int
VK_CONTROL: int
VK_V: int
KEYEVENTF_KEYUP: int

_MEDIA_CLIPBOARD_LOCK: threading.Lock
AUTO_SAVE_MAX_TRY: int
AUTO_SAVE_RETRY_DELAY: float
AUTO_SAVE_COPY_TIMEOUT: float


def _is_alive(ctrl: Optional[uia.Control]) -> bool: ...
def _runtime_id_hex(node: Any) -> Optional[str]: ...
def _get_full_uia_text(item: uia.Control) -> str: ...
def _extract_file_name(item: uia.Control, raw_text: Optional[str] = ...) -> Optional[str]: ...
def _msg_key(node: Any, text_for_key: str) -> Optional[str]: ...
def _hash_text_for_echo(s: str) -> str: ...
def _scroll_into_view(node: Any) -> None: ...
def _set_clipboard_files(paths: List[str]) -> bool: ...


def _reply_enter_only(
    win: uia.Control,
    content: str,
    *,
    mode: str = "text",
) -> bool: ...


def _avatar_xy_of_item(item: uia.Control) -> Optional[tuple[int, int]]: ...
def _click_avatar_once(item: uia.Control) -> bool: ...


@dataclass(eq=False)
class ChatWnd:
    title: str

    _reply_fn: Optional[Callable[[str], bool]]
    _incoming_cache: List[str]
    _lock: threading.Lock

    def _update_reply_fn(self, fn: Callable[[str], bool]) -> None: ...
    def _record_incoming(self, text: str, is_self: Optional[bool]) -> None: ...
    def reply(self, text: str) -> bool: ...
    def reply_file(self, file_path: str) -> bool: ...


class ChatWindowListener(threading.Thread):
    """
    单个聊天子窗口监听线程。
    """

    title: str
    on_message: OnMessage
    need_nickname: bool
    poll: float
    debug_nick: bool

    _stop: threading.Event
    _win: Optional[uia.Control]
    _last_key: Optional[str]
    _last_noid_text: Optional[str]

    _use_echo: bool
    _recent_sent: List[tuple[int, str]]

    _lm: LicenseManager
    _driver: WeChatDriver
    _resolver: Any
    _lock: threading.Lock

    _auto_save_image: bool
    _auto_save_file: bool
    _save_base_dir: Optional[str]
    _ops: ChatSubWindowOps

    _cb_param_count: int

    def __init__(
        self,
        title: str,
        on_message: OnMessage,
        *,
        driver: Optional[WeChatDriver],
        need_nickname: bool = ...,
        license_manager: Optional[LicenseManager] = ...,
        poll_sec: float = ...,
        debug_nick: bool = ...,
        auto_save_image: bool = ...,
        auto_save_file: bool = ...,
        save_base_dir: Optional[str] = ...,
    ) -> None: ...

    # 生命周期
    def stop(self) -> None: ...
    def push_outgoing_preview(self, text: str) -> None: ...

    # 内部工具
    def _bind_window_or_raise(self) -> None: ...
    def _make_reply_callable(self) -> Callable[[str], bool]: ...
    def _bring_front_and_stabilize(self) -> None: ...
    def _get_nickname(self, item: uia.Control) -> Optional[tuple[bool, str]]: ...

    def _auto_save_media_if_needed(
        self,
        item: uia.Control,
        mtype: MessageType,
    ) -> Optional[str]: ...

    # 线程主循环
    def run(self) -> None: ...


class MultiChatManager:
    _listeners: Dict[str, ChatWindowListener]
    _chat_wnd_by_title: Dict[str, ChatWnd]
    _lock: threading.Lock
    _msg_queue: Dict[ChatWnd, List[ChatMessage]]

    _need_nickname_default: bool
    _poll_sec_default: float
    _lm: LicenseManager
    _driver: WeChatDriver

    _auto_save_image_default: bool
    _auto_save_file_default: bool
    _save_base_dir_default: Optional[str]

    _user_cb: Optional[OnMessage]
    _user_cb_param_count: int

    def __init__(
        self,
        titles: Iterable[str],
        on_message: Optional[OnMessage] = ...,
        *,
        driver: WeChatDriver,
        need_nickname: bool = ...,
        poll_sec: float = ...,
        license_manager: Optional[LicenseManager] = ...,
        bring_front_on_new: Optional[bool] = ...,
        auto_save_image: bool = ...,
        auto_save_file: bool = ...,
        save_base_dir: Optional[str] = ...,
    ) -> None: ...

    def add_listens(
        self,
        titles: Iterable[str],
        *,
        need_nickname: Optional[bool] = ...,
        poll_sec: Optional[float] = ...,
        auto_save_image: Optional[bool] = ...,
        auto_save_file: Optional[bool] = ...,
        save_base_dir: Optional[str] = ...,
    ) -> None: ...

    def _on_message_from_listener(
        self,
        group: str,
        msg: ChatMessage,
        reply_callable: Optional[Callable[[str], bool]] = ...,
    ) -> None: ...

    def start_all(self) -> None: ...
    def stop_all(self, *, join: bool = ..., timeout: float = ...) -> None: ...
    def alive(self) -> Dict[str, bool]: ...
    def push_outgoing_preview(self, title: str, text: str) -> None: ...

    def get_listen_messages(
        self,
        *,
        clear: bool = True,
    ) -> Dict[ChatWnd, List[ChatMessage]]: ...

    def get_chat_wnd(self, title: str) -> Optional[ChatWnd]: ...
