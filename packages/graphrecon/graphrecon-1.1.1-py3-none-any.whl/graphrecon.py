#!/usr/bin/env python3
import argparse
import asyncio
import aiohttp
from urllib.parse import urljoin

__version__ = "1.1.1"

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[38;5;32m'
RESET = '\033[0m'

ENDPOINTS = [
    "api/v3/graphql", "graphql/v3", "api/v4/graphql", "graphql/v4", "v3/graphql",
    "v4/graphql", "api/v3", "api/v4", "v3/api", "v4/api", "v3/api/v1", "v3/api/v2",
    "v4/api/v1", "v4/api/v2", "graphql/v3/api", "graphql/v4/api", "v3/graphql/api",
    "v4/graphql/api", "api/v3/graphql/v1", "api/v4/graphql/v2", "v1/api/graphql/v3",
    "v2/api/graphql/v4", "v3/graphql/v1/api", "v4/graphql/v2/api","v1/graphql/v3/api",
    "v2/graphql/v4/api", "v3/api/graphql/v1", "v4/api/graphql/v2", "graphql/v1/api/v3",
    "graphql/v2/api/v4", "graphql", "api/graphql", "v1/graphql", "v2/graphql", "api",
    "graphql/api", "v1/api", "v2/api", "graphql/v1", "graphql/v2", "api/v1/graphql",
    "api/v2/graphql", "v1/api/graphql", "v2/api/graphql", "v1", "v2", "api/v1", "api/v2",
    "v1/api/v1", "v1/api/v2", "v2/api/v1", "v2/api/v2", "graphql/v1/api", "graphql/v2/api",
    "v1/graphql/api", "v2/graphql/api", "api/v1/graphql/v1", "api/v2/graphql/v2",
    "v1/api/graphql/v1", "v2/api/graphql/v2"
]


def Banner():
    print(rf"""
  ________                    .__   __________                            
 /  _____/___________  ______ |  |__\______   \ ____   ____  ____   ____  
/   \  __\_  __ \__  \ \____ \|  |  \|       _// __ \_/ ___\/  _ \ /    \ 
\    \_\  \  | \// __ \|  |_> >   Y  \    |   \  ___/\  \__(  <_> )   |  \
 \______  /__|  (____  /   __/|___|  /____|_  /\___  >\___  >____/|___|  /
        \/           \/|__|        \/       \/     \/     \/           \/ 
                                                                v{__version__}
                            {GREEN}pentestproject{RESET}
""")


async def check_site(session, url):
    try:
        async with session.get(url, allow_redirects=True) as resp:
            print(f"{BLUE}[+] Site reachable → {url} ({resp.status}){RESET}")
            return True
    except Exception:
        return False


async def scan_base(session, base_url, found):
    PAYLOAD = {"query": "{ __typename }"}
    semaphore = asyncio.Semaphore(15)

    async def scan(ep):
        full_url = urljoin(base_url.rstrip("/") + "/", ep)
        async with semaphore:
            try:
                async with session.post(full_url, json=PAYLOAD) as resp:
                    ct = resp.headers.get("Content-Type", "")
                    print(f"[DEBUG] {full_url} → {resp.status} | {ct}")

                    if "application/json" in ct:
                        data = await resp.json()
                        if "data" in data or "errors" in data:
                            found.add(full_url)
                            print(f"{GREEN}[+] GraphQL FOUND → {full_url}{RESET}")
            except Exception:
                pass

    await asyncio.gather(*(scan(ep) for ep in ENDPOINTS))


async def GraphQLScanner(target):
    found = set()

    if target.startswith(("http://", "https://")):
        base_urls = [target]
    else:
        base_urls = [f"https://{target}"]

    timeout = aiohttp.ClientTimeout(total=8)
    connector = aiohttp.TCPConnector(ssl=False, limit=50)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "GraphRecon/1.2"
    }

    async with aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
        headers=headers
    ) as session:

        for base_url in base_urls:
            if not await check_site(session, base_url):
                continue

            await scan_base(session, base_url, found)

            if found and base_url.startswith("https://"):
                break

    if not found:
        print(f"{RED}[-] GraphQL NOT FOUND{RESET}")


def main():
    Banner()
    parser = argparse.ArgumentParser(description="Async GraphQL scanner")
    parser.add_argument("-u", "--url", required=True, help="Target domain or URL")
    args = parser.parse_args()

    print(f"{YELLOW}[*] Scanning is starting{RESET}")
    asyncio.run(GraphQLScanner(args.url))


if __name__ == "__main__":
    main()
