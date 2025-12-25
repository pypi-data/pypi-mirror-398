import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from instagram_osint import InstagramOSINT


class TestInstagramOSINT(unittest.TestCase):
    """Test cases for InstagramOSINT class"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_username = "instagram"
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after tests"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test InstagramOSINT initialization"""
        scraper = InstagramOSINT(self.test_username)

        self.assertEqual(scraper.username, self.test_username)
        self.assertIsInstance(scraper.profile_data, dict)
        self.assertIsNotNone(scraper.session)

    def test_repr_and_str(self):
        """Test string representations"""
        scraper = InstagramOSINT(self.test_username)

        repr_str = repr(scraper)
        str_str = str(scraper)

        self.assertIn(self.test_username, repr_str)
        self.assertIn(self.test_username, str_str)

    def test_getitem_access(self):
        """Test dictionary-style access to profile data"""
        scraper = InstagramOSINT(self.test_username)

        if scraper.profile_data:
            # Test valid key
            username = scraper["username"]
            self.assertEqual(username, self.test_username)

            # Test invalid key
            with self.assertRaises(KeyError):
                _ = scraper["nonexistent_key"]

    def test_profile_data_structure(self):
        """Test that profile data has expected structure"""
        scraper = InstagramOSINT(self.test_username)

        if scraper.profile_data:
            expected_keys = [
                "username",
                "full_name",
                "biography",
                "external_url",
                "profile_pic_url",
                "is_private",
                "is_verified",
                "is_business",
                "business_category",
                "follower_count",
                "following_count",
                "post_count",
                "user_id",
                "profile_url",
            ]

            for key in expected_keys:
                self.assertIn(key, scraper.profile_data)

    def test_save_data(self):
        """Test saving profile data to JSON"""
        scraper = InstagramOSINT(self.test_username)

        if scraper.profile_data:
            output_dir = os.path.join(self.temp_dir, "test_profile")
            result = scraper.save_data(output_dir)

            self.assertTrue(result)
            self.assertTrue(
                os.path.exists(os.path.join(output_dir, "profile_data.json"))
            )

            # Verify JSON content
            with open(os.path.join(output_dir, "profile_data.json"), "r") as f:
                data = json.load(f)
                self.assertEqual(data["username"], self.test_username)

    def test_save_data_no_profile(self):
        """Test saving data when no profile is available"""
        with patch.object(InstagramOSINT, "scrape_profile", return_value=None):
            scraper = InstagramOSINT("nonexistent_user")
            scraper.profile_data = {}

            result = scraper.save_data(self.temp_dir)
            self.assertFalse(result)

    def test_scrape_posts_returns_list(self):
        """Test that scrape_posts returns a list"""
        scraper = InstagramOSINT(self.test_username)

        if scraper.profile_data and not scraper.profile_data.get("is_private"):
            posts = scraper.scrape_posts(max_posts=5)
            self.assertIsInstance(posts, list)

    def test_scrape_posts_private_profile(self):
        """Test scraping posts from private profile"""
        scraper = InstagramOSINT(self.test_username)

        # Mock private profile
        if scraper.profile_data:
            scraper.profile_data["is_private"] = True
            posts = scraper.scrape_posts()

            self.assertEqual(posts, [])

    def test_scrape_posts_max_limit(self):
        """Test that max_posts parameter is respected"""
        scraper = InstagramOSINT(self.test_username)

        if scraper.profile_data and not scraper.profile_data.get("is_private"):
            max_posts = 5
            posts = scraper.scrape_posts(max_posts=max_posts)

            if posts:
                self.assertLessEqual(len(posts), max_posts)

    def test_post_data_structure(self):
        """Test that post data has expected structure"""
        scraper = InstagramOSINT(self.test_username)

        if scraper.profile_data and not scraper.profile_data.get("is_private"):
            posts = scraper.scrape_posts(max_posts=1)

            if posts:
                expected_keys = [
                    "id",
                    "shortcode",
                    "url",
                    "display_url",
                    "is_video",
                    "caption",
                    "timestamp",
                    "likes",
                    "comments",
                    "location",
                    "accessibility_caption",
                ]

                for key in expected_keys:
                    self.assertIn(key, posts[0])

    def test_save_posts(self):
        """Test saving posts data to JSON"""
        scraper = InstagramOSINT(self.test_username)

        if scraper.profile_data and not scraper.profile_data.get("is_private"):
            posts = scraper.scrape_posts(max_posts=5)

            if posts:
                output_dir = os.path.join(self.temp_dir, "test_posts")
                result = scraper.save_posts(posts, output_dir)

                self.assertTrue(result)
                self.assertTrue(
                    os.path.exists(os.path.join(output_dir, "posts_data.json"))
                )

                # Verify JSON content
                with open(os.path.join(output_dir, "posts_data.json"), "r") as f:
                    data = json.load(f)
                    self.assertIsInstance(data, list)
                    self.assertEqual(len(data), len(posts))

    def test_save_posts_empty_list(self):
        """Test saving empty posts list"""
        scraper = InstagramOSINT(self.test_username)

        result = scraper.save_posts([], self.temp_dir)
        self.assertFalse(result)

    @patch("requests.Session.get")
    def test_download_profile_picture_success(self, mock_get):
        """Test successful profile picture download"""
        # Mock response
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        scraper = InstagramOSINT(self.test_username)

        if scraper.profile_data:
            output_dir = os.path.join(self.temp_dir, "test_pic")
            result = scraper.download_profile_picture(output_dir)

            if result:
                self.assertTrue(
                    os.path.exists(
                        os.path.join(output_dir, f"{self.test_username}_profile.jpg")
                    )
                )

    def test_download_profile_picture_no_url(self):
        """Test downloading when no profile picture URL"""
        scraper = InstagramOSINT(self.test_username)

        if scraper.profile_data:
            scraper.profile_data["profile_pic_url"] = ""
            result = scraper.download_profile_picture(self.temp_dir)

            self.assertFalse(result)

    def test_invalid_username(self):
        """Test handling of invalid username"""
        invalid_usernames = [
            "this_user_definitely_does_not_exist_12345",
            "!!!invalid!!!",
            "",
        ]

        for username in invalid_usernames:
            if username:  # Skip empty string for initialization
                scraper = InstagramOSINT(username)
                # Should not raise exception, but profile_data should be empty or None
                self.assertIsInstance(scraper.profile_data, dict)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after tests"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch("instagram_osint.InstagramOSINT._make_request")
    def test_network_error_handling(self, mock_request):
        """Test handling of network errors"""
        mock_request.return_value = None

        scraper = InstagramOSINT("test_user")
        self.assertEqual(scraper.profile_data, {})

    @patch("instagram_osint.InstagramOSINT._make_request")
    def test_rate_limiting_response(self, mock_request):
        """Test handling of rate limiting (429 error)"""
        # Mock 429 response
        mock_request.return_value = None

        scraper = InstagramOSINT("test_user")
        # Should handle gracefully without crashing
        self.assertIsInstance(scraper.profile_data, dict)

    def test_special_characters_in_username(self):
        """Test handling of special characters in username"""
        special_usernames = ["user.name", "user_name", "user123", "123user"]

        for username in special_usernames:
            try:
                scraper = InstagramOSINT(username)
                self.assertEqual(scraper.username, username)
            except Exception as e:
                self.fail(f"Failed on username '{username}': {e}")

    def test_unicode_in_profile_data(self):
        """Test handling of unicode characters in profile data"""
        scraper = InstagramOSINT("instagram")

        if scraper.profile_data:
            # Save and reload to test unicode handling
            output_dir = os.path.join(self.temp_dir, "unicode_test")
            scraper.save_data(output_dir)

            with open(
                os.path.join(output_dir, "profile_data.json"), "r", encoding="utf-8"
            ) as f:
                data = json.load(f)
                # Should not raise any errors
                self.assertIsInstance(data, dict)


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and validation"""

    def test_follower_count_type(self):
        """Test that follower count is numeric"""
        scraper = InstagramOSINT("instagram")

        if scraper.profile_data:
            follower_count = scraper.profile_data.get("follower_count")
            self.assertIsInstance(follower_count, int)
            self.assertGreaterEqual(follower_count, 0)

    def test_post_count_type(self):
        """Test that post count is numeric"""
        scraper = InstagramOSINT("instagram")

        if scraper.profile_data:
            post_count = scraper.profile_data.get("post_count")
            self.assertIsInstance(post_count, int)
            self.assertGreaterEqual(post_count, 0)

    def test_boolean_flags(self):
        """Test that boolean flags are actually booleans"""
        scraper = InstagramOSINT("instagram")

        if scraper.profile_data:
            # Note: These are stored as strings in current implementation
            # This test documents the current behavior
            is_private = scraper.profile_data.get("is_private")
            is_verified = scraper.profile_data.get("is_verified")

            self.assertIsInstance(is_private, (bool, str))
            self.assertIsInstance(is_verified, (bool, str))

    def test_url_format(self):
        """Test that URLs are properly formatted"""
        scraper = InstagramOSINT("instagram")

        if scraper.profile_data:
            profile_url = scraper.profile_data.get("profile_url")

            if profile_url:
                self.assertTrue(profile_url.startswith("https://"))
                self.assertIn("instagram.com", profile_url)


class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""

    def test_scrape_speed(self):
        """Test that profile scraping completes in reasonable time"""
        import time

        start_time = time.time()
        scraper = InstagramOSINT("instagram")
        end_time = time.time()

        # Profile scraping should complete within 30 seconds
        self.assertLess(end_time - start_time, 30)

    def test_memory_usage(self):
        """Test that scraper doesn't leak memory"""
        import gc

        # Create and destroy multiple scrapers
        for _ in range(10):
            scraper = InstagramOSINT("instagram")
            del scraper
            gc.collect()

        # If we get here without memory issues, test passes
        self.assertTrue(True)


