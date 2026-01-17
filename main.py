import asyncio
import json
from datetime import datetime
import websockets
from nats.aio.client import Client as NATS

# ------------------ 配置 ------------------
try:
    with open("config.json", "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print("\033[31m[错误] 找不到 config.json 文件！\033[0m")
    exit(1)

WS_URL = CONFIG["ws"]["ws_url"]
WS_TOKEN = CONFIG["ws"].get("token")
NATS_SERVER = CONFIG["nats"]["server"]
NATS_TOKEN = CONFIG["nats"].get("token")  # 新增
BLOCKED_PREFIXES = tuple(CONFIG["command"].get("blocked_prefixes", []))
GROUPS_CONFIG = CONFIG.get("groups", [])

current_ws = None
nc = NATS()
subscriptions = []

def log(category: str, message: str, color: str = "37"):
    time_str = datetime.now().strftime("%H:%M:%S")
    print(f"\033[{color}m[{time_str}] [{category}] {message}\033[0m")

def is_ws_active(ws):
    if ws is None: return False
    try:
        return not ws.closed
    except AttributeError:
        return True

async def send_group_msg(group_id: int, text: str):
    global current_ws
    if not is_ws_active(current_ws): return
    try:
        await current_ws.send(json.dumps({
            "action": "send_group_msg",
            "params": {"group_id": group_id, "message": text}
        }))
    except Exception:
        pass

async def connect_nats():
    if not nc.is_connected:
        try:
            # 支持 token
            options = {"servers": [NATS_SERVER]}
            if NATS_TOKEN:
                options["token"] = NATS_TOKEN
            await nc.connect(**options)
            log("NATS", f"连接成功: {NATS_SERVER}", "32")
        except Exception as e:
            log("ERROR", f"NATS 连接失败: {e}", "31")
            raise e

async def setup_forwarding():
    """根据 config 中的 groups 配置初始化所有转发任务"""
    global subscriptions
    await connect_nats()

    # 清理内存中的旧订阅
    for sub in subscriptions:
        try:
            await sub.unsubscribe()
        except:
            pass
    subscriptions.clear()

    for g_cfg in GROUPS_CONFIG:
        gid, subj, src = g_cfg["group_id"], g_cfg["subject"], g_cfg.get("source", "QQ")

        def make_handler(target_gid, self_src):
            async def handler(msg):
                global current_ws
                if not is_ws_active(current_ws): return
                try:
                    data = json.loads(msg.data.decode())
                    if data.get("source") == self_src: return

                    username = data.get('username', '未知用户')
                    content = data.get('message', '')
                    remote_src = data.get('source', 'Remote')

                    log("NATS->QQ", f"群 {target_gid} | <{username}> {content}", "36")
                    await send_group_msg(target_gid, f"[{remote_src}] <{username}> {content}")
                except Exception as e:
                    log("ERROR", f"NATS 处理异常: {e}", "31")

            return handler

        sub_obj = await nc.subscribe(subj, cb=make_handler(gid, src))
        subscriptions.append(sub_obj)
        log("SYSTEM", f"激活: 群 {gid} (主题: {subj} | 标识: {src})", "32")

def extract_text(raw_msg):
    if isinstance(raw_msg, list):
        return "".join(s["data"]["text"] for s in raw_msg if s["type"] == "text").strip()
    return str(raw_msg).strip()

async def handle_qq_message(event: dict):
    """处理 QQ 消息并发布到 NATS"""
    if event.get("post_type") != "message" or event.get("message_type") != "group":
        return

    group_id = event["group_id"]
    cfg = next((g for g in GROUPS_CONFIG if g["group_id"] == group_id), None)
    if not cfg: return

    text = extract_text(event.get("message"))
    if not text or text.startswith(BLOCKED_PREFIXES): return

    sender_name = event.get("sender", {}).get("nickname", "未知")
    payload = {
        "source": cfg.get("source", "QQ"),
        "username": sender_name,
        "message": text
    }

    log("QQ->NATS", f"群 {group_id} | {sender_name}: {text}", "34")
    try:
        await nc.publish(cfg["subject"], json.dumps(payload).encode())
    except Exception as e:
        log("ERROR", f"NATS 发布失败: {e}", "31")

async def main():
    global current_ws
    retry_delay = 1
    headers = {"Authorization": f"Bearer {WS_TOKEN}"} if WS_TOKEN else {}

    while True:
        try:
            log("SYSTEM", f"连接 WebSocket: {WS_URL}", "32")
            async with websockets.connect(WS_URL, extra_headers=headers) as ws:
                current_ws = ws
                log("SYSTEM", "WebSocket 连接成功", "32")
                retry_delay = 1

                await setup_forwarding()

                async for msg in ws:
                    try:
                        event = json.loads(msg)
                        if event.get("post_type") != "meta_event":
                            await handle_qq_message(event)
                    except Exception as e:
                        log("ERROR", f"事件循环异常: {e}", "31")

        except Exception as e:
            log("ERROR", f"连接断开: {e}", "31")
            current_ws = None
            for sub in subscriptions:
                try:
                    await sub.unsubscribe()
                except:
                    pass
            subscriptions.clear()

            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("SYSTEM", "程序手动停止", "33")
