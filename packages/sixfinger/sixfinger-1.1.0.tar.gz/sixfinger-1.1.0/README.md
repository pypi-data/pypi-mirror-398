# 🚀 Sixfinger - Ultra-Fast AI API

[![PyPI](https://img.shields.io/pypi/v/sixfinger.svg)](https://pypi.org/project/sixfinger/)
[![Python](https://img.shields.io/pypi/pyversions/sixfinger.svg)](https://pypi.org/project/sixfinger/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**~1,100 chars/sec** - 10-20x faster than OpenAI/Claude!

## ⚡ Features

- 🚀 **Ultra-fast**: ~1,100 characters/second
- 🤖 **9 AI Models**: Llama 3.1/3.3, Qwen3, GPT-OSS, etc.
- 🇹🇷 **Turkish optimized**: Qwen3-32B
- 💬 **Conversation context**
- 📡 **Streaming support**
- 💰 **Free tier**: 200 requests/month

## 📦 Installation

```bash
pip install sixfinger
For async support:

Bash

pip install sixfinger[async]
🔑 Get API Key
Sign up
Verify email
Get key from Dashboard
🚀 Quick Start
Python

from sixfinger import API

client = API(api_key="sixfinger_xxx")
response = client.chat("Merhaba!")
print(response.content)
Conversation
Python

from sixfinger import API

client = API(api_key="sixfinger_xxx")
conv = client.conversation()

conv.send("Merhaba!")
conv.send("Python nedir?")
conv.send("Neden popüler?")  # Remembers context!
Streaming
Python

from sixfinger import API

client = API(api_key="sixfinger_xxx")

for chunk in client.chat("Tell me a story", stream=True):
    print(chunk, end='', flush=True)
Async
Python

import asyncio
from sixfinger import AsyncAPI

async def main():
    async with AsyncAPI(api_key="sixfinger_xxx") as client:
        response = await client.chat("Merhaba!")
        print(response.content)

asyncio.run(main())
Model Selection
Python

# Auto model (recommended)
response = client.chat("Merhaba!")

# Turkish
response = client.chat("Osmanlı tarihi", model="qwen3-32b")

# Complex tasks
response = client.chat("Explain quantum physics", model="llama-70b")

# Fast
response = client.chat("Quick answer", model="llama-8b-instant")
🤖 Available Models
Model	Key	Size	Language	Plan
Llama 3.1 8B Instant	llama-8b-instant	8B	Multilingual	FREE+
Allam 2 7B	allam-2-7b	7B	Turkish/Arabic	FREE+
Qwen3 32B ⭐	qwen3-32b	32B	Turkish	STARTER+
Llama 3.3 70B	llama-70b	70B	Multilingual	STARTER+
GPT-OSS 120B	gpt-oss-120b	120B	Multilingual	PRO+
📊 Rate Limits
Plan	Price	Requests/Month	Tokens/Month
FREE	$0	200	20K
STARTER	$79	3K	300K
PRO	$199	75K	7.5M
PLUS	$499	500K	50M
📚 Documentation
Full docs: https://sfapi.pythonanywhere.com

🤝 Support
Email: sixfingerdev@gmail.com

📄 License
MIT License