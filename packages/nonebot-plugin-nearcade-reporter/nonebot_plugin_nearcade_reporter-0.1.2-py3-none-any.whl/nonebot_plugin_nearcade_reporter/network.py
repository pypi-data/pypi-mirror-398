from typing import Any, Optional

import httpx

_client = httpx.AsyncClient(base_url="https://nearcade.phizone.cn", timeout=10.0)


class NearcadeHttp:
    def __init__(self, api_token: str) -> None:
        self.api_token = api_token

    async def list_shops(
        self,
        keyword: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> dict[str, Any]:
        resp = await _client.get(
            "/api/shops",
            params={
                "q": keyword,
                "page": page,
                "limit": limit,
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def update_attendance(
        self,
        *,
        arcade_id: int,
        game_id: int,
        count: int,
        source: str,
        comment: str = "Update by Nearcade Reporter Bot",
    ) -> tuple[bool, str]:
        resp = await _client.post(
            f"/api/shops/{source}/{arcade_id}/attendance",
            headers={"Authorization": f"Bearer {self.api_token}"},
            json={
                "games": [
                    {
                        "id": game_id,
                        "currentAttendances": count,
                    }
                ],
                "comment": comment,
            },
        )
        if resp.is_success:
            try:
                data = resp.json()
                if isinstance(data, dict) and "message" in data:
                    return True, str(data["message"])
            except ValueError:
                pass
            return True, "ok"
        message = None
        try:
            data: Any = resp.json()
            if isinstance(data, dict):
                message = data.get("message")
        except ValueError:
            pass
        if not message:
            message = resp.text or resp.reason_phrase or "unknown error"
        return False, message

    async def get_attendance(
        self,
        *,
        arcade_id: int,
        source: str,
        reported: Optional[bool] = None,
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        params: dict[str, Any] = {}
        if reported is not None:
            params["reported"] = "true" if reported else "false"

        resp = await _client.get(
            f"/api/shops/{source}/{arcade_id}/attendance",
            params=params,
        )
        if resp.is_success:
            try:
                data = resp.json()
                if isinstance(data, dict):
                    return True, "ok", data
            except ValueError:
                pass
            return False, "Invalid response format", None
        message = None
        try:
            data = resp.json()
            if isinstance(data, dict):
                message = data.get("message")
        except ValueError:
            pass
        if not message:
            message = resp.text or resp.reason_phrase or "unknown error"
        return False, message, None
