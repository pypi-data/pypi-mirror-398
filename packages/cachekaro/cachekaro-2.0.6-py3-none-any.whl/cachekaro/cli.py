"""
Command-line interface for CacheKaro.

Provides analyze, clean, and report commands with various options.
"""

from __future__ import annotations

import argparse
import base64
import sys
from datetime import datetime

from cachekaro import __version__
from cachekaro.core.analyzer import Analyzer
from cachekaro.core.cleaner import Cleaner, CleanMode
from cachekaro.exporters import Exporter, TextExporter, get_exporter
from cachekaro.models.cache_item import CacheItem
from cachekaro.platforms import get_platform, get_platform_name
from cachekaro.platforms.base import Category, RiskLevel


# ANSI color codes - Purple/Dark theme
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    # Primary theme colors
    PURPLE = "\033[38;5;141m"       # Light purple
    DEEP_PURPLE = "\033[38;5;99m"   # Deep purple
    VIOLET = "\033[38;5;183m"       # Soft violet
    # Accent colors
    WHITE = "\033[38;5;255m"
    GRAY = "\033[38;5;245m"
    GREEN = "\033[38;5;114m"        # Soft green
    RED = "\033[38;5;204m"          # Soft red/pink
    YELLOW = "\033[38;5;221m"       # Soft yellow
    BLUE = "\033[38;5;111m"         # Soft blue
    CYAN = "\033[38;5;116m"         # Soft cyan
    MAGENTA = "\033[38;5;176m"      # Soft magenta


def color(text: str, c: str) -> str:
    """Apply color to text."""
    return f"{c}{text}{Colors.RESET}"


# Build metadata - do not modify
def _m(x: str) -> str:
    return base64.b64decode(x).decode()


_a = "TU9ISVQgQkFHUkk="  # Attribution identifier
_c = "SW5kaWE="  # Country identifier


def print_banner() -> None:
    """Print the CacheKaro banner."""
    _author = _m(_a)
    _country = _m(_c)
    banner = f"""
{Colors.PURPLE}{Colors.BOLD}░█████╗░░█████╗░░█████╗░██╗░░██╗███████╗██╗░░██╗░█████╗░██████╗░░█████╗░
██╔══██╗██╔══██╗██╔══██╗██║░░██║██╔════╝██║░██╔╝██╔══██╗██╔══██╗██╔══██╗
██║░░╚═╝███████║██║░░╚═╝███████║█████╗░░█████═╝░███████║██████╔╝██║░░██║
██║░░██╗██╔══██║██║░░██╗██╔══██║██╔══╝░░██╔═██╗░██╔══██║██╔══██╗██║░░██║
╚█████╔╝██║░░██║╚█████╔╝██║░░██║███████╗██║░╚██╗██║░░██║██║░░██║╚█████╔╝
░╚════╝░╚═╝░░╚═╝░╚════╝░╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░{Colors.RESET}

    {Colors.WHITE}{Colors.BOLD}Cross-Platform Storage & Cache Manager{Colors.RESET}
    {Colors.GRAY}Version {__version__} | {Colors.VIOLET}Clean It Up!{Colors.RESET}
    {Colors.GRAY}Made in{Colors.RESET} {Colors.WHITE}{Colors.BOLD}{_country}{Colors.RESET} {Colors.GRAY}with{Colors.RESET} {Colors.RED}♥{Colors.RESET}  {Colors.GRAY}by{Colors.RESET} {Colors.PURPLE}{Colors.BOLD}{_author}{Colors.RESET}
"""
    print(banner)


def progress_callback(name: str, current: int, total: int) -> None:
    """Display progress during scanning."""
    percent = (current / total) * 100
    bar_width = 30
    filled = int(bar_width * current / total)
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"\r{Colors.PURPLE}[{bar}] {percent:5.1f}%{Colors.RESET} {Colors.GRAY}- Scanning: {name[:40]:40s}{Colors.RESET}", end="", flush=True)
    if current == total:
        print()  # New line when done


