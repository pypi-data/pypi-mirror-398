"""
Test trap detection
"""
import pytest
from deepharvest.traps.detector import TrapDetector

class TestTrapDetector:
    """Test trap detection"""
    
    @pytest.mark.asyncio
    async def test_calendar_trap(self):
        """Test calendar trap detection"""
        detector = TrapDetector()
        
        url = "https://example.com/archive/2024/01/15/"
        assert detector._is_calendar_trap(url)
        
        url = "https://example.com/normal-page/"
        assert not detector._is_calendar_trap(url)
    
    @pytest.mark.asyncio
    async def test_session_id_trap(self):
        """Test session ID trap detection"""
        detector = TrapDetector()
        
        # Use a session ID longer than 20 characters (the threshold)
        url = "https://example.com/page?sessionid=abc123def456ghi789jkl012mno345pqr678"
        assert detector._is_session_id_trap(url)
        
        # Short session ID should not be detected
        url = "https://example.com/page?sessionid=abc123"
        assert not detector._is_session_id_trap(url)
        
        url = "https://example.com/page?id=123"
        assert not detector._is_session_id_trap(url)
    
    @pytest.mark.asyncio
    async def test_url_length_trap(self):
        """Test excessive URL length trap"""
        detector = TrapDetector()
        
        long_url = "https://example.com/" + "a" * 600
        assert detector._is_url_length_trap(long_url)
        
        normal_url = "https://example.com/normal-page"
        assert not detector._is_url_length_trap(normal_url)

