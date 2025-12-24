#!/usr/bin/env python3
"""A/B 测试框架 - 用于实验不同分组参数"""

import json
import sys
from datetime import datetime

# 确保可以导入项目模块
sys.path.insert(0, "src")

from paperlib_mcp.db import get_db, query_all, query_one


def collect_metrics() -> dict:
    """收集当前分组状态的指标"""
    basic = query_one("""
        SELECT 
            (SELECT COUNT(*) FROM claims) as total_claims,
            (SELECT COUNT(*) FROM claim_groups) as total_groups,
            (SELECT COUNT(*) FROM claim_group_members) as total_members
    """)
    
    stats = query_one("""
        SELECT 
            COUNT(DISTINCT m.claim_id)::float / NULLIF((SELECT COUNT(*) FROM claims), 0) as coverage,
            MAX(n) as max_group_size,
            AVG(n) as avg_group_size,
            percentile_cont(0.5) WITHIN GROUP (ORDER BY n) as p50_group_size,
            percentile_cont(0.9) WITHIN GROUP (ORDER BY n) as p90_group_size
        FROM claim_group_members m
        JOIN (SELECT group_id, COUNT(*) as n FROM claim_group_members GROUP BY group_id) t 
        ON t.group_id = m.group_id
    """)
    
    tax_hit = query_one("""
        SELECT 1 - COUNT(*)::float / NULLIF((SELECT COUNT(*) FROM claim_features), 0) as hit_rate
        FROM claim_features WHERE outcome_family = 'general'
    """)
    
    subgroups = query_one("SELECT COUNT(*) as n FROM claim_groups WHERE parent_group_id IS NOT NULL")
    
    return {
        "total_claims": basic["total_claims"],
        "groups_created": basic["total_groups"],
        "total_members": basic["total_members"],
        "coverage": float(stats["coverage"]) if stats["coverage"] else 0,
        "max_group_size": stats["max_group_size"],
        "avg_group_size": float(stats["avg_group_size"]) if stats["avg_group_size"] else 0,
        "p50_group_size": float(stats["p50_group_size"]) if stats["p50_group_size"] else 0,
        "p90_group_size": float(stats["p90_group_size"]) if stats["p90_group_size"] else 0,
        "taxonomy_hit_rate": float(tax_hit["hit_rate"]) if tax_hit["hit_rate"] else 0,
        "subgroups": subgroups["n"],
    }


def create_experiment(experiment_id: str, description: str, **params):
    """创建实验配置"""
    params_json = json.dumps(params, sort_keys=True)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO experiments (experiment_id, description, params_json)
                VALUES (%s, %s, %s::jsonb)
                ON CONFLICT (experiment_id) DO UPDATE SET 
                    description = EXCLUDED.description,
                    params_json = EXCLUDED.params_json
            """, (experiment_id, description, params_json))
    print(f"✓ Created experiment: {experiment_id}")
    return params


def run_experiment(experiment_id: str):
    """运行实验并记录指标"""
    exp = query_one("SELECT params_json FROM experiments WHERE experiment_id = %s", (experiment_id,))
    if not exp:
        print(f"✗ Experiment {experiment_id} not found")
        return None
    
    metrics = collect_metrics()
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO experiment_runs (experiment_id, metrics)
                VALUES (%s, %s::jsonb)
                RETURNING run_id
            """, (experiment_id, json.dumps(metrics)))
            run_id = cur.fetchone()["run_id"]
    
    print(f"✓ Run #{run_id} recorded for {experiment_id}")
    return {"run_id": run_id, "metrics": metrics}


def rate_run(run_id: int, rating: int, notes: str = None):
    """为运行评分"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE experiment_runs SET user_rating = %s, user_notes = %s
                WHERE run_id = %s
            """, (rating, notes, run_id))
    print(f"✓ Rated run #{run_id}: {rating}/5")


