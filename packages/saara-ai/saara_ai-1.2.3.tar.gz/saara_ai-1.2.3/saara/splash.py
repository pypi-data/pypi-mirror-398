"""
🪔 SAARA Splash Screen

A beautiful Sanskrit-inspired ASCII art splash with animated "Lamp of Knowledge" motif.
Features organic flame flickering animation using Rich's Live display.

© 2024-2025 Nikhil. All Rights Reserved.
"""

import time
import random
import sys

# Theme Colors
C_GOLD = '\033[93m'
C_CYAN = '\033[96m'
C_WHITE = '\033[97m'
C_GREY = '\033[90m'
C_RED = '\033[91m'
C_ORANGE = '\033[38;5;208m'
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'


def display_animated_splash(duration: float = 3.0):
    """
    Display an animated splash screen with flickering flame effect.
    
    Uses Rich's Live display for smooth in-place updates.
    
    Args:
        duration: How long to show the animation (seconds). Set to 0 for infinite.
    """
    try:
        from rich.console import Console
        from rich.live import Live
        from rich.panel import Panel
        from rich.text import Text
        from rich.align import Align
        
        console = Console()
        
        # Fire colors from hottest (Yellow) to coolest (Deep Red/Orange)
        FIRE_COLORS = ["#FFD700", "#FF8C00", "#FF4500", "#E25822", "#FFA500", "#FFAE42"]
        
        # Flame animation frames - different shapes for organic look
        FLAME_FRAMES = [
            ["   )  (   ", "  (    )  ", "   ) ॐ (   "],
            ["  (    )  ", "   )  (   ", "  ( ॐ  )  "],
            ["   ~  ~   ", "  ( ~~ )  ", "   ) ॐ (   "],
            ["  *    *  ", "   (  )   ", "  ( ॐ  )  "],
            ["   ^  ^   ", "  (    )  ", "   ) ॐ (   "],
            ["  (  ~ )  ", "   ~ ~ ~  ", "  ( ॐ  )  "],
        ]
        
        def generate_frame(frame_index: int) -> Align:
            """Generate a single animation frame."""
            
            # Select flame frame and randomize colors
            flame_frame = FLAME_FRAMES[frame_index % len(FLAME_FRAMES)]
            flame_color1 = random.choice(FIRE_COLORS)
            flame_color2 = random.choice(FIRE_COLORS)
            flame_color3 = random.choice(FIRE_COLORS[:3])  # Hotter colors for ॐ
            
            # Build the flame
            lamp = Text()
            lamp.append(f"                {flame_frame[0]}\n", style=f"bold {flame_color1}")
            lamp.append(f"                {flame_frame[1]}\n", style=f"bold {flame_color2}")
            lamp.append(f"                {flame_frame[2]}\n", style=f"bold {flame_color3}")
            lamp.append("                   _||_\n", style="#CD853F")
            lamp.append("                  [████]\n", style="#8B4513")
            
            # Sanskrit-styled logo using box drawing
            logo = Text()
            logo.append("\n")
            logo.append("    ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬       ▬▬▬▬▬▬▬▬▬▬\n", style="bold #FFD700")
            logo.append("    │  ╭──────────╮  │       │  ╭──────╯\n", style="bold #00CED1")
            logo.append("    │  ╰────╮     │  │       │  │\n", style="bold #00CED1")
            logo.append("    ╰──────┼─────╯  │       │  ╰──────╮\n", style="bold #00CED1")
            logo.append("           │        │       │         │\n", style="bold #00CED1")
            
            # Brand name with blocks
            brand = Text()
            brand.append("\n")
            brand.append("      S  A  A  R  A  ", style="bold #000000 on #FFD700")
            brand.append("  │  ", style="dim white")
            brand.append("  ज्ञानस्य सारः  ", style="bold #FFA500")
            brand.append("\n")
            
            # Subtitle
            subtitle = Text()
            subtitle.append("    ────────────────────────────────────────\n", style="dim #666666")
            subtitle.append("      Autonomous Document-to-LLM Data Engine\n", style="white")
            subtitle.append("      © 2024-2025 Nikhil. All Rights Reserved.\n", style="dim #888888")
            
            # Combine
            content = Text.assemble(lamp, logo, brand, subtitle)
            
            return Align.center(
                Panel(
                    Align.center(content),
                    border_style="#FFD700",
                    padding=(1, 4),
                    expand=False,
                    title="[bold #FFD700]🪔 SAARA[/bold #FFD700]",
                    subtitle="[dim]The Essence of Knowledge[/dim]"
                )
            )
        
        # Run animation
        if duration <= 0:
            # Infinite mode
            with Live(generate_frame(0), refresh_per_second=8, screen=False) as live:
                i = 0
                while True:
                    time.sleep(0.12)
                    live.update(generate_frame(i))
                    i += 1
        else:
            # Timed mode
            start_time = time.time()
            with Live(generate_frame(0), refresh_per_second=8, screen=False) as live:
                i = 0
                while time.time() - start_time < duration:
                    time.sleep(0.12)
                    live.update(generate_frame(i))
                    i += 1
            console.print()  # Clean line after animation
                    
    except ImportError:
        # Fallback to static splash if Rich is not available
        display_splash(animate=False)
    except KeyboardInterrupt:
        print(f"\n{C_GOLD}🪔{RESET} {C_GREY}नमस्ते। Goodbye!{RESET}\n")


def display_splash(animate: bool = True):
    """
    Displays the static Sanskrit 'SAARA' logo with a 'Knowledge' motif.
    
    For animated version, use display_animated_splash().
    
    Args:
        animate: If True, adds a subtle delay between lines (not full animation)
    """
    delay = 0.03 if animate else 0

    # The Lamp (Diya) - Symbolizing "The Essence of Knowledge"
    lamp_art = [
        f"                    {C_GOLD}   )  (   {RESET}",
        f"                    {C_GOLD}  (    )  {RESET}",
        f"                    {C_GOLD}  ( ॐ  )  {RESET}",
        f"                    {C_ORANGE}   _||_   {RESET}",
        f"                    {C_ORANGE}  [████]  {RESET}",
    ]

    # Sanskrit 'सार' (Saara) using box-drawing characters
    logo_lines = [
        f"    {C_GOLD}  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬       ▬▬▬▬▬▬▬▬▬▬{RESET}",
        f"    {C_CYAN}  │  ╭──────────╮  │       │  ╭──────╯{RESET}",
        f"    {C_CYAN}  │  ╰────╮     │  │       │  │       {RESET}",
        f"    {C_CYAN}  ╰──────┼─────╯  │       │  ╰──────╮{RESET}",
        f"    {C_CYAN}         │        │       │         │{RESET}",
    ]

    # Taglines
    title_en = "S  A  A  R  A"
    tagline_sanskrit = "ज्ञानस्य सारः"
    tagline_english = "Autonomous Document-to-LLM Data Engine"

    print("\n")

    # 1. Draw the Lamp
    for line in lamp_art:
        print(line)
        if animate:
            time.sleep(delay)

    print()

    # 2. Draw the Logo
    for line in logo_lines:
        print(line)
        if animate:
            time.sleep(delay)

    print()

    # 3. Footer
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
    # Demo: Run animated splash for 5 seconds, then show menu prompt
    print("\n" + "="*50)
    print("  SAARA Splash Screen Demo")
    print("="*50)
    print("\nRunning animated splash (Ctrl+C to skip)...\n")
    
    display_animated_splash(duration=5.0)
    
    print(f"\n{BOLD}{C_CYAN}saara{RESET} {C_GOLD}»{RESET} Type 'help' to begin your journey.\n")
