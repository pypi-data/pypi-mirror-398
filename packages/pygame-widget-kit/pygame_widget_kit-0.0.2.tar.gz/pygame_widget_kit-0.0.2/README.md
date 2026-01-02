# pygame-widget-kit

[![PyPI](https://img.shields.io/pypi/v/pygame-widget-kit.svg)](https://pypi.org/project/pygame-widget-kit/)

A GUI framework built on Pygame. pygame-widget-kit is a retained-mode UI system with a component tree, event routing, focus and modal management, and extensible widgets such as Select/Dropdown and TextInput with mouse-based text selection and clipboard support.

PyPI: https://pypi.org/project/pygame-widget-kit/

## Features

- Retained-mode component tree with nested children
- Event routing with hover, focus, and active state handling
- Modal/dropdown support via `UIManager`
- Built-in widgets: `Button`, `Text`, `Select`, `Radio`, `TextInput`
- Text input filtering modes (text, number, hex, binary, octal)
- Clipboard copy/paste in `TextInput` (requires `pygame.scrap`)

## Installation

```bash
pip install pygame-widget-kit
```

Pygame is listed as a dependency (pygame >= 2.0.0). Make sure you call `pygame.init()` before creating widgets.

## Usage

```python

import pygame
from pygame_widget_kit import *


SCREEN_WIDTH = 900
SCREEN_HEIGHT = 720


def update_label_from_input(input_box: TextInput, label: Text):
    label.set_text(f"Label: {input_box.text_value}")


def update_select_label(select: Select, label: Text):
    label.set_text(f"Selected: {select.selected_value}")


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    root = Widget((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), border_color=None)
    ui = UIManager(root)

    title = Text("pygame-widget-kit demo", pos=(24, 20), text_color=(0, 0, 0))
    root.add_child(title)

    input_box = TextInput(rect=(24, 70, 220, 36), initial_text="")
    update_button = Button("Update label", pos=(256, 70), size=(160, 36))
    value_label = Text("Label: (empty)", pos=(432, 76), text_color=(0, 0, 0))
    update_button.click_bind(update_label_from_input, input_box, value_label)

    root.add_child(input_box)
    root.add_child(update_button)
    root.add_child(value_label)

    input_types_title = Text("input types:", pos=(24, 150), text_color=(0, 0, 0))
    root.add_child(input_types_title)

    input_rows = [
        ("Allow all:", ALLOW_ALL_CHARS),
        ("Text only:", TEXT_ONLY),
        ("Number only:", NUMBER_ONLY),
        ("Hex only:", HEX_ONLY),
        ("Binary only:", BINARY_ONLY),
    ]

    input_label_x = 24
    input_box_x = 200
    input_row_y = 190
    input_row_gap = 44

    for index, (label_text, mode) in enumerate(input_rows):
        row_y = input_row_y + index * input_row_gap
        row_label = Text(label_text, pos=(input_label_x, row_y + 6), text_color=(0, 0, 0))
        row_input = TextInput(rect=(input_box_x, row_y, 240, 34), allowed_char_mode=mode)
        root.add_child(row_label)
        root.add_child(row_input)

    select_label = Text("Select:", pos=(24, 430), text_color=(0, 0, 0))
    select = Select(
        rect=(100, 424, 160, 32),
        options=["Easy", "Hard", "Expert"],
        default_index=0,
        z_index=2
    )
    select_value = Text("Selected: Easy", pos=(280, 430), text_color=(0, 0, 0))
    select.bind_on_option_chance(update_select_label, select, select_value)

    root.add_child(select_label)
    root.add_child(select)
    root.add_child(select_value)

    radio_label = Text("Radio:", pos=(24, 490), text_color=(0, 0, 0))
    radio = Radio(
        (100, 486, 150, 28),
        options=["OPTION A","OPTION B","OPTION C"],
        default_index=0,
    )
    radio_value = Text("Radio: A", pos=(280, 490), text_color=(0, 0, 0))

    root.add_child(radio_label)
    root.add_child(radio)
    root.add_child(radio_value)

    radio_last_value = radio.get_value()

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            ui.handle_event(event)

        current_radio_value = radio.get_value()
        if current_radio_value != radio_last_value:
            radio_value.set_text(f"Radio: {current_radio_value}")
            radio_last_value = current_radio_value

        screen.fill((250, 250, 250))
        root.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()



```

## Usage notes

- Use `UIManager` to handle events and manage focus/active state.
- Call `root.add_child(...)` to build a component tree. Child positions are relative to their parent.
- `TextInput` handles caret blink in `draw`, so you only need to call `draw` each frame.
- `Select` uses modal behavior through `UIManager`; clicks outside the dropdown close it.
- `Select` expects `options` as a list of strings and exposes `selected_value`.
- `Radio` expects `options` as a list of `(label, value)` tuples and exposes `get_value()`.

## TextInput allowed_char_mode

- `ALLOW_ALL_CHARS`
- `TEXT_ONLY`
- `NUMBER_ONLY`
- `HEX_ONLY`
- `BINARY_ONLY`
- `OCTAL_ONLY`

## Creating custom widgets

Subclass `UIComponent` and override any of the following hooks:

- `draw(surface)` for custom rendering
- `handle_event(event)` for keyboard/mouse logic
- `on_click(event)` for click behavior

## License

MIT
