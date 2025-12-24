"""
Content Generation Service - High-level abstraction for content generation pipeline.

ABOUTME: Clean abstraction layer over WorkflowEngine for benchmarks and external integrations
ABOUTME: Provides simplified interface with enhanced error handling and quality validation

Following Clean Architecture principles:
- Application Service layer that orchestrates domain operations
- Abstracts complex workflow orchestration behind simple interface  
- Handles cross-cutting concerns like logging, metrics, error handling
- Provides consistent interface for different use cases (benchmarks, production)
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Union, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from ..core.workflow_engine import WorkflowEngine, Stage
from ..core.stage_factory import create_benchmark_pipeline_stages, create_production_pipeline_stages, StageRegistrationError
from .quality_validation_service import ProductionQualityValidator, QualityReport, get_quality_validator

logger = logging.getLogger(__name__)


class GenerationMode(Enum):
    """Content generation mode enumeration."""
    PRODUCTION = "production"        # Full pipeline with all stages
    BENCHMARK = "benchmark"          # Optimized for testing/benchmarks
    QUALITY_ONLY = "quality_only"   # Skip generation, quality assessment only


class GenerationError(Exception):
    """Raised when content generation fails."""
    pass


class ValidationError(Exception):
    """Raised when content validation fails."""
    pass


@dataclass
class GenerationRequest:
    """
    Content generation request with all parameters.
    """
    primary_keyword: str
    company_name: str
    country: str = "US"
    language: str = "en"
    company_info: Optional[Dict[str, Any]] = None
    competitors: Optional[List[str]] = None
    custom_instructions: str = ""
    system_prompts: Optional[List[str]] = None
    mode: GenerationMode = GenerationMode.PRODUCTION
    
    def to_job_config(self) -> Dict[str, Any]:
        """Convert request to job configuration for workflow engine."""
        # Provide sensible defaults for all required fields
        company_info = self.company_info or {
            'description': 'Professional service provider',
            'website': f'https://{self.company_name.lower().replace(" ", "-")}.com'
        }
        
        return {
            'primary_keyword': self.primary_keyword,
            'country': self.country,
            'language': self.language,
            'company_name': self.company_name,
            'company_url': company_info.get('website', f'https://{self.company_name.lower().replace(" ", "-")}.com'),
            'company_data': {
                'company_name': self.company_name,
                'company_info': company_info,
                'company_competitors': self.competitors or []
            },
            'content_generation_instruction': self.custom_instructions,
            'system_prompts': self.system_prompts or []
        }


@dataclass
class GenerationResult:
    """
    Content generation result with content and quality metrics.
    """
    success: bool
    content: Optional[Dict[str, Any]]
    quality_report: Optional[QualityReport]
    execution_time_ms: float
    job_id: str
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
    
    @property
    def is_production_ready(self) -> bool:
        """Check if generated content meets production standards."""
        return (
            self.success and 
            self.content is not None and 
            self.quality_report is not None and 
            self.quality_report.is_production_ready
        )
    
    @property 
    def meets_premium_standards(self) -> bool:
        """Check if generated content meets premium quality standards (Smalt/Enter level)."""
        return (
            self.is_production_ready and 
            self.quality_report.meets_smalt_enter_standards
        )


class IContentGenerationService(Protocol):
    """
    Interface for content generation service implementations.
    
    Follows Interface Segregation Principle.
    """
    
    async def generate_content(self, request: GenerationRequest) -> GenerationResult:
        """Generate content based on request parameters."""
        pass
    
    async def validate_content_quality(
        self, 
        content: Dict[str, Any], 
        request: GenerationRequest
    ) -> QualityReport:
        """Validate content quality without regeneration."""
        pass
    
    def get_supported_markets(self) -> List[str]:
        """Get list of supported market configurations."""
        pass


class CircuitBreakerState(Enum):
    """Circuit breaker states for fault tolerance."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass 
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: float = 60.0     # Seconds before trying again
    success_threshold: int = 3          # Successes before closing


