import json
from unittest.mock import patch, mock_open

import pytest

from src.infrastructure.driven_adapters.local_files.local_papers import LocalPaper, PAPER_DIR

@pytest.fixture(name="resource_paper")
def resource_paper_fixture():
    """Create ResourcePaper instance for testing"""
    return LocalPaper()

@pytest.mark.asyncio
async def test_get_available_folders_success(resource_paper):
    """Test successful retrieval of available folders"""
    mock_folders = ["machine_learning", "deep_learning", "computer_vision"]

    with patch('os.path.exists') as mock_exists, \
            patch('os.listdir', return_value=mock_folders) as mock_listdir, \
            patch('os.path.isdir', return_value=True) as _mock_isdir, \
            patch('os.path.join', side_effect=lambda *args: "/".join(args)):

        # Mock exists to return True for PAPER_DIR and papers_info.json files
        mock_exists.side_effect = lambda path: True

        result = await resource_paper.get_available_folders()

        # Verify the result contains expected content
        assert "# Available Topics" in result
        assert "machine_learning" in result
        assert "deep_learning" in result
        assert "computer_vision" in result
        assert "Use @" in result

        # Verify directory operations
        mock_listdir.assert_called_once_with(PAPER_DIR)

@pytest.mark.asyncio
async def test_get_topic_papers_success(resource_paper):
    """Test successful retrieval of topic papers"""
    topic = "machine learning"
    mock_papers_data = {
        "1234.56789": {
            "title": "Deep Learning Fundamentals",
            "authors": ["John Doe", "Jane Smith"],
            "published": "2023-10-01",
            "pdf_url": "https://arxiv.org/pdf/1234.56789.pdf",
            "summary": "This paper explores the fundamentals of deep learning algorithms and their applications in various domains."
        },
        "2345.67890": {
            "title": "Neural Networks Overview",
            "authors": ["Alice Johnson"],
            "published": "2023-09-15",
            "pdf_url": "https://arxiv.org/pdf/2345.67890.pdf",
            "summary": "An comprehensive overview of neural network architectures and their practical implementations."
        }
    }

    with patch('os.path.exists', return_value=True), \
            patch('os.path.join', side_effect=lambda *args: "/".join(args)), \
            patch('builtins.open', mock_open(read_data=json.dumps(mock_papers_data))):

        result = await resource_paper.get_topic_papers(topic)

        # Verify content structure
        assert "# Papers on Machine Learning" in result
        assert "Total papers: 2" in result
        assert "Deep Learning Fundamentals" in result
        assert "Neural Networks Overview" in result
        assert "John Doe, Jane Smith" in result
        assert "Alice Johnson" in result
        assert "1234.56789" in result
        assert "2345.67890" in result
