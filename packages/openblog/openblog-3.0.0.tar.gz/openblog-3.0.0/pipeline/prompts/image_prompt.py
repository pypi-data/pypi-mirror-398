"""
Image Generation Prompt Generator

Maps to v4.1 Phase 8, Step 25: get-insights

Generates detailed, specific image generation prompts based on article headline
and company information for high-quality, authentic-looking article images.

Prompt requirements:
- Style: realistic, documentary, professional
- Lighting: natural daylight (not artificial)
- Authenticity: genuine/authentic setting (not stock-photo-like)
- Subject: Should relate to headline + company industry
- Output language: company language (from job_config.gpt_language)
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def generate_image_prompt(
    headline: str,
    company_data: Dict[str, Any],
    job_config: Dict[str, Any],
) -> str:
    """
    Generate detailed image generation prompt.

    Args:
        headline: Article headline
        company_data: Company information (name, industry, description)
        job_config: Job configuration (language, etc.)

    Returns:
        Detailed image prompt for image generator
    """
    company_name = company_data.get("company_name", "")
    industry = company_data.get("industry", "")
    description = company_data.get("description", "")
    language = job_config.get("gpt_language", "en")

    # Extract key concepts from headline
    headline_clean = headline.replace("Guide to", "").replace("Complete", "").strip()

    # Determine image style based on company industry
    industry_style = _get_industry_style(industry)

    # Build prompt in company's language
    if language == "de":
        prompt = _build_german_prompt(headline_clean, company_name, industry_style, industry)
    elif language == "fr":
        prompt = _build_french_prompt(headline_clean, company_name, industry_style, industry)
    elif language == "es":
        prompt = _build_spanish_prompt(headline_clean, company_name, industry_style, industry)
    else:
        prompt = _build_english_prompt(headline_clean, company_name, industry_style, industry)

    logger.debug(f"Generated image prompt for: {headline}")
    return prompt


def _get_industry_style(industry: str) -> str:
    """
    Determine image style based on industry.

    Args:
        industry: Industry/vertical

    Returns:
        Industry-specific style descriptor
    """
    industry_lower = industry.lower() if industry else ""

    if "tech" in industry_lower or "software" in industry_lower:
        return "modern tech workspace with computers and collaboration"
    elif "finance" in industry_lower or "bank" in industry_lower:
        return "professional financial environment with charts and data"
    elif "healthcare" in industry_lower or "medical" in industry_lower:
        return "professional healthcare setting with modern equipment"
    elif "retail" in industry_lower or "ecommerce" in industry_lower:
        return "modern retail or online business environment"
    elif "real estate" in industry_lower:
        return "modern property or real estate office environment"
    elif "education" in industry_lower:
        return "educational or learning environment"
    elif "marketing" in industry_lower or "advertising" in industry_lower:
        return "creative marketing agency or business environment"
    elif "food" in industry_lower or "restaurant" in industry_lower:
        return "professional culinary or food service setting"
    elif "travel" in industry_lower or "tourism" in industry_lower:
        return "scenic travel or hospitality setting"
    else:
        return "professional business environment with modern workspace"


def _build_english_prompt(
    headline: str,
    company_name: str,
    industry_style: str,
    industry: str,
) -> str:
    """Build English language image prompt."""
    return f"""Create a professional, realistic blog article header image (1200x630 pixels).

Subject: {headline}

Style Requirements:
- Professional and authentic documentary style
- Natural daylight lighting (not artificial or studio lighting)
- Genuine, realistic setting (avoid stock photo clichés)
- Modern, high-quality photography aesthetic
- Relevant to: {industry if industry else 'business'}

The image should visually represent the topic of "{headline}" in a {industry_style} context.
The setting should look authentic and professional, as if photographed in a real, working environment.
Include professional elements that convey expertise and credibility in the {industry if industry else 'business'} sector.

