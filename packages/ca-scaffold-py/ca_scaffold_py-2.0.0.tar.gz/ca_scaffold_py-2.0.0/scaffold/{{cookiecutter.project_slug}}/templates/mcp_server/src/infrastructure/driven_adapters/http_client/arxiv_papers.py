import json
import os
from typing import List
import arxiv

from src.domain.model.paper.gateway.paper_repository import PaperRepository


class ArxivPaper(PaperRepository):
    def __init__(self, client: arxiv.Client,  paper_dir: str = "arXiv-papers"):
        """
        Initialize the ArxivPaper tool with a specific arxiv client and directory.

        Args:
            arxiv: An instance of arxiv.Client to interact with the arXiv API
            paper_dir: Directory to store paper information (default: "arXiv-papers")
        """
        self.client = client
        self.paper_dir = paper_dir

    async def search_papers(
            self, topic: str, max_results: int = 5) -> List[str]:
        """
        Search for papers on arXiv based on a topic and store their information.

        Args:
            topic: The topic to search for
            max_results: Maximum number of results to retrieve (default: 5)

        Returns:
            List of paper IDs found in the search
        """

        # Search for the most relevant articles matching the queried topic
        search = arxiv.Search(
            query=topic,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        papers = self.client.results(search)

        # Create directory for this topic
        path = os.path.join(self.paper_dir, topic.lower().replace(" ", "_"))
        os.makedirs(path, exist_ok=True)

        file_path = os.path.join(path, "papers_info.json")

        # Try to load existing papers info
        try:
            with open(file_path, "r") as json_file:
                papers_info = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            papers_info = {}

        # Process each paper and add to papers_info
        paper_ids = []
        for paper in papers:
            paper_ids.append(paper.get_short_id())
            paper_info = {
                'title': paper.title,
                'authors': [author.name for author in paper.authors],
                'summary': paper.summary,
                'pdf_url': paper.pdf_url,
                'published': str(paper.published.date())
            }
            papers_info[paper.get_short_id()] = paper_info

        # Save updated papers_info to json file
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(papers_info, json_file, indent=2)

        print(f"Results are saved in: {file_path}")

        return paper_ids

    async def extract_info(self, paper_id: str) -> str:
        """
        Search for information about a specific paper across all topic directories.

        Args:
            paper_id: The ID of the paper to look for

        Returns:
            JSON string with paper information if found, error message if not found
        """

        for item in os.listdir(self.paper_dir):
            item_path = os.path.join(self.paper_dir, item)
            if os.path.isdir(item_path):
                file_path = os.path.join(item_path, "papers_info.json")
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, "r") as json_file:
                            papers_info = json.load(json_file)
                            if paper_id in papers_info:
                                return json.dumps(
                                    papers_info[paper_id],
                                    indent=2)
                    except (FileNotFoundError, json.JSONDecodeError) as e:
                        print(f"Error reading {file_path}: {str(e)}")
                        continue

        return f"There's no saved information related to paper {paper_id}."
