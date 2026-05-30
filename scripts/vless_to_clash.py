#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import parse_qs, unquote, urlparse


RULE_PROVIDERS = """rule-providers:
  advertising:
    type: http
    behavior: domain
    url: https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/category-ads-all.yaml
    path: ./ruleset/advertising.yaml
    interval: 86400

  cn-sites:
    type: http
    behavior: domain
    url: https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/cn.yaml
    path: ./ruleset/cn-sites.yaml
    interval: 86400

  cn-ip:
    type: http
    behavior: ipcidr
    url: https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geoip/cn.yaml
    path: ./ruleset/cn-ip.yaml
    interval: 86400

  geolocation-no-cn:
    type: http
    behavior: domain
    url: https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/geolocation-!cn.yaml
    path: ./ruleset/geolocation-no-cn.yaml
    interval: 86400
"""


def yaml_scalar(value: object) -> str:
    text = "" if value is None else str(value)
    if text == "":
        return '""'
    if re.match(r"^[A-Za-z0-9_./:@%+=,!-]+$", text):
        return text
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def first(query: Dict[str, List[str]], key: str, default: str = "") -> str:
    values = query.get(key)
    return values[0] if values else default


def slugify(text: str) -> str:
    text = unquote(text).strip()
    text = re.sub(r"^THX-", "", text)
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "vless-node"


def parse_vless(link: str, name_override: Optional[str] = None) -> Dict[str, object]:
    link = link.strip()
    if not link:
        raise ValueError("empty VLESS link")
    parsed = urlparse(link)
    if parsed.scheme.lower() != "vless":
        raise ValueError("expected vless:// link")
    if not parsed.username:
        raise ValueError("missing UUID in VLESS link")
    if not parsed.hostname:
        raise ValueError("missing server host in VLESS link")
    if not parsed.port:
        raise ValueError("missing server port in VLESS link")

    query = parse_qs(parsed.query, keep_blank_values=True)
    name = name_override or unquote(parsed.fragment or parsed.hostname)
    security = first(query, "security")
    tls = security in ("reality", "tls")
    network = first(query, "type", "tcp")

    node: Dict[str, object] = {
        "name": name,
        "type": "vless",
        "server": parsed.hostname,
        "port": parsed.port,
        "uuid": parsed.username,
        "network": network,
        "tls": tls,
        "udp": True,
    }

    flow = first(query, "flow")
    if flow:
        node["flow"] = flow

    sni = first(query, "sni")
    if sni:
        node["servername"] = sni

    fp = first(query, "fp")
    if fp:
        node["client-fingerprint"] = fp

    if security == "reality":
        reality: Dict[str, str] = {}
        public_key = first(query, "pbk")
        short_id = first(query, "sid")
        spider_x = first(query, "spx")
        if public_key:
            reality["public-key"] = public_key
        if short_id:
            reality["short-id"] = short_id
        if spider_x:
            reality["spider-x"] = unquote(spider_x)
        node["reality-opts"] = reality

    return node


def render_proxy(node: Dict[str, object]) -> str:
    lines = [
        "- client-fingerprint: " + yaml_scalar(node.get("client-fingerprint", "chrome")),
    ]
    if node.get("flow"):
        lines.append("  flow: " + yaml_scalar(node["flow"]))
    lines.extend(
        [
            "  name: " + yaml_scalar(node["name"]),
            "  network: " + yaml_scalar(node.get("network", "tcp")),
            "  port: " + yaml_scalar(node["port"]),
        ]
    )
    reality = node.get("reality-opts")
    if isinstance(reality, dict) and reality:
        lines.append("  reality-opts:")
        for key in ("public-key", "short-id", "spider-x"):
            if key in reality:
                lines.append("    " + key + ": " + yaml_scalar(reality[key]))
    lines.extend(
        [
            "  server: " + yaml_scalar(node["server"]),
            "  servername: " + yaml_scalar(node.get("servername", "")),
            "  tls: " + ("true" if node.get("tls") else "false"),
            "  type: vless",
            "  udp: " + ("true" if node.get("udp", True) else "false"),
            "  uuid: " + yaml_scalar(node["uuid"]),
        ]
    )
    return "\n".join(lines)


