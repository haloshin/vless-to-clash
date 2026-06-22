---
name: vless-to-clash
description: Convert vless:// proxy links, especially VLESS + Reality + TCP + Vision links from v2rayN/Shadowrocket/3X-UI, into Clash/Mihomo global YAML, rule-based YAML, subscription-ready files, QR codes, and user-facing import instructions. Use this skill whenever the user asks to turn VLESS links into Clash, Clash Verge, Mihomo, subscription links, YAML configs, QR codes, global mode configs, rule mode configs, or team-ready proxy distribution files.
---

# VLESS To Clash

Use this skill to turn one or more `vless://` links into clean Clash/Mihomo artifacts:

- global YAML: all traffic goes through the proxy group
- rule YAML: China/LAN/direct IPs go `DIRECT`, foreign/unknown traffic goes through the proxy group
- QR codes: one QR per raw `vless://` node, plus subscription QR codes when a public base URL is supplied
- usage notes: explain which file/link to use in Clash, Shadowrocket, and v2rayN

## Default Workflow

1. Collect one or more `vless://` links from the user.
2. Ask only for missing operational choices that materially affect output:
   - desired node name, if the link fragment is unclear
   - output folder, if the user wants files somewhere specific
   - public subscription base URL, if they want actual online subscription links
   - direct IPs, if trusted server IPs should bypass proxy in rule mode
3. Run `scripts/vless_to_clash.py`.
4. Validate the generated YAML by parsing it or at least checking the expected node names and rules.
5. Explain outputs plainly:
   - Clash/Clash Verge: use the YAML file or hosted subscription link.
   - Shadowrocket/v2rayN: use the raw `vless://` link or scan the VLESS QR.
   - Rule version: daily use, China direct/foreign proxy.
   - Global version: test/simple mode, everything goes proxy.

## Script

Use the bundled script for deterministic conversion:

```bash
python3 scripts/vless_to_clash.py \
  --input "vless://..." \
  --output-dir /path/to/output \
  --basename app \
  --mode both \
  --direct-ip 203.0.113.10
```

Useful options:

```text
--input LINK              One vless:// link. Can be repeated.
--input-file PATH         Text file containing vless:// links, one per line.
--output-dir PATH         Where to write artifacts.
--basename NAME           Output file prefix. Defaults to the first node name slug.
--name NAME               Override the first node name.
--mode global|rule|both   Which Clash YAML variants to generate.
--direct-ip IP            Add direct IP bypass rule. Can be repeated.
--publish-base URL        Public base URL for subscription links, e.g. https://example.com/subs.
--no-qr                   Skip QR generation.
```

If `--publish-base` is provided, the script writes subscription links into `USAGE.md` by combining:

```text
<publish-base>/<basename>-global.yaml
<publish-base>/<basename>-rule.yaml
```

The script does not upload files by itself. To make subscription links real, copy the generated YAML files to the web directory that serves that base URL.

## Mapping Rules

Parse the VLESS URL into Clash fields as follows:

```text
vless:// UUID             -> uuid
host after @              -> server
port after :              -> port
security=reality          -> tls: true + reality-opts
sni                       -> servername
fp                        -> client-fingerprint
pbk                       -> reality-opts.public-key
sid                       -> reality-opts.short-id
spx                       -> reality-opts.spider-x, when present
flow                      -> flow
type=tcp                  -> network: tcp
fragment after #          -> name
```

Ignore `encryption=none` and `headerType=none` for Clash output unless a future client requires them.

## Global YAML Shape

Use global mode for quick connectivity testing or users who explicitly want all traffic through the node:

```yaml
proxies:
  - name: NODE
    type: vless
    server: 1.2.3.4
    port: 443
    uuid: UUID
    network: tcp
    tls: true
    udp: true
    flow: xtls-rprx-vision
    servername: www.example.com
    client-fingerprint: chrome
    reality-opts:
      public-key: PUBLIC_KEY
      short-id: SHORT_ID

proxy-groups:
  - name: PROXY
    type: select
    proxies:
      - NODE
      - DIRECT

rules:
  - MATCH,PROXY
```

## Rule YAML Shape

Use rule mode for daily use:

```text
LAN/private/trusted server IPs -> DIRECT
NTP -> DIRECT
ads -> REJECT
China domains/IPs -> DIRECT
foreign domains -> PROXY
unknown -> PROXY
```

Use MetaCubeX rule providers:

```text
category-ads-all.yaml
geosite/cn.yaml
geoip/cn.yaml
geosite/geolocation-!cn.yaml
```

Place direct IP rules before LAN rules. For trusted proxy or subscription servers, add their IPs with `--direct-ip` so clients do not proxy back into the origin server.

## Team Distribution Guidance

When converting for team or organization proxy distribution:

- Keep different audience or permission groups in separate subscription files.
- Do not mix restricted nodes into ordinary subscriptions unless the user explicitly asks and has permission to distribute them.
- During testing, suffix node names with `-Rule`, such as `ACME-US-APP-Rule`.
- For final team distribution, prefer clean names without temporary testing suffixes, and explain that the subscription already contains rules.
- Provide both global and rule artifacts, but recommend rule mode for daily use.

## Output Explanation Template

After generating artifacts, answer with:

```text
已生成：
- 全局版 YAML：...
- 规则版 YAML：...
- VLESS 节点二维码：...
- 订阅二维码：...（如果提供 publish-base）
- 使用说明：...

怎么用：
- Clash / Clash Verge：导入规则版订阅链接或规则版 YAML；全局版只用于测试。
- Shadowrocket：扫 VLESS 节点二维码，或粘贴 vless:// 链接。
- v2rayN：导入 vless:// 链接；如果要 Clash 规则，需要用 Clash/Mihomo 客户端。
```
