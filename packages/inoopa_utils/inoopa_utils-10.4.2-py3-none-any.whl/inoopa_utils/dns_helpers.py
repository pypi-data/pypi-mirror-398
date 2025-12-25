import re
import idna
import asyncio
from typing import Literal
from tqdm.asyncio import tqdm
from aiodns import DNSResolver
from aiodns.error import DNSError
from pycares import ares_query_mx_result


DnsRecordType = Literal["A", "AAAA", "MX", "CNAME", "SRV", "TXT", "NS"]
# List of DNS servers to use for DNS resolution (Google & OpenDNS)
DNS_SERVERS = ["8.8.8.8", "208.67.222.222", "8.8.4.4", "208.67.220.220"]


def _validate_domain(domain: str) -> str | None:
    """
    Check the domain validity (fix it if possible).

    :return: the cleaned domain or None if it can't be fixed.
    """
    try:
        clean_domain = idna.encode(domain).decode("ascii").lower().strip()
    except (UnicodeError, idna.IDNAError):
        return None
    return clean_domain if re.match(r"^[\w.-]+\.\w{2,}$", clean_domain) else None


async def _check_domain_dns(domain: str, dns_types: list[DnsRecordType], resolver: DNSResolver) -> str | None:
    """Check if a domain has at least one of the dns_types DNS record."""
    validated_domain = _validate_domain(domain)
    if not validated_domain:
        return None
    for dns_type in dns_types:
        try:
            # Resolve the domain's DNS. Will raise an exception if the domain doesn't exist or timeout
            await resolver.query(validated_domain, dns_type)
            return domain
        # If one of these exceptions is raised, it means the domain doesn't exist or timed out
        except (DNSError, UnicodeError):
            continue
    return None


async def _get_domain_dns_mx_domain(domain: str, resolver: DNSResolver) -> tuple[str, str] | tuple[None, None]:
    """Return the domain's DNS record (based on the dns_type)."""
    validated_domain = _validate_domain(domain)
    if not validated_domain:
        return None, None
    try:
        records: list[ares_query_mx_result] = await resolver.query(domain, "MX")
        if not records:
            return None, None
        # get the first MX record host's domain
        mx_server_host = str(records[0].host)
        mx_server_domain = ".".join(mx_server_host.split(".")[-2:])
        return domain, mx_server_domain
    except (DNSError, UnicodeError):
        return None, None


async def check_if_domains_have_dns_async(
    domains: list[str],
    batch_size: int = 10_000,
    dns_timeout: float = 1,
    dns_types_to_check: list[DnsRecordType] = ["A", "AAAA"],
) -> set[str]:
    """Check all the domains in a wave. Return a set of valid domains."""
    valid_domains = []
    # Divide the domains in batches to avoid timeout issues
    domains_batches: list[list[str]] = [domains[i : i + batch_size] for i in range(0, len(domains), batch_size)]
    for domains_chunk in tqdm(domains_batches):
        resolver = DNSResolver(timeout=dns_timeout, nameservers=DNS_SERVERS, loop=asyncio.get_event_loop())
        tasks = [_check_domain_dns(domain, dns_types_to_check, resolver) for domain in domains_chunk]
        results = await asyncio.gather(*tasks)
        valid_domains.extend([r for r in results if r])
    return set(valid_domains)


def check_if_domains_have_dns(
    domains: list[str],
    batch_size: int = 10_000,
    dns_timeout: float = 1,
    dns_types_to_check: list[DnsRecordType] = ["A", "AAAA"],
) -> set[str]:
    """Check if a domain has at least one of the dns_types DNS record."""
    return asyncio.run(check_if_domains_have_dns_async(domains, batch_size, dns_timeout, dns_types_to_check))


async def get_domains_dns_mx_domain_async(
    domains: list[str], batch_size: int = 10_000, dns_timeout: float = 1
) -> dict[str, str]:
    """Check all the domains in a wave. Return a set of valid domains."""
    domain_to_mx_server_domain_mapper: dict[str, str] = {}
    # Divide the domains in batches to avoid timeout issues
    domains_batches: list[list[str]] = [domains[i : i + batch_size] for i in range(0, len(domains), batch_size)]
    for domains_chunk in tqdm(domains_batches):
        resolver = DNSResolver(timeout=dns_timeout, nameservers=DNS_SERVERS, loop=asyncio.get_event_loop())
        tasks = [_get_domain_dns_mx_domain(domain, resolver) for domain in domains_chunk]
        results = await asyncio.gather(*tasks)
        batch_mapper = {
            domain: mx_server_domain.strip().lower()  # MX server domain are registered in uppercase or with spaces
            for domain, mx_server_domain in results
            if mx_server_domain and domain
        }
        domain_to_mx_server_domain_mapper.update(batch_mapper)
    return domain_to_mx_server_domain_mapper


def get_domains_dns_mx_domain(domains: list[str], batch_size: int = 10_000, dns_timeout: float = 1) -> dict[str, str]:
    """Check all the domains in a wave. Return a set of valid domains."""
    return asyncio.run(get_domains_dns_mx_domain_async(domains, batch_size, dns_timeout))
