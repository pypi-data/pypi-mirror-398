"""
CLI command handlers for epistemic trajectory queries.
"""
import json
import sys
from typing import Optional

from empirica.data.session_database import SessionDatabase
from empirica.core.epistemic_trajectory import search_trajectories


def handle_epistemics_search_command(args):
    """
    Search epistemic learning trajectories across sessions.
    
    Usage:
        empirica epistemics-search --project-id <UUID> --query "OAuth2 learning" --output json
        empirica epistemics-search --project-id <UUID> --query "auth" --min-learning 0.2 --limit 10
    """
    try:
        project_id = args.project_id
        query = args.query or ""
        min_learning = getattr(args, 'min_learning', None)
        calibration = getattr(args, 'calibration', None)
        limit = getattr(args, 'limit', 5)
        output_format = getattr(args, 'output', 'json')
        
        if not project_id:
            print(json.dumps({
                "ok": False,
                "error": "project_id is required"
            }))
            sys.exit(1)
        
        # Search trajectories
        results = search_trajectories(
            project_id=project_id,
            query=query,
            min_learning_delta=min_learning,
            calibration_quality=calibration,
            limit=limit
        )
        
        if output_format == 'json':
            print(json.dumps({
                "ok": True,
                "results": results,
                "count": len(results),
                "query": query,
                "filters": {
                    "min_learning_delta": min_learning,
                    "calibration_quality": calibration
                }
            }, indent=2))
        else:
            # Human-readable format
            print(f"\n🧠 Epistemic Trajectory Search Results")
            print(f"{'=' * 70}")
            print(f"Query: {query}")
            if min_learning:
                print(f"Min learning delta: {min_learning}")
            if calibration:
                print(f"Calibration quality: {calibration}")
            print(f"\nFound {len(results)} trajectories:\n")
            
            for i, traj in enumerate(results, 1):
                score = traj.get('score', 0.0)
                session_id = traj.get('session_id', 'unknown')
                task = traj.get('task_description', 'No description')[:60]
                deltas = traj.get('deltas', {})
                know_delta = deltas.get('know', 0.0)
                uncertainty_delta = deltas.get('uncertainty', 0.0)
                calibration_acc = traj.get('calibration_accuracy', 'unknown')
                
                print(f"{i}. Session: {session_id[:8]}...")
                print(f"   Score: {score:.3f}")
                print(f"   Task: {task}")
                print(f"   Learning: know={know_delta:+.2f}, uncertainty={uncertainty_delta:+.2f}")
                print(f"   Calibration: {calibration_acc}")
                print()
        
    except Exception as e:
        print(json.dumps({
            "ok": False,
            "error": str(e)
        }))
        sys.exit(1)


def handle_epistemics_stats_command(args):
    """
    Show aggregate statistics for epistemic trajectories in a project.
    
    Usage:
        empirica epistemics-stats --project-id <UUID> --output json
    """
    try:
        project_id = args.project_id
        output_format = getattr(args, 'output', 'json')
        
        if not project_id:
            print(json.dumps({
                "ok": False,
                "error": "project_id is required"
            }))
            sys.exit(1)
        
        # Get all trajectories (no query, high limit)
        all_trajectories = search_trajectories(
            project_id=project_id,
            query="",
            limit=1000  # High limit to get all
        )
        
        if not all_trajectories:
            print(json.dumps({
                "ok": True,
                "message": "No trajectories found for this project",
                "stats": {}
            }))
            return
        
        # Compute statistics
        stats = {
            "total_sessions": len(all_trajectories),
            "avg_know_delta": sum(t.get('deltas', {}).get('know', 0.0) for t in all_trajectories) / len(all_trajectories),
            "avg_uncertainty_delta": sum(t.get('deltas', {}).get('uncertainty', 0.0) for t in all_trajectories) / len(all_trajectories),
            "high_learning_sessions": sum(1 for t in all_trajectories if t.get('deltas', {}).get('know', 0.0) >= 0.2),
            "calibration_breakdown": {
                "good": sum(1 for t in all_trajectories if t.get('calibration_accuracy') == 'good'),
                "fair": sum(1 for t in all_trajectories if t.get('calibration_accuracy') == 'fair'),
                "poor": sum(1 for t in all_trajectories if t.get('calibration_accuracy') == 'poor')
            },
            "investigation_rate": sum(1 for t in all_trajectories if t.get('investigation_phase', False)) / len(all_trajectories)
        }
        
        if output_format == 'json':
            print(json.dumps({
                "ok": True,
                "project_id": project_id,
                "stats": stats
            }, indent=2))
        else:
            # Human-readable format
            print(f"\n📊 Epistemic Trajectory Statistics")
            print(f"{'=' * 70}")
            print(f"Project: {project_id}")
            print(f"\nTotal Sessions: {stats['total_sessions']}")
            print(f"Average Learning:")
            print(f"  • Know delta: {stats['avg_know_delta']:+.2f}")
            print(f"  • Uncertainty delta: {stats['avg_uncertainty_delta']:+.2f}")
            print(f"\nHigh Learning Sessions (know Δ ≥0.2): {stats['high_learning_sessions']}")
            print(f"\nCalibration Breakdown:")
            print(f"  • Good: {stats['calibration_breakdown']['good']}")
            print(f"  • Fair: {stats['calibration_breakdown']['fair']}")
            print(f"  • Poor: {stats['calibration_breakdown']['poor']}")
            print(f"\nInvestigation Rate: {stats['investigation_rate']:.1%}")
            print()
        
    except Exception as e:
        print(json.dumps({
            "ok": False,
            "error": str(e)
        }))
        sys.exit(1)
