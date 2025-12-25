# -*- coding: utf-8 -*-
# weixinauto/domain/license_manager.py
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Tuple
import os

import requests

from ..secure.license_core import (
    get_machine_id,
    calc_local_signature,
    build_signed_request,
)


class LicenseNotActivatedError(RuntimeError):
    """当前设备尚未激活时抛出的异常"""
    pass


# ================= 激活文件存放路径（系统级） =================

def _get_license_dir() -> Path:
    system = os.name.lower()
    # Windows：优先用 ProgramData
    if system == "nt":
        base = os.environ.get("PROGRAMDATA")
        if base:
            return Path(base) / "weixinauto"
        # 兜底：用用户本地 AppData
        return Path.home() / "AppData" / "Local" / "weixinauto"
    else:
        # Linux / macOS：~/.config/weixinauto
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            return Path(xdg) / "weixinauto"
        return Path.home() / ".config" / "weixinauto"


LICENSE_DIR = _get_license_dir()
LICENSE_FILE = LICENSE_DIR / "license.json"


class LicenseManager:
    """
    负责：
    - 本地激活文件的读写和校验
    - 和服务器交互进行激活
    - 创建已授权的 WeChatDriver 实例

    机密配置 + 签名算法已经收进 secure.license_core，并会用 Cython 混淆。
    这里尽量只保留“壳”的逻辑，方便开源 / 放到 PyPI。
    """

    def __init__(self, license_file: Optional[Path] = None):
        self.license_file = license_file or LICENSE_FILE
        self._cache: Optional[dict] = None

    # ================= 本地存取 =================

    def _load_local(self) -> Optional[dict]:
        if self._cache is not None:
            return self._cache
        if not self.license_file.exists():
            return None
        try:
            with self.license_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return None

        if not self._verify_local_data(data):
            return None

        self._cache = data
        return data

    def _save_local(self, data: dict) -> None:
        # 确保目录存在
        self.license_file.parent.mkdir(parents=True, exist_ok=True)
        # 重新加签
        machine_id = data.get("machine_id", "") or get_machine_id()
        data["machine_id"] = machine_id
        data["signature"] = self._calc_signature(
            license_key=data.get("license_key", ""),
            machine_id=machine_id,
            expire_at=data.get("expire_at"),
        )
        tmp_path = self.license_file.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp_path.replace(self.license_file)
        self._cache = data

    # ================= 签名与校验 =================

    @staticmethod
    def _calc_signature(
        license_key: str,
        machine_id: str,
        expire_at: Optional[str],
    ) -> str:
        # 直接调用 secure.license_core 里的实现
        return calc_local_signature(license_key, machine_id, expire_at)

    def _verify_local_data(self, data: dict) -> bool:
        """
        本地 license.json 的完整性校验：
        - 签名是否匹配
        - 是否绑定在当前机器
        - 是否过期（如果有过期时间）
        """
        try:
            lic = data.get("license_key", "")
            mid = data.get("machine_id", "")
            exp = data.get("expire_at")
            sig = data.get("signature", "")
            if not lic or not mid or not sig:
                return False
            calc = self._calc_signature(lic, mid, exp)
            if calc != sig:
                return False

            # 机器必须匹配当前设备
            if mid != get_machine_id():
                return False

            # 过期时间校验（如果有）
            if exp:
                try:
                    # 接收 iso 格式（支持末尾 Z）
                    exp_str = exp.replace("Z", "+00:00")
                    dt_exp = datetime.fromisoformat(exp_str)
                    if dt_exp.tzinfo is None:
                        dt_exp = dt_exp.replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    if dt_exp < now:
                        return False
                except Exception:
                    # 解析失败你可以选择直接返回 False，这里我们宽松一点
                    pass

            return True
        except Exception:
            return False

    # ================= 对外方法：本地状态 =================

    def is_activated(self) -> bool:
        """只通过本地文件判断当前设备是否已激活"""
        data = self._load_local()
        return data is not None

    def ensure_activated(self) -> None:
        """未激活则抛 LicenseNotActivatedError"""
        if not self.is_activated():
            raise LicenseNotActivatedError(
                "当前设备尚未激活，请先调用 LicenseManager.activate_with_server(...) 或 Wechat.activate(...) 完成激活。"
            )

    # ================= 对外方法：服务器激活 =================

    def activate_with_server(
        self,
        license_key: str,
        *,
        package_name: Optional[str] = None,
        current_version: Optional[str] = None,
        timeout: float = 8.0,
    ) -> Tuple[bool, Optional[dict]]:
        """
        调用服务器进行激活，并在本地落盘 license 文件。

        返回: (成功与否, 服务器返回的 update 信息)
        - 当前版本不会对 update 做包下载，只是原样返回给上层（方便以后扩展）。
        """
        current_version = current_version or "0.0.0"

        machine_id = get_machine_id()

        # 这里完全交给 secure.license_core 去构造签名请求
        body_bytes, headers, url = build_signed_request(
            license_key=license_key,
            machine_id=machine_id,
            current_version=current_version,
            package_name=package_name,
        )

        resp = requests.post(url, data=body_bytes, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            raise RuntimeError(f"激活请求失败，HTTP {resp.status_code}: {resp.text}")

        try:
            data = resp.json()
        except Exception as e:
            raise RuntimeError(f"激活请求返回不是合法 JSON: {e}") from e

        if not data.get("ok"):
            msg = ""
            lic_info = data.get("license") or {}
            if isinstance(lic_info, dict):
                msg = lic_info.get("message") or ""
            raise RuntimeError(f"激活失败：{msg or '服务器拒绝了该秘钥'}")

        # === 走到这里说明激活成功 ===
        lic_block = data.get("license") or {}
        expire_at = lic_block.get("expire_at")  # 可能是 ISO 字符串，也可能是 null

        # 写本地 license 信息
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        local_data = {
            "license_key": license_key,
            "machine_id": machine_id,
            "expire_at": expire_at,         # 原样保存字符串即可
            "activated_at": now_iso,
            "last_check_at": now_iso,
        }

        update_info = data.get("update") if isinstance(data.get("update"), dict) else None

        # 最后把本地数据落盘
        self._save_local(local_data)

        return True, update_info

    # ================= 对外方法：创建 WeChatDriver =================

    def create_wechat_driver(
        self,
        *,
        current_version: Optional[str] = None,
        silent: bool = False,
    ):
        """
        对外统一入口：
        - silent=False（默认）：未激活则抛 LicenseNotActivatedError（给调试/内部用）
        - silent=True：未激活只返回 None，不抛异常（给 SDK 正式对外用）

        当前版本直接从 weixinauto.infra.uia.wechat_driver 导入：
        - 在你本机开发：是 .py + .pyd 共存，Python 会优先用 .pyd
        - 发给客户时：删除源码，只保留编译后的 .pyd，同样可以 import
        """
        if not self.is_activated():
            if silent:
                return None
            raise LicenseNotActivatedError(
                "当前设备尚未激活，请先调用 Wechat.activate(激活码) 完成激活。"
            )
        from weixinauto.infra.uia.wechat_driver import WeChatDriver
        return WeChatDriver(license_manager=self)
