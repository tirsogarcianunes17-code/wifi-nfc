#!/usr/bin/env python3
"""Genera dist/ (index.html, wifi.mobileconfig, _headers) a partir de config.txt.

Uso:  python3 build.py
"""
import html
import json
import sys
import uuid
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).parent
DIST = ROOT / "dist"

# seguridad en config.json -> (EncryptionType de Apple, tipo en el QR WIFI:)
SECURITY = {
    "WPA":  ("WPA",  "WPA"),
    "WPA2": ("WPA2", "WPA"),
    "WPA3": ("WPA3", "WPA"),
    "WEP":  ("WEP",  "WEP"),
    "NONE": ("None", "nopass"),
}


def parse_config_txt(text: str) -> dict:
    """Formato clave = valor, una por linea. Lineas vacias y las que empiezan por # se ignoran."""
    cfg = {}
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            sys.exit(f"config.txt linea {n}: falta el signo = -> {raw!r}")
        key, _, value = line.partition("=")
        cfg[key.strip().lower()] = value.strip()
    return cfg


def load_config() -> dict:
    cfg = parse_config_txt((ROOT / "config.txt").read_text(encoding="utf-8"))
    missing = [k for k in ("ssid", "seguridad", "nombre_negocio", "url_publica") if not cfg.get(k)]
    if missing:
        sys.exit(f"config.txt: faltan campos {missing}")
    sec = cfg["seguridad"].upper()
    if sec not in SECURITY:
        sys.exit(f"config.txt: seguridad debe ser una de {list(SECURITY)}")
    if sec != "NONE" and not cfg.get("password"):
        sys.exit("config.txt: password es obligatorio salvo con seguridad NONE")
    oculta = cfg.get("oculta", "no").lower() in ("si", "sí", "yes", "true", "1")
    return {**cfg, "seguridad": sec, "password": cfg.get("password", ""), "oculta": oculta}


def qr_escape(value: str) -> str:
    # Caracteres especiales del formato WIFI: se escapan con barra invertida
    out = value
    for ch in ("\\", ";", ",", ":", '"'):
        out = out.replace(ch, "\\" + ch)
    return out


def wifi_qr_payload(cfg: dict) -> str:
    _, qr_type = SECURITY[cfg["seguridad"]]
    parts = [f"T:{qr_type}", f"S:{qr_escape(cfg['ssid'])}"]
    if qr_type != "nopass":
        parts.append(f"P:{qr_escape(cfg['password'])}")
    if cfg["oculta"]:
        parts.append("H:true")
    return "WIFI:" + ";".join(parts) + ";;"


def mobileconfig(cfg: dict) -> str:
    enc, _ = SECURITY[cfg["seguridad"]]
    # UUIDs deterministas: reinstalar el perfil sustituye al anterior en vez de duplicarlo
    ns = uuid.uuid5(uuid.NAMESPACE_URL, cfg["url_publica"])
    payload_uuid = str(uuid.uuid5(ns, "wifi-payload")).upper()
    profile_uuid = str(uuid.uuid5(ns, "profile")).upper()
    ident = "wifi." + cfg["ssid"].lower().replace(" ", "-")
    name = xml_escape(cfg["nombre_negocio"])
    ssid = xml_escape(cfg["ssid"])
    password_key = (
        f"      <key>Password</key>\n      <string>{xml_escape(cfg['password'])}</string>\n"
        if enc != "None" else ""
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>PayloadContent</key>
  <array>
    <dict>
      <key>AutoJoin</key>
      <true/>
      <key>EncryptionType</key>
      <string>{enc}</string>
      <key>HIDDEN_NETWORK</key>
      <{'true' if cfg['oculta'] else 'false'}/>
{password_key}      <key>SSID_STR</key>
      <string>{ssid}</string>
      <key>ProxyType</key>
      <string>None</string>
      <key>PayloadDescription</key>
      <string>Configura la red Wi-Fi de {name}</string>
      <key>PayloadDisplayName</key>
      <string>Wi-Fi {name}</string>
      <key>PayloadIdentifier</key>
      <string>{ident}.wifi</string>
      <key>PayloadType</key>
      <string>com.apple.wifi.managed</string>
      <key>PayloadUUID</key>
      <string>{payload_uuid}</string>
      <key>PayloadVersion</key>
      <integer>1</integer>
    </dict>
  </array>
  <key>PayloadDescription</key>
  <string>Conecta tu iPhone al Wi-Fi de {name}. Puedes eliminarlo cuando quieras desde Ajustes.</string>
  <key>PayloadDisplayName</key>
  <string>Wi-Fi {name}</string>
  <key>PayloadIdentifier</key>
  <string>{ident}</string>
  <key>PayloadOrganization</key>
  <string>{name}</string>
  <key>PayloadRemovalDisallowed</key>
  <false/>
  <key>PayloadType</key>
  <string>Configuration</string>
  <key>PayloadUUID</key>
  <string>{profile_uuid}</string>
  <key>PayloadVersion</key>
  <integer>1</integer>
</dict>
</plist>
"""


def render_html(cfg: dict) -> str:
    template = (ROOT / "template.html").read_text(encoding="utf-8")
    client = {
        "ssid": cfg["ssid"],
        "password": cfg["password"],
        "open": cfg["seguridad"] == "NONE",
        "qr": wifi_qr_payload(cfg),
    }
    replacements = {
        "{{NOMBRE}}": html.escape(cfg["nombre_negocio"]),
        "{{SSID}}": html.escape(cfg["ssid"]),
        "{{PASSWORD}}": html.escape(cfg["password"]),
        "{{URL}}": html.escape(cfg["url_publica"]),
        "{{CONFIG_JSON}}": json.dumps(client, ensure_ascii=False).replace("</", "<\\/"),
    }
    out = template
    for key, value in replacements.items():
        out = out.replace(key, value)
    return out


HEADERS = """/wifi.mobileconfig
  Content-Type: application/x-apple-aspen-config
  Content-Disposition: attachment; filename="wifi.mobileconfig"
  Cache-Control: no-cache
/index.html
  Cache-Control: no-cache
"""


def main() -> None:
    cfg = load_config()
    DIST.mkdir(exist_ok=True)
    (DIST / "index.html").write_text(render_html(cfg), encoding="utf-8")
    (DIST / "wifi.mobileconfig").write_text(mobileconfig(cfg), encoding="utf-8")
    (DIST / "_headers").write_text(HEADERS, encoding="utf-8")
    print(f"OK  dist/ generado para «{cfg['ssid']}» ({cfg['seguridad']})")
    print(f"    Graba esta URL en la etiqueta NFC: {cfg['url_publica']}")


if __name__ == "__main__":
    main()
