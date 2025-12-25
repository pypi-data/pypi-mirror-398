"""
Instagram OSINT Tool
A powerful Instagram scraping and OSINT utility

Made by Junaid (https://abujuni.dev)
Version: 1.1.2

Original Script by sc1341 (https://0xd33r.com)

Updates:
- Uses Instagram's internal REST and GraphQL APIs for reliable data extraction.
"""

# ---------------------------------------------------------------------------------
# Disclaimer:
# This tool is intended for research and educational purposes only.
# The user is solely responsible for how this tool is used.

# The author does not encourage or support any illegal activity and is not responsible for misuse, damage, or legal consequences resulting from the use of this tool.
# ---------------------------------------------------------------------------------


import json
import os
import requests
import random
import string
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode


__name__ = "Instagram OSINT Tool"


class colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class InstagramOSINT:
    # Modern Instagram API endpoints (2025)
    PROFILE_API = "https://i.instagram.com/api/v1/users/web_profile_info/"
    GRAPHQL_API = "https://www.instagram.com/graphql/query/"

    # Fixed query_id for post pagination (stable as of 2025)
    POST_QUERY_ID = "17888483320059182"

    # Required header for API access
    IG_APP_ID = "936619743392459"

    def __init__(self, username: str):
        self.username = username
        self.profile_data = {}
        self.user_id = None

        # Modern user agents (2024-2025)
        self.useragents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        ]

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": random.choice(self.useragents),
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "X-Requested-With": "XMLHttpRequest",
                "X-IG-App-ID": self.IG_APP_ID,
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
            }
        )

        self.scrape_profile()

    def __repr__(self):
        return f"InstagramOSINT(username='{self.username}')"

    def __str__(self):
        return f"Current Username: {self.username}"

    def __getitem__(self, key):
        return self.profile_data[key]

    def _make_request(
        self, url: str, params: Optional[Dict] = None, max_retries: int = 3
    ) -> Optional[Dict]:
        """
        Make HTTP request with retry logic and rate limit handling
        """
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=15)

                # Handle rate limiting with exponential backoff
                if response.status_code == 429:
                    wait_time = (2**attempt) * 5  # 5, 10, 20 seconds
                    print(
                        colors.WARNING
                        + f"Rate limited. Waiting {wait_time}s before retry..."
                        + colors.ENDC
                    )
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    print(
                        colors.FAIL
                        + f"Request failed after {max_retries} attempts: {e}"
                        + colors.ENDC
                    )
                    return None
                time.sleep(2**attempt)

        return None

    def scrape_profile(self) -> Optional[Dict[str, Any]]:
        """
        Scrape profile using modern Instagram REST API endpoint
        Returns profile data dictionary or None on failure
        """
        print(colors.OKBLUE + f"[*] Fetching profile: {self.username}" + colors.ENDC)

        params = {"username": self.username}
        data = self._make_request(self.PROFILE_API, params)

        if not data or "data" not in data:
            print(
                colors.FAIL
                + f"Username '{self.username}' not found or profile is private"
                + colors.ENDC
            )
            return None

        try:
            user = data["data"]["user"]
            self.user_id = user["id"]

            # Extract profile data
            self.profile_data = {
                "username": user.get("username", "N/A"),
                "full_name": user.get("full_name", "N/A"),
                "biography": user.get("biography", ""),
                "external_url": user.get("external_url", ""),
                "profile_pic_url": user.get(
                    "profile_pic_url_hd", user.get("profile_pic_url", "")
                ),
                "is_private": user.get("is_private", True),
                "is_verified": user.get("is_verified", False),
                "is_business": user.get("is_business_account", False),
                "business_category": user.get("business_category_name", ""),
                "follower_count": user.get("edge_followed_by", {}).get("count", 0),
                "following_count": user.get("edge_follow", {}).get("count", 0),
                "post_count": user.get("edge_owner_to_timeline_media", {}).get(
                    "count", 0
                ),
                "user_id": self.user_id,
                "profile_url": f"https://www.instagram.com/{self.username}/",
            }

            print(colors.OKGREEN + f"[✓] Profile scraped successfully!" + colors.ENDC)
            return self.profile_data

        except (KeyError, TypeError) as e:
            print(colors.FAIL + f"Error parsing profile data: {e}" + colors.ENDC)
            return None

    def scrape_posts(self, max_posts: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape posts using Instagram's GraphQL API with pagination

        Args:
            max_posts: Maximum number of posts to scrape (None = all posts)

        Returns:
            List of post dictionaries
        """
        if not self.user_id:
            print(colors.FAIL + "[!] Profile must be scraped first" + colors.ENDC)
            return []

        if self.profile_data.get("is_private"):
            print(
                colors.WARNING
                + "[!] Cannot scrape posts from private profile"
                + colors.ENDC
            )
            return []

        posts = []
        end_cursor = None
        has_next = True
        page = 1

        print(colors.OKBLUE + f"[*] Scraping posts..." + colors.ENDC)

        while has_next:
            # Build GraphQL query parameters
            variables = {
                "id": self.user_id,
                "first": 24,  # Posts per page (Instagram default)
            }

            if end_cursor:
                variables["after"] = end_cursor

            params = {"query_id": self.POST_QUERY_ID, **variables}

            # Rate limiting: wait between requests
            if page > 1:
                wait_time = random.uniform(2, 5)
                time.sleep(wait_time)

            data = self._make_request(self.GRAPHQL_API, params)

            if not data or "data" not in data:
                print(
                    colors.WARNING + f"[!] No more posts or rate limited" + colors.ENDC
                )
                break

            try:
                timeline = data["data"]["user"]["edge_owner_to_timeline_media"]
                edges = timeline.get("edges", [])
                page_info = timeline.get("page_info", {})

                for edge in edges:
                    node = edge.get("node", {})

                    # Extract post data
                    post = {
                        "id": node.get("id"),
                        "shortcode": node.get("shortcode"),
                        "url": f"https://www.instagram.com/p/{node.get('shortcode')}/",
                        "display_url": node.get("display_url"),
                        "is_video": node.get("is_video", False),
                        "caption": self._extract_caption(node),
                        "timestamp": node.get("taken_at_timestamp"),
                        "likes": node.get("edge_liked_by", {}).get("count", 0),
                        "comments": node.get("edge_media_to_comment", {}).get(
                            "count", 0
                        ),
                        "location": (
                            node.get("location", {}).get("name")
                            if node.get("location")
                            else None
                        ),
                        "accessibility_caption": node.get("accessibility_caption", ""),
                    }

                    posts.append(post)

                    # Check max_posts limit
                    if max_posts and len(posts) >= max_posts:
                        has_next = False
                        break

                # Pagination
                has_next = has_next and page_info.get("has_next_page", False)
                end_cursor = page_info.get("end_cursor")

                print(
                    colors.OKGREEN
                    + f"[✓] Page {page}: Scraped {len(edges)} posts (Total: {len(posts)})"
                    + colors.ENDC
                )
                page += 1

            except (KeyError, TypeError) as e:
                print(colors.FAIL + f"Error parsing posts: {e}" + colors.ENDC)
                break

        print(colors.OKGREEN + f"[✓] Total posts scraped: {len(posts)}" + colors.ENDC)
        return posts

    def _extract_caption(self, node: Dict) -> str:
        """Extract caption text from post node"""
        try:
            edges = node.get("edge_media_to_caption", {}).get("edges", [])
            if edges:
                return edges[0].get("node", {}).get("text", "")
        except (KeyError, IndexError, TypeError):
            pass
        return ""

    def download_profile_picture(self, output_dir: str = ".") -> bool:
        """
        Download profile picture to specified directory

        Args:
            output_dir: Directory to save profile picture

        Returns:
            True if successful, False otherwise
        """
        if not self.profile_data.get("profile_pic_url"):
            print(colors.WARNING + "[!] No profile picture URL available" + colors.ENDC)
            return False

        try:
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.join(output_dir, f"{self.username}_profile.jpg")

            response = self.session.get(
                self.profile_data["profile_pic_url"], timeout=10
            )
            response.raise_for_status()

            with open(filename, "wb") as f:
                f.write(response.content)

            print(
                colors.OKGREEN + f"[✓] Profile picture saved: {filename}" + colors.ENDC
            )
            return True

        except Exception as e:
            print(
                colors.FAIL + f"Failed to download profile picture: {e}" + colors.ENDC
            )
            return False

    def download_posts(self, posts: List[Dict], output_dir: str = "posts") -> int:
        """
        Download post images to directory

        Args:
            posts: List of post dictionaries from scrape_posts()
            output_dir: Directory to save images

        Returns:
            Number of successfully downloaded images
        """
        os.makedirs(output_dir, exist_ok=True)
        downloaded = 0

        print(
            colors.OKBLUE + f"[*] Downloading {len(posts)} post images..." + colors.ENDC
        )

        for i, post in enumerate(posts, 1):
            try:
                if not post.get("display_url"):
                    continue

                filename = os.path.join(output_dir, f"{post['shortcode']}.jpg")

                # Rate limiting
                time.sleep(random.uniform(1, 3))

                response = self.session.get(post["display_url"], timeout=10)
                response.raise_for_status()

                with open(filename, "wb") as f:
                    f.write(response.content)

                downloaded += 1

                if i % 10 == 0:
                    print(
                        colors.OKGREEN
                        + f"[✓] Downloaded {i}/{len(posts)} images"
                        + colors.ENDC
                    )

            except Exception as e:
                print(
                    colors.WARNING
                    + f"[!] Failed to download post {post.get('shortcode')}: {e}"
                    + colors.ENDC
                )
                continue

        print(
            colors.OKGREEN
            + f"[✓] Downloaded {downloaded}/{len(posts)} images to {output_dir}/"
            + colors.ENDC
        )
        return downloaded

    def save_data(self, output_dir: Optional[str] = None) -> bool:
        """
        Save profile data to JSON file

        Args:
            output_dir: Directory to save data (default: username)

        Returns:
            True if successful
        """
        if not self.profile_data:
            print(colors.WARNING + "[!] No profile data to save" + colors.ENDC)
            return False

        if output_dir is None:
            output_dir = self.username

        try:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, "profile_data.json")

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.profile_data, f, indent=2, ensure_ascii=False)

            print(colors.OKGREEN + f"[✓] Profile data saved: {filepath}" + colors.ENDC)
            return True

        except Exception as e:
            print(colors.FAIL + f"Failed to save profile data: {e}" + colors.ENDC)
            return False

    def save_posts(self, posts: List[Dict], output_dir: Optional[str] = None) -> bool:
        """
        Save posts data to JSON file

        Args:
            posts: List of post dictionaries
            output_dir: Directory to save data (default: username)

        Returns:
            True if successful
        """
        if not posts:
            print(colors.WARNING + "[!] No posts to save" + colors.ENDC)
            return False

        if output_dir is None:
            output_dir = self.username

        try:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, "posts_data.json")

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(posts, f, indent=2, ensure_ascii=False)

            print(colors.OKGREEN + f"[✓] Posts data saved: {filepath}" + colors.ENDC)
            return True

        except Exception as e:
            print(colors.FAIL + f"Failed to save posts data: {e}" + colors.ENDC)
            return False

    def print_profile_data(self):
        """Print profile data to console in readable format"""
        if not self.profile_data:
            print(colors.WARNING + "[!] No profile data available" + colors.ENDC)
            return

        print(colors.HEADER + "=" * 60 + colors.ENDC)
        print(
            colors.BOLD
            + colors.OKGREEN
            + f"Instagram Profile: @{self.username}"
            + colors.ENDC
        )
        print(colors.HEADER + "=" * 60 + colors.ENDC)

        for key, value in self.profile_data.items():
            if key not in ["profile_pic_url", "user_id"]:  # Skip long URLs
                print(
                    f"{colors.OKBLUE}{key.replace('_', ' ').title()}:{colors.ENDC} {value}"
                )

        print(colors.HEADER + "=" * 60 + colors.ENDC)
