"""Tests for every tool. Apify is never called: httpx.post is replaced with a fake that
records the request and returns canned dataset rows."""

import asyncio

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from gulf_data_mcp import server as srv

ROWS = [{"ok": True}]


class FakeResponse:
    def __init__(self, status_code=200, rows=ROWS, text=""):
        self.status_code = status_code
        self._rows = rows
        self.text = text

    def json(self):
        return self._rows


@pytest.fixture
def apify(monkeypatch):
    """Set a token and capture each request sent to Apify."""
    monkeypatch.setenv("APIFY_TOKEN", "test-token")
    calls = []

    def fake_post(url, params=None, json=None, headers=None, timeout=None):
        calls.append({"url": url, "params": params, "json": json, "headers": headers})
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    return calls


def actor_url(actor):
    return srv.APIFY.format(actor=actor)


def test_dubai_property_transactions(apify):
    assert srv.dubai_property_transactions("2026-10-01", "2026-10-31", "mortgages") == ROWS
    call = apify[0]
    assert call["url"] == actor_url("dld-transactions-scraper")
    assert call["json"] == {"transactionType": "mortgages", "fromDate": "2026-10-01", "toDate": "2026-10-31"}


def test_gulf_jobs(apify):
    assert srv.gulf_jobs(["data analyst"], country="qatar", max_jobs_per_source=5) == ROWS
    call = apify[0]
    assert call["url"] == actor_url("gcc-jobs-aggregator")
    assert call["json"] == {"keywords": ["data analyst"], "country": "qatar", "maxJobsPerSource": 5}


def test_gold_price(apify):
    assert srv.gold_price(["PKR"], include_history=True, history_range="1y") == ROWS
    body = apify[0]["json"]
    assert apify[0]["url"] == actor_url("gold-price-scraper")
    assert body["currencies"] == ["PKR"]
    assert body["metals"] == ["gold", "silver"]
    assert body["getHistory"] is True and body["historyRange"] == "1y"


def test_amazon_best_sellers(apify):
    assert srv.amazon_best_sellers("sa", ["kitchen"], "new-releases", 10) == ROWS
    call = apify[0]
    assert call["url"] == actor_url("amazon-ae-scraper")
    assert call["json"] == {"amazonDomain": "sa", "bestSellerCategories": ["kitchen"],
                            "rankingList": "new-releases", "maxProducts": 10}


def test_noon_products(apify):
    assert srv.noon_products("iphone 17", country="egypt", max_products=3) == ROWS
    call = apify[0]
    assert call["url"] == actor_url("noon-scraper")
    assert call["json"] == {"searchTerms": ["iphone 17"], "noonDomain": "egypt-en", "maxProducts": 3}
    assert call["params"]["limit"] == 3


def test_web_search(apify):
    assert srv.web_search("dubai metro blue line", max_results=2) == ROWS
    body = apify[0]["json"]
    assert apify[0]["url"] == actor_url("ai-web-search-scraper")
    assert body["queries"] == ["dubai metro blue line"]
    assert body["engine"] == "duckduckgo" and body["maxResults"] == 2


def test_web_to_markdown(apify):
    assert srv.web_to_markdown(["https://example.com"], crawl_site=True, max_pages=4) == ROWS
    body = apify[0]["json"]
    assert apify[0]["url"] == actor_url("llm-web-scraper")
    assert body["startUrls"] == [{"url": "https://example.com"}]
    assert body["crawl"] is True and body["maxPages"] == 4


def test_sends_token_as_bearer(apify):
    srv.gold_price()
    assert apify[0]["headers"] == {"Authorization": "Bearer test-token"}
    assert apify[0]["params"] == {"clean": "true"}


def test_missing_token_raises(monkeypatch):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    with pytest.raises(ToolError, match="APIFY_TOKEN"):
        srv.gold_price()


def test_apify_error_raises(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test-token")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: FakeResponse(402, text="Not enough credit"))
    with pytest.raises(ToolError, match="HTTP 402"):
        srv.gold_price()


def test_every_tool_is_annotated_read_only():
    tools = asyncio.run(srv.server.list_tools())
    assert len(tools) == 7
    for tool in tools:
        a = tool.annotations
        assert (a.read_only_hint, a.destructive_hint, a.idempotent_hint, a.open_world_hint) == \
            (True, False, True, True), tool.name
