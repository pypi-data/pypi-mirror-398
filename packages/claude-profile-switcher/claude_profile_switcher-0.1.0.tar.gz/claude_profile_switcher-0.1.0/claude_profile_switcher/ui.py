"""Simple ASCII-based TUI interface for profile switcher."""

import sys
import time
from typing import List, Optional

from .claude_config import ClaudeConfigManager
from .models import Profile


# Key constants
KEY_UP = "UP"
KEY_DOWN = "DOWN"
KEY_LEFT = "LEFT"
KEY_RIGHT = "RIGHT"
KEY_ENTER = "ENTER"
KEY_SPACE = "SPACE"
KEY_ESC = "ESC"
QUIT = "QUIT"

# Key mappings
KEY_NAV_UP = {"w", "W", "k", "K", KEY_UP}
KEY_NAV_DOWN = {"s", "S", "j", "J", KEY_DOWN}
KEY_BACK = {"q", "Q" , KEY_ESC, KEY_LEFT}
KEY_ADD = {"a", "A"}
KEY_EDIT = {"e", "E", KEY_RIGHT}
KEY_DELETE = {"d", "D"}
KEY_YES = {"y", "Y"}
KEY_NO = {"n", "N"}
KEY_SAVE = {"s", "S"}
KEY_CANCEL = {"c", "C"}


