# Remnawave Python SDK

> [!WARNING]
> This repository is a fork of the official SDK [`remnawave/python-sdk`](https://github.com/remnawave/python-sdk).

[![Stars](https://img.shields.io/github/stars/snoups/remnapy.svg?style=social)](https://github.com/remnawave/remnapy/stargazers)
[![Forks](https://img.shields.io/github/forks/snoups/remnapy.svg?style=social)](https://github.com/remnawave/remnapy/network/members)
[![Issues](https://img.shields.io/github/issues/snoups/remnapy.svg)](https://github.com/snoups/remnapy/issues)
[![Supported python versions](https://img.shields.io/pypi/pyversions/remnapy.svg)](https://pypi.python.org/pypi/remnapy)
[![Downloads](https://img.shields.io/pypi/dm/remnapy.svg)](https://pypi.python.org/pypi/remnapy)
[![PyPi Package Version](https://img.shields.io/pypi/v/remnapy)](https://pypi.python.org/pypi/remnapy)

A Python SDK client for interacting with the **[Remnawave API](https://docs.rw/)**.
This library simplifies working with the API by providing convenient controllers, Pydantic models for requests and responses, and fast serialization with `orjson`. 

**🎉 Version 2.3.0** brings full compatibility with the latest Remnawave backend API, including new endpoints, improved response wrappers, and enhanced type safety.

## ✨ Key Features

- **Full v2.3.0 API compatibility**: Updated for latest Remnawave backend features
- **New controllers**: ConfigProfiles, InternalSquads, InfraBilling, NodesUsageHistory
- **Enhanced models**: OpenAPI-compliant response wrappers with improved field mappings
- **Controller-based design**: Split functionality into separate controllers for flexibility. Use only what you need!
- **Pydantic models**: Strongly-typed requests and responses for better reliability.
- **Fast serialization**: Powered by `orjson` for efficient JSON handling.
- **Modular usage**: Import individual controllers or the full SDK as needed.
- **Backward compatibility**: Legacy aliases maintained for smooth migration.

## 📦 Installation

### Production Version
Install the latest version from the new PyPI package:

```bash
pip install remnapy
```

### Development Version
If you need the development version:

```bash
pip install git+https://github.com/snoups/remnapy.git@development
```

---

## 🫥 Compatible versions

| Contract Version | Remnawave Panel Version |
| ---------------- | ----------------------- |
| 2.3.0            | >=2.3.0                 |

### Dependencies
- `orjson` (>=3.10.15, <4.0.0)
- `rapid-api-client` (==0.6.0)
- `httpx` (>=0.27.2, <0.28.0)

## 🚀 Usage

Here’s a quick example to get you started:

```python
import os
import asyncio

from remnapy import RemnawaveSDK  # Updated import for new package
from remnapy.models import (  # Updated import path
    UsersResponseDto, 
    UserResponseDto,
    GetAllConfigProfilesResponseDto,
    CreateInternalSquadRequestDto
)

async def main():
    # URL to your panel (ex. https://vpn.com or http://127.0.0.1:3000)
    base_url: str = os.getenv("REMNAWAVE_BASE_URL")
    # Bearer Token from panel (section: API Tokens) 
    token: str = os.getenv("REMNAWAVE_TOKEN")

    # Initialize the SDK
    remnawave = RemnawaveSDK(base_url=base_url, token=token)

    # Fetch all users
    response: UsersResponseDto = await remnawave.users.get_all_users_v2()
    total_users: int = response.total
    users: list[UserResponseDto] = response.users
    print("Total users: ", total_users)
    print("List of users: ", users)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🧪 Running Tests

To run the test suite, use Poetry:

```bash
poetry run pytest
```

## ❤️ About

This SDK was originally developed by [@kesevone](https://github.com/kesevone) for integration with Remnawave's API.

Previously maintained by [@sm1ky](https://github.com/sm1ky) at [`sm1ky/remnawave-api`](https://github.com/sm1ky/remnawave-api).

The official Remnawave repository is located at [`remnawave/python-sdk`](https://github.com/remnawave/python-sdk).

This repository is a fork of the official SDK.