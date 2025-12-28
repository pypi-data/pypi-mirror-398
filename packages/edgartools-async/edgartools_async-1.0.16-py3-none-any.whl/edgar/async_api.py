import os
import asyncio
from typing import Optional, Union

from edgar.core import set_identity
from edgar.httpclient import async_http_client
from edgar.httprequests import IdentityNotSetException, download_json_async, download_file_async
from edgar.entity.submissions import create_entity_from_submissions_json
from edgar.reference.tickers import (
    company_tickers_json_url,
    ticker_txt_url,
    mutual_fund_tickers_url,
)
import pyarrow as pa
from edgar.entity.data import extract_company_filings_table
from edgar.entity.filings import EntityFilings
from edgar.storage import is_using_local_storage
from edgar._filings import load_sgmls_concurrently

__all__ = ["get_company_async", "find_cik_async", "load_full_filings_async", "load_sgmls_concurrently"]


_ticker_lookup_cache: Optional[dict] = None
_ticker_lookup_lock = asyncio.Lock()


async def _build_ticker_lookup_async() -> dict:
    global _ticker_lookup_cache
    if _ticker_lookup_cache is not None:
        return _ticker_lookup_cache

    async with _ticker_lookup_lock:
        if _ticker_lookup_cache is not None:
            return _ticker_lookup_cache

        lookup: dict = {}
        async with async_http_client() as client:
            # company_tickers.json (listed + many delisted)
            try:
                j = await download_json_async(client, company_tickers_json_url)
                for item in j.values():
                    t = str(item.get("ticker", "")).upper()
                    if not t:
                        continue
                    cik = int(item["cik_str"])
                    lookup[t] = cik
                    base = t.split('-')[0]
                    lookup.setdefault(base, cik)
            except Exception:
                pass

            # ticker.txt (authoritative base mapping; often includes delisted)
            try:
                txt = await download_file_async(client, ticker_txt_url, as_text=True)
                if txt:
                    for line in txt.splitlines():
                        if not line.strip() or '\t' not in line:
                            continue
                        t, cik_str = line.split('\t')
                        t = t.strip().upper()
                        if cik_str and cik_str.strip().isdigit():
                            cik = int(cik_str.strip())
                            lookup[t] = cik
                            base = t.split('-')[0]
                            lookup.setdefault(base, cik)
            except Exception:
                pass

            # mutual funds / ETFs
            try:
                mf = await download_json_async(client, mutual_fund_tickers_url)
                for row in mf.get('data', []):
                    if len(row) >= 4:
                        cik, _, _, t = row[0], row[1], row[2], str(row[3]).upper()
                        if t:
                            lookup[t] = int(cik)
            except Exception:
                pass

        _ticker_lookup_cache = lookup
        return lookup


async def find_cik_async(ticker: str) -> Optional[int]:
    ticker = str(ticker).upper().replace('.', '-')
    lookup = await _build_ticker_lookup_async()
    return lookup.get(ticker)


async def get_company_async(cik_or_ticker: Union[str, int], user_agent: Optional[str] = None):
    """
    Fully async helper that resolves CIK and loads submissions without blocking.

    - Sets EDGAR identity if `user_agent` provided, else requires EDGAR_IDENTITY.
    - Resolves ticker -> CIK via async SEC file download.
    - Downloads submissions JSON asynchronously and constructs a Company object without extra network calls.
    """
    if user_agent:
        set_identity(user_agent)
    elif os.environ.get("EDGAR_IDENTITY") is None:
        raise IdentityNotSetException("User-Agent identity is not set. Pass user_agent or set EDGAR_IDENTITY.")

    # Resolve CIK
    if isinstance(cik_or_ticker, int) or (isinstance(cik_or_ticker, str) and cik_or_ticker.isdigit()):
        cik = int(str(cik_or_ticker).lstrip('0'))
    else:
        cik = await find_cik_async(str(cik_or_ticker))
        if cik is None:
            raise ValueError(f"Could not find CIK for ticker '{cik_or_ticker}'")

    # Download submissions and build Company without triggering sync I/O
    async with async_http_client() as client:
        submissions_json = await download_json_async(client, f"https://data.sec.gov/submissions/CIK{cik:010}.json")

    company = create_entity_from_submissions_json(submissions_json, entity_type='company')
    return company


async def load_full_filings_async(company) -> None:
    """
    Expand a Company's filings list asynchronously (no blocking) to include older filings.

    Mirrors EntityData._load_older_filings but uses async HTTP and avoids blocking the event loop.
    After this, you can call company.get_filings(..., trigger_full_load=False) inside async code safely.
    """
    data = company.data
    if getattr(data, "_loaded_all_filings", False) or is_using_local_storage():
        return

    files = getattr(data, "_files", [])
    if not files:
        data._loaded_all_filings = True
        return

    tables = [data.filings.data]
    async with async_http_client() as client:
        for f in files:
            submissions = await download_json_async(client, "https://data.sec.gov/submissions/" + f['name'])
            table = extract_company_filings_table(submissions)
            tables.append(table)

    combined = pa.concat_tables(tables)
    data.filings = EntityFilings(combined, cik=data.cik, company_name=data.name)
    data._loaded_all_filings = True
