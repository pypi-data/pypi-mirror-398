#!/usr/bin/env python3
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from paperlib_mcp.db import query_all

def run_diagnostics():
    print("--- 1. Top Duplicate Relations (Same Subj, Pred, Obj) ---")
    sql1 = """
    SELECT subj_entity_id, predicate, obj_entity_id, COUNT(*) AS n
    FROM relations
    GROUP BY subj_entity_id, predicate, obj_entity_id
    HAVING COUNT(*) > 1
    ORDER BY n DESC
    LIMIT 20;
    """
    rows1 = query_all(sql1)
    if not rows1:
        print("No duplicates found with count > 1.")
    for row in rows1:
        print(f"Subj: {row['subj_entity_id']}, Pred: {row['predicate']}, Obj: {row['obj_entity_id']}, Count: {row['n']}")

    print("\n--- 2. Relation Statistics ---")
    sql2 = "SELECT COUNT(*) as total FROM relations;"
    total = query_all(sql2)[0]['total']
    
    sql3 = """
    SELECT COUNT(DISTINCT (subj_entity_id, predicate, obj_entity_id)) as unique_keys 
    FROM relations;
    """
    unique = query_all(sql3)[0]['unique_keys']
    
    print(f"Total Relations: {total}")
    print(f"Unique Relation Keys: {unique}")
    if total > 0:
        print(f"Redundancy Ratio: {(total - unique) / total:.2%}")

if __name__ == "__main__":
    run_diagnostics()
