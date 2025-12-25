"""
Instagram OSINT CLI Tool
Made by Junaid (https://abujuni.dev)
Version: 1.0
A powerful command-line interface for Instagram OSINT operations

Disclaimer:
This tool is intended for research and educational purposes only.
The user is solely responsible for how this tool is used.

The author does not encourage or support any illegal activity and is not responsible for misuse, damage, or legal consequences resulting from the use of this tool.
"""

import argparse
import sys
import os
from typing import Optional
from datetime import datetime

# Import the Instagram OSINT class
from .instagramOSINT import InstagramOSINT, colors

from . import __version__ as module_ver

__version__ = "1.0.2"

class InstagramCLI:
    """Command-line interface for Instagram OSINT operations"""

    def __init__(self):
        self.parser = self._create_parser()
        self.scraper = None

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with all CLI options"""
        parser = argparse.ArgumentParser(
            prog="instagram-osint",
            description="Instagram OSINT Tool - Profile and post scraping utility",
            epilog="Created by Junaid (abujuni.dev)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # Required arguments
        parser.add_argument(
            "username", type=str, help="Instagram username to scrape (without @)"
        )

        # Profile options
        profile_group = parser.add_argument_group("Profile Options")
        profile_group.add_argument(
            "-p",
            "--profile",
            action="store_true",
            help="Display profile information (default behavior)",
        )
        profile_group.add_argument(
            "-s", "--save", action="store_true", help="Save profile data to JSON file"
        )
        profile_group.add_argument(
            "-d",
            "--download-pic",
            action="store_true",
            help="Download profile picture",
        )

        # Post options
        post_group = parser.add_argument_group("Post Options")
        post_group.add_argument(
            "-P",
            "--posts",
            action="store_true",
            help="Scrape posts from the profile",
        )
        post_group.add_argument(
            "-m",
            "--max-posts",
            type=int,
            metavar="N",
            help="Maximum number of posts to scrape (default: all)",
        )
        post_group.add_argument(
            "-D",
            "--download-posts",
            action="store_true",
            help="Download post images (requires -P/--posts)",
        )
        post_group.add_argument(
            "--save-posts", action="store_true", help="Save posts data to JSON file"
        )

        # Output options
        output_group = parser.add_argument_group("Output Options")
        output_group.add_argument(
            "-o",
            "--output",
            type=str,
            metavar="DIR",
            help="Output directory (default: username)",
        )
        output_group.add_argument(
            "-q", "--quiet", action="store_true", help="Quiet mode (minimal output)"
        )
        output_group.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Verbose mode (detailed output)",
        )
        output_group.add_argument(
            "--json-only",
            action="store_true",
            help="Output only JSON data (no formatted text)",
        )

        # Advanced options
        advanced_group = parser.add_argument_group("Advanced Options")
        advanced_group.add_argument(
            "-a",
            "--all",
            action="store_true",
            help="Perform all operations (profile + posts + downloads)",
        )
        advanced_group.add_argument(
            "--stats",
            action="store_true",
            help="Display engagement statistics (requires -P/--posts)",
        )
        advanced_group.add_argument(
            "--batch",
            type=str,
            metavar="FILE",
            help="Batch mode: scrape multiple usernames from file (one per line)",
        )

        return parser

    def print_banner(self):
        """Print CLI banner"""
        banner = fr"""
{colors.HEADER}
>>===========================================================================================================<<
||                                                                                                           ||
||     __  .__   __.      _______.___________.    ___       _______ .______          ___      .___  ___.     ||
||    |  | |  \ |  |     /       |           |   /   \     /  _____||   _  \        /   \     |   \/   |     ||
||    |  | |   \|  |    |   (----`---|  |----`  /  ^  \   |  |  __  |  |_)  |      /  ^  \    |  \  /  |     ||
||    |  | |  . `  |     \   \       |  |      /  /_\  \  |  | |_ | |      /      /  /_\  \   |  |\/|  |     ||
||    |  | |  |\   | .----)   |      |  |     /  _____  \ |  |__| | |  |\  \----./  _____  \  |  |  |  |     ||
||    |__| |__| \__| |_______/       |__|    /__/     \__\ \______| | _| `._____/__/     \__\ |__|  |__|     ||
||                                                                                                           ||
||      ______        _______. __  .__   __. .___________.   .___________.  ______     ______    __          ||
||     /  __  \      /       ||  | |  \ |  | |           |   |           | /  __  \   /  __  \  |  |         ||
||    |  |  |  |    |   (----`|  | |   \|  | `---|  |----`   `---|  |----`|  |  |  | |  |  |  | |  |         ||
||    |  |  |  |     \   \    |  | |  . `  |     |  |            |  |     |  |  |  | |  |  |  | |  |         ||
||    |  `--'  | .----)   |   |  | |  |\   |     |  |            |  |     |  `--'  | |  `--'  | |  `----.    ||
||     \______/  |_______/    |__| |__| \__|     |__|            |__|      \______/   \______/  |_______|    ||
||                                                                                                           ||
>>===========================================================================================================<<

Version      : {module_ver}
CLI Version  : {__version__}
Author       : Junaid(abujuni.dev)
{colors.ENDC}
"""
        print(banner)

    def run(self):
        args = self.parser.parse_args()

        # Print banner unless quiet mode
        if not args.quiet and not args.json_only:
            self.print_banner()

        # Handle batch mode
        if args.batch:
            self._batch_mode(args)
            return

        # Single user mode
        self._process_user(args)

    def _process_user(self, args):
        """Process a single username"""
        username = args.username.lstrip("@")
        output_dir = args.output or username

        # Initialize scraper
        if not args.quiet:
            print(f"{colors.OKBLUE}[*] Processing: @{username}{colors.ENDC}\n")

        self.scraper = InstagramOSINT(username)

        # Check if profile was scraped
        if not self.scraper.profile_data:
            print(
                f"{colors.FAIL}[✗] Failed to scrape profile for @{username}{colors.ENDC}"
            )
            sys.exit(1)

        # Display profile (unless json-only mode)
        if not args.json_only:
            self.scraper.print_profile_data()

        # Handle --all flag
        if args.all:
            args.save = True
            args.download_pic = True
            args.posts = True
            args.save_posts = True
            args.download_posts = True

        # Save profile data
        if args.save:
            self.scraper.save_data(output_dir)

        # Download profile picture
        if args.download_pic:
            self.scraper.download_profile_picture(output_dir)

        # Handle posts
        if args.posts:
            self._handle_posts(args, output_dir)

        # JSON output mode
        if args.json_only:
            import json

            print(json.dumps(self.scraper.profile_data, indent=2))

        if not args.quiet:
            print(
                f"\n{colors.OKGREEN}[✓] Operation completed for @{username}{colors.ENDC}"
            )
        print()

    def _handle_posts(self, args, output_dir):
        """Handle post scraping and related operations"""
        if self.scraper.profile_data.get("is_private"):
            print(
                f"{colors.WARNING}[!] Profile is private - cannot scrape posts{colors.ENDC}"
            )
            return

        # Scrape posts
        posts = self.scraper.scrape_posts(max_posts=args.max_posts)

        if not posts:
            print(f"{colors.WARNING}[!] No posts found{colors.ENDC}")
            return

        # Save posts data
        if args.save_posts or args.all:
            self.scraper.save_posts(posts, output_dir)

        # Download post images
        if args.download_posts or args.all:
            posts_dir = os.path.join(output_dir, "posts")
            self.scraper.download_posts(posts, posts_dir)

        # Display statistics
        if args.stats:
            self._display_stats(posts)

    def _display_stats(self, posts):
        """Display engagement statistics"""
        if not posts:
            return

        total_likes = sum(p["likes"] for p in posts)
        total_comments = sum(p["comments"] for p in posts)
        avg_likes = total_likes / len(posts)
        avg_comments = total_comments / len(posts)

        print(f"\n{colors.HEADER}{'='*60}{colors.ENDC}")
        print(f"{colors.BOLD}Engagement Statistics:{colors.ENDC}")
        print(f"{colors.HEADER}{'='*60}{colors.ENDC}")
        print(f"{colors.OKGREEN}Posts Analyzed:{colors.ENDC} {len(posts)}")
        print(f"{colors.OKGREEN}Total Likes:{colors.ENDC} {total_likes:,}")
        print(f"{colors.OKGREEN}Total Comments:{colors.ENDC} {total_comments:,}")
        print(f"{colors.OKGREEN}Average Likes:{colors.ENDC} {avg_likes:,.0f}")
        print(f"{colors.OKGREEN}Average Comments:{colors.ENDC} {avg_comments:,.0f}")

        # Engagement rate
        if self.scraper.profile_data.get("follower_count", 0) > 0:
            engagement_rate = (
                (avg_likes + avg_comments) / self.scraper.profile_data["follower_count"]
            ) * 100
            print(
                f"{colors.OKGREEN}Engagement Rate:{colors.ENDC} {engagement_rate:.2f}%"
            )

        # Top posts
        top_liked = sorted(posts, key=lambda x: x["likes"], reverse=True)[:3]
        print(f"\n{colors.OKBLUE}Top 3 Most Liked Posts:{colors.ENDC}")
        for i, post in enumerate(top_liked, 1):
            print(f"  {i}. {post['likes']:,} likes - {post['url']}")

        print(f"{colors.HEADER}{'='*60}{colors.ENDC}")

    def _batch_mode(self, args):
        """Process multiple usernames from a file"""
        try:
            with open(args.batch, "r") as f:
                usernames = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"{colors.FAIL}[✗] File not found: {args.batch}{colors.ENDC}")
            sys.exit(1)

        total = len(usernames)
        print(
            f"{colors.OKBLUE}[*] Batch mode: Processing {total} username(s){colors.ENDC}\n"
        )

        for i, username in enumerate(usernames, 1):
            print(f"{colors.HEADER}{'='*60}{colors.ENDC}")
            print(f"{colors.BOLD}[{i}/{total}] Processing: @{username}{colors.ENDC}")
            print(f"{colors.HEADER}{'='*60}{colors.ENDC}\n")

            # Create a copy of args with the current username
            current_args = argparse.Namespace(**vars(args))
            current_args.username = username
            current_args.batch = None  # Prevent recursion

            try:
                self._process_user(current_args)
            except Exception as e:
                print(
                    f"{colors.FAIL}[✗] Error processing @{username}: {e}{colors.ENDC}"
                )
                continue

            print()  # Blank line between users

        print(
            f"{colors.OKGREEN}[✓] Batch processing completed: {total} username(s){colors.ENDC}"
        )


def main():
    """Entry point for CLI"""
    try:
        cli = InstagramCLI()
        cli.run()
    except KeyboardInterrupt:
        print(f"\n{colors.WARNING}[!] Operation cancelled by user{colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"{colors.FAIL}[✗] Unexpected error: {e}{colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
