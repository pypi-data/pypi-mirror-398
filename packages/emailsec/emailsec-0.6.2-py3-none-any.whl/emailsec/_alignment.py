import typing

import publicsuffixlist

AlignmentMode = typing.Literal["relaxed", "strict"]


def is_spf_aligned(
    rfc5312_mail_from: str,
    rfc5322_from: str,
    mode: AlignmentMode = "relaxed",
) -> bool:
    match mode:
        case "strict":
            return rfc5312_mail_from.lower() == rfc5322_from.lower()
        case "relaxed":
            psl = publicsuffixlist.PublicSuffixList()
            return psl.privatesuffix(rfc5312_mail_from) == psl.privatesuffix(
                rfc5322_from
            )


def is_dkim_aligned(
    dkim_domain: str,
    rfc5322_from: str,
    mode: AlignmentMode = "relaxed",
) -> bool:
    match mode:
        case "strict":
            return dkim_domain.lower() == rfc5322_from.lower()
        case "relaxed":
            psl = publicsuffixlist.PublicSuffixList()
            return psl.privatesuffix(dkim_domain) == psl.privatesuffix(rfc5322_from)
