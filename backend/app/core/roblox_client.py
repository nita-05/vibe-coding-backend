import json
import re
from datetime import datetime
from typing import Any, Dict

import httpx

from app.config import settings


PLACE_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="4">
  <Meta name="ExplicitAutoJoints">true</Meta>
  <External>null</External>
  <External>nil</External>
  <Item class="Workspace" referent="RBX0">
    <Properties>
      <string name="Name">Workspace</string>
    </Properties>
  </Item>
  <Item class="Script" referent="RBX1">
    <Properties>
      <string name="Name">{script_name}</string>
      <Ref name="Parent">RBX0</Ref>
      <ProtectedString name="Source"><![CDATA[{script_source}]]></ProtectedString>
    </Properties>
  </Item>
</roblox>
"""


class RobloxClient:
    """Client for Roblox Open Cloud interactions."""

    def __init__(self):
        self.api_key = settings.roblox_api_key
        self.universe_id = settings.roblox_universe_id
        self.place_id = settings.roblox_place_id
        self.base_url = "https://apis.roblox.com"
        self.auth_headers = {"x-api-key": self.api_key} if self.api_key else {}

    def is_configured(self) -> bool:
        """Check if Roblox Open Cloud credentials are configured."""
        return all([self.api_key, self.universe_id, self.place_id])

    def _sanitize_script(self, script_content: str) -> str:
        """Ensure script content can live inside a CDATA block."""
        return script_content.replace("]]>", "]]]]><![CDATA[>")

    def _safe_filename(self, name: str) -> str:
        """Create a filesystem-safe filename."""
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip()).strip("-")
        return slug or "vibe-place"

    def _build_place_file(self, script_content: str, place_name: str) -> bytes:
        """Create a minimal RBXLX place containing the generated script."""
        script_source = self._sanitize_script(script_content)
        payload = PLACE_TEMPLATE.format(
            script_name=place_name or "VibeScript",
            script_source=script_source
        )
        return payload.encode("utf-8")

    async def publish_place(self, place_name: str, script_content: str, description: str = "") -> Dict[str, Any]:
        """
        Publish a generated place file to an existing Roblox place using Open Cloud.
        """
        if not self.is_configured():
            raise Exception("Roblox API not configured. Set ROBLOX_API_KEY, ROBLOX_UNIVERSE_ID, ROBLOX_PLACE_ID.")

        place_bytes = self._build_place_file(script_content, place_name)
        url = f"{self.base_url}/cloud/v2/universes/{self.universe_id}/places/{self.place_id}/versions"

        version_description = description or f"Published via Vibe Coding on {datetime.utcnow().isoformat()}Z"

        files = {
            "request": ("request.json", json.dumps({"versionDescription": version_description}), "application/json"),
            "placeFile": (f"{self._safe_filename(place_name)}.rbxlx", place_bytes, "application/octet-stream"),
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=self.auth_headers, files=files)

            if response.status_code not in (200, 201):
                raise Exception(f"Roblox API error: {response.status_code} - {response.text}")

            data = response.json()
            return {
                "success": True,
                "place_id": self.place_id,
                "version_number": data.get("versionNumber"),
                "play_url": self.get_play_url(self.place_id),
                "embed_url": self.get_embed_url(self.place_id),
                "message": version_description,
                "raw_response": data,
            }
        except httpx.RequestError as exc:
            raise Exception(f"Failed to connect to Roblox API: {str(exc)}")

    def get_play_url(self, place_id: str) -> str:
        """Get the playable URL for a Roblox place."""
        return f"https://www.roblox.com/games/{place_id}?launch=true"

    def get_embed_url(self, place_id: str) -> str:
        """Get the embeddable URL for Roblox Web Player."""
        return f"https://www.roblox.com/games/{place_id}?launch=true&displayName={place_id}"

