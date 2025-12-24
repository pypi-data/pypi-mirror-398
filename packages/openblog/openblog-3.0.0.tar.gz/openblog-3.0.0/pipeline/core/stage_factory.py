"""
Stage Factory - Centralized stage creation following SOLID principles.

ABOUTME: Single responsibility for creating and validating all pipeline stages
ABOUTME: Eliminates duplication across test files and benchmarks with DRY approach

Following SOLID principles:
- Single Responsibility: Only handles stage creation and validation
- Open/Closed: Extensible for new stages without modifying existing code
- Dependency Inversion: Depends on Stage abstraction, not concrete implementations
"""

import logging
from typing import List, Dict, Optional, Type
from abc import ABC

from .workflow_engine import Stage

# Import all stage implementations
try:
    from ..blog_generation.stage_00_data_fetch import DataFetchStage
    from ..blog_generation.stage_01_prompt_build import PromptBuildStage
    from ..blog_generation.stage_02_gemini_call import GeminiCallStage
    from ..blog_generation.stage_03_quality_refinement import QualityRefinementStage
    from ..blog_generation.stage_04_citations import CitationsStage
    from ..blog_generation.stage_05_internal_links import InternalLinksStage
    # Stages 6-8 consolidated: ToC and Metadata into Stage 2, FAQ/PAA validation into Stage 3
    from ..blog_generation.stage_06_image import ImageStage
    from ..blog_generation.stage_07_similarity_check import HybridSimilarityCheckStage
    from ..blog_generation.stage_08_cleanup import CleanupStage
    from ..blog_generation.stage_09_storage import StorageStage
except ImportError as e:
    logging.error(f"Failed to import stage modules: {e}")
    # For graceful degradation, we'll still provide the factory interface
    pass

logger = logging.getLogger(__name__)


class StageRegistrationError(Exception):
    """Raised when stage registration fails."""
    pass


class StageValidationError(Exception):
    """Raised when stage validation fails."""
    pass


class IStageFactory(ABC):
    """
    Interface for stage factory implementations.
    
    Follows Interface Segregation Principle - minimal interface for stage creation.
    """
    
    def create_all_stages(self) -> List[Stage]:
        """
        Create all pipeline stages.
        
        Returns:
            List of Stage instances in execution order (0-9)
            
        Raises:
            StageRegistrationError: If any stage creation fails
        """
        pass
    
    def create_stages_subset(self, stage_numbers: List[int]) -> List[Stage]:
        """
        Create specific subset of stages.
        
        Args:
            stage_numbers: List of stage numbers to create
            
        Returns:
            List of Stage instances for requested stages
            
        Raises:
            StageRegistrationError: If any requested stage creation fails
        """
        pass
    
    def validate_stages(self, stages: List[Stage]) -> bool:
        """
        Validate that all required stages are present and properly configured.
        
        Args:
            stages: List of Stage instances to validate
            
        Returns:
            True if all stages are valid
            
        Raises:
            StageValidationError: If validation fails
        """
        pass


