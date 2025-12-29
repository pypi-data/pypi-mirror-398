from git_miner.search.query import SearchOptions, SearchQueryBuilder


def test_search_query_builder_basic():
    builder = SearchQueryBuilder()
    query = builder.query("python").build()
    assert query == "python"


def test_search_query_builder_language():
    builder = SearchQueryBuilder()
    query = builder.query("web").language("python").build()
    assert "language:python" in query
    assert "web" in query


def test_search_query_builder_stars():
    builder = SearchQueryBuilder()
    query = builder.stars(min_stars=100, max_stars=1000).build()
    assert "stars:100..1000" in query


def test_search_query_builder_min_stars():
    builder = SearchQueryBuilder()
    query = builder.stars(min_stars=100).build()
    assert "stars:>=100" in query


def test_search_query_builder_forks():
    builder = SearchQueryBuilder()
    query = builder.forks(min_forks=10, max_forks=100).build()
    assert "forks:10..100" in query


def test_search_query_builder_license():
    builder = SearchQueryBuilder()
    query = builder.license("mit").build()
    assert "license:mit" in query


def test_search_query_builder_topics():
    builder = SearchQueryBuilder()
    query = builder.topic("machine-learning").build()
    assert "topic:machine-learning" in query


def test_search_query_builder_fork():
    builder = SearchQueryBuilder()
    query = builder.is_fork(True).build()
    assert "fork:true" in query


def test_search_query_builder_no_fork():
    builder = SearchQueryBuilder()
    query = builder.is_fork(False).build()
    assert "fork:false" in query


def test_search_query_builder_archived():
    builder = SearchQueryBuilder()
    query = builder.is_archived(True).build()
    assert "archived:true" in query


def test_search_query_builder_complex():
    builder = (
        SearchQueryBuilder()
        .query("web framework")
        .language("python")
        .stars(min_stars=1000)
        .license("mit")
        .is_fork(False)
    )
    query = builder.build()
    assert "web framework" in query
    assert "language:python" in query
    assert "stars:>=1000" in query
    assert "license:mit" in query
    assert "fork:false" in query


def test_search_options_default():
    options = SearchOptions()
    assert options.sort is None
    assert options.order == "desc"
    assert options.per_page == 100
    assert options.max_results is None


def test_search_options_custom():
    options = SearchOptions(sort="stars", order="asc", per_page=50, max_results=200)
    assert options.sort == "stars"
    assert options.order == "asc"
    assert options.per_page == 50
    assert options.max_results == 200


def test_search_options_per_page_limit():
    options = SearchOptions(per_page=150)
    assert options.per_page == 100
