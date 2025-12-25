import re
import aiohttp
import asyncio
import time
import json

def normalize_text(text: str) -> str:
    text = text.lower()

    replacements = {
        "hxxp://": "http://",
        "hxxps://": "https://",
        "[dot]": ".",
        "(dot)": ".",
        "{dot}": ".",
        " dot ": ".",
        "٫": ".",
        "。": ".",
        "／": "/",
        "：": ":",
        " ": ""
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text


LINK_REGEX = re.compile(
    r"""
    (?:
        https?:\/\/
        |
        www\.
        |
        (?:[a-z0-9-]+\.)+[a-z]{2,}
        |
        \b\d{1,3}(?:\.\d{1,3}){3}\b
    )
    (?:[^\s<>"]+)?
    """,
    re.VERBOSE | re.IGNORECASE
)


def has_link(text: str) -> bool:
    if not text:
        return False

    text = normalize_text(text)
    return bool(LINK_REGEX.search(text))

now = time.time()

def parse_markdown(text: str):
    if text is None:
        return [], ""

    md_patterns = {
        "Bold": r"\*\*([^\*]+?)\*\*",
        "Italic": r"__([^_]+?)__",
        "Underline": r"==([^=]+?)==",
        "Strike": r"~~([^~]+?)~~",
        "Mono": r"`([^`]+?)`",
        "Quote": r"××([^×]+?)××"
    }

    md_link_pattern = r"\[([^\]]+?)\]\(([^)]+?)\)"
    md_spoiler_pattern = r"\|\|([^|]+?)\|\|"

    html_patterns = {
        "Bold": [r"<b>([^<]+?)</b>", r"<strong>([^<]+?)</strong>"],
        "Italic": [r"<i>([^<]+?)</i>", r"<em>([^<]+?)</em>"],
        "Mono": [r"<code>([^<]+?)</code>"],
        "Strike": [r"<s>([^<]+?)</s>", r"<del>([^<]+?)</del>"],
        "Underline": [r"<u>([^<]+?)</u>"],
        "Spoiler": [r'<span\s+class=["\']tg-spoiler["\']>([^<]+?)</span>'],

        "Quote": [
            r"<blockquote>([^<]+?)</blockquote>",
            r"<q>([^<]+?)</q>"
        ]
    }

    html_link_pattern = r'<a\s+href=["\']([^"\']+?)["\']\s*>([^<]+?)</a>'

    all_matches = []

    for m in re.finditer(md_link_pattern, text):
        content, url = m.groups()
        all_matches.append({
            "type": "Link",
            "start": m.start(),
            "content": content,
            "full": m.group(0),
            "extra": url
        })

    for m in re.finditer(md_spoiler_pattern, text):
        content = m.group(1)
        all_matches.append({
            "type": "Spoiler",
            "start": m.start(),
            "content": content,
            "full": m.group(0),
            "extra": None
        })

    for style, p in md_patterns.items():
        for m in re.finditer(p, text):
            content = m.group(1)
            all_matches.append({
                "type": style,
                "start": m.start(),
                "content": content,
                "full": m.group(0),
                "extra": None
            })

    for style, pattern_list in html_patterns.items():
        for pattern in pattern_list:
            for m in re.finditer(pattern, text, flags=re.IGNORECASE | re.DOTALL):
                content = m.group(1)
                all_matches.append({
                    "type": style,
                    "start": m.start(),
                    "content": content,
                    "full": m.group(0),
                    "extra": None
                })

    for m in re.finditer(html_link_pattern, text, flags=re.IGNORECASE | re.DOTALL):
        url, content = m.groups()
        all_matches.append({
            "type": "Link",
            "start": m.start(),
            "content": content,
            "full": m.group(0),
            "extra": url
        })

    all_matches.sort(key=lambda x: x["start"])

    conflict = 0
    clean_text = text
    metadata = []

    for m in all_matches:
        start = m["start"] - conflict

        meta = {
            "type": m["type"],
            "from_index": start,
            "length": len(m["content"])
        }

        if m["type"] == "Link":
            meta["link_url"] = m["extra"]

        metadata.append(meta)

        diff = len(m["full"]) - len(m["content"])
        conflict += diff

        clean_text = clean_text.replace(m["full"], m["content"], 1)

    return metadata, clean_text

class Update:
    def __init__(self, message_data, chat_id, client):
        self.raw = message_data
        self.chat_id = chat_id
        self._client = client
        self.text = message_data.get("text", "")
        self.message_id = message_data.get("message_id", None)
        self.sender_id = message_data.get("sender_id", None)
        self.aux_data = message_data.get("aux_data", None)
        self.is_edited = message_data.get("is_edited", False)
        self.has_link = has_link(self.text)
        tim = message_data.get("time", None)
        try:
            self.time = int(float(tim)) if tim is not None else None
        except Exception:
            self.time = None
        self.reply_to_message = message_data.get("reply_to_message", None)
        self.entities = message_data.get("entities", None)
        self.caption = message_data.get("caption", None)
        self._parse_forward(message_data)
        self._parse_media(message_data)

    def _parse_forward(self, message_data):
        self.is_forward = False
        self.forwarded_from = None
        self.forwarded_from_sender_id = None
        self.forwarded_from_message_id = None
        self.forwarded_from_type = None
        f = None
        for key in ("forwarded_from", "forward_from", "forward"):
            if key in message_data and message_data.get(key):
                f = message_data.get(key)
                break
        if f:
            self.is_forward = True
            self.forwarded_from = f
            self.forwarded_from_sender_id = f.get("from_sender_id") or f.get("sender_id") or f.get("user_id")
            self.forwarded_from_message_id = f.get("message_id") or f.get("forwarded_message_id") or f.get("orig_message_id")
            self.forwarded_from_type = f.get("type_from") or f.get("type")

    def _parse_media(self, message_data):
        self.file = None
        self.files = []
        self.location = None
        if "file" in message_data and message_data.get("file"):
            f = message_data.get("file", {})
            self.file = f
            self.files.append(f)
        if "files" in message_data and isinstance(message_data.get("files"), list):
            for f in message_data.get("files", []):
                if f:
                    self.files.append(f)
        if "location" in message_data and message_data.get("location"):
            self.location = message_data.get("location")
        if self.files and not self.file:
            self.file = self.files[0]
        if self.file:
            self.file_id = self.file.get("file_id")
            self.file_name = self.file.get("file_name") or self.file.get("name")
            self.file_size = self.file.get("size") or self.file.get("file_size")
            ftype = self.file.get("type")
            if not ftype and self.file_name and "." in self.file_name:
                ftype = self.file_name.rsplit(".", 1)[-1].lower()
            self.file_type = ftype
        else:
            self.file_id = None
            self.file_name = None
            self.file_size = None
            self.file_type = None

    async def reply(self, text: str):
        return await self._client.send_text(self.chat_id, text, message_id=self.message_id)

    def has_media(self):
        return bool(self.files)

    def file_info(self):
        if not self.file:
            return None
        return {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "raw": self.file
        }

class WebhookUpdate:
    def __init__(self, inline_data, client):
        msg = inline_data.get("inline_message", {})
        self.text = msg.get("text", "")
        self.sender_id = msg.get("sender_id", "")
        self.message_id = msg.get("message_id", "")
        self.chat_id = msg.get("chat_id", "")
        self.aux_data = msg.get("aux_data", {})
        self.raw = msg
        self._client = client

    async def reply(self, text: str):
        return await self._client.send_text(self.chat_id, text, message_id=self.message_id)

class Client:
    def __init__(self, token: str):
        self.token = token
        self.session: aiohttp.ClientSession | None = None
        self._on_message_handler = None
        self._on_message_filter = None
        self._on_message_webhook_handler = None
        self._webhook_url = None
        self._running = False

    async def _request(self, method: str, data: dict, headers: dict | None = None):
        url = f"https://botapi.rubika.ir/v3/{self.token}/{method}"
        async with self.session.post(url, json=data, headers=headers) as resp:
            try:
                jsn = await resp.json()
                return jsn
            except Exception:
                try:
                    return await resp.text()
                except Exception:
                    return {}

    async def init(self):
        self.session = aiohttp.ClientSession()
        jsn = await self._request("getMe", {})
        if isinstance(jsn, dict) and jsn.get("status") != "INVALID_ACCESS":
            self.username = jsn["data"]["bot"]["username"]
            print(f"You have successfully logged in to the @{self.username} bot.\n")
            print("This library was created by the channel @roboka_library")
        else:
            raise ValueError(f"❌ Invalid token or connection issue: {jsn}")

    def _format_text_and_meta(self, text: str):
        if not isinstance(text, str):
            return text, None
        meta, plain = parse_markdown(text)
        if meta:
            return plain, {"meta_data_parts": meta}
        return plain, None

    async def send_text(self, chat_id: str, text: str, message_id: str | None = None):
        plain, meta = self._format_text_and_meta(text)
        data = {"chat_id": chat_id, "text": plain}
        if message_id is not None:
            data["reply_to_message_id"] = message_id
        if meta:
            data["metadata"] = meta
        return await self._request("sendMessage", data)

    def on_message(self, func=None, filter=None):
        if func is None:
            def decorator(f):
                self._on_message_handler = f
                self._on_message_filter = filter
                return f
            return decorator
        else:
            self._on_message_handler = func
            self._on_message_filter = filter
            return func

    def on_message_webhook(self, url):
        def decorator(func):
            self._on_message_webhook_handler = func
            self._webhook_url = url
            return func
        return decorator

    async def run(self, limit: int = 100, pollers: int = 3):
        await self.init()
        tasks = []
        if self._on_message_handler:
            tasks.append(asyncio.create_task(self._run_polling(limit, pollers)))
        if self._on_message_webhook_handler and self._webhook_url:
            tasks.append(asyncio.create_task(self._run_webhook()))
        if tasks:
            await asyncio.gather(*tasks)

    async def _run_polling(self, limit: int, pollers: int):
        url = f"https://botapi.rubika.ir/v3/{self.token}/getUpdates"
        offset_id = None
        processed_messages: set = set()
        self._running = True
        async def poll_loop():
            nonlocal offset_id
            while self._running:
                try:
                    data = {"limit": limit, "timeout": 20}
                    if offset_id:
                        data["offset_id"] = offset_id
                    async with self.session.post(url, json=data, timeout=25) as resp:
                        try:
                            jsn = await resp.json()
                        except Exception:
                            jsn = {}
                        updates = jsn.get("data", {}).get("updates", [])
                        offset_id = jsn.get("data", {}).get("next_offset_id", offset_id)
                        for upd in updates:
                            new_msg = upd.get("new_message", {})
                            if not new_msg:
                                continue
                            tim = new_msg.get("time")
                            if tim is None or float(tim) < now:
                                continue
                            chat_id = upd.get("chat_id")
                            message_id = new_msg.get("message_id")
                            if not message_id or message_id in processed_messages:
                                continue
                            processed_messages.add(message_id)
                            if chat_id and isinstance(chat_id, str):
                                if chat_id.startswith("b"):
                                    chat_type = "private"
                                elif chat_id.startswith("g"):
                                    chat_type = "group"
                                elif chat_id.startswith("c"):
                                    chat_type = "channel"
                                else:
                                    chat_type = None
                            else:
                                chat_type = None
                            if self._on_message_filter and self._on_message_filter != chat_type:
                                continue
                            if self._on_message_handler:
                                update_obj = Update(new_msg, chat_id, client=self)
                                asyncio.create_task(self._on_message_handler(update_obj))
                except asyncio.CancelledError:
                    break
                except Exception:
                    await asyncio.sleep(0.05)
        async with asyncio.TaskGroup() as tg:
            for _ in range(max(1, pollers)):
                tg.create_task(poll_loop())

    async def _run_webhook(self):
        last = ""
        first = True
        while True:
            try:
                async with self.session.get(self._webhook_url, timeout=5) as r:
                    r.raise_for_status()
                    data = (await r.text()).strip()
                    if data and data != last:
                        last = data
                        if first:
                            first = False
                            continue
                        try:
                            jsn = json.loads(data)
                        except Exception:
                            continue
                        if self._on_message_webhook_handler:
                            upd = WebhookUpdate(jsn, self)
                            asyncio.create_task(self._on_message_webhook_handler(upd))
            except Exception:
                await asyncio.sleep(0.2)
            await asyncio.sleep(0.2)

    async def create_keypad(self, chat_id: str, text: str, rows: list, message_id: str | None = None):
        plain, meta = self._format_text_and_meta(text)
        data = {"chat_id": chat_id, "text": plain, "chat_keypad_type": "New", "chat_keypad": {"rows": rows, "resize_keyboard": True, "on_time_keyboard": False}}
        if message_id is not None:
            data["reply_to_message_id"] = message_id
        if meta:
            data["metadata"] = meta
        return await self._request("sendMessage", data)

    async def send_poll(self, chat_id: str, question: str, options: list):
        plain, meta = self._format_text_and_meta(question)
        data = {"chat_id": chat_id, "question": plain, "options": options}
        if meta:
            data["metadata"] = meta
        return await self._request("sendPoll", data)

    async def send_location(self, chat_id: str, latitude: float, longitude: float, message_id: str | None = None):
        data = {"chat_id": chat_id, "latitude": latitude, "longitude": longitude}
        if message_id is not None:
            data["reply_to_message_id"] = message_id
        return await self._request("sendLocation", data)

    async def edit_text(self, chat_id: str, text: str, message_id: int):
        plain, meta = self._format_text_and_meta(text)
        data = {"chat_id": chat_id, "message_id": message_id, "text": plain}
        if meta:
            data["metadata"] = meta
        return await self._request("editMessageText", data)

    async def send_contact(self, chat_id: str, first_name: str, last_name: str, phone_number: str, message_id: int | None = None):
        data = {"chat_id": chat_id, "first_name": first_name, "last_name": last_name, "phone_number": phone_number}
        if message_id is not None:
            data["reply_to_message_id"] = message_id
        return await self._request("sendContact", data)

    async def get_chat(self, chat_id: str):
        return await self._request("getChat", {"chat_id": chat_id})

    async def forward_message(self, from_chat_id: str, message_id: int, to_chat_id: str):
        data = {"from_chat_id": from_chat_id, "message_id": message_id, "to_chat_id": to_chat_id}
        return await self._request("forwardMessage", data)

    async def delete_message(self, chat_id: str, message_id: int):
        data = {"chat_id": chat_id, "message_id": message_id}
        return await self._request("deleteMessage", data)

    async def create_inline_keypad(self, chat_id: str, text: str, rows: list, message_id: str | None = None):
        plain, meta = self._format_text_and_meta(text)
        data = {"chat_id": chat_id, "text": plain, "inline_keypad": {"rows": rows}}
        if message_id is not None:
            data["reply_to_message_id"] = message_id
        if meta:
            data["metadata"] = meta
        return await self._request("sendMessage", data)

    async def get_upload_url(self, type: str):
        res = await self._request("requestSendFile", {"type": type})
        return res.get("data", {}).get("upload_url")

    async def get_file_id(self, url: str, file_name: str, file_path: str):
        with open(file_path, "rb") as f:
            form = aiohttp.FormData()
            form.add_field("file", f, filename=file_name, content_type="application/octet-stream")
            async with self.session.post(url, data=form, ssl=False) as resp:
                try:
                    jsn = await resp.json()
                except Exception:
                    jsn = {}
                return jsn.get("data", {}).get("file_id")

    async def send_file(self, chat_id: str, text: str, file_name: str, file_path: str, file_type: str, message_id: str | None = None):
        upload_url = await self.get_upload_url(file_type)
        file_id = await self.get_file_id(upload_url, file_name, file_path)
        plain, meta = self._format_text_and_meta(text)
        data = {"chat_id": chat_id, "file_id": file_id, "text": plain}
        if message_id is not None:
            data["reply_to_message_id"] = message_id
        if meta:
            data["metadata"] = meta
        return await self._request("sendFile", data)

    async def send_image(self, chat_id: str, text: str, file_name: str, file_path: str, message_id: str | None = None):
        upload_url = await self.get_upload_url("Image")
        file_id = await self.get_file_id(upload_url, file_name, file_path)
        plain, meta = self._format_text_and_meta(text)
        data = {"chat_id": chat_id, "file_id": file_id, "text": plain}
        if message_id is not None:
            data["reply_to_message_id"] = message_id
        if meta:
            data["metadata"] = meta
        return await self._request("sendFile", data)

    async def send_video(self, chat_id: str, text: str, file_name: str, file_path: str, message_id: str | None = None):
        upload_url = await self.get_upload_url("Video")
        file_id = await self.get_file_id(upload_url, file_name, file_path)
        plain, meta = self._format_text_and_meta(text)
        data = {"chat_id": chat_id, "file_id": file_id, "text": plain}
        if message_id is not None:
            data["reply_to_message_id"] = message_id
        if meta:
            data["metadata"] = meta
        return await self._request("sendFile", data)

    async def get_updates(self, limit: int, offset_id: str | None = None):
        data = {"limit": limit}
        if offset_id is not None:
            data["offset_id"] = offset_id
        return await self._request("getUpdates", data)

    async def edit_keypad(self, chat_id: str, rows: list):
        data = {"chat_id": chat_id, "chat_keypad_type": "New", "chat_keypad": {"rows": rows, "resize_keyboard": True, "on_time_keyboard": False}}
        return await self._request("editChatKeypad", data)

    async def set_commands(self, commands: list):
        return await self._request("setCommands", {"bot_commands": commands})

    async def set_webhook(self, url: str, type: str):
        return await self._request("updateBotEndpoints", {"url": url, "type": type})

    async def close(self):
        self._running = False
        if self.session:
            await self.session.close()