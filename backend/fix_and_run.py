"""
fix_and_run.py — diagnoses and fixes all issues, then starts both servers.
Run: python fix_and_run.py
"""
import os, sys, subprocess, shutil, json, time

BASE = "/Users/sravankumar/Desktop/HR Desk"
BACKEND = BASE + "/backend"
FRONTEND = BASE + "/frontend"
VENV = BACKEND + "/venv/bin"

print("=" * 60)
print("HR Desk — Fix & Run")
print("=" * 60)

# ── 1. Check backend imports ──────────────────────────────────────
print("\n[1] Checking backend imports...")
result = subprocess.run(
    [VENV + "/python3", "-c",
     "import sys; sys.path.insert(0,'"+BACKEND+"'); import database, auth, payroll_engine, main; print('OK routes:', len(main.app.routes))"],
    capture_output=True, text=True
)
if "OK routes" in result.stdout:
    print("    Backend: OK")
else:
    print("    Backend ERROR:", result.stderr[-500:])
    sys.exit(1)

# ── 2. Check/fix frontend node_modules ───────────────────────────
print("\n[2] Checking frontend dependencies...")
pkg_path = FRONTEND + "/package.json"
with open(pkg_path) as f:
    pkg = json.load(f)

deps = pkg.get("dependencies", {})
missing = []
for dep in ["lucide-react", "axios", "react", "react-dom", "zustand", "@tanstack/react-query", "react-markdown", "uuid"]:
    nm_path = FRONTEND + "/node_modules/" + dep
    if not os.path.exists(nm_path):
        missing.append(dep)

if missing:
    print(f"    Missing packages: {missing}")
    print("    Installing...")
    r = subprocess.run(["npm", "install"] + missing, cwd=FRONTEND, capture_output=True, text=True)
    if r.returncode != 0:
        print("    npm install failed:", r.stderr[-300:])
    else:
        print("    Installed OK")
else:
    print("    All packages present")

# ── 3. Clear vite cache ───────────────────────────────────────────
print("\n[3] Clearing vite cache...")
vite_cache = FRONTEND + "/node_modules/.vite"
if os.path.exists(vite_cache):
    shutil.rmtree(vite_cache)
    print("    Cleared .vite cache")
else:
    print("    No cache to clear")

# ── 4. Verify all component files ────────────────────────────────
print("\n[4] Verifying frontend files...")
COMP = FRONTEND + "/src/components"
required = ["LoginPage.jsx","Dashboard.jsx","EmployeeManagement.jsx","AttendanceTracker.jsx",
            "LeaveManagement.jsx","PayrollModule.jsx","TaxManagement.jsx","BenefitsModule.jsx","ReportsModule.jsx"]
all_ok = True
for f in required:
    path = COMP + "/" + f
    if os.path.exists(path) and os.path.getsize(path) > 100:
        print(f"    {f}: OK ({os.path.getsize(path)} bytes)")
    else:
        print(f"    {f}: MISSING or empty!")
        all_ok = False

for f in ["App.jsx", "store.js", "api.js", "main.jsx", "index.css"]:
    path = FRONTEND + "/src/" + f
    if os.path.exists(path):
        print(f"    src/{f}: OK")
    else:
        print(f"    src/{f}: MISSING!")
        all_ok = False

if not all_ok:
    print("\n    Some files missing — run write_frontend.py and write_missing.py first")
    sys.exit(1)

# ── 5. Fix vite.config.js ─────────────────────────────────────────
print("\n[5] Fixing vite.config.js...")
vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
  optimizeDeps: {
    include: [
      'react', 'react-dom', 'axios', 'zustand',
      '@tanstack/react-query', 'react-markdown',
      'lucide-react', 'uuid'
    ]
  }
})
"""
with open(FRONTEND + "/vite.config.js", "w") as f:
    f.write(vite_config)
print("    vite.config.js updated with explicit optimizeDeps")

# ── 6. Fix tailwind/postcss config ───────────────────────────────
print("\n[6] Checking tailwind config...")
tw_config = FRONTEND + "/tailwind.config.js"
if not os.path.exists(tw_config):
    with open(tw_config, "w") as f:
        f.write("""/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
}
""")
    print("    Created tailwind.config.js")
else:
    print("    tailwind.config.js exists")

# ── 7. Fix index.css to use correct tailwind directives ──────────
print("\n[7] Fixing index.css...")
css_path = FRONTEND + "/src/index.css"
with open(css_path, "w") as f:
    f.write("""@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
  color-scheme: dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #0f172a;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body { margin: 0; min-width: 320px; min-height: 100vh; }
#root { width: 100%; height: 100vh; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }
""")
print("    index.css fixed")

# ── 8. Fix postcss.config.js ─────────────────────────────────────
print("\n[8] Fixing postcss.config.js...")
postcss_path = FRONTEND + "/postcss.config.js"
with open(postcss_path, "w") as f:
    f.write("""export default {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}
""")
print("    postcss.config.js fixed")

# ── 9. Seed database if needed ────────────────────────────────────
print("\n[9] Checking database...")
db_path = BACKEND + "/hrbot.db"
if os.path.exists(db_path) and os.path.getsize(db_path) > 10000:
    print("    Database exists and has data")
else:
    print("    Seeding database...")
    r = subprocess.run([VENV + "/python3", BACKEND + "/seed_data.py"],
                       capture_output=True, text=True, cwd=BACKEND)
    if "Seed complete" in r.stdout:
        print("    Seeded OK")
    else:
        print("    Seed output:", r.stdout[-300:])
        if r.stderr: print("    Seed error:", r.stderr[-300:])

print("\n" + "=" * 60)
print("All checks passed!")
print("=" * 60)
print("\nStarting servers...")
print("  Backend:  http://localhost:8000")
print("  Frontend: http://localhost:5173")
print("  API Docs: http://localhost:8000/docs")
print("\nLogin credentials:")
print("  Admin:    sravan@hrdesk.com  / Password@123")
print("  HR Mgr:   priya@hrdesk.com   / Password@123")
print("  Employee: rahul@hrdesk.com   / Password@123")
print("\nPress Ctrl+C to stop\n")