class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance.
    
    Protects against cascading failures in content generation pipeline.
    """
    
    def __init__(self, config: CircuitBreakerConfig = CircuitBreakerConfig()):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.config.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                self.logger.info("Circuit breaker entering half-open state")
            else:
                raise GenerationError("Circuit breaker is open - service temporarily unavailable")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful operation."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.logger.info("Circuit breaker closed - service recovered")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class ProductionContentGenerationService(IContentGenerationService):
    """
    Production-grade content generation service.
    
    Provides:
    - High-level abstraction over WorkflowEngine
    - Enhanced error handling with circuit breaker pattern
    - Comprehensive quality validation integration
    - Performance monitoring and metrics
    - Multiple generation modes (production, benchmark, quality-only)
    """
    
    def __init__(
        self,
        quality_validator: Optional[ProductionQualityValidator] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize content generation service.
        
        Args:
            quality_validator: Optional quality validator for dependency injection
            circuit_breaker_config: Optional circuit breaker configuration
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.quality_validator = quality_validator or get_quality_validator()
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config or CircuitBreakerConfig())
        
        # Performance tracking
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_execution_time_ms': 0.0,
            'quality_scores': []
        }
    
    async def generate_content(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate content based on request parameters.
        
        Args:
            request: Content generation request
            
        Returns:
            GenerationResult with content and quality metrics
            
        Raises:
            GenerationError: If content generation fails
            ValidationError: If content validation fails
        """
        start_time = time.time()
        job_id = f"{request.mode.value}-{request.country}-{int(time.time())}"
        
        self.metrics['total_requests'] += 1
        
        try:
            self.logger.info(f"Starting content generation: {job_id}")
            
            # Use circuit breaker for fault tolerance
            result = await self.circuit_breaker.call(
                self._generate_content_internal, request, job_id, start_time
            )
            
            self.metrics['successful_requests'] += 1
            self._update_performance_metrics(result.execution_time_ms, result.quality_report)
            
            return result
            
        except Exception as e:
            self.metrics['failed_requests'] += 1
            execution_time_ms = (time.time() - start_time) * 1000
            
            self.logger.error(f"Content generation failed for {job_id}: {e}")
            
            return GenerationResult(
                success=False,
                content=None,
                quality_report=None,
                execution_time_ms=execution_time_ms,
                job_id=job_id,
                error_message=str(e)
            )
    
    async def _generate_content_internal(
        self, 
        request: GenerationRequest, 
        job_id: str, 
        start_time: float
    ) -> GenerationResult:
        """Internal content generation with error handling."""
        
        # Create and configure workflow engine
        engine = WorkflowEngine()
        
        try:
            # Register stages based on generation mode
            if request.mode == GenerationMode.PRODUCTION:
                stages = create_production_pipeline_stages()
            elif request.mode == GenerationMode.BENCHMARK:
                stages = create_benchmark_pipeline_stages()
            else:
                raise GenerationError(f"Unsupported generation mode: {request.mode}")
            
            engine.register_stages(stages)
            self.logger.info(f"Registered {len(stages)} stages for {request.mode.value} mode")
            
        except StageRegistrationError as e:
            raise GenerationError(f"Stage registration failed: {e}")
        
        # Convert request to job configuration
        job_config = request.to_job_config()
        
        # Execute workflow with timeout
        try:
            # Set timeout based on mode (benchmark = 180s for tools, production = 300s)
            timeout = 180.0 if request.mode == GenerationMode.BENCHMARK else 300.0
            
            execution_context = await asyncio.wait_for(
                engine.execute(job_id, job_config), 
                timeout=timeout
            )
            
        except asyncio.TimeoutError:
            raise GenerationError(f"Content generation timed out after {timeout}s")
        except Exception as e:
            raise GenerationError(f"Workflow execution failed: {e}")
        
        # Extract content from execution context
        content = None
        if hasattr(execution_context, 'article_output') and execution_context.article_output:
            content = execution_context.article_output.model_dump()
        elif hasattr(execution_context, 'validated_article') and execution_context.validated_article:
            content = execution_context.validated_article
        elif hasattr(execution_context, 'final_article') and execution_context.final_article:
            content = execution_context.final_article
        
        if not content:
            raise GenerationError("No content produced by workflow pipeline")
        
        # Validate content quality
        try:
            quality_report = await self.validate_content_quality(content, request)
        except Exception as e:
            self.logger.warning(f"Quality validation failed: {e}")
            quality_report = None
        
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Collect warnings from execution context
        warnings = []
        if hasattr(execution_context, 'errors') and execution_context.errors:
            warnings = [f"Stage error: {error}" for error in execution_context.errors.values()]
        
        return GenerationResult(
            success=True,
            content=content,
            quality_report=quality_report,
            execution_time_ms=execution_time_ms,
            job_id=job_id,
            warnings=warnings
        )
    
    async def validate_content_quality(
        self, 
        content: Dict[str, Any], 
        request: GenerationRequest
    ) -> QualityReport:
        """
        Validate content quality without regeneration.
        
        Args:
            content: Content to validate
            request: Original generation request for context
            
        Returns:
            QualityReport with comprehensive validation results
            
        Raises:
            ValidationError: If validation process fails
        """
        try:
            job_config = request.to_job_config()
            
            # Create market profile for validation context
            market_profile = {
                'country': request.country,
                'language': request.language,
                'min_word_count': 1500,  # Default minimum
                'authorities': []         # Will be populated from MARKET_CONFIG
            }
            
            quality_report = self.quality_validator.validate_content(
                content, job_config, market_profile
            )
            
            self.logger.info(
                f"Quality validation complete: {quality_report.overall_score:.1f}% "
                f"({quality_report.overall_level.value})"
            )
            
            return quality_report
            
        except Exception as e:
            self.logger.error(f"Quality validation failed: {e}")
            raise ValidationError(f"Content quality validation failed: {e}")
    
    def get_supported_markets(self) -> List[str]:
        """
        Get list of supported market configurations.
        
        Returns:
            List of supported country codes
        """
        # Import here to avoid circular imports
        from ..prompts.main_article import MARKET_CONFIG
        
        supported_markets = list(MARKET_CONFIG.keys())
        supported_markets.remove('DEFAULT')  # Exclude fallback config
        
        return sorted(supported_markets)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        success_rate = 0.0
        if self.metrics['total_requests'] > 0:
            success_rate = (self.metrics['successful_requests'] / self.metrics['total_requests']) * 100
        
        avg_quality_score = 0.0
        if self.metrics['quality_scores']:
            avg_quality_score = sum(self.metrics['quality_scores']) / len(self.metrics['quality_scores'])
        
        return {
            'total_requests': self.metrics['total_requests'],
            'success_rate': success_rate,
            'avg_execution_time_ms': self.metrics['avg_execution_time_ms'],
            'avg_quality_score': avg_quality_score,
            'circuit_breaker_state': self.circuit_breaker.state.value,
            'failure_count': self.circuit_breaker.failure_count
        }
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_execution_time_ms': 0.0,
            'quality_scores': []
        }
        self.logger.info("Performance metrics reset")
    
    def _update_performance_metrics(
        self, 
        execution_time_ms: float, 
        quality_report: Optional[QualityReport]
    ):
        """Update internal performance metrics."""
        # Update average execution time
        total_requests = self.metrics['total_requests']
        current_avg = self.metrics['avg_execution_time_ms']
        self.metrics['avg_execution_time_ms'] = (
            (current_avg * (total_requests - 1) + execution_time_ms) / total_requests
        )
        
        # Track quality scores
        if quality_report:
            self.metrics['quality_scores'].append(quality_report.overall_score)
            
            # Keep only last 100 scores for memory efficiency
            if len(self.metrics['quality_scores']) > 100:
                self.metrics['quality_scores'] = self.metrics['quality_scores'][-100:]


