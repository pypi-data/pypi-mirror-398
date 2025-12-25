# weixin_newmessage.pyi
# -*- coding: utf-8 -*-
from __future__ import annotations

import threading
from typing import Callable, List, Optional

import uiautomation as uia

from .message import ChatMessage
from .message_extract import MessageType


def _bfs_children(root: uia.Control, max_nodes: int = 8000) -> List[uia.Control]: ...


class WeixinNewMessage:
    """
    主窗口新消息扫描器（单次流程版，按「X条未读」真实取多条消息）。
    """

    def __init__(
        self,
        driver: WeChatDriver,
        *,
        click_delay: float = 0.5,
        keep_foreground: bool = True,
        need_nickname: bool = False,
    ) -> None: ...

    # 会话过滤规则
    def _get_nickname_from_avatar(self, win: uia.Control, item: uia.Control) -> tuple[Optional[bool], Optional[str]]: ...
    def _is_mute_session(self, raw_name: str) -> bool: ...
    def _make_message_hash(
        self,
        group_title: str,
        node: uia.Control,
        text: str,
        mtype: MessageType,
    ) -> str: ...
    def reply(self, msg: ChatMessage, text: str) -> bool: ...
    def _is_official_or_public_session(self, title: str, raw_name: str, auto_id: str) -> bool: ...
    def _parse_unread_from_name(self, raw_name: str) -> tuple[str, int]: ...

    # 主窗口相关
    def _get_hwnd_from_driver(self) -> int: ...
    def _get_main_window_once(self) -> Optional[uia.Control]: ...
    def _ensure_main_window_ready(self, timeout_sec: float = 3.0) -> Optional[uia.Control]: ...
    def _ensure_main_foreground(self, main_win: uia.Control) -> None: ...

    # 「微信」Tab 查找与点击
    def _locate_message_tab(self, main_win: uia.Control) -> Optional[uia.Control]: ...
    def _click_control(self, ctrl: uia.Control, *, double: bool = False) -> bool: ...

    # 会话列表 & 消息列表
    def _get_session_list(self, main_win: uia.Control) -> Optional[uia.Control]: ...
    def _get_message_list(self, main_win: uia.Control) -> Optional[uia.Control]: ...

    # 工具：遍历会话列表（带滚动）
    def _iter_session_items_with_scroll(
        self,
        sess_list: uia.Control,
        *,
        max_rounds: int = 20,
    ) -> List[uia.Control]: ...

    # 核心：对单个会话，根据“X条未读”收集多条消息
    def _extract_last_k_messages(
        self,
        main_win: uia.Control,
        group_title: str,
        unread_count: int,
    ) -> List[ChatMessage]: ...

    def is_right_side_obstructed(self, main_win: uia.Control) -> bool: ...

    # 核心：单次扫描“有未读”的会话，并按数量取多条消息
    def scan_once(self) -> List[ChatMessage]: ...

    # 单次异步扫描（线程跑一次就结束）
    def scan_once_async(self, callback: Optional[Callable[[List[ChatMessage]], None]] = None) -> None: ...

    # 内部监听线程（for 循环测试版）
    def _watch_loop(self) -> None: ...

    def start_watch(
        self,
        callback: Callable[[List[ChatMessage]], None],
        *,
        interval_sec: float = 1.0,
        max_rounds: int = 10,
    ) -> None: ...

    def stop_watch(self) -> None: ...

    def get_last_results(self) -> List[ChatMessage]: ...