def render_proxies(nodes: List[Dict[str, object]]) -> str:
    return "proxies:\n" + "\n".join(render_proxy(node) for node in nodes) + "\n"


def render_group(nodes: List[Dict[str, object]]) -> str:
    lines = [
        "proxy-groups:",
        "- name: PROXY",
        "  proxies:",
    ]
    for node in nodes:
        lines.append("  - " + yaml_scalar(node["name"]))
    lines.extend(["  - DIRECT", "  type: select", ""])
    return "\n".join(lines)


def render_global(nodes: List[Dict[str, object]]) -> str:
    return render_proxies(nodes) + render_group(nodes) + "rules:\n- MATCH,PROXY\n"


def render_rule(nodes: List[Dict[str, object]], direct_ips: Iterable[str]) -> str:
    lines = [
        render_proxies(nodes).rstrip(),
        render_group(nodes).rstrip(),
        RULE_PROVIDERS.rstrip(),
        "rules:",
    ]
    direct_list = [ip.strip() for ip in direct_ips if ip.strip()]
    if direct_list:
        lines.append("  # Direct company/VPS IPs to avoid proxying back into origin servers")
        for ip in direct_list:
            cidr = ip if "/" in ip else ip + "/32"
            lines.append("  - IP-CIDR," + cidr + ",DIRECT,no-resolve")
        lines.append("")

    lines.extend(
        [
            "  # LAN and local traffic",
            "  - IP-CIDR,127.0.0.0/8,DIRECT,no-resolve",
            "  - IP-CIDR,10.0.0.0/8,DIRECT,no-resolve",
            "  - IP-CIDR,172.16.0.0/12,DIRECT,no-resolve",
            "  - IP-CIDR,192.168.0.0/16,DIRECT,no-resolve",
            "  - IP-CIDR,169.254.0.0/16,DIRECT,no-resolve",
            "  - IP-CIDR,224.0.0.0/4,DIRECT,no-resolve",
            "",
            "  # NTP direct to avoid time drift affecting Reality",
            "  - DST-PORT,123,DIRECT",
            "",
            "  # Ads",
            "  - RULE-SET,advertising,REJECT",
            "",
            "  # China sites and China IPs direct",
            "  - RULE-SET,cn-sites,DIRECT",
            "  - RULE-SET,cn-ip,DIRECT",
            "  - GEOIP,CN,DIRECT",
            "",
            "  # Foreign and unknown traffic through proxy",
            "  - RULE-SET,geolocation-no-cn,PROXY",
            "  - MATCH,PROXY",
            "",
        ]
    )
    return "\n".join(lines)


def read_links(args: argparse.Namespace) -> List[str]:
    links: List[str] = []
    for item in args.input or []:
        links.extend(extract_links(item))
    if args.input_file:
        links.extend(extract_links(Path(args.input_file).read_text()))
    if not links:
        raise SystemExit("No vless:// links supplied. Use --input or --input-file.")
    return links


def extract_links(text: str) -> List[str]:
    return re.findall(r"vless://[^\s；;]+", text)


def write_qr(path: Path, payload: str) -> bool:
    try:
        import qrcode  # type: ignore
    except Exception:
        return False
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(path)
    return True


