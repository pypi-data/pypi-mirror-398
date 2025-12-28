"""
maix.http module
"""
from __future__ import annotations
import maix._maix.err
import maix._maix.image
__all__: list[str] = ['JpegStreamer']
class JpegStreamer:
    def __init__(self, host: str = '', port: int = 8000, client_number: int = 16) -> None:
        ...
    def host(self) -> str:
        """
        Get host
        
        Returns: host name
        """
    def port(self) -> int:
        """
        Get port
        
        Returns: port
        """
    def set_html(self, data: str) -> maix._maix.err.Err:
        """
        add your style in this api
        default is:
        <html>
        <body>
        <h1>JPG Stream</h1>
        <img src='/stream'>
        </body>
        </html>
        
        Args:
          - data: html code
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def start(self) -> maix._maix.err.Err:
        """
        start jpeg streame
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def stop(self) -> maix._maix.err.Err:
        """
        stop http
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def write(self, img: maix._maix.image.Image) -> maix._maix.err.Err:
        """
        Write data to http
        
        Args:
          - img: image object
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
