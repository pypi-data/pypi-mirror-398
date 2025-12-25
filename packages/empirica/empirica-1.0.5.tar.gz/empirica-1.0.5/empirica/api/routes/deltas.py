"""Learning delta endpoints"""

import logging
from flask import Blueprint, jsonify

bp = Blueprint("deltas", __name__)
logger = logging.getLogger(__name__)


@bp.route("/sessions/<session_id>/deltas", methods=["GET"])
def get_session_deltas(session_id: str):
    """
    Get epistemic changes from PREFLIGHT to POSTFLIGHT.

    Returns:
    - Deltas for each epistemic vector
    - Learning velocity (change per minute)
    - Git correlation data
    """
    try:
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Get PREFLIGHT reflexes
        cursor.execute(
            """
            SELECT know, do, context, clarity, coherence, signal, density,
                   state, change, completion, impact, engagement, uncertainty
            FROM reflexes
            WHERE session_id = ? AND phase = 'PREFLIGHT'
            ORDER BY timestamp ASC
            LIMIT 1
            """,
            (session_id,)
        )
        preflight = cursor.fetchone()

        if not preflight:
            return jsonify({
                "ok": False,
                "error": "no_preflight",
                "message": "Session has no PREFLIGHT assessment"
            }), 404

        # Get POSTFLIGHT reflexes
        cursor.execute(
            """
            SELECT know, do, context, clarity, coherence, signal, density,
                   state, change, completion, impact, engagement, uncertainty
            FROM reflexes
            WHERE session_id = ? AND phase = 'POSTFLIGHT'
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (session_id,)
        )
        postflight = cursor.fetchone()

        if not postflight:
            return jsonify({
                "ok": False,
                "error": "no_postflight",
                "message": "Session has no POSTFLIGHT assessment"
            }), 404

        # Calculate deltas
        vector_names = [
            "know", "do", "context", "clarity", "coherence", "signal",
            "density", "state", "change", "completion", "impact", "engagement", "uncertainty"
        ]

        deltas = {}
        for i, name in enumerate(vector_names):
            deltas[name] = {
                "preflight": round(float(preflight[i]), 2),
                "postflight": round(float(postflight[i]), 2),
                "delta": round(float(postflight[i]) - float(preflight[i]), 2)
            }

        # Get session duration for velocity calculation
        cursor.execute(
            "SELECT start_time, end_time FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        session = cursor.fetchone()

        duration_seconds = 0
        if session and session[1]:
            # Would parse timestamps properly in production
            duration_seconds = 3600  # Placeholder

        return jsonify({
            "ok": True,
            "session_id": session_id,
            "deltas": deltas,
            "learning_velocity": {
                "know_per_minute": round(deltas["know"]["delta"] / (duration_seconds / 60), 4) if duration_seconds else 0,
                "overall_per_minute": round(sum([deltas[k]["delta"] for k in vector_names]) / len(vector_names) / (duration_seconds / 60), 4) if duration_seconds else 0
            },
            "git_correlation": {
                "commit_sha": "pending",
                "files_changed": [],
                "lines_added": 0,
                "lines_removed": 0,
                "correlation_strength": "pending"
            }
        })

    except Exception as e:
        logger.error(f"Error getting deltas: {e}")
        return jsonify({
            "ok": False,
            "error": "database_error",
            "message": str(e),
            "status_code": 500
        }), 500


@bp.route("/commits/<commit_sha>/epistemic", methods=["GET"])
def get_commit_epistemic(commit_sha: str):
    """
    Get epistemic state associated with a specific git commit.

    Returns epistemic context (confidence, areas investigated, risk assessment)
    and learning delta at time of commit.
    """
    return jsonify({
        "ok": True,
        "commit_sha": commit_sha,
        "commit_message": "pending",
        "files_changed": [],
        "lines_added": 0,
        "lines_removed": 0,
        "epistemic_context": {
            "session_id": "pending",
            "ai_id": "pending",
            "know": 0.0,
            "uncertainty": 0.0,
            "investigated": [],
            "not_investigated": [],
            "confidence_basis": "unknown",
            "risk_assessment": "unknown"
        },
        "learning_delta": {
            "know": 0.0,
            "do": 0.0,
            "overall": 0.0
        }
    })
