# Security Policy

## Sensitive Data

This repository is public. Do not commit:

- real production `vless://` links
- live proxy UUIDs, Reality public keys, short IDs, or generated QR codes for private nodes
- server passwords, SSH private keys, API keys, tokens, cookies, or 3X-UI credentials
- private server IPs when they identify non-public infrastructure

Use placeholders such as `UUID`, `PUBLIC_KEY`, `SHORT_ID`, `example.com`, and `203.0.113.10` in examples.

## Reporting Security Issues

If you find a security issue in this repository, please open a private report through GitHub Security Advisories when available, or contact the repository owner directly.

Please do not publish working private proxy credentials in public issues.

## Before Publishing Changes

Run a quick scan before pushing:

```bash
rg -n "vless://[A-Za-z0-9]{8}|pbk=|password|token|secret|api[_-]?key|private" . \
  --glob '!**/.git/**' \
  --glob '!**/.trash/**'
```

Then run the validation checks:

```bash
python3 -m py_compile scripts/vless_to_clash.py
python3 scripts/vless_to_clash.py \
  --input "vless://UUID@example.com:443?security=reality&sni=www.example.com&fp=chrome&pbk=PUBLIC_KEY&sid=SHORT_ID&type=tcp&flow=xtls-rprx-vision#Example-US" \
  --output-dir /tmp/vless-to-clash-check \
  --basename example-us \
  --mode both \
  --direct-ip 203.0.113.10 \
  --no-qr
```
