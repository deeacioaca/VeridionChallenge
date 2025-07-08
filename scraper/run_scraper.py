import time
import pandas as pd
import asyncio
import aiohttp
from scraper.crawler import try_fetch_with_fallback, extract_phone_numbers, extract_social_links, extract_address
from pathlib import Path
import random

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_CSV = BASE_DIR / "data" / "sample-websites.csv"
OUTPUT_CSV = BASE_DIR / "data" / "scraped_data.csv"
FAILED_CSV = BASE_DIR / "data" / "failed_domains.csv"
CONCURRENCY = 20

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/110.0.0.0 Safari/537.36",
]

headers = {"User-Agent": random.choice(USER_AGENTS)}

failed_domains = []

async def process_domain(session, domain: str, i: int):
    domain = domain.strip()
    print(f"[{i}] Crawling: {domain}")

    url, html, status = await try_fetch_with_fallback(session, domain)
    if not html:
        print(f"[{i}] ❌ Failed: {domain} (Status: {status})")
        failure = (domain, status)
        if failure not in failed_domains:
            failed_domains.append(failure)
        return None

    phones = extract_phone_numbers(html)
    socials = extract_social_links(html)
    address = extract_address(html)

    return {
        "domain": url,
        "phone_numbers": "; ".join(phones),
        "social_links": "; ".join(socials),
        "address": address if address else ""
    }


async def run_scraper():
    df = pd.read_csv(INPUT_CSV)
    domains = df['domain'].dropna().tolist()

    results = []

    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    async with aiohttp.ClientSession(headers=headers, connector=connector, trust_env=True) as session:
        tasks = [process_domain(session, domain, i + 1) for i, domain in enumerate(domains)]
        for future in asyncio.as_completed(tasks):
            result = await future
            if result:
                results.append(result)

    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Scraped data saved to {OUTPUT_CSV}")

    if failed_domains:
        pd.DataFrame(failed_domains, columns=["domain", "http_status"]).to_csv(FAILED_CSV, index=False)
        print(f"⚠️ {len(failed_domains)} failed domains saved to {FAILED_CSV}")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(run_scraper())
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\n⏱️ Total execution time: {elapsed:.2f} seconds")
