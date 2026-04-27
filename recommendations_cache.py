#!/usr/bin/env python3
"""
Recommendations Cache & Rate Limiter
Prevents excessive API calls to Gemini
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class RecommendationsCache:
    """Caches recommendations and enforces rate limits"""

    def __init__(self, cache_dir: str = './audit_data'):
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / 'recommendations_cache.json'
        self.rate_limit_file = self.cache_dir / 'gemini_rate_limit.json'

        # Rate limits (conservative to stay within free tier)
        self.MAX_CALLS_PER_MINUTE = 10  # Free tier is 15, using 10 for safety
        self.MAX_CALLS_PER_DAY = 1000   # Free tier is 1500, using 1000 for safety
        self.CACHE_TTL_HOURS = 1        # Cache recommendations for 1 hour

    def get_cached_recommendations(self, workspace_slug: str, use_ai: bool = False) -> Optional[Dict[str, Any]]:
        """Get cached recommendations if they exist and aren't stale"""
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)

            # Check if we have a cache for this workspace
            cache_key = f"{workspace_slug}_{'ai' if use_ai else 'basic'}"
            if cache_key not in cache:
                return None

            cached_data = cache[cache_key]
            cached_time = datetime.fromisoformat(cached_data['cached_at'])

            # Check if cache is still fresh
            if datetime.now() - cached_time < timedelta(hours=self.CACHE_TTL_HOURS):
                print(f"✅ Using cached recommendations (age: {(datetime.now() - cached_time).total_seconds() / 60:.1f} minutes)")
                return cached_data['data']
            else:
                print(f"⚠️  Cache expired (age: {(datetime.now() - cached_time).total_seconds() / 3600:.1f} hours)")
                return None

        except Exception as e:
            print(f"Cache read error: {e}")
            return None

    def cache_recommendations(self, workspace_slug: str, data: Dict[str, Any], use_ai: bool = False):
        """Save recommendations to cache"""
        try:
            # Load existing cache
            cache = {}
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)

            # Add new entry
            cache_key = f"{workspace_slug}_{'ai' if use_ai else 'basic'}"
            cache[cache_key] = {
                'cached_at': datetime.now().isoformat(),
                'data': data
            }

            # Write back to file
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)

            print(f"💾 Cached recommendations for {workspace_slug}")

        except Exception as e:
            print(f"Cache write error: {e}")

    def check_rate_limit(self) -> tuple[bool, str]:
        """
        Check if we're within rate limits for Gemini API
        Returns: (allowed, reason)
        """
        try:
            # Load rate limit tracker
            if self.rate_limit_file.exists():
                with open(self.rate_limit_file, 'r') as f:
                    rate_data = json.load(f)
            else:
                rate_data = {
                    'calls_this_minute': [],
                    'calls_today': [],
                    'last_reset': datetime.now().isoformat()
                }

            now = datetime.now()

            # Clean up old entries (older than 1 minute)
            one_minute_ago = now - timedelta(minutes=1)
            rate_data['calls_this_minute'] = [
                ts for ts in rate_data['calls_this_minute']
                if datetime.fromisoformat(ts) > one_minute_ago
            ]

            # Clean up old daily entries (older than 24 hours)
            one_day_ago = now - timedelta(days=1)
            rate_data['calls_today'] = [
                ts for ts in rate_data['calls_today']
                if datetime.fromisoformat(ts) > one_day_ago
            ]

            # Check per-minute limit
            if len(rate_data['calls_this_minute']) >= self.MAX_CALLS_PER_MINUTE:
                return False, f"Rate limit: {self.MAX_CALLS_PER_MINUTE} calls per minute exceeded. Wait 60 seconds."

            # Check daily limit
            if len(rate_data['calls_today']) >= self.MAX_CALLS_PER_DAY:
                return False, f"Rate limit: {self.MAX_CALLS_PER_DAY} calls per day exceeded. Try again tomorrow."

            return True, "OK"

        except Exception as e:
            print(f"Rate limit check error: {e}")
            return True, "OK"  # Allow on error (fail open)

    def record_api_call(self):
        """Record that we made an API call"""
        try:
            # Load existing data
            if self.rate_limit_file.exists():
                with open(self.rate_limit_file, 'r') as f:
                    rate_data = json.load(f)
            else:
                rate_data = {
                    'calls_this_minute': [],
                    'calls_today': [],
                    'last_reset': datetime.now().isoformat()
                }

            # Record this call
            now = datetime.now().isoformat()
            rate_data['calls_this_minute'].append(now)
            rate_data['calls_today'].append(now)

            # Write back
            with open(self.rate_limit_file, 'w') as f:
                json.dump(rate_data, f, indent=2)

            # Log stats
            print(f"📊 API calls: {len(rate_data['calls_this_minute'])} this minute, {len(rate_data['calls_today'])} today")

        except Exception as e:
            print(f"API call recording error: {e}")

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status for display"""
        try:
            if not self.rate_limit_file.exists():
                return {
                    'calls_this_minute': 0,
                    'calls_today': 0,
                    'remaining_minute': self.MAX_CALLS_PER_MINUTE,
                    'remaining_day': self.MAX_CALLS_PER_DAY
                }

            with open(self.rate_limit_file, 'r') as f:
                rate_data = json.load(f)

            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)
            one_day_ago = now - timedelta(days=1)

            # Count recent calls
            calls_minute = len([
                ts for ts in rate_data.get('calls_this_minute', [])
                if datetime.fromisoformat(ts) > one_minute_ago
            ])

            calls_day = len([
                ts for ts in rate_data.get('calls_today', [])
                if datetime.fromisoformat(ts) > one_day_ago
            ])

            return {
                'calls_this_minute': calls_minute,
                'calls_today': calls_day,
                'remaining_minute': max(0, self.MAX_CALLS_PER_MINUTE - calls_minute),
                'remaining_day': max(0, self.MAX_CALLS_PER_DAY - calls_day)
            }

        except Exception as e:
            print(f"Rate limit status error: {e}")
            return {
                'calls_this_minute': 0,
                'calls_today': 0,
                'remaining_minute': self.MAX_CALLS_PER_MINUTE,
                'remaining_day': self.MAX_CALLS_PER_DAY
            }

    def clear_cache(self):
        """Clear all cached recommendations"""
        if self.cache_file.exists():
            self.cache_file.unlink()
            print("🗑️  Cache cleared")

    def reset_rate_limits(self):
        """Reset rate limit tracking (use with caution!)"""
        if self.rate_limit_file.exists():
            self.rate_limit_file.unlink()
            print("🔄 Rate limits reset")


if __name__ == '__main__':
    # Test the cache
    cache = RecommendationsCache()

    # Test rate limit
    allowed, reason = cache.check_rate_limit()
    print(f"Rate limit check: {allowed} - {reason}")

    # Test status
    status = cache.get_rate_limit_status()
    print(f"Status: {json.dumps(status, indent=2)}")
