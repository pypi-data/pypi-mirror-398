from email.utils import parseaddr
from enum import Enum
from dataclasses import dataclass

from emailsec.config import AuthenticationConfiguration

from emailsec.spf.checker import check_spf, SPFCheck, SPFResult
from emailsec.dkim.checker import check_dkim, DKIMCheck, DKIMResult
from emailsec.dmarc import (
    check_dmarc,
    DMARCPolicy,
    DMARCCheck,
    DMARCResult,
)
from emailsec.arc import check_arc, ARCCheck, ARCChainStatus
import emailsec._utils

__all__ = [
    "authenticate_message",
    "AuthenticationResult",
    "DeliveryAction",
    "SMTPContext",
]


class DeliveryAction(Enum):
    """Final delivery results based on the authentication checks."""

    ACCEPT = "accept"
    QUARANTINE = "quarantine"
    REJECT = "reject"
    DEFER = "defer"  # SMTP server should return 451 4.3.0 Temporary lookup failure


@dataclass
class SMTPContext:
    """Context from the SMTP server processing the incoming email."""

    # Connection info
    sender_ip_address: str
    client_hostname: str | None  # EHLO/HELO hostname

    # Envelope data
    mail_from: str  # MAIL FROM address (envelope sender)

    # TOOD: timestamp to check for expired signature?


def _make_delivery_decision(
    spf_check: SPFCheck,
    dkim_check: DKIMCheck,
    arc_check: ARCCheck,
    dmarc_check: DMARCCheck,
) -> DeliveryAction:
    """
    Delivery decision logic following RFC 7489.

    1. DMARC policy is enforced first (if the sender has one)
    2. If DMARC passes → Accept
    3. If no DMARC or policy is "none" → Check individual authentications
    4. Default to quarantine for unauthenticated mail

    RFC 7489: "DMARC-compliant Mail Receivers typically disregard any
    mail-handling directive discovered as part of an authentication mechanism
    where a DMARC record is also discovered that specifies a policy other than 'none'"

    RFC 7489 warns against rejecting on SPF fail before checking DMARC,
    as this could prevent legitimate mail that passes DKIM+DMARC.
    """
    # Defer the delivery decision if SPF, DKIM, or DMARC failed with a temp error
    if (
        spf_check.result == SPFResult.TEMPERROR
        or dkim_check.result == DKIMResult.TEMPFAIL
        or dmarc_check.result == DMARCResult.TEMPERROR
    ):
        return DeliveryAction.DEFER

    # DMARC policy takes precedence (RFC 7489 Section 6.3)
    if dmarc_check.result == DMARCResult.FAIL:
        match dmarc_check.policy:
            case DMARCPolicy.REJECT:
                # RFC 7489: "the Mail Receiver SHOULD reject the message"
                return DeliveryAction.REJECT
            case DMARCPolicy.QUARANTINE:
                # RFC 7489: "the Mail Receiver SHOULD place the message in
                # a quarantine area or folder instead of delivering it"
                return DeliveryAction.QUARANTINE
            case DMARCPolicy.NONE:
                # RFC 7489: "the Domain Owner requests no specific action
                # be taken regarding delivery of the message"
                pass  # Continue to fallback logic
            case None:
                # This should never happen since FAIL result requires a policy
                pass

    # If DMARC passes, accept
    if dmarc_check.result == DMARCResult.PASS:
        return DeliveryAction.ACCEPT

    # Fallback logic when DMARC is not available or policy is "none"
    # RFC 7489: "Final disposition of a message is always a matter of local policy"

    # Accept if any DKIM signature passes
    if dkim_check.result == DKIMResult.SUCCESS:
        return DeliveryAction.ACCEPT

    # Accept if SPF passes
    if spf_check.result == SPFResult.PASS:
        return DeliveryAction.ACCEPT

    # TODO: if no DMARC policy (or none), look for a trusted ARC to fallback to accept

    # Conservative default for unauthenticated mail
    return DeliveryAction.QUARANTINE


