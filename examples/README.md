# Examples

These examples use placeholder values only. Do not commit real production proxy links or generated QR codes for private nodes.

## Example Input

```text
vless://UUID@example.com:443?security=reality&sni=www.example.com&fp=chrome&pbk=PUBLIC_KEY&sid=SHORT_ID&type=tcp&flow=xtls-rprx-vision#Example-US
```

## Generate Example Output

```bash
python3 ../scripts/vless_to_clash.py \
  --input "vless://UUID@example.com:443?security=reality&sni=www.example.com&fp=chrome&pbk=PUBLIC_KEY&sid=SHORT_ID&type=tcp&flow=xtls-rprx-vision#Example-US" \
  --output-dir ./generated \
  --basename example-us \
  --mode both \
  --direct-ip 203.0.113.10 \
  --no-qr
```

Expected artifacts:

```text
generated/example-us-global.yaml
generated/example-us-rule.yaml
generated/example-us-vless.txt
generated/example-us-USAGE.md
```
