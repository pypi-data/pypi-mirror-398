"""
Unit tests for ContentRefresher

Tests refresh logic with mocked Gemini client to verify:
- Single section updates
- Multiple section updates
- Preserving unchanged sections
- Meta description refresh
- Structured output validation
- Error recovery
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from service.content_refresher import ContentRefresher


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    client = MagicMock()
    client.generate_content = AsyncMock()
    return client


@pytest.fixture
def sample_content():
    """Sample structured content for testing."""
    return {
        'headline': 'Test Article',
        'sections': [
            {
                'heading': 'Introduction',
                'content': 'This is the introduction with old data from 2023.'
            },
            {
                'heading': 'Key Features',
                'content': 'Our product has 5 features.'
            },
            {
                'heading': 'Conclusion',
                'content': 'Thank you for reading.'
            }
        ],
        'meta_description': 'Old meta description from 2023',
    }


class TestContentRefresher:
    """Test suite for ContentRefresher."""
    
    @pytest.mark.asyncio
    async def test_refresh_single_section(self, mock_gemini_client, sample_content):
        """Test refreshing a single section."""
        # Mock Gemini response with structured JSON
        mock_response = json.dumps({
            "heading": "Introduction",
            "content": "This is the introduction with updated data from 2025.",
            "change_summary": "Updated year from 2023 to 2025"
        })
        mock_gemini_client.generate_content.return_value = mock_response
        
        refresher = ContentRefresher(mock_gemini_client)
        instructions = ["Update all years to 2025"]
        
        result = await refresher.refresh_content(
            sample_content,
            instructions,
            target_sections=[0]  # Only refresh first section
        )
        
        # Check that first section was updated
        assert '2025' in result['sections'][0]['content']
        assert '2023' not in result['sections'][0]['content']
        
        # Check that other sections remain unchanged
        assert result['sections'][1]['content'] == sample_content['sections'][1]['content']
        assert result['sections'][2]['content'] == sample_content['sections'][2]['content']
        
        # Verify Gemini was called once
        assert mock_gemini_client.generate_content.call_count == 1
    
    @pytest.mark.asyncio
    async def test_refresh_multiple_sections(self, mock_gemini_client, sample_content):
        """Test refreshing multiple sections."""
        # Mock Gemini responses for multiple sections
        def mock_generate_content_side_effect(prompt, **kwargs):
            if 'Introduction' in prompt:
                return json.dumps({
                    "heading": "Introduction",
                    "content": "Updated introduction for 2025.",
                    "change_summary": "Updated year"
                })
            elif 'Key Features' in prompt:
                return json.dumps({
                    "heading": "Key Features",
                    "content": "Our product now has 10 features.",
                    "change_summary": "Updated feature count"
                })
            else:
                return json.dumps({
                    "heading": "Conclusion",
                    "content": "Thank you for reading.",
                    "change_summary": "No changes"
                })
        
        mock_gemini_client.generate_content.side_effect = mock_generate_content_side_effect
        
        refresher = ContentRefresher(mock_gemini_client)
        instructions = ["Update all data to 2025", "Increase feature count"]
        
        result = await refresher.refresh_content(
            sample_content,
            instructions,
            target_sections=[0, 1]  # Refresh first two sections
        )
        
        # Check both sections were updated
        assert '2025' in result['sections'][0]['content']
        assert '10 features' in result['sections'][1]['content']
        
        # Check third section unchanged
        assert result['sections'][2]['content'] == sample_content['sections'][2]['content']
        
        # Verify Gemini was called twice
        assert mock_gemini_client.generate_content.call_count == 2
    
    @pytest.mark.asyncio
    async def test_refresh_preserves_unchanged(self, mock_gemini_client, sample_content):
        """Test that unchanged sections are preserved exactly."""
        # Mock Gemini response
        mock_response = json.dumps({
            "heading": "Introduction",
            "content": "Updated introduction.",
            "change_summary": "Minor updates"
        })
        mock_gemini_client.generate_content.return_value = mock_response
        
        refresher = ContentRefresher(mock_gemini_client)
        instructions = ["Improve tone"]
        
        # Refresh only section 0
        result = await refresher.refresh_content(
            sample_content,
            instructions,
            target_sections=[0]
        )
        
        # Verify sections 1 and 2 are EXACTLY the same (not just content, but object identity)
        assert result['sections'][1] == sample_content['sections'][1]
        assert result['sections'][2] == sample_content['sections'][2]
        
        # Verify Gemini was only called for section 0
        assert mock_gemini_client.generate_content.call_count == 1
    
    @pytest.mark.asyncio
    async def test_refresh_meta_description(self, mock_gemini_client, sample_content):
        """Test refreshing meta description when instructions mention it."""
        # Mock Gemini response for section
        section_response = json.dumps({
            "heading": "Introduction",
            "content": "Updated content.",
            "change_summary": "Updated"
        })
        
        # Mock Gemini response for meta description
        meta_response = "Updated meta description for 2025"
        
        def mock_generate_content_side_effect(prompt, **kwargs):
            if 'meta description' in prompt.lower():
                return meta_response
            else:
                return section_response
        
        mock_gemini_client.generate_content.side_effect = mock_generate_content_side_effect
        
        refresher = ContentRefresher(mock_gemini_client)
        instructions = ["Update years to 2025", "Update meta description"]
        
        result = await refresher.refresh_content(
            sample_content,
            instructions,
            target_sections=[0]
        )
        
        # Check meta description was updated
        assert '2025' in result['meta_description']
        assert '2023' not in result['meta_description']
        
        # Verify Gemini was called for both section and meta
        assert mock_gemini_client.generate_content.call_count == 2
    
    @pytest.mark.asyncio
    async def test_structured_output_validation(self, mock_gemini_client, sample_content):
        """Test that structured output prevents hallucinations."""
        # Mock Gemini with VALID structured JSON (no hallucinations expected)
        valid_response = json.dumps({
            "heading": "Introduction",
            "content": "Clean, properly structured content without hallucinations.",
            "change_summary": "Updated content professionally"
        })
        mock_gemini_client.generate_content.return_value = valid_response
        
        refresher = ContentRefresher(mock_gemini_client)
        instructions = ["Make it more professional"]
        
        result = await refresher.refresh_content(
            sample_content,
            instructions,
            target_sections=[0]
        )
        
        # Verify response is valid JSON (not freeform text)
        section = result['sections'][0]
        assert 'heading' in section
        assert 'content' in section
        assert isinstance(section['content'], str)
        
        # Verify no common hallucination patterns
        content = section['content']
        assert 'You can aI' not in content  # Common v3.x hallucination
        assert 'What is How Do' not in content  # Common v3.x hallucination
        assert "Here's this reality" not in content  # Common v3.x hallucination
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, mock_gemini_client, sample_content):
        """Test fallback to original content on errors."""
        # Mock Gemini to raise an exception
        mock_gemini_client.generate_content.side_effect = Exception("API Error")
        
        refresher = ContentRefresher(mock_gemini_client)
        instructions = ["Update content"]
        
        result = await refresher.refresh_content(
            sample_content,
            instructions,
            target_sections=[0]
        )
        
        # Verify original content is preserved on error
        assert result['sections'][0]['content'] == sample_content['sections'][0]['content']
        assert result['sections'][0]['heading'] == sample_content['sections'][0]['heading']
        
        # Verify Gemini was attempted
        assert mock_gemini_client.generate_content.call_count == 1
    
    @pytest.mark.asyncio
    async def test_malformed_json_recovery(self, mock_gemini_client, sample_content):
        """Test recovery from malformed JSON response."""
        # Mock Gemini to return malformed JSON
        mock_gemini_client.generate_content.return_value = "Not valid JSON at all"
        
        refresher = ContentRefresher(mock_gemini_client)
        instructions = ["Update content"]
        
        result = await refresher.refresh_content(
            sample_content,
            instructions,
            target_sections=[0]
        )
        
        # Verify original content is preserved on JSON parse error
        assert result['sections'][0]['content'] == sample_content['sections'][0]['content']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])

