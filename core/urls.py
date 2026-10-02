"""URL normalisation, shared by the retriever and the report verifier.

Tavily returns the same paper under many spellings, so exact-string dedupe
lets near-identical sources through and inflates the source list.
"""

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = re.compile(
    r"^(utm_|fbclid$|gclid$|mc_[ce]id$|igshid$|ref$|ref_src$|source$|spm$|yclid$|_hsenc$|_hsmi$)"
)

# arxiv.org/abs/2005.11401v3 -> arxiv.org/abs/2005.11401
# pre-2007 ids carry a category slash: hep-th/9901001v3 -> hep-th/9901001
ARXIV_VERSION = re.compile(r"(/abs/[\w./\-]+?)v\d+$")


def canonical_url(url: str) -> str:
    """Collapse a URL to the form that identifies the same underlying page."""
    if not url:
        return ""
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return url.strip().lower()

    scheme = "https"
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]

    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    path = ARXIV_VERSION.sub(r"\1", path)

    kept = [(k, v) for k, v in parse_qsl(parts.query) if not TRACKING_PARAMS.match(k.lower())]
    query = urlencode(sorted(kept))

    return urlunsplit((scheme, host, path, query, ""))
