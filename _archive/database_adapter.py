#!/usr/bin/env python3
"""
Database Adapter - Works with both SQLite (local) and PostgreSQL (production)
Automatically detects environment and uses appropriate database
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class DatabaseAdapter:
    """
    Unified database interface that works with:
    - SQLite (local development)
    - PostgreSQL (Render production)
    """

    def __init__(self, db_path: str = './audit_data/collective_learning.db'):
        self.db_type = 'sqlite'
        self.db_path = db_path

        # Check if DATABASE_URL is set (Render/production)
        database_url = os.environ.get('DATABASE_URL')

        if database_url:
            # Production: Use PostgreSQL
            print("🔗 Using PostgreSQL (production)")
            self.db_type = 'postgres'
            self._init_postgres(database_url)
        else:
            # Local: Use SQLite
            print("📁 Using SQLite (local development)")
            self.db_type = 'sqlite'
            self._init_sqlite(db_path)

    def _init_postgres(self, database_url: str):
        """Initialize PostgreSQL connection"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            self.conn = psycopg2.connect(database_url)
            self.cursor_factory = RealDictCursor
            print("✓ PostgreSQL connection established")
        except ImportError:
            print("⚠️  psycopg2 not installed - falling back to SQLite")
            print("   Run: pip install psycopg2-binary")
            self.db_type = 'sqlite'
            self._init_sqlite('./audit_data/collective_learning.db')
        except Exception as e:
            print(f"⚠️  PostgreSQL connection failed: {e}")
            print("   Falling back to SQLite")
            self.db_type = 'sqlite'
            self._init_sqlite('./audit_data/collective_learning.db')

    def _init_sqlite(self, db_path: str):
        """Initialize SQLite connection"""
        import sqlite3

        db_file = Path(db_path)
        db_file.parent.mkdir(exist_ok=True, parents=True)
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return dict-like rows

    def execute(self, query: str, params: Tuple = ()) -> Any:
        """Execute a query (handles both SQLite and PostgreSQL)"""
        # Convert SQLite ? placeholders to PostgreSQL %s placeholders
        if self.db_type == 'postgres':
            query = query.replace('?', '%s')

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def fetchall(self, query: str, params: Tuple = ()) -> List[Dict]:
        """Execute query and return all results as list of dicts"""
        cursor = self.execute(query, params)

        if self.db_type == 'postgres':
            # PostgreSQL with RealDictCursor returns dicts
            return [dict(row) for row in cursor.fetchall()]
        else:
            # SQLite with row_factory returns Row objects
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def fetchone(self, query: str, params: Tuple = ()) -> Optional[Dict]:
        """Execute query and return one result as dict"""
        cursor = self.execute(query, params)
        row = cursor.fetchone()

        if not row:
            return None

        if self.db_type == 'postgres':
            return dict(row)
        else:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))

    def create_tables(self):
        """Create database schema (works for both SQLite and PostgreSQL)"""
        # Workspace patterns table
        self.execute("""
            CREATE TABLE IF NOT EXISTS workspace_patterns (
                id SERIAL PRIMARY KEY,
                workspace_hash TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                industry TEXT,
                business_model TEXT,
                confidence TEXT,
                total_sources INTEGER,
                total_audiences INTEGER,
                enabled_audiences INTEGER,
                total_users BIGINT,
                destinations_connected TEXT,
                destination_categories TEXT,
                audience_categories TEXT,
                finding_types TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """ if self.db_type == 'postgres' else """
            CREATE TABLE IF NOT EXISTS workspace_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_hash TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                industry TEXT,
                business_model TEXT,
                confidence TEXT,
                total_sources INTEGER,
                total_audiences INTEGER,
                enabled_audiences INTEGER,
                total_users INTEGER,
                destinations_connected TEXT,
                destination_categories TEXT,
                audience_categories TEXT,
                finding_types TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Best practices table
        self.execute("""
            CREATE TABLE IF NOT EXISTS best_practices (
                id SERIAL PRIMARY KEY,
                industry TEXT NOT NULL,
                business_model TEXT,
                practice_category TEXT,
                practice_title TEXT,
                practice_description TEXT,
                evidence_count INTEGER DEFAULT 1,
                avg_impact TEXT,
                confidence_score REAL,
                example_pattern TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """ if self.db_type == 'postgres' else """
            CREATE TABLE IF NOT EXISTS best_practices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                industry TEXT NOT NULL,
                business_model TEXT,
                practice_category TEXT,
                practice_title TEXT,
                practice_description TEXT,
                evidence_count INTEGER DEFAULT 1,
                avg_impact TEXT,
                confidence_score REAL,
                example_pattern TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Implementation outcomes table
        self.execute("""
            CREATE TABLE IF NOT EXISTS implementation_outcomes (
                id SERIAL PRIMARY KEY,
                workspace_hash TEXT NOT NULL,
                recommendation_type TEXT,
                implementation_date TEXT,
                outcome TEXT,
                impact_metrics TEXT,
                lessons_learned TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """ if self.db_type == 'postgres' else """
            CREATE TABLE IF NOT EXISTS implementation_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_hash TEXT NOT NULL,
                recommendation_type TEXT,
                implementation_date TEXT,
                outcome TEXT,
                impact_metrics TEXT,
                lessons_learned TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Industry benchmarks table
        self.execute("""
            CREATE TABLE IF NOT EXISTS industry_benchmarks (
                id SERIAL PRIMARY KEY,
                industry TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                percentile_25 REAL,
                percentile_50 REAL,
                percentile_75 REAL,
                percentile_90 REAL,
                sample_size INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(industry, metric_name)
            )
        """ if self.db_type == 'postgres' else """
            CREATE TABLE IF NOT EXISTS industry_benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                industry TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                percentile_25 REAL,
                percentile_50 REAL,
                percentile_75 REAL,
                percentile_90 REAL,
                sample_size INTEGER,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(industry, metric_name)
            )
        """)

        print("✓ Database tables created/verified")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Testing
if __name__ == '__main__':
    print("=== DATABASE ADAPTER TEST ===\n")

    # Test initialization
    db = DatabaseAdapter()
    print(f"Database type: {db.db_type}")

    # Create tables
    db.create_tables()

    # Test insert
    db.execute("""
        INSERT INTO workspace_patterns (
            workspace_hash, analysis_date, industry, total_audiences
        ) VALUES (?, ?, ?, ?)
    """, ('test123', '2024-01-01', 'Media/Publishing', 100))

    # Test query
    results = db.fetchall("""
        SELECT * FROM workspace_patterns WHERE industry = ?
    """, ('Media/Publishing',))

    print(f"\nFound {len(results)} workspace patterns")
    if results:
        print(f"Sample: {results[0]}")

    db.close()
    print("\n✓ Database adapter test complete")
