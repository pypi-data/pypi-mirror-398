import pygame
from .Text import *
from .UIComponent import *
from functools import partial


class Button(UIComponent):
    def __init__(self, text_str = "Button",
                pos = (0,0),
                size = (200,40),
                style=None,
                z_index=0, 
                color=(175,175,175), 
                border_color = (100,100,100), 
                hover_color=(150,150,150),
                text_color = (0,0,0),
                padding = (20,10)
                ):
        self.text_str = text_str
        self.size = size
        self.text_color =text_color
        self.padding = padding
        self.text = Text(self.text_str,pos = self.padding,text_color=text_color,bg_color=None)
        
        self.click_function = None

        
        rect = (pos[0],pos[1],self.size[0],self.size[1])
        
        super().__init__(rect, style, z_index, color, border_color, hover_color)
        self.add_child(self.text)
    
    def click_bind(self, func, *args):
        self.click_function = partial(func, *args)


    def draw(self, surface):
        if self.visible == False:
            return
        
        color = self.color
        if self.hovered:
            color=self.hover_color

        if color is not None:
            pygame.draw.rect(surface,color,self.absolute_rect,0)
        if self.border_color:
            pygame.draw.rect(surface,self.border_color,self.absolute_rect,2)


        self.text.draw(surface)


    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.active = False

    def on_click(self, event):
        if self.click_function is not None:
            self.click_function()
        else:
            print("Button clicked")
    