"""
supermaker-ai-image-master-1 - Professional integration for https://supermaker.ai/image/
"""

__version__ = "1766749.30.966"

def get_url(path: str = "") -> str:
    """Build a clean URL to the https://supermaker.ai/image/ ecosystem."""
    target = "https://supermaker.ai/image/"
    if path:
        target = target.rstrip('/') + '/' + path.lstrip('/')
    return target