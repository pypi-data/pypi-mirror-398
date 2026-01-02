import pygame
from .UIComponent import *
from .Widget import *
from .Button import *

class Radio(Widget):
    def __init__(
        self,
        rect,
        options: list[str],
        default_index=0,
        item_height=24,
        spacing=6,
        z_index=0,
        color=(230, 230, 230),
        border_color=(180, 180, 180),
        check_color=(60, 160, 255),
        text_color=(0, 0, 0),
    ):
        super().__init__(rect, color=None, border_color=None, z_index=z_index)

        self.options_text = options
        self.selected_index = default_index

        self.item_height = item_height
        self.spacing = spacing

        self.color = color
        self.border_color = border_color
        self.check_color = check_color

        self.text_color = text_color

        self.options:list[RadioOption] = []
        self._build_options()

    def _build_options(self):
        y = 0

        for i, text in enumerate(self.options_text):
            opt = RadioOption(
                rect=(0, y, self.rect[2], self.item_height),
                index=i,
                text=text,
                radio=self,
                color=self.color,
                border_color=self.border_color,
                check_color=self.check_color,
                text_color=self.text_color,
            )
            self.options.append(opt)
            self.add_child(opt)
            

            y += self.item_height + self.spacing
    def get_value(self):
        if not self.options_text:
            return None
        return self.options_text[self.selected_index]

    def set_index(self, index):
        if 0 <= index < len(self.options_text):
            self.selected_index = index

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return
        for child in self.children:
            child.handle_event(event)



            
class RadioOption(Button):
    def __init__(
        self,
        rect,
        index,
        text:str,
        radio:Radio,
        color,
        border_color,
        check_color,
        text_color,
    ):
        

        

        self.radio = radio
        self.index = index
        self.check_color = check_color

        self.circle_radius = rect[3] // 3
        self.circle_center_offset = (self.circle_radius + 4, rect[3] // 2)

        super().__init__(text_str=text,pos = (rect[0],rect[1]),size=(rect[2],rect[3]),text_color = text_color,
                         border_color=border_color,color=color,padding=(self.circle_radius*3,0))


    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        x, y, w, h = self.absolute_rect
        cx = x + self.circle_center_offset[0]
        cy = y + self.circle_center_offset[1]

        # hover background
        if self.hovered:
            pygame.draw.rect(surface, (60, 60, 60), self.absolute_rect, 0)

        # outer circle
        pygame.draw.circle(surface, self.border_color, (cx, cy), self.circle_radius, 2)

        # inner dot
        if self.radio.selected_index == self.index:
            pygame.draw.circle(surface, self.check_color, (cx, cy), self.circle_radius - 4)

        self.text.draw(surface)
    
    def on_click(self, event):
        self.radio.selected_index = self.index
        if self.click_function is not None:
            self.click_function()
