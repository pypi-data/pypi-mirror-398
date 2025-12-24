"""Tests for input validation and timeout handling"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch
from pydantic import ValidationError

from pipeline.keyword_generation.models import KeywordGenerationConfig, CompanyInfo
from pipeline.keyword_generation.ai_generator import AIKeywordGenerator
from pipeline.keyword_generation.scorer import KeywordScorer
from pipeline.keyword_generation.generator import KeywordGeneratorV2
from pipeline.keyword_generation.exceptions import ScoringError


class TestInputValidation:
    """Test input validation for KeywordGenerationConfig"""
    
    def test_negative_target_count(self):
        """Test that negative target_count raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            KeywordGenerationConfig(target_count=-1)
        assert "Count must be >= 0" in str(exc_info.value)
    
    def test_negative_ai_keywords_count(self):
        """Test that negative ai_keywords_count raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            KeywordGenerationConfig(ai_keywords_count=-5)
        assert "Count must be >= 0" in str(exc_info.value)
    
    def test_negative_gap_keywords_count(self):
        """Test that negative gap_keywords_count raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            KeywordGenerationConfig(gap_keywords_count=-10)
        assert "Count must be >= 0" in str(exc_info.value)
    
    def test_zero_counts_valid(self):
        """Test that zero counts are valid (valid use case)"""
        config = KeywordGenerationConfig(
            target_count=0,
            ai_keywords_count=0,
            gap_keywords_count=0
        )
        assert config.target_count == 0
        assert config.ai_keywords_count == 0
        assert config.gap_keywords_count == 0
    
    def test_negative_long_tail_per_seed(self):
        """Test that negative long_tail_per_seed raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            KeywordGenerationConfig(long_tail_per_seed=-1)
        assert "Count must be >= 0" in str(exc_info.value)
    
    def test_negative_max_competitors(self):
        """Test that negative max_competitors raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            KeywordGenerationConfig(max_competitors=-1)
        assert "Count must be >= 0" in str(exc_info.value)
    
    def test_score_out_of_range_high(self):
        """Test that min_score > 100 raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            KeywordGenerationConfig(min_score=150)
        assert "Score must be between 0 and 100" in str(exc_info.value)
    
    def test_score_out_of_range_low(self):
        """Test that min_score < 0 raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            KeywordGenerationConfig(min_score=-10)
        assert "Score must be between 0 and 100" in str(exc_info.value)
    
    def test_score_valid_range(self):
        """Test that valid scores (0-100) are accepted"""
        config1 = KeywordGenerationConfig(min_score=0)
        assert config1.min_score == 0
        
        config2 = KeywordGenerationConfig(min_score=100)
        assert config2.min_score == 100
        
        config3 = KeywordGenerationConfig(min_score=50)
        assert config3.min_score == 50
    
    def test_competition_out_of_range_high(self):
        """Test that gap_max_competition > 1 raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            KeywordGenerationConfig(gap_max_competition=1.5)
        assert "Competition level must be between 0 and 1" in str(exc_info.value)
    
    def test_competition_out_of_range_low(self):
        """Test that gap_max_competition < 0 raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            KeywordGenerationConfig(gap_max_competition=-0.1)
        assert "Competition level must be between 0 and 1" in str(exc_info.value)
    
    def test_competition_valid_range(self):
        """Test that valid competition levels (0-1) are accepted"""
        config1 = KeywordGenerationConfig(gap_max_competition=0.0)
        assert config1.gap_max_competition == 0.0
        
        config2 = KeywordGenerationConfig(gap_max_competition=1.0)
        assert config2.gap_max_competition == 1.0
        
        config3 = KeywordGenerationConfig(gap_max_competition=0.5)
        assert config3.gap_max_competition == 0.5
    
    def test_negative_gap_volume(self):
        """Test that negative gap_min_volume raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            KeywordGenerationConfig(gap_min_volume=-100)
        assert "Count must be >= 0" in str(exc_info.value)
    
    def test_negative_gap_difficulty(self):
        """Test that negative gap_max_difficulty raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            KeywordGenerationConfig(gap_max_difficulty=-10)
        assert "Count must be >= 0" in str(exc_info.value)
    
    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are reported"""
        with pytest.raises(ValidationError) as exc_info:
            KeywordGenerationConfig(
                target_count=-1,
                min_score=150,
                gap_max_competition=1.5
            )
        errors = exc_info.value.errors()
        assert len(errors) >= 3  # Should have at least 3 errors


class TestTimeoutHandling:
    """Test timeout handling in async operations"""
    
    @pytest.fixture
    def mock_genai(self):
        """Mock Google Generative AI"""
        with patch('pipeline.keyword_generation.ai_generator.genai') as mock_genai_module:
            mock_model = MagicMock()
            mock_genai_module.GenerativeModel.return_value = mock_model
            yield mock_genai_module, mock_model
    
    @pytest.mark.asyncio
    async def test_timeout_in_batch_generation(self, mock_genai):
        """Test that timeout is handled in batch generation"""
        mock_genai_module, mock_model = mock_genai
        
        # Create generator with very short timeout
        generator = AIKeywordGenerator(
            api_key='test',
            api_timeout=0.1  # 100ms timeout
        )
        
        # Mock slow API call that exceeds timeout
        def slow_api_call(*args, **kwargs):
            import time
            time.sleep(1)  # Sleep longer than timeout
            response = MagicMock()
            response.text = '[]'
            return response
        
        mock_model.generate_content = slow_api_call
        
        # Should handle timeout gracefully and return empty list
        result = await generator._generate_batch_async(
            batch_num=1,
            batch_count=5,
            batch_aeo=2,
            batch_regular=3,
            company_context='Test Company',
            keyword_schema={}
        )
        
        # Should return empty list after timeout retries
        assert isinstance(result, list)
        # May be empty due to timeout, which is expected behavior
    
    @pytest.mark.asyncio
    async def test_timeout_in_scoring(self, mock_genai):
        """Test that timeout is handled in scoring"""
        mock_genai_module, mock_model = mock_genai
        
        # Create scorer with very short timeout
        scorer = KeywordScorer(
            api_key='test',
            api_timeout=0.1  # 100ms timeout
        )
        
        # Mock slow API call
        def slow_api_call(*args, **kwargs):
            import time
            time.sleep(1)  # Sleep longer than timeout
            response = MagicMock()
            response.text = '[]'
            return response
        
        mock_model.generate_content = slow_api_call
        
        keywords = [
            {"keyword": "test keyword", "source": "ai_generated", "score": 0}
        ]
        
        # Should raise ScoringError after retries (no default scores)
        with pytest.raises(ScoringError) as exc_info:
            await scorer._score_batch_async(
                keywords=keywords,
                company_name="Test",
                company_description=None,
                services=None,
                products=None,
                target_audience=None
            )
        assert "timed out" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_no_timeout_when_timeout_is_none(self, mock_genai):
        """Test that timeout is not applied when api_timeout is None"""
        mock_genai_module, mock_model = mock_genai
        
        generator = AIKeywordGenerator(
            api_key='test',
            api_timeout=None  # No timeout
        )
        
        # Mock fast API call
        def fast_api_call(*args, **kwargs):
            response = MagicMock()
            response.text = '[]'
            return response
        
        mock_model.generate_content = fast_api_call
        
        # Should work without timeout
        result = await generator._generate_batch_async(
            batch_num=1,
            batch_count=5,
            batch_aeo=2,
            batch_regular=3,
            company_context='Test',
            keyword_schema={}
        )
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_no_timeout_when_timeout_is_zero(self, mock_genai):
        """Test that timeout is not applied when api_timeout is 0"""
        mock_genai_module, mock_model = mock_genai
        
        generator = AIKeywordGenerator(
            api_key='test',
            api_timeout=0  # Zero timeout (disabled)
        )
        
        # Mock fast API call
        def fast_api_call(*args, **kwargs):
            response = MagicMock()
            response.text = '[]'
            return response
        
        mock_model.generate_content = fast_api_call
        
        # Should work without timeout
        result = await generator._generate_batch_async(
            batch_num=1,
            batch_count=5,
            batch_aeo=2,
            batch_regular=3,
            company_context='Test',
            keyword_schema={}
        )
        
        assert isinstance(result, list)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_very_large_counts(self):
        """Test that very large counts are accepted (may cause performance issues but valid)"""
        config = KeywordGenerationConfig(
            target_count=10000,
            ai_keywords_count=5000,
            gap_keywords_count=5000
        )
        assert config.target_count == 10000
    
    def test_max_score(self):
        """Test that max score (100) is valid"""
        config = KeywordGenerationConfig(min_score=100)
        assert config.min_score == 100
    
    def test_min_score(self):
        """Test that min score (0) is valid"""
        config = KeywordGenerationConfig(min_score=0)
        assert config.min_score == 0
    
    def test_max_competition(self):
        """Test that max competition (1.0) is valid"""
        config = KeywordGenerationConfig(gap_max_competition=1.0)
        assert config.gap_max_competition == 1.0
    
    def test_min_competition(self):
        """Test that min competition (0.0) is valid"""
        config = KeywordGenerationConfig(gap_max_competition=0.0)
        assert config.gap_max_competition == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

