"""
RegenerationEngine - Orchestrates content regeneration workflow

Handles automatic content regeneration when similarity detection indicates
content cannibalization. Integrates with existing WorkflowEngine and 
similarity checking systems.

Key Features:
- Prompt variation strategies for different regeneration attempts
- Integration with HybridSimilarityChecker 
- Complete regeneration loop with similarity re-checking
- Production-ready error handling and logging
- Metrics tracking for regeneration effectiveness

Usage:
    engine = RegenerationEngine(workflow_engine, similarity_manager)
    
    # Single article with regeneration
    result = await engine.generate_with_regeneration(job_config)
    
    # Batch generation with regeneration
    results = await engine.generate_batch_with_regeneration(job_configs)
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, NamedTuple
from dataclasses import dataclass
from enum import Enum

from .execution_context import ExecutionContext
from .workflow_engine import WorkflowEngine
from ..blog_generation.stage_07_similarity_check import (
    HybridBatchSimilarityManager, 
    RegenerationResult
)
from ..utils.hybrid_similarity_checker import HybridSimilarityChecker
from ..utils.gemini_embeddings import GeminiEmbeddingClient

logger = logging.getLogger(__name__)


class RegenerationStrategy(Enum):
    """Different approaches for content regeneration."""
    ANGLE_VARIATION = "angle_variation"      # Change perspective/angle
    EXAMPLE_VARIATION = "example_variation"  # Use different examples
    STYLE_VARIATION = "style_variation"      # Modify writing style
    DEPTH_VARIATION = "depth_variation"      # Change technical depth
    AUDIENCE_VARIATION = "audience_variation" # Adjust target audience


@dataclass
class RegenerationAttempt:
    """Details of a regeneration attempt."""
    attempt_number: int
    strategy: RegenerationStrategy
    similarity_score: float
    success: bool
    execution_time: float
    error_message: Optional[str] = None


@dataclass 
class RegenerationReport:
    """Complete report of regeneration workflow."""
    job_id: str
    original_similarity: Optional[float]
    final_similarity: float
    attempts_made: List[RegenerationAttempt]
    final_result: RegenerationResult
    total_time: float
    success: bool
    final_context: Optional[ExecutionContext] = None


class PromptVariationStrategy:
    """
    Generates prompt variations for regeneration attempts.
    
    Each strategy modifies the original prompt to encourage different content
    while maintaining the same core topic and keyword focus.
    """
    
    VARIATION_TEMPLATES = {
        RegenerationStrategy.ANGLE_VARIATION: [
            "Focus on practical implementation rather than theory",
            "Emphasize benefits and ROI rather than features", 
            "Take a beginner-friendly approach rather than expert-level",
            "Highlight common challenges and solutions",
            "Focus on industry trends and future outlook"
        ],
        
        RegenerationStrategy.EXAMPLE_VARIATION: [
            "Use different industry examples (healthcare, finance, retail)",
            "Include case studies from different company sizes",
            "Reference different tools and platforms", 
            "Showcase different geographic markets",
            "Feature different use case scenarios"
        ],
        
        RegenerationStrategy.STYLE_VARIATION: [
            "Write in a more conversational, approachable tone",
            "Use a data-driven, analytical writing style",
            "Adopt a step-by-step tutorial format",
            "Structure as a comparison/evaluation guide",
            "Present as a strategic business overview"
        ],
        
        RegenerationStrategy.DEPTH_VARIATION: [
            "Provide more technical details and specifications",
            "Focus on high-level concepts and strategies", 
            "Include more actionable implementation steps",
            "Emphasize conceptual understanding over tactics",
            "Balance theory with practical applications"
        ],
        
        RegenerationStrategy.AUDIENCE_VARIATION: [
            "Write for technical implementers and developers",
            "Target business decision-makers and executives",
            "Address small business owners and entrepreneurs", 
            "Focus on marketing professionals and agencies",
            "Tailor for industry specialists and consultants"
        ]
    }
    
    @classmethod
    def get_variation_instruction(cls, strategy: RegenerationStrategy, attempt: int) -> str:
        """Get specific variation instruction for regeneration attempt."""
        templates = cls.VARIATION_TEMPLATES[strategy]
        # Cycle through templates for multiple attempts
        template_index = (attempt - 1) % len(templates)
        return templates[template_index]
    
    @classmethod
    def apply_variation(cls, original_config: Dict[str, Any], strategy: RegenerationStrategy, attempt: int) -> Dict[str, Any]:
        """Apply prompt variation to job config."""
        config = original_config.copy()
        
        # Get variation instruction
        variation = cls.get_variation_instruction(strategy, attempt)
        
        # Add variation to prompt context
        if 'prompt_context' not in config:
            config['prompt_context'] = {}
            
        config['prompt_context']['regeneration_instruction'] = variation
        config['prompt_context']['regeneration_attempt'] = attempt
        config['prompt_context']['regeneration_strategy'] = strategy.value
        
        # Add attempt suffix to job_id to track regeneration attempts
        if 'job_id' in config:
            base_job_id = config['job_id'].split('_regen')[0]  # Remove any existing regen suffix
            config['job_id'] = f"{base_job_id}_regen_{attempt}_{strategy.value}"
        
        logger.info(f"Applied {strategy.value} variation for attempt {attempt}: {variation}")
        return config


class RegenerationEngine:
    """
    Core engine for content regeneration workflow.
    
    Orchestrates the complete regeneration process:
    1. Generate initial content
    2. Check similarity 
    3. If too similar, apply prompt variations and regenerate
    4. Repeat until acceptable similarity or max attempts reached
    5. Return final result with detailed metrics
    """
    
    def __init__(
        self, 
        workflow_engine: WorkflowEngine,
        embedding_client: GeminiEmbeddingClient,
        max_attempts: int = 3,
        similarity_threshold: float = 70.0
    ):
        """
        Initialize regeneration engine.
        
        Args:
            workflow_engine: WorkflowEngine for running pipeline stages
            embedding_client: GeminiEmbeddingClient for similarity checking
            max_attempts: Maximum regeneration attempts per article
            similarity_threshold: Similarity percentage that triggers regeneration
        """
        self.workflow_engine = workflow_engine
        self.embedding_client = embedding_client
        self.max_attempts = max_attempts
        self.similarity_threshold = similarity_threshold
        
        # Initialize similarity checking components
        self.similarity_checker = HybridSimilarityChecker(
            embedding_client=embedding_client,
            enable_regeneration=True,
            similarity_threshold=similarity_threshold
        )
        self.similarity_manager = HybridBatchSimilarityManager(
            self.similarity_checker, 
            max_regeneration_attempts=max_attempts
        )
        
        # Strategy rotation for multiple attempts
        self.regeneration_strategies = list(RegenerationStrategy)
        
        logger.info(f"RegenerationEngine initialized (max_attempts={max_attempts}, threshold={similarity_threshold}%)")
    
    async def generate_with_regeneration(
        self, 
        job_config: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> RegenerationReport:
        """
        Generate content with automatic regeneration on high similarity.
        
        Args:
            job_config: Job configuration for content generation
            progress_callback: Optional progress reporting callback
            
        Returns:
            RegenerationReport with complete workflow results
        """
        start_time = time.time()
        job_id = job_config.get('job_id', f"regen_{int(time.time())}")
        attempts = []
        
        logger.info(f"Starting regeneration workflow for job: {job_id}")
        
        try:
            # Attempt 1: Generate initial content
            current_config = job_config.copy()
            current_config['job_id'] = job_id
            
            for attempt in range(1, self.max_attempts + 1):
                attempt_start = time.time()
                logger.info(f"Regeneration attempt {attempt}/{self.max_attempts} for {job_id}")
                
                try:
                    # Apply prompt variation (skip for first attempt)
                    if attempt > 1:
                        strategy = self.regeneration_strategies[(attempt - 2) % len(self.regeneration_strategies)]
                        current_config = PromptVariationStrategy.apply_variation(
                            job_config, strategy, attempt
                        )
                    else:
                        strategy = None
                    
                    # Generate content using workflow engine
                    context = await self.workflow_engine.execute(
                        job_id=current_config['job_id'],
                        job_config=current_config,
                        progress_callback=progress_callback
                    )
                    
                    # Check similarity against batch
                    similarity_result = await self.similarity_manager.check_article_with_regeneration(
                        context, attempt
                    )
                    
                    attempt_time = time.time() - attempt_start
                    similarity_score = similarity_result.similarity_report.similarity_score
                    
                    # Record attempt
                    attempt_record = RegenerationAttempt(
                        attempt_number=attempt,
                        strategy=strategy,
                        similarity_score=similarity_score,
                        success=similarity_result.approved,
                        execution_time=attempt_time
                    )
                    attempts.append(attempt_record)
                    
                    logger.info(f"Attempt {attempt}: {similarity_score:.1f}% similarity, approved={similarity_result.approved}")
                    
                    # Check if we should continue or stop
                    if similarity_result.approved:
                        # Success! Content is acceptable
                        total_time = time.time() - start_time
                        
                        return RegenerationReport(
                            job_id=job_id,
                            original_similarity=attempts[0].similarity_score if attempts else None,
                            final_similarity=similarity_score,
                            attempts_made=attempts,
                            final_result=similarity_result,
                            total_time=total_time,
                            success=True,
                            final_context=context
                        )
                    
                    elif not similarity_result.regeneration_triggered:
                        # Rejected - no more regeneration attempts
                        break
                    
                    # Continue to next attempt with variation
                    
                except Exception as e:
                    attempt_time = time.time() - attempt_start
                    logger.error(f"Attempt {attempt} failed: {e}")
                    
                    attempt_record = RegenerationAttempt(
                        attempt_number=attempt,
                        strategy=strategy if attempt > 1 else None,
                        similarity_score=0.0,
                        success=False,
                        execution_time=attempt_time,
                        error_message=str(e)
                    )
                    attempts.append(attempt_record)
            
            # All attempts exhausted or failed
            total_time = time.time() - start_time
            final_result = attempts[-1] if attempts else None
            
            return RegenerationReport(
                job_id=job_id,
                original_similarity=attempts[0].similarity_score if attempts else None,
                final_similarity=final_result.similarity_score if final_result else 0.0,
                attempts_made=attempts,
                final_result=None,
                total_time=total_time,
                success=False
            )
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Regeneration workflow failed for {job_id}: {e}")
            
            return RegenerationReport(
                job_id=job_id,
                original_similarity=None,
                final_similarity=0.0,
                attempts_made=attempts,
                final_result=None,
                total_time=total_time,
                success=False
            )
    
    async def generate_batch_with_regeneration(
        self, 
        job_configs: List[Dict[str, Any]],
        parallel: bool = False,
        progress_callback: Optional[callable] = None
    ) -> List[RegenerationReport]:
        """
        Generate multiple articles with regeneration workflow.
        
        Args:
            job_configs: List of job configurations
            parallel: Whether to run jobs in parallel (False for sequential to avoid similarity conflicts)
            progress_callback: Optional progress reporting callback
            
        Returns:
            List of RegenerationReports for each job
        """
        logger.info(f"Starting batch regeneration for {len(job_configs)} jobs (parallel={parallel})")
        
        if parallel:
            # Run all jobs in parallel (may have similarity conflicts)
            tasks = [
                self.generate_with_regeneration(config, progress_callback)
                for config in job_configs
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Run jobs sequentially to avoid similarity conflicts
            results = []
            for i, config in enumerate(job_configs):
                logger.info(f"Processing job {i+1}/{len(job_configs)}")
                result = await self.generate_with_regeneration(config, progress_callback)
                results.append(result)
                
                # Brief pause between jobs to avoid rate limiting
                if i < len(job_configs) - 1:
                    await asyncio.sleep(1)
            
            return results
    
    def get_batch_summary(self) -> Dict[str, Any]:
        """Get summary of current batch processing state."""
        return self.similarity_manager.get_batch_summary()
    
    def clear_batch(self):
        """Clear batch memory for new session."""
        self.similarity_manager.clear_batch()
        logger.info("Regeneration engine batch cleared")


# Convenience functions for easy usage

async def create_regeneration_engine(
    workflow_engine: WorkflowEngine,
    gemini_api_key: str,
    max_attempts: int = 3
) -> RegenerationEngine:
    """Create configured regeneration engine."""
    embedding_client = GeminiEmbeddingClient(api_key=gemini_api_key)
    return RegenerationEngine(
        workflow_engine=workflow_engine,
        embedding_client=embedding_client,
        max_attempts=max_attempts
    )


async def generate_article_with_regeneration(
    workflow_engine: WorkflowEngine,
    job_config: Dict[str, Any],
    gemini_api_key: str,
    max_attempts: int = 3
) -> RegenerationReport:
    """Convenience function for single article generation with regeneration."""
    engine = await create_regeneration_engine(workflow_engine, gemini_api_key, max_attempts)
    return await engine.generate_with_regeneration(job_config)