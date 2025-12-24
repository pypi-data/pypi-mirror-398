import pytest
from src.infrastructure.driven_adapters.prompts.papers import PromptPaper

@pytest.fixture(name="prompt_paper")
def prompt_paper_fixture():
    """Create PromptPaper instance for testing"""
    return PromptPaper()

@pytest.mark.asyncio
async def test_generate_search_prompt_default_params(prompt_paper):
    """Test prompt generation with default parameters"""
    topic = "machine learning"

    result = await prompt_paper.generate_search_prompt(topic)

    # Verify basic structure
    assert isinstance(result, str)
    assert len(result) > 0

    # Verify topic is included
    assert topic in result
    assert f"'{topic}'" in result

    # Verify default num_papers (5) is used
    assert "5 academic papers" in result
    assert "max_results=5" in result

    # Verify key instructions are present
    assert "search_papers" in result
    assert "Paper title" in result
    assert "Authors" in result
    assert "Publication date" in result
    assert "Brief summary" in result
    assert "Main contributions" in result
    assert "Methodologies used" in result
