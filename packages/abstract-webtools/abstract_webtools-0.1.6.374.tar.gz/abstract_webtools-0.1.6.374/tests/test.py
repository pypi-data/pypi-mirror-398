from imports import *
import webbrowser
import urllib

import json
import re
from urllib.parse import urlparse, parse_qs

from abstract_webtools import requestManager


def extract_googlevideo_urls_from_html(html: str) -> list[str]:
    """
    DEBUG / INSPECTION ONLY.
    Finds googlevideo URLs embedded in JS blobs.
    """
    urls = set()
    for m in re.findall(r'"(https://[^"]+googlevideo\.com[^"]+)"', html):
        try:
            urls.add(json.loads(f'"{m}"'))
        except Exception:
            continue
    return list(urls)


def extract_player_response(url: str=None,html: str=None) -> dict:
    if url:
        req = requestManager(url)
        html = req.source_code

    m = re.search(
        r"ytInitialPlayerResponse\s*=\s*(\{.+?\});",
        html,
        re.S,
    )
    if not m:
        raise RuntimeError("ytInitialPlayerResponse not found")

    return json.loads(m.group(1))


def iter_streaming_urls(player_response: dict):
    streaming = player_response.get("streamingData", {})
    formats = (
        streaming.get("formats", []) +
        streaming.get("adaptiveFormats", [])
    )

    for fmt in formats:
        if "url" in fmt:
            yield fmt["url"], fmt
        elif "signatureCipher" in fmt:
            yield fmt["signatureCipher"], fmt
video_url = "https://www.youtube.com/shorts/6vP02wYh4Ds"
def looks_like_real_stream(url: str) -> bool:
    q = parse_qs(urlparse(url).query)
    return (
        'itag' in q and
        "mime" in q and
        ("sig" in q or "signature" in q)
    )
##video_url = "https://www.youtube.com/shorts/6vP02wYh4Ds"
##req_mgr = requestManager(video_url)
##source_code = req_mgr.source_code
##write_to_file(contents=source_code,file_path=os.path.join(os.getcwd(),"youtubesource.html"))
source_code = read_from_file(os.path.join(os.getcwd(),"youtubesource.html"))
player_responses = extract_player_response(html=source_code)
player_response = iter_streaming_urls(player_responses)
input(player_response)
for key,value in player_responses.items():
    
    print(key)
    input(value)
    

for raw in [url for url in googlevideo_urls if 'itag' in url]:
    print(raw)
    url = json.loads(f'"{raw}"')
    session = requests.Session()

    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
        "Referer": "https://www.youtube.com/",
        "Origin": "https://www.youtube.com",
        "Accept": "*/*",
        "Accept-Encoding": "identity",
        "Connection": "keep-alive",
    })

    with session.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open("video.mp4", "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)
