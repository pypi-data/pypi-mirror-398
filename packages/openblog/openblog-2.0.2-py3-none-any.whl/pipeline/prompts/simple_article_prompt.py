"""
Simple Article Prompt - Company Context Based
Replaces complex market-aware prompts with simple company context injection.
Enhanced with dynamically-generated voice personas from OpenContext.
"""

from typing import Dict, Any
import logging

from .voice_personas import get_voice_persona_section

logger = logging.getLogger(__name__)


def build_article_prompt(
    primary_keyword: str,
    company_context: Dict[str, Any],
    language: str = "en",
    word_count: int = None,
    country: str = None,
    content_generation_instruction: str = None,
    tone_override: str = None,
    system_prompts: list = None,
    **kwargs
) -> str:
    """
    Build a simple article prompt using company context.
    
    Args:
        primary_keyword: Main topic/keyword for the article
        company_context: Company information from CompanyContext.to_prompt_context()
        language: Target language (default: en)
        **kwargs: Additional parameters
    
    Returns:
        Complete prompt string ready for Gemini
    """
    
    # All fields are mandatory in output (from to_prompt_context)
    company_name = company_context.get("company_name", "the company")
    company_url = company_context.get("company_url", "")
    industry = company_context.get("industry", "")
    description = company_context.get("description", "")
    # Tone priority: job_config.tone_override > company_context.tone > "professional"
    tone = tone_override or company_context.get("tone", "professional")  # Renamed from brand_tone
    
    # Products & Services (renamed from products_services)
    products = company_context.get("products", "")
    target_audience = company_context.get("target_audience", "")
    competitors_raw = company_context.get("competitors", [])  # List format (matching opencontext)
    competitors = ", ".join(competitors_raw) if isinstance(competitors_raw, list) else str(competitors_raw) if competitors_raw else ""
    pain_points = company_context.get("pain_points", "")
    value_propositions = company_context.get("value_propositions", "")
    use_cases = company_context.get("use_cases", "")
    content_themes = company_context.get("content_themes", "")
    
    # Content guidelines (article-level from company_context)
    system_instructions = company_context.get("system_instructions", "")
    client_knowledge_base = company_context.get("client_knowledge_base", "")
    content_instructions = company_context.get("content_instructions", "")
    
    # Batch-level system prompts (merge with article-level)
    system_prompts = system_prompts or []
    batch_system_prompts_text = ""
    if system_prompts:
        batch_system_prompts_text = "\n".join([f"- {prompt}" for prompt in system_prompts])
    
    # Build the company context section
    company_section = f"""
COMPANY CONTEXT:
Company: {company_name}
Website: {company_url}"""
    
    if industry:
        company_section += f"\nIndustry: {industry}"
    
    if description:
        company_section += f"\nDescription: {description}"
        
    if products:
        company_section += f"\nProducts/Services: {products}"
    
    if target_audience:
        company_section += f"\nTarget Audience: {target_audience}"
    
    if tone:
        company_section += f"\nBrand Tone: {tone}"
    
    # Add optional sections if provided
    optional_sections = ""
    
    if pain_points:
        optional_sections += f"""

CUSTOMER PAIN POINTS:
{pain_points}"""
    
    if value_propositions:
        optional_sections += f"""

VALUE PROPOSITIONS:
{value_propositions}"""
    
    if use_cases:
        optional_sections += f"""

USE CASES:
{use_cases}"""
    
    if content_themes:
        optional_sections += f"""

CONTENT THEMES: {content_themes}"""
    
    if competitors:
        optional_sections += f"""

COMPETITORS TO DIFFERENTIATE FROM: {competitors}"""
    
    # Content guidelines section
    guidelines_section = ""

    # Article-level system instructions (from company_context)
    if system_instructions:
        guidelines_section += f"""

SYSTEM INSTRUCTIONS (Article-level):
{system_instructions}"""

    # Batch-level system prompts (applies to all articles in batch)
    if batch_system_prompts_text:
        guidelines_section += f"""

BATCH INSTRUCTIONS (Applies to all articles in this batch):
{batch_system_prompts_text}"""

    # Company knowledge base (article-level)
    if client_knowledge_base:
        guidelines_section += f"""

COMPANY KNOWLEDGE BASE:
{client_knowledge_base}"""

    # Article-level content instructions
    if content_instructions:
        guidelines_section += f"""

CONTENT WRITING INSTRUCTIONS (Article-level):
{content_instructions}"""

    # Voice persona section (from OpenContext - dynamically generated per company)
    voice_persona_section = ""
    persona_text = get_voice_persona_section(company_context)
    if persona_text:
        voice_persona_section = f"""

{persona_text}"""
        logger.debug(f"Added voice persona from OpenContext")
    
    # Determine word count target (dynamic or default)
    if word_count:
        word_count_text = f"{word_count:,} words"
        if word_count < 1500:
            word_count_range = f"{max(800, word_count - 200)}-{word_count + 200} words"
        elif word_count < 2500:
            word_count_range = f"{word_count - 300}-{word_count + 300} words"
        else:
            word_count_range = f"{word_count - 500}-{word_count + 500} words"
    else:
        word_count_text = "1,500-2,500 words"
        word_count_range = "1,500-2,500 words"
    
    # Build market context section (if country provided)
    market_section = ""
    if country:
        country_name_map = {
            "US": "United States", "DE": "Germany", "FR": "France", "GB": "United Kingdom", "UK": "United Kingdom",
            "IT": "Italy", "ES": "Spain", "NL": "Netherlands", "BE": "Belgium", "AT": "Austria", "CH": "Switzerland",
            "PL": "Poland", "SE": "Sweden", "NO": "Norway", "DK": "Denmark", "FI": "Finland", "IE": "Ireland",
            "PT": "Portugal", "GR": "Greece", "CZ": "Czech Republic", "HU": "Hungary", "RO": "Romania"
        }
        country_display = country_name_map.get(country.upper(), country.upper())
        market_section = f"""
TARGET MARKET:
- Primary country: {country_display} ({country.upper()})
- Adapt content for {country_display} market context, regulations, and cultural expectations
- Use market-appropriate examples, authorities, and references
- Consider local business practices and industry standards for {country_display}
"""
    
    # Build content generation instruction section (if provided)
    custom_instruction_section = ""
    if content_generation_instruction and content_generation_instruction.strip():
        custom_instruction_section = f"""

ADDITIONAL CONTENT INSTRUCTIONS:
{content_generation_instruction}
"""
    
    # Build the complete prompt
    prompt = f"""Write a comprehensive, high-quality blog article about "{primary_keyword}".

TOPIC FOCUS:
The article must be entirely focused on "{primary_keyword}". Every section, paragraph, and example should relate directly to this topic.
- Deep dive into what "{primary_keyword}" means, how it works, why it matters
- Provide practical, actionable insights about "{primary_keyword}"
- Include real-world examples and use cases related to "{primary_keyword}"
- Address common questions and concerns about "{primary_keyword}"

{voice_persona_section}{company_section}{optional_sections}{guidelines_section}{market_section}{custom_instruction_section}

ARTICLE REQUIREMENTS:
- Target language: {language}
- Write in {tone} tone
- Focus on providing genuine value to readers
- Include specific examples and actionable insights
- Structure with clear headings and subheadings
- Include introduction, main sections, and conclusion
- Make it engaging and informative
- Note: Word count target is specified dynamically in the system instruction (based on job configuration)

CRITICAL REQUIREMENTS (Detailed specifications in system instruction):
- Follow all citation requirements specified in the system instruction (every paragraph must include citations)
- Follow all section header requirements specified in the system instruction (2+ question-format headers)
- Follow all conversational tone requirements specified in the system instruction (10+ conversational phrases)
- Follow all content quality requirements specified in the system instruction (E-E-A-T, data-driven content, section variety)
- **MANDATORY:** Include `image_01_url` (Unsplash URL) and `image_01_alt_text` - these are REQUIRED fields in the JSON schema
- **RECOMMENDED:** Include `image_02_url` and `image_03_url` (Unsplash URLs) with alt text and credits for better engagement
- **CRITICAL FOR SEO:** Create VARIED section lengths (not uniform) - at least 2 LONG sections (700+ words), 2-3 MEDIUM sections (400-600 words), remaining SHORT (200-300 words). You decide which topics deserve LONG treatment based on their complexity and importance.

Please write the complete article now."""

    logger.debug(f"Generated prompt length: {len(prompt)} characters")
    logger.debug(f"Company context included: {bool(company_name and company_url)}")
    logger.debug(f"Optional sections: {len(optional_sections)} chars")
    logger.debug(f"Guidelines sections: {len(guidelines_section)} chars")
    logger.debug(f"Voice persona section: {len(voice_persona_section)} chars")
    
    return prompt


