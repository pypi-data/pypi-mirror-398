from __future__ import annotations

########## Copyright (c) ##########################################################
# SPDX-FileCopyrightText: 2025 Antonio Castro Snurmacher <acastro0841@gmail.com>
# SPDX-License-Identifier: MIT
###################################################################################

"""
######################################################################################################################
Programa  : help_core.py
Versión   : 2.0  (22-nov-2025)
Licencia de uso MIT

Descripción breve:
    Visor de ayuda independiente, basado únicamente en Pygame, con soporte de Markdown reducido.

Descripción detallada:
    Permite visualizar en una pantalla un texto de ayuda en formato markdown.
     - Sin dependencias de PopupDialogWindow ni de tu GUI.
     - Puede abrir su propia ventana (open_window) o renderizar en una surface/rect.
     - Estilos opcionales vía JSON + variant y/o style_overrides.

LIMITACIONES:
    Es un diseño basado en un subconjunto de Markdown. Dicho subconjunto está descrito en help_core_api_uso.md.
    Dicho diseño cubre los elementos más necesarios para poder ofrecer una visualización bien estructurada
    de la información.

Uso:
    Veasé la documentación: help_core_api_uso.md,  help_core_chuleta_rapida.md,  help_core_doc_actualizado.md

Requisitos:
    - Python 3.11
    - Pygame
######################################################################################################################
"""

"""
-----------------------------------------------------------------------------
_MiniMarkdown – Lenguaje soportado (Markdown reducido)
-----------------------------------------------------------------------------
Configuración:
  - tab_size (int): nº de espacios que sustituye a cada tabulador en normalize().
  - max_list_nesting (int): profundidad máxima de indentación para listas.
      *Internamente los niveles van de 0 a (max_list_nesting - 1).*
  - indent_per_level_spaces (int): nº de espacios que equivalen a 1 nivel de
      indentación para listas (PARSEO, no px en render).
#
Normalización:
  - normalize(text):
      · Reemplaza '\\t' por ' ' * tab_size.
      · Convierte CRLF/CR a LF.
    (parse() NO llama a normalize() automáticamente; úsala si necesitas unificar saltos/tabs.)
#
BLOQUES SOPORTADOS
------------------
1) Regla horizontal
   Sintaxis: una línea que contenga exactamente tres guiones (con o sin espacios alrededor)
      --- 
   Regex: r'^\\s*---\\s*$'
   Emite: {"type": "hr"}
#
2) Encabezados (h1..h6)
   Sintaxis: '# ' | '## ' | ... | '###### ' seguido del texto del título
      # Título 1
      ## Título 2
      ...
      ###### Título 6
   Regex: r'^(#{1,6})\\s+(.*)$'
   Emite: {"type": "h1"|...|"h6", "text": "..."}
#
3) Bloques de código "fence"
   Sintaxis: líneas con ``` para abrir/cerrar. No se detecta lenguaje.
      ```
      cualquier texto (se preserva tal cual, incluidas líneas vacías)
      ```
   Regex apertura/cierre: r'^\\s*```.*$'
   Emite: {"type": "code", "text": "<contenido tal cual>"}
   Nota: si el EOF llega con fence abierto, también se emite como bloque de código.
#
4) Bloques de código indentado  (DESACTIVADO EN ESTA IMPLEMENTACIÓN)
   En esta implementación se ha desactivado la detección automática de
   "bloques de código indentado" (líneas que comienzan con 4 espacios)
   porque:

     - pandoc genera listas con líneas de continuación sangradas con
       cuatro espacios (no son bloques de código reales).
     - Eso producía parches blancos indeseados en la ayuda al tratar
       esas líneas de continuación como código.

   Recomendación: generar el manual con pandoc usando fences ``` para
   los bloques de código reales y evitar confiar en indentaciones para
   indicar código.

   En consecuencia, actualmente no se emiten bloques de tipo "code"
   basados en indentación; los bloques de código se obtienen sólo a
   partir de fences ``` (ver sección 3).
#
5) Listas
   • Listas no ordenadas (UL):
        - Item uno
        * Item dos
      Regex: r'^(\\s*)([-*])\\s+(.*)$'
      Emite: {"type": "ul", "items": [{"level": L, "text": "..."} ...]}
#
   • Listas ordenadas (OL):
        1. Primer item
        2. Segundo item
      Regex: r'^(\\s*)(\\d+)\\.\\s+(.*)$'
      Emite: {"type": "ol", "items": [{"level": L, "num": N, "text": "..."} ...]}
#
   Nivel de indentación en ambos casos:
      L = min( len(espacios_previos) // indent_per_level_spaces,
               max_list_nesting - 1 )
     (No se parsean subpárrafos dentro de items; solo se acumulan líneas consecutivas
      que sigan siendo del mismo tipo de lista. No hay checkboxes, blockquotes ni imágenes.)
#
6) Párrafos
   Cualquier bloque de líneas consecutivas que no encaje en las reglas anteriores,
   separado por líneas en blanco. Se emite con saltos '\\n' internos si los hay.
   Emite: {"type": "p", "text": "..."}
#
ORDEN DE DETECCIÓN DE BLOQUES en parse():
  1) Saltos de línea vacíos (se ignoran entre bloques, excepto dentro de fence)
  2) Fence ```
  3) (Si in_fence) → acumular literal
  4) Regla horizontal (---)
  5) Encabezados (#..######)
  6) Código indentado (≥4 espacios)
  7) Listas (UL/OL)
  8) Párrafo
#
INLINE (tokenize_inline)
------------------------
1) Código en línea
   Sintaxis: `contenido`
   Regex: r'`([^`]+)`'
   Comportamiento:
     - Se "protege" primero: el contenido de `...` NO se procesa para negrita/itálica/links.
   Emite runs con: {"text": "...", code: True, bold: False, italic: False, link: False}
#
2) Énfasis
   • Negrita+itálica: ***texto***
      Regex: r'(?<!\\w)\\*\\*\\*(.+?)\\*\\*\\*(?!\\w)'
   • Negrita: **texto**
      Regex: r'(?<!\\w)\\*\\*(.+?)\\*\\*(?!\\w)'
   • Itálica: *texto*
      Regex: r'(?<!\\w)\\*(.+?)\\*(?!\\w)'
#
   Notas importantes:
     - Se aplican en este orden: *** → ** → *
     - Se exigen límites de “no-palabra” en ambos lados (negative lookbehind/ahead con \\w):
         · 'precio*2' NO activa itálica
         · '**negrita**,' SÍ (la coma no rompe el match)
     - Flags resultantes por run:
         · bold = True si (b OR bi)
         · italic = True si (i OR bi)
#
3) URLs
   Sintaxis: http://... o https://... (sin corchetes)
   Regex: r'(https?://\\S+)'
   Comportamiento:
     - Se marcan como link=True (y code=False).
     - Dentro de `code` NO se linka.
     - Nota: \\S+ captura hasta el siguiente espacio; si hay puntuación pegada
             al final (p. ej. una coma), se incluirá en el enlace.
#
Salida de tokenize_inline(text) → List[run]
   Cada run es un dict con claves:
     { "text": str, "bold": bool, "italic": bool, "code": bool, "link": bool }
#
LIMITACIONES/Diseño intencionado:
  - Títulos solo h1..h6.
  - No hay blockquotes, imágenes, tablas, ni enlaces estilo [texto](url).
  - Items de lista: solo texto plano por línea; no hay subbloques dentro del item.
  - El análisis inline no se realiza dentro de bloques de código (fence o indentado).
  - Los "límites de palabra" para * ** *** evitan falsos positivos dentro de tokens alfanuméricos.
-----------------------------------------------------------------------------

"""


