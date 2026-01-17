# 🌸 Fumi Standalone

> **致力于在不同消息平台间传递消息的信使o(*￣▽￣*)ブ**

Fumi 是一个基于 [NATS 服务器](https://github.com/nats-io) 的消息转发工具，旨在为不同消息平台之间构建一条转发通道。

我们假定消息分布在多个平台，并且存在多个来源，通过内置的 API、协议库、机器人进行相互的消息转发。

所有消息会按照统一的格式发送到 NATS 中心服务器上，再分别由各个客户端进行解析。

---

## 🚀 快速开始

### 1. 环境准备

确保你的环境中安装了 Python 3.9+。非常建议运行在虚拟环境中。

```bash
# 获取源码
git clone https://github.com/wotsginger/Fumi-Standalone.git
cd fumi-standalone

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置文件 `config.json`

在项目根目录创建并配置你的 `config.json`；

通过正向 Websocket（作为客户端对接Websocket服务器）对接支持 Onebot V11 的机器人协议。

因此需要填入对应的 Websocket 地址，同时如果有鉴权需要填入 Token；

在配置中填入对应的 NATS 的服务器地址和 Token；可以使用我社提供的 nats://web.sitmc.club:4222。如果对于信息安全有所顾虑，可以自行部署 NATS 服务器。

Command 中可以设置不被转发的消息头，如果群内有其他 Bot 可以通过这种方式屏蔽转发命令；

Groups 中可以设置指定的转发群组，其中 ID 为 QQ 群号，subject 是设置转发对应的频道， subject 相同的频道内消息会相互转发，subject 也可以是子节点的形式，例如设置为sitmc.chat。
source 则是用于标注频道自身的身份，即消息来源。

所有消息都会以 {"source":"","message":"","username":""} 的格式发送到 NATS 服务器对应的 subject 交由其他客户端解析。

注意：如果两个 QQ 群的 subject 相同，那么它们之间的群消息也会被相互转发，你也可以用这个办法将多个群聊连接在一起（？这真的会有人用吗）。

```json
{
  "ws": {
    "ws_url": "ws://127.0.0.1:3001",
    "token": "你的密钥"
  },
  "nats": {
    "server": "nats://your-nats-server:4222",
    "token": ""
  },
  "command": {
    "blocked_prefixes": ["/", ".", "["]
  },
  "groups": [
    {
      "group_id": 123456789,
      "subject": "game_chat",
      "source": "QQ-Main"
    },
    {
      "group_id": 123456789,
      "subject": "example",
      "source": "QQ"
    }
  ]
}
```

### 3. 运行

```bash
python main.py
```
