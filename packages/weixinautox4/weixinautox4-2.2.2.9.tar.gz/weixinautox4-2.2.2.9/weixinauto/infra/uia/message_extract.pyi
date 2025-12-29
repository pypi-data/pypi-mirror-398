# message_extract.pyi
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List
import uiautomation as uia

TARGET_WIN_WIDTH: int


class MessageType:
    TEXT: str
    IMAGE: str
    VOICE: str
    VIDEO: str
    FILE: str
    SYSTEM: str
    TRANSFER: str
    RED_ENVELOPE: str


def classify_by_classname(item: uia.Control) -> str: ...
def _node_text_candidates(n) -> List[str]: ...
def extract_text_deep(node) -> str: ...
