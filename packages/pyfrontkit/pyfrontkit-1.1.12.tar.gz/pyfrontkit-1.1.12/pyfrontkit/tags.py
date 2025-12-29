# Copyright (c) 2025 Eduardo Antonio Ferrera Rodríguez
# SPDX-License-Identifier: MIT
# pyfrontkit/tags.py

from .block import Block

# ============================================================
#            BLOCK SUBCLASSES
# ============================================================

class Div(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("div", *children, **kwargs)

class Section(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("section", *children, **kwargs)

class Article(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("article", *children, **kwargs)

class Header(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("header", *children, **kwargs)

class Footer(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("footer", *children, **kwargs)

class Nav(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("nav", *children, **kwargs)

class Main(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("main", *children, **kwargs)

class Aside(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("aside", *children, **kwargs)

class Button(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("button", *children, **kwargs)

class Form(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("form", *children, **kwargs)

class Ul(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("ul", *children, **kwargs)

class Li(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("li", *children, **kwargs)

class A(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("a", *children, **kwargs)        

class Video(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("video", *children, **kwargs)

class Audio(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("audio", *children, **kwargs)

class Picture(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("picture", *children, **kwargs)

class Object(Block):
    def __init__(self, *children, **kwargs):
        super().__init__("object", *children, **kwargs)


# ============================================================
#            TRANSPARENT TEXT BLOCK
# ============================================================

class T(Block):
    """
    Transparent block for textual content.
    Compatible with ctn_* kwargs and DOM.
    Does not generate its own tag.
    """

    def __init__(self, *children, **kwargs):
        super().__init__(tag="", *children, **kwargs)

        from .content import ContentFactory
        self.content_items = ContentFactory.create_from_kwargs(**kwargs)

        # Ignore children
        self.children = []

    def _render_opening_tag(self, indent: int) -> str:
        return ""

    def _render_closing_tag(self, indent: int) -> str:
        return ""


class Label(Block):
    def __init__(self, *children, **kwargs):
        # Si el usuario pasa for_ lo normalizamos antes de subir al padre
        if "for_" in kwargs:
            kwargs["for"] = kwargs.pop("for_")
        super().__init__("label", *children, **kwargs)

    def reveal(self, target_id, direction="top", duration="0.4s"):
        """
        Implements the 'Checkbox Hack' to toggle the visibility of a target element.
        
        This method automatically creates a hidden input and links it to the current 
        label using the 'for' attribute. It also generates the necessary CSS rules 
        to handle smooth transitions and state changes based on the checkbox status.

        Args:
            target_id (str): The HTML 'id' of the element to be revealed.
            direction (str): The entry animation direction ('top', 'bottom', 'left', 'right', 'fade').
            duration (str): CSS transition time (e.g., '0.4s').

        Returns:
            self: The current Label instance for method chaining.
        """
        
        # 1. Ensure the Label has a unique ID for precise CSS targeting
        label_id = self.attrs.get('id')
        if not label_id:
            # Generate a fallback ID based on the object's memory address if not provided
            label_id = f"lbl_auto_{id(self)}"
            self.attrs["id"] = label_id

        # 2. Setup the hidden Checkbox engine
        # The connection between Label and Input is established via the 'for' attribute
        check_id = f"chk_{target_id}"
        self.attrs["for"] = check_id
        
        # 3. Register the technical Input in the DOM
        # Attempt to import Input from void element definitions
        try:
            from .void import Input
        except ImportError:
            from .void_tags import Input
            
        # Create the technical checkbox that stores the toggle state
        chk = Input(type="checkbox", id=check_id)
        
        # Inject the input at the beginning of the registry to ensure it precedes
        # the target in the DOM, allowing the CSS general sibling selector (~) to work.
        from .block import Block
        Block._registry.insert(0, chk) 

        # 4. Define CSS Selectors and Animation logic
        target_selector = f"#{target_id}"
        
        # Dictionary mapping directions to initial CSS transform offsets
        moves = {
            "top": "translateY(-20px)",
            "bottom": "translateY(20px)",
            "left": "translateX(-20px)",
            "right": "translateX(20px)",
            "fade": "scale(0.95)"
        }
        
        initial_transform = moves.get(direction, "none")

        # Define the base (hidden) state for the target element
        base_css = (
            f"opacity: 0; visibility: hidden; "
            f"transform: {initial_transform}; "
            f"transition: all {duration} ease-in-out;"
        )
        
        # Define the active (visible) state triggered by the :checked pseudo-class
        active_css = (
            "opacity: 1 !important; "
            "visibility: visible !important; "
            "transform: translate(0,0) !important;"
        )
        
        # 5. Save styles to the global Style Manager
        from .style_manager import CSS_RULES_STYLE
        
        # Set the initial hidden state for the target
        CSS_RULES_STYLE.append({target_selector: {"css": base_css}})
        
        # Create the logic: "If checkbox is checked, modify target siblings or descendants"
        # Sibling selector case
        CSS_RULES_STYLE.append({f"#{check_id}:checked ~ {target_selector}": {"css": active_css}})
        # Deep descendant selector case (if target is nested)
        CSS_RULES_STYLE.append({f"#{check_id}:checked ~ * {target_selector}": {"css": active_css}})
        
        # Ensure the technical checkbox is never visible to the user
        CSS_RULES_STYLE.append({f"#{check_id}": {"css": "display: none !important;"}})

        return self
# ============================================================
#            FUNCTION ALIASES FOR FREE SYNTAX
# ============================================================

def div(*children, **kwargs):
    return Div(*children, **kwargs)

def section(*children, **kwargs):
    return Section(*children, **kwargs)

def article(*children, **kwargs):
    return Article(*children, **kwargs)

def header(*children, **kwargs):
    return Header(*children, **kwargs)

def footer(*children, **kwargs):
    return Footer(*children, **kwargs)

def nav(*children, **kwargs):
    return Nav(*children, **kwargs)

def main(*children, **kwargs):
    return Main(*children, **kwargs)

def aside(*children, **kwargs):
    return Aside(*children, **kwargs)

def button(*children, **kwargs):
    return Button(*children, **kwargs)

def form(*children, **kwargs):
    return Form(*children, **kwargs)

def ul(*children, **kwargs):
    return Ul(*children, **kwargs)

def li(*children, **kwargs):
    return Li(*children, **kwargs)

def a(*children, **kwargs):
    return A(*children, **kwargs)

def video(*children, **kwargs):
    return Video(*children, **kwargs)

def audio(*children, **kwargs):
    return Audio(*children, **kwargs)

def picture(*children, **kwargs):
    return Picture(*children, **kwargs)

def object(*children, **kwargs):
    return Object(*children, **kwargs)

def t(*children, **kwargs):
    return T(*children, **kwargs)

def label(*children, **kwargs):
    return Label(*children, **kwargs)
