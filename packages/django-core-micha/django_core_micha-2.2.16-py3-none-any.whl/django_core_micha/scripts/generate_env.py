import argparse
import os
import sys
import yaml
import re
import json

def parse_env_file(path):
    """Liest eine .env Datei in ein Dictionary ein."""
    if not os.path.exists(path):
        return {}
    data = {}
    env_regex = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$')
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            match = env_regex.search(line)
            if match:
                key, val = match.groups()
                # Quotes entfernen
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                data[key] = val
    return data

def write_env_file(path, lines):
    try:
        with open(path, "w", encoding='utf-8') as f:
            f.write("\n".join(lines))
            f.write("\n")
        print(f"✅ Successfully wrote {path}")
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        sys.exit(1)

def generate_env(env_name, config_path="project.yaml", output_path=".env"):
    print(f"⚙️  Generating .env for environment: {env_name}")
    
    if not os.path.exists(config_path):
        print(f"❌ Error: Config file '{config_path}' not found.")
        sys.exit(1)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # 1. Input-Quellen laden (Die "Zutaten")
    # ---------------------------------------------------------
    inputs = {}

    # A) OS Environment (niedrigste Prio, oft System-Müll, daher selektiv nutzen)
    # Wir laden hier NICHT alles, um die .env nicht mit PATH etc. vollzumüllen.
    
    # B) Lokale .env.local (Von sync_secrets.py erstellt)
    if os.path.exists(".env.local"):
        print("   📂 Loading .env.local")
        inputs.update(parse_env_file(".env.local"))

    # C) GitHub Secrets Context (Via Action 'toJson(secrets)') - Höchste Prio für Secrets
    secrets_json = os.environ.get("SECRETS_CONTEXT")
    if secrets_json:
        try:
            print("   🔓 Loading SECRETS_CONTEXT from GitHub")
            github_secrets = json.loads(secrets_json)
            inputs.update(github_secrets)
        except json.JSONDecodeError:
            print("   ⚠️ Error decoding SECRETS_CONTEXT")

    if env_name == "edge" and os.path.exists(".env.edge"):
        print("   📂 Loading .env.edge (Edge Overrides)")
        edge_vars = parse_env_file(".env.edge")
        inputs.update(edge_vars)

    # D) Explizite Overrides aus OS (z.B. CI-Variablen, die keine Secrets sind)
    # Wenn eine Variable im OS gesetzt ist UND wir sie explizit erwarten (siehe unten),
    # hat sie Vorrang. (Hier vereinfacht: Wir nehmen Inputs so wie sie sind).

    # 2. Struktur-Daten aus project.yaml laden
    # ---------------------------------------------------------
    if env_name not in config.get("environments", {}):
        print(f"❌ Error: Environment '{env_name}' not defined in {config_path}")
        sys.exit(1)

    env_config = config["environments"][env_name]
    domains = env_config.get("domains", [])
    use_traefik = env_config.get("use_traefik", False)

    overrides = env_config.get("env_overrides", {})
    if overrides:
        print(f"   ⚡ Applying {len(overrides)} overrides from project.yaml")
        # Das update() überschreibt existierende Keys in inputs mit den Werten aus yaml
        inputs.update(overrides)
    
    # Prefix Logik
    base_prefix = config.get("container_prefix", "app")
    if env_name == "staging":
        ctr_prefix = f"{base_prefix}_stage"
    elif env_name == "production":
        ctr_prefix = f"{base_prefix}_prod"
    elif env_name == "edge":
        ctr_prefix = f"{base_prefix}_edge"
    else:
        ctr_prefix = base_prefix

    # 3. .env Zusammenbauen
    # ---------------------------------------------------------
    lines = []
    written_keys = set()

    def add(key, value):
        """Helper: Fügt Zeile hinzu, verhindert Duplikate."""
        if key not in written_keys:
            lines.append(f"{key}={value}")
            written_keys.add(key)
    
    # --- A. Infrastruktur & Meta (Berechnet) ---
    add("ENV_TYPE", env_name)
    add("PROJECT_NAME", config.get("project_name", "Project"))
    add("CONTAINER_NAME_PREFIX", ctr_prefix)
    add("ROUTER_NAME", f"{config.get('project_name')}-{env_name}")
    add("MFA_WEBAUTHN_RP_NAME", config.get("project_name"))
    
    # Volumes (Namen berechnen)
    vol_config = env_config.get("volumes", {})
    add("DB_VOLUME_NAME", vol_config.get("postgres_data", {}).get("name", f"{ctr_prefix}_postgres_data") if isinstance(vol_config.get("postgres_data"), dict) else vol_config.get("postgres_data", f"{ctr_prefix}_postgres_data"))
    add("MEDIA_VOLUME_NAME", vol_config.get("media_volume", {}).get("name", f"{ctr_prefix}_media_volume") if isinstance(vol_config.get("media_volume"), dict) else vol_config.get("media_volume", f"{ctr_prefix}_media_volume"))
    add("EXCEL_VOLUME_NAME", vol_config.get("excel_volume", {}).get("name", f"{ctr_prefix}_excel_volume") if isinstance(vol_config.get("excel_volume"), dict) else vol_config.get("excel_volume", f"{ctr_prefix}_excel_volume"))

    # --- B. Netzwerk & URLs (Berechnet + Inputs) ---
    
    # Master Base URL (aus erster Domain ableiten)
    if domains:
        add("MASTER_BASE_URL", f"https://{domains[0]}")
    
    # Master Public IP (aus yaml Config -> wichtig für SCP/Sync)
    if "master_public_ip" in env_config:
        add("MASTER_PUBLIC_IP", env_config["master_public_ip"])

    # Ports (kommen aus Inputs/Secrets, Fallback nur damit Berechnung nicht crasht)
    web_port = inputs.get("WEB_PORT", "8000") 
    
    # Allowed Hosts
    add("DJANGO_ALLOWED_HOSTS", ",".join(domains))
    
    # CSRF Trusted Origins
    protocol = "https" if use_traefik else "http"
    csrf_urls = [f"{protocol}://{d}" for d in domains]
    
    if env_name == "local":
        # Lokal fügen wir localhost ports hinzu
        csrf_urls.extend([
            "http://localhost:3000", "http://127.0.0.1:3000",
            f"http://localhost:{web_port}", f"http://127.0.0.1:{web_port}"
        ])
    
    add("CSRF_TRUSTED_URLS", ",".join(csrf_urls))
    
    # Public Origin
    main_domain = domains[0] if domains else "localhost"
    if env_name == "local" or not use_traefik:
         add("PUBLIC_ORIGIN", f"{protocol}://{main_domain}:{web_port}")
    else:
         add("PUBLIC_ORIGIN", f"{protocol}://{main_domain}")

    # Traefik Rules
    if use_traefik:
        rules = [f"Host(`{d}`)" for d in domains]
        add("TRAEFIK_ROUTER_RULE", " || ".join(rules))
    else:
        add("TRAEFIK_ROUTER_RULE", "Host(`localhost`)")


    # --- C. Der "Dumme" Teil: Alles aus Inputs übernehmen ---
    # Hier nehmen wir einfach alles, was sync_secrets.py oder GitHub geliefert hat.
    # Wir müssen keine Felder mehr einzeln definieren (DB_USER, MAIL_HOST, etc.)
    
    # Sortieren für schönere Datei
    print(f"   📥 Injecting {len(inputs)} variables from inputs...")
    
    for key in sorted(inputs.keys()):
        # Überspringe interne GitHub-Keys, leere Keys und SSH_ Keys
        if not key or key.startswith("GITHUB_") or key.startswith("SSH_"): 
            continue
            
        val = inputs[key]
        
        # Multiline Handling (z.B. für Zertifikate oder Public Keys)
        if isinstance(val, str) and "\n" in val:
            # FIX: Backslashes sind in f-strings < Python 3.12 verboten.
            # Wir berechnen den Wert vorher in einer Variable.
            clean_val = val.replace(chr(10), "\\n").replace(chr(13), "")
            val = f'"{clean_val}"'

        add(key, val)

    # 4. Schreiben
    write_env_file(output_path, lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True, help="Environment (production, staging, local)")
    parser.add_argument("--output", default=".env", help="Output file path")
    parser.add_argument("--config", default="project.yaml", help="Path to project.yaml")
    args = parser.parse_args()
    
    generate_env(args.env, config_path=args.config, output_path=args.output)

if __name__ == "__main__":
    main()