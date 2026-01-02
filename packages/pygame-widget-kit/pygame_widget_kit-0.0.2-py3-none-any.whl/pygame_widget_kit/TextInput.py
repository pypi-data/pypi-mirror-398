import pygame
from .UIComponent import UIComponent
from .Text import Text
import time

""" 
class TextInput2(UIComponent):
    def __init__(
        self,
        rect,
        initial_text="",
        text_color=(0, 0, 0),
        bg_color=(220, 220, 220),
        hover_color=(240, 240, 240),
        caret_color=(0, 0, 0),
        padding=6,
        z_index=0
    ):
        super().__init__(
            rect=rect,
            z_index=z_index,
            color=bg_color,
            hover_color=hover_color
        )

        self.text_value = initial_text
        self.text_color = text_color
        self.caret_color = caret_color
        self.padding = padding

        # Text child
        self.text = Text(
            text_str=self.text_value,
            pos=(self.padding, self.padding),
            text_color=self.text_color
        )
        self.add_child(self.text)

        # caret
        self.caret_visible = True
        self._caret_timer = 0
        self._caret_interval = 500  # ms
    def handle_event(self, event):
        if not self.enabled or not self.visible:
            return

        if event.type == pygame.KEYDOWN and self.focused:

            # ESC → blur
            if event.key == pygame.K_ESCAPE:
                if self.ui_manager:
                    self.ui_manager.focused = None
                self.on_blur()
                return

            # ENTER → blur (submit gibi düşünebilirsin)
            if event.key == pygame.K_RETURN:
                if self.ui_manager:
                    self.ui_manager.focused = None
                self.on_blur()
                return

            # BACKSPACE
            if event.key == pygame.K_BACKSPACE:
                self.text_value = self.text_value[:-1]

            # Printable characters
            else:
                if event.unicode and event.unicode.isprintable():
                    self.text_value += event.unicode

            self.text.set_text(self.text_value)
    def on_click(self, event):
        # sadece focus almak yeterli
        pass
    def update(self, dt):
        if not self.focused:
            self.caret_visible = False
            return

        self._caret_timer += dt
        if self._caret_timer >= self._caret_interval:
            self._caret_timer = 0
            self.caret_visible = not self.caret_visible
    def draw(self, surface: pygame.Surface):
        super().draw(surface)

        # caret sadece focused iken
        if self.focused and self.caret_visible:
            text_w, text_h = self.text.render.get_size()

            caret_x = (
                self.absolute_rect[0]
                + self.padding
                + text_w
            )
            caret_y = (
                self.absolute_rect[1]
                + self.padding
            )

            caret_rect = pygame.Rect(
                caret_x,
                caret_y,
                2,
                text_h
            )

            pygame.draw.rect(surface, self.caret_color, caret_rect)
    def get_value(self):
        return self.text_value

    def set_value(self, value: str):
        self.text_value = value
        self.text.set_text(value)

    def clear(self):
        self.set_value("")
 """



ALLOW_ALL_CHARS = 0
NUMBER_ONLY = 1
TEXT_ONLY = 2
HEX_ONLY = 3
BINARY_ONLY = 4
OCTAL_ONLY = 5



