"""Gulf Data MCP server: Middle East market data and LLM-ready web data for AI agents.

Each tool runs a ready-made scraper (Apify Actor by get_anything) on the user's own
Apify account and returns the dataset rows. Set APIFY_TOKEN to your Apify API token
(https://console.apify.com/settings/integrations). You pay Apify's per-result price
for each tool call; Apify's free plan includes monthly credit.
"""

import os
from typing import Any, Literal

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

APIFY = "https://api.apify.com/v2/acts/get_anything~{actor}/run-sync-get-dataset-items"
TIMEOUT = 300  # run-sync waits up to 5 minutes for the run to finish

# Every tool only reads public web data: nothing is created, changed or deleted.
READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False,
                            idempotent_hint=True, open_world_hint=True)

server = MCPServer(
    name="gulf-data",
    title="Gulf Data",
    instructions=(
        "Live data for the Gulf and Middle East (Dubai property transactions, Gulf jobs, "
        "gold prices, Amazon and Noon products) plus web search and web-page-to-Markdown "
        "for grounding answers. Every call runs a paid-per-result scraper on the user's "
        "Apify account, so request only as many results as the question needs."
    ),
    website_url="https://getanything-site.vercel.app",
)


def run_actor(actor: str, run_input: dict[str, Any], limit: int | None = None) -> list[dict[str, Any]]:
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise ToolError("Set the APIFY_TOKEN environment variable to your Apify API token "
                           "(https://console.apify.com/settings/integrations).")
    params: dict[str, Any] = {"clean": "true"}
    if limit:
        params["limit"] = limit
    resp = httpx.post(APIFY.format(actor=actor), params=params, json=run_input,
                      headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)
    if resp.status_code >= 400:
        raise ToolError(f"Apify returned HTTP {resp.status_code}: {resp.text[:300]}")
    return resp.json()


@server.tool(annotations=READ_ONLY)
def dubai_property_transactions(
    from_date: str,
    to_date: str,
    transaction_type: Literal["sales", "mortgages", "gifts"] = "sales",
) -> list[dict[str, Any]]:
    """Official Dubai Land Department (DLD) registered property transactions for a date range,
    aggregated by community, property type, sub-type (flat, villa, office...) and first sale vs
    resale: transaction count, total value (AED), total area, price per sqm, average price.
    Dates are YYYY-MM-DD. English and Arabic names. Source: dubailand.gov.ae public data."""
    return run_actor("dld-transactions-scraper",
                     {"transactionType": transaction_type, "fromDate": from_date, "toDate": to_date})


@server.tool(annotations=READ_ONLY)
def gulf_jobs(
    keywords: list[str],
    country: Literal["uae", "saudi-arabia", "qatar", "kuwait", "bahrain", "oman"] = "uae",
    max_jobs_per_source: int = 20,
) -> list[dict[str, Any]]:
    """Current job listings in a Gulf country from LinkedIn, NaukriGulf, Bayt and GulfTalent in one
    search, with duplicates merged. Each job has title, company, location, posted date, the boards
    it appears on with links, seniority and job function. Bayt and GulfTalent are best effort."""
    return run_actor("gcc-jobs-aggregator",
                     {"keywords": keywords, "country": country, "maxJobsPerSource": max_jobs_per_source})


@server.tool(annotations=READ_ONLY)
def gold_price(
    currencies: list[str] = ["AED", "INR", "SAR", "USD"],
    include_history: bool = False,
    history_range: Literal["5d", "1mo", "3mo", "6mo", "1y"] = "1mo",
) -> list[dict[str, Any]]:
    """Live gold and silver prices in any currency (ISO codes like AED, INR, SAR, PKR, USD): per
    ounce, gram, kilo, tola and 10 grams, with 24k/22k/21k/18k/14k prices. Based on COMEX futures
    and live FX rates (market price, before jewellers' making charges). Optional daily history."""
    return run_actor("gold-price-scraper", {
        "metals": ["gold", "silver"], "currencies": currencies, "goldKarats": True,
        "getHistory": include_history, "historyRange": history_range, "historyInterval": "1d",
    })


@server.tool(annotations=READ_ONLY)
def amazon_best_sellers(
    marketplace: str = "ae",
    categories: list[str] = ["electronics"],
    ranking: Literal["bestsellers", "new-releases", "movers-and-shakers", "most-wished-for"] = "bestsellers",
    max_products: int = 20,
) -> list[dict[str, Any]]:
    """Amazon Best Sellers / New Releases / Movers & Shakers rankings for any of 21 marketplaces
    (marketplace = domain suffix: ae, sa, in, com, co.uk, de, co.jp, sg...). Categories are slugs
    from Best Sellers URLs (electronics, kitchen, beauty, toys-and-games, books...). Each product
    has rank, title, brand, ASIN, price, rating and URL."""
    return run_actor("amazon-ae-scraper", {
        "amazonDomain": marketplace, "bestSellerCategories": categories,
        "rankingList": ranking, "maxProducts": max_products,
    })


@server.tool(annotations=READ_ONLY)
def noon_products(
    query: str,
    country: Literal["uae", "saudi", "egypt"] = "uae",
    max_products: int = 20,
) -> list[dict[str, Any]]:
    """Search Noon, the largest marketplace in the UAE, Saudi Arabia and Egypt: product title,
    brand, price, discount, rating, seller and URL for a search query."""
    return run_actor("noon-scraper", {
        "searchTerms": [query], "noonDomain": f"{country}-en", "maxProducts": max_products,
    }, limit=max_products)


@server.tool(annotations=READ_ONLY)
def web_search(query: str, max_results: int = 5, fetch_page_content: bool = True,
               max_chars_per_page: int = 3000) -> list[dict[str, Any]]:
    """Search the web (DuckDuckGo) and return ranked results with title, URL, snippet and date,
    plus each result page's main text as clean Markdown (when fetch_page_content is true), trimmed
    to max_chars_per_page. Use it to ground answers in current sources and cite them."""
    return run_actor("ai-web-search-scraper", {
        "queries": [query], "engine": "duckduckgo", "maxResults": max_results,
        "fetchPageContent": fetch_page_content, "maxCharsPerPage": max_chars_per_page,
    })


@server.tool(annotations=READ_ONLY)
def web_to_markdown(urls: list[str], max_chars_per_page: int = 0, crawl_site: bool = False,
                    max_pages: int = 10) -> list[dict[str, Any]]:
    """Convert web pages to clean, LLM-ready Markdown (navigation, ads and cookie banners removed)
    with title, date and an approximate token count. JavaScript-heavy pages are rendered
    automatically. Set crawl_site to follow same-domain links (capped by max_pages)."""
    return run_actor("llm-web-scraper", {
        "startUrls": [{"url": u} for u in urls], "outputFormat": "markdown",
        "maxCharsPerPage": max_chars_per_page, "crawl": crawl_site, "maxPages": max_pages,
        "useBrowser": "auto",
    })


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