def compare_experiments(experiment_ids: list = None):
    """对比实验结果"""
    where = ""
    params = ()
    if experiment_ids:
        where = "WHERE e.experiment_id = ANY(%s)"
        params = (experiment_ids,)
    
    rows = query_all(f"""
        SELECT e.experiment_id, e.description, 
               r.run_id, r.metrics, r.user_rating, r.created_at
        FROM experiments e
        LEFT JOIN experiment_runs r ON r.experiment_id = e.experiment_id
        {where}
        ORDER BY e.experiment_id, r.created_at DESC
    """, params)
    
    print("\n" + "=" * 80)
    print("EXPERIMENT COMPARISON")
    print("=" * 80)
    
    current_exp = None
    for row in rows:
        if row["experiment_id"] != current_exp:
            current_exp = row["experiment_id"]
            print(f"\n📊 {row['experiment_id']}: {row['description']}")
        
        if row["run_id"]:
            m = row["metrics"]
            rating = f"⭐{row['user_rating']}" if row["user_rating"] else "unrated"
            print(f"   Run #{row['run_id']} ({rating})")
            print(f"      coverage: {m['coverage']:.2%}, groups: {m['groups_created']}, max: {m['max_group_size']}")
            print(f"      taxonomy: {m['taxonomy_hit_rate']:.2%}, subgroups: {m['subgroups']}")


def list_experiments():
    """列出所有实验"""
    rows = query_all("""
        SELECT e.experiment_id, e.description,
               e.params_json->>'split_threshold' as split_threshold,
               COUNT(r.run_id) as run_count,
               AVG(r.user_rating) as avg_rating
        FROM experiments e
        LEFT JOIN experiment_runs r ON r.experiment_id = e.experiment_id
        GROUP BY e.experiment_id, e.description, e.params_json
        ORDER BY e.created_at DESC
    """)
    
    print("\n" + "=" * 60)
    print("EXPERIMENTS")
    print("=" * 60)
    for r in rows:
        rating = f"⭐{r['avg_rating']:.1f}" if r["avg_rating"] else "—"
        print(f"  {r['experiment_id']}: {r['description']}")
        print(f"    threshold={r['split_threshold']}, runs={r['run_count']}, {rating}")


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="A/B Testing Framework")
    subparsers = parser.add_subparsers(dest="command")
    
    # create
    p_create = subparsers.add_parser("create", help="Create experiment")
    p_create.add_argument("id", help="Experiment ID")
    p_create.add_argument("description", help="Description")
    p_create.add_argument("--split", type=int, default=150, help="Split threshold")
    
    # run
    p_run = subparsers.add_parser("run", help="Run experiment")
    p_run.add_argument("id", help="Experiment ID")
    
    # rate
    p_rate = subparsers.add_parser("rate", help="Rate a run")
    p_rate.add_argument("run_id", type=int, help="Run ID")
    p_rate.add_argument("rating", type=int, choices=[1,2,3,4,5], help="Rating 1-5")
    p_rate.add_argument("--notes", help="Notes")
    
    # compare
    p_compare = subparsers.add_parser("compare", help="Compare experiments")
    p_compare.add_argument("ids", nargs="*", help="Experiment IDs to compare")
    
    # list
    subparsers.add_parser("list", help="List experiments")
    
    # metrics
    subparsers.add_parser("metrics", help="Show current metrics")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_experiment(args.id, args.description, split_threshold=args.split)
    elif args.command == "run":
        result = run_experiment(args.id)
        if result:
            print("\nMetrics:")
            for k, v in result["metrics"].items():
                print(f"  {k}: {v}")
    elif args.command == "rate":
        rate_run(args.run_id, args.rating, args.notes)
    elif args.command == "compare":
        compare_experiments(args.ids if args.ids else None)
    elif args.command == "list":
        list_experiments()
    elif args.command == "metrics":
        print("\nCurrent Metrics:")
        for k, v in collect_metrics().items():
            print(f"  {k}: {v}")
    else:
        parser.print_help()
