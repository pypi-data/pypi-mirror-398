"""Prompt templates for blog-writer."""

from .main_article import get_main_article_prompt
from .image_prompt import generate_image_prompt

__all__ = ["get_main_article_prompt", "generate_image_prompt"]

