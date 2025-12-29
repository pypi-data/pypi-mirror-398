"""Main entry point for Claude Profile Switcher"""

import argparse
import subprocess
import sys
from pathlib import Path

from .claude_config import ClaudeConfigManager
from .profile_manager import ProfileManager
from .ui import tui_main


def cmd_switch(profile_name: str, profile_manager: ProfileManager, claude_config: ClaudeConfigManager) -> int:
    """Switch to a specific profile

    Args:
        profile_name: Name of profile to switch to
        profile_manager: Profile manager instance
        claude_config: Claude config manager instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    profile = profile_manager.get_profile(profile_name)

    if not profile:
        print(f"Error: Profile '{profile_name}' not found", file=sys.stderr)
        return 1

    # Check if profile is complete
    if not profile.is_complete():
        print(f"Error: Profile '{profile_name}' is incomplete. Please configure base_url and api_key.", file=sys.stderr)
        return 1

    try:
        claude_config.apply_profile(profile)
        print(f"Switched to profile: {profile_name}")
        return 0
    except Exception as e:
        print(f"Error applying profile: {e}", file=sys.stderr)
        return 1


def cmd_launch(profile_name: str, profile_manager: ProfileManager, claude_config: ClaudeConfigManager) -> int:
    """Switch to a specific profile and launch claude-code

    Args:
        profile_name: Name of profile to switch to
        profile_manager: Profile manager instance
        claude_config: Claude config manager instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # First switch the profile
    exit_code = cmd_switch(profile_name, profile_manager, claude_config)
    if exit_code != 0:
        return exit_code

    # Then launch claude-code
    try:
        print("Launching claude-code...")
        subprocess.run(["claude"], check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error launching claude-code: {e}", file=sys.stderr)
        return e.returncode
    except FileNotFoundError:
        print("Error: 'claude' command not found. Make sure Claude Code is installed.", file=sys.stderr)
        return 1


def cmd_list(profile_manager: ProfileManager, claude_config: ClaudeConfigManager) -> int:
    """List all profiles with their configurations

    Args:
        profile_manager: Profile manager instance
        claude_config: Claude config manager instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    profiles = profile_manager.load_profiles()
    current = claude_config.get_current_profile_display(profiles)

    if not profiles:
        print("No profiles configured.")
        return 0

    print(f"{'Profile':<20} {'Base URL':<30} {'Status':<10}")
    print("-" * 60)

    for p in profiles:
        base_url = p.base_url or "(not set)"
        if len(base_url) > 28:
            base_url = base_url[:25] + "..."
        status = "✓ complete" if p.is_complete() else "✗ incomplete"
        active = " *" if p.name == current else ""
        print(f"{p.name:<20} {base_url:<30} {status}{active}")

    print(f"\nCurrent profile: {current}")
    return 0


def run_tui(profile_manager: ProfileManager, claude_config: ClaudeConfigManager) -> int:
    """Run the TUI interface

    Args:
        profile_manager: Profile manager instance
        claude_config: Claude config manager instance

    Returns:
        Exit code
    """
    try:
        profiles = profile_manager.load_profiles()
        selected_profile = tui_main(profiles, claude_config, profile_manager)

        if selected_profile:
            print(f"\nSwitched to: {selected_profile.name}")
        else:
            print("\nNo profile selected")

        return 0
    except Exception as e:
        print(f"Error running application: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Claude Code profile switcher - Manage API provider configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-profile                    Launch TUI interface
  claude-profile switch my-profile  Switch to 'my-profile'
  claude-profile s my-profile       Switch to 'my-profile' (short form)
  claude-profile launch my-profile  Switch to 'my-profile' and launch claude-code
  claude-profile l my-profile       Switch and launch (short form)
  claude-profile list               List all profiles
  claude-profile ls                 List all profiles (short form)
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Switch command
    switch_parser = subparsers.add_parser(
        "switch",
        aliases=["s"],
        help="Switch to a specific profile"
    )
    switch_parser.add_argument(
        "profile_name",
        help="Name of the profile to switch to"
    )

    # Launch command
    launch_parser = subparsers.add_parser(
        "launch",
        aliases=["l"],
        help="Switch to a profile and launch claude-code"
    )
    launch_parser.add_argument(
        "profile_name",
        help="Name of the profile to switch to"
    )

    # List command
    list_parser = subparsers.add_parser(
        "list",
        aliases=["ls", "show"],
        help="List all configured profiles"
    )

    # Parse arguments
    args = parser.parse_args()

    # Initialize managers
    profile_manager = ProfileManager()
    claude_config = ClaudeConfigManager()

    # Execute command or launch TUI
    if args.command in ["switch", "s"]:
        sys.exit(cmd_switch(args.profile_name, profile_manager, claude_config))
    elif args.command in ["launch", "l"]:
        sys.exit(cmd_launch(args.profile_name, profile_manager, claude_config))
    elif args.command in ["list", "ls", "show"]:
        sys.exit(cmd_list(profile_manager, claude_config))
    else:
        # No command specified, launch TUI
        sys.exit(run_tui(profile_manager, claude_config))


if __name__ == "__main__":
    main()
