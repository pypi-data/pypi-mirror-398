"""
Company Context - Simplified Input System
Replaces the complex market-aware system with simple company information fields.
All fields are optional except company URL.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class CompanyContext:
    """
    Simple company context for blog generation.
    
    INPUT: Only company_url is required (mandatory input).
    OUTPUT: All fields are mandatory in output (always present, even if empty).
    
    Field names match opencontext schema for compatibility:
    - products (not products_services)
    - tone (not brand_tone)
    """
    
    # REQUIRED INPUT FIELD
    company_url: str  # Required input - Company website URL
    
    # OPTIONAL INPUT FIELDS - Company Information (mandatory in output)
    company_name: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    
    # OPTIONAL INPUT FIELDS - Products & Services (mandatory in output)
    products: Optional[List[str]] = field(default_factory=list)  # Renamed from products_services
    target_audience: Optional[str] = None
    
    # OPTIONAL INPUT FIELDS - Competitive Context (mandatory in output)
    competitors: Optional[List[str]] = field(default_factory=list)
    tone: Optional[str] = None  # Renamed from brand_tone
    
    # OPTIONAL INPUT FIELDS - Business Context (mandatory in output)
    pain_points: Optional[List[str]] = field(default_factory=list)
    value_propositions: Optional[List[str]] = field(default_factory=list)
    use_cases: Optional[List[str]] = field(default_factory=list)
    content_themes: Optional[List[str]] = field(default_factory=list)
    
    # OPTIONAL INPUT FIELDS - Content Guidelines (mandatory in output, openblog-specific)
    system_instructions: Optional[str] = None  # Reusable prompts for all content
    client_knowledge_base: Optional[List[str]] = field(default_factory=list)  # Facts about company
    content_instructions: Optional[str] = None  # Style, format, requirements

    # OPTIONAL INPUT FIELD - Voice Persona (from OpenContext, dynamic per-company)
    voice_persona: Optional[Dict[str, Any]] = field(default_factory=dict)  # ICP-aligned writing style
    
    def validate(self) -> bool:
        """
        Validate the company context.
        Only company_url is required, everything else is optional.
        """
        if not self.company_url or not self.company_url.strip():
            raise ValueError("company_url is required")
        
        # Basic URL validation
        if not (self.company_url.startswith('http://') or self.company_url.startswith('https://')):
            logger.warning(f"Company URL should include protocol (http/https): {self.company_url}")
        
        return True
    
    def to_prompt_context(self) -> Dict[str, Any]:
        """
        Convert company context to prompt variables for content generation.
        
        OUTPUT: All fields are mandatory - always present in output (even if empty).
        This ensures consistent structure matching opencontext schema.
        
        Returns a dictionary suitable for prompt template injection.
        """
        # MANDATORY OUTPUT: All fields always present
        context = {
            # Required input
            "company_url": self.company_url,
            
            # Company Information (mandatory output)
            "company_name": self.company_name or "the company",
            "industry": self.industry or "",
            "description": self.description or "",
            
            # Products & Services (mandatory output)
            "products": ", ".join(self.products) if self.products else "",
            "target_audience": self.target_audience or "",
            
            # Competitive Context (mandatory output)
            "competitors": self.competitors or [],  # List format (matching opencontext string[])
            "tone": self.tone or "professional",
            
            # Business Context (mandatory output)
            "pain_points": "\n".join([f"- {point}" for point in self.pain_points]) if self.pain_points else "",
            "value_propositions": "\n".join([f"- {prop}" for prop in self.value_propositions]) if self.value_propositions else "",
            "use_cases": "\n".join([f"- {case}" for case in self.use_cases]) if self.use_cases else "",
            "content_themes": ", ".join(self.content_themes) if self.content_themes else "",
            
            # Content Guidelines (mandatory output, openblog-specific)
            "system_instructions": self.system_instructions or "",
            "client_knowledge_base": "\n".join([f"- {fact}" for fact in self.client_knowledge_base]) if self.client_knowledge_base else "",
            "content_instructions": self.content_instructions or "",

            # Voice Persona (from OpenContext, dynamic per-company)
            "voice_persona": self.voice_persona or {},
        }

        return context
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompanyContext':
        """
        Create CompanyContext from dictionary.
        
        Handles both list and string inputs for flexibility.
        Supports both old field names (products_services, brand_tone) and new names (products, tone)
        for backward compatibility with opencontext.
        """
        # Helper function to ensure list format
        def ensure_list(value):
            if isinstance(value, str):
                # Split by newlines or commas and clean up
                items = [item.strip() for item in value.replace('\n', ',').split(',') if item.strip()]
                return items
            elif isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            else:
                return []
        
        # Support both old and new field names (backward compatibility)
        # Old: products_services, brand_tone
        # New: products, tone (matching opencontext)
        products = ensure_list(
            data.get("products", []) or  # New name (opencontext)
            data.get("products_services", [])  # Old name (backward compat)
        )
        
        tone = (
            data.get("tone") or  # New name (opencontext)
            data.get("brand_tone")  # Old name (backward compat)
        )
        
        return cls(
            company_url=data.get("company_url", ""),
            company_name=data.get("company_name"),
            industry=data.get("industry"),
            description=data.get("description"),
            products=products,  # New name
            target_audience=data.get("target_audience"),
            competitors=ensure_list(data.get("competitors", [])),
            tone=tone,  # New name
            pain_points=ensure_list(data.get("pain_points", [])),
            value_propositions=ensure_list(data.get("value_propositions", [])),
            use_cases=ensure_list(data.get("use_cases", [])),
            content_themes=ensure_list(data.get("content_themes", [])),
            system_instructions=data.get("system_instructions"),
            client_knowledge_base=ensure_list(data.get("client_knowledge_base", [])),
            content_instructions=data.get("content_instructions"),
            voice_persona=data.get("voice_persona", {}) or {},
        )


def create_scaile_example() -> CompanyContext:
    """Create example CompanyContext for SCAILE."""
    return CompanyContext(
        company_url="https://scaile.tech",
        company_name="SCAILE",
        industry="AI Marketing & Answer Engine Optimization (AEO)",
        description="SCAILE provides an AI Visibility Engine designed to help B2B companies and startups appear in AI-generated search results like Google AI Overviews and ChatGPT. By focusing on Answer Engine Optimization (AEO) rather than traditional SEO, they offer a productized, automated solution to turn brands into authoritative sources for high-intent AI queries.",
        products=[  # Renamed from products_services
            "AI Visibility Engine",
            "AEO Foundation (30 articles/mo)",
            "AEO Expansion (50 articles/mo)", 
            "AEO Empire (100 articles/mo)",
            "Deep Intent Research",
            "5-LLM Visibility Tracking"
        ],
        target_audience="B2B Startups, SMEs (German Mittelstand), and Enterprise companies looking to dominate niche markets and automate inbound lead generation.",
        competitors=[
            "Profound", "Sight AI", "RevenueZen", "Omniscient Digital", 
            "iPullRank", "First Page Sage", "AWISEE", "WebFX", 
            "Intero Digital", "Nine Peaks Media"
        ],
        tone="Professional, results-oriented, innovative, confident, and efficient (emphasizing 'productized' solutions over 'selling hours').",  # Renamed from brand_tone
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
        system_instructions="Always mention sustainability. Focus on B2B audiences. Use technical language. Emphasize ROI and cost savings.",
        client_knowledge_base=[
            "We target Fortune 500 companies",
            "We specialize in security solutions", 
            "Founded in 2020"
        ],
        content_instructions="Include statistics, add case studies, use conversational tone, focus on AEO and Answer Engine visibility, include variations with 'AI search'"
    )