# Service factory and singleton management
_service_instance: Optional[ProductionContentGenerationService] = None


def get_content_generation_service() -> ProductionContentGenerationService:
    """
    Get singleton content generation service instance.
    
    Returns:
        ProductionContentGenerationService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = ProductionContentGenerationService()
    return _service_instance


def create_content_generation_service(
    quality_validator: Optional[ProductionQualityValidator] = None,
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
) -> ProductionContentGenerationService:
    """
    Factory function to create content generation service.
    
    Args:
        quality_validator: Optional quality validator for dependency injection
        circuit_breaker_config: Optional circuit breaker configuration
        
    Returns:
        Configured ProductionContentGenerationService instance
    """
    return ProductionContentGenerationService(quality_validator, circuit_breaker_config)


# Convenience functions for common use cases
async def generate_benchmark_content(
    keyword: str,
    company_name: str,
    country: str = "US",
    language: str = "en"
) -> GenerationResult:
    """
    Convenience function for benchmark content generation.
    
    Args:
        keyword: Primary keyword for content
        company_name: Company name
        country: Target country code
        language: Target language code
        
    Returns:
        GenerationResult with benchmark content
    """
    service = get_content_generation_service()
    
    request = GenerationRequest(
        primary_keyword=keyword,
        company_name=company_name,
        country=country,
        language=language,
        mode=GenerationMode.BENCHMARK
    )
    
    return await service.generate_content(request)


async def generate_production_content(
    keyword: str,
    company_name: str,
    country: str = "US", 
    language: str = "en",
    company_info: Optional[Dict[str, Any]] = None,
    competitors: Optional[List[str]] = None,
    custom_instructions: str = ""
) -> GenerationResult:
    """
    Convenience function for production content generation.
    
    Args:
        keyword: Primary keyword for content
        company_name: Company name
        country: Target country code
        language: Target language code
        company_info: Optional company information
        competitors: Optional list of competitors
        custom_instructions: Optional custom generation instructions
        
    Returns:
        GenerationResult with production content
    """
    service = get_content_generation_service()
    
    request = GenerationRequest(
        primary_keyword=keyword,
        company_name=company_name,
        country=country,
        language=language,
        company_info=company_info,
        competitors=competitors,
        custom_instructions=custom_instructions,
        mode=GenerationMode.PRODUCTION
    )
    
    return await service.generate_content(request)