"""NOTA1:
La instrucción from __future__ import annotations en Python 3.12 sirve para habilitar la evaluación diferida de las 
anotaciones de tipo. Esto significa que, en lugar de evaluar las anotaciones en el momento en que se define una 
función o clase, se evalúan como cadenas de texto (strings). Esta característica es útil para evitar problemas con 
referencias circulares y para permitir que las anotaciones hagan referencia a nombres que aún no se han definido

NOTA2:
Se puede generar un fichero con LibreOffice y pasarlo a formato markdown luego con:
    pandoc archivo.odt -t markdown -o archivo.md
"""

import os
import re
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import pygame

RGB = Tuple[int, int, int]

DEFAULT_STYLE: Dict[str, Any] = {
    "hlp_BaseFontSize": 20,
    "hlp_H1Size": 38, 
    "hlp_H2Size": 33, 
    "hlp_H3Size": 29,
    "hlp_H4Size": 26, 
    "hlp_H5Size": 24, 
    "hlp_H6Size": 22,
    "hlp_ColorText": (20, 20, 24),
    "hlp_ColorMuted": (90, 90, 100),
    "hlp_ColorLink": (30, 100, 200),
    "hlp_ColorCodeText": (30, 30, 34),
    # Fondo de bloques de código → BLANCO (petición)
    "hlp_ColorCodeBg": (255, 255, 255),
    "hlp_ColorRule": (111, 111, 111),
    "hlp_ColorScrollbarTrack": (180, 180, 180),
    "hlp_ColorScrollbarThumb": (80, 80, 120),
    # Fondo general del panel → gris claro (petición)
    "hlp_ColorPanelBg": (188, 188, 188),
    "hlp_ParaSpacing": 8, "hlp_ListSpacing": 8,
    "hlp_H1SpacingTop": 16, "hlp_H1SpacingBottom": 12,
    "hlp_H2SpacingTop": 12, "hlp_H2SpacingBottom": 8,
    "hlp_H3SpacingTop": 10, "hlp_H3SpacingBottom": 6,
    # ↓↓↓ Espaciados añadidos para h4..h6 (suaves)
    "hlp_H4SpacingTop": 8,  "hlp_H4SpacingBottom": 6,
    "hlp_H5SpacingTop": 6,  "hlp_H5SpacingBottom": 4,
    "hlp_H6SpacingTop": 6,  "hlp_H6SpacingBottom": 4,
    "hlp_IndentPerLevelPx": 24,   # píxeles de indentación por nivel (render)
    "hlp_WheelStep": 48,
    "hlp_BorderRadius": 8,
    "hlp_Padding": 16,
    "hlp_CodeBlockPad": 8,
    "hlp_LineHeightPct": 120,
    "hlp_CodeFontSize": 18,  # tamaño de fuente para código (inline y bloque)
    # Opcionales (si se definen, prevalecen sobre el cálculo por espacios):
    # "hlp_PaddingLeft":  ..., "hlp_PaddingRight": ...
}

@dataclass
class HelpConfig:
    md_text: str
    title: str = "Ayuda"
    size: Tuple[int, int] = (800, 480)

    # Parser / composición
    tab_size: int = 4
    max_list_nesting: int = 6
    indent_spaces_per_level: int = 2   # espacios que equivalen a un nivel (parseo)
    visual_indent_px: int = 24         # píxeles por nivel (render)

    # Interacción
    wheel_step: int = 48
    # Callback opcional para notificar que se ha alcanzado el límite de scroll
    # direction: "top" o "bottom".
    on_scroll_limit: Optional[Callable[[str], None]] = None
    # Tiempo mínimo en milisegundos entre llamadas a on_scroll_limit (0 = sin límite).
    scroll_limit_cooldown_ms: int = 0


    # Estilos
    style_json_path: Optional[str] = None
    style_variant: Optional[str] = None
    style_overrides: Optional[Dict[str, Any]] = None
    fonts_dir: Optional[str] = None     # directorio de TTF (si se usa)
    help_font_file: Optional[str] = None       # nombre TTF para texto normal
    help_code_font_file: Optional[str] = None  # nombre TTF para monoespaciada

    # Fondo del kernel (si quieres sobreescribir)
    kernel_bg: Optional[RGB] = None


