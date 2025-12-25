import httpx
from typing import List, Optional, Any, Dict
from .models import User, LibraryItem, Addon, Meta, Stream

class StremioAPIError(Exception):
    """Base error for Stremio API"""
    pass

class StremioAPIClient:
    """Async client for Stremio API"""
    
    BASE_URL = "https://api.strem.io"

    def __init__(self, auth_key: str, client: Optional[httpx.AsyncClient] = None):
        self.auth_key = auth_key
        self._client = client

    async def _post(self, method: str, payload: Dict[str, Any]) -> Any:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                    "Referer": "https://web.stremio.com/",
                },
                timeout=10.0
            )

        try:
            import json
            import logging
            logger = logging.getLogger(__name__)
            url = f"{self.BASE_URL}/api/{method}"
            
            # Mask sensitive data in logs
            log_payload = payload.copy()
            if "password" in log_payload:
                log_payload["password"] = "********"
            if "authKey" in log_payload:
                log_payload["authKey"] = log_payload["authKey"][:5] + "..."
            
            logger.debug("Stremio API Request: %s %s", method, log_payload)

            # Use text/plain for compatibility with some Stremio endpoints
            response = await self._client.post(
                url, 
                content=json.dumps(payload),
                headers={"Content-Type": "text/plain;charset=UTF-8"}
            )
            response.raise_for_status()
            data = response.json()
            
            logger.debug("Stremio API Response: %s", data)

            if "error" in data:
                raise StremioAPIError(f"API Error: {data['error'].get('message', data['error'])}")
            
            return data.get("result")
        except httpx.HTTPError as e:
            raise StremioAPIError(f"HTTP Connection Error: {e}")

    async def get_user(self) -> User:
        """Get current user information."""
        result = await self._post("getUser", {"authKey": self.auth_key, "type": "GetUser"})
        return User(**result)

    async def login(self, email: str, password: str) -> str:
        """Login with email and password, returns new authKey."""
        result = await self._post("login", {
            "email": email,
            "password": password,
            "type": "Login",
            "facebook": False
        })
        self.auth_key = result.get("authKey")
        return self.auth_key

    async def get_addons(self) -> List[Addon]:
        """Get user's installed addons"""
        result = await self._post("addonCollectionGet", {
            "authKey": self.auth_key, 
            "type": "AddonCollectionGet",
            "update": True
        })
        addons_data = result.get("addons", [])
        return [Addon(**addon) for addon in addons_data]

    async def get_library(self, all_items: bool = True, ids: Optional[List[str]] = None) -> List[LibraryItem]:
        """Get user's library items"""
        payload = {
            "authKey": self.auth_key,
            "collection": "libraryItem",
            "all": all_items
        }
        if ids:
            payload["ids"] = ids
            payload["all"] = False
            
        result = await self._post("datastoreGet", payload)
        if result is None:
            return []
        return [LibraryItem(**item) for item in result]

    async def get_continue_watching(self, limit: int = 20) -> List[LibraryItem]:
        """Sorted list of items currently being watched"""
        library = await self.get_library(all_items=True)
        # Filter: has video_id and lastWatched, and not fully watched
        watching = [
            item for item in library 
            if item.state.video_id and item.state.last_watched
            and not (item.type == "movie" and item.state.flagged_watched == 1)
        ]
        # Sort by last_watched descending
        watching.sort(key=lambda x: x.state.last_watched, reverse=True)
        return watching[:limit]

    async def get_meta(self, content_type: str, content_id: str) -> Optional[Meta]:
        """Get detailed metadata from Cinemeta."""
        # Note: Cinemeta is the standard meta addon for Stremio
        url = f"https://v3-cinemeta.strem.io/meta/{content_type}/{content_id}.json"
        
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                    "Referer": "https://web.stremio.com/",
                },
                timeout=10.0
            )

        try:
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()
            meta_data = data.get("meta")
            if meta_data:
                return Meta(**meta_data)
            return None
        except (httpx.HTTPError, Exception) as e:
            import logging
            logging.getLogger(__name__).warning("Failed to fetch meta from Cinemeta: %s", e)
            return None

    async def close(self):
        """Close the underlying HTTP client"""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
