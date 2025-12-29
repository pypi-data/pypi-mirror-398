from setuptools import setup, find_packages

setup(
    name="weixinautox4",  # 包名
    version="2.2.2.9",      # 版本号
    description="WeChat automation SDK with license management.",
    author="agentaibot",
    author_email="zhilongfeng66@gmail.com",
    python_requires=">=3.11,<3.12",
    # 这里不要再 include 顶层 pyarmor_runtime_xxx 了，只收 weixinauto 这棵树
    packages=find_packages(include=["weixinauto", "weixinauto.*"]),

    install_requires=[
        "requests>=2.24.0",
        "Cython>=0.29.21",
        "pydantic>=1.8.2",
        "Pillow>=9.0.0",
        "pywin32==311",
        "uiautomation==2.0.29",
    ],

    include_package_data=True,

    package_data={
        # PyArmor runtime：一定要加上这个 key（包名要和目录结构一一对应）
        "weixinauto.infra.uia.pyarmor_runtime_009672": [
            "pyarmor_runtime.*",   # 这样 .pyd 会被打包进去
        ],
        # uia 的 JSON 选择器
        "weixinauto.infra.uia": [
            "selectors/*.json",
            "*.pyi",          # ← 新增：打包所有 .pyi
        ],
        "weixinauto": [
            "*.pyi",          # ← 新增：例如 wechat.pyi
        ],
        # secure 下只打 pyd（license_core 原始 py 你自己留在源码工程）
        "weixinauto.secure": [
            "license_core.*",
        ],
    },

    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
)
