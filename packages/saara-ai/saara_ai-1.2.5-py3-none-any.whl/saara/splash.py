"""
🪔 SAARA Splash Screen

A beautiful Sanskrit-inspired ASCII art splash with animated "Lamp of Knowledge" motif.

© 2024-2025 Nikhil. All Rights Reserved.
"""

import time
import random
import sys
import os

# Theme Colors
C_GOLD = '\033[93m'
C_CYAN = '\033[96m'
C_WHITE = '\033[97m'
C_GREY = '\033[90m'
C_RED = '\033[91m'
C_ORANGE = '\033[38;5;208m'
C_YELLOW = '\033[38;5;220m'
C_FIRE1 = '\033[38;5;202m'  # Deep Orange
C_FIRE2 = '\033[38;5;208m'  # Orange
C_FIRE3 = '\033[38;5;214m'  # Light Orange
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'

# ANSI escape codes for cursor control
CURSOR_UP = '\033[A'
CURSOR_DOWN = '\033[B'
CLEAR_LINE = '\033[2K'
CURSOR_HOME = '\033[H'
HIDE_CURSOR = '\033[?25l'
SHOW_CURSOR = '\033[?25h'


def display_animated_splash(duration: float = 2.5):
    """
    Display an animated splash screen with flickering flame effect.
    
    Uses simple ANSI escape codes for smooth in-place updates (no Rich Live).
    
    Args:
        duration: How long to show the animation (seconds). Set to 0 for infinite.
    """
    # Fire color palette
    FIRE_COLORS = [C_GOLD, C_ORANGE, C_FIRE1, C_FIRE2, C_FIRE3, C_YELLOW]
    
    # Flame animation frames
    FLAME_FRAMES = [
        ("   )  (   ", "  (    )  ", "  ( ॐ  )  "),
        ("  (    )  ", "   )  (   ", "   ) ॐ (   "),
        ("   ~  ~   ", "  ( ~~ )  ", "  ( ॐ  )  "),
        ("  *    *  ", "   (  )   ", "   ) ॐ (   "),
        ("   ^  ^   ", "  (    )  ", "  ( ॐ  )  "),
        ("  (  ~ )  ", "   ~ ~ ~  ", "   ) ॐ (   "),
    ]
    
    def get_frame(frame_idx):
        """Generate a single frame of the animation."""
        flame = FLAME_FRAMES[frame_idx % len(FLAME_FRAMES)]
        c1 = random.choice(FIRE_COLORS)
        c2 = random.choice(FIRE_COLORS)
        c3 = random.choice(FIRE_COLORS[:3])  # Hotter colors for ॐ
        
        lines = [
            "",
            f"                    {c1}{flame[0]}{RESET}",
            f"                    {c2}{flame[1]}{RESET}",
            f"                    {c3}{flame[2]}{RESET}",
            f"                    {C_ORANGE}   _||_   {RESET}",
            f"                    {C_ORANGE}  [████]  {RESET}",
            "",
            f"    {C_GOLD}  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬       ▬▬▬▬▬▬▬▬▬▬{RESET}",
            f"    {C_CYAN}  │  ╭──────────╮  │       │  ╭──────╯{RESET}",
            f"    {C_CYAN}  │  ╰────╮     │  │       │  │       {RESET}",
            f"    {C_CYAN}  ╰──────┼─────╯  │       │  ╰──────╮{RESET}",
            f"    {C_CYAN}         │        │       │         │{RESET}",
            "",
            f"         {BOLD}{C_WHITE}S  A  A  R  A{RESET}  {C_GREY}│{RESET}  {C_GOLD}ज्ञानस्य सारः{RESET}",
            f"    {C_GREY}────────────────────────────────────────────{RESET}",
            f"    {C_GREY}Autonomous Document-to-LLM Data Engine{RESET}",
            f"    {C_GREY}© 2024-2025 Nikhil. All Rights Reserved.{RESET}",
            "",
        ]
        return lines
    
    num_lines = len(get_frame(0))
    
    try:
        # Hide cursor during animation
        print(HIDE_CURSOR, end='', flush=True)
        
        # Print initial frame
        initial_frame = get_frame(0)
        print('\n'.join(initial_frame))
        
        start_time = time.time()
        frame_idx = 0
        
        while True:
            # Check if duration exceeded
            if duration > 0 and (time.time() - start_time) >= duration:
                break
            
            time.sleep(0.15)
            frame_idx += 1
            
            # Move cursor up to overwrite previous frame
            print(f'\033[{num_lines}A', end='')
            
            # Print new frame
            new_frame = get_frame(frame_idx)
            print('\n'.join(new_frame))
            
    except KeyboardInterrupt:
        pass
    finally:
        # Show cursor again
        print(SHOW_CURSOR, end='', flush=True)