def usage_markdown(
    basename: str,
    nodes: List[Dict[str, object]],
    links: List[str],
    outputs: Dict[str, Path],
    publish_base: Optional[str],
    qr_paths: List[Path],
) -> str:
    public_global = public_rule = None
    if publish_base:
        base = publish_base.rstrip("/")
        if "global" in outputs:
            public_global = base + "/" + outputs["global"].name
        if "rule" in outputs:
            public_rule = base + "/" + outputs["rule"].name

    lines = [
        "# VLESS to Clash 输出说明",
        "",
        "## 节点",
    ]
    for node in nodes:
        lines.append("- `" + str(node["name"]) + "` -> `" + str(node["server"]) + ":" + str(node["port"]) + "`")

    lines.extend(["", "## 文件"])
    for key, path in outputs.items():
        lines.append("- " + key + ": `" + str(path) + "`")

    if public_global or public_rule:
        lines.extend(["", "## 订阅链接"])
        if public_global:
            lines.append("- Clash 全局版: `" + public_global + "`")
        if public_rule:
            lines.append("- Clash 规则版: `" + public_rule + "`")
        lines.append("")
        lines.append("订阅链接只有在这些 YAML 文件已经上传到对应 Web 目录后才可用。")

    lines.extend(
        [
            "",
            "## 怎么用",
            "- Clash / Clash Verge: 优先导入规则版 YAML 或规则版订阅链接；全局版主要用于测试。",
            "- Shadowrocket: 扫 VLESS 节点二维码，或粘贴原始 `vless://` 链接。",
            "- v2rayN: 导入原始 `vless://` 链接；Clash 规则 YAML 适用于 Clash/Mihomo 客户端。",
            "",
            "## 原始 VLESS 链接",
        ]
    )
    for link in links:
        lines.append("```text")
        lines.append(link)
        lines.append("```")

    if qr_paths:
        lines.extend(["", "## 二维码"])
        for qr in qr_paths:
            lines.append("- `" + str(qr) + "`")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert vless:// links to Clash/Mihomo YAML files.")
    parser.add_argument("--input", action="append", help="vless:// link or text containing links. Repeatable.")
    parser.add_argument("--input-file", help="File containing vless:// links.")
    parser.add_argument("--output-dir", default=".", help="Output directory.")
    parser.add_argument("--basename", help="Output file prefix.")
    parser.add_argument("--name", help="Override the first node name.")
    parser.add_argument("--mode", choices=["global", "rule", "both"], default="both")
    parser.add_argument("--direct-ip", action="append", default=[], help="IP/CIDR to force DIRECT in rule mode. Repeatable.")
    parser.add_argument("--publish-base", help="Public base URL used to describe subscription links.")
    parser.add_argument("--no-qr", action="store_true", help="Do not generate QR images.")
    args = parser.parse_args()

    links = read_links(args)
    nodes: List[Dict[str, object]] = []
    for idx, link in enumerate(links):
        nodes.append(parse_vless(link, args.name if idx == 0 else None))

    basename = args.basename or slugify(str(nodes[0]["name"]))
    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    outputs: Dict[str, Path] = {}
    if args.mode in ("global", "both"):
        path = out_dir / (basename + "-global.yaml")
        path.write_text(render_global(nodes))
        outputs["global"] = path
    if args.mode in ("rule", "both"):
        path = out_dir / (basename + "-rule.yaml")
        path.write_text(render_rule(nodes, args.direct_ip))
        outputs["rule"] = path

    raw_path = out_dir / (basename + "-vless.txt")
    raw_path.write_text("\n".join(links) + "\n")
    outputs["vless"] = raw_path

    qr_paths: List[Path] = []
    if not args.no_qr:
        qr_dir = out_dir / "qr"
        qr_dir.mkdir(exist_ok=True)
        for idx, link in enumerate(links, start=1):
            node_slug = slugify(str(nodes[idx - 1]["name"]))
            qr_path = qr_dir / (node_slug + "-vless-qr.png")
            if write_qr(qr_path, link):
                qr_paths.append(qr_path)
        if args.publish_base:
            base = args.publish_base.rstrip("/")
            for key in ("global", "rule"):
                if key in outputs:
                    qr_path = qr_dir / (basename + "-" + key + "-subscription-qr.png")
                    if write_qr(qr_path, base + "/" + outputs[key].name):
                        qr_paths.append(qr_path)

    usage_path = out_dir / (basename + "-USAGE.md")
    usage_path.write_text(usage_markdown(basename, nodes, links, outputs, args.publish_base, qr_paths))
    outputs["usage"] = usage_path

    print("Generated artifacts:")
    for key, path in outputs.items():
        print(f"- {key}: {path}")
    for path in qr_paths:
        print(f"- qr: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
