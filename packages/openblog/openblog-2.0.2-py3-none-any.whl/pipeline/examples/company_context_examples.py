"""
Company Context Examples
Example company data for testing and reference.
"""

from ..core.company_context import CompanyContext

def get_scaile_example() -> CompanyContext:
    """
    SCAILE - AI Marketing & Answer Engine Optimization
    Complete example with all supported fields.
    """
    return CompanyContext(
        # REQUIRED FIELD
        company_url="https://scaile.tech",
        
        # OPTIONAL FIELDS - Company Information  
        company_name="SCAILE",
        industry="AI Marketing & Answer Engine Optimization (AEO)",
        description="SCAILE provides an AI Visibility Engine designed to help B2B companies and startups appear in AI-generated search results like Google AI Overviews and ChatGPT. By focusing on Answer Engine Optimization (AEO) rather than traditional SEO, they offer a productized, automated solution to turn brands into authoritative sources for high-intent AI queries.",
        
        # OPTIONAL FIELDS - Products & Services
        products=[  # Renamed from products_services to match opencontext
            "AI Visibility Engine",
            "AEO Foundation (30 articles/mo)",
            "AEO Expansion (50 articles/mo)", 
            "AEO Empire (100 articles/mo)",
            "Deep Intent Research",
            "5-LLM Visibility Tracking"
        ],
        target_audience="B2B Startups, SMEs (German Mittelstand), and Enterprise companies looking to dominate niche markets and automate inbound lead generation.",
        
        # OPTIONAL FIELDS - Competitive Context
        competitors=[
            "Profound", "Sight AI", "RevenueZen", "Omniscient Digital", 
            "iPullRank", "First Page Sage", "AWISEE", "WebFX", 
            "Intero Digital", "Nine Peaks Media"
        ],
        tone="Professional, results-oriented, innovative, confident, and efficient (emphasizing 'productized' solutions over 'selling hours').",  # Renamed from brand_tone to match opencontext
        
        # OPTIONAL FIELDS - Business Context
        pain_points=[
            "Invisibility in modern AI search tools like ChatGPT and Google AI Overviews",
            "Declining effectiveness of traditional SEO and manual sales outreach", 
            "High costs and difficulty in scaling content production for multiple markets",
            "Lack of qualified inbound leads from technical or niche audiences",
            "Unpredictable revenue funnels and reliance on headcount for growth"
        ],
        value_propositions=[
            "Guaranteed visibility in the new era of AI-driven search",
            "A productized, automated engine that replaces manual agency hours",
            "Ability to dominate multiple markets with zero additional headcount", 
            "KPI-first approach focused on tangible revenue and lead growth",
            "Comprehensive tracking across major LLMs to ensure brand authority"
        ],
        use_cases=[
            "Ranking for 'Best [Product] for [Industry]' queries in ChatGPT",
            "Securing visibility in Google AI Overviews for high-intent searches",
            "Automating content creation to enter new language markets (e.g., German & English)",
            "Establishing brand authority as a primary source for AI answers", 
            "Scaling inbound lead generation without increasing marketing headcount"
        ],
        content_themes=[
            "Answer Engine Optimization (AEO)",
            "AI Search Visibility", 
            "Generative Engine Optimization (GEO)",
            "B2B Sales Automation",
            "Digital Go-to-Market Strategy",
            "High-Intent Query Optimization"
        ],
        
        # OPTIONAL FIELDS - Content Guidelines
        system_instructions="Always mention sustainability. Focus on B2B audiences. Use technical language. Emphasize ROI and cost savings.",
        client_knowledge_base=[
            "We target Fortune 500 companies",
            "We specialize in security solutions", 
            "Founded in 2020"
        ],
        content_instructions="Include statistics, add case studies, use conversational tone, focus on AEO and Answer Engine visibility, include variations with 'AI search'"
    )


def get_minimal_example() -> CompanyContext:
    """
    Minimal example - only required field (company_url).
    Shows that all other fields are optional.
    """
    return CompanyContext(
        company_url="https://example.com"
    )


# Export all examples for easy importing
COMPANY_EXAMPLES = {
    "scaile": get_scaile_example(),
    "minimal": get_minimal_example()
}