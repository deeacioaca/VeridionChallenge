import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup

PHONE_REGEX_PATTERNS = [
    r'\+\d{1,3} \d{3} \d{3} \d{4}',
    r'\d{3}-\d{3}-\d{4}',
    r'\(\d{3}\) \d{3}-\d{4}',
    r'\d{5}-\d{6}',
    r'\d{2,5} \d{2,5} \d{2,5} \d{2,5}',
    r'\d{3} \d{3} \d{4}',
    r'\(\d{2}\) \d{4,5}-\d{4}',
    r'\d{10}',
    r'1-800-\d{3}-\d{4}',
]

SOCIAL_DOMAINS = ["facebook.com", "linkedin.com", "twitter.com", "instagram.com", "youtube.com"]

ADDRESS_REGEX = re.compile(r'\d{1,5}\s+\w+(\s\w+)*,\s*[A-Z]{2}\s*\d{5}')

def extract_phone_numbers(html: str) -> list[str]:
    # Parse HTML and extract visible text
    soup = BeautifulSoup(html, "html.parser")
    # Remove script and style tags (not visible)
    for tag in soup(["script", "style"]):
        tag.decompose()

    visible_text = soup.get_text(separator=" ", strip=True)
    # Set to collect unique phone numbers
    matches = set()
    for pattern in PHONE_REGEX_PATTERNS:
        regex = re.compile(pattern)
        found = regex.findall(visible_text)
        matches.update(found)
    return list(matches)

def extract_social_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        href = a['href']
        if any(domain in href for domain in SOCIAL_DOMAINS):
            links.append(href)
    return list(set(links))

def extract_address(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

    # First, <address> tag
    address_elements = soup.find_all("address")
    for element in address_elements:
        address_text = element.get_text(separator=" ", strip=True)
        if address_text and not email_pattern.search(address_text):
            return address_text

    # Then, div/span with 'address' class
    possible_address_divs = soup.find_all(
        lambda tag: tag.name in ['div', 'span']
        and tag.has_attr('class')
        and any('address' in cls.lower() for cls in tag['class'])
    )
    for element in possible_address_divs:
        address_text = element.get_text(separator=" ", strip=True)
        if address_text and not email_pattern.search(address_text):
            return address_text

    # Finally, regex search in raw HTML text
    match = ADDRESS_REGEX.search(soup.get_text(separator=" ", strip=True))
    if match:
        return match.group()
    return None

async def _decode_response(response) -> str | None:
    """Try to decode response text, with fallbacks on decoding errors."""
    try:
        return await response.text()
    except UnicodeDecodeError:
        print(f"[WARN] UnicodeDecodeError, trying fallback decoding.")
        raw = await response.read()
        for encoding in ['iso-8859-1', 'windows-1252']:
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
        print(f"[ERROR] Failed to decode response with fallback encodings.")
        return None

async def _fetch(session: aiohttp.ClientSession, url: str, ssl_flag) -> tuple[str | None, int | None]:
    """Single fetch attempt with specified SSL verification flag."""
    async with session.get(url, timeout=45, ssl=ssl_flag) as response:
        status = response.status
        if status == 200:
            html = await _decode_response(response)
            return html, status
        print(f"[WARN] {url} returned status {status}")
        return None, status

async def fetch_html(session: aiohttp.ClientSession, url: str, retries=2, delay=1) -> tuple[str | None, int | None]:
    last_status = None
    for attempt in range(1, retries + 1):
        try:
            html, status = await _fetch(session, url, ssl_flag=False)
            last_status = status
            if html is not None:
                return html, status
        except aiohttp.ClientConnectorSSLError as e:
            print(f"[SSL ERROR] {url} → {e}, retrying without SSL verification.")
            try:
                html, status = await _fetch(session, url, ssl_flag=False)
                last_status = status
                if html is not None:
                    return html, status
            except Exception as e2:
                print(f"[SSL RETRY FAIL] {url} → {type(e2).__name__}: {e2}")
        except Exception as e:
            print(f"[ERROR] {url} → {type(e).__name__}: {e}")

        if attempt < retries:
            await asyncio.sleep(delay * attempt)  # Exponential backoff

    return None, last_status

async def try_fetch_with_fallback(session: aiohttp.ClientSession, domain: str) -> tuple[str, str | None, int | None]:
    for protocol in ["https://", "http://"]:
        for prefix in ["www.", ""]:
            url = f"{protocol}{prefix}{domain}"
            html, status = await fetch_html(session, url)
            if html:
                return url, html, status
            elif status:  # Record non-None status if no html
                last_status = status
    return f"https://{domain}", None, last_status if 'last_status' in locals() else None

