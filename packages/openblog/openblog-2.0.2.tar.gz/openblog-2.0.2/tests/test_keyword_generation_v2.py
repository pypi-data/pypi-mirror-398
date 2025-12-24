"""Unit tests for Keyword Generation V2"""

import pytest
import json
import threading
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

from pipeline.keyword_generation.ai_generator import AIKeywordGenerator
from pipeline.keyword_generation.scorer import KeywordScorer
from pipeline.keyword_generation.generator import KeywordGeneratorV2
from pipeline.keyword_generation.models import CompanyInfo, KeywordGenerationConfig, KeywordSource, IntentType
from pipeline.keyword_generation.exceptions import AIGenerationError, ScoringError, GapAnalysisError
from pipeline.integrations.seranking.gap_analyzer_wrapper import GapAnalyzerWrapper


class TestAIKeywordGenerator:
    """Tests for AIKeywordGenerator"""
    
    @pytest.fixture
    def mock_genai(self):
        """Mock google.generativeai"""
        with patch('pipeline.keyword_generation.ai_generator.genai') as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = Mock()
            yield mock_genai, mock_model
    
    @pytest.fixture
    def generator(self, mock_genai):
        """Create generator instance"""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            gen = AIKeywordGenerator(api_key='test_key')
            # Ensure rate limit attributes exist (for backward compatibility in tests)
            if not hasattr(gen, '_rate_limit_lock'):
                gen._rate_limit_lock = threading.Lock()
                gen._last_api_call_time = 0.0
                gen._rate_limit_delay = 0.5
            return gen
    
    def test_init_success(self, mock_genai):
        """Test successful initialization"""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            gen = AIKeywordGenerator(api_key='test_key')
            assert gen.api_key == 'test_key'
            assert gen.model is not None
    
    def test_init_missing_api_key(self):
        """Test initialization without API key"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Google API key not found"):
                AIKeywordGenerator()
    
    def test_generate_seed_keywords_success(self, generator, mock_genai):
        """Test successful seed keyword generation"""
        mock_genai, mock_model = mock_genai
        
        # Mock response
        mock_response = MagicMock()
        mock_response.text = json.dumps([
            {"keyword": "ai consulting", "type": "short-tail", "intent": "commercial", "notes": "Relevant"},
            {"keyword": "machine learning solutions", "type": "long-tail", "intent": "informational", "notes": "Relevant"}
        ])
        mock_model.generate_content.return_value = mock_response
        
        keywords = generator.generate_seed_keywords(
            company_name="Test Co",
            industry="Tech",
            count=2
        )
        
        assert len(keywords) == 2
        assert keywords[0]["keyword"] == "ai consulting"
        assert keywords[0]["source"] == KeywordSource.AI_GENERATED.value
        mock_model.generate_content.assert_called_once()
    
    def test_generate_seed_keywords_empty_response(self, generator, mock_genai):
        """Test handling of empty response"""
        mock_genai, mock_model = mock_genai
        
        mock_response = MagicMock()
        mock_response.text = "[]"
        mock_model.generate_content.return_value = mock_response
        
        keywords = generator.generate_seed_keywords(company_name="Test", count=10)
        assert keywords == []
    
    def test_generate_seed_keywords_api_error(self, generator, mock_genai):
        """Test handling of API errors - should return empty list after retries"""
        mock_genai, mock_model = mock_genai
        mock_model.generate_content.side_effect = Exception("API Error")
        
        # After retries fail, should return empty list (graceful degradation)
        result = generator.generate_seed_keywords(company_name="Test", count=10)
        assert result == []  # Should return empty list, not raise exception
    
    def test_generate_long_tail_variants(self, generator, mock_genai):
        """Test long-tail variant generation"""
        mock_genai, mock_model = mock_genai
        
        mock_response = MagicMock()
        mock_response.text = json.dumps([
            {"keyword": "how to implement ai solutions", "question_based": True, "intent": "question"},
            {"keyword": "best ai consulting services", "question_based": False, "intent": "commercial"}
        ])
        mock_model.generate_content.return_value = mock_response
        
        variants = generator.generate_long_tail_variants(
            seed_keywords=["ai consulting"],
            company_name="Test Co",
            variants_per_seed=2
        )
        
        assert len(variants) == 2
        assert variants[0]["is_question"] is True
    
    def test_deduplicate_keywords(self, generator):
        """Test keyword deduplication"""
        keywords = [
            {"keyword": "ai consulting"},
            {"keyword": "AI Consulting"},  # Duplicate (case-insensitive)
            {"keyword": "machine learning"},
            {"keyword": "machine learning solutions"},  # Similar but different
        ]
        
        deduplicated = generator.deduplicate_keywords(keywords)
        assert len(deduplicated) == 3  # Removed one duplicate
    
    def test_parse_json_response_markdown(self, generator):
        """Test parsing JSON wrapped in markdown"""
        response_text = "```json\n[{\"keyword\": \"test\"}]\n```"
        result = generator._parse_json_response(response_text)
        assert result == [{"keyword": "test"}]


class TestKeywordScorer:
    """Tests for KeywordScorer"""
    
    @pytest.fixture
    def mock_genai(self):
        """Mock google.generativeai"""
        with patch('pipeline.keyword_generation.scorer.genai') as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = Mock()
            yield mock_genai, mock_model
    
    @pytest.fixture
    def scorer(self, mock_genai):
        """Create scorer instance"""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            scorer = KeywordScorer(api_key='test_key')
            # Ensure rate limit method exists (for tests that don't use new params)
            if not hasattr(scorer, '_rate_limit'):
                scorer._rate_limit = lambda: None  # No-op for tests
            return scorer
    
    def test_score_keywords_success(self, scorer, mock_genai):
        """Test successful keyword scoring"""
        mock_genai, mock_model = mock_genai
        
        mock_response = MagicMock()
        mock_response.text = json.dumps([
            {"keyword": "ai consulting", "score": 85, "reasoning": "Highly relevant"},
            {"keyword": "machine learning", "score": 75, "reasoning": "Relevant"}
        ])
        mock_model.generate_content.return_value = mock_response
        
        keywords = [
            {"keyword": "ai consulting"},
            {"keyword": "machine learning"}
        ]
        
        scored = scorer.score_keywords(
            keywords=keywords,
            company_name="Test Co"
        )
        
        assert len(scored) == 2
        assert scored[0]["score"] == 85
        assert scored[1]["score"] == 75
    
    def test_score_keywords_batch_processing(self, scorer, mock_genai):
        """Test batch processing of keywords"""
        mock_genai, mock_model = mock_genai
        
        # Track which batch we're on
        call_count = [0]
        
        # Mock to return keywords for each batch (25 keywords per batch)
        def mock_generate_content(*args, **kwargs):
            call_count[0] += 1
            batch_num = call_count[0]
            mock_response = MagicMock()
            # Return 25 keywords with scores matching the batch
            # Batch 1: keywords 0-24, Batch 2: 25-49, etc.
            start_idx = (batch_num - 1) * 25
            mock_response.text = json.dumps([
                {"keyword": f"keyword{i}", "score": 50 + (i % 25)}
                for i in range(start_idx, min(start_idx + 25, 100))
            ])
            return mock_response
        
        mock_model.generate_content.side_effect = mock_generate_content
        
        keywords = [{"keyword": f"keyword{i}"} for i in range(100)]
        scored = scorer.score_keywords(keywords, company_name="Test", batch_size=50)
        
        # Should make 4 API calls (100 keywords / 25 max_batch_size = 4 batches)
        # Note: max_batch_size is now 25, so batch_size=50 is capped at 25
        assert mock_model.generate_content.call_count == 4
        assert len(scored) == 100  # All keywords should be scored
    
    def test_score_keywords_api_error(self, scorer, mock_genai):
        """Test handling of API errors - should raise ScoringError"""
        from pipeline.keyword_generation.exceptions import ScoringError
        
        mock_genai, mock_model = mock_genai
        mock_model.generate_content.side_effect = Exception("API Error")
        
        keywords = [{"keyword": "test"}]
        
        # Should raise ScoringError after retries (no default scores)
        with pytest.raises(ScoringError):
            scorer.score_keywords(keywords, company_name="Test")
    
    def test_filter_by_score(self):
        """Test score filtering"""
        keywords = [
            {"keyword": "high", "score": 90},
            {"keyword": "medium", "score": 50},
            {"keyword": "low", "score": 30},
        ]
        
        filtered = KeywordScorer.filter_by_score(keywords, min_score=40)
        assert len(filtered) == 2
        assert all(kw["score"] >= 40 for kw in filtered)


class TestKeywordGeneratorV2:
    """Tests for KeywordGeneratorV2 orchestrator"""
    
    @pytest.fixture
    def company_info(self):
        """Sample company info"""
        return CompanyInfo(
            name="Test Company",
            url="test.com",
            industry="Tech",
            services=["AI Consulting"],
            products=["AI Platform"]
        )
    
    @pytest.fixture
    def config(self):
        """Default config"""
        return KeywordGenerationConfig(
            target_count=10,
            ai_keywords_count=5,
            gap_keywords_count=5,
            enable_long_tail_expansion=False,
            enable_gap_analysis=False,  # Disable for unit tests
        )
    
    @pytest.fixture
    def generator(self):
        """Create generator with mocked dependencies"""
        with patch('pipeline.keyword_generation.generator.AIKeywordGenerator') as mock_ai_class, \
             patch('pipeline.keyword_generation.generator.SEORankingAPIClient') as mock_se_class, \
             patch('pipeline.keyword_generation.generator.KeywordScorer') as mock_scorer_class, \
             patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key', 'SERANKING_API_KEY': 'test_key'}):
            
            # Setup mocks
            mock_ai_instance = MagicMock()
            # Use AsyncMock for async method
            mock_ai_instance.generate_seed_keywords_async = AsyncMock(return_value=[
                {
                    "keyword": f"ai keyword {i}",
                    "source": "ai_generated",
                    "score": 0,
                    "intent": "informational",
                    "is_question": False,
                    "word_count": 2,
                }
                for i in range(5)
            ])
            # Keep sync method for backward compatibility
            mock_ai_instance.generate_seed_keywords.return_value = [
                {
                    "keyword": f"ai keyword {i}",
                    "source": "ai_generated",
                    "score": 0,
                    "intent": "informational",
                    "is_question": False,
                    "word_count": 2,
                }
                for i in range(5)
            ]
            mock_ai_instance.generate_long_tail_variants.return_value = []  # No long-tail for tests
            mock_ai_instance.deduplicate_keywords.side_effect = lambda x, **kwargs: x  # Accept similarity_threshold
            mock_ai_class.return_value = mock_ai_instance
            
            mock_se_instance = MagicMock()
            mock_se_instance.test_connection.return_value = False
            mock_se_class.return_value = mock_se_instance
            
            mock_scorer_instance = MagicMock()
            # Return keywords with scores >= min_score (40)
            # CRITICAL: Must preserve all fields from input keywords
            def score_kw(keywords, **kwargs):
                result = []
                for i, k in enumerate(keywords):
                    scored = dict(k)  # Make a copy to preserve all fields
                    scored["score"] = 60 + i  # Add/update score (60-64, all >= 40)
                    result.append(scored)
                return result
            # Use AsyncMock for async method
            async def score_kw_async(keywords, **kwargs):
                return score_kw(keywords, **kwargs)
            mock_scorer_instance.score_keywords_async = AsyncMock(side_effect=score_kw_async)
            mock_scorer_instance.score_keywords.side_effect = score_kw
            # Preserve the static filter_by_score method
            mock_scorer_instance.filter_by_score = KeywordScorer.filter_by_score
            mock_scorer_class.return_value = mock_scorer_instance
            
            # Also ensure the filter method is accessible in the generator module
            import pipeline.keyword_generation.generator as gen_module
            gen_module.KeywordScorer.filter_by_score = KeywordScorer.filter_by_score
            
            gen = KeywordGeneratorV2()
            # Ensure mocks are assigned
            gen.ai_generator = mock_ai_instance
            gen.scorer = mock_scorer_instance
            gen.seranking_client = mock_se_instance
            
            yield gen
    
    @pytest.mark.asyncio
    async def test_generate_ai_only(self, generator, company_info, config):
        """Test generation with AI keywords only"""
        config.enable_gap_analysis = False
        
        # Ensure the generator uses the mocked instances
        # Use AsyncMock for async method
        generator.ai_generator.generate_seed_keywords_async = AsyncMock(return_value=[
            {
                "keyword": f"ai keyword {i}",
                "source": "ai_generated",
                "score": 0,
                "intent": "informational",
                "is_question": False,
                "word_count": 2,
            }
            for i in range(5)
        ])
        generator.ai_generator.generate_long_tail_variants.return_value = []  # No long-tail
        generator.ai_generator.deduplicate_keywords.side_effect = lambda x, **kwargs: x  # Accept similarity_threshold
        
        result = await generator.generate(company_info, config)
        
        assert result.statistics.total_keywords > 0
        assert result.statistics.ai_keywords == 5
        assert result.statistics.gap_keywords == 0
        assert result.primary_keyword is not None
    
    @pytest.mark.asyncio
    async def test_generate_with_gap_analysis(self, generator, company_info, config):
        """Test generation with gap analysis"""
        config.enable_gap_analysis = True
        
        # Setup AI generator
        generator.ai_generator.generate_seed_keywords.return_value = [
            {"keyword": f"ai keyword {i}", "source": "ai_generated", "score": 0}
            for i in range(5)
        ]
        generator.ai_generator.generate_long_tail_variants.return_value = []
        generator.ai_generator.deduplicate_keywords.side_effect = lambda x, **kwargs: x  # Accept similarity_threshold
        
        # Mock gap analysis
        generator.seranking_client.test_connection.return_value = True
        generator.seranking_client.extract_domain.return_value = 'test.com'
        generator.seranking_client.analyze_content_gaps.return_value = []
        
        with patch('pipeline.keyword_generation.generator.GapAnalyzerWrapper') as mock_wrapper:
            mock_wrapper.batch_convert_gaps.return_value = []
            
            result = await generator.generate(company_info, config)
            assert result.statistics.total_keywords > 0
    
    @pytest.mark.asyncio
    async def test_generate_merges_keywords(self, generator, company_info, config):
        """Test that keywords from both sources are merged"""
        config.enable_gap_analysis = True
        
        # Setup AI generator
        generator.ai_generator.generate_seed_keywords.return_value = [
            {"keyword": f"ai keyword {i}", "source": "ai_generated", "score": 0}
            for i in range(5)
        ]
        generator.ai_generator.generate_long_tail_variants.return_value = []
        generator.ai_generator.deduplicate_keywords.side_effect = lambda x, **kwargs: x  # Accept similarity_threshold
        
        # Setup gap analysis
        generator.seranking_client.test_connection.return_value = True
        generator.seranking_client.extract_domain.return_value = 'test.com'
        generator.seranking_client.analyze_content_gaps.return_value = []
        
        with patch('pipeline.keyword_generation.generator.GapAnalyzerWrapper') as mock_wrapper:
            mock_wrapper.batch_convert_gaps.return_value = [
                {
                    "keyword": f"gap keyword {i}",
                    "source": "gap_analysis",
                    "score": 0,
                    "intent": "informational",
                    "is_question": False,
                    "word_count": 2,
                }
                for i in range(5)
            ]
            
            result = await generator.generate(company_info, config)
            # Should have keywords from both sources
            assert result.statistics.ai_keywords == 5
            assert result.statistics.gap_keywords == 5


class TestGapAnalyzerWrapper:
    """Tests for GapAnalyzerWrapper"""
    
    def test_convert_gap_to_keyword_dict(self):
        """Test gap to keyword conversion"""
        gap = {
            "keyword": "test keyword",
            "aeo_score": 45.5,
            "volume": 1000,
            "difficulty": 30,
            "competitor": "competitor.com",
            "intent": "question"
        }
        
        kw_dict = GapAnalyzerWrapper.convert_gap_to_keyword_dict(gap)
        
        assert kw_dict["keyword"] == "test keyword"
        assert kw_dict["source"] == "gap_analysis"
        assert kw_dict["aeo_score"] == 45.5
        assert kw_dict["volume"] == 1000
        assert kw_dict["is_question"] is True
    
    def test_batch_convert_gaps(self):
        """Test batch conversion"""
        gaps = [
            {"keyword": "keyword1", "volume": 100},
            {"keyword": "keyword2", "volume": 200},
        ]
        
        converted = GapAnalyzerWrapper.batch_convert_gaps(gaps)
        assert len(converted) == 2
        assert all(kw["source"] == "gap_analysis" for kw in converted)
    
    def test_filter_by_score_range(self):
        """Test filtering by AEO score range"""
        keywords = [
            {"keyword": "high", "aeo_score": 80},
            {"keyword": "medium", "aeo_score": 50},
            {"keyword": "low", "aeo_score": 20},
        ]
        
        filtered = GapAnalyzerWrapper.filter_by_score_range(
            keywords, min_aeo_score=40, max_aeo_score=70
        )
        assert len(filtered) == 1
        assert filtered[0]["keyword"] == "medium"
    
    def test_sort_by_aeo_score(self):
        """Test sorting by AEO score"""
        keywords = [
            {"keyword": "low", "aeo_score": 20},
            {"keyword": "high", "aeo_score": 80},
            {"keyword": "medium", "aeo_score": 50},
        ]
        
        sorted_kw = GapAnalyzerWrapper.sort_by_aeo_score(keywords)
        assert sorted_kw[0]["keyword"] == "high"
        assert sorted_kw[-1]["keyword"] == "low"
    
    def test_get_statistics(self):
        """Test statistics calculation"""
        keywords = [
            {"keyword": "kw1", "aeo_score": 50, "volume": 100, "difficulty": 30, "intent": "question", "has_aeo_features": True},
            {"keyword": "kw2", "aeo_score": 60, "volume": 200, "difficulty": 40, "intent": "informational", "has_aeo_features": False},
        ]
        
        stats = GapAnalyzerWrapper.get_statistics(keywords)
        
        assert stats["total"] == 2
        assert stats["avg_aeo_score"] == 55.0
        assert stats["with_aeo_features"] == 1
        assert stats["question_keywords"] == 1

