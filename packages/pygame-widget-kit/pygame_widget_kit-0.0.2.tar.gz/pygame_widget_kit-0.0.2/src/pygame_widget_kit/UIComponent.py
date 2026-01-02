import pygame

class UIComponent:
    def __init__(self, rect, style=None,z_index = 0, color = None, border_color:tuple[int,int,int] = (0,255,0),hover_color = None):
        self.rect = rect    
        self.absolute_rect = rect          
        #self.style = style or {}

        self.parent:UIComponent = None
        self.children:list[UIComponent] = []
        self.ui_manager = None

        self.visible = True
        self.enabled = True

        self.hovered = False
        self.active = False
        self.focused = False
        self.z_index = z_index

        self.border_color = border_color
        self.show_border = True if border_color is not None else False
        self.color_active = tuple(max(c - 40, 0) for c in color) if color is not None else None

        self.color = color

        self.hover_color = hover_color or (tuple(min(c + 30, 255) for c in color) if color is not None else None) 



    def add_child(self, component:"UIComponent"):
        component.parent = self
        component.ui_manager = self.ui_manager
        self.children.append(component)
        component.update_absolute_rect()
    
    def update_absolute_rect(self):
        if self.parent is not None:
            self.absolute_rect = (self.rect[0]+self.parent.absolute_rect[0],
                            self.rect[1]+self.parent.absolute_rect[1],
                            self.rect[2],
                            self.rect[3])
        else:
            self.absolute_rect = self.rect
    
        for child in self.children:
            child.update_absolute_rect()
    
    def set_pos(self,pos_x,pos_y):
        self.rect = (pos_x,pos_y,self.rect[2],self.rect[3])
        self.update_absolute_rect()    

    
    
    def handle_event(self, event):
        pass

    def on_hover(self, is_hover):
        self.hovered = is_hover

    def on_click(self,event):
        pass

    def on_focus(self):
        self.focused = True

    def on_blur(self):
        self.focused = False
    
    def draw_child(self, surface: pygame.Surface):
        for child in sorted(self.children, key=lambda c: c.z_index):
            child.draw(surface)

    def is_in_rect(self,pos):
        if self.absolute_rect[0]<pos[0] < self.absolute_rect[0]+self.absolute_rect[2] and \
            self.absolute_rect[1]<pos[1] < self.absolute_rect[1]+self.absolute_rect[3]:
            return True
        return False
    

    def set_hover(self,is_hover):
        if self.visible == False or self.enabled==False:
            return
        
        self.hovered = is_hover
        if is_hover == False:
            for child in self.children:
                child.set_hover(False)
        






    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        fill_color = self.color

        if not self.enabled:
            if fill_color is not None:
                fill_color = tuple(c // 2 for c in fill_color)

        elif self.active:
            if fill_color is not None:
                fill_color = self.color_active

        elif self.hovered:
            if fill_color is not None:
                fill_color = self.hover_color

        if fill_color is not None:    
            pygame.draw.rect(surface, fill_color, self.absolute_rect, 0)

        if self.show_border:
            border_color = self.color
            

            if self.focused:
                border_color =self.border_color
            pygame.draw.rect(surface, border_color, self.absolute_rect, 2)

        self.draw_child(surface)
    


        

