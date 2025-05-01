import unittest
import os
import json
import re


class ExtensionApiSecurityTest(unittest.TestCase):
    """Tests to ensure the extension properly implements API security"""

    def setUp(self):
        self.background_js_path = os.path.join(
            os.path.dirname(__file__), "../../src/extension/background/background.js"
        )

        # API key that should be in the background.js file
        self.expected_api_key = "vid-xyz-123456789-vidify-secure-key"

    def test_api_key_exists_in_background_js(self):
        """Verify the API key is defined in background.js"""
        with open(self.background_js_path, "r") as f:
            content = f.read()

        # Check if API_KEY variable is defined with the correct value
        api_key_pattern = r'const\s+API_KEY\s*=\s*[\'"]([^\'"]+)[\'"]'
        match = re.search(api_key_pattern, content)

        self.assertIsNotNone(match, "API_KEY constant not found in background.js")
        self.assertEqual(
            match.group(1),
            self.expected_api_key,
            "API_KEY value doesn't match expected value",
        )

    def test_api_key_included_in_fetch_requests(self):
        """Verify the API key is included in all fetch request headers"""
        with open(self.background_js_path, "r") as f:
            content = f.read()

        # Check for required patterns directly in the file content
        # Pattern that would indicate headers with API key for transcript search
        transcript_pattern = (
            r"headers.*?['\"]X-API-Key['\"].*?API_KEY.*?transcript_search"
        )
        # Pattern for object search
        object_pattern = r"headers.*?['\"]X-API-Key['\"].*?API_KEY.*?object_search"
        # Pattern for fetchFromSPI
        spi_pattern = r"headers.*?['\"]X-API-Key['\"].*?API_KEY.*?fetchFromSPI"

        # Check that all fetch requests to these endpoints include the API key
        self.assertTrue(
            re.search(transcript_pattern, content, re.DOTALL)
            or re.search(
                r"transcript_search.*?headers.*?['\"]X-API-Key['\"].*?API_KEY",
                content,
                re.DOTALL,
            ),
            "X-API-Key header with API_KEY not found in transcript_search",
        )

        self.assertTrue(
            re.search(object_pattern, content, re.DOTALL)
            or re.search(
                r"object_search.*?headers.*?['\"]X-API-Key['\"].*?API_KEY",
                content,
                re.DOTALL,
            ),
            "X-API-Key header with API_KEY not found in object_search",
        )

        self.assertTrue(
            re.search(spi_pattern, content, re.DOTALL)
            or re.search(
                r"fetchFromSPI.*?headers.*?['\"]X-API-Key['\"].*?API_KEY",
                content,
                re.DOTALL,
            ),
            "X-API-Key header with API_KEY not found in fetchFromSPI",
        )

    def test_manifest_includes_required_hosts(self):
        """Verify the manifest.json includes necessary host permissions"""
        manifest_path = os.path.join(
            os.path.dirname(__file__), "../../src/extension/manifest.json"
        )

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        # Check host permissions
        self.assertIn(
            "host_permissions", manifest, "manifest.json is missing host_permissions"
        )

        # Check for API URL in host permissions
        api_permissions = False
        for permission in manifest["host_permissions"]:
            if "vidify-378225991600.us-central1.run.app" in permission:
                api_permissions = True
                break

        self.assertTrue(
            api_permissions, "manifest.json is missing permission for the API host"
        )


if __name__ == "__main__":
    unittest.main()
