"""
Async HTTP clients for SemanticScholar and OpenAlex literature search APIs.
Both APIs are free and require no authentication key.

- SemanticScholar: https://api.semanticscholar.org/graph/v1/paper/search
- OpenAlex:        https://api.openalex.org/works
"""

from typing import Any, Dict, List
import httpx
from utils.logger import logger


class SemanticScholarClient:
    """Async client for the Semantic Scholar paper search API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    async def search(
        self,
        query: str,
        year_from: int,
        year_to: int,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers matching query, filtered to year_from–year_to.

        Returns:
            List of {title, abstract, year, citation_count, source} dicts.
            Returns [] on any error (timeout, rate limit, network issue).
        """
        params = {
            "query": query,
            "fields": "title,abstract,year,citationCount",
            "limit": limit,
            "year": f"{year_from}-{year_to}",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                papers = []
                for item in data.get("data", []):
                    papers.append({
                        "title": item.get("title") or "",
                        "abstract": item.get("abstract") or "",
                        "year": item.get("year"),
                        "citation_count": item.get("citationCount", 0),
                        "source": "SemanticScholar",
                    })
                return papers
        except Exception as e:
            logger.warning(f"SemanticScholar search failed for '{query}': {e}")
            return []


class OpenAlexClient:
    """Async client for the OpenAlex works search API."""

    BASE_URL = "https://api.openalex.org/works"

    async def search(
        self,
        query: str,
        year_from: int,
        year_to: int,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for works matching query, filtered to year_from–year_to.

        Note: OpenAlex abstracts are stored as an inverted index and are not
        returned here. Only title, year, and citation count are available.

        Returns:
            List of {title, abstract, year, citation_count, source} dicts.
            Returns [] on any error.
        """
        params = {
            "search": query,
            "filter": f"publication_year:{year_from}-{year_to}",
            "per-page": limit,
            "sort": "cited_by_count:desc",
            "select": "title,publication_year,cited_by_count",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                papers = []
                for item in data.get("results", []):
                    papers.append({
                        "title": item.get("title") or "",
                        "abstract": "",  # inverted-index format — not usable as plain text
                        "year": item.get("publication_year"),
                        "citation_count": item.get("cited_by_count", 0),
                        "source": "OpenAlex",
                    })
                return papers
        except Exception as e:
            logger.warning(f"OpenAlex search failed for '{query}': {e}")
            return []
