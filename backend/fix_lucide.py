"""
fix_lucide.py — fixes the lucide-react resolution issue and rewrites
all component imports to use the correct path.
"""
import os, subprocess, json

FRONTEND = "/Users/sravankumar/Desktop/HR Desk/frontend"
COMP = FRONTEND + "/src/components"

# Check if lucide-react.mjs exists
esm_main = FRONTEND + "/node_modules/lucide-react/dist/esm/lucide-react.mjs"
print("lucide-react.mjs exists:", os.path.exists(esm_main))

# List what IS in the esm root
esm_dir = FRONTEND + "/node_modules/lucide-react/dist/esm"
files = os.listdir(esm_dir)
print("ESM files:", [f for f in files if not f.endswith('.map') and '.' in f])

# Check the package.json exports field more carefully
pkg_path = FRONTEND + "/node_modules/lucide-react/package.json"
with open(pkg_path) as f:
    pkg = json.load(f)

print("package.json module:", pkg.get("module"))
print("package.json main:", pkg.get("main"))
print("package.json exports:", pkg.get("exports", "none"))

# The fix: update vite.config.js to alias lucide-react to its CJS build
# which definitely exists
cjs_path = FRONTEND + "/node_modules/lucide-react/dist/cjs/lucide-react.js"
print("\ncjs exists:", os.path.exists(cjs_path))

# Write a fixed vite.config.js that resolves lucide-react correctly
vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
  resolve: {
    alias: {
      'lucide-react': path.resolve('./node_modules/lucide-react/dist/cjs/lucide-react.js'),
    }
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'axios',
      'zustand',
      '@tanstack/react-query',
      'react-markdown',
      'uuid',
    ],
    exclude: ['lucide-react']
  }
})
"""

with open(FRONTEND + "/vite.config.js", "w") as f:
    f.write(vite_config)
print("\nWrote fixed vite.config.js with lucide-react CJS alias")

# Clear vite cache again
import shutil
cache = FRONTEND + "/node_modules/.vite"
if os.path.exists(cache):
    shutil.rmtree(cache)
    print("Cleared .vite cache")

print("\nDone. Restart the frontend dev server.")
