"""
Stage 3: Quality Refinement & Validation

🛡️ AI-ONLY QUALITY REFINEMENT (Zero Regex/String Manipulation)

This stage is part of a 2-layer production quality system:
- Layer 1: Prevention (Stage 2 prompt rules)
- Layer 2: AI-based quality refinement (this stage) [NON-BLOCKING]

Uses Gemini AI to detect and fix quality issues:
1. Structural issues (truncated lists, malformed HTML, orphaned paragraphs)
2. AI language markers (em/en dashes, robotic phrases, academic citations)
3. Content quality (incomplete sentences, grammar issues)
4. AEO optimization (citations, conversational phrases, question patterns)
5. Domain-only URL enhancement in Sources field
6. FAQ/PAA validation and deduplication (consolidated from Stage 8)

All fixes are performed by Gemini AI - no regex or string manipulation.
Runs AFTER Stage 2 (Generation + Extraction) but BEFORE Stage 4-9 (Parallel stages).
"""

import logging
import asyncio
import html
from typing import Dict, List, Any, Optional, Tuple

from ..core import ExecutionContext, Stage
from ..models.output_schema import ArticleOutput

logger = logging.getLogger(__name__)


def _encode_html_entities_in_content(article_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encode HTML entities in HTML content fields.
    
    Properly encodes & characters in text content (not already part of entities).
    Uses minimal regex - only splits HTML tags from text content.
    
    Args:
        article_dict: Dictionary containing article fields
        
    Returns:
        Dictionary with HTML entities properly encoded
    """
    import re
    
    # HTML content fields that may contain entities
    html_fields = [
        'Intro', 'Direct_Answer',
        'section_01_content', 'section_02_content', 'section_03_content',
        'section_04_content', 'section_05_content', 'section_06_content',
        'section_07_content', 'section_08_content', 'section_09_content',
    ]
    
    encoded_dict = article_dict.copy()
    
    for field in html_fields:
        if field in encoded_dict and encoded_dict[field]:
            content = str(encoded_dict[field])
            
            # Only process if content contains HTML tags
            if '<' in content and '>' in content:
                # Split content into HTML tags and text content
                # This regex splits on HTML tags: <...>
                parts = re.split(r'(<[^>]+>)', content)
                encoded_parts = []
                
                for part in parts:
                    if part.startswith('<') and part.endswith('>'):
                        # This is an HTML tag - preserve as-is
                        encoded_parts.append(part)
                    else:
                        # This is text content - encode & that's not already part of an entity
                        # Only encode & that's not followed by amp;, lt;, gt;, quot;, #, or a letter
                        # This handles: & -> &amp; but preserves &amp;, &lt;, etc.
                        encoded_text = re.sub(
                            r'&(?!amp;|lt;|gt;|quot;|#\d+;|#[xX][0-9a-fA-F]+;|[a-zA-Z]+;)',
                            '&amp;',
                            part
                        )
                        encoded_parts.append(encoded_text)
                
                encoded_dict[field] = ''.join(encoded_parts)
    
    return encoded_dict


class QualityRefinementStage(Stage):
    """
    Stage 3: Quality Refinement & Validation.
    
    Executed after Stage 2 (Generation + Extraction).
    
    Uses Gemini AI to detect and fix quality issues in content:
    - Structural issues (truncated lists, malformed HTML, orphaned paragraphs)
    - AI language markers (em/en dashes, robotic phrases, academic citations)
    - Content quality (incomplete sentences, grammar issues)
    - AEO optimization (citations, conversational phrases, question patterns)
    - Domain-only URL enhancement in Sources field
    - FAQ/PAA validation and deduplication (consolidated from Stage 8)
    """
    
    stage_num = 3  # Quality refinement after generation + extraction
    stage_name = "Quality Refinement & Validation"
    
    # Quality thresholds
    KEYWORD_TARGET_MIN = 5
    KEYWORD_TARGET_MAX = 8
    FIRST_PARAGRAPH_MIN_WORDS = 60
    FIRST_PARAGRAPH_MAX_WORDS = 100
    
    # AI marker patterns
    AI_MARKERS = {
        "em_dash": "—",
        "en_dash": "–",
        "robotic_phrases": [
            "Here's how",
            "Here's what",
            "Key points:",
            "Key benefits include:",
            "Important considerations:",
            "That's why similarly",
            "If you want another",
            "You'll find to",
            "Here are key points:",
            "Here are the key points:",
            "Here are key takeaways:",
        ]
    }
    
    # COMPREHENSIVE QUALITY CHECKLIST
    # These are the issues Stage 3 must detect and fix
    QUALITY_CHECKLIST = """
    STAGE 3 QUALITY CHECKLIST - All issues to detect and fix:
    
    1. DUPLICATE BULLET LISTS
       Problem: Paragraph followed by <ul><li> that repeats the same content
       Example: "<p>AI improves X, Y, Z.</p><ul><li>AI improves X</li><li>Y</li><li>Z</li></ul>"
       Fix: Remove the duplicate bullet list, keep only the paragraph
    
    2. TRUNCATED LIST ITEMS
       Problem: List items cut off mid-sentence without punctuation
       Example: "<li>The best practice for 2025 is platformization - consolidating point solutions into</li>"
       Fix: Complete the sentence or remove the truncated item
    
    3. MALFORMED NESTED LISTS
       Problem: Improper HTML nesting like </p> inside <li>, or <ul> inside <li><ul>
       Example: "<ul><li>Text</p><ul><li>Nested</li></ul></li></ul>"
       Fix: Flatten the list structure, ensure proper HTML nesting
    
    4. ORPHANED INCOMPLETE PARAGRAPHS
       Problem: Paragraphs that are just "This" or incomplete sentences
       Example: "<p>This </p>" or "<p>. Also, the</p>"
       Fix: Remove the orphaned paragraph or complete it
    
    5. MISSING SOURCES
       Problem: Sources mentioned in text (IBM, Gartner, Forrester) not in Sources section
       Fix: Ensure all referenced sources appear in the Sources field with proper URLs
    
    6. ACADEMIC CITATIONS [N] IN BODY
       Problem: [1], [2], [1][2] markers appear directly in content
       Fix: Convert to natural language: "according to IBM" or remove
    
    7. EM DASHES AND EN DASHES
       Problem: — and – characters that look robotic
       Fix: Replace with regular hyphens or rewrite sentence
    
    8. ROBOTIC SUMMARY PHRASES
       Problem: "Here are key points:" followed by bullet list duplicating content
       Fix: Remove the phrase and the redundant list
    
    9. PERIOD AT START OF PARAGRAPH/LIST
       Problem: ". Also," or ". 3. Identity" at start of content
       Fix: Remove the orphaned period
    
    10. LOWERCASE AFTER PERIOD
        Problem: "sentence ends. new sentence" (lowercase after period)
        Fix: Capitalize the first letter after the period
    """
    
    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 3: Detect and fix quality issues.
        
        NEW FLOW (Dec 2024):
        1. REGEX CLEANUP FIRST - fast, deterministic fixes
        2. GEMINI REVIEW - semantic fixes that need AI
        
        Args:
            context: ExecutionContext with structured_data from Stage 2
        
        Returns:
            Updated context with refined structured_data
        """
        logger.info(f"Stage 3: {self.stage_name}")
        
        # Validate input
        if not context.structured_data:
            logger.warning("No structured_data available, skipping refinement")
            return context
        
        # ============================================================
        # STEP 1: SKIP REGEX CLEANUP - AI-only approach
        # ============================================================
        # All fixes should come from improved prompts in Stage 2
        # No regex cleanup - trust AI to generate correct content
        logger.info("🔧 Step 1: Skipping regex cleanup (AI-only approach)")
        
        # ============================================================
        # STEP 2: GEMINI REVIEW (MANDATORY - always runs)
        # ============================================================
        logger.info("🤖 Step 2: Gemini quality review (MANDATORY)...")
        context = await self._gemini_full_review(context)
        
        # ============================================================
        # STEP 3: HUMANIZE LANGUAGE (integrated into Gemini review)
        # ============================================================
        # Humanization is now handled by Gemini in Step 2 (_gemini_full_review)
        logger.info("✍️ Step 3: Humanization handled by Gemini review (Step 2)")
        
        # ============================================================
        # STEP 4+5: AEO OPTIMIZATION + URL ENHANCEMENT (PARALLEL)
        # These modify different fields so can run concurrently
        # ============================================================
        logger.info("🚀 Step 4+5: AEO optimization + URL enhancement (parallel)...")

        # Run both in parallel - they modify different fields (sections vs Sources)
        await asyncio.gather(
            self._optimize_aeo_components(context),
            self._enhance_domain_only_urls(context)
        )

        # ============================================================
        # STEP 6: VALIDATE FAQ/PAA (previously Stage 8)
        # ============================================================
        logger.info("❓ Step 6: Validating FAQ/PAA items...")
        context = self._validate_faq_paa(context)

        # ============================================================
        # STEP 7: CONTENT QUALITY VALIDATION (NEW - Human-like patterns)
        # ============================================================
        logger.info("📊 Step 7: Validating content quality patterns...")
        context = await self._validate_content_quality(context)

        # ============================================================
        # STEP 7B: QUALITY FIX LOOP (if score < 60, try to fix issues)
        # ============================================================
        initial_metrics = context.parallel_results.get("content_quality", {})
        initial_score = initial_metrics.get("score", 0)

        # Only attempt fix if: score < 60, not already attempted, and we have issues to fix
        if initial_score < 60 and not context.parallel_results.get("quality_fix_attempted"):
            context.parallel_results["quality_fix_attempted"] = True

            # Build targeted fix instructions based on detected issues
            fix_instructions = []

            question_openers = initial_metrics.get("question_openers", 0)
            if question_openers > 2:
                fix_instructions.append(
                    f"REWRITE {question_openers} section openers that start with questions. "
                    "Replace with STATEMENTS, STATISTICS, or SCENARIOS (not questions)."
                )

            attribution_ratio = initial_metrics.get("attribution_ratio", 0)
            if attribution_ratio > 0.35:
                fix_instructions.append(
                    "REDUCE attribution phrases ('According to...', 'Research shows...', 'Experts say...'). "
                    "State facts confidently without hedging."
                )

            content_blocks = initial_metrics.get("content_blocks_found", 0)
            if content_blocks < 2:
                missing = []
                if not initial_metrics.get("has_decision_framework"):
                    missing.append("a decision framework (e.g., 'Choose X if you need Y. Go with Z if you prioritize W.')")
                if not initial_metrics.get("has_scenario"):
                    missing.append("a concrete scenario (e.g., 'Imagine you're processing payments at 2am when...')")
                if not initial_metrics.get("has_mistake_callout"):
                    missing.append("a mistake callout (e.g., 'Here's where most teams go wrong...')")
                if not initial_metrics.get("has_hot_take"):
                    missing.append("a hot take/opinion (e.g., 'Honestly, most enterprises over-complicate this.')")
                if missing:
                    fix_instructions.append(f"ADD within the content: {', '.join(missing[:2])}")

            if fix_instructions:
                logger.info(f"🔧 Step 7B: Quality Fix Loop - {len(fix_instructions)} issues to fix...")
                context = await self._apply_quality_fixes(context, fix_instructions, initial_metrics)

                # Re-run validation to measure improvement
                logger.info("📊 Step 7B: Re-validating after fixes...")
                context = await self._validate_content_quality(context)

                # Log improvement
                new_metrics = context.parallel_results.get("content_quality", {})
                new_score = new_metrics.get("score", 0)
                if new_score > initial_score:
                    logger.info(f"   ✅ Quality improved: {initial_score} → {new_score}/100")
                else:
                    logger.warning(f"   ⚠️ Quality unchanged: {initial_score} → {new_score}/100")

        # ============================================================
        # STEP 8: SET QUALITY STATUS ON OUTPUT (for downstream filtering)
        # ============================================================
        quality_metrics = context.parallel_results.get("content_quality", {})

        # If quality validation didn't run (no content), mark as failed
        if not quality_metrics:
            logger.warning("🚨 No quality metrics available - marking as failed")
            quality_score = 0
            quality_failed = True
        else:
            quality_failed = quality_metrics.get("quality_failed", False)
            quality_score = quality_metrics.get("score", 0)

        # Store quality status on structured_data for output
        if context.structured_data:
            context.structured_data.quality_score = quality_score
            context.structured_data.quality_failed = quality_failed

        if quality_failed:
            logger.warning(
                f"🚨 LOW QUALITY: score={quality_score}/100, "
                f"openers={quality_metrics.get('unique_opener_types', 0)}/4, "
                f"attribution={quality_metrics.get('attribution_ratio', 0)}, "
                f"blocks={quality_metrics.get('content_blocks_found', 0)}/4 "
                f"- Article will be stored with quality_failed=True"
            )
        else:
            logger.info(f"✅ Quality check passed: {quality_score}/100")

        return context
    async def _gemini_full_review(self, context: ExecutionContext) -> ExecutionContext:
        """
        MANDATORY Gemini review with full quality checklist.
        
        Gemini reviews ALL content fields and fixes any issues it finds,
        even if our detection logic missed them.
        """
        from pydantic import BaseModel, Field
        from typing import List
        import json
        
        # Define response schema
        class ContentFix(BaseModel):
            issue_type: str = Field(description="Type of issue fixed (e.g., 'em_dash', 'robotic_phrase', 'structural')")
            field: str = Field(description="Which field was fixed")
            description: str = Field(description="Brief description of what was fixed")
        
        class ReviewResponse(BaseModel):
            fixed_content: str = Field(description="The complete fixed content")
            issues_fixed: int = Field(description="Number of issues fixed")
            fixes: List[ContentFix] = Field(default_factory=list, description="Detailed list of all fixes applied")
            em_dashes_fixed: int = Field(default=0, description="Number of em dashes (—) removed")
            en_dashes_fixed: int = Field(default=0, description="Number of en dashes (–) removed")
            lists_added: int = Field(default=0, description="Number of lists added (if any)")
            citations_added: int = Field(default=0, description="Number of citations added (if any)")
        
        # CRITICAL: Add markdown prevention instruction at the very top
        markdown_prevention = """
🚨 CRITICAL: OUTPUT FORMATTING REQUIREMENTS 🚨

**FORBIDDEN - NEVER USE THESE:**
- **bold text** (markdown format) ❌
- *italic text* (markdown format) ❌
- # Heading (markdown format) ❌
- [link text](url) (markdown format) ❌

**REQUIRED - ALWAYS USE THESE:**
- <strong>bold text</strong> (HTML format) ✅
- <em>italic text</em> (HTML format) ✅
- <h1>Heading</h1> (HTML format) ✅
- <a href="url">link text</a> (HTML format) ✅

NEVER output markdown formatting. ALWAYS output HTML formatting.
        """
        
        # Full quality checklist - AI-only approach (no regex)
        CHECKLIST = markdown_prevention + """
# Quality Review Checklist

You are an expert quality editor. Your job is to find and fix ALL issues using AI intelligence.
Be SURGICAL - only change what's broken, preserve everything else.

## Structural Issues (CRITICAL)

- **Truncated list items**: Items ending mid-word ("secur", "autom", "manag") - complete or remove
- **Fragment lists**: Single-item lists that are clearly part of a sentence - merge into paragraph
- **Duplicate summary lists**: Paragraph followed by "<ul>" repeating same content - remove duplicate list
- **Orphaned HTML tags**: </p>, </li>, </ul> in wrong places - fix HTML structure
- **Malformed HTML nesting**: <ul> inside <p>, </p> inside <li> - fix nesting
- **Empty paragraphs**: <p>This </p>, <p>. Also,</p> - remove or complete
- **Broken sentences**: "</p><p><strong>How can</strong> you..." - merge into single paragraph
- **Orphaned <strong> tags**: "<p><strong>If you</strong></p> want..." → "<p><strong>If you</strong> want...</p>"
- **Unencoded HTML entities**: & characters in text content must be encoded as &amp; (e.g., "Bain & Company" → "Bain &amp; Company")
  - Only encode & that's not already part of an HTML entity (preserve &amp;, &lt;, &gt;, etc.)
  - Only encode in text content, not in HTML tag attributes

## Capitalization Issues

- **Brand names**: "iBM" → "IBM", "nIST" → "NIST", "mCKinsey" → "McKinsey"
- **Lowercase after period**: "sentence. the next" → "sentence. The next"
- **All-caps words**: "THE BEST" → "the best"

## AI Marker Issues (CRITICAL - ZERO TOLERANCE)

- **Em dashes (—)**: MUST replace with " - " (space-hyphen-space) or comma - NEVER leave em dashes
  - **CRITICAL:** Search EVERY paragraph for the em dash character (—). It can appear anywhere:
    - Between words: "development—the" → "development - the" or "development, the"
    - After phrases: "stages—the left" → "stages - the left" or "stages, the left"
    - In quotes: "left"—side → "left" - side
    - After punctuation: "security—and" → "security - and" or "security, and"
    - Before numbers: "version—2025" → "version - 2025" or "version 2025"
    - In compound phrases: "zero-trust—based" → "zero-trust - based" or "zero-trust-based"
    - After HTML tags: "</p>—<p>" → "</p> - <p>" or "</p>, <p>"
    - In citations: "According to IBM—the report" → "According to IBM - the report"
    - At sentence start: "—This approach" → "This approach" or "- This approach"
    - At sentence end: "the approach—" → "the approach" or "the approach."
    - Between sentences: "sentence.—Next" → "sentence. Next" or "sentence - Next"
  - **Examples to find and fix:**
    - "testing to the earliest stages of development—the 'left' side" → "testing to the earliest stages of development - the 'left' side"
    - "errors—such as leaving" → "errors - such as leaving" or "errors, such as leaving"
    - "approach—which ensures" → "approach - which ensures" or "approach, which ensures"
    - "security—and compliance" → "security - and compliance" or "security and compliance"
    - "version—2025" → "version - 2025" or "version 2025"
    - "zero-trust—based architecture" → "zero-trust - based architecture" or "zero-trust-based architecture"
    - "data—including sensitive" → "data - including sensitive" or "data, including sensitive"
    - "cloud—on-premises" → "cloud - on-premises" or "cloud to on-premises"
    - "stages of development—the 'left' side" → "stages of development - the 'left' side"
  - **How to fix:** Replace EVERY em dash (—) with either:
    - " - " (space-hyphen-space) for clarity
    - "," (comma) if it makes grammatical sense
    - " to " if it's a range (e.g., "2020—2025" → "2020 to 2025")
    - Remove if at sentence start/end
    - Rewrite the sentence if needed
  - **VALIDATION:** After fixing, search the entire content again for "—" - there should be ZERO em dashes remaining
  - **TRACKING:** Count how many em dashes you fixed and include in em_dashes_fixed field
- **En dashes (–)**: MUST replace with "-" (hyphen) or " to " - NEVER leave en dashes
  - Search for the en dash character (–) and replace with regular hyphen "-" or " to "
- **Academic citations [N]**: Remove all [1], [2], [1][2] markers from body (keep natural language citations only)
- **Robotic phrases**: "delve into", "crucial to note", "it's important to understand" → rewrite naturally
- **Formulaic transitions**: "Here's how/what" → rewrite naturally
- **Redundant lists**: "Key points include:" followed by redundant bullets → remove redundant list
- **HTML in titles**: Section titles with <p> tags → remove all HTML tags

## Humanization (Natural Language)

Replace AI-typical phrases with natural alternatives:
- "seamlessly" → "smoothly" or "easily"
- "leverage" → "use" or "apply"
- "utilize" → "use"
- "impactful" → "effective" or "meaningful"
- "robust" → "strong" or "reliable"
- "comprehensive" → "full" or "complete"
- "empower" → "help" or "enable"
- "streamline" → "simplify" or "speed up"
- "cutting-edge" → "modern" or "new"
- "furthermore" → ". Also," or remove
- "moreover" → ". Plus," or remove
- "it's important to note that" → remove or rewrite
- "in conclusion" → remove
- "to summarize" → remove

Use contractions naturally: "it is" → "it's", "you are" → "you're", "do not" → "don't"

## Content Quality Issues

- **Incomplete sentences**: Ending abruptly without punctuation - complete or remove
- **Double prefixes**: "What is Why is X" → "Why is X"
- **Repeated content**: Redundant content in same section - remove duplicates
- **Broken grammar**: "You can to mitigate" → "To mitigate" or "You can mitigate"
- **Missing verbs/subjects**: Incomplete sentences - complete
- **Orphaned conjunctions**: ". Also, the" → ". The"

## Link Issues

- **Broken links**: Causing sentence fragmentation - fix
- **Wrong link text**: Domain name instead of title - fix
- **Split sentences**: External links splitting sentences - fix

## AEO Optimization (CRITICAL FOR SCORE 95+)

- **Citation distribution**: Ensure 40%+ paragraphs have natural language citations
  - Add: "According to [Source]...", "[Source] reports...", "Research by [Source]..."
  - Target: 12-15 citations across the article
  - **Citation validation**: Verify that sources mentioned in text (IBM, Gartner, NIST, etc.) match sources in the Sources field
  - If a source is cited but not in Sources field, note it (but don't modify Sources field - that's handled elsewhere)
- **Conversational phrases**: Ensure 8+ instances
  - "you can", "you'll", "here's", "let's", "this is", "when you", "if you"
  - Add naturally if missing (don't force)
- **Question patterns**: Ensure 5+ question patterns
  - "what is", "how does", "why does", "when should", "where can", "how can", "what are"
  - Add rhetorical questions naturally if missing
- **Direct language**: Use "is", "are", "does" not "might be", "could be"
  - Replace vague language with direct statements
- **Lists**: If content is long (500+ words) and has no lists, consider adding 1-2 bullet or numbered lists for readability
  - Lists help break up long paragraphs and improve readability
  - Only add lists if they improve the content (don't force)
  - Track if you added any lists in lists_added field

## Your Task

1. Read the content carefully
2. Find ALL issues matching the checklist above
3. **CRITICAL:** Search for em dashes (—) and en dashes (–) FIRST - scan every character, they can be hidden in long sentences
4. ALSO find any OTHER issues (typos, grammar, awkward phrasing)
5. Fix each issue surgically - complete broken sentences, remove duplicates, fix grammar
6. HUMANIZE language - replace AI-typical phrases with natural alternatives
7. ENHANCE AEO components - add citations, conversational phrases, question patterns where missing
8. **VALIDATION:** Before returning, verify:
   - ZERO em dashes (—) remain in the content
   - ZERO en dashes (–) remain in the content
   - All robotic phrases replaced
   - All structural issues fixed
9. Return the complete fixed content

**Be thorough. Production quality means ZERO defects AND AEO score 95+.**
"""
        
        data = context.structured_data
        if not data:
            return context
        
        article_dict = data.dict() if hasattr(data, 'dict') else dict(data)
        total_fixes = 0
        
        # Content fields to review
        content_fields = [
            'section_01_content', 'section_02_content', 'section_03_content',
            'section_04_content', 'section_05_content', 'section_06_content',
            'section_07_content', 'section_08_content', 'section_09_content',
            'Intro', 'Direct_Answer',
        ]
        
        # Required fields: If empty, that's a quality issue (should be flagged)
        required_fields = {
            'Intro', 'Direct_Answer',
            'section_01_content', 'section_02_content', 'section_03_content',
            'section_04_content', 'section_05_content', 'section_06_content',
        }
        
        # Optional fields: Can legitimately be empty (articles might only have 6 sections)
        optional_fields = {
            'section_07_content', 'section_08_content', 'section_09_content',
        }
        
        # Initialize Gemini client
        from ..models.gemini_client import GeminiClient
        gemini_client = GeminiClient()
        
        # PARALLELIZE: Create tasks for all fields to review concurrently
        async def review_field(field: str) -> Tuple[str, int, str, int, int, int, int]:
            """Review a single field and return (field_name, issues_fixed, fixed_content, em_dashes_fixed, en_dashes_fixed, lists_added, citations_added)."""
            content = article_dict.get(field)
            
            # Handle empty/invalid content
            if not content or not isinstance(content, str):
                # Empty required field - flag as quality issue but can't fix it here
                if field in required_fields:
                    logger.debug(f"   ⚠️ {field}: Required field is empty (quality issue - Stage 2 should populate)")
                # Empty optional field - OK to skip
                return (field, 0, content or "", 0, 0, 0, 0)
            
            # Skip optional fields if very short (they can legitimately be empty/short)
            if field in optional_fields and len(content) < 100:
                return (field, 0, content or "", 0, 0, 0, 0)
            
            # Required fields: Always review, even if short (to detect quality issues)
            # Note: Stage 3 can't populate empty fields (that's Stage 2's job),
            # but we should still review short content to detect quality issues
            if field in required_fields and len(content) < 100:
                logger.debug(f"   ⚠️ {field}: Required field is very short ({len(content)} chars) - may be incomplete")
                # Still review it - Gemini can flag it as incomplete
            
            prompt = f"""{CHECKLIST}

FIELD: {field}

CONTENT TO REVIEW:
{content}

Return JSON with:
- fixed_content: The complete fixed content
- issues_fixed: Total number of issues fixed
- fixes[]: Array of ContentFix objects describing each fix
- em_dashes_fixed: Count of em dashes (—) removed
- en_dashes_fixed: Count of en dashes (–) removed
- lists_added: Count of lists added (if any)
- citations_added: Count of citations added (if any)

If no issues, return original content unchanged with issues_fixed=0 and all counts at 0.
"""
            
            try:
                response = await gemini_client.generate_content(
                    prompt=prompt,
                    enable_tools=False,
                    response_schema=ReviewResponse.model_json_schema()
                )
                
                if response and response.strip():
                    # Parse response
                    json_str = response.strip()
                    if json_str.startswith('```'):
                        json_str = json_str.split('\n', 1)[1] if '\n' in json_str else json_str[3:]
                    if json_str.endswith('```'):
                        json_str = json_str[:-3]
                    
                    try:
                        result = json.loads(json_str)
                        issues_fixed = result.get('issues_fixed', 0)
                        fixed_content = result.get('fixed_content', content)
                        em_dashes_fixed = result.get('em_dashes_fixed', 0)
                        en_dashes_fixed = result.get('en_dashes_fixed', 0)
                        lists_added = result.get('lists_added', 0)
                        citations_added = result.get('citations_added', 0)
                        fixes_list = result.get('fixes', [])
                        
                        # Log detailed fixes if any
                        if fixes_list:
                            for fix in fixes_list[:3]:  # Log first 3 fixes
                                fix_type = fix.get('issue_type', 'unknown')
                                fix_desc = fix.get('description', '')
                                logger.debug(f"      Fix: {fix_type} - {fix_desc}")
                        
                        if em_dashes_fixed > 0:
                            logger.debug(f"      Removed {em_dashes_fixed} em dash(es)")
                        if en_dashes_fixed > 0:
                            logger.debug(f"      Removed {en_dashes_fixed} en dash(es)")
                        if lists_added > 0:
                            logger.debug(f"      Added {lists_added} list(s)")
                        if citations_added > 0:
                            logger.debug(f"      Added {citations_added} citation(s)")
                        
                        return (field, issues_fixed, fixed_content, em_dashes_fixed, en_dashes_fixed, lists_added, citations_added)
                    except json.JSONDecodeError:
                        logger.debug(f"   ⚠️ {field}: Could not parse Gemini response")
                        return (field, 0, content, 0, 0, 0, 0)
                else:
                    # Empty or None response
                    logger.debug(f"   ⚠️ {field}: Empty response from Gemini")
                    return (field, 0, content, 0, 0, 0, 0)
                        
            except Exception as e:
                logger.debug(f"   ⚠️ {field}: Review failed - {e}")
                return (field, 0, content, 0, 0, 0, 0)
            
            # Fallback (should never reach here, but ensure we always return 7 values)
            return (field, 0, content, 0, 0, 0, 0)
        
        # Execute all reviews in parallel (with rate limiting via semaphore)
        # Limit concurrent calls to avoid API rate limits (max 15 concurrent - increased for performance)
        semaphore = asyncio.Semaphore(15)
        
        async def review_field_with_limit(field: str):
            async with semaphore:
                return await review_field(field)
        
        logger.info(f"   🔄 Reviewing {len(content_fields)} fields in parallel (max 15 concurrent)...")
        tasks = [review_field_with_limit(field) for field in content_fields]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and track metrics
        total_em_dashes_fixed = 0
        total_en_dashes_fixed = 0
        total_lists_added = 0
        total_citations_added = 0
        
        for result in results:
            if isinstance(result, Exception):
                logger.debug(f"   ⚠️ Field review exception: {result}")
                continue
            
            # Defensive check: ensure result is a tuple with 7 values
            if not isinstance(result, tuple) or len(result) != 7:
                logger.warning(f"   ⚠️ Unexpected result format: {type(result)}, length: {len(result) if isinstance(result, tuple) else 'N/A'}")
                logger.warning(f"      Result: {str(result)[:200]}")
                # Skip this result
                continue
            
            field, issues_fixed, fixed_content, em_dashes_fixed, en_dashes_fixed, lists_added, citations_added = result
            if issues_fixed > 0:
                article_dict[field] = fixed_content
                total_fixes += issues_fixed
                total_em_dashes_fixed += em_dashes_fixed
                total_en_dashes_fixed += en_dashes_fixed
                total_lists_added += lists_added
                total_citations_added += citations_added
                
                fix_summary = []
                if em_dashes_fixed > 0:
                    fix_summary.append(f"{em_dashes_fixed} em dash(es)")
                if en_dashes_fixed > 0:
                    fix_summary.append(f"{en_dashes_fixed} en dash(es)")
                if lists_added > 0:
                    fix_summary.append(f"{lists_added} list(s)")
                if citations_added > 0:
                    fix_summary.append(f"{citations_added} citation(s)")
                
                summary_text = f"{issues_fixed} issues fixed"
                if fix_summary:
                    summary_text += f" ({', '.join(fix_summary)})"
                
                logger.info(f"   ✅ {field}: {summary_text}")
            else:
                # No issues fixed, but review completed
                pass
                # Continue with other fields
        
        # POST-REVIEW VALIDATION: Check for remaining em/en dashes
        em_dash = "—"
        en_dash = "–"
        remaining_em_dashes = {}
        remaining_en_dashes = {}
        
        for field in content_fields:
            content = article_dict.get(field, "")
            if content:
                em_count = content.count(em_dash)
                en_count = content.count(en_dash)
                if em_count > 0:
                    remaining_em_dashes[field] = em_count
                if en_count > 0:
                    remaining_en_dashes[field] = en_count
        
        # PARALLEL second pass for remaining em/en dashes
        if remaining_em_dashes or remaining_en_dashes:
            logger.warning(f"   ⚠️ Dashes still present - running parallel second pass")

            async def fix_dash(field: str, count: int, dash_type: str, dash_char: str) -> Tuple[str, int, str, bool]:
                """Fix dashes in a single field. Returns (field, count_fixed, content, success)."""
                content = article_dict.get(field, "")
                if not content:
                    return (field, 0, "", False)

                if dash_type == "em":
                    prompt = f"""CRITICAL: This content still contains {count} em dash(es) (—).
You MUST find and replace EVERY em dash with " - " (space-hyphen-space) or a comma.

CONTENT:
{content}

Find ALL em dashes (—) and replace them. Return the complete fixed content with ZERO em dashes remaining."""
                else:
                    prompt = f"""CRITICAL: This content still contains {count} en dash(es) (–).
You MUST find and replace EVERY en dash with "-" (hyphen) or " to " (space-to-space).

CONTENT:
{content}

Find ALL en dashes (–) and replace them. Return the complete fixed content with ZERO en dashes remaining."""

                try:
                    response = await gemini_client.generate_content(
                        prompt=prompt,
                        enable_tools=False,
                        response_schema=None
                    )
                    if response and dash_char not in response:
                        response_stripped = response.strip()
                        if len(response_stripped) > len(content) * 0.5:
                            return (field, count, response_stripped, True)
                except Exception as e:
                    logger.debug(f"   ⚠️ {field}: Second pass {dash_type} dash fix failed - {e}")
                return (field, 0, content, False)

            # Build all tasks for parallel execution
            dash_tasks = []
            for field, count in remaining_em_dashes.items():
                dash_tasks.append(fix_dash(field, count, "em", em_dash))
            for field, count in remaining_en_dashes.items():
                dash_tasks.append(fix_dash(field, count, "en", en_dash))

            # Execute all dash fixes in parallel
            if dash_tasks:
                logger.info(f"   🔄 Fixing {len(dash_tasks)} fields with remaining dashes in parallel...")
                dash_results = await asyncio.gather(*dash_tasks, return_exceptions=True)

                for result in dash_results:
                    if isinstance(result, Exception):
                        continue
                    field, count_fixed, fixed_content, success = result
                    if success and count_fixed > 0:
                        article_dict[field] = fixed_content
                        total_fixes += count_fixed
                        if field in remaining_em_dashes:
                            total_em_dashes_fixed += count_fixed
                            logger.info(f"   ✅ {field}: Fixed {count_fixed} remaining em dash(es) in second pass")
                        else:
                            total_en_dashes_fixed += count_fixed
                            logger.info(f"   ✅ {field}: Fixed {count_fixed} remaining en dash(es) in second pass")
        
        if total_fixes > 0:
            summary_parts = [f"{total_fixes} total issues fixed"]
            if total_em_dashes_fixed > 0:
                summary_parts.append(f"{total_em_dashes_fixed} em dash(es)")
            if total_en_dashes_fixed > 0:
                summary_parts.append(f"{total_en_dashes_fixed} en dash(es)")
            if total_lists_added > 0:
                summary_parts.append(f"{total_lists_added} list(s) added")
            if total_citations_added > 0:
                summary_parts.append(f"{total_citations_added} citation(s) added")
            
            logger.info(f"   📝 Gemini fixed {' | '.join(summary_parts)} across all fields")
            
            # Encode HTML entities in HTML content fields
            article_dict = _encode_html_entities_in_content(article_dict)
            
            context.structured_data = ArticleOutput(**article_dict)
        else:
            logger.info("   ℹ️ Gemini review: no additional issues found")
        
        return context
    
    async def _optimize_aeo_components(self, context: ExecutionContext) -> ExecutionContext:
        """
        Optimize AEO components to boost score to 95+.
        
        Checks and fixes:
        - Citation distribution (40%+ paragraphs have citations)
        - Conversational phrases (8+ instances)
        - Question patterns (5+ instances)
        - Direct Answer quality (length, keyword, citation)
        """
        from ..models.gemini_client import GeminiClient
        import json
        
        data = context.structured_data
        if not data:
            return context
        
        article_dict = data.dict() if hasattr(data, 'dict') else dict(data)
        
        # Use Gemini to analyze AEO components (AI-only, no regex)
        gemini_client = GeminiClient()
        
        # Get Direct Answer early (needed for all code paths)
        direct_answer = article_dict.get('Direct_Answer', '')
        primary_keyword = context.job_config.get("primary_keyword", "") if context.job_config else ""
        
        # Build content summary for analysis
        all_content = article_dict.get('Intro', '') + ' ' + direct_answer
        for i in range(1, 10):
            all_content += ' ' + article_dict.get(f'section_{i:02d}_content', '')
        
        # Ask Gemini to count AEO components
        analysis_prompt = f"""Analyze this article content and count AEO (Agentic Search Optimization) components.

CONTENT:
{all_content[:5000]}  # Limit to avoid token limits

Count and return JSON with:
- citation_count: Number of natural language citations (patterns: "According to [Source]", "[Source] reports", "Research by [Source]")
- phrase_count: Number of conversational phrases ("you can", "you'll", "here's", "let's", "this is", "when you", "if you")
- question_count: Number of question patterns ("what is", "how does", "why does", "when should", "where can", "how can", "what are")
- direct_answer_words: Word count of Direct Answer (strip HTML first)
- has_citation_in_da: Boolean - does Direct Answer contain a citation?
- has_keyword_in_da: Boolean - does Direct Answer contain the primary keyword "{primary_keyword}"?

Return ONLY valid JSON, no explanations.
"""
        
        try:
            from pydantic import BaseModel, Field
            class AEOAnalysis(BaseModel):
                citation_count: int = Field(description="Number of natural language citations")
                phrase_count: int = Field(description="Number of conversational phrases")
                question_count: int = Field(description="Number of question patterns")
                direct_answer_words: int = Field(description="Word count of Direct Answer")
                has_citation_in_da: bool = Field(description="Does Direct Answer contain citation?")
                has_keyword_in_da: bool = Field(description="Does Direct Answer contain primary keyword?")
            
            analysis_response = await gemini_client.generate_content(
                prompt=analysis_prompt,
                enable_tools=False,
                response_schema=AEOAnalysis.model_json_schema()
            )
            
            if analysis_response:
                analysis_json = json.loads(analysis_response.strip().replace('```json', '').replace('```', '').strip())
                citation_count = analysis_json.get('citation_count', 0)
                phrase_count = analysis_json.get('phrase_count', 0)
                question_count = analysis_json.get('question_count', 0)
                direct_answer_words = analysis_json.get('direct_answer_words', 0)
                has_citation_in_da = analysis_json.get('has_citation_in_da', False)
                has_keyword_in_da = analysis_json.get('has_keyword_in_da', False)
            else:
                # Fallback: use simple string counting (minimal, acceptable for detection)
                citation_count = all_content.lower().count('according to') + all_content.lower().count('reports') + all_content.lower().count('research by')
                phrase_count = sum(1 for phrase in ['you can', "you'll", "here's", "let's", "this is", "when you", "if you"] if phrase in all_content.lower())
                question_count = sum(1 for pattern in ['what is', 'how does', 'why does', 'when should', 'where can', 'how can', 'what are'] if pattern in all_content.lower())
                # Simple word count (approximate, but acceptable)
                direct_answer_words = len(direct_answer.split()) if direct_answer else 0
                has_citation_in_da = 'according to' in direct_answer.lower() or 'reports' in direct_answer.lower()
                has_keyword_in_da = primary_keyword.lower() in direct_answer.lower() if primary_keyword and direct_answer else False
        except Exception as e:
            logger.warning(f"   ⚠️ AEO analysis failed, using fallback: {e}")
            # Fallback: minimal string operations (acceptable for detection)
            citation_count = all_content.lower().count('according to') + all_content.lower().count('reports')
            phrase_count = sum(1 for phrase in ['you can', "you'll", "here's"] if phrase in all_content.lower())
            question_count = sum(1 for pattern in ['what is', 'how does'] if pattern in all_content.lower())
            direct_answer_words = len(direct_answer.split()) if direct_answer else 0
            has_citation_in_da = 'according to' in direct_answer.lower() if direct_answer else False
            has_keyword_in_da = primary_keyword.lower() in direct_answer.lower() if primary_keyword and direct_answer else False
        
        # AEO scorer gives points for: 30-80 words (2.5-5.0 pts), <30 or >80 words (0 pts)
        # So we should optimize if outside 30-80 range OR missing citation/keyword
        # Accept 30-80 words (gets at least 2.5 points), optimize otherwise
        needs_da_length_fix = direct_answer_words < 30 or direct_answer_words > 80
        
        logger.info(f"📊 AEO Status: Citations={citation_count} (target: 12+), Phrases={phrase_count} (target: 8+), Questions={question_count} (target: 5+)")
        logger.info(f"   Direct Answer: {direct_answer_words} words (target: 40-60), Citation={'✅' if has_citation_in_da else '❌'}, Keyword={'✅' if has_keyword_in_da else '❌'}")
        
        # Always optimize if below targets (more aggressive) - INCLUDES KEYWORD CHECK
        needs_optimization = (
            citation_count < 15 or  # Target: 12-15, optimize if <15
            phrase_count < 10 or    # Target: 8+, optimize if <10 (buffer)
            question_count < 6 or   # Target: 5+, optimize if <6 (buffer)
            (direct_answer_words < 30 or direct_answer_words > 70 or not has_citation_in_da or not has_keyword_in_da)  # ADD: keyword check
        )
        
        if not needs_optimization:
            logger.info("✅ AEO components already optimal")
            return context
        
        # Use Gemini to optimize AEO components
        gemini_client = GeminiClient()
        
        aeo_prompt = f"""You are an AEO (Agentic Search Optimization) expert. Optimize this article to score 95+/100.

CURRENT STATUS:
- Citations: {citation_count} (target: 12-15 natural language citations)
- Conversational phrases: {phrase_count} (target: 8+)
- Question patterns: {question_count} (target: 5+)
- Direct Answer: {direct_answer_words} words (target: 40-60), Citation: {'Yes' if has_citation_in_da else 'No'}

OPTIMIZATION TASKS:
1. Add natural language citations to paragraphs missing them (target: 40%+ paragraphs have citations)
   - Use patterns: "According to [Source]...", "[Source] reports...", "Research by [Source]..."
   - Add 2-5 more citations if below 12 total
2. Add conversational phrases naturally (target: 8+ total)
   - Use: "you can", "you'll", "here's", "let's", "this is", "when you", "if you"
   - Add 2-4 more phrases if below 8 total
3. Add question patterns naturally (target: 5+ total) - CRITICAL FOR AEO SCORE
   - Use these EXACT patterns: "What is", "How does", "Why does", "When should", "Where can", "How can", "What are"
   - Add AT LEAST 5 question patterns total across all sections
   - Examples: "What is API security testing?", "How does automation help?", "Why should you implement this?"
   - Add 3-5 more question patterns if currently below 5 total
4. Enhance Direct Answer if needed:
   - Ensure 40-60 words
   - Include primary keyword
   - Include natural language citation

Return the optimized article content. Be surgical - only add what's missing, don't rewrite everything.
"""
        
        # Optimize sections that need improvement (AGGRESSIVE - optimize more sections)
        optimized_count = 0
        sections_to_optimize = []
        
        # Identify sections that need optimization (more aggressive criteria)
        for i in range(1, 10):
            field = f'section_{i:02d}_content'
            content = article_dict.get(field, '')
            if not content or len(content) < 200:
                continue
            
            # Simple string counting for section analysis (minimal, acceptable for detection)
            section_citations = content.lower().count('according to') + content.lower().count('reports')
            section_phrases = sum(1 for phrase in ['you can', "you'll", "here's", "let's", "this is", "when you", "if you"] if phrase in content.lower())
            section_questions = sum(1 for pattern in ['what is', 'how does', 'why does', 'when should', 'where can', 'how can', 'what are'] if pattern in content.lower())
            
            # More aggressive: optimize if section is missing ANY component or below average
            needs_opt = (
                section_citations < 2 or  # Less than 2 citations (was: == 0)
                (section_phrases < 2 and phrase_count < 10) or  # Less than 2 phrases and overall below target
                (section_questions == 0 and question_count < 6)  # No questions and overall below target
            )
            
            if needs_opt:
                sections_to_optimize.append((i, field, content, section_citations, section_phrases, section_questions))
        
        # Optimize up to 7 sections (increased from 5) - prioritize those with 0 citations/phrases
        sections_to_optimize.sort(key=lambda x: (x[3] == 0, x[4] == 0, x[5] == 0), reverse=True)  # Prioritize sections missing components
        sections_to_optimize = sections_to_optimize[:7]  # Increased from 5 to 7 sections
        
        # PARALLELIZE: Optimize all sections concurrently
        async def optimize_section(section_data: tuple) -> Tuple[str, str, bool]:
            """Optimize a single section and return (field_name, optimized_content, success)."""
            i, field, content, section_citations, section_phrases, section_questions = section_data
            
            section_prompt = f"""{aeo_prompt}

SECTION TO OPTIMIZE:
{content}

Return ONLY the optimized section content with added citations, conversational phrases, and question patterns.
Be GENEROUS - add 2-3 citations, 2-3 conversational phrases, and 1-2 question patterns naturally.
"""
            try:
                response = await gemini_client.generate_content(
                    prompt=section_prompt,
                    response_schema=None  # Free-form response
                )
                
                if response and len(response) > 100:
                    return (field, response.strip(), True)
                else:
                    return (field, content, False)
            except Exception as e:
                logger.debug(f"   ⚠️ {field}: AEO optimization failed - {e}")
                return (field, content, False)
        
        # Execute all optimizations in parallel (with rate limiting via semaphore)
        # Limit concurrent calls to avoid API rate limits (max 10 concurrent - increased for performance)
        if sections_to_optimize:
            semaphore = asyncio.Semaphore(10)
            
            async def optimize_section_with_limit(section_data: tuple):
                async with semaphore:
                    return await optimize_section(section_data)
            
            logger.info(f"   🔄 Optimizing {len(sections_to_optimize)} sections in parallel (max 10 concurrent)...")
            tasks = [optimize_section_with_limit(section_data) for section_data in sections_to_optimize]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    logger.debug(f"   ⚠️ Section optimization exception: {result}")
                    continue
                
                field, optimized_content, success = result
                if success:
                    article_dict[field] = optimized_content
                    optimized_count += 1
                    # Get original stats for logging
                    original_section = next((s for s in sections_to_optimize if s[1] == field), None)
                    if original_section:
                        _, _, _, section_citations, section_phrases, _ = original_section
                        logger.info(f"   ✅ Optimized {field} (had {section_citations} citations, {section_phrases} phrases)")
        
        # Verify question patterns were added (post-optimization check)
        all_content_after = article_dict.get('Intro', '') + ' ' + article_dict.get('Direct_Answer', '')
        for i in range(1, 10):
            all_content_after += ' ' + article_dict.get(f'section_{i:02d}_content', '')
        question_patterns = ['what is', 'how does', 'why does', 'when should', 'where can', 'how can', 'what are']
        question_count_after = sum(1 for pattern in question_patterns if pattern in all_content_after.lower())
        
        if question_count_after < 5:
            logger.warning(f"⚠️ Only {question_count_after} question patterns found after optimization (target: 5+)")
            # Note: Could add fallback regex injection here if needed
        
        # Optimize Direct Answer if needed (CRITICAL - worth 25 points!)
        # Check: citation, keyword, OR truly unreasonable length
        # Don't optimize just for length if it's reasonable (20-150 words is fine)
        needs_da_optimization = direct_answer and (needs_da_length_fix or not has_citation_in_da or not has_keyword_in_da)
        
        if needs_da_optimization:
            logger.info(f"   🔧 Direct Answer needs optimization: {direct_answer_words} words, Citation={'✅' if has_citation_in_da else '❌'}, Keyword={'✅' if has_keyword_in_da else '❌'}")
            try:
                da_prompt = f"""You are optimizing a Direct Answer for AEO (Agentic Search Optimization). This is CRITICAL - worth 25 points.

CURRENT Direct Answer ({direct_answer_words} words):
{direct_answer}

REQUIREMENTS (ALL MUST BE MET):
1. Word count: MUST be 30-80 words (ideal: 40-60 words) - currently {direct_answer_words} words {'(TOO LONG - shorten to 30-80 words)' if direct_answer_words > 80 else '(TOO SHORT - expand to 30-80 words)' if direct_answer_words < 30 else '(OK length, but ensure 30-80 range)'}
2. Primary keyword: MUST include "{primary_keyword}" naturally in the text
3. Citation: MUST include ONE natural language citation like "According to [Source]..." or "[Source] reports..."

OUTPUT FORMAT:
- Return ONLY the optimized Direct Answer text
- NO explanations, NO markdown, NO HTML tags
- Just the plain text Direct Answer (30-80 words)
- Start directly with the answer content

Example format (40-60 words):
"According to Gartner research, {primary_keyword} involves [brief explanation]. This approach helps organizations [benefit]. Key practices include [practice 1], [practice 2], and [practice 3]."

Now optimize the Direct Answer above to meet ALL requirements. Ensure it's 30-80 words.
"""
                logger.debug(f"   📤 Sending Direct Answer optimization request to Gemini...")
                response = await gemini_client.generate_content(
                    prompt=da_prompt,
                    response_schema=None
                )
                
                if response:
                    optimized_da = response.strip()
                    # Remove markdown code blocks (minimal string operation, acceptable)
                    if optimized_da.startswith('```'):
                        optimized_da = optimized_da.split('\n', 1)[1] if '\n' in optimized_da else optimized_da[3:]
                    if optimized_da.endswith('```'):
                        optimized_da = optimized_da[:-3]
                    optimized_da = optimized_da.replace('```', '').strip()
                    # Simple word count (approximate, but acceptable)
                    optimized_da_words = len(optimized_da.split())
                    
                    # AEO scorer gives points for: 30-80 words (2.5-5.0 pts), <30 or >80 words (0 pts)
                    # Accept 30-80 words (gets at least 2.5 points)
                    if 30 <= optimized_da_words <= 80:
                        article_dict['Direct_Answer'] = optimized_da
                        optimized_count += 1
                        # Calculate expected AEO points for logging
                        if 40 <= optimized_da_words <= 60:
                            score_note = "5.0 pts"
                        else:
                            score_note = "2.5 pts"
                        logger.info(f"   ✅ Optimized Direct_Answer ({direct_answer_words} → {optimized_da_words} words, {score_note})")
                    elif optimized_da_words > 80:
                        # Gemini returned >80 words - try intelligent truncation (better than 0 points)
                        words = optimized_da.split()
                        # Try to find sentence boundary near 60-70 words
                        truncated = ' '.join(words[:70])
                        last_period = truncated.rfind('.')
                        last_exclamation = truncated.rfind('!')
                        last_question = truncated.rfind('?')
                        last_sentence_end = max(last_period, last_exclamation, last_question)
                        
                        if last_sentence_end > len(' '.join(words[:50])):  # At least 50 words
                            truncated = truncated[:last_sentence_end + 1].strip()
                        else:
                            truncated = ' '.join(words[:60])  # Fallback: first 60 words
                        
                        truncated_words = len(truncated.split())
                        if 30 <= truncated_words <= 80:
                            article_dict['Direct_Answer'] = truncated
                            optimized_count += 1
                            logger.info(f"   ✅ Truncated Direct_Answer to {truncated_words} words (was {optimized_da_words}, gets 2.5 pts)")
                        else:
                            logger.warning(f"   ⚠️ Direct_Answer: Could not truncate effectively ({truncated_words} words) - keeping original")
                    else:
                        logger.warning(f"   ⚠️ Direct_Answer: Too short ({optimized_da_words} words, min: 30) - keeping original")
                else:
                    logger.warning(f"   ⚠️ Direct_Answer: Gemini returned empty response")
            except Exception as e:
                logger.error(f"   ❌ Direct_Answer: AEO optimization failed - {e}", exc_info=True)
        else:
            logger.debug(f"   ℹ️ Direct Answer already optimal: {direct_answer_words} words, Citation={'✅' if has_citation_in_da else '❌'}, Keyword={'✅' if has_keyword_in_da else '❌'}")
        
        if optimized_count > 0:
            logger.info(f"🚀 AEO optimization: Enhanced {optimized_count} fields")
            
            # Encode HTML entities in HTML content fields
            article_dict = _encode_html_entities_in_content(article_dict)
            
            context.structured_data = ArticleOutput(**article_dict)
            # Set flag to skip Stage 10's AEO enforcement (avoids conflicts)
            context.stage_3_optimized = True
            logger.info("   🏷️ Flagged: Stage 10 will skip AEO enforcement (Stage 3 already optimized)")
        else:
            logger.info("ℹ️ AEO optimization: No fields needed enhancement")
        
        return context
    
    # REMOVED: All detection methods (_detect_quality_issues, _check_*, _issues_to_rewrites)
    # These used regex and are no longer needed - Gemini handles all detection and fixes directly
        """
        Generate semantic variations for a keyword.
        
        This is a simple heuristic - could be improved with NLP.
        """
        # Extract the main concept (last 1-2 words usually)
        words = primary_keyword.split()
        
        variations = [
            "these tools",
            "these solutions",
            "these platforms",
            "the technology",
            "this approach"
        ]
        
        # Try to generate more specific variations
        if "AI" in primary_keyword or "artificial intelligence" in primary_keyword.lower():
            variations.extend([
                "AI assistants",
                "AI systems",
                "intelligent tools",
                "automated solutions"
            ])
        
        if "code" in primary_keyword.lower():
            variations.extend([
                "code generators",
                "development tools",
                "coding assistants"
            ])
        
        if "tool" in primary_keyword.lower():
            variations.extend([
                "software",
                "applications",
                "utilities"
            ])
        
        # Return unique variations (max 5)
        return list(dict.fromkeys(variations))[:5]
    
    async def _enhance_domain_only_urls(self, context: ExecutionContext) -> ExecutionContext:
        """
        Enhance domain-only URLs in Sources field using grounding URLs from Stage 2.
        
        Converts URLs like 'gartner.com' to full URLs like 'gartner.com/articles/specific-report'
        by matching domains to grounding URLs from Google Search.
        
        Args:
            context: ExecutionContext with structured_data and grounding_urls
            
        Returns:
            Updated context with enhanced Sources field
        """
        # Check if Sources field exists
        if not context.structured_data or not hasattr(context.structured_data, 'Sources'):
            logger.debug("No Sources field available for enhancement")
            return context
        
        sources_text = context.structured_data.Sources or ""
        if not sources_text.strip():
            logger.debug("Sources field is empty")
            return context
        
        # Check if grounding URLs are available
        grounding_urls = getattr(context, 'grounding_urls', [])
        if not grounding_urls:
            logger.debug("No grounding URLs available for enhancement")
            return context
        
        logger.info(f"📎 Enhancing domain-only URLs using {len(grounding_urls)} grounding URLs (AI-only parsing)")
        
        # Build domain -> full URL map from grounding URLs
        domain_to_urls = {}
        for grounding in grounding_urls:
            url = grounding.get('url', '')
            title = grounding.get('title', '')
            if not url or not title:
                continue
            # Title IS the domain (e.g., "gartner.com", "ibm.com")
            domain = title.lower().replace('www.', '').strip()
            if domain and domain not in domain_to_urls:
                domain_to_urls[domain] = url
        
        logger.debug(f"   Domain map: {list(domain_to_urls.keys())[:5]}...")
        
        # Use AI to parse citations and identify domain-only URLs
        if not hasattr(self, 'gemini_client') or not self.gemini_client:
            from pipeline.models.gemini_client import GeminiClient
            self.gemini_client = GeminiClient()
        
        prompt = f"""Parse citations from the Sources field and identify domain-only URLs that need enhancement.

Sources field format: [number]: URL – Title
Example: [1]: https://gartner.com – Gartner Report 2024

CRITICAL REQUIREMENTS:
1. Parse ALL citations from the text
2. For each citation, identify if the URL is domain-only (path has <= 1 part)
   - Domain-only examples: https://gartner.com, https://ibm.com/reports
   - Full URL examples: https://gartner.com/articles/specific-report, https://ibm.com/reports/data-breach-2024
3. For domain-only URLs, extract the domain (without www.)
4. Return structured JSON with citations and enhancement suggestions

Available grounding URLs (domain -> full URL):
{chr(10).join([f"- {domain}: {url}" for domain, url in list(domain_to_urls.items())[:10]])}

Sources field text:
{sources_text}

Return a JSON object with:
- citations: array of parsed citations
- enhancements: array of enhancements to apply (citation_number, original_url, enhanced_url)
"""
        
        try:
            from google.genai import types
            
            response_schema = types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "citations": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "number": types.Schema(type=types.Type.INTEGER),
                                "url": types.Schema(type=types.Type.STRING),
                                "title": types.Schema(type=types.Type.STRING)
                            }
                        )
                    ),
                    "enhancements": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "citation_number": types.Schema(type=types.Type.INTEGER),
                                "original_url": types.Schema(type=types.Type.STRING),
                                "enhanced_url": types.Schema(type=types.Type.STRING)
                            }
                        )
                    )
                },
                required=["citations", "enhancements"]
            )
            
            response = await self.gemini_client.generate_content(
                prompt=prompt,
                response_schema=response_schema,
                enable_tools=False
            )
            
            if not response:
                logger.warning("⚠️ AI parsing returned no response for domain-only enhancement")
                return context
            
            import json
            parsed = json.loads(response)
            enhancements = parsed.get('enhancements', [])
            
            if not enhancements:
                logger.debug("   No domain-only URLs found or no matching grounding URLs")
                return context
            
            # Use AI to apply all enhancements at once (no regex, no string manipulation)
            enhancement_list = []
            for enhancement in enhancements:
                citation_num = enhancement.get('citation_number')
                original_url = enhancement.get('original_url', '').strip()
                enhanced_url = enhancement.get('enhanced_url', '').strip()
                
                if citation_num and original_url and enhanced_url:
                    enhancement_list.append({
                        'citation_number': citation_num,
                        'original_url': original_url,
                        'enhanced_url': enhanced_url
                    })
            
            if not enhancement_list:
                logger.debug("   No valid enhancements to apply")
                return context
            
            # Ask AI to apply all enhancements and return updated Sources field
            apply_prompt = f"""Update the Sources field by replacing domain-only URLs with full URLs.

Apply these enhancements:
{chr(10).join([f"- Citation [{e['citation_number']}]: Replace {e['original_url']} with {e['enhanced_url']}" for e in enhancement_list])}

Current Sources field:
{sources_text}

CRITICAL REQUIREMENTS:
1. Apply ALL enhancements listed above
2. Keep the exact same format: [number]: URL – Title
3. Keep all other citations unchanged
4. Return ONLY the updated Sources field text (no explanations, no markdown)

Return the complete updated Sources field with all enhancements applied.
"""
            
            try:
                apply_response = await self.gemini_client.generate_content(
                    prompt=apply_prompt,
                    enable_tools=False
                )
                
                if apply_response and apply_response.strip():
                    enhanced_sources = apply_response.strip()
                    enhanced_count = len(enhancement_list)
                    logger.info(f"✅ Enhanced {enhanced_count} domain-only URLs in Sources field (AI-only)")
                    
                    # Update structured_data Sources field
                    article_dict = context.structured_data.model_dump()
                    article_dict['Sources'] = enhanced_sources
                    context.structured_data = ArticleOutput(**article_dict)
                else:
                    logger.warning("⚠️ AI enhancement application returned no response")
            except Exception as e:
                logger.error(f"❌ AI enhancement application failed: {e}")
                logger.warning("   Continuing without enhancement")
                
        except Exception as e:
            logger.error(f"❌ AI domain-only enhancement failed: {e}")
            logger.warning("   Continuing without enhancement")
        
        return context

    def _validate_faq_paa(self, context: ExecutionContext) -> ExecutionContext:
        """
        Validate and clean FAQ/PAA items (previously Stage 8).
        
        Args:
            context: ExecutionContext with structured_data
            
        Returns:
            Updated context with validated FAQ/PAA in parallel_results
        """
        if not context.structured_data:
            from ..models.faq_paa import FAQList, PAAList
            context.parallel_results["faq_items"] = FAQList()
            context.parallel_results["paa_items"] = PAAList()
            return context
        
        from ..models.faq_paa import FAQItem, FAQList, PAAItem, PAAList
        
        # Extract FAQ items
        faq_list = FAQList()
        faq_fields = [
            (1, getattr(context.structured_data, 'faq_01_question', '') or '', getattr(context.structured_data, 'faq_01_answer', '') or ''),
            (2, getattr(context.structured_data, 'faq_02_question', '') or '', getattr(context.structured_data, 'faq_02_answer', '') or ''),
            (3, getattr(context.structured_data, 'faq_03_question', '') or '', getattr(context.structured_data, 'faq_03_answer', '') or ''),
            (4, getattr(context.structured_data, 'faq_04_question', '') or '', getattr(context.structured_data, 'faq_04_answer', '') or ''),
            (5, getattr(context.structured_data, 'faq_05_question', '') or '', getattr(context.structured_data, 'faq_05_answer', '') or ''),
            (6, getattr(context.structured_data, 'faq_06_question', '') or '', getattr(context.structured_data, 'faq_06_answer', '') or ''),
        ]
        
        for num, question, answer in faq_fields:
            if question and question.strip() and answer and answer.strip():
                faq_list.add_item(num, question.strip(), answer.strip())
        
        # Extract PAA items
        paa_list = PAAList()
        paa_fields = [
            (1, getattr(context.structured_data, 'paa_01_question', '') or '', getattr(context.structured_data, 'paa_01_answer', '') or ''),
            (2, getattr(context.structured_data, 'paa_02_question', '') or '', getattr(context.structured_data, 'paa_02_answer', '') or ''),
            (3, getattr(context.structured_data, 'paa_03_question', '') or '', getattr(context.structured_data, 'paa_03_answer', '') or ''),
            (4, getattr(context.structured_data, 'paa_04_question', '') or '', getattr(context.structured_data, 'paa_04_answer', '') or ''),
        ]
        
        for num, question, answer in paa_fields:
            if question and question.strip() and answer and answer.strip():
                paa_list.add_item(num, question.strip(), answer.strip())
        
        logger.info(f"Extracted {faq_list.count()} FAQ items, {paa_list.count()} PAA items")
        
        # Validate and clean (remove duplicates, invalid items)
        seen_faq_questions = set()
        unique_faq_items = []
        for item in faq_list.items:
            q_lower = item.question.lower().strip()
            if q_lower not in seen_faq_questions and item.is_valid():
                unique_faq_items.append(item)
                seen_faq_questions.add(q_lower)
        
        seen_paa_questions = set()
        unique_paa_items = []
        for item in paa_list.items:
            q_lower = item.question.lower().strip()
            if q_lower not in seen_paa_questions and item.is_valid():
                unique_paa_items.append(item)
                seen_paa_questions.add(q_lower)
        
        # Create cleaned lists
        cleaned_faq = FAQList(items=unique_faq_items)
        cleaned_paa = PAAList(items=unique_paa_items)
        
        # Renumber
        cleaned_faq.renumber()
        cleaned_paa.renumber()
        
        logger.info(f"✅ Validated: {cleaned_faq.count_valid()} FAQ, {cleaned_paa.count_valid()} PAA")
        
        # Check minimum requirements
        if not cleaned_faq.is_minimum_met():
            logger.warning(f"⚠️  FAQ count below minimum: {cleaned_faq.count()} < {cleaned_faq.min_items}")
        if not cleaned_paa.is_minimum_met():
            logger.warning(f"⚠️  PAA count below minimum: {cleaned_paa.count()} < {cleaned_paa.min_items}")
        
        # Store in context
        context.parallel_results["faq_items"] = cleaned_faq
        context.parallel_results["paa_items"] = cleaned_paa
        context.parallel_results["faq_count"] = cleaned_faq.count()
        context.parallel_results["paa_count"] = cleaned_paa.count()

        return context

    async def _validate_content_quality(self, context: ExecutionContext) -> ExecutionContext:
        """
        Validate content quality for human-like writing patterns.

        Checks:
        1. Section opener variety (max 2 questions, varied types)
        2. Citation density (not over-attributed)
        3. Required content blocks (decision framework, scenario, mistake, hot take)

        This is a VALIDATION step - it logs warnings and stores quality metrics
        but doesn't block the pipeline. Quality issues are flagged for review.
        """
        import re

        if not context.structured_data:
            logger.warning("No structured_data for content quality validation")
            return context

        logger.info("📊 Validating content quality patterns...")

        # Collect all section content
        section_fields = [
            'section_01_content', 'section_02_content', 'section_03_content',
            'section_04_content', 'section_05_content', 'section_06_content',
            'section_07_content', 'section_08_content', 'section_09_content',
        ]

        sections = []
        for field in section_fields:
            content = getattr(context.structured_data, field, '') or ''
            if content.strip():
                sections.append(content)

        all_content = ' '.join(sections)

        # ============================================================
        # CHECK 1: Section Opener Variety
        # ============================================================
        question_openers = 0
        opener_types = []

        question_patterns = [
            r'^<p>\s*What\s+is',
            r'^<p>\s*Why\s+(do|does|is|are|should)',
            r'^<p>\s*How\s+(do|does|can|to)',
            r'^<p>\s*When\s+(should|do|does)',
            r'^<p>\s*Where\s+(do|does|can)',
            r'^<p>\s*Who\s+(should|can|does)',
        ]

        for section in sections:
            # Get first paragraph - extract full content including HTML tags, then strip them
            first_p_match = re.search(r'^<p>(.*?)</p>', section.strip(), re.DOTALL | re.IGNORECASE)
            if first_p_match:
                # Strip HTML tags to get plain text for analysis
                first_html = first_p_match.group(1).strip()
                first_text = re.sub(r'<[^>]+>', '', first_html).strip()[:100]

                # Check if it's a question opener (check raw text, not wrapped in <p>)
                is_question = any(re.match(pattern.replace('^<p>\\s*', '^\\s*'), first_text, re.IGNORECASE) for pattern in question_patterns)
                if is_question:
                    question_openers += 1
                    opener_types.append('QUESTION')
                elif re.match(r'^\d', first_text):
                    opener_types.append('STATISTIC')
                elif any(word in first_text.lower() for word in ['imagine', 'picture this', "let's say", 'consider a', 'here\'s exactly']):
                    opener_types.append('SCENARIO')
                elif any(word in first_text.lower() for word in ['honestly', 'unpopular', 'contrary', 'most people', 'the truth is', 'skip', 'overrated']):
                    opener_types.append('BOLD_CLAIM')
                else:
                    opener_types.append('STATEMENT')

        # Count unique opener types
        unique_openers = len(set(opener_types))

        # Log opener analysis
        logger.info(f"   Section openers: {opener_types}")
        logger.info(f"   Question openers: {question_openers} (max 2 recommended)")
        logger.info(f"   Unique opener types: {unique_openers} (aim for 3+)")

        if question_openers > 2:
            logger.warning(f"   ⚠️ Too many question openers: {question_openers} (robotic pattern)")

        if unique_openers < 3:
            logger.warning(f"   ⚠️ Low opener variety: only {unique_openers} types used")

        # ============================================================
        # CHECK 2: Citation Density (Over-Attribution)
        # ============================================================
        attribution_patterns = [
            r'according to\s+\w+',
            r'research\s+(by|from|shows|suggests)',
            r'study\s+(by|from|shows|finds)',
            r'experts?\s+(say|suggest|recommend|note)',
            r'analysts?\s+(say|suggest|predict|note)',
            r'reports?\s+(show|indicate|suggest)',
        ]

        attribution_count = 0
        for pattern in attribution_patterns:
            attribution_count += len(re.findall(pattern, all_content, re.IGNORECASE))

        # Count total paragraphs for ratio
        paragraph_count = len(re.findall(r'<p>', all_content))
        attribution_ratio = attribution_count / max(paragraph_count, 1)

        logger.info(f"   Attribution phrases: {attribution_count} in {paragraph_count} paragraphs")
        logger.info(f"   Attribution ratio: {attribution_ratio:.2f} (aim for <0.3)")

        if attribution_ratio > 0.4:
            logger.warning(f"   ⚠️ Over-attribution detected: {attribution_ratio:.2f} ratio")

        # ============================================================
        # CHECK 3: Required Content Blocks (simple presence indicators)
        # ============================================================
        # Simplified from complex regex to simple keyword presence checks.
        # Less strict, but more reliable and easier to maintain.
        content_lower = all_content.lower()

        # Decision framework: Presence of decision-making language
        decision_indicators = ["if you", "choose", "when to use", "go with", "pick"]
        has_decision_framework = sum(1 for ind in decision_indicators if ind in content_lower) >= 2

        # Scenario: Presence of immersive narrative language
        scenario_indicators = ["imagine", "picture", "step 1", "let's say", "here's what happens"]
        has_scenario = any(ind in content_lower for ind in scenario_indicators)

        # Mistake callout: Presence of warning/avoidance language
        mistake_indicators = ["mistake", "wrong", "avoid", "don't", "never do"]
        has_mistake = sum(1 for ind in mistake_indicators if ind in content_lower) >= 2

        # Hot take: Presence of opinionated language
        hot_take_indicators = ["honestly", "overrated", "truth is", "most people get", "unpopular"]
        has_hot_take = any(ind in content_lower for ind in hot_take_indicators)

        content_blocks_found = sum([has_decision_framework, has_scenario, has_mistake, has_hot_take])

        logger.info(f"   Required content blocks found: {content_blocks_found}/4")
        logger.info(f"      - Decision framework: {'✅' if has_decision_framework else '❌'}")
        logger.info(f"      - Concrete scenario: {'✅' if has_scenario else '❌'}")
        logger.info(f"      - Mistake callout: {'✅' if has_mistake else '❌'}")
        logger.info(f"      - Hot take/opinion: {'✅' if has_hot_take else '❌'}")

        if content_blocks_found < 3:
            logger.warning(f"   ⚠️ Missing content blocks: only {content_blocks_found}/4 found")

        # ============================================================
        # CHECK 4: Voice Persona Adherence (filler phrase check only)
        # ============================================================
        # Simplified: Just check for universally bad filler phrases.
        # The complex dont_list mapping was fragile and rarely matched.
        voice_violations = 0

        # Filler phrases that indicate robotic/AI-generated content
        filler_phrases = [
            "it's important to note",
            "it's worth mentioning",
            "in today's rapidly evolving",
            "in today's digital landscape",
            "needless to say",
            "as we all know",
            "at the end of the day",
            "it goes without saying",
            "moving forward",
            "in conclusion",
            "let's dive in",
            "without further ado",
        ]

        for filler in filler_phrases:
            if filler in content_lower:
                voice_violations += 1
                logger.debug(f"      Found filler phrase: '{filler}'")

        if voice_violations > 0:
            logger.warning(f"   ⚠️ Voice persona violations: {voice_violations} filler/dont patterns found")
        else:
            logger.info(f"   ✅ Voice persona: No filler phrases or dont_list violations detected")

        # ============================================================
        # CALCULATE QUALITY SCORE (simplified)
        # ============================================================
        quality_score = 0

        # Opener variety (max 30 points)
        # Question openers: 0-2 is good (15 pts), 3-4 is ok (8 pts), 5+ is bad (0 pts)
        if question_openers <= 2:
            quality_score += 15
        elif question_openers <= 4:
            quality_score += 8

        # Unique opener types: 3+ is good (15 pts), 2 is ok (10 pts), 1 is bad (5 pts)
        if unique_openers >= 3:
            quality_score += 15
        elif unique_openers >= 2:
            quality_score += 10
        else:
            quality_score += 5

        # Attribution (max 30 points) - simplified: just check ratio
        # <0.25 is good (30 pts), 0.25-0.40 is ok (20 pts), >0.40 is over-attributed (10 pts)
        if attribution_count == 0:
            quality_score += 10  # No citations - not ideal but not fatal
        elif attribution_ratio <= 0.25:
            quality_score += 30  # Good balance
        elif attribution_ratio <= 0.40:
            quality_score += 20  # Acceptable
        else:
            quality_score += 10  # Over-attributed

        # Content blocks (max 40 points) - 10 pts each
        quality_score += content_blocks_found * 10

        logger.info(f"📊 Content Quality Score: {quality_score}/100")

        # Determine quality status (three-tier system for nuanced handling)
        # 70+ = PASS (auto-approve), 60-69 = WARNING (needs human review), <60 = FAIL (reject)
        # Note: quality_failed articles are flagged but NOT blocked - downstream filters decide
        quality_failed = quality_score < 60  # Hard fail threshold
        quality_warning = quality_score < 70 and quality_score >= 60  # Soft warning zone

        if quality_failed:
            logger.warning(f"   ⚠️ LOW QUALITY SCORE: {quality_score}/100 - article flagged for review")
        elif quality_warning:
            logger.warning(f"   ⚠️ MODERATE QUALITY: {quality_score}/100 - some patterns need improvement")
        else:
            logger.info(f"   ✅ GOOD QUALITY: {quality_score}/100")

        # Store quality metrics in context (used by downstream systems)
        context.parallel_results["content_quality"] = {
            "score": quality_score,
            "quality_failed": quality_failed,  # Flag for filtering/rejection
            "quality_warning": quality_warning,  # Flag for review
            "question_openers": question_openers,
            "unique_opener_types": unique_openers,
            "opener_types": opener_types,
            "attribution_count": attribution_count,
            "attribution_ratio": round(attribution_ratio, 2),
            "has_decision_framework": has_decision_framework,
            "has_scenario": has_scenario,
            "has_mistake_callout": has_mistake,
            "has_hot_take": has_hot_take,
            "content_blocks_found": content_blocks_found,
            "voice_persona_violations": voice_violations,  # Count of filler phrase violations
        }

        # Log enforcement status
        if quality_failed:
            logger.warning("   🚨 QUALITY_FAILED=True - downstream systems should filter this article")

        return context

    async def _apply_quality_fixes(
        self,
        context: ExecutionContext,
        fix_instructions: list,
        quality_metrics: dict
    ) -> ExecutionContext:
        """
        Apply AI-driven fixes to content that failed quality validation.

        Instead of just logging warnings, this method calls Gemini to actually
        FIX the detected issues:
        - Rewrite question openers to be statements/scenarios
        - Reduce over-attribution phrases
        - Add missing content blocks (decision framework, scenario, etc.)

        Args:
            context: ExecutionContext with structured_data
            fix_instructions: List of specific fixes to apply
            quality_metrics: Dict with detected quality issues

        Returns:
            Updated context with fixed content
        """
        import json

        if not context.structured_data or not fix_instructions:
            return context

        logger.info(f"🔧 Quality Fix Loop: Applying {len(fix_instructions)} fixes...")

        # Collect all section content to fix
        section_fields = [
            'section_01_content', 'section_02_content', 'section_03_content',
            'section_04_content', 'section_05_content', 'section_06_content',
            'section_07_content', 'section_08_content', 'section_09_content',
        ]

        sections_content = {}
        for field in section_fields:
            content = getattr(context.structured_data, field, '') or ''
            if content.strip():
                sections_content[field] = content

        if not sections_content:
            logger.warning("   No section content to fix")
            return context

        # Get opener types for context
        opener_types = quality_metrics.get("opener_types", [])

        # Build the fix prompt
        fix_prompt = f"""You are a content quality editor. Your job is to FIX specific quality issues in the article sections below.

## FIXES REQUIRED (Do ALL of these):

{chr(10).join(f"- {instruction}" for instruction in fix_instructions)}

## CURRENT SECTION OPENER ANALYSIS:

{chr(10).join(f"Section {i+1}: {opener_types[i] if i < len(opener_types) else 'N/A'}" for i in range(len(sections_content)))}

## RULES:

1. **PRESERVE all existing content** - only modify what's specifically mentioned in the fixes
2. **Keep HTML formatting** - use <p>, <strong>, <ul>, <li> etc., NOT markdown
3. **Be surgical** - don't rewrite entire sections, just fix the specific issues
4. **For question openers**: Replace "What is X?" style openers with VARIED alternatives:
   - Use a MIX of opener types (don't make them all the same):
   - STATEMENT: "X is the foundation of Y." or "The key to X lies in Y."
   - STATISTIC: "87% of enterprises now use X." or "In 2024, X grew by 40%."
   - SCENARIO: "Imagine your team discovers X at 2am." or "Picture this: Y happens."
   - BOLD_CLAIM: "Honestly, X is overrated." or "Most developers get X wrong."
   - IMPORTANT: Use at least 3 DIFFERENT opener types across all sections for variety
5. **For over-attribution**: Reduce HEDGING phrases but KEEP citations:
   - KEEP statistics and sources: "IBM reports breach costs average $4.45M" → keep as is
   - REMOVE hedging language: "According to experts, X is important" → "X is important"
   - State facts confidently: "Research shows MFA is effective" → "MFA blocks 99.9% of attacks"
   - IMPORTANT: Do NOT remove all citations - reduce attribution ratio but preserve authority
6. **For missing content blocks**: Add naturally within relevant sections:
   - Decision framework: "Choose X if you need Y. Go with Z if you prioritize W."
   - Scenario: "Imagine you're processing payments at 2am when..."
   - Mistake: "Here's where most teams go wrong: they assume..."
   - Hot take: "Honestly, most enterprises over-complicate this."

## SECTIONS TO FIX:

{chr(10).join(f"### {field}:{chr(10)}{content}{chr(10)}" for field, content in sections_content.items())}

## OUTPUT FORMAT:

Return JSON with:
- fixed_sections: Dict mapping field names to their COMPLETE fixed content
- fixes_applied: List of strings describing what was fixed
- success: true if fixes were applied

Only include sections that were actually modified. If a section doesn't need changes, don't include it.
"""

        try:
            # Initialize Gemini client
            from ..models.gemini_client import GeminiClient
            gemini_client = GeminiClient()

            # Note: We don't use response_schema here because Gemini doesn't support
            # additionalProperties which Pydantic includes for dict fields.
            # The prompt already requests JSON format, so we parse manually.
            response = await gemini_client.generate_content(
                prompt=fix_prompt,
                enable_tools=False
            )

            if response and response.strip():
                # Parse response
                json_str = response.strip()
                if json_str.startswith('```'):
                    json_str = json_str.split('\n', 1)[1] if '\n' in json_str else json_str[3:]
                if json_str.endswith('```'):
                    json_str = json_str[:-3]

                try:
                    result = json.loads(json_str)
                    fixed_sections = result.get('fixed_sections', {})
                    fixes_applied = result.get('fixes_applied', [])

                    if fixed_sections:
                        # Apply fixes to structured_data
                        for field, fixed_content in fixed_sections.items():
                            if field in section_fields and fixed_content:
                                setattr(context.structured_data, field, fixed_content)
                                logger.info(f"   ✅ Fixed: {field}")

                        # Log what was fixed
                        for fix in fixes_applied[:5]:  # Log first 5
                            logger.info(f"      - {fix}")

                        logger.info(f"   🔧 Applied {len(fixed_sections)} section fixes")
                    else:
                        logger.warning("   ⚠️ No sections were fixed by Gemini")

                except json.JSONDecodeError as e:
                    logger.warning(f"   ⚠️ Could not parse quality fix response: {e}")
            else:
                logger.warning("   ⚠️ Empty response from Gemini quality fix")

        except Exception as e:
            logger.warning(f"   ⚠️ Quality fix failed: {e}")

        return context

