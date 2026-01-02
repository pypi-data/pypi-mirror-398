import pygame
from .Text import *
from .UIComponent import *

class Button(UIComponent):
    def __init__(self, text_str = "Button",
                pos = (0,0),
                size = (200,40),
                style=None,
                z_index=0, 
                color=(255,175,175), 
                border_color = None, 
                hover_color=(150,150,150),
                text_color = (0,0,0)):
        self.text_str = text_str
        self.size = size
        self.text_color =text_color
        self.text = Text(self.text_str,pos = (20,20),text_color=text_color,bg_color=None)
        
        rect = (pos[0],pos[1],self.size[0],self.size[1])
        self.cc = 0
        super().__init__(rect, style, z_index, color, border_color, hover_color)
        self.add_child(self.text)
    
    def draw(self, surface):
        if self.visible == False:
            return
        
        color = self.color
        if self.hovered:
            color=self.hover_color

        if color is not None:
            pygame.draw.rect(surface,color,self.absolute_rect,0)

        self.text.draw(surface)


    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.active = False

    def on_click(self, event):
        print("Button clicked",self.cc)
        self.cc +=1
