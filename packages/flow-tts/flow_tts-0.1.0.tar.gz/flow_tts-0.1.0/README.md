# FlowTTS Python SDK

> OpenAI-style TTS SDK for Tencent Cloud - Simple, elegant, Python-first

English | [简体中文](./README_CN.md)

FlowTTS is a lightweight Text-to-Speech SDK that wraps Tencent Cloud's TRTC TTS API with an OpenAI-compatible interface. Write elegant code with just a few lines.

## ✨ Features

- 🎯 **OpenAI-Compatible API** - Drop-in replacement for OpenAI TTS
- 🐍 **Python-First** - Designed for Python 3.8+
- 🔷 **Type Hints** - Full type safety with mypy support
- 🎤 **Rich Voice Library** - 380+ preset voices in multiple languages
- 🔍 **Auto Language Detection** - Automatically detects text language
- 📦 **Simple Installation** - Easy pip install

## 📦 Installation

```bash
pip install flow-tts
```

## 🚀 Quick Start

```python
from flow_tts import FlowTTS

client = FlowTTS({
    "secret_id": "your-secret-id",
    "secret_key": "your-secret-key",
    "sdk_app_id": 1234567890
})

# Synthesize speech
response = client.synthesize({
    "text": "你好，世界！",
    "voice": "v-female-R2s4N9qJ",
    "format": "wav"
})

# Save to file
with open("output.wav", "wb") as f:
    f.write(response["audio"])

print(f"Generated {len(response['audio'])} bytes")
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file:

```env
TX_SECRET_ID=your-tencent-cloud-secret-id
TX_SECRET_KEY=your-tencent-cloud-secret-key
TRTC_SDK_APP_ID=your-trtc-app-id
```

### Client Options

```python
from flow_tts import FlowTTSConfig

config: FlowTTSConfig = {
    "secret_id": "...",      # Tencent Cloud Secret ID
    "secret_key": "...",     # Tencent Cloud Secret Key
    "sdk_app_id": 123456,    # TRTC SDK App ID
    "region": "ap-beijing"   # Region (optional)
}
```

## 📖 Voice Management

```python
# Get all available voices
voices = client.get_voices()
print(f"Total voices: {len(voices['preset'])}")

# Search voices
gentle_voices = client.search_voices("温柔")
print(f"Found {len(gentle_voices)} gentle voices")

# Get specific voice info
voice = client.get_voice("v-female-R2s4N9qJ")
print(voice["name"])  # "温柔姐姐"
```

## 🎤 Voice Selection

The SDK provides 380+ preset voices:
- 77 Turbo voices (low latency)
- 303 Extended voices (high quality)

### Recommended Voices

| Voice ID | Name | Language | Features |
|---------|------|---------|----------|
| `v-female-R2s4N9qJ` | 温柔姐姐 | Chinese | Gentle, Warm |
| `v-male-Bk7vD3xP` | 威严霸总 | Chinese | Mature, Steady |
| `v-female-p9Xy7Q1L` | 清晰女旁白 | English | Clear, Professional |

## 📄 License

MIT License - see [LICENSE](../../LICENSE) file

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📮 Links

- GitHub: [chicogong/flow-tts](https://github.com/chicogong/flow-tts)
- PyPI: [flow-tts](https://pypi.org/project/flow-tts/) (coming soon)
- Node.js SDK: [npm/flow-tts](https://www.npmjs.com/package/flow-tts)

## 🙏 Acknowledgments

Built on top of Tencent Cloud TRTC TTS API.
