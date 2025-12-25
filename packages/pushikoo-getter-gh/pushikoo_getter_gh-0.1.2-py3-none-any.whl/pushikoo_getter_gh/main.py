from datetime import datetime

from dateutil import tz
from loguru import logger
from pushikoo_interface import Detail, Getter

from pushikoo_getter_gh.api import GitHubAPIClient
from pushikoo_getter_gh.config import AdapterConfig, InstanceConfig


class GithubGetter(Getter[AdapterConfig, InstanceConfig]):
    """GitHub commits getter adapter."""

    def __init__(self) -> None:
        self._commit_cache: dict[str, dict] = {}
        self.repo = self.instance_config.repo

        logger.debug(f"{self.adapter_name}.{self.identifier} initialized for repo {self.repo}")

    def _create_api(self) -> GitHubAPIClient:
        """Create API client instance with current config (supports hot-reload)."""
        # Get the token from adapter config using instance config key
        token_key = self.instance_config.auth
        token = self.config.auth.get(token_key, "")
        return GitHubAPIClient(
            token=token if token else None,
            proxies=self.ctx.get_proxies(),
        )

    def timeline(self) -> list[str]:
        """Fetch commit list and return SHA identifiers."""
        if not self.instance_config.commit:
            logger.debug(f"Commit monitoring disabled for {self.identifier}")
            return []

        api = self._create_api()
        commits = api.get_commits(self.repo)

        # Cache commits for detail retrieval
        self._commit_cache.clear()
        for commit in commits:
            sha = commit.get("sha")
            if sha:
                self._commit_cache[sha] = commit

        return list(self._commit_cache.keys())

    def _parse_timestamp(self, date_str: str) -> int:
        """Parse GitHub timestamp to Unix timestamp."""
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        dt = dt.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
        return int(dt.timestamp())

    def _get_commit(self, sha: str) -> dict:
        """Get commit from cache."""
        if sha not in self._commit_cache:
            raise KeyError(f"Commit {sha} not found in cache")
        return self._commit_cache[sha]

    def detail(self, identifier: str) -> Detail:
        """Get detail of a single commit."""
        commit = self._get_commit(identifier)

        commit_data = commit.get("commit", {})
        time_str = commit_data.get("committer", {}).get("date", "")
        ts = self._parse_timestamp(time_str) if time_str else 0
        author = commit_data.get("author", {}).get("name", "")
        message = commit_data.get("message", "")
        url = f"https://github.com/{self.repo}/commit/{identifier}"

        return Detail(
            ts=ts,
            content=message,
            title=f"Github仓库{self.repo}产生了新的提交",
            author_name=author,
            url=url,
            image=[],
            extra_detail=[],
            detail={},
        )

    def details(self, identifiers: list[str]) -> Detail:
        """Get aggregated detail of multiple commits."""
        if not identifiers:
            raise ValueError("No identifiers provided")

        contents = []
        urls = []
        ts = 0
        author = ""

        for sha in identifiers:
            commit = self._get_commit(sha)
            commit_data = commit.get("commit", {})

            time_str = commit_data.get("committer", {}).get("date", "")
            if time_str:
                ts = self._parse_timestamp(time_str)

            author = commit_data.get("author", {}).get("name", "")
            message = commit_data.get("message", "")
            url = f"https://github.com/{self.repo}/commit/{sha}"

            contents.append(message)
            urls.append(url)

        return Detail(
            ts=ts,
            content="\n".join(contents),
            title=f"Github仓库{self.repo}产生了新的提交",
            author_name=author,
            url="\n".join(urls),
            image=[],
            extra_detail=[],
            detail={},
        )
