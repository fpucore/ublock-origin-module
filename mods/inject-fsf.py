#!/usr/bin/env python3

#   
#    uBlock Origin (for H Navigator)
#        Guided by FSF principles for JavaScript freedom.
#    
#    Copyright (C) 2026 Chris McGimpsey-Jones
#    Copyright (C) 2014-2026 Raymond Hill
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see {http://www.gnu.org/licenses/}.
#

import json
import re
import shutil
import sys
from pathlib import Path

repo_dir = Path(sys.argv[1])
mods_dir = Path(sys.argv[2])

# Copy custom filter > source tree
source_filter = mods_dir / "fsf" / "fsf-oriented-proprietary-js-filter-v0.1.1.txt"
target_filter = repo_dir / "assets" / "fsf" / "fsf-oriented-proprietary-js-filter-v0.1.1.txt"

if not source_filter.is_file():
    sys.exit(f"FSF-oriented Proprietary JS Filter not found: {source_filter}")

target_filter.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(source_filter, target_filter)

# Load persistent custom asset def
entry_file = mods_dir / "fsf-assets-entry.json"

if not entry_file.is_file():
    sys.exit(f"FSF asset definition not found: {entry_file}")

with entry_file.open(encoding="utf-8") as f:
    custom_entries = json.load(f)

if not isinstance(custom_entries, dict):
    sys.exit("FSF asset definition must be a JSON object")

# Merge into both upstream asset registries
for filename in ("assets.json", "assets.dev.json"):
    manifest = repo_dir / "assets" / filename

    if not manifest.is_file():
        sys.exit(f"Upstream asset registry not found: {manifest}")

    with manifest.open(encoding="utf-8") as f:
        assets = json.load(f)

    if not isinstance(assets, dict):
        sys.exit(f"Invalid asset registry structure: {manifest}")

    assets.update(custom_entries)

    with manifest.open("w", encoding="utf-8") as f:
        json.dump(assets, f, ensure_ascii=False, indent=4)
        f.write("\n")

    print(f"Updated {filename}")

# Refresh the bundled registry even when an older registry is cached
assets_js = repo_dir / "src" / "js" / "assets.js"

old = """            if ( bin instanceof Object ) {
                if ( bin.assetSourceRegistry instanceof Object ) {
                    assetSourceRegistry = bin.assetSourceRegistry;
                    ubolog('Loaded assetSourceRegistry');
                    return assetSourceRegistry;
                }
            }
"""

new = """            if ( bin instanceof Object ) {
                if ( bin.assetSourceRegistry instanceof Object ) {
                    assetSourceRegistry = bin.assetSourceRegistry;
                    return assets.fetchText(µb.assetsJsonPath).then(details => {
                        if ( details.content !== '' ) {
                            updateAssetSourceRegistry(details.content, true);
                        }
                        ubolog('Loaded assetSourceRegistry');
                        return assetSourceRegistry;
                    });
                }
            }
"""

source = assets_js.read_text(encoding="utf-8")

if old in source:
    source = source.replace(old, new, 1)
    assets_js.write_text(source, encoding="utf-8")
    print("Patched assets.js: cached registry refresh enabled")
elif new in source:
    print("assets.js already contains the registry refresh patch")
else:
    sys.exit("ERROR: Could not locate the expected assets.js code. No patch applied.")

# Hide the dumb obsolete warning for bundled local filter lists
old = """            assetEntry.obsolete = true;
"""

new = """            assetEntry.obsolete = reIsExternalPath.test(assetEntry.contentURL);
"""

if old in source:
    source = source.replace(old, new, 1)
    assets_js.write_text(source, encoding="utf-8")
    print("Patched assets.js: local filter freshness warning suppressed")
elif new in source:
    print("assets.js already contains the local filter warning patch")
else:
    sys.exit("ERROR: Could not locate the expected obsolete-status code.")

# Set default accent color to red
background_js = repo_dir / "src" / "js" / "background.js"
source = background_js.read_text(encoding="utf-8")

pattern = (
    r"uiAccentCustom:\s*false\s*,\s*"
    r"uiAccentCustom0:\s*['\"]#aca0f7['\"]\s*,?"
)

replacement = (
    "uiAccentCustom: true,\n"
    "    uiAccentCustom0: '#e53935',"
)

source, count = re.subn(pattern, replacement, source, count=1)

if count:
    background_js.write_text(source, encoding="utf-8")
    print("Patched background.js: default accent color set to red")
elif re.search(
    r"uiAccentCustom:\s*true\s*,\s*"
    r"uiAccentCustom0:\s*['\"]#e53935['\"]",
    source
):
    print("background.js already contains the red accent defaults")
else:
    sys.exit("ERROR: Could not locate the expected accent settings.")

# Print success output
print(f"Installed FSF-oriented Proprietary JS Filter: {target_filter}")
