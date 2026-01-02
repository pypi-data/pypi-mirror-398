import pygame
from .UIComponent import UIComponent
from .Text import Text
from .Button import *
from functools import partial


class SelectOption(Button):
    def __init__(self,value:str, rect, parent_select:"Select", color=(200,200,200),border_color = (127,127,127)):
        super().__init__(text_str=value,pos=(rect[0],rect[1]),size=(rect[2],rect[3]), color=color,padding=(5,5),text_color=(0,0,0),border_color=border_color)
        self.value = value
        self.parent_select = parent_select


    def on_click(self, event):
        self.parent_select.set_value(self.value)
        self.parent_select.close()
        if self.click_function:
            self.click_function()






class Select(UIComponent):
    def __init__(
        self,
        rect,
        options:list[str],
        default_index=0,
        color=(180,180,180),
        hover_color=(200,200,200),
        border_color = (0,255,0),
        z_index = 0
    ):
        super().__init__(rect, color=color, hover_color=hover_color,border_color=border_color,z_index=z_index)

        self.options = options
        self.is_open = False
        self.selected_value = options[default_index] 

        # Görünen text
        self.text = Text(
            text_str=self.selected_value,
            pos=(8, 8),
            text_color=(0,0,0)
        )
        self.add_child(self.text)

        # Dropdown option container
        self.option_height = rect[3]
        self.option_components:list[SelectOption] = []
        self.add_all_options()

        self.on_option_change = None
    

    def bind_on_option_chance(self,func,*args):
        self.on_option_change = partial(func, *args)

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()


    def add_all_options(self):
        base_x, base_y, w, h = self.rect

        for i, value in enumerate(self.options):
            opt_rect = (
                0,
                h * (i + 1),
                w,
                h
            )

            opt = SelectOption(
                value,
                opt_rect,
                parent_select=self,
                color=(220,220,220)
            )
            opt.z_index = self.z_index + 1
            self.add_child(opt)
            self.option_components.append(opt)
            opt.visible = False

    def open(self):
        if self.is_open:
            return

        self.is_open = True
        for opt in self.option_components:
            opt.visible = True
    
        self.ui_manager.modal = self


    def close(self):
        self.is_open = False
        # for opt in self.option_components:
        #     self.children.remove(opt)
        #self.option_components.clear()
        self.ui_manager.modal = None
        for opt in self.option_components:
            opt.visible = False


    def set_value(self, value):
        self.selected_value = value
        self.text.set_text(value)
        if self.on_option_change:
            self.on_option_change()

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