def validate_prompt_inputs(primary_keyword: str, company_context: Dict[str, Any]) -> bool:
    """
    Validate that required inputs are provided for prompt generation.
    
    Args:
        primary_keyword: Main topic/keyword
        company_context: Company information dictionary
    
    Returns:
        True if valid, raises ValueError if invalid
    """
    if not primary_keyword or not primary_keyword.strip():
        raise ValueError("primary_keyword is required and cannot be empty")
    
    if not company_context.get("company_url"):
        raise ValueError("company_url is required in company_context")
    
    return True


def get_prompt_length_estimate(
    primary_keyword: str,
    company_context: Dict[str, Any],
    language: str = "en"
) -> int:
    """
    Estimate the prompt length without building the full prompt.
    Useful for checking if prompt will be too long for API limits.
    """
    base_prompt_length = 800  # Approximate base template length
    
    # Add length of dynamic content
    keyword_length = len(primary_keyword) if primary_keyword else 0
    company_name_length = len(company_context.get("company_name", "")) 
    description_length = len(company_context.get("description", ""))
    
    # Add length of optional sections
    optional_length = sum([
        len(company_context.get("products", "")),
        len(company_context.get("target_audience", "")),
        len(", ".join(company_context.get("competitors", [])) if isinstance(company_context.get("competitors", []), list) else company_context.get("competitors", "")),
        len(company_context.get("pain_points", "")),
        len(company_context.get("value_propositions", "")),
        len(company_context.get("use_cases", "")),
        len(company_context.get("content_themes", "")),
        len(company_context.get("system_instructions", "")),
        len(company_context.get("client_knowledge_base", "")),
        len(company_context.get("content_instructions", ""))
    ])
    
    estimated_length = base_prompt_length + keyword_length + company_name_length + description_length + optional_length
    
    logger.debug(f"Estimated prompt length: {estimated_length} characters")
    return estimated_length