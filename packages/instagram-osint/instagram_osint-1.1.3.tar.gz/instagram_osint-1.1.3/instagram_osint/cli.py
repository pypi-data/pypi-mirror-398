"""
Instagram OSINT CLI Tool
Made by Junaid (https://abujuni.dev)
Version: 1.0.3
A powerful command-line interface for Instagram OSINT operations

Disclaimer:
This tool is intended for research and educational purposes only.
The user is solely responsible for how this tool is used.

The author does not encourage or support any illegal activity and is not responsible for misuse, damage, or legal consequences resulting from the use of this tool.
"""

import argparse
import sys
import os
from typing import Optional, List
from datetime import datetime

# Import the Instagram OSINT class
from .instagramOSINT import InstagramOSINT, colors

from . import __version__ as module_ver

__version__ = "1.0.3"


class CLIError(Exception):
    """Base exception for CLI errors"""

    pass


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
            "username",
            type=str,
            nargs="?",
            help="Instagram username to scrape (without @)",
        )

        basic_info = parser.add_argument_group("Basic")
        basic_info.add_argument(
            "-V",
            "--version",
            action="store_true",
            help="Display the current CLI version.",
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
        banner = rf"""
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

    def error(self, message: str, exit_code: int = 1):
        """Print error message and exit"""
        print(f"{colors.FAIL}[✗] Error: {message}{colors.ENDC}", file=sys.stderr)
        sys.exit(exit_code)

    def warning(self, message: str):
        """Print warning message"""
        print(f"{colors.WARNING}[!] Warning: {message}{colors.ENDC}")

    def success(self, message: str):
        """Print success message"""
        print(f"{colors.OKGREEN}[✓] {message}{colors.ENDC}")

    def info(self, message: str):
        """Print info message"""
        print(f"{colors.OKBLUE}[*] {message}{colors.ENDC}")

    def run(self):
        args = self.parser.parse_args()

        # Handle version flag
        if args.version:
            print(f"igosint version : {__version__}")
            print(f"Module version  : {module_ver}")
            sys.exit(0)

        # Validate username requirement
        if not args.username and not args.batch:
            self.parser.print_help()
            self.error("Username or --batch file is required")

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
        try:
            username = args.username.lstrip("@")

            if not username:
                raise CLIError("Invalid username provided")

            output_dir = args.output or username

            # Initialize scraper
            if not args.quiet:
                self.info(f"Processing: @{username}\n")

            try:
                self.scraper = InstagramOSINT(username)
            except Exception as e:
                raise CLIError(f"Failed to initialize scraper: {str(e)}")

            # Check if profile was scraped
            if not self.scraper.profile_data:
                raise CLIError(f"Failed to scrape profile for @{username}")

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
                try:
                    self.scraper.save_data(output_dir)
                except Exception as e:
                    self.warning(f"Failed to save profile data: {str(e)}")

            # Download profile picture
            if args.download_pic:
                try:
                    self.scraper.download_profile_picture(output_dir)
                except Exception as e:
                    self.warning(f"Failed to download profile picture: {str(e)}")

            # Handle posts
            if args.posts:
                self._handle_posts(args, output_dir)

            # JSON output mode
            if args.json_only:
                import json

                print(json.dumps(self.scraper.profile_data, indent=2))

            if not args.quiet:
                self.success(f"Operation completed for @{username}")
            print()

        except CLIError as e:
            self.error(str(e))
        except KeyboardInterrupt:
            self.warning("Operation cancelled by user")
            sys.exit(0)
        except Exception as e:
            self.error(f"Unexpected error: {str(e)}")

    def _handle_posts(self, args, output_dir):
        """Handle post scraping and related operations"""
        try:
            if self.scraper.profile_data.get("is_private"):
                self.warning("Profile is private - cannot scrape posts")
                return

            # Scrape posts
            try:
                posts = self.scraper.scrape_posts(max_posts=args.max_posts)
            except Exception as e:
                self.warning(f"Failed to scrape posts: {str(e)}")
                return

            if not posts:
                self.warning("No posts found")
                return

            # Save posts data
            if args.save_posts or args.all:
                try:
                    self.scraper.save_posts(posts, output_dir)
                except Exception as e:
                    self.warning(f"Failed to save posts data: {str(e)}")

            # Download post images
            if args.download_posts or args.all:
                try:
                    posts_dir = os.path.join(output_dir, "posts")
                    self.scraper.download_posts(posts, posts_dir)
                except Exception as e:
                    self.warning(f"Failed to download posts: {str(e)}")

            # Display statistics
            if args.stats:
                self._display_stats(posts)

        except Exception as e:
            self.warning(f"Error handling posts: {str(e)}")

    def _display_stats(self, posts):
        """Display engagement statistics"""
        if not posts:
            return

        try:
            total_likes = sum(p.get("likes", 0) for p in posts)
            total_comments = sum(p.get("comments", 0) for p in posts)
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
            follower_count = self.scraper.profile_data.get("follower_count", 0)
            if follower_count > 0:
                engagement_rate = ((avg_likes + avg_comments) / follower_count) * 100
                print(
                    f"{colors.OKGREEN}Engagement Rate:{colors.ENDC} {engagement_rate:.2f}%"
                )

            # Top posts
            top_liked = sorted(posts, key=lambda x: x.get("likes", 0), reverse=True)[:3]
            print(f"\n{colors.OKBLUE}Top 3 Most Liked Posts:{colors.ENDC}")
            for i, post in enumerate(top_liked, 1):
                print(
                    f"  {i}. {post.get('likes', 0):,} likes - {post.get('url', 'N/A')}"
                )

            print(f"{colors.HEADER}{'='*60}{colors.ENDC}")

        except Exception as e:
            self.warning(f"Failed to display statistics: {str(e)}")

    def _batch_mode(self, args):
        """Process multiple usernames from a file"""
        try:
            # Validate batch file
            if not os.path.exists(args.batch):
                raise CLIError(f"Batch file not found: {args.batch}")

            # Read usernames
            try:
                with open(args.batch, "r") as f:
                    usernames = [line.strip() for line in f if line.strip()]
            except PermissionError:
                raise CLIError(f"Permission denied reading file: {args.batch}")
            except Exception as e:
                raise CLIError(f"Failed to read batch file: {str(e)}")

            if not usernames:
                raise CLIError("Batch file is empty")

            total = len(usernames)
            self.info(f"Batch mode: Processing {total} username(s)\n")

            success_count = 0
            failed_usernames = []

            for i, username in enumerate(usernames, 1):
                print(f"{colors.HEADER}{'='*60}{colors.ENDC}")
                print(
                    f"{colors.BOLD}[{i}/{total}] Processing: @{username}{colors.ENDC}"
                )
                print(f"{colors.HEADER}{'='*60}{colors.ENDC}\n")

                # Create a copy of args with the current username
                current_args = argparse.Namespace(**vars(args))
                current_args.username = username
                current_args.batch = None

                try:
                    self._process_user(current_args)
                    success_count += 1
                except Exception as e:
                    self.warning(f"Failed to process @{username}: {str(e)}")
                    failed_usernames.append(username)
                    continue

                print()

            # Summary
            print(f"{colors.HEADER}{'='*60}{colors.ENDC}")
            self.success(
                f"Batch processing completed: {success_count}/{total} successful"
            )

            if failed_usernames:
                print(
                    f"{colors.WARNING}Failed usernames: {', '.join(failed_usernames)}{colors.ENDC}"
                )

            print(f"{colors.HEADER}{'='*60}{colors.ENDC}")

        except CLIError as e:
            self.error(str(e))
        except KeyboardInterrupt:
            self.warning("Batch processing cancelled by user")
            sys.exit(0)
        except Exception as e:
            self.error(f"Unexpected error in batch mode: {str(e)}")


def main():
    """Entry point for CLI"""
    cli = InstagramCLI()
    cli.run()


if __name__ == "__main__":
    main()
