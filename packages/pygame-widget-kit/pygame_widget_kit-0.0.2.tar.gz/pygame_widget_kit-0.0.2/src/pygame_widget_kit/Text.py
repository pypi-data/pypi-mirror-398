import pygame
from .UIComponent import *

class Text(UIComponent):
    def __init__(self, text_str="",font_size=25,
                 font_type='Veranda',pos=(0,0),
                 text_color:tuple[int,int,int] = (127,127,127),
                 bg_color:tuple[int,int,int] = (0,0,0),
                 style=None, 
                 z_index=0, 
                 color=None, 
                 
                 border_color=...):
        
        self.font_size=font_size
        self.font_type=font_type
        self.font = pygame.font.SysFont(self.font_type, self.font_size)
        self.text_str = text_str
        self.text_color = text_color
        self.render = self.font.render(text_str, True,self.text_color , None)        
        self.size = self.render.get_size()
        rect = (pos[0],pos[1],self.size[0],self.size[1])
        
        super().__init__(rect, style, z_index, color, border_color)
        
    def set_text(self,new_text_str):
        self.text_str = new_text_str
        self.render = self.font.render(self.text_str, True,self.text_color , None)        
        self.size = self.render.get_size()

    
    def update_font_size(self,new_size):
        self.font_size = new_size
        self.font = pygame.font.SysFont(self.font_type, self.font_size)
        self.render = self.font.render(self.text_str, True,(255,255,255) , None)        
        self.size = self.render.get_size()
    def update_font_type(self,new_type):
        self.font_type = new_type
        self.font = pygame.font.SysFont(self.font_type, self.font_size)
        self.render = self.font.render(self.text_str, True,(255,255,255) , None)        
        self.size = self.render.get_size()
    

    def draw(self, surface):
        surface.blit(self.render,self.absolute_rect)
        



""" 

class text():
    def __init__(self,text_str="",font_size=25,font_type='Veranda',pos=(0,0),text_color:tuple[int,int,int] = (0,0,0)):
        self.font_size=font_size
        self.font_type=font_type
        self.font = pygame.font.SysFont(self.font_type, self.font_size)
        self.text_str = text_str
        self.text_color = text_color
        self.render = self.font.render(text_str, True,self.text_color , None)        
        self.size = self.render.get_size()
        self.pos = pos

    def draw(self,pencere:pygame.Surface):
        pencere.blit(self.render,self.pos)

    def update_text(self,new_text_str):
        self.text_str = new_text_str
        self.render = self.font.render(self.text_str, True,self.text_color , None)        
        self.size = self.render.get_size()

    def update_pos(self,new_pos):
        self.pos = new_pos
    def update_font_size(self,new_size):
        self.font_size = new_size
        self.font = pygame.font.SysFont(self.font_type, self.font_size)
        self.render = self.font.render(self.text_str, True,(255,255,255) , None)        
        self.size = self.render.get_size()
    def update_font_type(self,new_type):
        self.font_type = new_type
        self.font = pygame.font.SysFont(self.font_type, self.font_size)
        self.render = self.font.render(self.text_str, True,(255,255,255) , None)        
        self.size = self.render.get_size()

 """