@dataclass
class AuthenticationResult:
    delivery_action: DeliveryAction
    spf_check: SPFCheck
    dkim_check: DKIMCheck
    dmarc_check: DMARCCheck | None
    arc_check: ARCCheck


async def authenticate_message(
    smtp_context: SMTPContext,
    raw_email: bytes,
    configuration: AuthenticationConfiguration | None = None,
) -> AuthenticationResult:
    """
    Authenticate an incoming email using SPF, DKIM, and DMARC.

    Authentication flow:
    1. SPF (RFC 7208): Verify the sending IP is authorized for the envelope sender domain
    2. DKIM (RFC 6376): Verify cryptographic signatures on the email
    3. ARC (RFC 8617): Check authentication chain if present (for forwarded mail)
    4. DMARC (RFC 7489): Evaluate if SPF/DKIM align with the From header domain
    5. Make delivery decision based on combined results

    Delivery decision logic following RFC 7489.

    1. DMARC policy is enforced first (if the sender has one)
    2. If DMARC passes, then accept
    3. If no DMARC or policy is "none", then check individual SPF/DKIM
    4. Default to quarantine for unauthenticated mail
    """
    body_and_headers = emailsec._utils.body_and_headers_for_canonicalization(raw_email)
    header_from_raw = emailsec._utils.header_value(body_and_headers[1], "from")

    # Extract domain from From header for DMARC evaluation (RFC 7489 Section 3.1)
    # From header can be "Name <email@domain.com>" or just "email@domain.com"
    _, email_address = parseaddr(header_from_raw)
    if not email_address or "@" not in email_address:
        # RFC 5322: From header must contain a valid email address
        # Malformed From header should result in rejection
        return AuthenticationResult(
            delivery_action=DeliveryAction.REJECT,
            spf_check=SPFCheck(SPFResult.NONE, "", "", "Malformed From header"),
            dkim_check=DKIMCheck(DKIMResult.PERMFAIL, None, None),
            dmarc_check=None,
            arc_check=ARCCheck(ARCChainStatus.NONE, "Malformed From header"),
        )

    header_from = email_address.partition("@")[2]

    # Step 1: SPF Check (RFC 7208)
    # RFC 7489: SPF authenticates the envelope sender domain
    spf_check = await check_spf(
        smtp_context.sender_ip_address,
        smtp_context.mail_from,
    )

    # Step 2: DKIM Verification (RFC 6376)
    # Performed independently of SPF per RFC 7489 Section 4.3
    dkim_check = await check_dkim(raw_email)

    # Step 3: ARC Processing (RFC 8617) - if ARC headers present
    # RFC 8617 Section 7.2: "allows Internet Mail Handler to potentially base
    # decisions of message disposition on authentication assessments"
    arc_check = await check_arc(raw_email, body_and_headers)

    # Step 4: DMARC Evaluation (RFC 7489)
    # RFC 7489: "A message satisfies the DMARC checks if at least one of the
    # supported authentication mechanisms produces a 'pass' result"
    dmarc_check = await check_dmarc(
        header_from=header_from,
        envelope_from=smtp_context.mail_from,
        spf_check=spf_check,
        dkim_check=dkim_check,
        arc_check=arc_check,
        configuration=configuration,
    )

    # Handle DMARC temp errors, defer for temporary DNS issues
    # (treat perm errors as "no DMARC policy" and continue processing)
    if dmarc_check.result == DMARCResult.TEMPERROR:
        return AuthenticationResult(
            delivery_action=DeliveryAction.DEFER,
            spf_check=spf_check,
            dkim_check=dkim_check,
            dmarc_check=dmarc_check,
            arc_check=arc_check,
        )

    # Step 5: Make delivery decision
    # RFC 7489: "Final disposition of a message is always a matter of local policy"
    return AuthenticationResult(
        delivery_action=_make_delivery_decision(
            spf_check, dkim_check, arc_check, dmarc_check
        ),
        spf_check=spf_check,
        dkim_check=dkim_check,
        dmarc_check=dmarc_check,
        arc_check=arc_check,
    )
