# 🌸 Fumi Standalone

> **致力于在不同消息平台间传递消息的信使o(*￣▽￣*)ブ**

Fumi 是一个基于 [NATS 服务器](https://github.com/nats-io) 的消息转发工具，旨在为不同消息平台之间构建一条转发通道。

---

## 🚀 快速开始

### 1. 环境准备

确保你的环境中安装了 Python 3.9+。

```bash
# 获取源码
git clone https://github.com/wotsginger/Fumi-Standalone.git
cd fumi-standalone

# 安装依赖
pip install -r requirements.txt

```

### 2. 配置文件 `config.json`

在项目根目录创建并配置你的 `config.json`：

```json
{
  "napcat": {
    "ws_url": "ws://127.0.0.1:3001",
    "token": "你的密钥"
  },
  "nats": {
    "server": "nats://your-nats-server:4222"
  },
  "command": {
    "blocked_prefixes": ["/", ".", "["]
  },
  "groups": [
    {
      "group_id": 123456789,
      "subject": "game_chat",
      "source": "QQ-Main"
    }
  ]
}

```

### 3. 运行

```bash
python main.py
```
