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

    def reveal(self, target, direction="top", duration="0.4s"):
        """
        Activa un menú o contenedor oculto usando el ID del target.
        """
        # 1. Asegurar IDs
        target_id = target.attrs.get('id')
        if not target_id:
            raise ValueError("El target del reveal necesita un id obligatorio.")

        # 2. El Checkbox invisible (El motor)
        check_id = f"chk_{target_id}"
        self.attrs["for"] = check_id
        
        # 3. Importar Input y registrarlo
        from .tags import Input
        chk = Input(type="checkbox", id=check_id)
        # Lo metemos al principio del registro para que el selector '~' lo encuentre
        self._registry.insert(0, chk) 

        # 4. Los estilos (Usando tu lógica de form)
        selector, _ = target._get_main_selector()
        
        # Diccionario de movimientos
        moves = {
            "top": "translateY(-20px)",
            "bottom": "translateY(20px)",
            "left": "translateX(-20px)",
            "right": "translateX(20px)",
            "fade": "scale(0.95)" # Un pequeño efecto de zoom en lugar de mover
        }
        
        # Estilo Base
        base_css = (
            f"opacity: 0; visibility: hidden; "
            f"transform: {moves.get(direction, 'none')}; "
            f"transition: all {duration} ease;"
        )
        
        # Estilo Activo (Checked)
        active_css = "opacity: 1; visibility: visible; transform: translate(0,0);"
        
        # Guardar en CSS_RULES_STYLE
        from .style_manager import CSS_RULES_STYLE
        CSS_RULES_STYLE.append({selector: {"css": base_css}})
        CSS_RULES_STYLE.append({f"#{check_id}:checked ~ {selector}": {"css": active_css}})
        # Esconder el checkbox
        CSS_RULES_STYLE.append({f"#{check_id}": {"css": "display: none;"}})

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
