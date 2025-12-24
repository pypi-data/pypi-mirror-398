from datetime import datetime
from typing import Generator

import json

from unittest.mock import MagicMock, patch, mock_open
import pytest

import arxiv
from arxiv import Client

from src.infrastructure.driven_adapters.http_client.arxiv_papers import ArxivPaper

def create_mock_result(entry_id: str, title: str, summary: str) -> arxiv.Result:
    """Create a mock arxiv Result object"""
    result = MagicMock(spec=arxiv.Result)
    result.entry_id = entry_id
    result.title = title
    result.summary = summary
    result.authors = [MagicMock(name="Test Author")]
    result.published = datetime(2023, 10, 1)
    result.updated = datetime(2023, 10, 2)
    result.pdf_url = f"https://arxiv.org/pdf/{entry_id}.pdf"
    return result

def create_mock_results_generator() -> Generator[arxiv.Result, None, None]:
    """Create a generator of mock arxiv Results"""
    results = [
        create_mock_result("1234.56789", "AI Paper 1", "Summary of AI paper 1"),
        create_mock_result("2345.67890", "AI Paper 2", "Summary of AI paper 2"),
        create_mock_result("3456.78901", "AI Paper 3", "Summary of AI paper 3")
    ]
    for result in results:
        yield result

@pytest.mark.asyncio
async def test_search_papers_success():
    """Test successful paper search and processing"""
    mock_client = MagicMock(spec=Client)
    mock_client.results.return_value = create_mock_results_generator()

    with patch("os.path.join", return_value="/tmp/test_papers"), \
         patch("os.makedirs") as mock_makedirs, \
         patch("builtins.open", mock_open()) as mock_file, \
         patch("os.path.exists", return_value=False), \
         patch('json.dump') as mock_json_dump:

        paper_adapter = ArxivPaper(mock_client, "/tmp")
        result = await paper_adapter.search_papers("llm", max_results=3)

        # Verify client was called with correct search
        mock_client.results.assert_called_once()

        # Verify directory creation
        mock_makedirs.assert_called_once_with("/tmp/test_papers", exist_ok=True)

        # Verify files were written (should be called 3 times for 3 papers)
        assert mock_file.call_count == 2

        # Verify JSON dump was called once
        mock_json_dump.assert_called_once()

        # Verify return type is list
        assert isinstance(result, list)

@pytest.mark.asyncio
async def test_extract_info_success():
    """Test successful information extraction from papers"""
    mock_client = MagicMock()
    papers_info = {
        "0906.5243v1": {
            "title": "Application of Monte Carlo-based statistical significance determinations to the Beta Cephei stars V400 Car, V401 Car, V403 Car and V405 Car",
            "authors": [
            "C. A. Engelbrecht",
            "F. A. M. Frescura",
            "B. S. Frank"
            ],
            "summary": "We have used Lomb-Scargle periodogram analysis and Monte Carlo significance\ntests to detect periodicities above the 3-sigma level in the Beta Cephei stars\nV400 Car, V401 Car, V403 Car and V405 Car. These methods produce six previously\nunreported periodicities in the expected frequency range of excited pulsations:\none in V400 Car, three in V401 Car, one in V403 Car and one in V405 Car. One of\nthese six frequencies is significant above the 4-sigma level. We provide\nstatistical significances for all of the periodicities found in these four\nstars.",
            "pdf_url": "http://arxiv.org/pdf/0906.5243v1",
            "published": "2009-06-29"
        },
        "2002.02070v1": {
            "title": "Understanding Car-Speak: Replacing Humans in Dealerships",
            "authors": [
            "Habeeb Hooshmand",
            "James Caverlee"
            ],
            "summary": "A large portion of the car-buying experience in the United States involves\ninteractions at a car dealership. At the dealership, the car-buyer relays their\nneeds to a sales representative. However, most car-buyers are only have an\nabstract description of the vehicle they need. Therefore, they are only able to\ndescribe their ideal car in \"car-speak\". Car-speak is abstract language that\npertains to a car's physical attributes. In this paper, we define car-speak. We\nalso aim to curate a reasonable data set of car-speak language. Finally, we\ntrain several classifiers in order to classify car-speak.",
            "pdf_url": "http://arxiv.org/pdf/2002.02070v1",
            "published": "2020-02-06"
        }
    }

    expected_file_path = "/tmp/llm/papers_info.json"

    with patch('builtins.open', mock_open()) as mock_file, \
         patch('json.load') as mock_json_load, \
         patch('os.path.join', side_effect=[
             '/tmp/llm',
             expected_file_path
        ]) as mock_join, \
         patch('os.listdir', return_value=["llm"]), \
         patch('os.path.isdir', return_value=True), \
         patch('os.path.isfile', return_value=True):

        mock_json_load.return_value = papers_info

        paper_adapter = ArxivPaper(mock_client, "/tmp")
        result = await paper_adapter.extract_info("0906.5243v1")

        # Verify JSON load was called with the correct file
        mock_json_load.assert_called_once_with(mock_file.return_value)

        # Verify file was opened with correct parameters
        mock_file.assert_called_once_with(expected_file_path, "r")

        # Verify os.path.join was called with the correct arguments
        mock_join.assert_any_call("/tmp", "llm")
        mock_join.assert_any_call("/tmp/llm", "papers_info.json")

        # Verify return value
        assert json.loads(result) == papers_info["0906.5243v1"]
