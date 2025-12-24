
import requests
import re
import hashlib
from .config import USER_AGENT

# This global dictionary will be populated by canopy.py before threads start
fingerprints = {}


def clean_html(html):
    """Remove whitespace and scripts from HTML for fingerprinting"""
    html = re.sub(r'\s+', '', html)
    html = re.sub(r'<script.*?>.*?</script>', '', html, flags=re.DOTALL)
    return html


def hash_html(html):
    """Generate hash of cleaned HTML"""
    return hashlib.md5(html.encode()).hexdigest()


def check_username(job, timeout):
    """
    job = { "platform": platform_name, "url": profile_url, "username": username }
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.get(job['url'], headers=headers, timeout=timeout, allow_redirects=True)

        # Status code check
        if response.status_code >= 400:
            return {"status": "MISSING", "platform": job['platform']}

        # Redirect check
        if response.url.strip('/') != job['url'].strip('/'):
            false_redirects = ['login', 'signup', 'search', 'typo', '404', 'user-not-found', 'error', 'notfound']
            if any(k in response.url.lower() for k in false_redirects):
                return {"status": "MISSING", "platform": job['platform']}

        # Fingerprint check
        fp = fingerprints.get(job['platform'])
        if fp:
            html_clean = clean_html(response.text)[:500]
            html_hash = hash_html(html_clean)
            if html_hash == fp:
                return {"status": "MISSING", "platform": job['platform']}

        # Keyword check
        error_msg = job.get('errorMsg', '').lower()
        content_lower = response.text.lower()
        generic_errors = ["not found", "does not exist", "couldn't find"]
        if (error_msg and error_msg in content_lower) or any(k in content_lower for k in generic_errors):
            return {"status": "MISSING", "platform": job['platform']}

        # Passed all checks
        return {"status": "FOUND", "platform": job['platform'], "url": response.url}

    except Exception:
        return {"status": "ERROR", "platform": job['platform']}
