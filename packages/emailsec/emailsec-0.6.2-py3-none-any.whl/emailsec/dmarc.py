from enum import StrEnum
from dataclasses import dataclass
from typing import Literal

import publicsuffixlist
from emailsec._dns_resolver import DNSResolver
from emailsec._alignment import is_spf_aligned, is_dkim_aligned, AlignmentMode
from emailsec.config import AuthenticationConfiguration
from emailsec import _errors as errors
from emailsec.spf.checker import SPFResult, SPFCheck
from emailsec.dkim.checker import DKIMResult, DKIMCheck
from emailsec.arc import ARCChainStatus, ARCCheck
from emailsec._authentication_results import extract_original_auth_results

__all__ = [
    "check_dmarc",
    "get_dmarc_policy",
    "DMARCCheck",
    "DMARCResult",
    "DMARCPolicy",
    "DMARCRecord",
]


class DMARCPolicy(StrEnum):
    NONE = "none"
    QUARANTINE = "quarantine"
    REJECT = "reject"


@dataclass
class DMARCRecord:
    """Holds a parsed DMARC DNS record."""

    policy: DMARCPolicy
    spf_mode: AlignmentMode
    dkim_mode: AlignmentMode
    # percentage: int


class DMARCResult(StrEnum):
    """Defined in RFC 7489 Section 11.2"""

    PASS = "pass"
    FAIL = "fail"
    NONE = "none"
    PERMERROR = "permerror"
    TEMPERROR = "temperror"


@dataclass
class DMARCCheck:
    result: DMARCResult
    policy: DMARCPolicy | None
    spf_aligned: bool | None = None
    dkim_aligned: bool | None = None
    arc_override_applied: bool = False


_DMARCError = Literal[DMARCResult.TEMPERROR] | Literal[DMARCResult.PERMERROR]


async def _fetch_dmarc_record(
    resolver: DNSResolver, domain: str
) -> tuple[DMARCRecord | None, _DMARCError | None]:
    """Fetch and parse DMARC record for the given domain."""
    try:
        txt_records = await resolver.txt(f"_dmarc.{domain}")
    except errors.Permerror:
        return None, DMARCResult.PERMERROR
    except errors.Temperror:
        return None, DMARCResult.TEMPERROR

    if not txt_records:
        return None, None

    try:
        record = parse_dmarc_record(txt_records[0].text)
        return record, None
    except Exception:
        return None, DMARCResult.PERMERROR


async def get_dmarc_policy(
    domain: str,
) -> tuple[DMARCRecord | None, _DMARCError | None]:
    """Fetch DMARC policy according to RFC 7489 Section 6.1."""
    resolver = DNSResolver()

    record, error = await _fetch_dmarc_record(resolver, domain)

    # Temp error means early return
    if error == DMARCResult.TEMPERROR or record:
        return record, error

    # RFC 7489 Section 6.6.3: "If the set is now empty, the Mail Receiver MUST query the DNS for
    # a DMARC TXT record at the DNS domain matching the Organizational
    # Domain in place of the RFC5322.From domain in the message (if
    # different).
    psl = publicsuffixlist.PublicSuffixList()
    organizational_domain = psl.privatesuffix(domain.lower()) or domain

    if organizational_domain != domain:
        org_record, org_error = await _fetch_dmarc_record(
            resolver, organizational_domain
        )
        # Return org domain result if we found a record or hit a temp error
        if org_error == DMARCResult.TEMPERROR or org_record:
            return org_record, org_error

    # No policy found anywhere, return the original domain's result
    return record, error


def parse_dmarc_record(record: str) -> DMARCRecord:
    tags = {}
    for part in record.split(";"):
        part = part.strip()
        if "=" in part:
            key, value = part.split("=", 1)
            tags[key.strip()] = value.strip()

    if "v" not in tags:
        raise ValueError("Missing mandatory v=DMARC1 tag")

    if tags["v"] != "DMARC1":
        raise ValueError(f"Invalid DMARC version: {tags['v']}, expected DMARC1")

    if "p" not in tags:
        raise ValueError("Missing mandatory p= tag")

    return DMARCRecord(
        policy=DMARCPolicy(tags.get("p", "none")),
        spf_mode="strict" if tags.get("aspf") == "s" else "relaxed",
        dkim_mode="strict" if tags.get("adkim") == "s" else "relaxed",
        # percentage=int(tags.get('pct', '100'))
    )


async def check_dmarc(
    header_from: str,
    envelope_from: str,
    spf_check: SPFCheck,
    dkim_check: DKIMCheck,
    arc_check: ARCCheck,
    configuration: AuthenticationConfiguration | None = None,
) -> DMARCCheck:
    """
    DMARC evaluation per RFC 7489 Section 3 (Identifier Alignment).

    RFC 7489: "A message satisfies the DMARC checks if at least one of the supported
    authentication mechanisms: 1. produces a 'pass' result, and 2. produces that
    result based on an identifier that is in alignment"
    """

    # Get DMARC policy (RFC 7489 Section 6.1)
    dmarc_policy, error = await get_dmarc_policy(header_from)

    # Return early if we hit temp/perm errors
    if error:
        return DMARCCheck(result=error, policy=None)

    # No policy found
    if not dmarc_policy:
        return DMARCCheck(result=DMARCResult.NONE, policy=None)

    # Check identifier alignment (RFC 7489 Section 3.1)
    # SPF alignment: envelope sender domain vs header from domain
    envelope_domain = (
        envelope_from.split("@")[-1] if "@" in envelope_from else envelope_from
    )
    spf_aligned = spf_check.result == SPFResult.PASS and is_spf_aligned(
        envelope_domain, header_from, dmarc_policy.spf_mode
    )

    # DKIM alignment: signing domain (d=) vs header from domain
    dkim_aligned = bool(
        dkim_check.result == DKIMResult.SUCCESS
        and dkim_check.domain
        and is_dkim_aligned(dkim_check.domain, header_from, dmarc_policy.dkim_mode)
    )

    # RFC 7489: DMARC passes if either SPF or DKIM is aligned and passes
    dmarc_pass = spf_aligned or dkim_aligned

    # ARC override logic (RFC 8617 Section 7.2.1)
    # RFC 8617: "a DMARC processor MAY choose to accept the authentication
    # assessments provided by an Authenticated Received Chain"
    arc_override_applied = False
    if (
        not dmarc_pass
        and configuration
        and configuration.trusted_arc_signers
        and arc_check.signer in configuration.trusted_arc_signers
        and arc_check.result == ARCChainStatus.PASS
        and arc_check.aar_header
    ):
        parsed_aar = extract_original_auth_results(
            arc_check.result, arc_check.aar_header
        )
        if parsed_aar and "dmarc" in parsed_aar and parsed_aar["dmarc"] == "pass":
            dmarc_pass = True
            arc_override_applied = True

    return DMARCCheck(
        result=DMARCResult.PASS if dmarc_pass else DMARCResult.FAIL,
        policy=dmarc_policy.policy,
        spf_aligned=spf_aligned,
        dkim_aligned=dkim_aligned,
        arc_override_applied=arc_override_applied,
    )