class TUI:
    """Simple ASCII-based TUI for profile management."""

    def __init__(self, profiles: List[Profile], claude_config: ClaudeConfigManager, profile_manager=None):
        self.profiles = profiles
        self.claude_config = claude_config
        self.profile_manager = profile_manager

        self.selected_index = 0
        self.mode = "main"  # main, edit, add, delete_confirm
        self.edit_profile = None
        self.delete_profile_name = None

        self.form_data = {}
        self.form_field = 0

        self.message = ""
        self.message_timeout = 0

    # ---------- Drawing helpers ----------
    def clear_screen(self) -> None:
        # Move cursor to top-left; actual clearing is done after rendering.
        sys.stdout.write("\033[H")

    def _clear_below_cursor(self) -> None:
        # Clear everything below current cursor position.
        sys.stdout.write("\033[J")

    def _print_block(self, lines: List[str]) -> None:
        """Print lines and clear the remainder of each line to avoid artifacts."""
        for line in lines:
            sys.stdout.write(line)
            sys.stdout.write("\033[K\n")  # Clear to end of line then newline

    def draw_box(self, lines: List[str], title: str = "", width: int = 70) -> List[str]:
        """Draw a framed box around content."""
        for line in lines:
            if len(line) > width:
                width = len(line) + 4

        result = []

        if title:
            title_padding = (width - len(title) - 2) // 2
            top_border = "┌" + "─" * title_padding + " " + title + " " + "─" * (width - len(title) - title_padding - 4) + "┐"
        else:
            top_border = "┌" + "─" * (width - 2) + "┐"
        result.append(top_border)

        for line in lines:
            result.append("│ " + line.ljust(width - 4) + " │")

        result.append("└" + "─" * (width - 2) + "┘")
        return result

    def show_message(self, msg: str) -> None:
        """Show a temporary message for ~2 seconds."""
        self.message = msg
        self.message_timeout = 2

    # ---------- Input helpers ----------
    def read_key(self) -> str:
        """
        Robust key reading using os.read to bypass Python's input buffering.
        Handles rapid escape sequences correctly.
        """
        import termios
        import select
        import os  # 必须导入 os 模块

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            # 设置 Raw 模式
            new_settings = termios.tcgetattr(fd)
            new_settings[3] = new_settings[3] & ~(termios.ICANON | termios.ECHO)
            new_settings[6][termios.VMIN] = 1
            new_settings[6][termios.VTIME] = 0
            termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)

            # 1. 读取第一个字节 (阻塞等待用户输入)
            # 使用 os.read 避免 Python 的 IO 缓冲问题
            try:
                first_byte = os.read(fd, 1)
            except OSError:
                return ""
            
            if not first_byte:
                return ""
                
            ch = first_byte.decode(errors='ignore')

            # 2. 如果不是 ESC，直接返回
            if ch != "\x1b":
                if ch in ("\r", "\n"): return KEY_ENTER
                if ch == " ": return KEY_SPACE
                return ch

            # 3. 如果是 ESC (\x1b)，检查是否有后续内容
            # 使用极短的超时来区分 "按下 ESC 键" 和 "发送转义序列"
            ready, _, _ = select.select([fd], [], [], 0.01)
            
            if not ready:
                return KEY_ESC

            # 4. 读取序列的第二个字节 (通常是 '[')
            second_byte = os.read(fd, 1)
            ch2 = second_byte.decode(errors='ignore')

            if ch2 == '[':
                # CSI 序列: \x1b[...
                # 再次检查是否有第三个字节
                ready, _, _ = select.select([fd], [], [], 0.01)
                if not ready:
                    return KEY_ESC # 只有 \x1b[ 没有后续，这很不寻常，但也退回 ESC
                
                third_byte = os.read(fd, 1)
                ch3 = third_byte.decode(errors='ignore')
                
                # 严格匹配方向键
                if ch3 == 'A': return KEY_UP
                if ch3 == 'B': return KEY_DOWN
                if ch3 == 'C': return KEY_RIGHT  # 新增
                if ch3 == 'D': return KEY_LEFT   # 新增
                
                # 如果需要处理 PageUp/Down 等更长的序列 (如 \x1b[5~)，可以在这里扩展
                # 但对于你的代码，目前只需要处理到这里，避免多读
                
            elif ch2 == 'O':
                # SS3 序列 (某些终端的方向键是 \x1bOA / \x1bOB)
                ready, _, _ = select.select([fd], [], [], 0.01)
                if ready:
                    third_byte = os.read(fd, 1)
                    ch3 = third_byte.decode(errors='ignore')
                    if ch3 == 'A': return KEY_UP
                    if ch3 == 'B': return KEY_DOWN

            # 如果读到了 \x1b 但不符合上述已知的方向键模式
            # 这是一个无法识别的序列。
            # 这里的策略是：已经消耗了缓冲区的数据，直接返回 ESC，避免残留字符干扰后续输入
            return KEY_ESC

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    def get_input(self, prompt: str, default: str = "", password: bool = False) -> Optional[str]:
        """Get user input in cooked mode; returns None on empty cancel."""
        import termios

        fd = sys.stdin.fileno()
        saved_settings = termios.tcgetattr(fd)

        normal_settings = termios.tcgetattr(fd)
        normal_settings[3] = normal_settings[3] | termios.ICANON
        normal_settings[3] = normal_settings[3] | termios.ECHO
        normal_settings[6][termios.VMIN] = 1
        normal_settings[6][termios.VTIME] = 0

        sys.stdout.write("\033[H")
        sys.stdout.write("\n" * 20)
        sys.stdout.write("\033[J")
        sys.stdout.flush()

        full_prompt = f"{prompt} [{default[20:] + "..." if len(default) > 20 else default}]: " if default else f"{prompt}: "

        try:
            termios.tcsetattr(fd, termios.TCSAFLUSH, normal_settings)
            if password:
                import getpass

                value = getpass.getpass(full_prompt)
            else:
                value = input(full_prompt)

            if not value and default:
                return default
            return value if value else None
        except (KeyboardInterrupt, EOFError):
            raise
        finally:
            try:
                termios.tcsetattr(fd, termios.TCSAFLUSH, saved_settings)
            except Exception:
                pass

    # ---------- Rendering ----------
    def refresh_display(self) -> None:
        self.clear_screen()

        if self.mode == "main":
            self._display_main()
        elif self.mode in {"edit", "add"}:
            self._display_form()
        elif self.mode == "delete_confirm":
            self._display_delete_confirm()

        # Remove any leftover content below the current render.
        self._clear_below_cursor()
        sys.stdout.flush()

    def _display_main(self) -> None:
        current_name = self.claude_config.get_current_profile_display(self.profiles)
        status_lines = [f"Active: {current_name}"]
        if self.message:
            status_lines.append(f"Msg: {self.message}")

        profile_lines = []
        if not self.profiles:
            profile_lines.extend(["No profiles configured.", "", "Press 'a' to add a new profile."])
        else:
            for i, profile in enumerate(self.profiles):
                status_symbol = "✓" if profile.is_complete() else "✗"
                prefix = "► " if i == self.selected_index else "  "
                profile_lines.append(f"{prefix}{status_symbol} {profile.name}")

        profile_lines.append("")
        profile_lines.append("Enter: Switch | a: Add | →: Edit | d: Delete | q: Quit")

        self._print_block(self.draw_box(status_lines, "Current Status", 70))
        
        # [修复] 使用 \033[K 清除当前行剩余内容，防止留下"编辑界面"的残影
        sys.stdout.write("\033[K\n") 
        
        self._print_block(self.draw_box(profile_lines, "Available Profiles", 70))

    def _display_form(self) -> None:
        title = "Edit Profile" if self.mode == "edit" else "Add Profile"
        form_fields = [
            ("name", "Name"),
            ("base_url", "Base URL"),
            ("api_key", "API Key"),
            ("haiku_model", "Haiku Model (optional)"),
            ("sonnet_model", "Sonnet Model (optional)"),
            ("opus_model", "Opus Model (optional)"),
        ]

        form_lines = []
        for i, (field, label) in enumerate(form_fields):
            prefix = "► " if i == self.form_field else "  "
            value = self.form_data.get(field, "")
            if value and len(value) > 20:
                value = value[:20] + "..."
            masked = "*" * len(value) if field == "api_key" and value else value
            display_value = f" [{masked}]" if masked else ""
            form_lines.append(f"{prefix}{label}{display_value}")

        form_lines.append("")
        form_lines.append("→: Edit field | Esc: Cancel | Ctrl+C: Quit")

        self._print_block(self.draw_box(form_lines, title, 70))

    def _display_delete_confirm(self) -> None:
        confirm_lines = [
            "Are you sure you want to delete profile:",
            "",
            f"  {self.delete_profile_name}",
            "",
            "y: Confirm | n/Esc: Cancel",
        ]

        self._print_block(self.draw_box(confirm_lines, "Confirm Deletion", 50))

    # ---------- State operations ----------
    def edit_field(self) -> None:
        form_fields = [
            ("name", "Name"),
            ("base_url", "Base URL"),
            ("api_key", "API Key"),
            ("haiku_model", "Haiku Model"),
            ("sonnet_model", "Sonnet Model"),
            ("opus_model", "Opus Model"),
        ]

        field_key, field_label = form_fields[self.form_field]
        current_value = self.form_data.get(field_key, "")
        is_password = field_key == "api_key"

        new_value = self.get_input(field_label, current_value or "", is_password)
        if new_value is None:
            # User pressed ESC to cancel, don't change the value
            return

        self.form_data[field_key] = new_value
        # Auto-save but stay in edit mode
        self._save_form(switch_to_main=False)

    def _save_form(self, switch_to_main: bool = True) -> bool:
        """Save form data to profile manager.

        Args:
            switch_to_main: If True, return to main menu after saving.
                           If False, stay in edit/add mode.
        """
        name = self.form_data.get("name", "").strip()
        if not name:
            self.show_message("Error: Name is required")
            return False

        if self.mode == "add":
            for p in self.profiles:
                if p.name == name:
                    self.show_message(f"Error: Profile '{name}' already exists")
                    return False
        elif self.mode == "edit":
            for p in self.profiles:
                if p.name == name and p.name != self.edit_profile.name:
                    self.show_message(f"Error: Profile '{name}' already exists")
                    return False

        profile = Profile(
            name=name,
            base_url=self.form_data.get("base_url") or None,
            api_key=self.form_data.get("api_key") or None,
            haiku_model=self.form_data.get("haiku_model") or None,
            sonnet_model=self.form_data.get("sonnet_model") or None,
            opus_model=self.form_data.get("opus_model") or None,
        )

        if self.mode == "add":
            self.profile_manager.add_profile(profile)
            self.show_message(f"Profile '{name}' added")
        else:
            self.profile_manager.update_profile(self.edit_profile.name, profile)
            self.show_message(f"Profile '{name}' updated")

        self.profiles = self.profile_manager.load_profiles()

        if switch_to_main:
            self.mode = "main"
            self.form_data = {}
        else:
            # Stay in edit mode, update form_data and edit_profile
            self.form_data = {
                "name": profile.name,
                "base_url": profile.base_url or "",
                "api_key": profile.api_key or "",
                "haiku_model": profile.haiku_model or "",
                "sonnet_model": profile.sonnet_model or "",
                "opus_model": profile.opus_model or "",
            }
            if self.mode == "edit":
                self.edit_profile = profile
        return True

    def start_add(self) -> None:
        self.mode = "add"
        self.form_data = {}
        self.form_field = 0
        self.edit_profile = None

    def start_edit(self) -> None:
        if not self.profiles or self.selected_index >= len(self.profiles):
            return
        self.mode = "edit"
        self.edit_profile = self.profiles[self.selected_index]
        self.form_data = {
            "name": self.edit_profile.name,
            "base_url": self.edit_profile.base_url or "",
            "api_key": self.edit_profile.api_key or "",
            "haiku_model": self.edit_profile.haiku_model or "",
            "sonnet_model": self.edit_profile.sonnet_model or "",
            "opus_model": self.edit_profile.opus_model or "",
        }
        self.form_field = 0

    def start_delete(self) -> None:
        if not self.profiles or self.selected_index >= len(self.profiles):
            return
        self.mode = "delete_confirm"
        self.delete_profile_name = self.profiles[self.selected_index].name

    # ---------- Handlers ----------
    def handle_main(self, key: str) -> Optional[object]:
        if key in KEY_BACK:
            return QUIT
        if key in KEY_NAV_UP:
            if self.profiles:
                self.selected_index = max(0, self.selected_index - 1)
        elif key in KEY_NAV_DOWN:
            if self.profiles:
                self.selected_index = min(len(self.profiles) - 1, self.selected_index + 1)
        elif key in {KEY_ENTER, KEY_SPACE}:
            if self.selected_index < len(self.profiles):
                profile = self.profiles[self.selected_index]
                if profile.is_complete():
                    self.claude_config.apply_profile(profile)
                    return profile
                self.show_message("Error: Profile incomplete (needs URL & Key)")
        elif key in KEY_ADD:
            self.start_add()
        elif key in KEY_EDIT:
            self.start_edit()
        elif key in KEY_DELETE:
            self.start_delete()
        return None

    def handle_form(self, key: str) -> None:
        if key in KEY_BACK:
            self.mode = "main"
            self.form_data = {}
            return

        if key in KEY_NAV_UP:
            self.form_field = max(0, self.form_field - 1)
        elif key in KEY_NAV_DOWN:
            self.form_field = min(5, self.form_field + 1)
        elif key in KEY_EDIT:
            self.edit_field()

    def handle_delete_confirm(self, key: str) -> None:
        if key in KEY_YES:
            self.profile_manager.delete_profile(self.delete_profile_name)
            self.profiles = self.profile_manager.load_profiles()
            self.show_message(f"Profile '{self.delete_profile_name}' deleted")
            self.mode = "main"
            if self.profiles:
                self.selected_index = min(self.selected_index, len(self.profiles) - 1)
            else:
                self.selected_index = 0
            return

        if key in KEY_NO or key in KEY_BACK:
            self.mode = "main"
            self.delete_profile_name = None

    # ---------- Main loop ----------
    def run(self) -> Optional[Profile]:
        try:
            while True:
                self.refresh_display()

                if self.message_timeout > 0:
                    time.sleep(0.05)
                    self.message_timeout = max(0, self.message_timeout - 0.05)
                    if self.message_timeout <= 0:
                        self.message = ""
                    continue

                key = self.read_key()

                if self.mode == "main":
                    result = self.handle_main(key)
                    if result == QUIT:
                        return None
                    if isinstance(result, Profile):
                        return result
                elif self.mode in {"edit", "add"}:
                    self.handle_form(key)
                elif self.mode == "delete_confirm":
                    self.handle_delete_confirm(key)

        except KeyboardInterrupt:
            print("\nCancelled by user")
            return None
        finally:
            import termios

            try:
                fd = sys.stdin.fileno()
                termios.tcsetattr(fd, termios.TCSADRAIN, termios.tcgetattr(fd))
            except Exception:
                pass


def tui_main(profiles: List[Profile], claude_config: ClaudeConfigManager, profile_manager=None) -> Optional[Profile]:
    """Run the simple TUI and return the selected profile."""
    ui = TUI(profiles, claude_config, profile_manager)
    return ui.run()
