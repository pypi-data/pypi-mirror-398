"""
Graphics Prompt Generation

Generates prompts for HTML-based graphics creation using OpenFigma.
"""

def generate_graphics_config(title: str, content: str, company_data: dict = None) -> dict:
    """
    Generate graphics configuration for HTML-based graphics.
    
    Args:
        title: Title for the graphic
        content: Content context
        company_data: Company information for design language
        
    Returns:
        Graphics configuration dictionary
    """
    return {
        "type": "html_graphic",
        "title": title,
        "content": content,
        "company_data": company_data or {},
        "style": "modern_infographic"
    }

async def generate_graphics_config_async(title: str, content: str, company_data: dict = None) -> dict:
    """
    Async version of generate_graphics_config.
    """
    return generate_graphics_config(title, content, company_data)