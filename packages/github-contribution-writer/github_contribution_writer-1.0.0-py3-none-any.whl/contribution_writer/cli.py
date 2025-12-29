#!/usr/bin/env python3
"""
GitHub Contribution Graph Word Writer

Generate backdated git commits to draw words on your GitHub contribution graph.
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta

from contribution_writer.font import (
    CHAR_SPACING,
    CHAR_WIDTH,
    FONT,
    print_grid,
    word_to_grid,
)


def get_year_start_sunday(year: int) -> datetime:
    """Get the first Sunday of the year (or last Sunday of previous year if Jan 1 isn't Sunday)."""
    jan1 = datetime(year, 1, 1)
    # GitHub graph starts on Sunday, so find the Sunday of the week containing Jan 1
    days_since_sunday = (
        jan1.weekday() + 1
    )  # Monday=0, so Sunday=6, but we want Sunday=0
    if jan1.weekday() == 6:  # If Jan 1 is Sunday
        days_since_sunday = 0
    return jan1 - timedelta(days=days_since_sunday)


def calculate_center_offset(word_width: int) -> int:
    """Calculate the week offset to center the word in the year."""
    # A year has ~52-53 weeks
    weeks_in_year = 52
    center_offset = (weeks_in_year - word_width) // 2
    return max(0, center_offset)


def grid_to_dates(
    grid: list[list[int]], year: int, center: bool = True
) -> dict[datetime, int]:
    """
    Convert a pixel grid to a dictionary of dates and commit counts.

    Args:
        grid: 7-row grid where each column is a week
        year: The year to generate commits for
        center: Whether to center the word in the year

    Returns:
        Dictionary mapping dates to number of commits needed
    """
    dates = {}
    word_width = len(grid[0])  # Number of columns (weeks)

    # Get starting Sunday
    start_sunday = get_year_start_sunday(year)

    # Calculate offset for centering
    if center:
        week_offset = calculate_center_offset(word_width)
    else:
        week_offset = 0

    # Map each pixel to a date
    for col in range(word_width):
        for row in range(7):  # 7 days in a week
            if grid[row][col]:
                # Calculate the date
                # row 0 = Sunday, row 1 = Monday, ..., row 6 = Saturday
                date = start_sunday + timedelta(weeks=week_offset + col, days=row)

                # Only include dates within the target year
                if date.year == year:
                    # Intensity: use varying commit counts for darker squares
                    dates[date] = (
                        grid[row][col] * 5
                    )  # 5 commits per pixel for good visibility

    return dates


def preview_commits(dates: dict[datetime, int], word: str) -> None:
    """Print a preview of what commits will be generated."""
    print(f"\n Preview for '{word.upper()}':")
    print("=" * 50)

    if not dates:
        print("No commits to generate (word may not fit in the year)")
        return

    sorted_dates = sorted(dates.keys())
    start_date = sorted_dates[0].strftime("%Y-%m-%d")
    end_date = sorted_dates[-1].strftime("%Y-%m-%d")
    print(f" Date range: {start_date} to {end_date}")
    print(f" Total commits: {sum(dates.values())}")
    print(f" Days with commits: {len(dates)}")

    print("\n Visual preview:")
    grid = word_to_grid(word)
    print_grid(grid)


def init_git_repo(path: str) -> None:
    """Initialize a git repo if it doesn't exist."""
    git_dir = os.path.join(path, ".git")
    if not os.path.exists(git_dir):
        subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
        print(" Initialized new git repository")


def generate_commits(
    dates: dict[datetime, int], path: str, dry_run: bool = False
) -> None:
    """Generate git commits for each date."""
    if dry_run:
        print("\n DRY RUN - No commits will be created")
        return

    # Initialize repo if needed
    init_git_repo(path)

    # File to modify for commits
    contrib_file = os.path.join(path, "contributions.txt")

    total_commits = sum(dates.values())
    commit_count = 0

    print(f"\n Generating {total_commits} commits...")

    for date in sorted(dates.keys()):
        num_commits = dates[date]
        date_str = date.strftime("%Y-%m-%d 12:00:00")

        for i in range(num_commits):
            commit_count += 1

            # Append to file
            with open(contrib_file, "a", encoding="utf-8") as f:
                f.write(f"Contribution: {date.strftime('%Y-%m-%d')} #{i + 1}\n")

            # Stage the file
            subprocess.run(
                ["git", "add", "contributions.txt"],
                cwd=path,
                check=True,
                capture_output=True,
            )

            # Create commit with backdated timestamp
            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = date_str
            env["GIT_COMMITTER_DATE"] = date_str

            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"Contribution {date.strftime('%Y-%m-%d')} #{i + 1}",
                ],
                cwd=path,
                check=True,
                capture_output=True,
                env=env,
            )

            # Progress indicator
            if commit_count % 10 == 0 or commit_count == total_commits:
                pct = int(commit_count / total_commits * 100)
                print(f"  Progress: {commit_count}/{total_commits} ({pct}%)", end="\r")

    print(f"\n Created {total_commits} commits!")
    print("\n Next steps:")
    print("  1. Create a new repo on GitHub (e.g., 'contribution-art')")
    print(
        "  2. Run: git remote add origin git@github.com:YOUR_USERNAME/contribution-art.git"
    )
    print("  3. Run: git branch -M main")
    print("  4. Run: git push -u origin main")


def validate_word(word: str) -> bool:
    """Validate that the word can be rendered."""
    word = word.upper()
    max_weeks = 52
    word_width = len(word) * (CHAR_WIDTH + CHAR_SPACING) - CHAR_SPACING

    if word_width > max_weeks:
        print(
            f" Error: '{word}' is too long ({word_width} weeks needed, max {max_weeks})"
        )
        print("   Maximum ~8 characters recommended")
        return False

    for char in word:
        if char not in FONT:
            print(f" Error: Character '{char}' is not supported")
            print("   Supported: A-Z, 0-9, space")
            return False

    return True


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Draw words on your GitHub contribution graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  contribution-writer "HELLO" --year 2025 --dry-run
  contribution-writer "DINESH" --year 2025
  contribution-writer "2025" --year 2025 --no-center
        """,
    )
    parser.add_argument("word", help="The word to draw (A-Z, 0-9, max ~8 chars)")
    parser.add_argument(
        "--year", type=int, default=2025, help="Target year (default: 2025)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without creating commits"
    )
    parser.add_argument(
        "--no-center",
        action="store_true",
        help="Start from beginning of year instead of centering",
    )
    parser.add_argument(
        "--intensity",
        type=int,
        default=5,
        choices=range(1, 11),
        help="Commits per pixel for intensity (1-10, default: 5)",
    )

    args = parser.parse_args()

    # Validate
    if not validate_word(args.word):
        sys.exit(1)

    # Generate grid
    grid = word_to_grid(args.word)

    # Scale intensity
    if args.intensity != 5:
        for row_idx, row in enumerate(grid):
            for col_idx, cell in enumerate(row):
                if cell:
                    grid[row_idx][col_idx] = 1  # Keep as 1, will multiply in grid_to_dates

    # Calculate dates
    dates = grid_to_dates(grid, args.year, center=not args.no_center)

    # Adjust intensity
    if args.intensity != 5:
        dates = {date: count // 5 * args.intensity for date, count in dates.items()}

    # Preview
    preview_commits(dates, args.word)

    # Generate
    if not args.dry_run:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        generate_commits(dates, script_dir, dry_run=args.dry_run)
    else:
        print("\n Remove --dry-run to generate commits")


if __name__ == "__main__":
    main()
