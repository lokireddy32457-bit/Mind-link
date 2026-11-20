"""
Mind Link — Google Places Reviews Cache
Fetches rating, review count, and up to 5 reviews from the Google Places API.
Caches results in PostgreSQL for CACHE_TTL_HOURS to avoid hitting the API on every request.

Env vars required:
  GOOGLE_PLACES_API_KEY — Google Cloud API key with Places API enabled
  GOOGLE_PLACE_ID       — The Place ID of the clinic (e.g. ChIJ...)
"""

import os, json, logging, requests
from datetime import datetime, timedelta, timezone

logger = logging.getLogger('mindlink.reviews')

GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')
GOOGLE_PLACE_ID = os.environ.get('GOOGLE_PLACE_ID', '')
CACHE_TTL_HOURS = 24
CACHE_DB_KEY = 'google_reviews_cache'

FALLBACK = {
    'rating': 4.9,
    'review_count': 574,
    'reviews': [],
    'cached_at': None,
    'source': 'fallback',
}

def _fetch_from_api() -> dict | None:
    """Call Google Places API (legacy Details endpoint) and return parsed data."""
    if not GOOGLE_PLACES_API_KEY or not GOOGLE_PLACE_ID:
        logger.warning('GOOGLE_PLACES_API_KEY or GOOGLE_PLACE_ID not set — skipping fetch.')
        return None
    url = 'https://maps.googleapis.com/maps/api/place/details/json'
    params = {
        'place_id': GOOGLE_PLACE_ID,
        'fields': 'rating,user_ratings_total,reviews',
        'key': GOOGLE_PLACES_API_KEY,
        'language': 'en',
        'reviews_sort': 'newest',
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') != 'OK':
            logger.error('Places API error: %s', data.get('status'))
            return None
        result = data['result']
        reviews = []
        for r in result.get('reviews', [])[:5]:
            reviews.append({
                'author': r.get('author_name', 'Anonymous'),
                'avatar_url': r.get('profile_photo_url', ''),
                'rating': r.get('rating', 5),
                'text': r.get('text', ''),
                'time_desc': r.get('relative_time_description', ''),
                'author_url': r.get('author_url', ''),
            })
        return {
            'rating': result.get('rating', FALLBACK['rating']),
            'review_count': result.get('user_ratings_total', FALLBACK['review_count']),
            'reviews': reviews,
            'cached_at': datetime.now(timezone.utc).isoformat(),
            'source': 'api',
        }
    except Exception as exc:
        logger.error('Places API fetch failed: %s', exc)
        return None

def _load_from_db() -> dict | None:
    """Load cached JSON from site_settings table."""
    try:
        from database import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT value, updated_at FROM site_settings WHERE key = %s", (CACHE_DB_KEY,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        cached_at = row[1]  # datetime
        # Check TTL
        if datetime.now(timezone.utc) - cached_at.replace(tzinfo=timezone.utc) > timedelta(hours=CACHE_TTL_HOURS):
            return None  # stale
        return json.loads(row[0])
    except Exception as exc:
        logger.error('DB cache load failed: %s', exc)
        return None

def _save_to_db(data: dict):
    """Persist JSON to site_settings table."""
    try:
        from database import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO site_settings (key, value, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
        """, (CACHE_DB_KEY, json.dumps(data)))
        conn.commit()
        conn.close()
        logger.info('Google reviews cached to DB (%d reviews)', len(data.get('reviews', [])))
    except Exception as exc:
        logger.error('DB cache save failed: %s', exc)

def get_google_reviews(force_refresh: bool = False) -> dict:
    """
    Public API. Returns dict with keys: rating, review_count, reviews, cached_at, source.
    Uses DB cache (24h TTL). Falls back to FALLBACK if API unavailable.
    """
    if not force_refresh:
        cached = _load_from_db()
        if cached:
            cached['source'] = 'cache'
            return cached

    fresh = _fetch_from_api()
    if fresh:
        _save_to_db(fresh)
        return fresh

    # Last resort: try stale cache regardless of TTL
    try:
        from database import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT value FROM site_settings WHERE key = %s", (CACHE_DB_KEY,))
        row = cur.fetchone()
        conn.close()
        if row:
            stale = json.loads(row[0])
            stale['source'] = 'stale_cache'
            return stale
    except Exception:
        pass

    return FALLBACK.copy()