class TextInput(UIComponent):
    def __init__(
        self,
        rect,
        initial_text="",
        allowed_char_mode:int=0,
        text_color=(0, 0, 0),
        bg_color=(220, 220, 220),
        hover_color=(240, 240, 240),
        selection_color=(100, 150, 255),
        caret_color=(0, 0, 0),
        padding=6,
        z_index=0
    ):
        
        super().__init__(
            rect=rect,
            z_index=z_index,
            color=bg_color,
            hover_color=hover_color
        )

        self.text_value = initial_text
        self.text_color = text_color
        self.selection_color = selection_color
        self.caret_color = caret_color
        self.padding = padding
        self.allowed_char_mode=allowed_char_mode

        # text render
        self.text = Text(
            text_str=self.text_value,
            pos=(self.padding, self.padding),
            text_color=self.text_color
        )
        self.add_child(self.text)

        # caret & selection
        self.cursor_index = len(self.text_value)
        self.selection_start = None
        self.selection_end = None
        self.dragging = False

        # caret blink
        self.caret_visible = True
        self._caret_timer = 0
        self._caret_interval = 0.5
        self.last_blinked_at = time.time()

    
    def _mouse_to_index(self, mouse_x):
        local_x = mouse_x - self.absolute_rect[0] - self.padding
        if local_x <= 0:
            return 0

        for i in range(len(self.text_value) + 1):
            w = self.text.font.size(self.text_value[:i])[0]
            if local_x < w:
                return i

        return len(self.text_value)
    def on_click(self, event):
        self.dragging = True
        self.cursor_index = self._mouse_to_index(event.pos[0])
        self.selection_start = self.cursor_index
        self.selection_end = None


    def handle_event(self, event:pygame.Event):
        if not self.focused or not self.enabled:
            return

        # MOUSE DRAG SELECTION
        if event.type == pygame.MOUSEMOTION and self.dragging:
            idx = self._mouse_to_index(event.pos[0])
            self.selection_end = idx
            self.cursor_index = idx

        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            if self.selection_start == self.selection_end:
                self.selection_start = self.selection_end = None

        if event.type == pygame.KEYDOWN:

            # BACKSPACE
            if event.key == pygame.K_BACKSPACE:
                if self.has_selection():
                    self.delete_selection()
                elif self.cursor_index > 0:
                    self.text_value = (
                        self.text_value[:self.cursor_index - 1]
                        + self.text_value[self.cursor_index:]
                    )
                    self.cursor_index -= 1


            #arrow keys
            elif event.key == pygame.K_UP:
                self.cursor_index = 0
            elif event.key == pygame.K_DOWN:
                self.cursor_index = len(self.text_value)
            elif event.key == pygame.K_RIGHT:
                if self.cursor_index <len(self.text_value):
                    self.cursor_index+=1
            elif event.key == pygame.K_LEFT:
                if self.cursor_index > 0:
                    self.cursor_index-=1
            
            
            
            # NORMAL CHARACTER
            elif event.unicode and event.unicode.isprintable():
                c:str = event.unicode
                if self.allowed_char_mode == ALLOW_ALL_CHARS:
                    self.insert_text(c)
                elif self.allowed_char_mode == TEXT_ONLY:
                    if c.isnumeric() == False:
                        self.insert_text(c)
                elif self.allowed_char_mode == NUMBER_ONLY:
                    if c.isnumeric():
                        self.insert_text(c)
                elif self.allowed_char_mode == HEX_ONLY:
                    if c.isnumeric() or c.capitalize() in "ABCDEF":
                        self.insert_text(c)
                elif self.allowed_char_mode == BINARY_ONLY:
                    if c in "10":
                        self.insert_text(c)
                elif self.allowed_char_mode == OCTAL_ONLY:
                    if c in "12345678":
                        self.insert_text(c)
                
                
                

            

            self.text.set_text(self.text_value)


    def has_selection(self):
        return (
            self.selection_start is not None
            and self.selection_end is not None
            and self.selection_start != self.selection_end
        )

    def get_selection_range(self):
        return sorted((self.selection_start, self.selection_end))

    def get_selected_text(self):
        a, b = self.get_selection_range()
        return self.text_value[a:b]

    def delete_selection(self):
        a, b = self.get_selection_range()
        self.text_value = self.text_value[:a] + self.text_value[b:]
        self.cursor_index = a
        self.selection_start = self.selection_end = None

    def insert_text(self, s):
        if self.has_selection():
            self.delete_selection()

        self.text_value = (
            self.text_value[:self.cursor_index]
            + s
            + self.text_value[self.cursor_index:]
        )
        self.cursor_index += len(s)
    def update(self):
        if not self.focused:
            self.caret_visible = False
            return

        
        if time.time() - self.last_blinked_at >= self._caret_interval:
            self.last_blinked_at = time.time()
            self.caret_visible = not self.caret_visible

    def draw(self, surface):
        super().draw(surface)
        self.update()

        # SELECTION
        if self.has_selection():
            a, b = self.get_selection_range()
            x1 = self.absolute_rect[0] + self.padding + self.text.font.size(self.text_value[:a])[0]
            x2 = self.absolute_rect[0] + self.padding + self.text.font.size(self.text_value[:b])[0]

            h = self.text.render.get_height()
            y = self.absolute_rect[1] + self.padding

            pygame.draw.rect(
                surface,
                self.selection_color,
                (x1, y, x2 - x1, h)
            )

            # redraw text over selection
            self.text.draw(surface)

        # CARET
        if self.focused and self.caret_visible:
            cx = self.absolute_rect[0] + self.padding + self.text.font.size(
                self.text_value[:self.cursor_index]
            )[0]
            cy = self.absolute_rect[1] + self.padding

            pygame.draw.rect(
                surface,
                self.caret_color,
                (cx, cy, 2, self.text.render.get_height())
            )
