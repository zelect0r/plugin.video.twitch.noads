# -*- coding: utf-8 -*-
"""

    Copyright (C) 212-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
import re
import time
import threading
import hashlib
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, urljoin

try:
    from http.server import ThreadingHTTPServer as HTTPServer
except ImportError:
    from http.server import HTTPServer

try:
    from .common import log_utils
except (ImportError, ModuleNotFoundError):
    class _FakeLog:
        LOGDEBUG = 0
        LOGINFO = 1
        LOGWARNING = 2
        LOGERROR = 3

        def log(self, msg, level=0):
            pass

    log_utils = _FakeLog()

import requests


# ---------------------------------------------------------------------------
# Ad detection patterns
# ---------------------------------------------------------------------------
AD_URL_PATTERNS = [
    re.compile(r'/ad/', re.IGNORECASE),
    re.compile(r'amazon-adsystem', re.IGNORECASE),
    re.compile(r'advertisement', re.IGNORECASE),
    re.compile(r'/ads/', re.IGNORECASE),
    re.compile(r'advert', re.IGNORECASE),
    re.compile(r'commercial', re.IGNORECASE),
    re.compile(r'sponsor', re.IGNORECASE),
    re.compile(r'promo', re.IGNORECASE),
    re.compile(r'preroll', re.IGNORECASE),
    re.compile(r'midroll', re.IGNORECASE),
    re.compile(r'postroll', re.IGNORECASE),
    re.compile(r'overlay', re.IGNORECASE),
    re.compile(r'banner', re.IGNORECASE),
    re.compile(r'click', re.IGNORECASE),
    re.compile(r'tracking', re.IGNORECASE),
    re.compile(r'beacon', re.IGNORECASE),
    re.compile(r'analytics', re.IGNORECASE),
    re.compile(r'metrics', re.IGNORECASE),
    re.compile(r'doubleclick', re.IGNORECASE),
    re.compile(r'googlesyndication', re.IGNORECASE),
    re.compile(r'adservice', re.IGNORECASE),
    re.compile(r'adserver', re.IGNORECASE),
    re.compile(r'adtech', re.IGNORECASE),
    re.compile(r'advertising', re.IGNORECASE),
    re.compile(r'mobileads', re.IGNORECASE),
    re.compile(r'video-ads', re.IGNORECASE),
    re.compile(r'player-ads', re.IGNORECASE),
    re.compile(r'vast', re.IGNORECASE),
    re.compile(r'vpaid', re.IGNORECASE),
    re.compile(r'ima', re.IGNORECASE),
    re.compile(r'adsense', re.IGNORECASE),
    re.compile(r'adwords', re.IGNORECASE),
    re.compile(r'admanager', re.IGNORECASE),
    re.compile(r'adview', re.IGNORECASE),
    re.compile(r'adclick', re.IGNORECASE),
    re.compile(r'adcount', re.IGNORECASE),
    re.compile(r'adframe', re.IGNORECASE),
    re.compile(r'adimage', re.IGNORECASE),
    re.compile(r'adlog', re.IGNORECASE),
    re.compile(r'adnet', re.IGNORECASE),
    re.compile(r'adobe', re.IGNORECASE),
    re.compile(r'adpicker', re.IGNORECASE),
    re.compile(r'adpoint', re.IGNORECASE),
    re.compile(r'adprovider', re.IGNORECASE),
    re.compile(r'adrequest', re.IGNORECASE),
    re.compile(r'adresponse', re.IGNORECASE),
    re.compile(r'adsdk', re.IGNORECASE),
    re.compile(r'adserver', re.IGNORECASE),
    re.compile(r'adspace', re.IGNORECASE),
    re.compile(r'adtag', re.IGNORECASE),
    re.compile(r'adtype', re.IGNORECASE),
    re.compile(r'adunit', re.IGNORECASE),
    re.compile(r'adurl', re.IGNORECASE),
    re.compile(r'advideo', re.IGNORECASE),
    re.compile(r'adzone', re.IGNORECASE),
    re.compile(r'bannerad', re.IGNORECASE),
    re.compile(r'bannerads', re.IGNORECASE),
    re.compile(r'clickad', re.IGNORECASE),
    re.compile(r'clickads', re.IGNORECASE),
    re.compile(r'flashad', re.IGNORECASE),
    re.compile(r'flashads', re.IGNORECASE),
    re.compile(r'html5ad', re.IGNORECASE),
    re.compile(r'html5ads', re.IGNORECASE),
    re.compile(r'imagead', re.IGNORECASE),
    re.compile(r'imageads', re.IGNORECASE),
    re.compile(r'inlinead', re.IGNORECASE),
    re.compile(r'inlineads', re.IGNORECASE),
    re.compile(r'layerad', re.IGNORECASE),
    re.compile(r'layerads', re.IGNORECASE),
    re.compile(r'linkad', re.IGNORECASE),
    re.compile(r'linkads', re.IGNORECASE),
    re.compile(r'mediaad', re.IGNORECASE),
    re.compile(r'mediaads', re.IGNORECASE),
    re.compile(r'popupad', re.IGNORECASE),
    re.compile(r'popupads', re.IGNORECASE),
    re.compile(r'popunder', re.IGNORECASE),
    re.compile(r'popunderad', re.IGNORECASE),
    re.compile(r'popunderads', re.IGNORECASE),
    re.compile(r'prerollad', re.IGNORECASE),
    re.compile(r'prerollads', re.IGNORECASE),
    re.compile(r'rollad', re.IGNORECASE),
    re.compile(r'rollads', re.IGNORECASE),
    re.compile(r'scrollad', re.IGNORECASE),
    re.compile(r'scrollads', re.IGNORECASE),
    re.compile(r'sidebarad', re.IGNORECASE),
    re.compile(r'sidebarads', re.IGNORECASE),
    re.compile(r'skyscraperad', re.IGNORECASE),
    re.compile(r'skyscraperads', re.IGNORECASE),
    re.compile(r'staticad', re.IGNORECASE),
    re.compile(r'staticads', re.IGNORECASE),
    re.compile(r'textad', re.IGNORECASE),
    re.compile(r'textads', re.IGNORECASE),
    re.compile(r'videoad', re.IGNORECASE),
    re.compile(r'videoads', re.IGNORECASE),
    re.compile(r'videoad', re.IGNORECASE),
    re.compile(r'videoads', re.IGNORECASE),
    re.compile(r'webad', re.IGNORECASE),
    re.compile(r'webads', re.IGNORECASE),
    re.compile(r'widgetad', re.IGNORECASE),
    re.compile(r'widgetads', re.IGNORECASE),
]

AD_DATERANGE_CLASSES = [
    'twitch-ad', 'twitchads', 'amazon', 'ad-break', 'advertisement',
    'twitch-stitched-ad', 'stitched-ad', 'preroll', 'midroll', 'postroll',
    'twitch-ad-quartile', 'ad-quartile', 'twitch-ad-roll',
    'ad', 'ads', 'advert', 'commercial', 'sponsor', 'promo',
    'twitch-ad-roll', 'twitch-ad-pod', 'twitch-ad-pod-position',
    'twitch-ad-pod-length', 'twitch-ad-url', 'twitch-ad-click-beacon-id',
    'twitch-ad-ad-format', 'twitch-ad-af-icr-ad-id',
    'twitch-ad-af-icr-creative-id', 'twitch-ad-af-icr-media-duration',
    'twitch-ad-dsa-ss-context', 'twitch-ad-dsa-ss-location',
    'twitch-ad-dsa-version', 'twitch-ad-loudness', 'twitch-ad-line-item-id',
    'twitch-ad-rads-token', 'twitch-ad-stitched', 'twitch-ad-stitched-ad',
    'twitch-ad-stitched-ad-roll', 'twitch-ad-stitched-ad-roll-type',
    'twitch-ad-stitched-ad-pod', 'twitch-ad-stitched-ad-pod-position',
    'twitch-ad-stitched-ad-pod-length', 'twitch-ad-stitched-ad-url',
    'twitch-ad-stitched-ad-click-beacon-id', 'twitch-ad-stitched-ad-ad-format',
    'twitch-ad-stitched-ad-af-icr-ad-id', 'twitch-ad-stitched-ad-af-icr-creative-id',
    'twitch-ad-stitched-ad-af-icr-media-duration', 'twitch-ad-stitched-ad-dsa-ss-context',
    'twitch-ad-stitched-ad-dsa-ss-location', 'twitch-ad-stitched-ad-dsa-version',
    'twitch-ad-stitched-ad-loudness', 'twitch-ad-stitched-ad-line-item-id',
    'twitch-ad-stitched-ad-rads-token',
]

AD_ZONE_START_TAGS = ('#EXT-X-CUE-OUT', '#EXT-X-SCTE35-OUT', '#EXT-X-SPLICEINSERT')
AD_ZONE_END_TAGS = ('#EXT-X-CUE-IN', '#EXT-X-SCTE35-IN')

# Additional ad indicators in DATERANGE attributes
AD_DATERANGE_KEYWORDS = [
    'ad-', 'ads', 'advert', 'preroll', 'midroll', 'postroll',
    'stitched', 'amazon', 'twitch-ad', 'commercial', 'sponsor', 'promo',
    'twitch-ad-roll', 'twitch-ad-pod', 'twitch-ad-pod-position',
    'twitch-ad-pod-length', 'twitch-ad-url', 'twitch-ad-click-beacon-id',
    'twitch-ad-ad-format', 'twitch-ad-af-icr-ad-id',
    'twitch-ad-af-icr-creative-id', 'twitch-ad-af-icr-media-duration',
    'twitch-ad-dsa-ss-context', 'twitch-ad-dsa-ss-location',
    'twitch-ad-dsa-version', 'twitch-ad-loudness', 'twitch-ad-line-item-id',
    'twitch-ad-rads-token', 'twitch-ad-stitched', 'twitch-ad-stitched-ad',
    'twitch-ad-stitched-ad-roll', 'twitch-ad-stitched-ad-roll-type',
    'twitch-ad-stitched-ad-pod', 'twitch-ad-stitched-ad-pod-position',
    'twitch-ad-stitched-ad-pod-length', 'twitch-ad-stitched-ad-url',
    'twitch-ad-stitched-ad-click-beacon-id', 'twitch-ad-stitched-ad-ad-format',
    'twitch-ad-stitched-ad-af-icr-ad-id', 'twitch-ad-stitched-ad-af-icr-creative-id',
    'twitch-ad-stitched-ad-af-icr-media-duration', 'twitch-ad-stitched-ad-dsa-ss-context',
    'twitch-ad-stitched-ad-dsa-ss-location', 'twitch-ad-stitched-ad-dsa-version',
    'twitch-ad-stitched-ad-loudness', 'twitch-ad-stitched-ad-line-item-id',
    'twitch-ad-stitched-ad-rads-token',
]

# Twitch-specific ad tags that indicate ad content
AD_TWITCH_TAGS = [
    'X-TV-TWITCH-AD-',
    'X-TV-TWITCH-AD-ROLL-TYPE',
    'X-TV-TWITCH-AD-POD-LENGTH',
    'X-TV-TWITCH-AD-POD-POSITION',
    'X-TV-TWITCH-AD-URL',
    'X-TV-TWITCH-AD-CLICK-BEACON-ID',
    'X-TV-TWITCH-AD-AD-FORMAT',
    'X-TV-TWITCH-AD-AF-ICR-AD-ID',
    'X-TV-TWITCH-AD-AF-ICR-CREATIVE-ID',
    'X-TV-TWITCH-AD-AF-ICR-MEDIA-DURATION',
    'X-TV-TWITCH-AD-DSA-SS-CONTEXT',
    'X-TV-TWITCH-AD-DSA-SS-LOCATION',
    'X-TV-TWITCH-AD-DSA-VERSION',
    'X-TV-TWITCH-AD-LOUDNESS',
    'X-TV-TWITCH-AD-LINE-ITEM-ID',
    'X-TV-TWITCH-AD-RADS-TOKEN',
]

# ---------------------------------------------------------------------------
# Caches (thread-safe)
# ---------------------------------------------------------------------------
_cache_lock = threading.Lock()

# segment cache: url -> (content_bytes, content_type, timestamp)
_segment_cache = OrderedDict()
SEGMENT_CACHE_MAX = 512
SEGMENT_TTL = 300  # 5 minutes

# playlist cache: url -> (processed_text, timestamp)
_playlist_cache = OrderedDict()
PLAYLIST_TTL = 4  # refresh slightly more often than target duration

# manifest cache: playlist_url -> (processed_text, timestamp)
_manifest_cache = OrderedDict()


def _cache_get(cache, key, ttl):
    with _cache_lock:
        entry = cache.get(key)
        if entry is None:
            return None
        content, ts = entry
        if time.time() - ts > ttl:
            cache.pop(key, None)
            return None
        # move to end (LRU)
        cache.move_to_end(key)
        return content


def _cache_put(cache, key, content, max_size):
    with _cache_lock:
        cache[key] = (content, time.time())
        cache.move_to_end(key)
        while len(cache) > max_size:
            cache.popitem(last=False)


def _cache_clear():
    with _cache_lock:
        _segment_cache.clear()
        _playlist_cache.clear()
        _manifest_cache.clear()


# ---------------------------------------------------------------------------
# Playlist processing
# ---------------------------------------------------------------------------
def _is_tag(line, names):
    for name in names:
        if line == name or line.startswith(name + ':'):
            return True
    return False


def _is_ad_daterange(line):
    """Check if a DATERANGE tag indicates an ad (class-based or keyword-based)."""
    lower = line.lower()
    # Check class attribute against known ad classes
    for cls in AD_DATERANGE_CLASSES:
        if ('class="%s"' % cls) in lower or ("class='%s'" % cls) in lower:
            return True
    # Check if any ad keyword appears in the tag
    for kw in AD_DATERANGE_KEYWORDS:
        if kw in lower:
            return True
    return False


def _has_twitch_ad_tag(line):
    """Check if a line contains any Twitch-specific ad tag."""
    for tag in AD_TWITCH_TAGS:
        if tag in line:
            return True
    return False


def _parse_ad_segments(lines):
    ad_indices = set()
    in_daterange_ad = False
    seen_dr_segment = False
    in_cue_ad = False

    for i, line in enumerate(lines):
        s = line.strip()

        # Check for Twitch-specific ad tags (X-TV-TWITCH-AD-*)
        if _has_twitch_ad_tag(s):
            ad_indices.add(i)
            # Also mark surrounding segments as ads
            in_daterange_ad = True
            seen_dr_segment = False
            continue

        if s.startswith('#EXT-X-DATERANGE:'):
            if _is_ad_daterange(s):
                ad_indices.add(i)
                in_daterange_ad = True
                seen_dr_segment = False
            else:
                in_daterange_ad = False
            continue

        if _is_tag(s, AD_ZONE_START_TAGS):
            ad_indices.add(i)
            in_cue_ad = True
            continue

        if _is_tag(s, AD_ZONE_END_TAGS):
            ad_indices.add(i)
            in_cue_ad = False
            continue

        if s.startswith('#EXT-X-DISCONTINUITY'):
            if in_daterange_ad:
                ad_indices.add(i)
                if seen_dr_segment:
                    in_daterange_ad = False
                    seen_dr_segment = False
            elif in_cue_ad:
                ad_indices.add(i)
                continue

        if not s.startswith('#') and s:
            if in_daterange_ad or in_cue_ad:
                ad_indices.add(i)
                seen_dr_segment = True
        elif s.startswith('#EXT-X-ENDLIST'):
            in_daterange_ad = False
            in_cue_ad = False

    return ad_indices


def _parse_url_pattern_ad_segments(lines):
    ad_indices = set()
    for i, line in enumerate(lines):
        s = line.strip()
        if not s.startswith('#') and s and any(p.search(s) for p in AD_URL_PATTERNS):
            ad_indices.add(i)
            j = i - 1
            while j >= 0:
                prev = lines[j].strip()
                if prev.startswith('#EXTINF') or prev.startswith('#EXT-X-DISCONTINUITY'):
                    ad_indices.add(j)
                    j -= 1
                else:
                    break
            j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if nxt.startswith('#EXT-X-DISCONTINUITY'):
                    ad_indices.add(j)
                    j += 1
                else:
                    break
    return ad_indices


class _ProxyState:
    playlist_url = None
    headers = {}
    proxy_base = None
    url_map = {}
    _lock = threading.Lock()


def _rewrite_url(absolute_url):
    proxy_base = _ProxyState.proxy_base
    if not proxy_base:
        return absolute_url
    with _ProxyState._lock:
        key = uuid.uuid4().hex[:12]
        _ProxyState.url_map[key] = absolute_url
    return '%s/proxy/%s' % (proxy_base.rstrip('/'), key)


def _process_playlist(content, base_url):
    if not content:
        return content

    lines = content.splitlines(keepends=True)
    ad_indices = _parse_ad_segments(lines) | _parse_url_pattern_ad_segments(lines)

    # Remove EXTINF tags that precede removed segments (avoid orphaned tags)
    for i in list(ad_indices):
        s = lines[i].strip()
        if not s.startswith('#') and s:
            j = i - 1
            if j >= 0 and lines[j].strip().startswith('#EXTINF'):
                ad_indices.add(j)

    out = []
    for i, line in enumerate(lines):
        if i in ad_indices:
            continue
        s = line.strip()
        ending = '\n' if line.endswith('\n') else ''
        if not s.startswith('#') and s:
            absolute = urljoin(base_url, s)
            out.append(_rewrite_url(absolute) + ending)
        elif 'URI="' in line:
            def _uri_repl(m):
                return 'URI="%s"' % _rewrite_url(urljoin(base_url, m.group(1)))
            out.append(re.sub(r'URI="([^"]*)"', _uri_repl, line))
        else:
            out.append(line)
    return ''.join(out)


# ---------------------------------------------------------------------------
# HTTP fetch with session, retries, and SSL fallback
# ---------------------------------------------------------------------------
_session = None
_session_lock = threading.Lock()


def _get_session():
    global _session
    if _session is None:
        with _session_lock:
            if _session is None:
                _session = requests.Session()
                adapter = requests.adapters.HTTPAdapter(
                    pool_connections=50,
                    pool_maxsize=50,
                    max_retries=0,
                )
                _session.mount('http://', adapter)
                _session.mount('https://', adapter)
    return _session


def _fetch(url, headers, timeout=30, stream=False):
    session = _get_session()
    last_exc = None
    for attempt in range(3):
        try:
            resp = session.get(url, headers=headers, timeout=timeout, stream=stream)
            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt < 2:
                    time.sleep(0.3 * (attempt + 1))
                    continue
            return resp
        except requests.exceptions.SSLError:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            return session.get(url, headers=headers, timeout=timeout, stream=stream, verify=False)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_exc = e
            if attempt < 2:
                time.sleep(0.2 * (attempt + 1))
                continue
    if last_exc:
        raise last_exc
    return resp


# ---------------------------------------------------------------------------
# HTTP request handler
# ---------------------------------------------------------------------------
class AdBlockHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    timeout = 30

    def log_message(self, format, *args):
        pass

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError):
            self.close_connection = True
        except Exception:
            self.close_connection = True

    # -- GET routing -------------------------------------------------------
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ('/manifest.m3u8', '/playlist.m3u8'):
            self._handle_manifest()
        elif path == '/health':
            self._respond(200, b'OK', 'text/plain')
        elif path.startswith('/proxy/'):
            key = path[len('/proxy/'):]
            with _ProxyState._lock:
                target = _ProxyState.url_map.get(key)
            self._handle_proxy_url(target)
        else:
            self._respond(404, b'Not found', 'text/plain')

    # -- manifest (initial + playlist refresh) -----------------------------
    def _handle_manifest(self):
        with _ProxyState._lock:
            playlist_url = _ProxyState.playlist_url
            headers = dict(_ProxyState.headers)

        if not playlist_url:
            self._respond(503, b'No playlist URL configured', 'text/plain')
            return

        # Check manifest cache first
        cached = _cache_get(_manifest_cache, playlist_url, PLAYLIST_TTL)
        if cached is not None:
            self._respond(200, cached, 'application/vnd.apple.mpegurl')
            return

        try:
            resp = _fetch(playlist_url, headers)
            resp.raise_for_status()
        except Exception as e:
            # Fallback to playlist cache
            cached = _cache_get(_playlist_cache, playlist_url, 60)
            if cached:
                log_utils.log('AdBlockProxy: Twitch unreachable, serving cached playlist',
                              log_utils.LOGWARNING)
                self._respond(200, cached.encode('utf-8'), 'application/vnd.apple.mpegurl')
                return
            log_utils.log('AdBlockProxy: Failed to fetch playlist: %s' % str(e),
                          log_utils.LOGERROR)
            self._respond(502, b'Failed to fetch playlist', 'text/plain')
            return

        content_type = resp.headers.get('Content-Type', 'application/vnd.apple.mpegurl')
        processed = _process_playlist(resp.text, playlist_url)

        _cache_put(_manifest_cache, playlist_url, processed.encode('utf-8'), 10)

        if processed != resp.text:
            log_utils.log('AdBlockProxy: Processed playlist (ads filtered)', log_utils.LOGDEBUG)
            # Debug: log ad-related lines from raw playlist
            raw_lines = resp.text.splitlines()
            ad_lines = [l.strip() for l in raw_lines if 'ad' in l.lower() or 'DATERANGE' in l or 'CUE' in l or 'DISCONTINUITY' in l]
            if ad_lines:
                log_utils.log('AdBlockProxy: Raw ad lines: %s' % ' | '.join(ad_lines[:10]), log_utils.LOGDEBUG)
        else:
            log_utils.log('AdBlockProxy: No ads detected in playlist', log_utils.LOGDEBUG)

        self._respond(200, processed.encode('utf-8'), content_type)

    # -- proxied URLs (variant playlists + segments) ------------------------
    def _handle_proxy_url(self, target_url):
        if not target_url:
            self._respond(404, b'Unknown proxy target', 'text/plain')
            return

        with _ProxyState._lock:
            headers = dict(_ProxyState.headers)

        is_playlist = '.m3u8' in urlparse(target_url).path.lower()

        if is_playlist:
            # Variant playlist: check cache
            cached = _cache_get(_playlist_cache, target_url, PLAYLIST_TTL)
            if cached is not None:
                self._respond(200, cached.encode('utf-8'), 'application/vnd.apple.mpegurl')
                return
            try:
                resp = _fetch(target_url, headers)
                resp.raise_for_status()
            except Exception as e:
                cached = _cache_get(_playlist_cache, target_url, 60)
                if cached:
                    self._respond(200, cached.encode('utf-8'), 'application/vnd.apple.mpegurl')
                    return
                log_utils.log('AdBlockProxy: Failed to fetch proxied playlist: %s' % str(e),
                              log_utils.LOGERROR)
                self._respond(502, b'Failed to fetch playlist', 'text/plain')
                return

            content_type = resp.headers.get('Content-Type', 'application/vnd.apple.mpegurl')
            processed = _process_playlist(resp.text, target_url)
            _cache_put(_playlist_cache, target_url, processed, 50)
            self._respond(200, processed.encode('utf-8'), content_type)
            return

        # Media segment: check cache first
        cached_content = _cache_get(_segment_cache, target_url, SEGMENT_TTL)
        if cached_content is not None:
            content, content_type = cached_content
            self._respond(200, content, content_type)
            return

        try:
            resp = _fetch(target_url, headers, timeout=30, stream=True)
            resp.raise_for_status()
        except (ConnectionResetError, BrokenPipeError):
            return
        except Exception as e:
            log_utils.log('AdBlockProxy: Failed to fetch segment: %s' % str(e),
                          log_utils.LOGWARNING)
            self._respond(502, b'Failed to fetch segment', 'text/plain')
            return

        content_type = resp.headers.get('Content-Type', 'video/MP2T')

        # Read full content for caching (segments are small, ~1-2 MB)
        try:
            content = resp.content
        except Exception:
            self._respond(502, b'Failed to read segment', 'text/plain')
            return

        _cache_put(_segment_cache, target_url, (content, content_type), SEGMENT_CACHE_MAX)
        self._respond(200, content, content_type)

    # -- response helper ---------------------------------------------------
    def _respond(self, status, body, content_type):
        try:
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, BrokenPipeError):
            pass
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Proxy server
# ---------------------------------------------------------------------------
class AdBlockProxy:
    """
    Local HTTP proxy that filters Twitch ad segments from HLS playlists.
    Uses segment caching, playlist caching, and connection pooling for
    high-performance parallel request handling.
    """

    def __init__(self):
        self._server = None
        self._thread = None
        self._port = 0

    def start(self, playlist_url, headers=None):
        with _ProxyState._lock:
            _ProxyState.playlist_url = playlist_url
            _ProxyState.headers = headers or {}
            _ProxyState.proxy_base = None
            _ProxyState.url_map = {}

        self._server = HTTPServer(('127.0.0.1', 0), AdBlockHandler)
        self._server.daemon_threads = True
        self._port = self._server.server_address[1]
        with _ProxyState._lock:
            _ProxyState.proxy_base = 'http://127.0.0.1:%d' % self._port
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        log_utils.log('AdBlockProxy: Started on port %d' % self._port, log_utils.LOGINFO)

    def get_proxy_url(self):
        if not self._port:
            return None
        return 'http://127.0.0.1:%d/manifest.m3u8' % self._port

    def update_playlist_url(self, playlist_url, headers=None):
        with _ProxyState._lock:
            _ProxyState.playlist_url = playlist_url
            if headers is not None:
                _ProxyState.headers = headers

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
            self._thread = None
            with _ProxyState._lock:
                _ProxyState.proxy_base = None
                _ProxyState.url_map = {}
            _cache_clear()
            log_utils.log('AdBlockProxy: Stopped', log_utils.LOGINFO)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_proxy_instance = None


def get_proxy():
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = AdBlockProxy()
    return _proxy_instance
