# Gulf Data MCP

[![M8ven Score](https://m8ven.ai/badge/mcp/getanything-1/gulf-data-mcp)](https://m8ven.ai/mcp/getanything-1/gulf-data-mcp?s=readme)

An MCP server that gives Claude, ChatGPT, Cursor and other AI agents **live Gulf & Middle East data** plus **web search and web-to-Markdown** for grounding answers.

| Tool | What it returns |
|---|---|
| `dubai_property_transactions` | Official Dubai Land Department (DLD) registered sales, mortgages or gifts for any date range: count, value (AED), area, **price per sqm**, first sale vs resale, by community and property type. |
| `gulf_jobs` | Current jobs in the UAE, Saudi Arabia, Qatar, Kuwait, Bahrain or Oman from **LinkedIn, NaukriGulf, Bayt and GulfTalent** in one search, duplicates merged. |
| `gold_price` | Gold and silver in any currency (AED, INR, SAR, PKR, USD...), per gram, tola, kilo and 10 g, with 24k/22k/21k/18k/14k prices and optional history. |
| `amazon_best_sellers` | Best Sellers / New Releases / Movers & Shakers for **21 Amazon marketplaces** (UAE, Saudi, India, US, UK, Germany, Japan...). |
| `noon_products` | Product search on **Noon** (UAE, Saudi Arabia, Egypt): price, discount, rating, seller. |
| `web_search` | Web search results with each page's main text as clean Markdown, ready to cite. |
| `web_to_markdown` | Any URL (or a whole site) to clean, LLM-ready Markdown with token counts. |

Each tool runs a maintained, ready-made scraper on [Apify](https://apify.com/get_anything) using **your own Apify account**, so there are no shared rate limits and no data passes through a third-party server.

## Setup

1. Create a free Apify account and copy your API token from **Console → Settings → Integrations**.
2. Add the server to your MCP client.

**Claude Desktop / Cursor / any stdio client** (needs [uv](https://docs.astral.sh/uv/)):

```json
{
  "mcpServers": {
    "gulf-data": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/GetAnything-1/gulf-data-mcp", "gulf-data-mcp"],
      "env": { "APIFY_TOKEN": "your-apify-token" }
    }
  }
}
```

**Or with pip:**

```bash
pip install git+https://github.com/GetAnything-1/gulf-data-mcp
APIFY_TOKEN=your-apify-token gulf-data-mcp
```

Then ask your assistant things like:

- *"Which Dubai communities had the most apartment resales last month, and at what price per sqm?"*
- *"Find accountant jobs in Riyadh posted this week, grouped by company."*
- *"What's the 22k gold price per gram in Dubai and Mumbai right now?"*
- *"Show the top 10 Amazon.ae best sellers in electronics and compare with Noon prices."*
- *"Search the web for the latest UAE visa rule changes and summarise the top 5 sources with links."*

## Cost

Each call runs a pay-per-result scraper on your Apify account (typically $1–10 per 1,000 results; see each scraper's page). Apify's free plan includes monthly credit, which covers plenty of agent use. Keep `max_*` parameters small for quick questions.

| Tool | Scraper |
|---|---|
| `dubai_property_transactions` | [DLD Transactions Scraper](https://apify.com/get_anything/dld-transactions-scraper) |
| `gulf_jobs` | [GCC Jobs Aggregator](https://apify.com/get_anything/gcc-jobs-aggregator) |
| `gold_price` | [Gold Price Scraper](https://apify.com/get_anything/gold-price-scraper) |
| `amazon_best_sellers` | [Amazon Products & Best Sellers](https://apify.com/get_anything/amazon-ae-scraper) |
| `noon_products` | [Noon Scraper](https://apify.com/get_anything/noon-scraper) |
| `web_search` | [AI Web Search Scraper](https://apify.com/get_anything/ai-web-search-scraper) |
| `web_to_markdown` | [LLM Web Scraper](https://apify.com/get_anything/llm-web-scraper) |

## Notes

- Data comes from public pages and official public sources. No logins to the source sites.
- The scrapers don't solve CAPTCHAs or defeat bot protection. If a source refuses (Bayt and GulfTalent sometimes do from the cloud), those results are skipped and not charged.
- Live market examples built with this data: [gold price today](https://getanything-site.vercel.app/data/gold-price), [Dubai price per sqm](https://getanything-site.vercel.app/data/dubai-price-per-sqm).

## License

MIT. Questions or a data source you need? get.anything2026@gmail.com
