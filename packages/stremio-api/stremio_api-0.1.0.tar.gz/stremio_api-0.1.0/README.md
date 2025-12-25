# Stremio-API

A lightweight, asynchronous Python wrapper for the Stremio API.

## Features
- ✨ Async functionality using `httpx`
- 👤 User authentication and profile management
- 📚 Library and Addon collection access
- 📺 "Continue Watching" synchronization
- 🎬 Metadata fetching (via Cinemeta)

## Installation
```bash
pip install stremio-api
```

## Quick Start
You can log in directly using your Stremio credentials:

```python
import asyncio
from stremio_api import StremioAPIClient

async def main():
    # Initialize without an auth key (or with None)
    async with StremioAPIClient(auth_key=None) as client:
        # Login with email and password
        auth_key = await client.login("your.email@example.com", "your_password")
        print(f"Logged in! New Auth Key: {auth_key}")

        # Get user info
        user = await client.get_user()
        print(f"User profile: {user.email}")

        # Fetch Continue Watching items
        watching = await client.get_continue_watching(limit=5)
        for item in watching:
            print(f"Watching: {item.name}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Usage with Existing Auth Key
If you already have an `authKey` (e.g. from local storage), you can skip the login:

```python
client = StremioAPIClient(auth_key="YOUR_EXISTING_KEY")
user = await client.get_user()
```
