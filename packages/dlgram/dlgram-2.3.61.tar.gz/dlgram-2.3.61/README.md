# Pygram

<p align="center">
  <b>Elegant, modern, and fully asynchronous Telegram MTProto framework for Python</b>
</p>

---

## Introduction

**Pygram** is a modern, elegant, and fully asynchronous MTProto API framework for Telegram, designed for both **user accounts** and **bots**. It provides a clean and intuitive Python interface to interact with Telegram’s core API, while still exposing powerful low-level capabilities when you need them.

Whether you're building automation tools, chat utilities, music bots, or full‑fledged Telegram clients, Pygram gives you the flexibility, performance, and developer experience you expect from a modern framework.

---

## Quick Example

```python
from pyrogram import Client, filters

app = Client("my_account")


@app.on_message(filters.private)
async def hello(client, message):
    await message.reply("Hello from Pygram!")


app.run()
```

---

## Key Features

* 🚀 Ready to Use – Install with pip and start immediately
* 🧠 Easy & Intuitive – Clean, Pythonic API
* ✨ Elegant – Developer‑friendly abstractions
* ⚡ Fast – Powered by TgCrypto (C based)
* 🧩 Type‑hinted – Excellent IDE support
* 🔄 Fully Asynchronous – Async-first design
* 🛠 Powerful – Full Telegram API access

---

## Installation

```bash
pip3 install pygram
```

Or install the latest development version directly from GitHub:

```bash
pip3 install git+https://github.com/growxupdate/pygram.git
```

---

> Pygram is built for developers who want speed, clarity, and full control over Telegram’s MTProto API.