def confirm_clean(item: CacheItem) -> bool:
    """Interactive confirmation for cleaning."""
    size_color = Colors.RED if item.size_bytes > 100 * 1024 * 1024 else Colors.YELLOW
    risk_color = {
        RiskLevel.SAFE: Colors.GREEN,
        RiskLevel.MODERATE: Colors.YELLOW,
        RiskLevel.CAUTION: Colors.RED,
    }.get(item.risk_level, Colors.RESET)

    print(f"\n{color(item.name, Colors.BOLD)}")
    print(f"  Path: {item.path}")
    print(f"  Size: {color(item.formatted_size, size_color)}")
    print(f"  Risk: {color(item.risk_level.value.upper(), risk_color)}")
    print(f"  Description: {item.description}")

    try:
        response = input(f"\n{color('Delete?', Colors.YELLOW)} [y/N/q(uit)]: ").strip().lower()
        if response == "q":
            print(f"\n{color('Cleaning cancelled.', Colors.YELLOW)}")
            sys.exit(0)
        return response == "y"
    except (KeyboardInterrupt, EOFError):
        print(f"\n{color('Cleaning cancelled.', Colors.YELLOW)}")
        sys.exit(0)


def clean_progress_callback(name: str, current: int, total: int, size_freed: int) -> None:
    """Display progress during cleaning."""
    size_str = format_size(size_freed)
    print(f"\r{Colors.PURPLE}[{current}/{total}]{Colors.RESET} {Colors.GREEN}Cleaned: {size_str:>12s}{Colors.RESET}", end="", flush=True)
    if current == total:
        print()


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable string."""
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    elif size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes} B"


def parse_size(size_str: str) -> int:
    """Parse size string (e.g., '100MB') to bytes."""
    size_str = size_str.strip().upper()

    multipliers = {
        "B": 1,
        "K": 1024,
        "KB": 1024,
        "M": 1024 * 1024,
        "MB": 1024 * 1024,
        "G": 1024 * 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
    }

    for suffix, multiplier in sorted(multipliers.items(), key=lambda x: -len(x[0])):
        if size_str.endswith(suffix):
            value = float(size_str[:-len(suffix)])
            return int(value * multiplier)

    # No suffix, assume bytes
    return int(float(size_str))


def cmd_analyze(args: argparse.Namespace) -> int:
    """Run the analyze command."""
    # Only print banner for text format and when not outputting to file
    show_ui = args.format == "text" and not args.output

    if show_ui:
        print_banner()
        platform = get_platform()
        print(f"{color('Platform:', Colors.WHITE)} {Colors.PURPLE}{platform.name}{Colors.RESET}")
        print(f"{color('Scanning cache locations...', Colors.GRAY)}\n")
    else:
        platform = get_platform()

    # Parse options
    categories = None
    if args.category and args.category != "all":
        try:
            categories = [Category(args.category)]
        except ValueError:
            print(f"{color('Error:', Colors.RED)} Invalid category: {args.category}")
            return 1

    max_risk = RiskLevel.CAUTION
    if args.safe_only:
        max_risk = RiskLevel.SAFE

    min_size = 0
    if args.min_size:
        try:
            min_size = parse_size(args.min_size)
        except ValueError:
            print(f"{color('Error:', Colors.RED)} Invalid size: {args.min_size}")
            return 1

    # Create analyzer
    analyzer = Analyzer(
        platform=platform,
        stale_threshold_days=args.stale_days,
        min_size_bytes=min_size,
        include_empty=args.include_empty,
        progress_callback=progress_callback if (show_ui and not args.quiet) else None,
    )

    # Run analysis
    result = analyzer.analyze(categories=categories, max_risk=max_risk)

    # Export result
    exporter: Exporter
    if args.format == "text":
        exporter = TextExporter(use_colors=not args.no_color)
        output = exporter.export(result)
        print(output)
    else:
        exporter = get_exporter(args.format)
        output = exporter.export(result)

        if args.output:
            output_path = exporter.export_to_file(result, args.output)
            print(f"\n{color('Report saved to:', Colors.GREEN)} {output_path}")
        else:
            print(output)

    return 0


def cmd_clean(args: argparse.Namespace) -> int:
    """Run the clean command."""
    print_banner()

    platform = get_platform()
    print(f"{color('Platform:', Colors.WHITE)} {Colors.PURPLE}{platform.name}{Colors.RESET}")

    # Determine cleaning mode
    if args.dry_run:
        mode = CleanMode.DRY_RUN
        print(f"{color('Mode:', Colors.WHITE)} {Colors.YELLOW}Dry Run{Colors.RESET} {Colors.GRAY}(no files will be deleted){Colors.RESET}\n")
    elif args.auto:
        mode = CleanMode.AUTO
        print(f"{color('Mode:', Colors.WHITE)} {Colors.RED}Auto{Colors.RESET} {Colors.GRAY}(all items will be cleaned without confirmation){Colors.RESET}")
        try:
            response = input(f"\n{color('Are you sure?', Colors.RED)} [y/N]: ").strip().lower()
            if response != "y":
                print("Cancelled.")
                return 0
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return 0
        print()
    else:
        mode = CleanMode.INTERACTIVE
        print(f"{color('Mode:', Colors.WHITE)} {Colors.PURPLE}Interactive{Colors.RESET} {Colors.GRAY}(confirm each item){Colors.RESET}\n")

    # Parse options
    max_risk = RiskLevel.SAFE
    if args.risk == "moderate":
        max_risk = RiskLevel.MODERATE
    elif args.risk == "caution":
        max_risk = RiskLevel.CAUTION

    categories = None
    if args.category and args.category != "all":
        try:
            categories = [Category(args.category)]
        except ValueError:
            print(f"{color('Error:', Colors.RED)} Invalid category: {args.category}")
            return 1

    min_size = 0
    if args.min_size:
        try:
            min_size = parse_size(args.min_size)
        except ValueError:
            print(f"{color('Error:', Colors.RED)} Invalid size: {args.min_size}")
            return 1

    # First, scan to find items
    print(f"{color('Scanning cache locations...', Colors.GRAY)}")
    analyzer = Analyzer(
        platform=platform,
        stale_threshold_days=args.stale_days,
        min_size_bytes=min_size,
        progress_callback=progress_callback,
    )

    result = analyzer.analyze(max_risk=max_risk)

    # Filter items
    items = result.items
    if categories:
        items = [item for item in items if item.category in categories]
    if args.stale_only:
        items = [item for item in items if item.is_stale]

    if not items:
        print(f"\n{color('No items to clean.', Colors.YELLOW)}")
        return 0

    print(f"\n{color(f'Found {len(items)} items to clean', Colors.WHITE)}")
    print(f"Total size: {color(format_size(sum(i.size_bytes for i in items)), Colors.PURPLE)}\n")

    # Create cleaner
    cleaner = Cleaner(
        mode=mode,
        backup_enabled=args.backup,
        max_risk=max_risk,
        confirm_callback=confirm_clean if mode == CleanMode.INTERACTIVE else None,
        progress_callback=clean_progress_callback if mode != CleanMode.INTERACTIVE else None,
    )

    # Clean
    summary = cleaner.clean(items)

    # Print summary
    print(f"\n{color('═' * 60, Colors.PURPLE)}")
    print(f"{color('CLEANING SUMMARY', Colors.WHITE)}")
    print(f"{color('═' * 60, Colors.PURPLE)}")

    if args.dry_run:
        print(f"\n{color('[DRY RUN]', Colors.YELLOW)} Would have freed: {color(summary.formatted_size_freed, Colors.GREEN)}")
        print(f"Items: {summary.items_cleaned}")
    else:
        print(f"\n{color('Space freed:', Colors.GREEN)} {color(summary.formatted_size_freed, Colors.BOLD)}")
        print(f"Items cleaned: {summary.items_cleaned}")
        print(f"Items skipped: {summary.items_skipped}")
        if summary.items_failed > 0:
            print(f"{color(f'Items failed: {summary.items_failed}', Colors.RED)}")

    print(f"Duration: {summary.duration_seconds:.2f} seconds\n")

    # Show current disk usage
    disk = platform.get_disk_usage()
    print(f"{color('Current disk status:', Colors.WHITE)}")
    print(f"  {Colors.GRAY}Used:{Colors.RESET} {format_size(disk.used_bytes)} ({disk.used_percent:.1f}%)")
    print(f"  {Colors.GRAY}Free:{Colors.RESET} {Colors.GREEN}{format_size(disk.free_bytes)}{Colors.RESET}")

    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Generate a detailed report."""
    print_banner()

    platform = get_platform()
    print(f"{color('Generating report...', Colors.GRAY)}\n")

    analyzer = Analyzer(
        platform=platform,
        progress_callback=progress_callback if not args.quiet else None,
    )

    result = analyzer.analyze()

    # Determine output format
    output_format = args.format or "html"
    exporter = get_exporter(output_format)

    # Generate output path if not specified
    output_path = args.output
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"cachekaro_report_{timestamp}.{exporter.file_extension}"

    # Export
    final_path = exporter.export_to_file(result, output_path)
    print(f"\n{color('Report saved to:', Colors.WHITE)} {Colors.PURPLE}{final_path}{Colors.RESET}")

    return 0


