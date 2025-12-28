from __future__ import annotations
from ..imports import *
from .path_utils import *

import os
import subprocess
from .error_utils import *
OVERRIDES = {
    ("TS2307", "path"): ["yarn add -D @types/node"]
}

def apply_overrides(rules):
    for r in rules:
        key = (r["codes"][0], r["vars"][0])
        if key in OVERRIDES:
            r["fixes"] = OVERRIDES[key]
    return rules
import os, subprocess
from abstract_react import run_build_get_errors, get_entry_output

# Special overrides for known tricky modules
OVERRIDES = {
    ("TS2307", "path"): ["yarn add -D @types/node"],
    ("TS2307", "fs"):   ["yarn add -D @types/node"],
}

def derive_rules_from_entries(entries):
    """Turn parsed TS errors into fix rules (guesses)."""
    rules = []
    for e in entries:
        code = e.get("code")
        for v in e.get("vars", []):
            fixes = []
            if code == "TS2307":  # Cannot find module
                if v.startswith("@"):
                    fixes.append(f"yarn add {v}")
                else:
                    fixes.append(f"yarn add {v}")
                # Add types, unless it's a Node built-in
                fixes.append(f"yarn add -D @types/{v.replace('@','').replace('/','__')}")
            elif code == "TS7016":  # Missing declaration file
                fixes.append("mkdir -p src/types")
                fixes.append(f'echo "declare module \'{v}\';" >> src/types/shims.d.ts')

            # Apply overrides
            key = (code, v)
            if key in OVERRIDES:
                fixes = OVERRIDES[key]

            if fixes:
                rules.append({"codes": [code], "vars": [v], "fixes": fixes})
    return rules

def apply_fixes(rules):
    """Run each fix shell command in order."""
    applied = []
    for r in rules:
        for cmd in r["fixes"]:
            print(f"⚡ Applying: {cmd}")
            subprocess.run(cmd, shell=True, check=False)
            applied.append(cmd)
    return applied


def suggest_fixes(entries):
    """Return a list of suggested shell commands to fix TS errors."""
    fixes = []
    for e in entries:
        code = e.get("code")
        for var in e.get("vars", []):
            if code in AUTO_FIXES and var in AUTO_FIXES[code]:
                fixes.extend(AUTO_FIXES[code][var])
    # deduplicate while preserving order
    seen = set()
    return [f for f in fixes if not (f in seen or seen.add(f))]

def apply_fixes(fixes, *, auto=False):
    """Run suggested fixes. If auto=False, ask before running each."""
    applied = []
    for cmd in fixes:
        if auto:
            print(f"⚡ Applying fix: {cmd}")
            subprocess.run(cmd, shell=True, check=False)
            applied.append(cmd)
        else:
            ans = input(f"Run fix? {cmd} [y/N]: ").strip().lower()
            if ans.startswith("y"):
                print(f"⚡ Applying fix: {cmd}")
                subprocess.run(cmd, shell=True, check=False)
                applied.append(cmd)
    return applied

def fix_errors(parsed_output, *, auto=False):
    """Suggest and optionally apply fixes given parsed tsc/vite output."""
    errors = parsed_output.get("errors", [])
    fixes = suggest_fixes(errors)
    if not fixes:
        print("✅ No known fixes found.")
        return []
    print("🛠 Suggested fixes:")
    for f in fixes:
        print("   ", f)
    return apply_fixes(fixes, auto=auto)
def derive_fixes(parsed_output):
    """Inspect parsed entries and suggest fixes dynamically."""
    entries = parsed_output.get("errors", [])
    fixes = []
    for e in entries:
        code = e.get("code")
        for rule in FIX_RULES:
            if code in rule["codes"]:
                for v in e.get("vars", []):
                    if v in rule["vars"]:
                        fixes.extend(rule["fixes"])
    # Deduplicate while preserving order
    seen = set()
    return [f for f in fixes if not (f in seen or seen.add(f))]
def apply_and_retry(parsed_output, build_cmd="yarn build", auto=False):
    fixes = derive_fixes(parsed_output)
    if not fixes:
        print("✅ No known fixes.")
        return parsed_output
    
    print("🛠 Suggested fixes:")
    for f in fixes:
        print("   ", f)

    for cmd in fixes:
        if auto or input(f"Run fix? {cmd} [y/N]: ").lower().startswith("y"):
            print(f"⚡ Applying: {cmd}")
            subprocess.run(cmd, shell=True, check=False)

    # retry build
    print("🔄 Retrying build...")
    subprocess.run(build_cmd, shell=True, check=False)
