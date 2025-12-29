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
        """
        Label component that abstracts the HTML <label> tag.
        Normalizes 'for_' attribute to 'for'.
        """
        if "for_" in kwargs:
            kwargs["for"] = kwargs.pop("for_")
        super().__init__("label", *children, **kwargs)

    def reveal(self, target_id, direction="top", duration="0.4s"):
        """
        Implements a professional 'reveal' effect using the Checkbox Hack.
        
        This method automates the creation of a hidden state-control input and 
        generates the necessary CSS rules to show/hide a target element by its ID.

        Args:
            target_id (str): The ID of the block to be toggled.
            direction (str): Animation starting point ('top', 'bottom', 'left', 'right', 'fade').
            duration (str): Speed of the transition (e.g., '0.3s').

        Returns:
            self: The Label instance for further method chaining.
        """
        
        # 1. Identity management
        # Ensure the label has an ID for CSS specificity
        label_id = self.attrs.get('id')
        if not label_id:
            label_id = f"lbl_auto_{id(self)}"
            self.attrs["id"] = label_id

        # 2. State Engine (The hidden checkbox)
        # We link the label to this checkbox via the 'for' attribute
        check_id = f"chk_{target_id}"
        self.attrs["for"] = check_id
        
        # 3. Component Registration
        # Importing from your specific void_element.py file
        try:
            from .void_element import Input
        except ImportError:
            # Fallback if the class is mapped differently
            from .void_element import Input_ as Input
            
        # Create the technical checkbox that will hold the toggle state
        chk = Input(type="checkbox", id=check_id)
        
        # We insert the checkbox at the beginning of the registry to ensure
        # it is a preceding sibling of the target in the final HTML.
        from .block import Block
        Block._registry.insert(0, chk) 

        # 4. CSS Logic Construction
        target_selector = f"#{target_id}"
        
        # Animation offset presets
        moves = {
            "top": "translateY(-20px)",
            "bottom": "translateY(20px)",
            "left": "translateX(-20px)",
            "right": "translateX(20px)",
            "fade": "scale(0.95)"
        }
        
        initial_transform = moves.get(direction, "none")

        # Hidden state (Base)
        base_css = (
            f"opacity: 0; "
            f"visibility: hidden; "
            f"transform: {initial_transform}; "
            f"transition: all {duration} ease-in-out;"
        )
        
        # Visible state (Triggered by :checked)
        active_css = (
            "opacity: 1 !important; "
            "visibility: visible !important; "
            "transform: translate(0,0) !important;"
        )
        
        # 5. Global Style Injection
        from .style_manager import CSS_RULES_STYLE
        
        # Set target to be hidden by default
        CSS_RULES_STYLE.append({target_selector: {"css": base_css}})
        
        # Rule: When checkbox is checked, reveal target (sibling or descendant of sibling)
        CSS_RULES_STYLE.append({f"#{check_id}:checked ~ {target_selector}": {"css": active_css}})
        CSS_RULES_STYLE.append({f"#{check_id}:checked ~ * {target_selector}": {"css": active_css}})
        
        # Hide the technical checkbox itself from the UI
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
