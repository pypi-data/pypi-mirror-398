import ipaddress
import asyncio
import time
from dataclasses import dataclass
from emailsec._dns_resolver import DNSResolver
import cachetools


@dataclass
class DNSBLEntry:
    return_code: str
    description: str | None


@dataclass
class DNSBLResult:
    ip_address: str
    is_listed: bool
    listed_on: list[str]
    entries: dict[str, DNSBLEntry]
    failed_queries: list[str]

    def get_smtp_response(self) -> str | None:
        if self.is_listed:
            sources = ", ".join(self.listed_on)
            # Include description from first entry if available
            first_entry = next(iter(self.entries.values()), None)
            if first_entry and first_entry.description:
                return f"550 5.7.1 {first_entry.description}"
            return f"550 5.7.1 IP blocked by {sources}"
        return None


class DNSBLChecker:
    """DNSBL checker with caching."""

    def __init__(self, cache_size: int = 1000):
        """Initialize DNSBL checker with cache.

        Args:
            cache_size: Maximum number of cache entries
        """
        self._cache = cachetools.LRUCache(maxsize=cache_size)
        self._cache_expiry: dict[tuple[str, str], float] = {}
        self._resolver: DNSResolver | None = None

    def _get_resolver(self) -> DNSResolver:
        if self._resolver is None:
            self._resolver = DNSResolver(no_max_lookups=True)
        return self._resolver

    async def check_ip(self, ip: str, blocklists: list[str]) -> DNSBLResult:
        """Check if an IP address is listed in DNS blacklists.

        Args:
            ip: IP address to check
            blocklists: List of DNSBL domains to query

        Returns:
            DNSBLResult with listing status and details
        """
        # Sanity check, will raise ValueError if invalid
        ipaddress.ip_address(ip)

        queries = []
        for blocklist in blocklists:
            queries.append(self._check_single_dnsbl(ip, blocklist))

        results = await asyncio.gather(*queries, return_exceptions=True)

        listed_on = []
        entries: dict[str, DNSBLEntry] = {}
        failed_queries = []

        for i, result in enumerate(results):
            blocklist = blocklists[i]

            if isinstance(result, Exception):
                failed_queries.append(blocklist)
            elif result:
                listed_on.append(blocklist)
                entries[blocklist] = result  # type: ignore
            # No/None results means it's not listed

        return DNSBLResult(
            ip_address=ip,
            is_listed=bool(listed_on),
            listed_on=listed_on,
            entries=entries,
            failed_queries=failed_queries,
        )

    async def _check_single_dnsbl(self, ip: str, blocklist: str) -> DNSBLEntry | None:
        cache_key = (ip, blocklist)

        if cache_key in self._cache:
            expiry_time = self._cache_expiry.get(cache_key)
            if expiry_time and time.time() < expiry_time:
                return self._cache[cache_key]
            else:
                self._cache.pop(cache_key, None)
                self._cache_expiry.pop(cache_key, None)

        parsed_ip = ipaddress.ip_address(ip)
        if parsed_ip.version == 4:
            reversed_addr = parsed_ip.reverse_pointer.removesuffix(".in-addr.arpa")
        else:
            # IPv6: convert to nibble format as per RFC 5782 Section 2.4
            hex_addr = parsed_ip.packed.hex()
            reversed_addr = ".".join(reversed(hex_addr))

        query_name = f"{reversed_addr}.{blocklist}"

        # Query both A and TXT records as per RFC 5782
        resolver = self._get_resolver()

        a_result = await resolver.a(query_name)

        ttl = 300
        if a_result and hasattr(a_result[0], "ttl"):
            ttl = a_result[0].ttl

        if not a_result or not a_result[0].host.startswith("127."):
            self._cache[cache_key] = None
            self._cache_expiry[cache_key] = time.time() + ttl
            return None

        return_code = a_result[0].host

        # Validate return code is in 127.0.0.0/8 range (RFC 5782 Section 2.1)
        try:
            code_ip = ipaddress.ip_address(return_code)
            if not (code_ip.version == 4 and str(code_ip).startswith("127.")):
                self._cache[cache_key] = None
                self._cache_expiry[cache_key] = time.time() + ttl
                return None
        except ValueError:
            self._cache[cache_key] = None
            self._cache_expiry[cache_key] = time.time() + ttl
            return None

        # Fetch TXT record for description (RFC 5782 Section 2.1)
        description = None
        try:
            txt_result = await resolver.txt(query_name)
            if txt_result and txt_result[0].text:
                desc = txt_result[0].text
                if isinstance(desc, bytes):
                    description = desc.decode("utf-8", errors="ignore")
                else:
                    description = str(desc)
        except Exception:
            # description is optional, let it fail silently
            pass

        result = DNSBLEntry(return_code=return_code, description=description)

        self._cache[cache_key] = result
        self._cache_expiry[cache_key] = time.time() + ttl

        return result