class ProductionStageFactory(IStageFactory):
    """
    Production-grade stage factory implementation.
    
    Handles:
    - Safe stage instantiation with error handling
    - Stage validation and dependency checking
    - Comprehensive logging and monitoring
    - Graceful degradation for missing dependencies
    """
    
    def __init__(self):
        """Initialize factory with stage registry."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._stage_registry = self._build_stage_registry()
    
    def _build_stage_registry(self) -> Dict[int, Type[Stage]]:
        """
        Build registry of available stage classes.
        
        Returns:
            Dictionary mapping stage numbers to stage classes
        """
        registry = {}
        
        # Standard pipeline stages (0-9) - CONSOLIDATED VERSION
        stage_classes = [
            (0, DataFetchStage),
            (1, PromptBuildStage),
            (2, GeminiCallStage),  # Includes ToC + Metadata
            (3, QualityRefinementStage),  # Includes FAQ/PAA validation
            (4, CitationsStage),
            (5, InternalLinksStage),
            (6, ImageStage),  # Renumbered from 7
            (7, HybridSimilarityCheckStage),  # Renumbered from 9
            (8, CleanupStage),  # Renumbered from 11
            (9, StorageStage),  # Renumbered from 12
        ]
        
        for stage_num, stage_class in stage_classes:
            try:
                # Validate that class exists and implements Stage interface
                if not issubclass(stage_class, Stage):
                    self.logger.warning(f"Stage {stage_num} ({stage_class.__name__}) does not implement Stage interface")
                    continue
                
                registry[stage_num] = stage_class
                self.logger.debug(f"Registered stage {stage_num}: {stage_class.__name__}")
                
            except NameError:
                self.logger.warning(f"Stage {stage_num} class not found, skipping registration")
                continue
            except Exception as e:
                self.logger.error(f"Failed to register stage {stage_num}: {e}")
                continue
        
        self.logger.info(f"Built stage registry with {len(registry)} stages")
        return registry
    
    def create_all_stages(self) -> List[Stage]:
        """
        Create all available pipeline stages.
        
        Returns:
            List of Stage instances in execution order
            
        Raises:
            StageRegistrationError: If critical stage creation fails
        """
        stages = []
        failed_stages = []
        
        # Create stages in order (0-9)
        for stage_num in sorted(self._stage_registry.keys()):
            try:
                stage_instance = self._create_stage_instance(stage_num)
                stages.append(stage_instance)
                self.logger.debug(f"Created stage {stage_num}: {stage_instance}")
                
            except Exception as e:
                self.logger.error(f"Failed to create stage {stage_num}: {e}")
                failed_stages.append(stage_num)
                
                # Critical stages - fail fast
                if stage_num in [0, 1, 2, 3, 8, 9]:
                    raise StageRegistrationError(
                        f"Critical stage {stage_num} creation failed: {e}"
                    )
        
        if failed_stages:
            self.logger.warning(f"Non-critical stages failed: {failed_stages}")
        
        self.logger.info(f"Created {len(stages)} stages successfully")
        return stages
    
    def create_stages_subset(self, stage_numbers: List[int]) -> List[Stage]:
        """
        Create specific subset of stages.
        
        Args:
            stage_numbers: List of stage numbers to create
            
        Returns:
            List of Stage instances for requested stages
            
        Raises:
            StageRegistrationError: If any requested stage creation fails
        """
        stages = []
        
        for stage_num in sorted(stage_numbers):
            if stage_num not in self._stage_registry:
                raise StageRegistrationError(f"Stage {stage_num} not available in registry")
            
            try:
                stage_instance = self._create_stage_instance(stage_num)
                stages.append(stage_instance)
                
            except Exception as e:
                raise StageRegistrationError(
                    f"Failed to create requested stage {stage_num}: {e}"
                )
        
        self.logger.info(f"Created {len(stages)} requested stages: {stage_numbers}")
        return stages
    
    def _create_stage_instance(self, stage_num: int) -> Stage:
        """
        Create single stage instance with error handling.
        
        Args:
            stage_num: Stage number to create
            
        Returns:
            Stage instance
            
        Raises:
            Exception: If stage creation fails
        """
        if stage_num not in self._stage_registry:
            raise ValueError(f"Stage {stage_num} not registered")
        
        stage_class = self._stage_registry[stage_num]
        
        try:
            # Create instance with default constructor
            stage_instance = stage_class()
            
            # Validate instance
            if not hasattr(stage_instance, 'stage_num'):
                raise AttributeError(f"Stage {stage_num} missing required attribute: stage_num")
            
            if not hasattr(stage_instance, 'stage_name'):
                raise AttributeError(f"Stage {stage_num} missing required attribute: stage_name")
            
            if stage_instance.stage_num != stage_num:
                raise ValueError(
                    f"Stage number mismatch: expected {stage_num}, got {stage_instance.stage_num}"
                )
            
            return stage_instance
            
        except Exception as e:
            self.logger.error(f"Stage {stage_num} instantiation failed: {e}")
            raise
    
    def validate_stages(self, stages: List[Stage]) -> bool:
        """
        Validate stage list for completeness and correctness.
        
        Args:
            stages: List of Stage instances to validate
            
        Returns:
            True if all stages are valid
            
        Raises:
            StageValidationError: If validation fails
        """
        if not stages:
            raise StageValidationError("No stages provided for validation")
        
        # Check for duplicates
        stage_numbers = [stage.stage_num for stage in stages]
        if len(stage_numbers) != len(set(stage_numbers)):
            duplicates = [num for num in stage_numbers if stage_numbers.count(num) > 1]
            raise StageValidationError(f"Duplicate stages found: {duplicates}")
        
        # Validate critical stages are present
        critical_stages = [0, 1, 2, 3, 8, 9]
        missing_critical = [num for num in critical_stages if num not in stage_numbers]
        if missing_critical:
            raise StageValidationError(f"Missing critical stages: {missing_critical}")
        
        # Validate each stage implementation
        for stage in stages:
            try:
                # Check interface compliance
                if not hasattr(stage, 'execute'):
                    raise AttributeError(f"Stage {stage.stage_num} missing execute method")
                
                if not callable(stage.execute):
                    raise AttributeError(f"Stage {stage.stage_num} execute is not callable")
                
                # Check stage attributes
                if not isinstance(stage.stage_num, int):
                    raise TypeError(f"Stage {stage.stage_num} stage_num must be int")
                
                if not isinstance(stage.stage_name, str):
                    raise TypeError(f"Stage {stage.stage_num} stage_name must be str")
                
            except Exception as e:
                raise StageValidationError(f"Stage {stage.stage_num} validation failed: {e}")
        
        # Check stage ordering
        sorted_stages = sorted(stages, key=lambda s: s.stage_num)
        if stages != sorted_stages:
            self.logger.warning("Stages not in sequential order - reordering recommended")
        
        self.logger.info(f"Validated {len(stages)} stages successfully")
        return True
    
    def get_available_stages(self) -> List[int]:
        """
        Get list of available stage numbers.
        
        Returns:
            List of available stage numbers
        """
        return sorted(self._stage_registry.keys())
    
    def is_stage_available(self, stage_num: int) -> bool:
        """
        Check if specific stage is available.
        
        Args:
            stage_num: Stage number to check
            
        Returns:
            True if stage is available
        """
        return stage_num in self._stage_registry


# Factory singleton for easy access
_factory_instance: Optional[ProductionStageFactory] = None


def get_stage_factory() -> ProductionStageFactory:
    """
    Get singleton stage factory instance.
    
    Returns:
        ProductionStageFactory instance
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = ProductionStageFactory()
    return _factory_instance


def create_production_pipeline_stages() -> List[Stage]:
    """
    Convenience function to create all production pipeline stages.
    
    Returns:
        List of all pipeline stages ready for registration
        
    Raises:
        StageRegistrationError: If stage creation fails
    """
    factory = get_stage_factory()
    stages = factory.create_all_stages()
    factory.validate_stages(stages)
    return stages


def create_benchmark_pipeline_stages() -> List[Stage]:
    """
    Create stages specifically for benchmark testing.
    
    Optimized subset for fast benchmark execution:
    - Includes all critical stages (0-3, 8-9)
    - Includes essential parallel stages (6-7)
    - Excludes optional stages that might cause timeouts
    
    Returns:
        List of benchmark-optimized pipeline stages
        
    Raises:
        StageRegistrationError: If stage creation fails
    """
    factory = get_stage_factory()
    
    # Core stages needed for content generation and quality assessment
    # Stages 6-8 consolidated: ToC and Metadata into Stage 2, FAQ/PAA validation into Stage 3
    benchmark_stages = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    stages = factory.create_stages_subset(benchmark_stages)
    factory.validate_stages(stages)
    
    logger.info(f"Created benchmark pipeline with {len(stages)} stages")
    return stages