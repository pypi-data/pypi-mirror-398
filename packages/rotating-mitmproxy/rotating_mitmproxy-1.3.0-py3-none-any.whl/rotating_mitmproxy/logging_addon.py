"""
Logging addon for rotating mitmproxy.

Provides 3-level logging system:
- minimal: Summary stats only, no per-request logging
- normal: Log page requests (exclude assets), show all events
- verbose: Log all requests including assets
"""

import time
import logging
from typing import Optional, Set
from urllib.parse import urlparse

from mitmproxy import http


# Asset extensions to filter out in 'normal' mode
ASSET_EXTENSIONS: Set[str] = {
    '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
    '.woff', '.woff2', '.ttf', '.eot', '.otf',  # Fonts
    '.webp', '.avif', '.bmp',  # Images
    '.mp4', '.webm', '.mp3', '.wav', '.ogg',  # Media
    '.map',  # Source maps
}

# URL path patterns that indicate asset requests
ASSET_PATH_PATTERNS: Set[str] = {
    '/image/', '/images/', '/img/', '/assets/', '/static/',
    '/css/', '/js/', '/fonts/', '/media/', '/files/',
}

# Content-type prefixes that indicate assets
ASSET_CONTENT_TYPES: Set[str] = {
    'image/', 'font/', 'audio/', 'video/',
    'text/css', 'application/javascript', 'text/javascript',
    'application/font', 'application/x-font',
}


class LoggingAddon:
    """
    Unified logging addon for rotating mitmproxy.
    
    Log levels:
    - minimal: Only startup, periodic stats, and major events (proxy failures)
    - normal: Page requests + all events (default)
    - verbose: All requests including assets + all events
    """
    
    def __init__(self, log_level: str = 'normal', rotator=None, stats_interval: int = 30):
        """
        Initialize logging addon.
        
        Args:
            log_level: 'minimal', 'normal', or 'verbose'
            rotator: ProxyRotator instance for stats
            stats_interval: Seconds between periodic stats (for minimal mode)
        """
        self.log_level = log_level
        self.rotator = rotator
        self.stats_interval = stats_interval
        
        self.logger = logging.getLogger("rotating_mitmproxy")
        
        # Request tracking for periodic stats
        self.request_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.last_stats_time = time.time()
    
    def _is_asset(self, url: str, response=None) -> bool:
        """
        Check if URL is an asset request.
        
        Uses multiple heuristics:
        1. File extension in URL path
        2. URL path patterns (e.g., /image/, /static/)
        3. Content-Type from response header
        """
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Check file extension
        if any(path.endswith(ext) for ext in ASSET_EXTENSIONS):
            return True
        
        # Check path patterns
        if any(pattern in path for pattern in ASSET_PATH_PATTERNS):
            return True
        
        # Check content-type from response
        if response and response.headers:
            content_type = response.headers.get('content-type', '').lower()
            if any(content_type.startswith(ct) for ct in ASSET_CONTENT_TYPES):
                return True
        
        return False
    
    def _get_short_url(self, url: str, max_len: int = 60) -> str:
        """Get shortened URL for logging."""
        if len(url) <= max_len:
            return url
        return url[:max_len - 3] + "..."
    
    def response(self, flow: http.HTTPFlow) -> None:
        """Handle response - log request result."""
        # Get request metadata
        request_start = flow.metadata.get("request_start_time", time.time())
        response_time = time.time() - request_start
        proxy_id = flow.metadata.get("selected_proxy", "direct")
        url = flow.request.pretty_url
        method = flow.request.method
        
        # Determine success/failure
        success = flow.response is not None and flow.response.status_code < 400
        status = flow.response.status_code if flow.response else "ERR"
        
        # Update counters
        self.request_count += 1
        if success:
            self.success_count += 1
        else:
            self.fail_count += 1
        
        # Determine if we should log this request
        should_log = False
        if self.log_level == 'verbose':
            should_log = True
        elif self.log_level == 'normal':
            should_log = not self._is_asset(url, flow.response)
        elif self.log_level == 'minimal':
            # In minimal mode, only log failures
            should_log = not success
        
        # Log request result
        if should_log:
            short_url = self._get_short_url(url)
            icon = "✓" if success else "✗"
            self.logger.info(f"{icon} {method} {short_url} → {status} ({response_time:.2f}s) via {proxy_id}")
        
        # Periodic stats for minimal mode
        if self.log_level == 'minimal':
            self._maybe_log_stats()
    
    def error(self, flow: http.HTTPFlow) -> None:
        """Handle connection errors."""
        url = flow.request.pretty_url
        proxy_id = flow.metadata.get("selected_proxy", "direct")
        
        self.request_count += 1
        self.fail_count += 1
        
        # Always log connection errors
        short_url = self._get_short_url(url)
        self.logger.warning(f"✗ {flow.request.method} {short_url} → CONNECTION ERROR via {proxy_id}")
    
    def _maybe_log_stats(self) -> None:
        """Log periodic stats if interval has passed."""
        current_time = time.time()
        elapsed = current_time - self.last_stats_time
        
        if elapsed >= self.stats_interval:
            self._log_stats(elapsed)
            self.last_stats_time = current_time
            # Reset counters for next interval
            self.request_count = 0
            self.success_count = 0
            self.fail_count = 0
    
    def _log_stats(self, elapsed: float) -> None:
        """Log summary statistics."""
        if self.rotator:
            try:
                stats = self.rotator.get_statistics()
                healthy = stats['healthy_proxies']
                total = stats['total_proxies']
                
                self.logger.info(
                    f"[{elapsed:.0f}s] {self.request_count} req "
                    f"({self.success_count} ok, {self.fail_count} fail) | "
                    f"{healthy}/{total} proxies healthy"
                )
            except Exception:
                self.logger.info(
                    f"[{elapsed:.0f}s] {self.request_count} req "
                    f"({self.success_count} ok, {self.fail_count} fail)"
                )
        else:
            self.logger.info(
                f"[{elapsed:.0f}s] {self.request_count} req "
                f"({self.success_count} ok, {self.fail_count} fail)"
            )


def create_logging_addon(log_level: str = 'normal', rotator=None, 
                         stats_interval: int = 30) -> LoggingAddon:
    """Factory function to create logging addon."""
    return LoggingAddon(log_level=log_level, rotator=rotator, 
                        stats_interval=stats_interval)