Technical requirements:
- Size: 1200x630 pixels (landscape)
- Format: High-quality realistic photo
- No text, logos, or watermarks
- High contrast and visibility
- Professional color grading
"""


def _build_german_prompt(
    headline: str,
    company_name: str,
    industry_style: str,
    industry: str,
) -> str:
    """Build German language image prompt."""
    return f"""Erstelle ein professionelles, realistisches Blog-Artikel-Kopfbildes (1200x630 Pixel).

Thema: {headline}

Stilanforderungen:
- Professioneller und authentischer dokumentarischer Stil
- Natürliche Tageslichtbeleuchtung (keine künstliche oder Studiobeleuchtung)
- Authentische, realistische Umgebung (keine Stock-Foto-Klischees)
- Moderne, hochwertige Fotografie-Ästhetik
- Relevant für: {industry if industry else 'Geschäfte'}

Das Bild sollte das Thema "{headline}" in einem {industry_style} visuell darstellen.
Die Umgebung sollte authentisch und professionell wirken, als würde sie in einer echten, arbeitenden Umgebung fotografiert.
Fügen Sie professionelle Elemente ein, die Fachwissen und Glaubwürdigkeit in der {industry if industry else 'Geschäfts'}-Branche vermitteln.

Technische Anforderungen:
- Größe: 1200x630 Pixel (Querformat)
- Format: Hochwertige realistische Fotografie
- Kein Text, Logos oder Wasserzeichen
- Hoher Kontrast und Sichtbarkeit
- Professionelle Farbbearbeitung
"""


def _build_french_prompt(
    headline: str,
    company_name: str,
    industry_style: str,
    industry: str,
) -> str:
    """Build French language image prompt."""
    return f"""Créez une image d'en-tête de blog professionnelle et réaliste (1200x630 pixels).

Sujet: {headline}

Exigences de style:
- Style documentaire professionnel et authentique
- Éclairage naturel à la lumière du jour (pas d'éclairage artificiel ou de studio)
- Cadre authentique et réaliste (éviter les clichés des photos de stock)
- Esthétique photographique moderne et de haute qualité
- Pertinent pour: {industry if industry else 'business'}

L'image devrait représenter visuellement le sujet "{headline}" dans un contexte de {industry_style}.
Le cadre devrait sembler authentique et professionnel, comme s'il était photographié dans un vrai environnement de travail.
Incluez des éléments professionnels qui transmettent l'expertise et la crédibilité dans le secteur {industry if industry else 'commercial'}.

Exigences techniques:
- Taille: 1200x630 pixels (paysage)
- Format: Photo réaliste de haute qualité
- Pas de texte, de logos ou de filigranes
- Contraste élevé et visibilité
- Correction couleur professionnelle
"""


def _build_spanish_prompt(
    headline: str,
    company_name: str,
    industry_style: str,
    industry: str,
) -> str:
    """Build Spanish language image prompt."""
    return f"""Crea una imagen de encabezado de artículo de blog profesional y realista (1200x630 píxeles).

Tema: {headline}

Requisitos de estilo:
- Estilo documental profesional y auténtico
- Iluminación natural con luz diurna (sin iluminación artificial ni de estudio)
- Entorno auténtico y realista (evitar clichés de fotos de archivo)
- Estética fotográfica moderna y de alta calidad
- Relevante para: {industry if industry else 'negocios'}

La imagen debe representar visualmente el tema "{headline}" en un contexto de {industry_style}.
El entorno debe parecer auténtico y profesional, como si estuviera fotografiado en un ambiente de trabajo real.
Incluya elementos profesionales que transmitan experiencia y credibilidad en el sector {industry if industry else 'empresarial'}.

Requisitos técnicos:
- Tamaño: 1200x630 píxeles (horizontal)
- Formato: Fotografía realista de alta calidad
- Sin texto, logotipos ni marcas de agua
- Alto contraste y visibilidad
- Corrección de color profesional
"""
