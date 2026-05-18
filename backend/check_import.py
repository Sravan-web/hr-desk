import sys
sys.path.insert(0, '/Users/sravankumar/Desktop/HR Desk/backend')

print("=== Import Test ===")
try:
    import database
    print("database: OK  tables:", list(database.Base.metadata.tables.keys()))
except Exception as e:
    print(f"database: FAIL - {e}")

try:
    import auth
    print("auth: OK")
except Exception as e:
    print(f"auth: FAIL - {e}")

try:
    import payroll_engine
    print("payroll_engine: OK")
except Exception as e:
    print(f"payroll_engine: FAIL - {e}")

try:
    import main
    print("main: OK")
    print("routes:", [r.path for r in main.app.routes[:8]])
except Exception as e:
    import traceback
    print(f"main: FAIL - {e}")
    traceback.print_exc()
