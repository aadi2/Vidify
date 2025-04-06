import pytest
import sys
import os

# Add src directory to path for imports to work
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../src'))

from backend.utils.url_validator import is_valid_youtube_url, extract_video_id


class TestUrlValidator:
    """Test cases for the URL validator functions."""

    def test_valid_youtube_urls(self):
        """Test valid YouTube URLs should pass validation."""
        valid_urls = [
            # Standard youtube.com URLs
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "youtube.com/watch?v=dQw4w9WgXcQ",
            "www.youtube.com/watch?v=dQw4w9WgXcQ",
            # URL with additional parameters
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLx65qkgCWNJIgVrndMrhc2-zdTslZNlio",
            # youtu.be short URLs
            "https://youtu.be/dQw4w9WgXcQ",
            "http://youtu.be/dQw4w9WgXcQ",
            "youtu.be/dQw4w9WgXcQ",
            # youtu.be with timestamp
            "https://youtu.be/dQw4w9WgXcQ?t=10",
            # Embed URLs
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "youtube.com/embed/dQw4w9WgXcQ",
            # Shorts
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "youtube.com/shorts/dQw4w9WgXcQ",
        ]

        for url in valid_urls:
            assert is_valid_youtube_url(url), f"URL should be valid: {url}"

    def test_invalid_youtube_urls(self):
        """Test invalid URLs should fail validation."""
        invalid_urls = [
            # Empty/None values
            "",
            None,
            # Malformed URLs
            "youtube",
            "youtube.com",
            "htt://www.youtube.com/watch?v=dQw4w9WgXcQ",
            # Missing video IDs
            "https://www.youtube.com/watch",
            "https://www.youtube.com/watch?v=",
            "https://youtu.be/",
            # Other video platforms
            "https://vimeo.com/123456789",
            "https://www.dailymotion.com/video/x7tfqtp",
            # Same-domain incorrect paths
            "https://www.youtube.com/results?search_query=test",
            "https://www.youtube.com/feed/trending",
            # Malicious attempts
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            # Invalid protocols
            "file:///etc/passwd",
            "data:text/html;base64,PHNjcmlwdD5hbGVydCgnWFNTJyk8L3NjcmlwdD4=",
        ]

        for url in invalid_urls:
            assert not is_valid_youtube_url(url), f"URL should be invalid: {url}"

    def test_video_id_extraction(self):
        """Test extracting video IDs from valid YouTube URLs."""
        test_cases = [
            # Standard youtube.com URLs
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("http://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s", "dQw4w9WgXcQ"),
            # youtu.be URLs
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("http://youtu.be/dQw4w9WgXcQ?t=10", "dQw4w9WgXcQ"),
            # Embed URLs
            ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            # Shorts
            ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ]

        for url, expected_id in test_cases:
            assert extract_video_id(url) == expected_id, f"Failed to extract ID from {url}"

    def test_invalid_video_id_extraction(self):
        """Test extracting video IDs from invalid URLs returns None."""
        invalid_urls = [
            "",
            None,
            "youtube.com",
            "https://www.youtube.com/watch",
            "https://vimeo.com/123456789",
        ]

        for url in invalid_urls:
            assert extract_video_id(url) is None, f"Should not extract ID from {url}"


if __name__ == "__main__":
    pytest.main(["-v", "url_validator_test.py"])