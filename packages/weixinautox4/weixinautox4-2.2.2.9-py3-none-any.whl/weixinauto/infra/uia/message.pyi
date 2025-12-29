# message.pyi
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from .message_extract import MessageType


class MessageAction(Protocol):
    """
    动作接口：具体实现由 DefaultMessageActions 完成。
    这里只定义签名，避免循环依赖。
    """

    def save_file(
        self,
        msg: ChatMessage,
        base_dir: Optional[str] = None,
    ) -> Optional[str]:
        ...

    def save_image(
        self,
        msg: ChatMessage,
        base_dir: Optional[str] = None,
        # base_dir: Optional[str] = None,
    ) -> Optional[str]:
        ...


@dataclass
class ChatMessage:
    """
    微信一条消息的抽象：
      - group: 群名 / 会话名
      - text: 解析后的纯文本
      - ts:   时间戳（float）
      - mtype: 消息类型（文本 / 图片 / 文件 / …）
      - raw_text: 原始文本（带换行）
      - is_self: 是否自己发的
      - sender: 昵称（开启 need_nickname=True 时才会有）
      - internal_tag: 内部标签，用来做“自回声”等标记
      - file_name: 文件名称
      - file_path: 文件路径
    """

    group: str
    text: str
    ts: float
    mtype: MessageType
    raw_text: str = ...
    is_self: Optional[bool] = ...
    sender: Optional[str] = ...
    internal_tag: Optional[str] = ...
    file_name: Optional[str] = ...
    file_path: Optional[str] = ...

    # 运行时字段（监听时填充）
    _key: Optional[str] = ...
    _node: Optional[object] = ...
    actions: Optional[MessageAction] = ...

    def bind_actions(self, actions: MessageAction) -> None:
        ...

    def save_file(self, base_dir: Optional[str] = None) -> Optional[str]:
        ...

    def save_image(self, base_dir: Optional[str] = None) -> Optional[str]:
        ...