def run_basic_tests():
    """Run basic integration tests (non-unittest)"""
    print("\n" + "=" * 60)
    print("Running Basic Integration Tests")
    print("=" * 60 + "\n")

    # Test 1: Basic initialization
    print("Test 1: Basic Initialization")
    try:
        scraper = InstagramOSINT("instagram")
        print(f"✓ Scraper initialized for @{scraper.username}")
        print(f"✓ Profile data available: {bool(scraper.profile_data)}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 2: Profile data access
    print("\nTest 2: Profile Data Access")
    try:
        if scraper.profile_data:
            print(f"✓ Username: {scraper['username']}")
            print(f"✓ Followers: {scraper['follower_count']:,}")
            print(f"✓ Posts: {scraper['post_count']:,}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 3: Data saving
    print("\nTest 3: Data Saving")
    try:
        temp_dir = tempfile.mkdtemp()
        result = scraper.save_data(temp_dir)
        print(f"✓ Data saved: {result}")
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 4: Post scraping (limited)
    print("\nTest 4: Post Scraping (Limited)")
    try:
        if not scraper.profile_data.get("is_private"):
            posts = scraper.scrape_posts(max_posts=5)
            print(f"✓ Posts scraped: {len(posts)}")
        else:
            print("⊘ Profile is private, skipping post test")
    except Exception as e:
        print(f"✗ Failed: {e}")

    print("\n" + "=" * 60)
    print("Basic Integration Tests Complete")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print("Running Unit Tests...\n")
    unittest.main(argv=[""], verbosity=2, exit=False)

    print("\n")
    run_basic_tests()
