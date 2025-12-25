#!/usr/bin/env python3
"""
Task Repository - Database operations for SubTask persistence

Provides CRUD operations for tasks and decompositions.
MVP implementation: Simple database operations for task tracking.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from empirica.data.session_database import SessionDatabase
from .types import SubTask, TaskDecomposition, TaskStatus, EpistemicImportance

logger = logging.getLogger(__name__)


class TaskRepository:
    """Database operations for Task persistence"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize repository
        
        Args:
            db_path: Optional custom database path
        """
        self.db = SessionDatabase(db_path=db_path)
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create task-related tables if they don't exist"""
        try:
            # SubTasks table
            self.db.conn.execute("""
                CREATE TABLE IF NOT EXISTS subtasks (
                    id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    epistemic_importance TEXT NOT NULL,
                    estimated_tokens INTEGER,
                    actual_tokens INTEGER,
                    completion_evidence TEXT,
                    notes TEXT,
                    created_timestamp REAL NOT NULL,
                    completed_timestamp REAL,
                    subtask_data TEXT NOT NULL,
                    FOREIGN KEY (goal_id) REFERENCES goals(id)
                )
            """)
            
            # Task dependencies table
            self.db.conn.execute("""
                CREATE TABLE IF NOT EXISTS subtask_dependencies (
                    subtask_id TEXT NOT NULL,
                    depends_on_subtask_id TEXT NOT NULL,
                    PRIMARY KEY (subtask_id, depends_on_subtask_id),
                    FOREIGN KEY (subtask_id) REFERENCES subtasks(id),
                    FOREIGN KEY (depends_on_subtask_id) REFERENCES subtasks(id)
                )
            """)
            
            # Task decompositions (metadata)
            self.db.conn.execute("""
                CREATE TABLE IF NOT EXISTS task_decompositions (
                    goal_id TEXT PRIMARY KEY,
                    total_estimated_tokens INTEGER,
                    created_timestamp REAL NOT NULL,
                    decomposition_data TEXT NOT NULL,
                    FOREIGN KEY (goal_id) REFERENCES goals(id)
                )
            """)
            
            self.db.conn.commit()
            logger.info("Task tables ensured in database")
            
        except Exception as e:
            logger.error(f"Error creating task tables: {e}")
            raise
    
    def save_subtask(self, subtask: SubTask) -> bool:
        """
        Save subtask to database
        
        Args:
            subtask: SubTask object to save
            
        Returns:
            True if successful
        """
        try:
            # Serialize full subtask as JSON
            subtask_data = json.dumps(subtask.to_dict())
            
            # Insert main subtask record
            self.db.conn.execute("""
                INSERT OR REPLACE INTO subtasks 
                (id, goal_id, description, status, epistemic_importance,
                 estimated_tokens, actual_tokens, completion_evidence, notes,
                 created_timestamp, completed_timestamp, subtask_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                subtask.id,
                subtask.goal_id,
                subtask.description,
                subtask.status.value,
                subtask.epistemic_importance.value,
                subtask.estimated_tokens,
                subtask.actual_tokens,
                subtask.completion_evidence,
                subtask.notes,
                subtask.created_timestamp,
                subtask.completed_timestamp,
                subtask_data
            ))
            
            # Insert dependencies (delete old ones first)
            self.db.conn.execute(
                "DELETE FROM subtask_dependencies WHERE subtask_id = ?",
                (subtask.id,)
            )
            for dep_id in subtask.dependencies:
                self.db.conn.execute("""
                    INSERT INTO subtask_dependencies
                    (subtask_id, depends_on_subtask_id)
                    VALUES (?, ?)
                """, (subtask.id, dep_id))
            
            self.db.conn.commit()
            logger.info(f"Saved subtask {subtask.id}: {subtask.description[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error saving subtask {subtask.id}: {e}")
            self.db.conn.rollback()
            return False
    
    def get_subtask(self, subtask_id: str) -> Optional[SubTask]:
        """
        Retrieve subtask by ID
        
        Args:
            subtask_id: SubTask identifier
            
        Returns:
            SubTask object or None if not found
        """
        try:
            cursor = self.db.conn.execute(
                "SELECT subtask_data FROM subtasks WHERE id = ?",
                (subtask_id,)
            )
            row = cursor.fetchone()
            
            if row:
                subtask_dict = json.loads(row[0])
                return SubTask.from_dict(subtask_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving subtask {subtask_id}: {e}")
            return None
    
    def get_goal_subtasks(self, goal_id: str) -> List[SubTask]:
        """
        Retrieve all subtasks for a goal
        
        Args:
            goal_id: Goal identifier
            
        Returns:
            List of SubTask objects
        """
        try:
            cursor = self.db.conn.execute(
                "SELECT subtask_data FROM subtasks WHERE goal_id = ? ORDER BY created_timestamp",
                (goal_id,)
            )
            
            subtasks = []
            for row in cursor.fetchall():
                subtask_dict = json.loads(row[0])
                subtasks.append(SubTask.from_dict(subtask_dict))
            
            return subtasks
            
        except Exception as e:
            logger.error(f"Error retrieving goal subtasks: {e}")
            return []
    
    def update_subtask_status(
        self,
        subtask_id: str,
        status: TaskStatus,
        completion_evidence: Optional[str] = None
    ) -> bool:
        """
        Update subtask status
        
        Args:
            subtask_id: SubTask identifier
            status: New status
            completion_evidence: Optional evidence (commit hash, etc.)
            
        Returns:
            True if successful
        """
        try:
            import time
            timestamp = time.time() if status == TaskStatus.COMPLETED else None
            
            self.db.conn.execute("""
                UPDATE subtasks 
                SET status = ?, completed_timestamp = ?, completion_evidence = ?
                WHERE id = ?
            """, (status.value, timestamp, completion_evidence, subtask_id))
            
            # Also update the subtask_data JSON
            subtask = self.get_subtask(subtask_id)
            if subtask:
                subtask.status = status
                subtask.completed_timestamp = timestamp
                if completion_evidence:
                    subtask.completion_evidence = completion_evidence
                subtask_data = json.dumps(subtask.to_dict())
                
                self.db.conn.execute(
                    "UPDATE subtasks SET subtask_data = ? WHERE id = ?",
                    (subtask_data, subtask_id)
                )
            
            self.db.conn.commit()
            logger.info(f"Updated subtask {subtask_id} status: {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating subtask status: {e}")
            self.db.conn.rollback()
            return False
    
    def save_decomposition(self, decomposition: TaskDecomposition) -> bool:
        """
        Save task decomposition metadata
        
        Args:
            decomposition: TaskDecomposition object
            
        Returns:
            True if successful
        """
        try:
            # Save all subtasks first
            for subtask in decomposition.subtasks:
                self.save_subtask(subtask)
            
            # Save decomposition metadata
            decomposition_data = json.dumps(decomposition.to_dict())
            
            self.db.conn.execute("""
                INSERT OR REPLACE INTO task_decompositions
                (goal_id, total_estimated_tokens, created_timestamp, decomposition_data)
                VALUES (?, ?, ?, ?)
            """, (
                decomposition.goal_id,
                decomposition.total_estimated_tokens,
                decomposition.created_timestamp,
                decomposition_data
            ))
            
            self.db.conn.commit()
            logger.info(f"Saved decomposition for goal {decomposition.goal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving decomposition: {e}")
            self.db.conn.rollback()
            return False
    
    def get_decomposition(self, goal_id: str) -> Optional[TaskDecomposition]:
        """
        Retrieve task decomposition for a goal
        
        Args:
            goal_id: Goal identifier
            
        Returns:
            TaskDecomposition object or None if not found
        """
        try:
            cursor = self.db.conn.execute(
                "SELECT decomposition_data FROM task_decompositions WHERE goal_id = ?",
                (goal_id,)
            )
            row = cursor.fetchone()
            
            if row:
                decomposition_dict = json.loads(row[0])
                return TaskDecomposition.from_dict(decomposition_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving decomposition: {e}")
            return None
    
    def query_subtasks(
        self,
        goal_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        epistemic_importance: Optional[EpistemicImportance] = None
    ) -> List[SubTask]:
        """
        Query subtasks with filters
        
        Args:
            goal_id: Filter by goal
            status: Filter by status
            epistemic_importance: Filter by importance
            
        Returns:
            List of matching SubTask objects
        """
        try:
            query = "SELECT subtask_data FROM subtasks WHERE 1=1"
            params = []
            
            if goal_id:
                query += " AND goal_id = ?"
                params.append(goal_id)
            
            if status:
                query += " AND status = ?"
                params.append(status.value)
            
            if epistemic_importance:
                query += " AND epistemic_importance = ?"
                params.append(epistemic_importance.value)
            
            query += " ORDER BY created_timestamp"
            
            cursor = self.db.conn.execute(query, params)
            
            subtasks = []
            for row in cursor.fetchall():
                subtask_dict = json.loads(row[0])
                subtasks.append(SubTask.from_dict(subtask_dict))
            
            return subtasks
            
        except Exception as e:
            logger.error(f"Error querying subtasks: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        self.db.close()
