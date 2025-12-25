# WeixinAuto（Windows 微信自动化）

基于 UIAutomation 的微信 PC 端自动化工具，用来：

- 打开 / 切换聊天窗口  
- 发送文本消息  
- 监听指定群 / 会话的新消息  
- 批量监听多个群，并统一处理消息  

> ⚠️ 仅支持 **Windows + 新版微信（`weixin.exe`）**，并且需要保持微信登录状态。

---

## 环境要求

- Windows 10 | 11
- Python 3.10+（建议）  
- PC 微信客户端4.1版本以上的（`weixin.exe`）  
- 依赖库：
  - `uiautomation`
  - 以及项目自带的其他依赖（建议用 `requirements.txt` 安装）

```bash
  pip install -r requirements.txt
```

---

## 核心类概览

主要对外只需要关心一个类：`Wechat`

```python
from weixinauto.wechat import Wechat
```

核心能力：

- `send_message(target, text)`：给指定的target目标发送消息
- `send_file(target, file_path)`：给指定的target目标发送文件
- `add_listen_chat(title, on_new, ...)`：监听单个会话（回调模式）
- `add_listens(titles, ...) + start_listen() + get_listen_message()`：批量监听（轮询模式）
- `stop_listen(title=None)`：停止监听

---

## 1. 激活示例

首次运行必须要激活才能实例化对象：

```python
from weixinauto.wechat import Wechat

wx = Wechat()

# 直接按会话名发送（群名 / 好友昵称）
ok = wx.activate("LIC-XGFD8TF3-QTKIZ8Q5")

print("发送结果：", ok)
```

说明：

- 一台电脑一个授权码，授权码有效期为1年：
  1. 联系wx:agentaibot获得授权码
  2. 每个授权码一年300元
---

## 2. 发送消息示例

向指定群 / 好友发送一条文本消息（稳定）：

```python
from weixinauto.wechat import Wechat

wx = Wechat()

# 直接按会话名发送（群名 / 好友昵称）
ok = wx.send_message("工作群", "大家好，我是机器人~")

print("发送结果：", ok)
```

说明：

- 内部会自动：
  1. 打开 / 切换到对应聊天窗口（搜索框搜索 + 回车）
  2. 找到输入框
  3. 写入文本并发送

---
## 3. 发送文件示例

向指定群 / 好友发送一条文本消息：

```python
from weixinauto.wechat import Wechat

wx = Wechat()

# 直接按会话名发送（群名 / 好友昵称）
ok = wx.send_file("工作群", r"E:\1.jpg")

print("发送结果：", ok)
```

说明：

- 内部会自动：
  1. 打开 / 切换到对应聊天窗口（搜索框搜索 + 回车）
  2. 找到输入框
  3. 粘贴文件并发送

---
## 4. 单个窗口监听（回调方式）

### 4.1 回调函数签名

推荐签名：

```python
def on_new(group: str, msg, reply):
    ...
```

- `group`: 当前消息所属群 / 会话标题（字符串）
- `msg`: `ChatMessage` 对象，包含：
  - `msg.group`   → 群名 / 会话名  
  - `msg.text`    → 文本内容（去掉尾部空白）  
  - `msg.raw_text`→ 原始文本（包含尾部空白）  
  - `msg.ts`      → 时间戳（float）  
  - `msg.mtype`   → 消息类型（文本 / 图片 / 红包 / 转账等）  
  - `msg.is_self` → 是否为自己发的消息（True / False / None）  
  - `msg.sender`  → 发送者昵称（`need_nickname=True` 且解析成功时）  
- `reply`: 一个函数 `reply(text: str) -> bool`，用于回复当前窗口  

> 如果你的回调只写两个参数（`def on_new(group, msg):`），也支持，只是收不到 `reply` 函数。

### 4.2 示例：监听一个群并自动回复

```python
import time
from weixinauto.wechat import Wechat


def on_new(group, msg, reply):
    print(f"收到新消息，来自群组：{group}")
    print(f"消息内容：{msg.text}")
    print(f"发送人：{msg.sender}，是否自己：{msg.is_self}")

    # 简单示例：别人说“1”，我回“收到1”
    if msg.text == "1" and not msg.is_self:
        reply("收到1")


def main():
    wx = Wechat()

    # 打开 + 监听单个群（不需要昵称 → 不会点头像，不会移动鼠标）
    ok = wx.add_listen_chat(
        title="工作群",
        on_new=on_new,
        interval_sec=0.18,
        need_nickname=False,  # 若为 True，会点击头像获取昵称
    )
    if not ok:
        print("监听失败，请确认已加入该群并能正常搜索到。")
        return

    print("开始监听：工作群")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("停止监听")
        wx.stop_listen("工作群")


if __name__ == "__main__":
    main()
```
消息必须要判断msg.is_self是不是自己发的，如果是就不要再回复了，这里做了回声检测。

---

## 5. 批量监听多个群（轮询方式）

如果你需要同时监听很多个群，并统一拉取所有新消息做处理，推荐使用：

- `add_listens(...)`
- `start_listen()`
- `get_listen_message()`

这一套。
> wx.add_listen_chat("工作群", on_message,auto_save_image=True,auto_save_file=True)
- auto_save_image=True开启图片下载,auto_save_file=True开启文件下载
- 文件下载成功后，msg.file_path就是图片或者文件的路径。

