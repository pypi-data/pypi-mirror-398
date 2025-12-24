"""
Regeneration System Integration

Simple integration layer to make the regeneration system easy to use with
existing OpenBlog pipeline infrastructure.

Provides:
- Drop-in replacement for existing batch generation scripts
- Backward compatibility with current workflow
- Easy configuration and setup
- Integration with existing job configs and output formats

Usage:
    # Replace existing batch generation with regeneration-enabled version
    from pipeline.integrations.regeneration_integration import BatchGeneratorWithRegeneration
    
    generator = BatchGeneratorWithRegeneration()
    results = await generator.generate_batch(job_configs)
    
    # Or use convenience function
    from pipeline.integrations.regeneration_integration import generate_batch_with_regeneration
    results = await generate_batch_with_regeneration(job_configs)
"""

import asyncio
import os
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from ..core.regeneration_engine import RegenerationEngine, create_regeneration_engine
from ..core.workflow_engine import WorkflowEngine
from ..production.batch_generation_with_regeneration import ProductionBatchRunner

logger = logging.getLogger(__name__)


class BatchGeneratorWithRegeneration:
    """
    Drop-in replacement for existing batch generators with regeneration support.
    
    Provides the same interface as existing batch generation but adds automatic
    similarity detection and content regeneration capabilities.
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        max_regeneration_attempts: int = 3,
        similarity_threshold: float = 70.0,
        enable_regeneration: bool = True,
        output_dir: Optional[str] = None
    ):
        """
        Initialize batch generator with regeneration.
        
        Args:
            gemini_api_key: Gemini API key (defaults to env GEMINI_API_KEY)
            max_regeneration_attempts: Max regeneration attempts per article
            similarity_threshold: Similarity % that triggers regeneration
            enable_regeneration: Whether to enable regeneration (can disable for testing)
            output_dir: Output directory for results
        """
        self.enable_regeneration = enable_regeneration
        
        if self.enable_regeneration:
            # Use full regeneration system
            self.runner = ProductionBatchRunner(
                gemini_api_key=gemini_api_key,
                max_regeneration_attempts=max_regeneration_attempts,
                similarity_threshold=similarity_threshold,
                output_dir=output_dir or "batch_output_with_regeneration"
            )
        else:
            # Fallback to basic workflow engine
            self.runner = None
            self.workflow_engine = self._setup_basic_workflow_engine()
        
        logger.info(f"BatchGeneratorWithRegeneration initialized (regeneration={'enabled' if enable_regeneration else 'disabled'})")
    
    def _setup_basic_workflow_engine(self) -> WorkflowEngine:
        """Setup basic workflow engine for non-regeneration mode."""
        from ..blog_generation.stage_00_data_fetch import DataFetchStage
        from ..blog_generation.stage_01_prompt_build import PromptBuildStage
        from ..blog_generation.stage_02_gemini_call import GeminiCallStage
        # Stage 3 (Extraction) is now part of Stage 2 (Generation + Extraction)
        from ..blog_generation.stage_04_citations import CitationsStage
        from ..blog_generation.stage_05_internal_links import InternalLinksStage
        # Stages 6-8 consolidated: ToC and Metadata into Stage 2, FAQ/PAA validation into Stage 3
        from ..blog_generation.stage_06_image import ImageStage
        from ..blog_generation.stage_07_similarity_check import HybridSimilarityCheckStage
        from ..blog_generation.stage_08_cleanup import CleanupStage
        from ..blog_generation.stage_09_storage import StorageStage
        
        engine = WorkflowEngine()
        stages = [
            DataFetchStage(), PromptBuildStage(), GeminiCallStage(),  # Stage 3 (Extraction) is now part of Stage 2
            CitationsStage(), InternalLinksStage(), TableOfContentsStage(), MetadataStage(),
            FAQPAAStage(), ImageStage(), CleanupStage(), StorageStage()
        ]
        engine.register_stages(stages)
        return engine
    
    async def generate_single(
        self, 
        job_config: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Generate single article with optional regeneration.
        
        Args:
            job_config: Job configuration
            progress_callback: Optional progress callback
            
        Returns:
            Article generation result
        """
        if self.enable_regeneration:
            # Use regeneration system
            result = await self.runner.run_batch(
                job_configs=[job_config],
                sequential=True,
                save_results=False,
                progress_callback=progress_callback
            )
            
            # Extract single result
            if result['successful_articles'] > 0:
                generation_reports = result['generation_reports']
                if generation_reports and generation_reports[0]['success']:
                    return {
                        'success': True,
                        'job_id': generation_reports[0]['job_id'],
                        'regeneration_report': generation_reports[0],
                        'attempts': generation_reports[0]['attempts_made'],
                        'final_similarity': generation_reports[0]['final_similarity']
                    }
            
            return {
                'success': False,
                'error': 'Article generation failed',
                'result': result
            }
        else:
            # Use basic workflow engine
            try:
                context = await self.workflow_engine.execute(
                    job_id=job_config.get('job_id', f"single_{int(asyncio.get_event_loop().time())}"),
                    job_config=job_config,
                    progress_callback=progress_callback
                )
                
                return {
                    'success': True,
                    'job_id': context.job_id,
                    'context': context,
                    'regeneration_enabled': False
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'regeneration_enabled': False
                }
    
    async def generate_batch(
        self,
        job_configs: List[Dict[str, Any]],
        sequential: bool = True,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Generate batch of articles with optional regeneration.
        
        Args:
            job_configs: List of job configurations
            sequential: Run sequentially (True) or parallel (False) 
            progress_callback: Optional progress callback
            
        Returns:
            Batch generation results
        """
        if self.enable_regeneration:
            # Use full regeneration system
            return await self.runner.run_batch(
                job_configs=job_configs,
                sequential=sequential,
                save_results=True,
                progress_callback=progress_callback
            )
        else:
            # Use basic workflow engine
            logger.info(f"Generating {len(job_configs)} articles without regeneration")
            
            results = []
            for i, config in enumerate(job_configs):
                if progress_callback:
                    progress_callback(i, len(job_configs), f"Processing article {i+1}")
                
                result = await self.generate_single(config)
                results.append(result)
            
            successful = sum(1 for r in results if r.get('success', False))
            
            return {
                'total_articles': len(job_configs),
                'successful_articles': successful,
                'failed_articles': len(job_configs) - successful,
                'success_rate': successful / len(job_configs) * 100 if job_configs else 0,
                'regeneration_enabled': False,
                'results': results,
                'status': 'completed'
            }


# Convenience functions for easy integration

async def generate_batch_with_regeneration(
    job_configs: List[Dict[str, Any]],
    gemini_api_key: Optional[str] = None,
    max_regeneration_attempts: int = 3,
    similarity_threshold: float = 70.0,
    sequential: bool = True,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate batch with regeneration.
    
    Drop-in replacement for existing batch generation functions.
    """
    generator = BatchGeneratorWithRegeneration(
        gemini_api_key=gemini_api_key,
        max_regeneration_attempts=max_regeneration_attempts,
        similarity_threshold=similarity_threshold,
        enable_regeneration=True
    )
    
    return await generator.generate_batch(
        job_configs=job_configs,
        sequential=sequential,
        progress_callback=progress_callback
    )


async def generate_single_with_regeneration(
    job_config: Dict[str, Any],
    gemini_api_key: Optional[str] = None,
    max_regeneration_attempts: int = 3,
    similarity_threshold: float = 70.0,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate single article with regeneration.
    """
    generator = BatchGeneratorWithRegeneration(
        gemini_api_key=gemini_api_key,
        max_regeneration_attempts=max_regeneration_attempts,
        similarity_threshold=similarity_threshold,
        enable_regeneration=True
    )
    
    return await generator.generate_single(
        job_config=job_config,
        progress_callback=progress_callback
    )


# Backward compatibility functions

async def generate_batch_legacy_compatible(
    job_configs: List[Dict[str, Any]],
    enable_similarity_checking: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Legacy-compatible batch generation function.
    
    Provides same interface as existing batch generators while adding
    regeneration capabilities when enabled.
    """
    if enable_similarity_checking:
        return await generate_batch_with_regeneration(
            job_configs=job_configs,
            **kwargs
        )
    else:
        generator = BatchGeneratorWithRegeneration(enable_regeneration=False)
        return await generator.generate_batch(job_configs)


# Integration helpers

def migrate_existing_batch_script(script_path: str, backup: bool = True) -> str:
    """
    Helper to migrate existing batch generation scripts to use regeneration.
    
    Args:
        script_path: Path to existing batch script
        backup: Whether to create backup of original
        
    Returns:
        Path to migrated script
    """
    script_path = Path(script_path)
    
    if backup and script_path.exists():
        backup_path = script_path.with_suffix(f"{script_path.suffix}.backup")
        script_path.rename(backup_path)
        logger.info(f"Backup created: {backup_path}")
    
    # Create migrated script content
    migrated_content = f'''#!/usr/bin/env python3
"""
Migrated batch generation script with regeneration support.
Original: {script_path.name}
Migrated: {script_path.name}

This script has been automatically migrated to use the regeneration system.
"""

import asyncio
from pipeline.integrations.regeneration_integration import generate_batch_with_regeneration

# Your original job configurations
JOB_CONFIGS = [
    # Add your job configurations here
]

async def main():
    """Main batch generation with regeneration."""
    print("🚀 Batch Generation with Regeneration")
    
    results = await generate_batch_with_regeneration(
        job_configs=JOB_CONFIGS,
        sequential=True,  # Recommended for similarity checking
        max_regeneration_attempts=3,
        similarity_threshold=70.0
    )
    
    print(f"✅ Generated {{results['successful_articles']}}/{{results['total_articles']}} articles")
    if results.get('articles_requiring_regeneration', 0) > 0:
        print(f"🔄 {{results['articles_requiring_regeneration']}} articles required regeneration")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Write migrated script
    with open(script_path, 'w') as f:
        f.write(migrated_content)
    
    logger.info(f"Script migrated: {script_path}")
    return str(script_path)


# Configuration presets for common use cases

REGENERATION_PRESETS = {
    'conservative': {
        'max_regeneration_attempts': 2,
        'similarity_threshold': 80.0  # High threshold, less regeneration
    },
    'balanced': {
        'max_regeneration_attempts': 3,
        'similarity_threshold': 70.0  # Default settings
    },
    'aggressive': {
        'max_regeneration_attempts': 5,
        'similarity_threshold': 60.0  # Low threshold, more regeneration
    },
    'testing': {
        'max_regeneration_attempts': 1,
        'similarity_threshold': 50.0  # For testing regeneration triggers
    }
}


def get_regeneration_preset(preset_name: str) -> Dict[str, Any]:
    """Get predefined regeneration configuration preset."""
    if preset_name not in REGENERATION_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(REGENERATION_PRESETS.keys())}")
    
    return REGENERATION_PRESETS[preset_name].copy()


async def generate_batch_with_preset(
    job_configs: List[Dict[str, Any]],
    preset: str = 'balanced',
    **kwargs
) -> Dict[str, Any]:
    """Generate batch using predefined regeneration preset."""
    preset_config = get_regeneration_preset(preset)
    preset_config.update(kwargs)  # Allow overrides
    
    return await generate_batch_with_regeneration(
        job_configs=job_configs,
        **preset_config
    )