def cmd_version(args: argparse.Namespace) -> int:
    """Show version information."""
    print(f"CacheKaro version {__version__}")
    print(f"Platform: {get_platform_name()}")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Show system information."""
    print_banner()

    platform = get_platform()
    info = platform.get_platform_info()
    disk = platform.get_disk_usage()

    print(f"{color('System Information', Colors.WHITE)}")
    print(f"{Colors.PURPLE}{'═' * 40}{Colors.RESET}")
    print(f"{Colors.GRAY}Platform:{Colors.RESET} {Colors.PURPLE}{info.name}{Colors.RESET}")
    print(f"{Colors.GRAY}Version:{Colors.RESET} {info.version}")
    print(f"{Colors.GRAY}Architecture:{Colors.RESET} {info.architecture}")
    print(f"{Colors.GRAY}Hostname:{Colors.RESET} {info.hostname}")
    print(f"{Colors.GRAY}Username:{Colors.RESET} {info.username}")
    print(f"{Colors.GRAY}Home Directory:{Colors.RESET} {info.home_dir}")
    print()
    print(f"{color('Disk Usage', Colors.WHITE)}")
    print(f"{Colors.PURPLE}{'═' * 40}{Colors.RESET}")
    print(f"{Colors.GRAY}Total:{Colors.RESET} {format_size(disk.total_bytes)}")
    print(f"{Colors.GRAY}Used:{Colors.RESET} {format_size(disk.used_bytes)} ({disk.used_percent:.1f}%)")
    print(f"{Colors.GRAY}Free:{Colors.RESET} {Colors.GREEN}{format_size(disk.free_bytes)}{Colors.RESET}")
    print()
    print(f"{color('Cache Paths', Colors.WHITE)}")
    print(f"{Colors.PURPLE}{'═' * 40}{Colors.RESET}")
    existing = platform.get_existing_paths()
    print(f"{Colors.GRAY}Total defined:{Colors.RESET} {len(platform.get_cache_paths())}")
    print(f"{Colors.GRAY}Existing on system:{Colors.RESET} {Colors.PURPLE}{len(existing)}{Colors.RESET}")

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="cachekaro",
        description="CacheKaro - Cross-Platform Storage & Cache Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cachekaro analyze                  # Analyze storage usage
  cachekaro analyze --format json    # Output as JSON
  cachekaro analyze --category dev   # Only development caches
  cachekaro clean                    # Interactive cleaning
  cachekaro clean --dry-run          # Preview what would be cleaned
  cachekaro clean --auto             # Clean all without prompts
  cachekaro report                   # Generate HTML report
  cachekaro report --format csv      # Generate CSV report

For more information, visit: https://github.com/mohitbagri/cachekaro
        """,
    )

    parser.add_argument(
        "-V", "--version",
        action="store_true",
        help="Show version and exit",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze storage and cache usage",
        aliases=["scan", "check"],
    )
    analyze_parser.add_argument(
        "-f", "--format",
        choices=["text", "json", "csv", "html"],
        default="text",
        help="Output format (default: text)",
    )
    analyze_parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Save output to file",
    )
    analyze_parser.add_argument(
        "-c", "--category",
        choices=["all", "user_cache", "system_cache", "browser", "development", "logs", "trash", "downloads", "application"],
        default="all",
        help="Category to analyze (default: all)",
    )
    analyze_parser.add_argument(
        "--min-size",
        metavar="SIZE",
        help="Minimum size to show (e.g., 100MB)",
    )
    analyze_parser.add_argument(
        "--stale-days",
        type=int,
        default=30,
        metavar="DAYS",
        help="Days after which cache is considered stale (default: 30)",
    )
    analyze_parser.add_argument(
        "--safe-only",
        action="store_true",
        help="Only show safe-to-clean items",
    )
    analyze_parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Include empty cache locations",
    )
    analyze_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    analyze_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    analyze_parser.set_defaults(func=cmd_analyze)

    # clean command
    clean_parser = subparsers.add_parser(
        "clean",
        help="Clean cache and temporary files",
        aliases=["clear", "delete"],
    )
    clean_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be cleaned without deleting",
    )
    clean_parser.add_argument(
        "--auto",
        action="store_true",
        help="Clean all items without confirmation",
    )
    clean_parser.add_argument(
        "-c", "--category",
        choices=["all", "user_cache", "system_cache", "browser", "development", "logs", "trash", "downloads", "application"],
        default="all",
        help="Category to clean (default: all)",
    )
    clean_parser.add_argument(
        "--risk",
        choices=["safe", "moderate", "caution"],
        default="safe",
        help="Maximum risk level to clean (default: safe)",
    )
    clean_parser.add_argument(
        "--min-size",
        metavar="SIZE",
        help="Only clean items larger than SIZE (e.g., 50MB)",
    )
    clean_parser.add_argument(
        "--stale-only",
        action="store_true",
        help="Only clean stale items (not accessed recently)",
    )
    clean_parser.add_argument(
        "--stale-days",
        type=int,
        default=30,
        metavar="DAYS",
        help="Days after which cache is considered stale (default: 30)",
    )
    clean_parser.add_argument(
        "--backup",
        action="store_true",
        help="Backup before deleting",
    )
    clean_parser.set_defaults(func=cmd_clean)

    # report command
    report_parser = subparsers.add_parser(
        "report",
        help="Generate a detailed report",
    )
    report_parser.add_argument(
        "-f", "--format",
        choices=["text", "json", "csv", "html"],
        default="html",
        help="Report format (default: html)",
    )
    report_parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Output file path",
    )
    report_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    report_parser.set_defaults(func=cmd_report)

    # info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show system information",
    )
    info_parser.set_defaults(func=cmd_info)

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle version flag
    if args.version:
        return cmd_version(args)

    # Handle no command
    if not args.command:
        # Default to analyze
        args.command = "analyze"
        args.format = "text"
        args.output = None
        args.category = "all"
        args.min_size = None
        args.stale_days = 30
        args.safe_only = False
        args.include_empty = False
        args.no_color = False
        args.quiet = False
        return cmd_analyze(args)

    # Run the command
    try:
        result: int = args.func(args)
        return result
    except KeyboardInterrupt:
        print(f"\n{color('Interrupted.', Colors.YELLOW)}")
        return 130
    except Exception as e:
        print(f"\n{color('Error:', Colors.RED)} {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
