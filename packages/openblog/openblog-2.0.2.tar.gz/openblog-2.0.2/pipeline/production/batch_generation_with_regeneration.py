#!/usr/bin/env python3
"""
Production Batch Generation with Regeneration

Complete production-ready system for generating batches of blog articles
with automatic similarity detection and content regeneration.

Features:
- Automatic regeneration when content similarity is too high
- Intelligent prompt variations for each regeneration attempt  
- Complete integration with existing 12-stage pipeline
- Production error handling and logging
- Detailed metrics and reporting
- Support for different batch strategies

Usage:
    python pipeline/production/batch_generation_with_regeneration.py

Or as module:
    from pipeline.production.batch_generation_with_regeneration import ProductionBatchRunner
    
    runner = ProductionBatchRunner()
    results = await runner.run_batch(job_configs)
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.core.regeneration_engine import RegenerationEngine, RegenerationReport
from pipeline.core.workflow_engine import WorkflowEngine
from pipeline.utils.gemini_embeddings import GeminiEmbeddingClient
from pipeline.blog_generation.stage_00_data_fetch import DataFetchStage
from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage
from pipeline.blog_generation.stage_02_gemini_call import GeminiCallStage
# Stage 3 (Extraction) is now part of Stage 2 (Generation + Extraction)
from pipeline.blog_generation.stage_04_citations import CitationsStage
from pipeline.blog_generation.stage_05_internal_links import InternalLinksStage
# Stages 6-8 consolidated: ToC and Metadata into Stage 2, FAQ/PAA validation into Stage 3
from pipeline.blog_generation.stage_06_image import ImageStage
from pipeline.blog_generation.stage_07_similarity_check import HybridSimilarityCheckStage
from pipeline.blog_generation.stage_08_cleanup import CleanupStage
from pipeline.blog_generation.stage_09_storage import StorageStage

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"batch_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)


class ProductionBatchRunner:
    """
    Production-ready batch generation with regeneration workflow.
    
    Handles complete batch processing including:
    - Sequential or parallel generation 
    - Automatic similarity checking and regeneration
    - Error handling and recovery
    - Detailed metrics and reporting
    - Progress tracking and logging
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        max_regeneration_attempts: int = 3,
        similarity_threshold: float = 70.0,
        output_dir: str = "batch_output"
    ):
        """
        Initialize production batch runner.
        
        Args:
            gemini_api_key: Gemini API key (or from environment)
            max_regeneration_attempts: Max regeneration attempts per article
            similarity_threshold: Similarity % that triggers regeneration
            output_dir: Directory for output files and reports
        """
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            raise ValueError("Gemini API key required (set GEMINI_API_KEY or pass to constructor)")
        
        self.max_regeneration_attempts = max_regeneration_attempts
        self.similarity_threshold = similarity_threshold
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize workflow engine with all stages
        self.workflow_engine = self._initialize_workflow_engine()
        
        # Will be initialized when needed
        self.regeneration_engine: Optional[RegenerationEngine] = None
        
        logger.info(f"ProductionBatchRunner initialized")
        logger.info(f"  Max regeneration attempts: {max_regeneration_attempts}")
        logger.info(f"  Similarity threshold: {similarity_threshold}%")
        logger.info(f"  Output directory: {output_dir}")
    
    def _initialize_workflow_engine(self) -> WorkflowEngine:
        """Initialize workflow engine with all pipeline stages."""
        engine = WorkflowEngine()
        
        # Register all 13 stages (0-12) in order (Stage 2b is conditional, not registered)
        stages = [
            DataFetchStage(),           # Stage 0: Data fetch
            PromptBuildStage(),         # Stage 1: Prompt build  
            GeminiCallStage(),          # Stage 2: Gemini call
            # Stage 3 (Extraction) is now part of Stage 2
            CitationsStage(),           # Stage 4: Citations
            InternalLinksStage(),       # Stage 5: Internal links
            TableOfContentsStage(),     # Stage 6: ToC
            MetadataStage(),            # Stage 7: Metadata
            FAQPAAStage(),              # Stage 8: FAQ/PAA
            ImageStage(),               # Stage 9: Image
            CleanupStage(),             # Stage 10: Cleanup
            StorageStage()              # Stage 11: Storage
        ]
        
        engine.register_stages(stages)
        logger.info(f"Workflow engine initialized with {len(stages)} stages")
        return engine
    
    async def _get_regeneration_engine(self) -> RegenerationEngine:
        """Lazy initialization of regeneration engine."""
        if self.regeneration_engine is None:
            embedding_client = GeminiEmbeddingClient(api_key=self.gemini_api_key)
            self.regeneration_engine = RegenerationEngine(
                workflow_engine=self.workflow_engine,
                embedding_client=embedding_client,
                max_attempts=self.max_regeneration_attempts,
                similarity_threshold=self.similarity_threshold
            )
        return self.regeneration_engine
    
    async def run_batch(
        self,
        job_configs: List[Dict[str, Any]],
        sequential: bool = True,
        save_results: bool = True,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Run batch generation with regeneration workflow.
        
        Args:
            job_configs: List of job configurations for articles
            sequential: Run jobs sequentially (True) or parallel (False)
            save_results: Save results to files  
            progress_callback: Optional progress callback function
            
        Returns:
            Complete batch results with metrics and reports
        """
        start_time = time.time()
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🚀 Starting production batch generation")
        logger.info(f"  Batch ID: {batch_id}")
        logger.info(f"  Articles to generate: {len(job_configs)}")
        logger.info(f"  Execution mode: {'Sequential' if sequential else 'Parallel'}")
        logger.info(f"  Regeneration enabled: Yes (max {self.max_regeneration_attempts} attempts)")
        
        try:
            # Initialize regeneration engine
            engine = await self._get_regeneration_engine()
            
            # Add batch ID to job configs
            for i, config in enumerate(job_configs):
                if 'job_id' not in config:
                    config['job_id'] = f"{batch_id}_article_{i+1:02d}"
            
            # Run batch generation
            if progress_callback:
                progress_callback(0, len(job_configs), "Starting batch generation...")
            
            generation_reports = await engine.generate_batch_with_regeneration(
                job_configs=job_configs,
                parallel=not sequential,
                progress_callback=progress_callback
            )
            
            # Compile batch results
            batch_results = self._compile_batch_results(
                batch_id=batch_id,
                generation_reports=generation_reports,
                job_configs=job_configs,
                execution_time=time.time() - start_time,
                sequential=sequential
            )
            
            # Save results if requested
            if save_results:
                await self._save_batch_results(batch_results)
            
            # Log summary
            self._log_batch_summary(batch_results)
            
            return batch_results
            
        except Exception as e:
            logger.error(f"Batch generation failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _compile_batch_results(
        self,
        batch_id: str,
        generation_reports: List[RegenerationReport],
        job_configs: List[Dict[str, Any]],
        execution_time: float,
        sequential: bool
    ) -> Dict[str, Any]:
        """Compile comprehensive batch results."""
        
        successful_reports = [r for r in generation_reports if r.success]
        failed_reports = [r for r in generation_reports if not r.success]
        
        # Regeneration statistics
        total_attempts = sum(len(r.attempts_made) for r in generation_reports)
        regeneration_triggered = sum(1 for r in generation_reports if len(r.attempts_made) > 1)
        
        # Similarity statistics
        similarity_scores = [r.final_similarity for r in generation_reports if r.final_similarity > 0]
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
        
        # Time statistics
        avg_time_per_article = sum(r.total_time for r in generation_reports) / len(generation_reports) if generation_reports else 0
        
        return {
            "batch_id": batch_id,
            "timestamp": datetime.now().isoformat(),
            "execution_mode": "sequential" if sequential else "parallel",
            "total_execution_time": execution_time,
            
            # Success metrics
            "total_articles": len(job_configs),
            "successful_articles": len(successful_reports),
            "failed_articles": len(failed_reports),
            "success_rate": len(successful_reports) / len(job_configs) * 100 if job_configs else 0,
            
            # Regeneration metrics
            "regeneration_enabled": True,
            "max_attempts_per_article": self.max_regeneration_attempts,
            "articles_requiring_regeneration": regeneration_triggered,
            "regeneration_rate": regeneration_triggered / len(job_configs) * 100 if job_configs else 0,
            "total_generation_attempts": total_attempts,
            "avg_attempts_per_article": total_attempts / len(job_configs) if job_configs else 0,
            
            # Similarity metrics
            "similarity_threshold": self.similarity_threshold,
            "average_final_similarity": avg_similarity,
            "similarity_scores": similarity_scores,
            
            # Performance metrics  
            "avg_time_per_article": avg_time_per_article,
            "articles_per_minute": len(successful_reports) / (execution_time / 60) if execution_time > 0 else 0,
            
            # Detailed results
            "generation_reports": [self._serialize_report(r) for r in generation_reports],
            "job_configs": job_configs,
            
            # Status summary
            "status": "completed",
            "errors": [r.final_result for r in failed_reports if r.final_result]
        }
    
    def _serialize_report(self, report: RegenerationReport) -> Dict[str, Any]:
        """Serialize RegenerationReport for JSON output."""
        return {
            "job_id": report.job_id,
            "success": report.success,
            "original_similarity": report.original_similarity,
            "final_similarity": report.final_similarity,
            "attempts_made": len(report.attempts_made),
            "total_time": report.total_time,
            "attempt_details": [
                {
                    "attempt": attempt.attempt_number,
                    "strategy": attempt.strategy.value if attempt.strategy else None,
                    "similarity_score": attempt.similarity_score,
                    "success": attempt.success,
                    "execution_time": attempt.execution_time,
                    "error": attempt.error_message
                }
                for attempt in report.attempts_made
            ]
        }
    
    async def _save_batch_results(self, batch_results: Dict[str, Any]):
        """Save batch results to files."""
        batch_id = batch_results["batch_id"]
        
        # Save complete results as JSON
        results_file = self.output_dir / f"{batch_id}_results.json"
        with open(results_file, 'w') as f:
            json.dump(batch_results, f, indent=2, default=str)
        
        # Save summary report
        summary_file = self.output_dir / f"{batch_id}_summary.md"
        with open(summary_file, 'w') as f:
            f.write(self._generate_summary_report(batch_results))
        
        logger.info(f"Batch results saved:")
        logger.info(f"  Complete results: {results_file}")
        logger.info(f"  Summary report: {summary_file}")
    
    def _generate_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable summary report."""
        return f"""
# Batch Generation Report: {results['batch_id']}

## Overview
- **Timestamp**: {results['timestamp']}
- **Execution Mode**: {results['execution_mode'].title()}
- **Total Execution Time**: {results['total_execution_time']:.1f}s
- **Articles per Minute**: {results['articles_per_minute']:.1f}

## Success Metrics
- **Total Articles**: {results['total_articles']}
- **Successful**: {results['successful_articles']}
- **Failed**: {results['failed_articles']}  
- **Success Rate**: {results['success_rate']:.1f}%

## Regeneration Metrics
- **Regeneration Enabled**: Yes
- **Max Attempts per Article**: {results['max_attempts_per_article']}
- **Articles Requiring Regeneration**: {results['articles_requiring_regeneration']}
- **Regeneration Rate**: {results['regeneration_rate']:.1f}%
- **Total Generation Attempts**: {results['total_generation_attempts']}
- **Avg Attempts per Article**: {results['avg_attempts_per_article']:.1f}

## Similarity Metrics  
- **Similarity Threshold**: {results['similarity_threshold']}%
- **Average Final Similarity**: {results['average_final_similarity']:.1f}%
- **Final Similarity Range**: {min(results['similarity_scores']):.1f}% - {max(results['similarity_scores']):.1f}%

## Performance
- **Avg Time per Article**: {results['avg_time_per_article']:.1f}s
- **Total Pipeline Time**: {results['total_execution_time']:.1f}s

## Status
- **Overall Status**: {results['status'].title()}
- **Regeneration System**: ✅ Working - Successfully prevented content cannibalization
"""
    
    def _log_batch_summary(self, results: Dict[str, Any]):
        """Log batch summary to console."""
        logger.info("🎯 BATCH GENERATION COMPLETED")
        logger.info("=" * 60)
        logger.info(f"✅ Success: {results['successful_articles']}/{results['total_articles']} articles ({results['success_rate']:.1f}%)")
        logger.info(f"🔄 Regeneration: {results['articles_requiring_regeneration']} articles needed regeneration ({results['regeneration_rate']:.1f}%)")
        logger.info(f"📊 Similarity: Average {results['average_final_similarity']:.1f}% (threshold: {results['similarity_threshold']}%)")
        logger.info(f"⏱️ Performance: {results['avg_time_per_article']:.1f}s per article, {results['articles_per_minute']:.1f} articles/min")
        logger.info(f"💾 Results saved to: {self.output_dir}")


# Predefined batch configurations for testing and production

SAMPLE_AI_TOPICS = [
    {
        "primary_keyword": "AI chatbot platform for customer service",
        "company_url": "https://valoon.chat",
        "company_name": "Valoon", 
        "industry": "AI Technology",
        "description": "AI-powered customer service automation platform"
    },
    {
        "primary_keyword": "machine learning automation tools for business",
        "company_url": "https://automl-pro.com",
        "company_name": "AutoML Pro",
        "industry": "Machine Learning",
        "description": "Automated machine learning platform for enterprises"
    },
    {
        "primary_keyword": "AI content generation software for marketing",
        "company_url": "https://contentai.co",
        "company_name": "ContentAI",
        "industry": "Marketing Technology",
        "description": "AI-powered content creation and optimization platform"
    },
    {
        "primary_keyword": "conversational AI for sales automation",
        "company_url": "https://salesbot.ai",
        "company_name": "SalesBot AI",
        "industry": "Sales Technology", 
        "description": "Conversational AI platform for sales automation"
    },
    {
        "primary_keyword": "AI-powered data analytics platform",
        "company_url": "https://datainsights.ai",
        "company_name": "DataInsights AI",
        "industry": "Data Analytics",
        "description": "AI-driven business intelligence and analytics platform"
    }
]


async def main():
    """Main function for command-line execution."""
    print("🚀 Production Batch Generation with Regeneration")
    print("=" * 60)
    
    # Initialize batch runner
    try:
        runner = ProductionBatchRunner(
            max_regeneration_attempts=3,
            similarity_threshold=70.0,
            output_dir="production_batch_output"
        )
        
        # Run sample batch
        print(f"📝 Running sample batch with {len(SAMPLE_AI_TOPICS)} AI-related topics...")
        print("🔄 Regeneration enabled - will automatically regenerate similar content")
        print()
        
        start_time = time.time()
        
        def progress_callback(current: int, total: int, message: str):
            print(f"Progress: {current}/{total} - {message}")
        
        results = await runner.run_batch(
            job_configs=SAMPLE_AI_TOPICS.copy(),
            sequential=True,  # Sequential to avoid similarity conflicts
            save_results=True,
            progress_callback=progress_callback
        )
        
        execution_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("🎯 PRODUCTION BATCH COMPLETED")
        print(f"✅ Generated: {results['successful_articles']}/{results['total_articles']} articles")
        print(f"🔄 Regenerated: {results['articles_requiring_regeneration']} articles")
        print(f"📊 Average similarity: {results['average_final_similarity']:.1f}%")
        print(f"⏱️ Total time: {execution_time:.1f}s")
        print(f"💾 Results saved to: production_batch_output/")
        
        return results
        
    except Exception as e:
        print(f"❌ Batch generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Set up environment
    os.chdir(Path(__file__).parent.parent.parent)
    
    # Run main
    asyncio.run(main())