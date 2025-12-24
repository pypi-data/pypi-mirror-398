#!/usr/bin/env python3
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from paperlib_mcp.db import get_db

def apply_migration():
    # migration is in the root initdb folder, script is in paperlib_mcp/scripts
    migration_path = Path(__file__).parent.parent.parent / "initdb" / "004_m4_canonicalization.sql"
    print(f"Reading migration from {migration_path}")
    
    with open(migration_path, "r") as f:
        sql = f.read()
    
    print("Applying migration...")
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        print("Migration applied successfully.")
    except Exception as e:
        print(f"Error applying migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_migration()
