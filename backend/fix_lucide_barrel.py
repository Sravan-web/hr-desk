"""
fix_lucide_barrel.py
Creates the missing lucide-react barrel export file so vite can resolve it.
Also creates a CJS shim.
"""
import os, json

FRONTEND = "/Users/sravankumar/Desktop/HR Desk/frontend"
LR = FRONTEND + "/node_modules/lucide-react"
ESM = LR + "/dist/esm"

# Find all icon .mjs files
icons_dir = ESM + "/icons"
icon_files = []
if os.path.exists(icons_dir):
    icon_files = [f[:-4] for f in os.listdir(icons_dir) if f.endswith('.mjs') and not f.endswith('.map')]
    print(f"Found {len(icon_files)} icon files in dist/esm/icons/")
else:
    print("No icons dir found, checking ESM root...")
    icon_files = [f[:-4] for f in os.listdir(ESM) if f.endswith('.mjs') and not f.endswith('.map') and f not in ['createLucideIcon.mjs','context.mjs','Icon.mjs','DynamicIcon.mjs','defaultAttributes.mjs']]

# Build the barrel content
# Re-export from individual icon files
lines = [
    "// Auto-generated barrel export for lucide-react",
    "export { default as createLucideIcon } from './createLucideIcon.mjs';",
    "export { default as Icon } from './Icon.mjs';",
]

if icon_files:
    for icon in sorted(icon_files):
        lines.append(f"export {{ default as {icon} }} from './icons/{icon}.mjs';")
else:
    # Fallback: export the icons we actually use in the app
    used_icons = [
        'Send','Upload','FileText','Settings','User','Clock','MessageSquare',
        'AlertCircle','CheckCircle','Menu','X','ChevronRight','Sparkles','Loader2',
        'LayoutDashboard','Users','Calendar','DollarSign','Calculator','Shield',
        'BarChart2','LogOut','Bell','TrendingUp','TrendingDown','Plus','Search',
        'Edit2','Trash2','LogIn','LogOut','Info','Heart','Briefcase','Star',
        'Eye','EyeOff','Lock','Mail','Play','Phone','Building2','Download',
    ]
    # Check which ones exist as individual files
    for icon in used_icons:
        icon_path = ESM + f"/icons/{icon}.mjs"
        if os.path.exists(icon_path):
            lines.append(f"export {{ default as {icon} }} from './icons/{icon}.mjs';")

barrel_content = "\n".join(lines) + "\n"

# Write the barrel file
barrel_path = ESM + "/lucide-react.mjs"
with open(barrel_path, "w") as f:
    f.write(barrel_content)
print(f"Created barrel: {barrel_path} ({os.path.getsize(barrel_path)} bytes)")

# Also create a CJS directory and shim
cjs_dir = LR + "/dist/cjs"
os.makedirs(cjs_dir, exist_ok=True)

# Create a simple CJS shim that requires the ESM icons
cjs_lines = [
    '"use strict";',
    'Object.defineProperty(exports, "__esModule", { value: true });',
]

# Check if icons exist as individual files
if os.path.exists(icons_dir):
    for icon in sorted(icon_files[:50]):  # limit for size
        cjs_lines.append(f'var _{icon} = require("../esm/icons/{icon}.mjs");')
        cjs_lines.append(f'exports.{icon} = _{icon}.default || _{icon};')

cjs_content = "\n".join(cjs_lines) + "\n"
cjs_path = cjs_dir + "/lucide-react.js"
with open(cjs_path, "w") as f:
    f.write(cjs_content)
print(f"Created CJS shim: {cjs_path}")

# Update package.json to point to the barrel
pkg_path = LR + "/package.json"
with open(pkg_path) as f:
    pkg = json.load(f)

pkg["module"] = "dist/esm/lucide-react.mjs"
pkg["main"] = "dist/esm/lucide-react.mjs"  # point both to ESM barrel

with open(pkg_path, "w") as f:
    json.dump(pkg, f, indent=2)
print("Updated package.json to point to barrel")

# Clear vite cache
import shutil
cache = FRONTEND + "/node_modules/.vite"
if os.path.exists(cache):
    shutil.rmtree(cache)
    print("Cleared .vite cache")

print("\nDone!")
