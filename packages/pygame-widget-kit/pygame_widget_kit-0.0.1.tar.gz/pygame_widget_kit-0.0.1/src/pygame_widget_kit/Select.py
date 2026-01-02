import pygame
from .UIComponent import UIComponent
from .Text import Text


class SelectOption(UIComponent):
    def __init__(self, text, value, rect, parent_select, color=(200,200,200)):
        super().__init__(rect, color=color)
        self.value = value
        self.parent_select = parent_select

        self.label = Text(
            text_str=text,
            pos=(5, 5),
            text_color=(0,0,0)
        )
        self.add_child(self.label)

    def handle_event(self, event):
        if not self.enabled or not self.visible:
            return

        if event.type == pygame.MOUSEBUTTONUP:
            if self.is_in_rect(event.pos):
                self.on_click(event)

    def on_click(self, event):
        self.parent_select.set_value(self.value)
        self.parent_select.close()



class Select(UIComponent):
    def __init__(
        self,
        rect,
        options:list[tuple[str, any]],
        default_index=0,
        color=(180,180,180),
        hover_color=(200,200,200)
    ):
        super().__init__(rect, color=color, hover_color=hover_color)

        self.options = options
        self.is_open = False
        self.selected_index = default_index

        # Görünen text
        self.text = Text(
            text_str=self.options[self.selected_index][0],
            pos=(8, 8),
            text_color=(0,0,0)
        )
        self.add_child(self.text)

        # Dropdown option container
        self.option_height = rect[3]
        self.option_components:list[SelectOption] = []

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()

    def open(self):
        if self.is_open:
            return

        self.is_open = True
        self.option_components.clear()

        base_x, base_y, w, h = self.rect

        for i, (label, value) in enumerate(self.options):
            opt_rect = (
                0,
                h * (i + 1),
                w,
                h
            )

            opt = SelectOption(
                label,
                value,
                opt_rect,
                parent_select=self,
                color=(220,220,220)
            )
            opt.z_index = self.z_index + 1
            self.add_child(opt)
            self.option_components.append(opt)

        self.ui_manager.modal = self


    def close(self):
        self.is_open = False

        for opt in self.option_components:
            self.children.remove(opt)

        self.option_components.clear()
        self.ui_manager.modal = None

    def set_value(self, value):
        for i, (_, v) in enumerate(self.options):
            if v == value:
                self.selected_index = i
                self.text.update_text(self.options[i][0])
                break

    def on_click(self, event):
        self.toggle()
    
    def draw(self, surface: pygame.Surface):

        super().draw(surface)

        cx = self.absolute_rect[0] + self.absolute_rect[2] - 15
        cy = self.absolute_rect[1] + self.absolute_rect[3] // 2

        if self.is_open:
            # ▲ yukarı bakan caret
            points = [
                (cx - 5, cy + 3),
                (cx + 5, cy + 3),
                (cx, cy - 3),
            ]
        else:
            # ▼ aşağı bakan caret
            points = [
                (cx - 5, cy - 3),
                (cx + 5, cy - 3),
                (cx, cy + 3),
            ]

        pygame.draw.polygon(surface, (0, 0, 0), points)
