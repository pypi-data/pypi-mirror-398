# PolyKV - Python

[![PyPI version](https://img.shields.io/pypi/v/polykv.svg)](https://pypi.org/project/polykv/)
![License](https://img.shields.io/badge/license-MIT-green.svg)
[![Stars](https://img.shields.io/github/stars/polykv/polykv-python?style=social)](https://github.com/polykv/polykv-python)

**Native Key-Value Store for Python.**

A lightweight, modern persistence layer. Perfect for CLI tools, bots, and small web services that need simple state management without a heavy database.

> **One API, Everywhere.** This library is part of the [PolyKV](https://github.com/polykv/polykv) ecosystem. Use the same consistent API across 12+ languages.

## ✨ Why PolyKV Python?

-   ⚡️ **Flexible I/O**
    Supports both `asyncio` for modern apps and synchronous mode for simple scripts.

-   🐍 **Pure Python**
    Zero binary dependencies. easy to install, easy to bundle, works everywhere Python works.

-   📂 **XDG Compliant**
    Automatically respects standard configuration paths (XDG on Linux, Library on macOS) so your app behaves like a good citizen.

## 📦 Installation

```bash
pip install polykv
```

## 🚀 Usage

### Complete Async Example

```python
import asyncio
from polykv import PolyKV

async def main():
    # Zero Config - just give it a namespace
    db = PolyKV("BotConfig")

    # 1. Save
    await db.set_string("token", "secret-123")
    await db.set_number("retries", 5)

    # 2. Read
    token = await db.get_string("token")
    print(f"Token: {token}")

    # 3. Clear
    await db.clear()

if __name__ == "__main__":
    asyncio.run(main())
```

### Synchronous Example

```python
from polykv import PolyKVSync

def main():
    db = PolyKVSync("MyScript")
    db.set_string("mode", "batch")
    print(db.get_string("mode"))

if __name__ == "__main__":
    main()
```

## 📂 Storage Locations

-   **macOS**: `~/Library/Preferences/BotConfig/BotConfig.json`
-   **Linux**: `~/.config/BotConfig/BotConfig.json`
-   **Windows**: `%APPDATA%\BotConfig\BotConfig.json`

## 🌍 Platform Support

| Language | Verified Runtime (✅) | Build Only (🛠) |
| :--- | :--- | :--- |
| [**TypeScript**](https://github.com/polykv/polykv-typescript) | CLI (Node.js), Browser, React Native (iOS/Android) | - |
| [**Dart**](https://github.com/polykv/polykv-dart) | Flutter (iOS/Android/macOS), CLI | - |
| [**Go**](https://github.com/polykv/polykv-go) | macOS, Linux, Windows, iOS, Android, CLI | - |
| [**Rust**](https://github.com/polykv/polykv-rust) | macOS, iOS, Android, CLI | Linux, Windows |
| [**Swift**](https://github.com/polykv/polykv-swift) | iOS, macOS, CLI | - |
| [**C++**](https://github.com/polykv/polykv-cpp) | macOS, iOS, Android, CLI | - |
| [**Python**](https://github.com/polykv/polykv-python) | CLI, Web, Android | - |
| [**Kotlin**](https://github.com/polykv/polykv-kotlin) | CLI, Web, Android | - |
| [**C#**](https://github.com/polykv/polykv-csharp) | CLI | Android, Windows |
| [**Java**](https://github.com/polykv/polykv-java) | CLI, Android | - |
| [**Ruby**](https://github.com/polykv/polykv-ruby) | CLI | - |
| [**PHP**](https://github.com/polykv/polykv-php) | CLI | - |

> **✅ Runtime Verified**: Full CRUD operations verified via automated tests on actual devices/simulators.

## 📜 License

MIT
