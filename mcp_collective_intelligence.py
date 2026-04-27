#!/usr/bin/env python3
"""
MCP Collective Intelligence - Shared learning system for CDP best practices

Uses Model Context Protocol to:
1. Store anonymized workspace analysis results
2. Query similar company patterns for benchmarking
3. Surface collective best practices by industry
4. Learn from actual implementation outcomes

Privacy-first: Only aggregated patterns, no customer PII
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict
import hashlib


class CollectiveLearningDB:
    """
    SQLite-based collective learning database
    Stores anonymized workspace patterns and outcomes
    """

    def __init__(self, db_path: str = './audit_data/collective_learning.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Workspace patterns table (anonymized)
        cursor.execute("""
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
                destinations_connected TEXT,  -- JSON array
                destination_categories TEXT,  -- JSON object
                audience_categories TEXT,     -- JSON object
                finding_types TEXT,           -- JSON array
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Best practices table (emerged from multiple analyses)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS best_practices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                industry TEXT NOT NULL,
                business_model TEXT,
                practice_category TEXT,  -- activation, hygiene, optimization
                practice_title TEXT,
                practice_description TEXT,
                evidence_count INTEGER DEFAULT 1,  -- How many workspaces validate this
                avg_impact TEXT,  -- Observed impact when implemented
                confidence_score REAL,  -- Statistical confidence
                example_pattern TEXT,  -- Anonymized example
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Implementation outcomes table (what actually worked)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS implementation_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_hash TEXT NOT NULL,
                recommendation_type TEXT,
                implementation_date TEXT,
                outcome TEXT,  -- success, partial, failed
                impact_metrics TEXT,  -- JSON: {metric: value}
                lessons_learned TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Industry benchmarks table (aggregated stats)
        cursor.execute("""
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

        conn.commit()
        conn.close()

    def store_workspace_pattern(self, analysis_result: Dict[str, Any], workspace_slug: str = ""):
        """
        Store anonymized workspace pattern
        workspace_slug is hashed for privacy
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Hash workspace slug for privacy
        workspace_hash = hashlib.sha256(workspace_slug.encode()).hexdigest()[:16]

        # Extract key patterns
        layer0 = analysis_result.get('layer0_business_inference', {})
        structured = analysis_result.get('structured_data', {})
        workspace_summary = structured.get('workspace_summary', {})
        destinations = structured.get('destination_summary', {})

        cursor.execute("""
            INSERT INTO workspace_patterns (
                workspace_hash, analysis_date, industry, business_model, confidence,
                total_sources, total_audiences, enabled_audiences, total_users,
                destinations_connected, destination_categories, audience_categories, finding_types
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workspace_hash,
            datetime.now().isoformat(),
            layer0.get('industry', {}).get('primary', 'Unknown'),
            layer0.get('business_model', {}).get('primary', 'Unknown'),
            layer0.get('overall_assessment', {}).get('confidence', 'low'),
            workspace_summary.get('total_sources', 0),
            workspace_summary.get('total_audiences', 0),
            workspace_summary.get('enabled_audiences', 0),
            workspace_summary.get('total_users_in_audiences', 0),
            json.dumps(destinations.get('all_destinations', [])),
            json.dumps(destinations.get('by_category', {})),
            json.dumps(self._extract_audience_categories(structured)),
            json.dumps(self._extract_finding_types(analysis_result))
        ))

        conn.commit()
        conn.close()

    def query_similar_workspaces(self, industry: str, business_model: str = None, limit: int = 10) -> List[Dict]:
        """
        Find similar workspaces for benchmarking
        Returns anonymized patterns
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if business_model:
            cursor.execute("""
                SELECT industry, business_model, confidence,
                       total_sources, total_audiences, enabled_audiences, total_users,
                       destinations_connected, destination_categories, audience_categories
                FROM workspace_patterns
                WHERE industry = ? AND business_model = ?
                ORDER BY analysis_date DESC
                LIMIT ?
            """, (industry, business_model, limit))
        else:
            cursor.execute("""
                SELECT industry, business_model, confidence,
                       total_sources, total_audiences, enabled_audiences, total_users,
                       destinations_connected, destination_categories, audience_categories
                FROM workspace_patterns
                WHERE industry = ?
                ORDER BY analysis_date DESC
                LIMIT ?
            """, (industry, limit))

        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        conn.close()
        return results

    def get_industry_benchmarks(self, industry: str) -> Dict[str, Any]:
        """
        Get aggregated benchmarks for an industry
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate benchmarks on-the-fly from workspace_patterns
        cursor.execute("""
            SELECT
                COUNT(*) as sample_size,
                AVG(total_audiences) as avg_audiences,
                AVG(enabled_audiences) as avg_enabled_audiences,
                AVG(total_users) as avg_users,
                AVG(CAST(enabled_audiences AS FLOAT) / NULLIF(total_audiences, 0)) as avg_activation_rate
            FROM workspace_patterns
            WHERE industry = ?
        """, (industry,))

        row = cursor.fetchone()
        if row and row[0] > 0:  # Has data
            benchmarks = {
                'industry': industry,
                'sample_size': row[0],
                'avg_total_audiences': round(row[1]) if row[1] else 0,
                'avg_enabled_audiences': round(row[2]) if row[2] else 0,
                'avg_total_users': round(row[3]) if row[3] else 0,
                'avg_activation_rate': round(row[4] * 100, 1) if row[4] else 0
            }
        else:
            benchmarks = {'industry': industry, 'sample_size': 0, 'message': 'Insufficient data for benchmarking'}

        conn.close()
        return benchmarks

    def get_best_practices(self, industry: str, category: str = None) -> List[Dict]:
        """
        Retrieve emerged best practices for an industry
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if category:
            cursor.execute("""
                SELECT practice_category, practice_title, practice_description,
                       evidence_count, avg_impact, confidence_score, example_pattern
                FROM best_practices
                WHERE industry = ? AND practice_category = ?
                ORDER BY confidence_score DESC, evidence_count DESC
            """, (industry, category))
        else:
            cursor.execute("""
                SELECT practice_category, practice_title, practice_description,
                       evidence_count, avg_impact, confidence_score, example_pattern
                FROM best_practices
                WHERE industry = ?
                ORDER BY confidence_score DESC, evidence_count DESC
            """, (industry,))

        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        conn.close()
        return results

    def add_best_practice(self, industry: str, business_model: str, practice: Dict[str, Any]):
        """
        Add or update a best practice
        Called when pattern emerges from multiple analyses
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO best_practices (
                industry, business_model, practice_category, practice_title,
                practice_description, evidence_count, avg_impact, confidence_score, example_pattern
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            industry,
            business_model,
            practice.get('category'),
            practice.get('title'),
            practice.get('description'),
            practice.get('evidence_count', 1),
            practice.get('avg_impact'),
            practice.get('confidence_score', 0.5),
            practice.get('example_pattern')
        ))

        conn.commit()
        conn.close()

    def _extract_audience_categories(self, structured_data: Dict) -> Dict:
        """Extract audience category distribution"""
        audiences = structured_data.get('audience_insights', [])
        categories = defaultdict(int)
        for aud in audiences:
            cat = aud.get('category', 'general')
            categories[cat] += 1
        return dict(categories)

    def _extract_finding_types(self, analysis_result: Dict) -> List[str]:
        """Extract finding types from analysis"""
        findings = analysis_result.get('structured_data', {}).get('findings_summary', {})
        return findings.get('finding_types', [])


class MCPCollectiveIntelligence:
    """
    MCP-compatible interface for collective learning
    Provides context queries during analysis
    """

    def __init__(self, db_path: str = './audit_data/collective_learning.db'):
        self.db = CollectiveLearningDB(db_path)

    def get_contextual_insights(self, layer0_inference: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get collective insights based on inferred business context
        This is called during Layer 1-4 to enrich prompts
        """
        industry = layer0_inference.get('industry', {}).get('primary', 'Unknown')
        business_model = layer0_inference.get('business_model', {}).get('primary')

        # Query similar workspaces
        similar = self.db.query_similar_workspaces(industry, business_model, limit=10)

        # Get industry benchmarks
        benchmarks = self.db.get_industry_benchmarks(industry)

        # Get emerged best practices
        best_practices = self.db.get_best_practices(industry)

        return {
            'industry': industry,
            'business_model': business_model,
            'similar_workspaces_analyzed': len(similar),
            'benchmarks': benchmarks,
            'best_practices': best_practices[:5],  # Top 5
            'collective_context': self._format_collective_context(similar, benchmarks, best_practices)
        }

    def _format_collective_context(self, similar: List[Dict], benchmarks: Dict, practices: List[Dict]) -> str:
        """
        Format collective intelligence as prompt context
        This gets injected into Layers 1-4
        """
        if not similar:
            return ""

        context = f"""
---

## Collective Intelligence (From {len(similar)} Similar Workspaces)

### Industry Benchmarks
Based on {benchmarks.get('sample_size', 0)} {benchmarks.get('industry')} workspaces analyzed:
- Average audiences: {benchmarks.get('avg_total_audiences', 'N/A')}
- Average enabled: {benchmarks.get('avg_enabled_audiences', 'N/A')}
- Average activation rate: {benchmarks.get('avg_activation_rate', 'N/A')}%

### Common Patterns for {benchmarks.get('industry')} Companies
"""

        # Add destination patterns
        if similar:
            dest_counts = defaultdict(int)
            for ws in similar:
                dests = json.loads(ws.get('destinations_connected', '[]'))
                for d in dests:
                    dest_counts[d] += 1

            if dest_counts:
                top_dests = sorted(dest_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                context += "\nMost common destinations:\n"
                for dest, count in top_dests:
                    pct = (count / len(similar)) * 100
                    context += f"- {dest} ({pct:.0f}% of similar workspaces)\n"

        # Add best practices
        if practices:
            context += "\n### Emerged Best Practices\n"
            for practice in practices[:3]:
                context += f"\n**{practice['practice_title']}**\n"
                context += f"- {practice['practice_description']}\n"
                context += f"- Evidence: {practice['evidence_count']} workspaces\n"
                if practice.get('avg_impact'):
                    context += f"- Average impact: {practice['avg_impact']}\n"

        context += """
---

Use these benchmarks and best practices to:
1. Compare this workspace to industry norms
2. Identify gaps vs. similar companies
3. Recommend proven patterns (not just theoretical)
4. Set realistic impact expectations based on actual outcomes
"""

        return context

    def contribute_analysis(self, analysis_result: Dict[str, Any], workspace_slug: str = ""):
        """
        Store this analysis to contribute to collective learning
        Called after analysis completes
        """
        try:
            self.db.store_workspace_pattern(analysis_result, workspace_slug)
            print(f"✓ Contributed workspace pattern to collective intelligence")
        except Exception as e:
            print(f"⚠️  Could not contribute to collective intelligence: {e}")

    def record_implementation_outcome(self, workspace_slug: str, recommendation_type: str,
                                     outcome: str, impact_metrics: Dict[str, Any],
                                     lessons_learned: str = ""):
        """
        Record what happened when a recommendation was implemented
        This helps refine best practices over time
        """
        conn = sqlite3.connect(self.db.path)
        cursor = conn.cursor()

        workspace_hash = hashlib.sha256(workspace_slug.encode()).hexdigest()[:16]

        cursor.execute("""
            INSERT INTO implementation_outcomes (
                workspace_hash, recommendation_type, implementation_date,
                outcome, impact_metrics, lessons_learned
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            workspace_hash,
            recommendation_type,
            datetime.now().isoformat(),
            outcome,
            json.dumps(impact_metrics),
            lessons_learned
        ))

        conn.commit()
        conn.close()


# CLI testing
if __name__ == '__main__':
    print("=== MCP COLLECTIVE INTELLIGENCE SYSTEM ===\n")

    # Initialize
    mcp = MCPCollectiveIntelligence()

    # Test: Seed with sample data
    print("Seeding database with sample patterns...\n")

    sample_inference = {
        'industry': {'primary': 'Media/Publishing'},
        'business_model': {'primary': 'Subscription'}
    }

    sample_analysis = {
        'layer0_business_inference': sample_inference,
        'structured_data': {
            'workspace_summary': {
                'total_sources': 16,
                'total_audiences': 239,
                'enabled_audiences': 166,
                'total_users_in_audiences': 62000000
            },
            'destination_summary': {
                'all_destinations': ['Braze', 'Iterable', 'Sailthru'],
                'by_category': {'email': ['Braze', 'Iterable']}
            },
            'audience_insights': [
                {'category': 'subscription', 'size': 100000},
                {'category': 'engagement', 'size': 50000}
            ],
            'findings_summary': {
                'finding_types': ['activation_gap', 'underutilized_source']
            }
        }
    }

    # Store pattern
    mcp.contribute_analysis(sample_analysis, 'test_workspace_1')

    # Query insights
    print("Querying collective insights...\n")
    insights = mcp.get_contextual_insights(sample_inference)

    print(f"Industry: {insights['industry']}")
    print(f"Similar workspaces: {insights['similar_workspaces_analyzed']}")
    print(f"\nBenchmarks: {json.dumps(insights['benchmarks'], indent=2)}")

    print("\n" + "="*70)
    print("COLLECTIVE CONTEXT FOR PROMPTS:")
    print("="*70)
    print(insights['collective_context'])
