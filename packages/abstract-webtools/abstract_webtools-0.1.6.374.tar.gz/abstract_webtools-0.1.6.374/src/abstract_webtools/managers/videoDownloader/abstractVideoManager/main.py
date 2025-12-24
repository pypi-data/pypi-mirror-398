from .imports import *
from .src import *
# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
VIDEO_MGR = AbstractVideoManager()
def get_itags(video_url):
    player = extract_player_response(video_url)
    itags = get_any_value(player,'itag')
    return itags
def get_itag(video_url,itag=None):
    itags = get_itags(video_url)
    if itag and itag in itags:
        pass
    else:
        itag = itags[0]
    return itag

def getDirectUrlDict(video_url,itag=None):
    
    itag = get_itag(video_url,itag=itag)
    result = VIDEO_MGR.resolve_direct_url(video_url=video_url,itag=itag)
    return result
def getDirectUrl(video_url,itag=None):
    result = getDirectUrlDict(video_url=video_url,itag=itag)
    return result["direct_url"]
def getMetaData(video_url,itag=None):
    result = getDirectUrlDict(video_url=video_url,itag=itag)
    return result["metadata"]
def getTitle(video_url,itag=None):
    result = getMetaData(video_url=video_url,itag=itag)
    return result.get("title", "video").replace("/", "_")  
def getVideoFilename(video_url,itag=None):
    title = getTitle(video_url=video_url,itag=itag)
    return f"{title}.mp4" 
def abstractVideoDownload(video_url,itag=None):
    direct_url = getDirectUrl(video_url=video_url,itag=itag)
    filename = getVideoFilename(video_url=video_url,itag=itag)
    out = VIDEO_MGR.download(
        url=direct_url,
        filename=filename,
    )
