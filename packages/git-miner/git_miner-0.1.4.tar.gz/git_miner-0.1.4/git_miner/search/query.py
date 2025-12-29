from datetime import datetime


class SearchQueryBuilder:
    """Builds GitHub repository search queries."""

    def __init__(self):
        self._terms: list[str] = []
        self._filters: list[str] = []

    def query(self, term: str) -> "SearchQueryBuilder":
        """Add a search term."""
        self._terms.append(term)
        return self

    def language(self, language: str) -> "SearchQueryBuilder":
        """Filter by programming language."""
        self._filters.append(f"language:{language}")
        return self

    def stars(
        self, min_stars: int | None = None, max_stars: int | None = None
    ) -> "SearchQueryBuilder":
        """Filter by star count range."""
        if min_stars is not None and max_stars is not None:
            self._filters.append(f"stars:{min_stars}..{max_stars}")
        elif min_stars is not None:
            self._filters.append(f"stars:>={min_stars}")
        elif max_stars is not None:
            self._filters.append(f"stars:<={max_stars}")
        return self

    def forks(
        self, min_forks: int | None = None, max_forks: int | None = None
    ) -> "SearchQueryBuilder":
        """Filter by fork count range."""
        if min_forks is not None and max_forks is not None:
            self._filters.append(f"forks:{min_forks}..{max_forks}")
        elif min_forks is not None:
            self._filters.append(f"forks:>={min_forks}")
        elif max_forks is not None:
            self._filters.append(f"forks:<={max_forks}")
        return self

    def license(self, license_type: str) -> "SearchQueryBuilder":
        """Filter by license type."""
        self._filters.append(f"license:{license_type}")
        return self

    def created_after(self, date: datetime | str) -> "SearchQueryBuilder":
        """Filter by creation date after given date."""
        date_str = date if isinstance(date, str) else date.strftime("%Y-%m-%d")
        self._filters.append(f"created:>{date_str}")
        return self

    def created_before(self, date: datetime | str) -> "SearchQueryBuilder":
        """Filter by creation date before given date."""
        date_str = date if isinstance(date, str) else date.strftime("%Y-%m-%d")
        self._filters.append(f"created:<{date_str}")
        return self

    def updated_after(self, date: datetime | str) -> "SearchQueryBuilder":
        """Filter by last update date after given date."""
        date_str = date if isinstance(date, str) else date.strftime("%Y-%m-%d")
        self._filters.append(f"updated:>{date_str}")
        return self

    def updated_before(self, date: datetime | str) -> "SearchQueryBuilder":
        """Filter by last update date before given date."""
        date_str = date if isinstance(date, str) else date.strftime("%Y-%m-%d")
        self._filters.append(f"updated:<{date_str}")
        return self

    def topic(self, topic: str) -> "SearchQueryBuilder":
        """Filter by topic/tag."""
        self._filters.append(f"topic:{topic}")
        return self

    def is_fork(self, value: bool = True) -> "SearchQueryBuilder":
        """Filter for forks or non-forks."""
        self._filters.append("fork:true" if value else "fork:false")
        return self

    def is_archived(self, value: bool = True) -> "SearchQueryBuilder":
        """Filter for archived repositories."""
        self._filters.append("archived:true" if value else "archived:false")
        return self

    def size(
        self, min_size: int | None = None, max_size: int | None = None
    ) -> "SearchQueryBuilder":
        """Filter by repository size in KB."""
        if min_size is not None and max_size is not None:
            self._filters.append(f"size:{min_size}..{max_size}")
        elif min_size is not None:
            self._filters.append(f"size:>={min_size}")
        elif max_size is not None:
            self._filters.append(f"size:<={max_size}")
        return self

    def custom_filter(self, filter_str: str) -> "SearchQueryBuilder":
        """Add a custom filter string."""
        self._filters.append(filter_str)
        return self

    def build(self) -> str:
        """Build the final search query string."""
        query_parts = self._terms + self._filters
        return " ".join(query_parts) if query_parts else ""


class SearchOptions:
    """Options for repository search."""

    def __init__(
        self,
        sort: str | None = None,
        order: str = "desc",
        per_page: int = 100,
        max_results: int | None = None,
    ):
        self.sort = sort
        self.order = order
        self.per_page = min(per_page, 100)
        self.max_results = max_results
