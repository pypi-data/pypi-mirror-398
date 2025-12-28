#!/usr/bin/env python3

import argparse
import asyncio
import os
import sys
from typing import Any, Optional

import aiohttp
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

REQUEST_TIMEOUT = 30


def get_env_var(name: str, default: Optional[str] = None, required: bool = False) -> str:
    value = os.environ.get(name, "")
    if not value:
        if default is not None:
            return default
        if required:
            print(f"{name} environment variable is not defined", file=sys.stderr)
            raise SystemExit(1)
    return value


async def get_paths_async(
    session: aiohttp.ClientSession,
    vault_addr: str,
    kv_path: str,
    vault_skip_verify: bool,
    search_path: str,
    current_path: str = "",
) -> list[str]:
    url = f"{vault_addr}/v1/{kv_path}/metadata{current_path}?list=true"
    try:
        async with session.get(url, ssl=False if vault_skip_verify else None) as response:
            response.raise_for_status()
            json_response = await response.json()
            keys = json_response.get("data", {}).get("keys", [])
    except aiohttp.ClientResponseError as e:
        if e.status == 403:
            return []
        raise

    matching_paths: list[str] = []
    tasks: list[asyncio.Task[list[str]]] = []

    for key in keys:
        if key.endswith("/"):
            new_path = f"{current_path}/{key.strip('/')}"
            tasks.append(
                asyncio.create_task(
                    get_paths_async(
                        session,
                        vault_addr,
                        kv_path,
                        vault_skip_verify,
                        search_path,
                        new_path,
                    )
                )
            )
        elif search_path.lower() in key.lower():
            matching_paths.append(f"{current_path}/{key}".strip("/"))

    if tasks:
        subpaths = await asyncio.gather(*tasks)
        for sublist in subpaths:
            matching_paths.extend(sublist)

    return matching_paths


def get_paths(
    vault_addr: str,
    vault_token: str,
    kv_path: str,
    vault_skip_verify: bool,
    search_path: str,
) -> list[str]:
    headers = {"X-Vault-Token": vault_token}

    async def wrapper():
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            return await get_paths_async(session, vault_addr, kv_path, vault_skip_verify, search_path)

    return asyncio.run(wrapper())


def get_secret(
    vault_addr: str,
    vault_token: str,
    kv_path: str,
    vault_skip_verify: bool,
    search_secret: str,
) -> dict[str, Any]:
    headers = {"X-Vault-Token": vault_token}
    url = f"{vault_addr}/v1/{kv_path}/data/{search_secret}"
    response = requests.get(
        url,
        headers=headers,
        verify=not vault_skip_verify,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    secret_data = response.json().get("data", {}).get("data", {})
    return secret_data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search and display secrets in HashiCorp Vault"
    )
    parser.add_argument(
        "-sp",
        "--search-path",
        dest="search_path",
        metavar="SEARCH_PATH",
        type=str,
        help="Search HashiCorp Vault for a matching string",
    )
    parser.add_argument(
        "-ss",
        "--search-secret",
        dest="search_secret",
        metavar="SECRET_PATH",
        type=str,
        help="Display all key/value pairs at a specific path",
    )

    args = parser.parse_args()

    if args.search_path is None and args.search_secret is None:
        parser.print_help()
        return 1

    vault_addr = get_env_var("VAULT_ADDR", required=True)
    vault_skip_verify = get_env_var("VAULT_SKIP_VERIFY", default="0") == "1"
    vault_token = get_env_var("VAULT_TOKEN", required=True)
    vault_kv_path = get_env_var("VAULT_KV_PATH", required=True)

    if vault_skip_verify:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    if args.search_path:
        matching_paths = get_paths(
            vault_addr,
            vault_token,
            vault_kv_path,
            vault_skip_verify,
            args.search_path,
        )
        print("Matching paths:")
        for item in matching_paths or ["(no matches)"]:
            print(item)

    if args.search_secret:
        secret_data = get_secret(
            vault_addr,
            vault_token,
            vault_kv_path,
            vault_skip_verify,
            args.search_secret,
        )
        print("Secret data:")
        for key, value in secret_data.items() or {"(empty)": ""}.items():
            print(f"{key}: {value}")

    return 0


def run() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    run()
