from pathlib import Path
from typing import Any

import pytest
import requests

from src.fetcher import FetchError, PoliteFetcher


class FakeResponse:
    def __init__(self, status_code: int, text: str = "<html>ok</html>") -> None:
        self.status_code = status_code
        self.text = text
        self.content = text.encode("utf-8")


class FakeSession:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[dict[str, object]] = []

    def get(self, url: str, **kwargs: object) -> Any:
        self.calls.append({"url": url, **kwargs})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make_fetcher(
    tmp_path: Path,
    session: FakeSession,
    *,
    sleep_calls: list[float] | None = None,
) -> PoliteFetcher:
    calls = sleep_calls if sleep_calls is not None else []
    return PoliteFetcher(
        cache_dir=tmp_path,
        user_agent="FlyRankInternship-A9/1.0 (student assignment)",
        session=session,
        sleep_fn=calls.append,
        monotonic_fn=lambda: 0.0,
    )


def test_successful_response_is_cached_and_reused(tmp_path: Path) -> None:
    session = FakeSession([FakeResponse(200, "<html>book list</html>")])
    fetcher = make_fetcher(tmp_path, session)

    first = fetcher.fetch("https://example.test/page", "catalogue/page-1.html")
    second = fetcher.fetch("https://example.test/page", "catalogue/page-1.html")

    assert first == "<html>book list</html>"
    assert second == first
    assert len(session.calls) == 1
    assert fetcher.stats.pages_fetched == 1
    assert fetcher.stats.cache_hits == 1


def test_empty_cache_file_is_refetched(tmp_path: Path) -> None:
    cache_file = tmp_path / "catalogue" / "page-1.html"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text("", encoding="utf-8")
    session = FakeSession([FakeResponse(200, "<html>fresh</html>")])
    fetcher = make_fetcher(tmp_path, session)

    assert fetcher.fetch("https://example.test/page", "catalogue/page-1.html") == "<html>fresh</html>"
    assert len(session.calls) == 1


def test_request_has_identity_and_timeout(tmp_path: Path) -> None:
    session = FakeSession([FakeResponse(200)])
    fetcher = make_fetcher(tmp_path, session)

    fetcher.fetch("https://example.test/page", "page.html")

    assert session.calls[0]["headers"] == {
        "User-Agent": "FlyRankInternship-A9/1.0 (student assignment)"
    }
    assert session.calls[0]["timeout"] == 10.0


def test_response_uses_detected_utf8_instead_of_latin1_default(tmp_path: Path) -> None:
    response = requests.Response()
    response.status_code = 200
    response._content = "<p class='price_color'>£51.77</p>".encode("utf-8")
    response.encoding = "ISO-8859-1"
    session = FakeSession([response])
    fetcher = make_fetcher(tmp_path, session)

    html = fetcher.fetch("https://example.test/book", "book.html")

    assert "£51.77" in html
    assert "Â£" not in html


def test_two_real_requests_are_spaced_by_half_a_second(tmp_path: Path) -> None:
    session = FakeSession([FakeResponse(200), FakeResponse(200)])
    sleep_calls: list[float] = []
    fetcher = make_fetcher(tmp_path, session, sleep_calls=sleep_calls)

    fetcher.fetch("https://example.test/one", "one.html")
    fetcher.fetch("https://example.test/two", "two.html")

    assert sleep_calls == [0.5]


@pytest.mark.parametrize("first_failure", [FakeResponse(500), requests.Timeout("slow")])
def test_timeout_and_server_error_are_retried_once(
    tmp_path: Path, first_failure: object
) -> None:
    session = FakeSession([first_failure, FakeResponse(200, "recovered")])
    fetcher = make_fetcher(tmp_path, session)

    assert fetcher.fetch("https://example.test/page", "page.html") == "recovered"
    assert len(session.calls) == 2


@pytest.mark.parametrize("status", [403, 404])
def test_forbidden_and_missing_pages_are_not_retried(tmp_path: Path, status: int) -> None:
    session = FakeSession([FakeResponse(status)])
    fetcher = make_fetcher(tmp_path, session)

    with pytest.raises(FetchError, match=str(status)):
        fetcher.fetch("https://example.test/page", "page.html")

    assert len(session.calls) == 1
