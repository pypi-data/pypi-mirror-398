# help_core_pygame: Independent Markdown Help Viewer (Pygame)

![License MIT](https://img.shields.io/badge/License-MIT-green.svg)

[ Spanish README_ES.md is available ](https://github.com/acastr008/help_core_pygame/blob/main/README_ES.md)


## Overview

`help_core_pygame` is a Python library designed to offer a **highly portable and independent help visualization solution**, based solely on **Pygame**.

It allows rendering text with **reduced Markdown formatting** directly in a *standalone* window or on any Pygame surface, without relying on complex GUI libraries.

### Primary Use

It is the ideal solution for Pygame projects that require a professionally formatted help screen, including lists, code, and styles (bold, italics), with full **scroll functionality** and event handling.
The help content must be provided in Markdown text format. The Markdown support is not complete but is sufficient to provide attractive and well-structured help.

## Key Features

* **No Complex External Dependencies:** Based solely on Pygame, ensuring maximum portability.
* **Reduced Markdown Support:** Handles the most essential elements for documentation: headers (`#`), paragraphs, lists (`-`, `1.`), inline code (`` `code` ``), and fenced code blocks (```).
* **Standalone Mode (Own Window):** Includes the `open_help_standalone` function to open a dedicated window with its own event loop (closes with `ESC` or `QUIT`).
* **Embedded Mode (Overlay):** Allows integrating the `HelpViewer` onto a `pygame.Surface` and managing its events (`handle_event`) in your own loop.
* **Advanced Scrolling:** Full support for mouse wheel scrolling, scrollbar dragging (*thumb*), and keys (`PgUp/PgDn`, `Home/End`).
* **Limit Notification:** Allows defining a *callback* (`on_scroll_limit`) to notify when the scroll reaches the top or bottom limit, with a configurable *cooldown* to prevent bouncing (ideal for playing limit sounds, like `beep_scroll.mp3`).

---

## Installation

The package is available on PyPI (using the project name `help_core_pygame`):

```bash
pip install help-core-pygame
Requirement: You need to have pygame installed in your environment.
```

# Quick Usage Example (Standalone Mode)
The following example shows how to launch the help viewer in its own window and how to configure the scroll limit callback with a sound.

```Python

import pygame
# IMPORTANT! The module name to import is help_core_pygame.
from help_core_pygame import open_help_standalone 

# Initialize Pygame (essential to use the viewer)
pygame.init()

# 1. Read the Markdown content
try:
    MD_TEXT = open("my_help.md", encoding="utf-8").read()
except FileNotFoundError:
    MD_TEXT = "# Error\nHelp file not found."

# 2. Prepare the sound for the scroll limit
try:
    # Adjust this path to where you have the asset in your project.
    # The 'beep_scroll.mp3' file must be in an accessible path.
    beep_sound = pygame.mixer.Sound("beep_scroll.mp3") 
except pygame.error:
    print("Warning: Could not load sound file 'beep_scroll.mp3'.")
    beep_sound = None

# 3. Define the limit callback
def beep_on_limit(where: str) -> None:
    """Function called when the scroll limit is reached (top/bottom)."""
    print(f"Scroll limit reached: {where}")
    if beep_sound is not None:
        beep_sound.play()

# 4. Call the standalone function
open_help_standalone(
    md_text=MD_TEXT,
    title="My Application Help",
    size=(1200, 900),
    wheel_step=48,
    kernel_bg=(222, 222, 222),  # Light gray background
    on_scroll_limit=beep_on_limit,
    scroll_limit_cooldown_ms=300, # 300 ms anti-bounce
)

# Quit Pygame upon completion
pygame.quit()
The file examples/demo_help_standalone.py contains a complete demo of this mode.
```

# 2) Usage Example for Embedded Mode (Overlay Mode)
A demo is provided in examples/demo_help_overlay_beep.py. Help is activated by pressing F1 and is displayed in the program's main window. It uses the embedded mode of HelpViewer (not open_help_standalone). When exiting the help, the screen content is recovered, and drawing can continue.

