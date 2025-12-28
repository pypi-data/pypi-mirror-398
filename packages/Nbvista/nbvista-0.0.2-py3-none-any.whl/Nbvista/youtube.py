from Nbvista.custom_exception import InvalidURLException
from Nbvista.logger import logger
from IPython.display import HTML, display
import re


def render_YouTube_video(url: str, width: int = 780, height: int=440):
    try:
        # Extract ID using a more robust regex
        regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
        match = re.search(regex, url)
        if not match:
            raise InvalidURLException
        
        video_id = match.group(1)
        
        # Use youtube-nocookie.com and add the referrerpolicy attribute
        # This is the key to fixing Error 153
        embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}"
        
        iframe = f"""
        <iframe width="{width}" height="{height}" 
        src="{embed_url}" 
        title="YouTube video player" 
        frameborder="0" 
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
        referrerpolicy="strict-origin-when-cross-origin" 
        allowfullscreen>
        </iframe>
        """
        display(HTML(iframe))
        logger.info("YouTube video rendered successfully.")

        return "success"
    
    except Exception as e:
        raise e
    
 