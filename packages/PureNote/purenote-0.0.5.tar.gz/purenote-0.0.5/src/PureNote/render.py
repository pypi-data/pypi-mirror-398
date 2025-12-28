from IPython import display
from IPython.display import HTML
import urllib.request
import re

from PureNote.custom_exception import InvalidURLException
from PureNote.logger import logger


def is_valid(url:str)->bool:
    """
    Checking whether a URL is reachable
    """
    try:
        response_status=urllib.request.urlopen(url,timeout=5).getcode()
        logger.debug(f"response_status: {response_status}")
        return response_status==200
    except Exception as e:
        logger.exception(e)
        return False


def render_website(url:str,width:str="100%",height:str="600")->None:
    """
    Render a website inline inside Jupyter Notebook / Google Colab.
    """
    if not is_valid(url):
        logger.error(f"Invalid URL: {url}")
        raise InvalidURLException(f"Invalid URL: {url}")

    iframe=display.IFrame(src=url,width=width,height=height)
    display.display(iframe)

    logger.info("Website rendered successfully.")


def render_youtube_video(url:str,width:int=780,height:int=440)->None:
    """
    Render a YouTube video inline inside Jupyter Notebook / Google Colab.
    """
    regex=r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match=re.search(regex,url)

    if not match:
        logger.error(f"Invalid YouTube URL: {url}")
        raise InvalidURLException(f"Invalid YouTube URL: {url}")

    video_id=match.group(1)
    embed_url=f"https://www.youtube-nocookie.com/embed/{video_id}"

    iframe=f"""
    <iframe width="{width}" height="{height}"
    src="{embed_url}"
    title="YouTube video player"
    frameborder="0"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    referrerpolicy="strict-origin-when-cross-origin"
    allowfullscreen>
    </iframe>
    """

    display.display(HTML(iframe))
    logger.info("YouTube video rendered successfully.")
