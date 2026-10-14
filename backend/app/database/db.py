"""Database abstraction layer using SQLite for logs, diagnostics, and analytics."""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.app.core.config import BASE_DIR, settings
from backend.app.core.logging import logger

DB_FILE = BASE_DIR / "kisan_shakti.db"

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Disease predictions history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS disease_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crop_name TEXT NOT NULL,
        disease_name TEXT NOT NULL,
        confidence REAL NOT NULL,
        is_healthy BOOLEAN NOT NULL,
        alternatives_json TEXT,
        image_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # User queries log (categorized by module)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS query_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_text TEXT NOT NULL,
        module_routed TEXT NOT NULL,
        language TEXT DEFAULT 'en',
        confidence REAL,
        response_preview TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Feedback or flagged items
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_id INTEGER,
        rating INTEGER,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully at %s", DB_FILE)

def log_disease_prediction(crop_name: str, disease_name: str, confidence: float, is_healthy: bool, alternatives: List[Dict[str, Any]], image_name: str = "") -> int:
    """Logs a disease prediction for analytics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO disease_predictions (crop_name, disease_name, confidence, is_healthy, alternatives_json, image_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (crop_name, disease_name, confidence, is_healthy, json.dumps(alternatives), image_name))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id
    except Exception as e:
        logger.error(f"Failed to log disease prediction: {e}")
        return -1

def log_query(query_text: str, module_routed: str, language: str = "en", confidence: float = 1.0, response_preview: str = "") -> int:
    """Logs a general query for system observability and analytics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO query_logs (query_text, module_routed, language, confidence, response_preview)
            VALUES (?, ?, ?, ?, ?)
        """, (query_text[:500], module_routed, language, confidence, response_preview[:500]))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id
    except Exception as e:
        logger.error(f"Failed to log query: {e}")
        return -1

def get_analytics_summary() -> Dict[str, Any]:
    """Retrieves aggregated statistics for the analytics dashboard."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Count total predictions
        cursor.execute("SELECT COUNT(*) as total FROM disease_predictions")
        total_predictions = cursor.fetchone()["total"]

        # Predictions by crop
        cursor.execute("SELECT crop_name, COUNT(*) as count FROM disease_predictions GROUP BY crop_name")
        by_crop = {row["crop_name"]: row["count"] for row in cursor.fetchall()}

        # Predictions by disease
        cursor.execute("SELECT disease_name, COUNT(*) as count FROM disease_predictions GROUP BY disease_name ORDER BY count DESC LIMIT 10")
        by_disease = {row["disease_name"]: row["count"] for row in cursor.fetchall()}

        # Module usage count
        cursor.execute("SELECT module_routed, COUNT(*) as count FROM query_logs GROUP BY module_routed")
        by_module = {row["module_routed"]: row["count"] for row in cursor.fetchall()}

        # Language distribution
        cursor.execute("SELECT language, COUNT(*) as count FROM query_logs GROUP BY language")
        by_lang = {row["language"]: row["count"] for row in cursor.fetchall()}

        conn.close()
        return {
            "total_predictions": total_predictions,
            "by_crop": by_crop,
            "by_disease": by_disease,
            "by_module": by_module,
            "by_language": by_lang
        }
    except Exception as e:
        logger.error(f"Failed to fetch analytics summary: {e}")
        return {
            "total_predictions": 0,
            "by_crop": {},
            "by_disease": {},
            "by_module": {},
            "by_language": {}
        }
