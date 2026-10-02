"""Same paper, several spellings, one source.

Tavily returns arXiv preprints under both their versioned abstract path and
mirrors, so exact-string dedupe lets near-identical sources through and pads
the report's source list. Pre-2007 identifiers carry a slash (hep-th/9901001),
which is the common case in older literature and the one a naive version
regex misses.
"""

from core.urls import canonical_url


def test_new_style_arxiv_versions_collapse():
    assert canonical_url("https://arxiv.org/abs/2005.11401v1") == canonical_url(
        "https://arxiv.org/abs/2005.11401v2"
    )


def test_old_style_arxiv_versions_collapse():
    """hep-th/9901001 -- every pre-2007 id has a category slash."""
    assert canonical_url("https://arxiv.org/abs/hep-th/9901001v1") == canonical_url(
        "https://arxiv.org/abs/hep-th/9901001v2"
    )


def test_tracking_and_www_are_stripped():
    assert canonical_url(
        "http://www.Arxiv.org/abs/2005.11401?utm_source=x#s"
    ) == canonical_url("https://arxiv.org/abs/2005.11401")