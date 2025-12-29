# emailsec

[![builds.sr.ht status](https://builds.sr.ht/~tsileo/emailsec.svg)](https://builds.sr.ht/~tsileo/emailsec?)
[![PyPI version](https://badge.fury.io/py/emailsec.svg)](https://pypi.org/project/emailsec/)

`emailsec` authenticates incoming emails with SPF, DKIM, DMARC, and ARC.

**This project is still in early development.**

## Features

### Authentication Protocols

- **SPF** (Sender Policy Framework) - [RFC 7208](https://tools.ietf.org/html/rfc7208)  
  Verifies the sending IP address is authorized to send email for a domain

- **DKIM** (DomainKeys Identified Mail) - [RFC 6376](https://tools.ietf.org/html/rfc6376)  
  Validates email authenticity using cryptographic signatures
  
- **DMARC** (Domain-based Message Authentication, Reporting, and Conformance) - [RFC 7489](https://tools.ietf.org/html/rfc7489)  
  Combines SPF and DKIM results with policy enforcement

- **ARC** (Authenticated Received Chain) - [RFC 8617](https://tools.ietf.org/html/rfc8617)  
  Preserves authentication results across email forwarding

### Reputation

- **DNSBL** (DNS-based Blacklists) - [RFC 5782](https://tools.ietf.org/html/rfc5782)  
  Checks sender IP addresses against DNS blacklists for reputation filtering

## Usage

### Message Authentication

```python
>>> import asyncio
>>> from emailsec import authenticate_message, SMTPContext
>>>
>>> smtp_ctx = SMTPContext(
...     sender_ip_address="203.0.113.42",
...     client_hostname="mail.example.com",
...     mail_from="alice@example.com",
... )
>>> raw_email = b"""From: Alice <alice@example.com>
... To: Bob <bob@company.com>
... Subject: Hello from the conference
... Date: Mon, 27 Jan 2025 10:30:45 +0000
... Message-ID: <20250127103045.4A8B2@mail.example.com>
... Content-Type: text/plain; charset=UTF-8
... DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=example.com;
...     s=selector1; h=from:to:subject:date:message-id;
...     bh=eKhvPb2btxd7/zv/sYlR5Z4ws09I2c1WJzPa=;
...     b=C70Bf8rWjJZJt/RcOnoFJquifA1XNB/yiKVP==
...
... Hi Bob,
...
... Cheers,
... Alice
... """
>>>
>>> asyncio.run(authenticate_message(smtp_ctx, raw_email))
AuthenticationResult(
    delivery_action=<DeliveryAction.ACCEPT: 'accept'>,
    spf_check=SPFCheck(
        result=<SPFResult.PASS: 'pass'>,
        domain="example.com",
        sender_ip="203.0.113.42",
        exp=""
    ),
    dkim_check=DKIMCheck(
        result=<DKIMResult.SUCCESS: 'SUCCESS'>,
        domain="example.com",
        selector="selector1",
        signature={
            'v': '1',
            'a': 'rsa-sha256',
            'c': 'relaxed/relaxed',
            'd': 'example.com',
            'h': 'from:to:subject:date:message-id',
            's': 'selector1',
            'bh': 'eKhvPb2btxd7/zv/sYlR5Z4ws09I2c1WJzPa...',
            'b': 'C70Bf8rWjJZJt/RcOnoFJquifA1XNB/yiKVP...'
        }
    ),
    dmarc_check=DMARCCheck(
        result=<DMARCResult.PASS: 'pass'>,
        policy=<DMARCPolicy.QUARANTINE: 'quarantine'>,
        spf_aligned=True,
        dkim_aligned=True,
        arc_override_applied=False
    ),
    arc_check=ARCCheck(
        result=<ARCChainStatus.NONE: 'none'>,
        exp="No ARC Sets",
        signer=None,
        aar_header=None
    )
)
```

### DNSBL

```python
>>> from emailsec.dnsbl import DNSBLChecker
>>> asyncio.run(DNSBLChecker().check_ip("172.235.181.217", ["zen.spamhaus.org"]))
DNSBLResult(
    ip_address='172.235.181.217',
    is_listed=True,
    listed_on=['zen.spamhaus.org'],
    entries={
        'zen.spamhaus.org': DNSBLEntry(
            return_code='127.0.0.3',
            description='Listed by CSS, see https://check.spamhaus.org/query/ip/172.235.181.217'
        )
    },
    failed_queries=[]
)
```

### Sender Policy Framework

[RFC 7208](https://datatracker.ietf.org/doc/html/rfc7208)-compliant parser and checker.

#### Parser

```python
>>> from emailsec.spf.parser import parse_record
>>> parse_record("v=spf1 +a mx/30 mx:example.org/30 -all")
[A(qualifier=<Qualifier.PASS: '+'>, domain_spec=None, cidr=None),
 MX(qualifier=<Qualifier.PASS: '+'>, domain_spec=None, cidr='/30'),
 MX(qualifier=<Qualifier.PASS: '+'>, domain_spec='example.org', cidr='/30'),
 All(qualifier=<Qualifier.FAIL: '-'>)]
```

#### Checker

```python
>>> import asyncio
>>> from emailsec.spf import check_spf
>>> asyncio.run(check_spf(sender_ip="192.0.2.10", sender="hello@example.com"))
SPFCheck(result=<SPFResult.PASS: 'pass'>, domain='example.com', sender_ip='192.0.2.10', exp='')
```

### DKIM

[RFC 6376](https://datatracker.ietf.org/doc/html/rfc6376)-compliant signature verification.

```python
>>> import asyncio
>>> from emailsec.dkim import check_dkim
>>> asyncio.run(check_dkim(raw_email))
DKIMCheck(result=<DKIMResult.SUCCESS: 'SUCCESS'>, domain='example.com', selector='selector1', ...)
```

### ARC

[RFC 8617](https://datatracker.ietf.org/doc/html/rfc8617)-compliant chain validation.

```python
>>> import asyncio
>>> from emailsec.arc import check_arc
>>> asyncio.run(check_arc(raw_email))
ARCCheck(result=<ARCChainStatus.PASS: 'pass'>, signer='forwarder.example', ...)
```

### DMARC

[RFC 7489](https://datatracker.ietf.org/doc/html/rfc7489)-compliant policy lookup and evaluation.

```python
>>> import asyncio
>>> from emailsec.dmarc import get_dmarc_policy
>>> asyncio.run(get_dmarc_policy("example.com"))
(DMARCRecord(policy=<DMARCPolicy.REJECT: 'reject'>, spf_mode='relaxed', dkim_mode='relaxed'), None)
```

### Optimizing Multiple Checks

When running multiple checks on the same message (e.g., DKIM and ARC), you can parse the message once and reuse it:

```python
>>> from emailsec import body_and_headers_for_canonicalization
>>> from emailsec.dkim import check_dkim
>>> from emailsec.arc import check_arc
>>>
>>> # Parse once
>>> body_and_headers = body_and_headers_for_canonicalization(raw_email)
>>>
>>> # Reuse for both checks
>>> dkim_result = await check_dkim(raw_email, body_and_headers)
>>> arc_result = await check_arc(raw_email, body_and_headers)
```

## Documentation

Project documentation is available at https://emailsec.hexa.ninja/.

## Contribution

Contributions are welcome but please open an issue to start a discussion before starting something consequent.

## License

Copyright (c) 2025 Thomas Sileo and contributors. Released under the MIT license.