### 5.1 启动批量监听

```python
import time
from weixinauto.wechat import Wechat
from weixinauto.infra.uia.message import ChatMessage


def main():
    wx = Wechat()

    # 需要监听的群 / 会话列表
    groups = ["工作群", "测试群A", "测试群B"]

    # 1) 批量添加监听（内部会自动尝试打开这些会话窗口）
    wx.add_listens(
        titles=groups,
        need_nickname=False,  # 批量监听一般建议关闭昵称点击
        poll_sec=0.15,
    )

    # 2) 启动所有监听线程
    wx.start_listen()

    print("开始批量监听：", groups)

    try:
        while True:
            # 3) 定期拉取所有新消息（默认取一次就清空内部队列）
            mp = wx.get_listen_message(clear=True)  # { group_title: [ChatMessage, ...] }

            for group_title, msgs in mp.items():
                for msg in msgs:  # type: ChatMessage
                    print(f"[{group_title}] {msg.sender or '未知'}: {msg.text}")

                    # 示例：简单自动回复
                    if not msg.is_self and msg.mtype == "text":
                        wx.send_message(group_title, "pong")

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("停止所有监听")
        wx.stop_listen()  # 不传 title → 停止所有监听


if __name__ == "__main__":
    main()
```

### 5.2 `get_listen_message` / `get_listen_messages` 返回结构

**简单版本（按标题返回）：**

```python
mp = wx.get_listen_message(clear=True)
# 返回：
# {
#     "工作群": [ChatMessage, ChatMessage, ...],
#     "测试群A": [...],
#     ...
# }
```

如果你想拿到 `ChatWnd` 对象（每个窗口都自带 `reply()`），可以用底层的：

```python
from weixinauto.infra.uia.chat_listener import ChatWnd, ChatMessage

mp2: dict[ChatWnd, list[ChatMessage]] = wx.get_listen_messages(clear=True)
for chat_wnd, msgs in mp2.items():
    print(chat_wnd.title)
    for msg in msgs:
        print("  >>", msg.text)
    # 统一从这个窗口回复
    chat_wnd.reply("统一从 ChatWnd.reply 回复")
```

---

## 6. 回声防止机制说明

为了避免机器人“自言自语”死循环，内部做了两层防护：

1. **发送回声检测**（`ChatWnd.reply` 内部）  
   - 如果当前要发送的内容，与最近收到的消息文本完全一致，会认为是“回声测试”，直接跳过本次发送。
2. **窗口 + 文本哈希缓存**  
   - 对于同一个聊天窗口，如果同一条文本刚刚发过一遍，会认为是重复触发，不再发送。

只要你的逻辑不是：

> 收到 A → 原样回 A → 收到 A（自己）再回 A → ……

一般都不会出现无限循环。
> 另外调用在调用自动回复的时候，一定要注意判断消息的发送人，如果是自己发送的，直接拒绝回复。
> if not msg.is_self and msg.mtype == "text" 标准写法。
> 消息返回的时候，系统消息也会返回，比如时间消息。

---

## 7. 主窗口消息监听

主窗口消息监听采用了线程锁：

```python
def on_new(
    msgs: List[ChatMessage],
    reply: Callable[[ChatMessage, str], None]
) -> None:
    print("==== 本轮未读会话 ====")
    for m in msgs:
        print(f"[{m.group}] -> {m.text} -> {m.sender} -> {m.is_self} - {m.mtype}")
        if m.text and "测试" in m.text:
            time.sleep(0.3)
            ok = reply(m, "这是自动回复：收到你的测试消息啦～")
            print(f"[Reply] to {m.group}: {'OK' if ok else 'FAIL'}")
            
wx.get_new_message(on_new, interval_sec=2.0)

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("收到 Ctrl+C，中止监听...")
    finally:
        # 如果你在 Wechat 里实现了 stop_listen，可以顺带优雅关闭
        try:
            wx.stop_new_message_listen()
        except AttributeError:
            pass
```

1. **目前处于内测阶段**  
   - 并发情况下消息会丢失，昵称获取还在开发中
2. **消息回复**  
   - 消息在回复时会锁定线程，监听会停止，回复完成后，监听恢复。

---

## 8. 停止与清理

- **停止单个监听窗口**（`add_listen_chat` 创建的那个）：

```python
wx.stop_listen("工作群")
```

- **停止所有监听**（包括单个监听 + 批量监听）：

```python
wx.stop_listen()
```

- **完整关闭（包括 driver 清理）**：

```python
wx.shutdown()
```

---

## 9. 常见注意事项
1. **后续更新内容**  
2. 监听主窗口新消息
3. 下载图片，视频消息
4. 多窗口回复文件消息

## 10. 常见注意事项

1. **必须保持微信已登录且主窗口可见**  
2. 若开启 `need_nickname=True`：
   - 内部会通过点击头像弹出名片来解析昵称
   - 可能短暂移动鼠标、抢占前台窗口，适合「专用机器」或「前台机器人」场景  
3. 若对前台干扰敏感，建议：
   - 所有监听都使用 `need_nickname=False`
   - 不需要 `msg.sender` 和 `msg.is_self` 的精确判断也可以正常工作  

---

后续如果你再加登录检测、导航栏点击、昵称设置校验之类的功能，可以在这个 README 下面再扩一节「高级功能」。  
