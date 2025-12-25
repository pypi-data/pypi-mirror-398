import requests
from loguru import logger


class GitHubAPIClient:
    """GitHub API client for fetching commits."""

    BASE_URL = "https://api.github.com"
    API_VERSION = "2022-11-28"

    def __init__(self, token: str | None = None, proxies: dict | None = None) -> None:
        self.token = token
        self.proxies = proxies or {}

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.API_VERSION,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get_commits(self, repo: str, per_page: int = 30) -> list[dict]:
        """Fetch commits from a GitHub repository.

        Args:
            repo: Repository path (e.g., 'owner/repo')
            per_page: Number of commits to fetch (default 30)

        Returns:
            List of commit objects from GitHub API

        Raises:
            Exception: If API request fails
        """
        url = f"{self.BASE_URL}/repos/{repo}/commits"
        params = {"per_page": per_page}

        logger.debug(f"Fetching commits from {repo}")
        response = requests.get(
            url,
            headers=self._get_headers(),
            params=params,
            proxies=self.proxies,
        )

        if response.ok:
            commits = response.json()
            logger.debug(f"Fetched {len(commits)} commits from {repo}")
            return commits
        else:
            logger.error(f"Failed to fetch commits from {repo}: {response.text}")
            raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
