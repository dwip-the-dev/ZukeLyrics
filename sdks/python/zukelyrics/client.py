import json
import base64
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

class ZukeLyricsClient:
    def __init__(self, owner: str = "dwip-the-dev", repo: str = "ZukeLyrics", branch: str = "main", token: Optional[str] = None):
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.token = token
        self.cdn_primary = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/lyrics-database"
        self.cdn_fallback = f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch}/lyrics-database"
        self.api_base = f"https://api.github.com/repos/{owner}/{repo}/contents/lyrics-database"

    def get_relative_path(self, video_id: str) -> str:
        clean = video_id.strip()
        c1 = clean[0] if clean and clean[0].isalnum() else "_"
        c2 = clean[1] if len(clean) > 1 and clean[1].isalnum() else "_"
        return f"{c1}/{c2}/{clean}.json"

    def get_lyrics(self, video_id: str) -> Optional[Dict[str, Any]]:
        rel_path = self.get_relative_path(video_id)
        
        # Try primary CDN
        for cdn_url in [f"{self.cdn_primary}/{rel_path}", f"{self.cdn_fallback}/{rel_path}"]:
            try:
                req = urllib.request.Request(cdn_url, headers={"User-Agent": "ZukeLyrics-Python-SDK"})
                with urllib.request.urlopen(req, timeout=8) as response:
                    if response.status == 200:
                        return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    continue
            except Exception:
                continue
        return None

    def has_lyrics(self, video_id: str) -> bool:
        rel_path = self.get_relative_path(video_id)
        for cdn_url in [f"{self.cdn_primary}/{rel_path}", f"{self.cdn_fallback}/{rel_path}"]:
            try:
                req = urllib.request.Request(cdn_url, method="HEAD", headers={"User-Agent": "ZukeLyrics-Python-SDK"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                continue
        return False

    def get_catalog(self) -> List[Dict[str, Any]]:
        base = f"https://cdn.jsdelivr.net/gh/{self.owner}/{self.repo}@{self.branch}/index/catalog.json"
        try:
            req = urllib.request.Request(base, headers={"User-Agent": "ZukeLyrics-Python-SDK"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8"))
        except Exception:
            pass
        return []

    def search(self, query: str) -> List[Dict[str, Any]]:
        base = f"https://cdn.jsdelivr.net/gh/{self.owner}/{self.repo}@{self.branch}/index/search-index.json"
        try:
            req = urllib.request.Request(base, headers={"User-Agent": "ZukeLyrics-Python-SDK"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    q_lower = query.lower().strip()
                    return [
                        item for item in data.get("tracks", [])
                        if q_lower in item.get("searchKey", "") or q_lower in item.get("title", "").lower() or q_lower in item.get("artist", "").lower()
                    ]
        except Exception:
            pass
        return []

    def get_stats(self) -> Dict[str, Any]:
        base = f"https://cdn.jsdelivr.net/gh/{self.owner}/{self.repo}@{self.branch}/api/v1/stats.json"
        try:
            req = urllib.request.Request(base, headers={"User-Agent": "ZukeLyrics-Python-SDK"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8"))
        except Exception:
            pass
        return {}

    def upload_lyrics(self, payload: Dict[str, Any], token: Optional[str] = None) -> bool:
        active_token = token or self.token
        if not active_token:
            raise ValueError("No GitHub Personal Access Token (PAT) provided for write operation.")

        video_id = payload.get("videoId")
        if not video_id:
            raise ValueError("Payload missing 'videoId'")

        rel_path = self.get_relative_path(video_id)
        api_url = f"{self.api_base}/{rel_path}"
        json_str = json.dumps(payload, indent=2, ensure_ascii=False)
        b64_content = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

        # Check existing file for SHA
        existing_sha = None
        try:
            check_req = urllib.request.Request(
                api_url,
                headers={
                    "Authorization": f"Bearer {active_token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "ZukeLyrics-Python-SDK"
                }
            )
            with urllib.request.urlopen(check_req, timeout=8) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    existing_sha = data.get("sha")
        except Exception:
            pass

        body_data = {
            "message": f"Add/update synced lyrics for {payload.get('title')} - {payload.get('artist')} [{video_id}]",
            "content": b64_content,
            "branch": self.branch
        }
        if existing_sha:
            body_data["sha"] = existing_sha

        put_req = urllib.request.Request(
            api_url,
            data=json.dumps(body_data).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {active_token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "ZukeLyrics-Python-SDK"
            },
            method="PUT"
        )

        with urllib.request.urlopen(put_req, timeout=12) as put_resp:
            return put_resp.status in (200, 201)
