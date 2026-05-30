# vless-to-clash

[English](README.md) | [中文](README.zh-CN.md)

Codex/Claude skill for converting `vless://` links into Clash/Mihomo configs, rule-based configs, subscription-ready files, and QR codes.

It is designed for VLESS + Reality + TCP + Vision links commonly exported by v2rayN, Shadowrocket, and 3X-UI.

## What It Generates

- Clash global YAML: all traffic goes through the proxy group.
- Clash rule YAML: LAN/China traffic goes `DIRECT`, foreign and unknown traffic goes through the proxy group.
- Raw `vless://` text file.
- VLESS QR codes for Shadowrocket/v2rayN/mobile import.
- Subscription QR codes when a public base URL is supplied.
- A `USAGE.md` explaining how to import each artifact.

## Install As A Skill

Clone this repository into your skills directory:

```bash
git clone https://github.com/haloshin/vless-to-clash.git ~/.claude/skills/vless-to-clash
```

For Codex setups that read from `~/.codex/skills`, create a symlink:

```bash
ln -s ~/.claude/skills/vless-to-clash ~/.codex/skills/vless-to-clash
```

## Script Usage

Run the bundled converter directly:

```bash
python3 scripts/vless_to_clash.py \
  --input "vless://..." \
  --output-dir ./outputs/app \
  --basename app \
  --mode both \
  --direct-ip 203.0.113.10
```

Useful options:

```text
--input LINK              One vless:// link. Can be repeated.
--input-file PATH         Text file containing vless:// links, one per line.
--output-dir PATH         Where to write artifacts.
--basename NAME           Output file prefix.
--name NAME               Override the first node name.
--mode global|rule|both   Generate global YAML, rule YAML, or both.
--direct-ip IP            Add direct IP bypass rule. Can be repeated.
--publish-base URL        Public base URL used to describe subscription links.
--no-qr                   Skip QR generation.
```

## Example

```bash
python3 scripts/vless_to_clash.py \
  --input "vless://UUID@example.com:443?security=reality&sni=www.example.com&fp=chrome&pbk=PUBLIC_KEY&sid=SHORT_ID&type=tcp&flow=xtls-rprx-vision#Example-US" \
  --output-dir ./outputs/example \
  --basename example-us \
  --mode both \
  --publish-base https://example.com/subs
```

Generated files:

```text
example-us-global.yaml
example-us-rule.yaml
example-us-vless.txt
example-us-USAGE.md
qr/
```

## Clash vs Shadowrocket/v2rayN

- Clash / Clash Verge / Mihomo: import the generated YAML file or a hosted YAML subscription URL.
- Shadowrocket: scan the VLESS QR code or paste the raw `vless://` link.
- v2rayN: import the raw `vless://` link.

Rule-based YAML is mainly for Clash/Mihomo clients. Shadowrocket and v2rayN have their own routing/rule behavior.

## Rule Mode

Rule mode uses MetaCubeX rule providers:

- `category-ads-all.yaml`
- `geosite/cn.yaml`
- `geoip/cn.yaml`
- `geosite/geolocation-!cn.yaml`

Default routing:

```text
LAN/private/direct IPs -> DIRECT
NTP -> DIRECT
ads -> REJECT
China domains/IPs -> DIRECT
foreign domains -> PROXY
unknown -> PROXY
```

Use `--direct-ip` for company/VPS IPs that should not be proxied back into the origin server.

## Security Notes

- Do not commit real production `vless://` links to public repositories.
- Do not commit server passwords, private keys, API keys, or 3X-UI credentials.
- Treat VLESS UUIDs and Reality public keys as sensitive distribution material when they identify a private proxy node.
- Generated QR codes can contain live proxy credentials; do not publish them unless intended.

## License

MIT
