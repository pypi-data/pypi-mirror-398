"""
🪔 SAARA Splash Screen

A beautiful Sanskrit-inspired ASCII art splash with the "Lamp of Knowledge" motif.
Displays देवनागरी (Devanagari) script using box-drawing characters for maximum readability.
"""

import time
import sys


# Theme Colors: High Contrast for Readability
C_GOLD = '\033[93m'      # Yellow - Wisdom/Light
C_CYAN = '\033[96m'      # Cyan - Technology/Depth
C_WHITE = '\033[97m'     # White - Clean text
C_GREY = '\033[90m'      # Grey - Subtle hints
C_RED = '\033[91m'       # Red - For accents
C_MAGENTA = '\033[95m'   # Magenta - For highlights
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'


def display_splash(animate: bool = True):
    """
    Displays a highly readable Sanskrit 'SAARA' logo with a 'Knowledge' motif.
    
    The design uses:
    - Box-drawing characters for smooth Devanagari strokes
    - A "Diya" (Lamp) symbolizing the essence of knowledge
    - Color separation for visual clarity
    
    Args:
        animate: If True, adds a subtle animation delay between lines
    """
    delay = 0.03 if animate else 0

    # The Lamp (Diya) - Symbolizing "The Essence of Knowledge"
    lamp_art = [
        f"                    {C_GOLD}   )  (   {RESET}",
        f"                    {C_GOLD}  (    )  {RESET}",
        f"                    {C_GOLD}  ( ॐ  )  {RESET}",
        f"                    {C_GOLD}   _||_   {RESET}",
        f"                    {C_GOLD}  [____]  {RESET}",
    ]

    # Sanskrit 'सार' (Saara) using box-drawing characters for maximum clarity
    # Char 1: स (Sa) + ा (aa matra)
    # Char 2: र (Ra)
    # The top line (Shirorekha) in Gold unites them - a hallmark of Devanagari
    
    logo_lines = [
        # Line 1: The Top Bar (Shirorekha) - Solid and continuous, defining feature
        f"    {C_GOLD}  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬       ▬▬▬▬▬▬▬▬▬▬{RESET}",
        
        # Line 2: Top curves of स and the vertical of र
        f"    {C_CYAN}  │  ╭──────────╮  │       │  ╭──────╯{RESET}",
        
        # Line 3: Middle connections - the loop in स
        f"    {C_CYAN}  │  ╰────╮     │  │       │  │       {RESET}",
        
        # Line 4: The diagonal stroke (characteristic of many Devanagari letters)
        f"    {C_CYAN}  ╰──────┼─────╯  │       │  ╰──────╮{RESET}",
        
        # Line 5: Bottom stems
        f"    {C_CYAN}         │        │       │         │{RESET}",
    ]

    # Taglines with Sanskrit meaning
    title_en = "S  A  A  R  A"
    tagline_sanskrit = "ज्ञानस्य सारः"      # "The Essence of Knowledge"
    tagline_english = "Autonomous Document-to-LLM Data Engine"

    # --- RENDER SEQUENCE ---
    
    print("\n")

    # 1. Draw the Lamp (The 'Essence')
    for line in lamp_art:
        print(line)
        if animate:
            time.sleep(delay)

    print()

    # 2. Draw the Sanskrit Text Logo
    for line in logo_lines:
        print(line)
        if animate:
            time.sleep(delay)

    print()

    # 3. Clean Modern Footer
    print(f"         {BOLD}{C_WHITE}{title_en}{RESET}  {C_GREY}│{RESET}  {C_GOLD}{tagline_sanskrit}{RESET}")
    print(f"    {C_GREY}────────────────────────────────────────────{RESET}")
    print(f"    {C_GREY}{tagline_english}{RESET}")
    print(f"    {C_GREY}© 2024-2025 Nikhil. All Rights Reserved.{RESET}")
    print()


def display_minimal_header():
    """
    Display a compact single-line header for subcommands.
    """
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
    # Test the splash screen
    display_splash(animate=True)
    print(f"{BOLD}{C_CYAN}saara{RESET} {C_GOLD}»{RESET} ", end="")
    print("Type 'help' to begin your journey.\n")
