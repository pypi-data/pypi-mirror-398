#!/usr/bin/env python3
import argparse
import sys
import shutil
import subprocess
import yaml
import json
import os
from pathlib import Path

# --- Configuration ---
SECRETS_YAML_PATH = "secrets.yaml"
LOCAL_ENV_FILE = ".env.local"
PROTON_CLI_CMD = "pass-cli"  # Der Befehl für Proton Pass

def check_dependencies(target):
    """Prüft, ob nötige CLIs vorhanden sind."""
    if target == "github" and not shutil.which("gh"):
        print("❌ Error: 'gh' CLI is required for GitHub sync.")
        sys.exit(1)
    
    if not shutil.which(PROTON_CLI_CMD):
        # Nur Warnung, da man lokal evtl. nur Defaults nutzt
        print(f"⚠️  Warning: '{PROTON_CLI_CMD}' not found. You can only use defaults or manual input.")
        return False
    return True

def get_proton_secret(proton_path):
    """
    Holt ein Secret via Proton Pass CLI.
    Format: proton://Vault Name/Item Name/Field
    Robust gegen "Hidden" vs "Text" Felder.
    """
    if not proton_path or not proton_path.startswith("proton://"):
        return None
    
    clean_path = proton_path.replace("proton://", "")
    parts = clean_path.split("/")
    
    if len(parts) < 3:
        print(f"   ❌ Invalid path format: {clean_path} (Expected: Vault/Item/Field)")
        return None

    vault = parts[0]
    item = parts[1]
    field = parts[2]
    
    try:
        print(f"   🔄 Fetching [{vault}] -> [{item}] -> {field} ...", end="", flush=True)
        
        # Befehl: pass-cli item view ... --output json
        cmd = [
            PROTON_CLI_CMD, "item", "view",
            "--vault-name", vault,
            "--item-title", item,
            "--output", "json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(" [CLI ERROR]")
            # print(f"STDERR: {result.stderr}") # Uncomment for debug
            return None

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(" [JSON ERROR]")
            return None
        
        # --- JSON Parsing (Robust) ---
        val = None
        
        # 1. Root normalisieren: Manchmal ist alles in data['item'], manchmal direkt in data
        # Wir suchen das 'content' Objekt, das 'title' und 'extra_fields' enthält.
        item_root = data.get("item", data)
        content_root = item_root.get("content", {})
        
        # Falls Proton CLI Struktur sich ändert und content direkt im Root liegt:
        if "extra_fields" not in content_root and "extra_fields" in item_root:
             content_root = item_root

        # 2. Standard-Felder (username, password, url, note)
        if field == "password":
            val = content_root.get("password")
        elif field == "username":
            val = content_root.get("username")
        elif field == "note":
            val = content_root.get("note")
        elif field == "url":
             urls = content_root.get("urls", [])
             val = urls[0] if urls else None

        # 3. Extra Felder ('extra_fields' Liste durchsuchen)
        if val is None:
            extra_fields = content_root.get("extra_fields", [])
            
            for f in extra_fields:
                # Case-Insensitive Name Match
                if f.get("name", "").lower() == field.lower():
                    
                    # Inhalt holen
                    f_content = f.get("content", {})
                    
                    if isinstance(f_content, dict):
                        # Robustheit: Prüfe explizit auf die Keys, die Proton nutzt.
                        # Wir nutzen 'if ... in' statt 'get() or', damit auch leere Strings ("") valid sind.
                        
                        if "Hidden" in f_content:
                            val = f_content["Hidden"]
                        elif "Text" in f_content:
                            val = f_content["Text"]
                        elif "value" in f_content:
                            val = f_content["value"]
                        # Fallback für Lowercase Varianten (falls JSON sich ändert)
                        elif "hidden" in f_content:
                            val = f_content["hidden"]
                        elif "text" in f_content:
                            val = f_content["text"]
                    else:
                        # Fallback: Content ist direkt der Wert
                        val = str(f_content)
                    
                    # Wenn wir das Feld gefunden haben (auch wenn es leer ist), brechen wir ab
                    break
        
        if val is not None:
            print(" [OK]")
            return val
        else:
            print(f" [FIELD '{field}' NOT FOUND]")
            return None

    except Exception as e:
        print(f" [EXCEPTION: {e}]")
        return None
    
    
def sync_local(config, secrets_def, has_proton):
    print(f"📂 Syncing to {LOCAL_ENV_FILE} ...")
    
    output_lines = ["# Auto-generated local secrets from secrets.yaml"]
    
    for key, definition in secrets_def.items():
        dev_default = definition.get("dev_default")
        source = definition.get("source")
        
        value = ""
        
        # Strategie:
        # 1. Wenn dev_default existiert -> Nimm es (schnell, kein Proton nötig)
        # 2. Wenn dev_default NULL ist -> Wir brauchen zwingend den echten Wert (Proton)
        
        if dev_default is not None:
            value = str(dev_default)
            print(f"   ✅ {key}: Using dev_default")
        else:
            # Kein Default -> Wir müssen Proton fragen
            if has_proton and source:
                fetched = get_proton_secret(source)
                if fetched:
                    value = fetched
            
            # Fallback: Manuelle Eingabe (wenn Proton fehlt oder Fehler war)
            if not value:
                print(f"   ⚠️  {key}: No default and Proton fetch failed.")
                user_in = input(f"      Please enter value for {key}: ").strip()
                value = user_in
        
        output_lines.append(f"{key}={value}")
    
    with open(LOCAL_ENV_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
        f.write("\n")
    
    print(f"✅ Successfully wrote {LOCAL_ENV_FILE}")

def sync_github(config, secrets_def):
    target_repo = config.get("target_repo")
    if not target_repo:
        print("❌ Error: 'config.target_repo' missing in secrets.yaml")
        sys.exit(1)
        
    print(f"☁️  Syncing to GitHub Repo: {target_repo}")
    print("   (Fetching REAL secrets from Proton - ignoring defaults)")
    
    for key, definition in secrets_def.items():
        source = definition.get("source")
        
        if not source:
            print(f"   ⚠️  Skipping {key}: No 'source' defined in YAML.")
            continue
            
        value = get_proton_secret(source)
        
        if value:
            print(f"   🚀 Pushing {key} to GitHub...", end="", flush=True)
            
            # GH CLI aufrufen und Secret via Stdin pipen (sicherer & erhält Newlines)
            cmd = ["gh", "secret", "set", key, "--repo", target_repo]
            proc = subprocess.run(cmd, input=value, text=True, capture_output=True)
            
            if proc.returncode == 0:
                print(" [OK]")
            else:
                print(f" [ERROR]\n     {proc.stderr.strip()}")
        else:
            print(f"   ❌ Failed to fetch {key} from Proton.")

def main():
    parser = argparse.ArgumentParser(description="Sync secrets from Proton Pass to Local or GitHub.")
    parser.add_argument("--target", choices=["local", "github"], required=True, help="Destination for secrets")
    args = parser.parse_args()
    
    # Check dependencies
    has_proton = check_dependencies(args.target)
    
    # Load YAML
    if not Path(SECRETS_YAML_PATH).exists():
        print(f"❌ Error: {SECRETS_YAML_PATH} not found.")
        sys.exit(1)
        
    try:
        with open(SECRETS_YAML_PATH, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML: {e}")
        sys.exit(1)
    
    config = data.get("config", {})
    secrets_def = data.get("secrets", {})
    
    if not secrets_def:
        print("❌ Error: No 'secrets' block found in YAML.")
        sys.exit(1)

    # Dispatch
    if args.target == "local":
        sync_local(config, secrets_def, has_proton)
    elif args.target == "github":
        sync_github(config, secrets_def)

if __name__ == "__main__":
    main()

# python scripts/sync_secrets.py --target local
# python scripts/sync_secrets.py --target github