def display_splash(animate: bool = True):
    """
    Displays the static Sanskrit 'SAARA' logo with a 'Knowledge' motif.
    
    For animated version, use display_animated_splash().
    
    Args:
        animate: If True, adds a subtle delay between lines
    """
    delay = 0.03 if animate else 0

    # The Lamp (Diya)
    lamp_art = [
        f"                    {C_GOLD}   )  (   {RESET}",
        f"                    {C_GOLD}  (    )  {RESET}",
        f"                    {C_GOLD}  ( ॐ  )  {RESET}",
        f"                    {C_ORANGE}   _||_   {RESET}",
        f"                    {C_ORANGE}  [████]  {RESET}",
    ]

    # Sanskrit logo
    logo_lines = [
        f"    {C_GOLD}  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬       ▬▬▬▬▬▬▬▬▬▬{RESET}",
        f"    {C_CYAN}  │  ╭──────────╮  │       │  ╭──────╯{RESET}",
        f"    {C_CYAN}  │  ╰────╮     │  │       │  │       {RESET}",
        f"    {C_CYAN}  ╰──────┼─────╯  │       │  ╰──────╮{RESET}",
        f"    {C_CYAN}         │        │       │         │{RESET}",
    ]

    title_en = "S  A  A  R  A"
    tagline_sanskrit = "ज्ञानस्य सारः"
    tagline_english = "Autonomous Document-to-LLM Data Engine"

    print("\n")

    for line in lamp_art:
        print(line)
        if animate:
            time.sleep(delay)

    print()

    for line in logo_lines:
        print(line)
        if animate:
            time.sleep(delay)

    print()

    print(f"         {BOLD}{C_WHITE}{title_en}{RESET}  {C_GREY}│{RESET}  {C_GOLD}{tagline_sanskrit}{RESET}")
    print(f"    {C_GREY}────────────────────────────────────────────{RESET}")
    print(f"    {C_GREY}{tagline_english}{RESET}")
    print(f"    {C_GREY}© 2024-2025 Nikhil. All Rights Reserved.{RESET}")
    print()


def display_minimal_header():
    """Display a compact single-line header for subcommands."""
    print(f"\n{C_GOLD}🪔{RESET} {BOLD}{C_CYAN}SAARA{RESET} {C_GREY}• ज्ञानस्य सारः{RESET}")
    print(f"{C_GREY}{'─' * 40}{RESET}\n")


def display_version():
    """Display version information with style."""
    from importlib.metadata import version as get_version
    
    try:
        ver = get_version("saara-ai")
    except Exception:
        ver = "dev"
    
    print(f"\n{C_GOLD}🪔{RESET} {BOLD}SAARA{RESET} v{ver}")
    print(f"{C_GREY}The Essence of Knowledge • ज्ञानस्य सारः{RESET}")
    print(f"{C_GREY}© 2024-2025 Nikhil. All Rights Reserved.{RESET}\n")


def display_goodbye():
    """Display a styled goodbye message."""
    print(f"\n{C_GOLD}🪔{RESET} {C_GREY}May knowledge light your path. नमस्ते।{RESET}\n")


if __name__ == "__main__":
    print("\nSAARA Animated Splash Demo (2.5 seconds)...\n")
    display_animated_splash(duration=2.5)
    print(f"\n{BOLD}{C_CYAN}saara{RESET} {C_GOLD}»{RESET} Ready!\n")
