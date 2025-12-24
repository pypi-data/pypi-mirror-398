"""
Test URL normalization and deduplication
"""
import pytest
from deepharvest.core.url_utils import URLNormalizer, deduplicate_urls

class TestURLNormalizer:
    """Test URL normalization"""
    
    def test_normalize_scheme_and_host(self):
        """Test scheme and host normalization"""
        url = "HTTP://WWW.EXAMPLE.COM/path"
        normalized = URLNormalizer.normalize(url)
        assert normalized == "http://www.example.com/path"
    
    def test_remove_default_ports(self):
        """Test default port removal"""
        url = "http://example.com:80/path"
        normalized = URLNormalizer.normalize(url)
        assert normalized == "http://example.com/path"
        
        url = "https://example.com:443/path"
        normalized = URLNormalizer.normalize(url)
        assert normalized == "https://example.com/path"
    
    def test_remove_tracking_params(self):
        """Test tracking parameter removal"""
        url = "https://example.com/page?utm_source=test&utm_campaign=ad&id=123"
        normalized = URLNormalizer.normalize(url)
        assert "utm_source" not in normalized
        assert "utm_campaign" not in normalized
        assert "id=123" in normalized
    
    def test_remove_trailing_slash(self):
        """Test trailing slash removal"""
        url = "https://example.com/path/"
        normalized = URLNormalizer.normalize(url)
        assert normalized == "https://example.com/path"
    
    def test_collapse_slashes(self):
        """Test duplicate slash collapsing"""
        url = "https://example.com//path///to////page"
        normalized = URLNormalizer.normalize(url)
        assert normalized == "https://example.com/path/to/page"
    
    def test_remove_fragment(self):
        """Test fragment removal"""
        url = "https://example.com/page#section"
        normalized = URLNormalizer.normalize(url)
        assert "#" not in normalized

@pytest.mark.asyncio
async def test_deduplicate_urls():
    """Test URL deduplication"""
    urls = [
        "https://example.com/page",
        "https://example.com/page/",
        "https://example.com/page?utm_source=test"
    ]
    
    deduplicated = await deduplicate_urls(urls)
    assert len(deduplicated) == 1

