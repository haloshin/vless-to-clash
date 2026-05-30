# vless-to-clash

[English](README.md) | [中文](README.zh-CN.md)

这是一个 Codex / Claude Skill，用来把 `vless://` 链接转换成 Clash / Mihomo 可用配置、规则版配置、可发布订阅文件和二维码。

它主要面向 v2rayN、Shadowrocket、3X-UI 常见导出的 VLESS + Reality + TCP + Vision 链接。

## 能生成什么

- Clash 全局版 YAML：所有流量都走代理。
- Clash 规则版 YAML：局域网 / 国内流量走 `DIRECT`，国外和未知流量走代理。
- 原始 `vless://` 链接文本文件。
- VLESS 二维码：适合 Shadowrocket、v2rayN、手机端扫码导入。
- 订阅二维码：提供公开访问地址时生成。
- `USAGE.md`：说明每个文件和二维码怎么用。

## 作为 Skill 安装

克隆到你的 skills 目录：

```bash
git clone https://github.com/haloshin/vless-to-clash.git ~/.claude/skills/vless-to-clash
```

如果你的 Codex 从 `~/.codex/skills` 读取 Skill，可以创建软链接：

```bash
ln -s ~/.claude/skills/vless-to-clash ~/.codex/skills/vless-to-clash
```

## 脚本用法

也可以直接运行转换脚本：

```bash
python3 scripts/vless_to_clash.py \
  --input "vless://..." \
  --output-dir ./outputs/app \
  --basename app \
  --mode both \
  --direct-ip 203.0.113.10
```

常用参数：

```text
--input LINK              一个 vless:// 链接，可重复传入。
--input-file PATH         包含 vless:// 链接的文本文件，每行一条。
--output-dir PATH         输出目录。
--basename NAME           输出文件名前缀。
--name NAME               覆盖第一个节点名称。
--mode global|rule|both   生成全局版、规则版，或两者都生成。
--direct-ip IP            规则版里强制直连的 IP，可重复传入。
--publish-base URL        公开订阅地址前缀，用来写入使用说明和生成订阅二维码。
--no-qr                   不生成二维码。
```

## 示例

```bash
python3 scripts/vless_to_clash.py \
  --input "vless://UUID@example.com:443?security=reality&sni=www.example.com&fp=chrome&pbk=PUBLIC_KEY&sid=SHORT_ID&type=tcp&flow=xtls-rprx-vision#Example-US" \
  --output-dir ./outputs/example \
  --basename example-us \
  --mode both \
  --publish-base https://example.com/subs
```

生成文件：

```text
example-us-global.yaml
example-us-rule.yaml
example-us-vless.txt
example-us-USAGE.md
qr/
```

## Clash、Shadowrocket、v2rayN 怎么用

- Clash / Clash Verge / Mihomo：导入生成的 YAML 文件，或导入已经托管到服务器上的 YAML 订阅链接。
- Shadowrocket：扫描 VLESS 二维码，或粘贴原始 `vless://` 链接。
- v2rayN：导入原始 `vless://` 链接。

规则版 YAML 主要给 Clash / Mihomo 客户端使用。Shadowrocket 和 v2rayN 有自己的分流规则机制，不一定直接使用 Clash 规则 YAML。

## 规则版逻辑

规则版使用 MetaCubeX 规则集：

- `category-ads-all.yaml`
- `geosite/cn.yaml`
- `geoip/cn.yaml`
- `geosite/geolocation-!cn.yaml`

默认路由逻辑：

```text
局域网 / 私有 IP / 指定直连 IP -> DIRECT
NTP 对时 -> DIRECT
广告 -> REJECT
中国大陆域名 / IP -> DIRECT
国外域名 -> PROXY
未知流量 -> PROXY
```

如果你的公司 VPS、订阅服务器或内部服务 IP 不希望被代理回源站，可以用 `--direct-ip` 加进去。

## 安全注意事项

- 不要把真实生产 `vless://` 链接提交到公开仓库。
- 不要提交服务器密码、私钥、API Key、3X-UI 面板账号密码。
- 当 VLESS UUID 和 Reality 参数对应私有节点时，也应视为敏感分发材料。
- 二维码里可能包含真实代理凭证；除非本来就是要公开分发，否则不要上传到公开仓库。

## License

MIT