# ---------------------------------------------------------------------------
# Parser de Markdown reducido con límites de palabra
# ---------------------------------------------------------------------------
class _MiniMarkdown:
    """
    #, ##, ###, ####, #####, ###### → títulos
    --- → línea horizontal
    - / * → lista viñetas, 1. → lista numerada
    Bloques de código: … o 4 espacios
    Énfasis: *itálica*, **negrita**, ***ambas***
    `inline code`
    URLs http://...
    Bloques de código "fence"  con ``` para abrir/cerrar. No se detecta lenguaje
    (No hay imágenes, tablas ni enlaces con [texto](url))
    """
    def __init__(self, tab_size: int = 4, max_list_nesting: int = 4, indent_per_level_spaces: int = 2):
        self.tab_size = max(1, int(tab_size))
        self.max_list_nesting = max(1, int(max_list_nesting))
        # nº de espacios que equivalen a 1 nivel en PARSEO (no px en render)
        self.spaces_per_level = max(1, int(indent_per_level_spaces))

        # Bloques
        self._re_hr     = re.compile(r"^\s*---\s*$")
        # Ampliamos encabezados a 1..6 almohadillas (petición)
        self._re_h      = re.compile(r"^(#{1,6})\s+(.*)$")
        self._re_ul     = re.compile(r"^(\s*)([-*])\s+(.*)$")
        self._re_ol     = re.compile(r"^(\s*)(\d+)\.\s+(.*)$")
        self._re_fence  = re.compile(r"^\s*```.*$")

        # Inline:
        # Para ***texto*** relajamos los límites de palabra para evitar que se
        # rompa en casos donde va pegado a otras palabras; ** y * mantienen
        # los límites para evitar falsos positivos tipo "precio*2".
        self._re_bold_italic = re.compile(r"\*\*\*(.+?)\*\*\*")
        self._re_bold        = re.compile(r"(?<!\w)\*\*(.+?)\*\*(?!\w)")
        self._re_italic      = re.compile(r"(?<!\w)\*(.+?)\*(?!\w)")

        self._re_inline_code = re.compile(r"`([^`]+)`")
        self._re_url         = re.compile(r"(https?://\S+)")

    def normalize(self, text: str) -> str:
        return text.replace("\t", " " * self.tab_size).replace("\r\n", "\n").replace("\r", "\n")

    def parse(self, text: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        lines = text.split("\n")
        n = len(lines)
        i = 0
        in_fence = False
        fence_buf: List[str] = []

        while i < n:
            line = lines[i]

            # Saltar vacías entre bloques (pero no dentro de fence)
            if not in_fence and line.strip() == "":
                i += 1
                continue

            # Fence ```
            if self._re_fence.match(line):
                if not in_fence:
                    in_fence = True
                    fence_buf = []
                else:
                    out.append({"type": "code", "text": "\n".join(fence_buf)})
                    in_fence = False
                i += 1
                continue

            if in_fence:
                fence_buf.append(line)  # ← dentro del fence, preservamos TODO, incluidas líneas vacías
                i += 1
                continue

            # Regla horizontal
            if self._re_hr.match(line):
                out.append({"type": "hr"})
                i += 1
                continue

            # Encabezados (ahora h1..h6)
            mh = self._re_h.match(line)
            if mh:
                level = len(mh.group(1))
                out.append({"type": f"h{level}", "text": mh.group(2).strip()})
                i += 1
                continue


            # ----------------------------------------------------------------------
            # >>> Eliminada la regla: "Si empieza con 4 espacios → bloque de código"
            # (Se conserva el comentario para documentación, pero no se aplica.)


            # Listas
            mul = self._re_ul.match(line)
            mol = self._re_ol.match(line)
            if mul or mol:
                kind = "ul" if mul else "ol"
                items: List[Dict[str, Any]] = []
                while i < n:
                    cur = lines[i]
                    m = (self._re_ul.match(cur) if kind == "ul" else self._re_ol.match(cur))
                    if not m:
                        break
                    indent_spaces = len(m.group(1))
                    level = min(indent_spaces // self.spaces_per_level, self.max_list_nesting - 1)
                    if kind == "ul":
                        text_item = m.group(3).strip()
                        items.append({"level": level, "text": text_item})
                    else:
                        num = int(m.group(2))
                        text_item = m.group(3).strip()
                        items.append({"level": level, "num": num, "text": text_item})
                    i += 1
                out.append({"type": kind, "items": items})
                continue

            # Párrafo
            para = [line]
            i += 1
            while i < n and lines[i].strip() != "" and not self._re_h.match(lines[i]) \
                  and not self._re_hr.match(lines[i]) and not lines[i].startswith("    ") \
                  and not self._re_ul.match(lines[i]) and not self._re_ol.match(lines[i]) \
                  and not self._re_fence.match(lines[i]):
                para.append(lines[i])
                i += 1
            # Saltar separadores vacíos entre párrafos
            while i < n and lines[i].strip() == "":
                i += 1
            text_p = "\n".join(para).strip()
            if text_p:
                out.append({"type": "p", "text": text_p})

        # Fence sin cierre al EOF → se considera bloque de código
        if in_fence and fence_buf:
            out.append({"type": "code", "text": "\n".join(fence_buf)})

        # Fence sin cierre al EOF → se considera bloque de código
        if in_fence and fence_buf:
            out.append({"type": "code", "text": "\n".join(fence_buf)})

        return out

    def tokenize_inline(self, text: str) -> List[Dict[str, Any]]:
        runs: List[Dict[str, Any]] = []

        # proteger inline code
        parts: List[Tuple[str, bool]] = []
        last = 0
        for m in self._re_inline_code.finditer(text):
            if m.start() > last:
                parts.append((text[last:m.start()], False))
            parts.append((m.group(1), True))
            last = m.end()
        if last < len(text):
            parts.append((text[last:], False))

        def emit_plain(seg: str) -> None:
            # *** → ** → *
            base: List[Tuple[str, Dict[str, bool]]] = [(seg, {})]

            def apply(regex, flag, incoming):
                out = []
                for chunk, attrs in incoming:
                    if attrs:
                        out.append((chunk, attrs))
                        continue
                    pos = 0
                    for m in regex.finditer(chunk):
                        if m.start() > pos:
                            out.append((chunk[pos:m.start()], {}))
                        out.append((m.group(1), {flag: True}))
                        pos = m.end()
                    if pos < len(chunk):
                        out.append((chunk[pos:], {}))
                return out

            base = apply(self._re_bold_italic, "bi", base)
            base = apply(self._re_bold, "b", base)
            base = apply(self._re_italic, "i", base)

            for txt, flags in base:
                if not txt:
                    continue
                runs.append({
                    "text": txt,
                    "bold": bool(flags.get("b") or flags.get("bi")),
                    "italic": bool(flags.get("i") or flags.get("bi")),
                    "code": False,
                    "link": False
                })

        for seg, is_code in parts:
            if is_code:
                runs.append({"text": seg, "bold": False, "italic": False, "code": True, "link": False})
            else:
                emit_plain(seg)

        # URLs
        final: List[Dict[str, Any]] = []
        for r in runs:
            if r["code"] or not r["text"]:
                final.append(r)
                continue
            txt = r["text"]
            pos = 0
            for m in self._re_url.finditer(txt):
                if m.start() > pos:
                    final.append({**r, "text": txt[pos:m.start()], "link": False})
                final.append({**r, "text": m.group(1), "link": True, "code": False})
                pos = m.end()
            if pos < len(txt):
                final.append({**r, "text": txt[pos:], "link": False})
        return final


# ---------------------------------------------------------------------------
# Visor de ayuda (standalone o embebido)
# ---------------------------------------------------------------------------
class HelpViewer:
    def __init__(self, cfg: HelpConfig):
        self.cfg = cfg
        self.style = self._load_style(cfg)
        self.kernel_bg: RGB = cfg.kernel_bg or tuple(self.style.get("Krn_ColorBg", self.style["hlp_ColorPanelBg"]))  # type: ignore

        self.parser = _MiniMarkdown(
            tab_size=cfg.tab_size,
            max_list_nesting=cfg.max_list_nesting,
            indent_per_level_spaces=cfg.indent_spaces_per_level
        )

        # Estado/layout
        self._rect_abs: Optional[pygame.Rect] = None
        self._w = 0
        self._h = 0
        self._content_height = 0
        self._scroll = 0
        self._dragging = False
        self._drag_start_y = 0
        self._scroll_start = 0

        # Cooldown para notificaciones de límite de scroll
        self._last_scroll_limit_ms: int = 0

        # Fuentes
        self._fonts: Dict[str, pygame.font.Font] = {}
        self._fonts_code: Dict[str, pygame.font.Font] = {}

        # Documento parseado + líneas compuestas
        normalized = self.parser.normalize(cfg.md_text)
        self._blocks: List[Dict[str, Any]] = self.parser.parse(normalized)
        self._lines: List[Dict[str, Any]] = []


    # ----------- Notify Scroll Limit -----------------
    def _notify_scroll_limit(self, where: str) -> None:
        """Lanza el callback de límite de scroll respetando el cooldown configurado."""
        if self.cfg.on_scroll_limit is None:
            return

        cooldown_ms = self.cfg.scroll_limit_cooldown_ms
        if cooldown_ms <= 0:
            self.cfg.on_scroll_limit(where)
            return

        now_ms: int = pygame.time.get_ticks()
        if self._last_scroll_limit_ms > 0:
            elapsed: int = now_ms - self._last_scroll_limit_ms
            if elapsed < cooldown_ms:
                return

        self._last_scroll_limit_ms = now_ms
        self.cfg.on_scroll_limit(where)


    # ---------- Standalone ----------
    def open_window(self) -> None:
        """Abre su propia ventana pygame y muestra la ayuda (sin PopupWindow)."""
        pygame.init()
        screen = pygame.display.set_mode(self.cfg.size)
        pygame.display.set_caption(self.cfg.title)
        clock = pygame.time.Clock()

        # Estado previo de ratón y autorepetición de teclas
        prev_mouse_visible: bool = pygame.mouse.get_visible()
        prev_key_delay, prev_key_interval = pygame.key.get_repeat()

        # Para el modo standalone queremos ver siempre el cursor y permitir autorepeat
        pygame.mouse.set_visible(True)
        pygame.key.set_repeat(250, 40)

        # Montaje virtual usando toda la ventana como rect útil
        rect = screen.get_rect()
        self.on_mount(rect)

        try:
            running = True
            while running:
                dt = clock.tick(60)
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        running = False
                    elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        self.handle_event(e)

                screen.fill((0, 0, 0))
                self.draw(screen, rect)
                pygame.display.flip()
        finally:
            self.on_unmount()

            # Restaurar autorepetición previa
            if prev_key_delay == 0 and prev_key_interval == 0:
                pygame.key.set_repeat()
            else:
                pygame.key.set_repeat(prev_key_delay, prev_key_interval)

            # Restaurar visibilidad previa del ratón
            pygame.mouse.set_visible(prev_mouse_visible)

            pygame.quit()

    # ---------- Embebido (surface/rect dados) ----------
    def on_mount(self, rect: pygame.Rect) -> None:
        self._rect_abs = rect.copy()
        self._w, self._h = rect.width, rect.height
        self._ensure_fonts()
        self._compose_all()
        self._scroll = 0

    def on_unmount(self) -> None:
        self._rect_abs = None
        self._w = self._h = 0
        self._lines.clear()
        self._blocks.clear()

    def wants_keyboard(self) -> bool: return True

    def wants_wheel(self) -> bool: return True

    # ---- Gestión de eventos -------------------------------------
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self._rect_abs:
            return False

        if event.type == pygame.MOUSEWHEEL:
            step = int(self.style["hlp_WheelStep"])
            max_scroll = max(0, self._content_height - self._h)
            old_scroll = self._scroll

            if event.y > 0:
                target = self._scroll - step
            elif event.y < 0:
                target = self._scroll + step
            else:
                return False

            if target < 0:
                new_scroll = 0
            elif target > max_scroll:
                new_scroll = max_scroll
            else:
                new_scroll = target

            self._scroll = new_scroll

            if self._scroll == old_scroll:
                if old_scroll <= 0:
                    where = "top"
                else:
                    where = "bottom"
                self._notify_scroll_limit(where)

            return True



        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._content_height > self._h:
                track = self._scrollbar_rect()
                if track.collidepoint(event.pos):
                    thumb = self._thumb_rect(track)
                    if thumb.collidepoint(event.pos):
                        self._dragging = True
                        self._drag_start_y = event.pos[1]
                        self._scroll_start = self._scroll
                        return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging:
                self._dragging = False
                return True


        if event.type == pygame.MOUSEMOTION and self._dragging:
            track = self._scrollbar_rect()
            thumb = self._thumb_rect(track)
            dy = event.pos[1] - self._drag_start_y
            track_space = track.height - thumb.height

            if track_space > 0:
                max_scroll = max(0, self._content_height - self._h)
                old_scroll = self._scroll

                frac = dy / float(track_space)
                raw_pos = self._scroll_start + frac * max_scroll

                hit_limit = False
                where = ""

                if raw_pos < 0:
                    new_scroll = 0
                    # Solo consideramos “intento de rebasar” si ya estábamos en el tope
                    if old_scroll <= 0:
                        hit_limit = True
                        where = "top"
                elif raw_pos > max_scroll:
                    new_scroll = max_scroll
                    # Igual para el límite inferior
                    if old_scroll >= max_scroll:
                        hit_limit = True
                        where = "bottom"
                else:
                    # Dentro de los límites: no hay intento de rebasar, aunque
                    # por redondeo new_scroll pueda coincidir con old_scroll.
                    new_scroll = int(raw_pos)

                self._scroll = new_scroll

                if hit_limit and where:
                    self._notify_scroll_limit(where)

            return True

        if event.type == pygame.KEYDOWN:
            step = int(self.style["hlp_WheelStep"])
            max_scroll = max(0, self._content_height - self._h)

            old_scroll = self._scroll
            wanted: Optional[int] = None

            if event.key == pygame.K_UP:
                wanted = self._scroll - step // 2
            elif event.key == pygame.K_DOWN:
                wanted = self._scroll + step // 2
            elif event.key == pygame.K_PAGEUP:
                wanted = self._scroll - self._h + step // 2
            elif event.key == pygame.K_PAGEDOWN:
                wanted = self._scroll + self._h - step // 2
            elif event.key == pygame.K_HOME:
                wanted = 0
            elif event.key == pygame.K_END:
                wanted = max_scroll

            if wanted is None:
                return False

            # Aplicar límite superior/inferior de forma explícita
            if wanted < 0:
                new_scroll = 0
            elif wanted > max_scroll:
                new_scroll = max_scroll
            else:
                new_scroll = wanted

            self._scroll = new_scroll

            if self._scroll == old_scroll:
                if old_scroll <= 0:
                    where = "top"
                else:
                    where = "bottom"
                self._notify_scroll_limit(where)

            return True

        return False



    def update(self, dt_ms: int) -> None:
        pass


    def _font_for(self, font_key: str) -> pygame.font.Font:
        """Devuelve la fuente asociada a un rol lógico de texto.

        Se consulta primero la tabla de fuentes proporcionales, luego la de
        fuentes monoespaciadas; si no se encuentra ninguna, se usa la fuente
        de párrafo como último recurso.
        """
        font = self._fonts.get(font_key) or self._fonts_code.get(font_key)
        if font is None:
            # Fallback razonable: evita reventar por un font_key raro y
            # mantiene legibilidad usando la fuente de párrafo.
            return self._fonts["para"]
        return font


    def draw(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        surface.fill(self.kernel_bg, rect)

        ox, oy = rect.x, rect.y
        clip_prev = surface.get_clip()
        surface.set_clip(rect)


        # ------------------------------------------------------------------
        # MÁRGENES LATERALES BASADOS EN TAMAÑO DE FUENTE + ESCALA
        #
        # - Unidad: tamaño base lógico de la fuente de párrafo
        #           (hlp_BaseFontSize) * hlp_FontScale.
        # - Por defecto:
        #       margen_izquierdo  = 3.0 * unidad
        #       margen_derecho    = 5.0 * unidad
        # - Si el estilo define explícitamente hlp_PaddingLeft/Right, se
        #   respetan esos valores.
        # - El padding vertical se controla con hlp_Padding.
        # ------------------------------------------------------------------
        base_size = float(self.style.get("hlp_BaseFontSize", 20))
        scale = float(self.style.get("hlp_FontScale", 1.0))
        base_unit = base_size * scale

        padding = int(self.style["hlp_Padding"])

        pad_left = int(self.style.get("hlp_PaddingLeft", 3.0 * base_unit))
        pad_right = int(self.style.get("hlp_PaddingRight", 5.0 * base_unit))

        x0 = ox + pad_left
        y0 = oy + padding
        x1 = ox + rect.width - pad_right
        max_w = max(0, x1 - x0)

        # Altura visible real dentro del rectángulo de ayuda
        visible_height = max(0, rect.height - padding * 2)

        # Ajuste del scroll: no debe pasar de manera que el último contenido
        # quede oculto por la zona de padding inferior.
        max_scroll = max(0, self._content_height - visible_height)
        if self._scroll > max_scroll:
            self._scroll = max_scroll
        if self._scroll < 0:
            self._scroll = 0

        viewport_top = self._scroll
        viewport_bottom = self._scroll + visible_height

        # Si hlp_CodeBlockMode no tiene nada usar modo "code_block"
        code_mode = str(self.style.get("hlp_CodeBlockMode", "code_block")).lower()

        for ln in self._lines:
            y = ln["y"]
            if y + ln["h"] < viewport_top or y > viewport_bottom:
                continue
            draw_y = y0 + (y - viewport_top)

            # Fondo para código, según modo configurado.
            if code_mode == "code_line":
                # Modo clásico: fondo por línea, usando todo el ancho disponible.
                if ln.get("is_code") and ln.get("code_rect"):
                    cr = ln["code_rect"]
                    bg_rect = pygame.Rect(x0 + cr.x, draw_y + cr.y, max_w, cr.h)
                    pygame.draw.rect(
                        surface,
                        self.style["hlp_ColorCodeBg"],
                        bg_rect,
                        border_radius=4,
                    )
            else:
                # Modo 'block': se dibuja una caja por bloque de código.
                if ln.get("code_bg"):
                    indent = int(ln.get("code_bg_indent", 0))
                    block_width = int(ln.get("code_bg_width", max_w))
                    # El ancho de la caja no debe sobrepasar el espacio disponible.
                    block_width = max(0, min(block_width, max_w - indent))
                    bg_rect = pygame.Rect(x0 + indent, draw_y, block_width, ln["h"])
                    pygame.draw.rect(
                        surface,
                        self.style["hlp_ColorCodeBg"],
                        bg_rect,
                        border_radius=4,
                    )


            if ln.get("hr"):
                col = self.style["hlp_ColorRule"]
                pygame.draw.line(surface, col, (x0, draw_y + ln["h"] // 2), (x1, draw_y + ln["h"] // 2), 1)
                continue

            # Dibujo del texto
            for font_key, color, text, rx in ln["runs"]:
                if not text:
                    continue

                # En modo 'block', las líneas de código llevan una indentación
                # adicional (code_block_indent) para que el texto quede dentro
                # de la caja blanca.
                extra_indent = 0
                if code_mode == "code_block" and ln.get("is_code"):
                    extra_indent = int(ln.get("code_block_indent", 0))

                font = self._font_for(font_key)
                surf = font.render(text, True, color)
                surface.blit(surf, (x0 + extra_indent + rx, draw_y))


        surface.set_clip(clip_prev)

        if self._content_height > rect.height:
            track = self._scrollbar_rect()
            thumb = self._thumb_rect(track)
            pygame.draw.rect(surface, self.style["hlp_ColorScrollbarTrack"], track, border_radius=6)
            pygame.draw.rect(surface, self.style["hlp_ColorScrollbarThumb"], thumb, border_radius=6)

    def _compose_code_block_as_lines(self, blk: dict, width: int, y: int, para_sp: int) -> int:
        """Composición de bloques de código en modo 'line':
        fondo por línea, ocupando todo el ancho disponible.
        """
        import pygame  # aseguramos disponibilidad local

        lines_raw = blk["text"].split("\n")
        codepad = int(self.style["hlp_CodeBlockPad"])

        for raw in lines_raw:
            if not raw:
                # Línea vacía de código: reserva altura pero sin texto.
                h = self._line_height_for("code")
                self._lines.append(
                    {
                        "y": y,
                        "h": h,
                        "is_code": True,
                        "runs": [],
                        "code_rect": pygame.Rect(0, 0, max(0, width), h),
                    }
                )
                y += h
                continue

            wrapped = self._wrap_text_preserving_words(raw, width, font_role="code")
            for wline in wrapped:
                h = self._line_height_for("code")
                self._lines.append(
                    {
                        "y": y,
                        "h": h,
                        "is_code": True,
                        "runs": [("code", self.style["hlp_ColorCodeText"], wline, codepad)],
                        "code_rect": pygame.Rect(0, 0, max(0, width), h),
                    }
                )
                y += h

        y += para_sp
        return y

    def _compose_code_block_as_box(self, blk: dict, width: int, y: int, para_sp: int) -> int:
        """Composición de bloques de código en modo 'block':
        se genera una caja blanca envolvente, indentada y ajustada al texto.
        """
        lines_raw = blk["text"].split("\n")
        codepad = int(self.style["hlp_CodeBlockPad"])

        # Unidad de medida basada en tamaño de fuente normal y escala.
        base_size = float(self.style.get("hlp_BaseFontSize", 20))
        scale = float(self.style.get("hlp_FontScale", 1.0))
        base_unit = base_size * scale

        # Márgenes internos del bloque de código respecto a la columna de texto.
        block_inset_left = base_unit
        block_inset_right = base_unit

        # Ancho interno máximo disponible para el texto de código (sin contar
        # los márgenes específicos del bloque).
        inner_width = max(0, int(width - (block_inset_left + block_inset_right)))

        block_top_y = y
        temp_lines: list[dict] = []
        block_max_text_width = 0.0

        for raw in lines_raw:
            if not raw:
                # Línea vacía dentro del bloque de código.
                h = self._line_height_for("code")
                temp_lines.append(
                    {
                        "y": y,
                        "h": h,
                        "is_code": True,
                        "runs": [],
                        "code_block_indent": block_inset_left,
                    }
                )
                y += h
                continue

            wrapped = self._wrap_text_preserving_words(raw, inner_width, font_role="code")
            for wline in wrapped:
                h = self._line_height_for("code")
                # Medimos el ancho real del texto de código para ajustar la caja.
                w, _ = self._measure_text(wline, "code")
                line_width = w + 2 * codepad
                block_max_text_width = max(block_max_text_width, line_width)

                temp_lines.append(
                    {
                        "y": y,
                        "h": h,
                        "is_code": True,
                        "runs": [("code", self.style["hlp_ColorCodeText"], wline, codepad)],
                        "code_block_indent": block_inset_left,
                    }
                )
                y += h

        block_bottom_y = y
        block_height = block_bottom_y - block_top_y

        if block_height <= 0:
            # Bloque vacío: sólo separamos y devolvemos.
            y += para_sp
            return y

        # Ancho mínimo razonable para la caja (aunque el código sea muy corto).
        space_px = self._space_px()
        min_block_width = 4 * space_px + 2 * codepad

        # El ancho de la caja se basa en el texto más ancho, pero no excede
        # el ancho interno disponible.
        block_width = max(min_block_width, min(block_max_text_width, inner_width))

        # Entrada especial para el fondo del bloque de código. Se añade antes
        # de las líneas para que se dibuje debajo del texto.
        self._lines.append(
            {
                "y": block_top_y,
                "h": block_height,
                "code_bg": True,
                "code_bg_indent": block_inset_left,
                "code_bg_width": int(block_width),
                # Importante: 'runs' vacío para que el bucle de dibujo no falle
                # al iterar ln["runs"].
                "runs": [],
            }
        )


        # Añadimos ahora las líneas de código que pertenecen a este bloque.
        for line_entry in temp_lines:
            line_entry["code_bg_width"] = int(block_width)
            self._lines.append(line_entry)

        y += para_sp
        return y



    # ---------- Composición ----------
    def _compose_all(self) -> None:
        self._lines.clear()

        # Padding asimétrico coherente con draw():
        # márgenes laterales en función de hlp_BaseFontSize * hlp_FontScale.
        base_size = float(self.style.get("hlp_BaseFontSize", 20))
        scale = float(self.style.get("hlp_FontScale", 1.0))
        base_unit = base_size * scale

        padding = int(self.style["hlp_Padding"])

        pad_left = int(self.style.get("hlp_PaddingLeft", 3.0 * base_unit))
        pad_right = int(self.style.get("hlp_PaddingRight", 5.0 * base_unit))

        width = max(0, self._w - (pad_left + pad_right))
        y = 0

        para_sp = int(self.style["hlp_ParaSpacing"])
        list_sp = int(self.style["hlp_ListSpacing"])
        h1_top, h1_bot = int(self.style["hlp_H1SpacingTop"]), int(self.style["hlp_H1SpacingBottom"])
        h2_top, h2_bot = int(self.style["hlp_H2SpacingTop"]), int(self.style["hlp_H2SpacingBottom"])
        h3_top, h3_bot = int(self.style["hlp_H3SpacingTop"]), int(self.style["hlp_H3SpacingBottom"])
        # Espaciados adicionales h4..h6 (nuevos)
        h4_top, h4_bot = int(self.style["hlp_H4SpacingTop"]), int(self.style["hlp_H4SpacingBottom"])
        h5_top, h5_bot = int(self.style["hlp_H5SpacingTop"]), int(self.style["hlp_H5SpacingBottom"])
        h6_top, h6_bot = int(self.style["hlp_H6SpacingTop"]), int(self.style["hlp_H6SpacingBottom"])

        indent_px = int(self.style.get("hlp_IndentPerLevelPx", 24))

        # Tabla de símbolos para viñetas de distintos niveles.
        bullet_symbols = ["•", "º"]

        for blk in self._blocks:
            btype = blk["type"]

            if btype in ("h1", "h2", "h3", "h4", "h5", "h6"):
                size_key = {"h1": "H1", "h2": "H2", "h3": "H3", "h4": "H4", "h5": "H5", "h6": "H6"}[btype]
                top = {"h1": h1_top, "h2": h2_top, "h3": h3_top, "h4": h4_top, "h5": h5_top, "h6": h6_top}[btype]
                bot = {"h1": h1_bot, "h2": h2_bot, "h3": h3_bot, "h4": h4_bot, "h5": h5_bot, "h6": h6_bot}[btype]
                y += top
                lines, _ = self._wrap_runs(
                    runs=self.parser.tokenize_inline(blk["text"]),
                    width=width,
                    font_role=f"head_{size_key}",
                    color=self.style["hlp_ColorText"],
                    base_indent=0,
                )
                for L in lines:
                    L["y"] = y
                    self._lines.append(L)
                    y += L["h"]
                y += bot
                continue

            if btype == "p":
                # Tratamos los '\n' explícitos dentro del texto como saltos de línea
                # visibles. Cada línea se compone como un pequeño párrafo independiente.
                raw_text = blk["text"]
                sub_paragraphs = raw_text.split("\n")

                for idx, raw_para in enumerate(sub_paragraphs):
                    if not raw_para:
                        # Línea vacía explícita: añadimos un pequeño salto vertical.
                        y += self._line_height_for("para")
                        continue

                    runs = self.parser.tokenize_inline(raw_para)
                    lines, _ = self._wrap_runs(
                        runs=runs,
                        width=width,
                        font_role="para",
                        color=self.style["hlp_ColorText"],
                        base_indent=0,
                    )
                    for L in lines:
                        L["y"] = y
                        self._lines.append(L)
                        y += L["h"]

                    # Pequeño espacio entre líneas explícitas, salvo tras la última.
                    if idx < len(sub_paragraphs) - 1:
                        y += int(self._line_height_for("para") * 0.2)

                # Espaciado estándar entre este bloque y el siguiente.
                y += para_sp
                continue


            if btype == "hr":
                lh = self._line_height_for("para")
                self._lines.append({"y": y, "h": lh, "runs": [], "hr": True})
                y += lh + para_sp
                continue

            if btype in ("ul", "ol"):
                for item in blk["items"]:
                    # Nivel lógico de indentación (0, 1, 2, ...) calculado por el parser.
                    level = max(0, int(item.get("level", 0)))
                    text = item["text"]

                    if btype == "ul":
                        # Elegir símbolo según nivel: '•', 'º'
                        idx = level % len(bullet_symbols)
                        bullet_char = bullet_symbols[idx]
                        prefix_text = f"{bullet_char} "
                    else:
                        # Listas numeradas: siempre "N. "
                        prefix_text = f"{item.get('num', 1)}. "

                    prefix_x = indent_px * (level + 1) # Dejamos un nivel de sangría visual para el primer nivel

                    prefix_w, _ = self._measure_text(prefix_text, "para")
                    gap = 8
                    base_indent = prefix_x + prefix_w + gap

                    runs = self.parser.tokenize_inline(text)
                    plines, _ = self._wrap_runs(
                        runs=runs,
                        width=width,
                        font_role="para",
                        color=self.style["hlp_ColorText"],
                        base_indent=base_indent,
                        prefix=(prefix_text, prefix_x),
                    )
                    for L in plines:
                        L["y"] = y
                        self._lines.append(L)
                        y += L["h"]
                    y += list_sp
                continue

            if btype == "code":
                mode = str(self.style.get("hlp_CodeBlockMode", "code_line")).lower()
                if mode == "code_block":
                    y = self._compose_code_block_as_box(blk, width, y, para_sp)
                else:
                    # Modo por defecto: comportamiento clásico por líneas.
                    y = self._compose_code_block_as_lines(blk, width, y, para_sp)
                continue

        
        # ----------------------------------------------------------------------------------------------------
        # "self._content_height = max(0, y)" haría que la última linea al final del texto quedara tocando el 
        # borde inferior del la pantalla sin respetar ningún margen. Por ello vamos a crear un margen virtual 
        # al final del documento equivalente a un par de líneas de párrafo para evitar que la última línea de 
        # texto quede pegada al borde inferior cuando se hace scroll hasta el final, incluso aunque el
        # markdown no termine en líneas en blanco.
        # -----------------------------------------------------------------------------------------------------
        extra_bottom = 2 * self._line_height_for("para")
        self._content_height = max(0, y + extra_bottom)

    def _wrap_runs(self, runs: List[Dict[str, Any]], width: int, font_role: str, color: RGB,
                   base_indent: int, prefix: Optional[Tuple[str, int]] = None) -> Tuple[List[Dict[str, Any]], int]:
        lines: List[Dict[str, Any]] = []
        line_runs: List[Tuple[str, RGB, str, int]] = []
        x = base_indent
        y_height = 0
        total_h = 0

        def flush_line():
            nonlocal line_runs, x, y_height, total_h
            if not line_runs and total_h == 0:
                y_height = self._line_height_for(font_role)
            if line_runs or y_height > 0:
                lines.append({"h": max(y_height, 1), "runs": line_runs[:]})
                total_h += max(y_height, 1)
            line_runs.clear()
            x = base_indent
            y_height = 0

        if prefix:
            ptxt, px = prefix
            font_key = self._font_key_for(font_role, False, False)
            line_runs.append((font_key, self.style["hlp_ColorText"], ptxt, px))

        tokens: List[Tuple[str, str, RGB]] = []
        for r in runs:
            if not r["text"]:
                continue
            if r.get("code"):
                font_key = "code"; col = self.style["hlp_ColorCodeText"]
            else:
                font_key = self._font_key_for(font_role, bool(r.get("bold")), bool(r.get("italic")))
                col = self.style["hlp_ColorLink"] if r.get("link") else color
            tokens.append((r["text"], font_key, col))

        for text, font_key, col in tokens:
            parts = self._split_preserving_spaces(text)
            for part in parts:
                w, h = self._measure_text(part, font_key)
                if x + w <= width or x == base_indent:
                    line_runs.append((font_key, col, part, x))
                    x += w
                    y_height = max(y_height, h)
                else:
                    if part.strip() == "":
                        flush_line()
                        continue
                    if w > width:
                        leftover = part
                        while leftover:
                            chunk = self._fit_text(leftover, width - x, font_key)
                            if not chunk:
                                chunk = leftover[0]
                            cw, ch = self._measure_text(chunk, font_key)
                            line_runs.append((font_key, col, chunk, x))
                            x += cw
                            y_height = max(y_height, ch)
                            leftover = leftover[len(chunk):]
                            if leftover:
                                flush_line()
                        continue
                    flush_line()
                    line_runs.append((font_key, col, part, x))
                    x += w
                    y_height = max(y_height, h)

        flush_line()
        return lines, total_h


    def _wrap_text_preserving_words(self, text: str, max_width: int, font_role: str) -> List[str]:
        """Envuelve una línea respetando palabras y espacios, sin perder texto.

        - No colapsa espacios: la indentación de código se mantiene.
        - No parte palabras salvo que no quepan ni solas.
        - Si max_width <= 0, devuelve el texto tal cual.
        """
        if max_width <= 0:
            return [text] if text else [""]

        if not text:
            return [""]

        import re

        # Separamos en "trozos": secuencias de espacios o secuencias sin espacios.
        # Ejemplo: "    for x in y" -> ["    ", "for", " ", "x", " ", "in", " ", "y"]
        tokens = re.findall(r"\s+|\S+", text)

        lines: list[str] = []
        current = ""

        for tok in tokens:
            candidate = current + tok
            width, _ = self._measure_text(candidate, font_role)

            if not current:
                # Primera pieza de la línea: la aceptamos incluso si se desborda.
                current = candidate
                continue

            if width <= max_width:
                # Cabe en la línea actual.
                current = candidate
            else:
                # No cabe: cerramos la línea actual y empezamos una nueva con este token.
                lines.append(current)
                current = tok

        if current:
            lines.append(current)

        return lines



    def _split_preserving_spaces(self, s: str) -> List[str]:
        if not s: return []
        tokens: List[str] = []
        buf = []
        is_space = s[0].isspace()
        for ch in s:
            if ch.isspace() == is_space:
                buf.append(ch)
            else:
                tokens.append("".join(buf))
                buf = [ch]
                is_space = ch.isspace()
        if buf:
            tokens.append("".join(buf))
        return tokens

    def _fit_text(self, s: str, max_w: int, font_key: str) -> str:
        if max_w <= 0: return ""
        lo, hi = 1, len(s); best = ""
        while lo <= hi:
            mid = (lo + hi) // 2
            w, _ = self._measure_text(s[:mid], font_key)
            if w <= max_w:
                best = s[:mid]; lo = mid + 1
            else:
                hi = mid - 1
        return best

    # ---------- Fuentes / estilo ----------
    def _load_style(self, cfg: HelpConfig) -> Dict[str, Any]:
        style = dict(DEFAULT_STYLE)

        # Cargar JSON si procede
        if cfg.style_json_path and os.path.exists(cfg.style_json_path):
            try:
                with open(cfg.style_json_path, "r", encoding="utf-8") as f:
                    blob = json.load(f)
                if isinstance(blob, dict):
                    if cfg.style_variant and cfg.style_variant in blob:
                        style.update(blob[cfg.style_variant])
                    else:
                        # si no hay variants, aplicar plano
                        style.update(blob)
            except Exception:
                pass

        # Overrides directos
        if cfg.style_overrides:
            style.update(cfg.style_overrides)

        # Normalizar colores a tuplas
        for k, v in list(style.items()):
            if ("Color" in k or "Krn_Color" in k) and isinstance(v, list) and len(v) == 3:
                style[k] = tuple(int(x) for x in v)

        # Guardarraíles
        style["hlp_IndentPerLevelPx"] = int(style.get("hlp_IndentPerLevelPx", self.cfg.visual_indent_px))
        style["hlp_WheelStep"] = int(style.get("hlp_WheelStep", self.cfg.wheel_step))
        style["hlp_Padding"] = int(style.get("hlp_Padding", 16))
        style["hlp_CodeBlockPad"] = int(style.get("hlp_CodeBlockPad", 8))

        # Factor global de escala de fuentes. Se puede sobreescribir desde
        # style_overrides con 'hlp_FontScale'. Si no se indica, vale 1.0.
        style["hlp_FontScale"] = float(style.get("hlp_FontScale", 1.0))

        # Modo de renderizado de bloques de código:
        #   "code_line"  → fondo por línea, a todo el ancho (modo actual).
        #   "code_block" → caja blanca envolvente, ajustada al texto.
        style["hlp_CodeBlockMode"] = style.get("hlp_CodeBlockMode", "code_line")

        return style


    def _ensure_fonts_OLD(self) -> None:
        """Crea y cachea fuentes según el estilo o fallback."""
        pygame.font.init()
        base_sz = int(self.style["hlp_BaseFontSize"])
        code_sz = int(self.style.get("hlp_CodeFontSize", base_sz))  # ← tamaño específico para código
        h1 = int(self.style["hlp_H1Size"])
        h2 = int(self.style["hlp_H2Size"])
        h3 = int(self.style["hlp_H3Size"])
        # Añadidos h4..h6
        h4 = int(self.style["hlp_H4Size"])
        h5 = int(self.style["hlp_H5Size"])
        h6 = int(self.style["hlp_H6Size"])

        # Rutas de TTF (opcionales)
        font_path = None
        code_font_path = None
        if self.cfg.fonts_dir:
            if self.cfg.help_font_file:
                fp = os.path.join(self.cfg.fonts_dir, self.cfg.help_font_file)
                if os.path.exists(fp): font_path = fp
            if self.cfg.help_code_font_file:
                cp = os.path.join(self.cfg.fonts_dir, self.cfg.help_code_font_file)
                if os.path.exists(cp): code_font_path = cp

    def _ensure_fonts(self) -> None:
        """Crea y cachea fuentes según el estilo o fallback."""
        pygame.font.init()

        # Factor global de escala de fuentes (1.0 = sin cambios)
        scale = float(self.style.get("hlp_FontScale", 1.0))

        def scale_size(raw: int) -> int:
            """Aplica escala a un tamaño de fuente, con un mínimo razonable."""
            return max(8, int(round(raw * scale)))

        base_sz = scale_size(int(self.style["hlp_BaseFontSize"]))
        code_sz = scale_size(int(self.style.get("hlp_CodeFontSize", self.style["hlp_BaseFontSize"])))
        h1 = scale_size(int(self.style["hlp_H1Size"]))
        h2 = scale_size(int(self.style["hlp_H2Size"]))
        h3 = scale_size(int(self.style["hlp_H3Size"]))
        # Añadidos h4..h6
        h4 = scale_size(int(self.style["hlp_H4Size"]))
        h5 = scale_size(int(self.style["hlp_H5Size"]))
        h6 = scale_size(int(self.style["hlp_H6Size"]))

        # Rutas de TTF (opcionales)
        font_path = None
        code_font_path = None
        if self.cfg.fonts_dir:
            if self.cfg.help_font_file:
                fp = os.path.join(self.cfg.fonts_dir, self.cfg.help_font_file)
                if os.path.exists(fp): font_path = fp
            if self.cfg.help_code_font_file:
                cp = os.path.join(self.cfg.fonts_dir, self.cfg.help_code_font_file)
                if os.path.exists(cp): code_font_path = cp

        def make_font(size: int, bold: bool = False, italic: bool = False, mono: bool = False) -> pygame.font.Font:
            # 1) Si hay TTF explícitos, los usamos y forzamos negrita/itálica con set_bold/set_italic
            if mono and code_font_path and os.path.exists(code_font_path):
                f = pygame.font.Font(code_font_path, size)
                f.set_bold(bold)
                f.set_italic(italic)
                return f

            if font_path and os.path.exists(font_path):
                f = pygame.font.Font(font_path, size)
                f.set_bold(bold)
                f.set_italic(italic)
                return f

            # 2) Fallbacks de sistema: creamos la fuente "normal" y luego
            #    aplicamos siempre set_bold/set_italic, en vez de confiar
            #    en los flags de SysFont, que según el sistema pueden
            #    perder la negrita cuando se combina con itálica.
            if mono:
                try:
                    f = pygame.font.SysFont("DejaVuSansMono", size)
                    f.set_bold(bold)
                    f.set_italic(italic)
                    return f
                except Exception:
                    pass

            f = pygame.font.SysFont("Arial", size)
            f.set_bold(bold)
            f.set_italic(italic)
            return f


        # Fuentes para párrafos
        self._fonts["para"]    = make_font(base_sz)
        self._fonts["para_b"]  = make_font(base_sz, bold=True)
        self._fonts["para_i"]  = make_font(base_sz, italic=True)
        self._fonts["para_bi"] = make_font(base_sz, bold=True, italic=True)

        # Encabezados
        self._fonts["head_H1"] = make_font(h1, bold=True)
        self._fonts["head_H2"] = make_font(h2, bold=True)
        self._fonts["head_H3"] = make_font(h3, bold=True)
        self._fonts["head_H4"] = make_font(h4, bold=True)
        self._fonts["head_H5"] = make_font(h5, bold=True)
        self._fonts["head_H6"] = make_font(h6, bold=True)

        # Código (inline y bloque)
        self._fonts_code["code"] = make_font(code_sz, mono=True)

    def _font_key_for(self, role: str, bold: bool, italic: bool) -> str:
        if role.startswith("head_"): return role
        if bold and italic: return "para_bi"
        if bold: return "para_b"
        if italic: return "para_i"
        return "para"

    def _measure_text(self, s: str, font_key: str) -> Tuple[int, int]:
        f = self._fonts.get(font_key) or self._fonts_code.get(font_key) or self._fonts["para"]
        w, h = f.size(s)
        line_pct = int(self.style.get("hlp_LineHeightPct", 120))
        line_h = max(h, int(f.get_height() * line_pct / 100))
        return w, line_h

    def _line_height_for(self, role: str) -> int:
        key = self._font_key_for(role, False, False) if not role.startswith("head_") else role
        _, h = self._measure_text("Ag", key)
        return h

    def _space_px(self) -> int:
        """Ancho en píxeles de un espacio ' ' usando la fuente de párrafo."""
        w, _ = self._measure_text(" ", "para")
        return max(1, w)

    def _scrollbar_rect(self) -> pygame.Rect:
        assert self._rect_abs is not None
        r = self._rect_abs
        padding = int(self.style["hlp_Padding"])
        track_w = 10
        return pygame.Rect(r.right - padding - track_w, r.top + padding, track_w, r.height - 2 * padding)

    def _thumb_rect(self, track: pygame.Rect) -> pygame.Rect:
        view_h = self._h
        content_h = max(self._content_height, 1)
        inner_h = track.height
        ratio = min(1.0, view_h / float(content_h))
        thumb_h = max(24, int(inner_h * ratio))
        max_scroll = max(0, content_h - view_h)
        frac = 0.0 if max_scroll == 0 else self._scroll / float(max_scroll)
        yoff = int((inner_h - thumb_h) * frac)
        return pygame.Rect(track.x, track.y + yoff, track.width, thumb_h)

    # ---------- Adaptador opcional para tu Popup (sin dependencia) ----------
    def as_interactive(self):
        """
        Devuelve un objeto con la interfaz:
          on_mount(rect), on_unmount(), update(dt), draw(surface, rect),
          handle_event(event)->bool, wants_keyboard(), wants_wheel()
        usable por tu SurfacePPsct sin importar este módulo a tu GUI.
        """
        viewer = self
        class _Adapter:
            def on_mount(self, rect): viewer.on_mount(rect)
            def on_unmount(self): viewer.on_unmount()
            def update(self, dt): viewer.update(dt)
            def draw(self, surface, rect): viewer.draw(surface, rect)
            def handle_event(self, event): return viewer.handle_event(event)
            def wants_keyboard(self): return viewer.wants_keyboard()
            def wants_wheel(self): return viewer.wants_wheel()
        return _Adapter()


# ---------------------------------------------------------------------------
# Helpers de conveniencia
# ---------------------------------------------------------------------------
def open_help_standalone(
    md_text: str,
    title: str = "Ayuda",
    size: Tuple[int, int] = (800, 480),
    *,
    style_json_path: Optional[str] = None,
    style_variant: Optional[str] = None,
    style_overrides: Optional[Dict[str, Any]] = None,
    fonts_dir: Optional[str] = None,
    help_font_file: Optional[str] = None,
    help_code_font_file: Optional[str] = None,
    indent_spaces_per_level: int = 2,
    visual_indent_px: int = 24,
    wheel_step: int = 48,
    kernel_bg: Optional[RGB] = None,
    on_scroll_limit: Optional[Callable[[str], None]] = None,
    scroll_limit_cooldown_ms: int = 0,    
) -> None:
    cfg = HelpConfig(
        md_text=md_text,
        title=title,
        size=size,
        style_json_path=style_json_path,
        style_variant=style_variant,
        style_overrides=style_overrides,
        fonts_dir=fonts_dir,
        help_font_file=help_font_file,
        help_code_font_file=help_code_font_file,
        indent_spaces_per_level=indent_spaces_per_level,
        visual_indent_px=visual_indent_px,
        wheel_step=wheel_step,
        kernel_bg=kernel_bg,
        on_scroll_limit=on_scroll_limit,
        scroll_limit_cooldown_ms=scroll_limit_cooldown_ms,
    )
    HelpViewer(cfg).open_window()


