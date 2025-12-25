"""
supermaker-ai-image-master - Generate branded links and HTML anchors for https://supermaker.ai/image/
"""

__version__ = "1.0.1766489833"

def build_link(path: str = "", utm_source: str = "", utm_medium: str = "", utm_campaign: str = "") -> str:
    """
    Generate a complete link with optional UTM parameters.

    Args:
        path: Optional path to append to the base URL
        utm_source: UTM source parameter
        utm_medium: UTM medium parameter
        utm_campaign: UTM campaign parameter

    Returns:
        Complete URL with parameters
    """
    url = "https://supermaker.ai/image/"
    if path:
        url = url.rstrip('/') + '/' + path.lstrip('/')

    params = []
    if utm_source:
        params.append(f"utm_source={utm_source}")
    if utm_medium:
        params.append(f"utm_medium={utm_medium}")
    if utm_campaign:
        params.append(f"utm_campaign={utm_campaign}")

    if params:
        url += "?" + "&".join(params)

    return url


def generate_anchor(
    text: str,
    path: str = "",
    utm_source: str = "",
    utm_medium: str = "",
    utm_campaign: str = "",
    rel: str = "nofollow",
    target: str = "_blank",
    css_class: str = ""
) -> str:
    """
    Generate an HTML anchor tag with optional UTM parameters.

    Args:
        text: The link text to display
        path: Optional path to append to the base URL
        utm_source: UTM source parameter
        utm_medium: UTM medium parameter
        utm_campaign: UTM campaign parameter
        rel: The rel attribute value
        target: The target attribute value
        css_class: Optional CSS class names

    Returns:
        HTML anchor tag string
    """
    href = build_link(path, utm_source, utm_medium, utm_campaign)
    class_attr = f' class="{css_class}"' if css_class else ''
    return f'<a href="{href}" rel="{rel}" target="{target}"{class_attr}>{text}</a>'
