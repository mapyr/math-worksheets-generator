#!/usr/bin/env python3
"""
Generator kart pracy z działaniami pisemnymi (dodawanie z przeniesieniem, odejmowanie z pożyczką, tryb mieszany).

Domyślne parametry (styl „zeszyt_czysty”):
- --problems 18
- --mode addition
- --max-digits 2
- --cols 2 --rows 9
- --problem-fontsize 26
- --operation-bar-style vector
- --result-guide-style none
- --answer-lines 0
- --post-bar-gap-factor 1.5
- --seed 26 (lub alternatywnie --seed-text można użyć słów/etykiet)

Możesz użyć --seed-text "etykieta_tygodnia" aby mieć powtarzalne zestawy bez pamiętania liczbowych seedów.

ROZSZERZENIA:
- Dodano tryb operacji:
  * --mode addition        : tylko dodawanie (domyślnie)
  * --mode subtraction     : tylko odejmowanie (wymusza a >= b i co najmniej jedną „pożyczkę”)
  * --mode mixed           : miks dodawania i odejmowania (losowo albo z balansem)
  * --mixed-ratio R        : ułamek zadań które będą dodawaniem (0..1, domyślnie 0.5) w trybie mixed

- Konfigurowalne odstępy i linie na odpowiedź ucznia pod każdym zadaniem:
  * --answer-lines N
  * --answer-line-spacing F (lub --answer-line-spacing-mm MM)
  * --answer-line-width FRACTION
  * --answer-line-color HEX/COLOR
  * --answer-line-thickness PT
  * --addition-gap-mm MM           : pionowy odstęp między składnikami (a,b)
  * --post-bar-gap-factor F        : większy odstęp pod kreską

- Regulacja typografii:
  * --problem-fontsize, --number-fontsize, --title-fontsize, --subtitle-fontsize
  * --compact-layout, --no-subtitle

RÓŻNICE DLA ODEJMOWANIA:
- W zapisie pojawia się operator '-' zamiast '+'.
- Algorytm losowania pilnuje co najmniej jednej pożyczki (borrow) między kolumnami.

RÓŻNICE DLA TRYBU MIESZANEGO:
- Każdy Problem zawiera pole 'op' ∈ {'+','-'}.
- Strona z odpowiedziami pokazuje właściwy operator.

Przykład użycia (odejmowanie):
python main.py -n 40 --mode subtraction --max-digits 4 --cols 3 --rows 6 --answer-lines 2 --addition-gap-mm 7 --post-bar-gap-factor 1.6 -o odejmowanie.pdf

Przykład (mieszany 60% dodawania):
python main.py -n 50 --mode mixed --mixed-ratio 0.6 --max-digits 4 --answer-lines 3 --answer-line-spacing-mm 9 -o mieszane.pdf

Zalecane środowisko (requirements.txt):
matplotlib
numpy
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Sequence

# --- Przygotowanie backendu Matplotlib (ważne dla macOS / środowisk bez GUI) ---
try:
    import matplotlib

    if "MPLBACKEND" not in os.environ:
        current_backend = matplotlib.get_backend().lower()
        if not current_backend.startswith("agg"):
            matplotlib.use("Agg")
except Exception as _e:  # pragma: no cover
    print(f"[WARN] Nie udało się wstępnie ustawić backendu Matplotlib: {_e}", file=sys.stderr)

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
import hashlib
from typing import Tuple


# --- Dane konfiguracyjne / struktury --- #
__all__ = [
    "Problem",
    "has_carry",
    "has_borrow",
    "generate_problems",
    "format_problem",
    "infer_width",
    "draw_page",
    "draw_answers_page",
    "build_pdf",
    "parse_args",
    "main",
]
@dataclass(frozen=True)
class Problem:
    a: int
    b: int
    op: str = "+"  # '+' albo '-'

    def answer(self) -> int:
        if self.op == "+":
            return self.a + self.b
        elif self.op == "-":
            return self.a - self.b
        raise ValueError(f"Nieznany operator: {self.op}")


# --- Logika generowania --- #
def has_carry(a: int, b: int) -> bool:
    """
    True jeśli w dodawaniu pisemnym a + b wystąpi co najmniej jedno przeniesienie.
    """
    carry = 0
    x, y = a, b
    while x > 0 or y > 0 or carry:
        dx = x % 10
        dy = y % 10
        s = dx + dy + carry
        if s >= 10:
            return True
        carry = s // 10
        x //= 10
        y //= 10
    return False


def has_borrow(a: int, b: int) -> bool:
    """
    True jeśli w odejmowaniu pisemnym a - b (a >= b) wystąpi co najmniej jedna pożyczka.
    """
    borrow = 0
    x, y = a, b
    while x > 0 or y > 0:
        dx = x % 10
        dy = y % 10
        dv = dx - borrow
        if dv < dy:
            return True
        borrow = 1 if dv < dy else 0
        x //= 10
        y //= 10
    return False


def generate_problems(
    n: int,
    min_value: int = 12,
    max_digits: int = 4,
    unique: bool = False,
    seed: int | None = None,
    mode: str = "addition",
    mixed_ratio: float = 0.5,
) -> list[Problem]:
    """
    Generuje listę Problem zgodnie z trybem:
      addition    : dodawanie z co najmniej jednym przeniesieniem
      subtraction : odejmowanie z co najmniej jedną pożyczką
      mixed       : miks; liczba zadań dodawania = round(n * mixed_ratio)
    """
    if not (2 <= max_digits <= 9):
        raise ValueError("max_digits powinno być w zakresie 2..9.")
    if mode not in {"addition", "subtraction", "mixed"}:
        raise ValueError("mode musi być: addition | subtraction | mixed")
    if mode == "mixed" and not (0.0 <= mixed_ratio <= 1.0):
        raise ValueError("mixed_ratio musi być w zakresie 0..1")

    if seed is not None:
        random.seed(seed)

    upper = 10 ** max_digits - 1
    target_add = n if mode == "addition" else (0 if mode == "subtraction" else round(n * mixed_ratio))
    target_sub = n - target_add

    problems: list[Problem] = []
    seen_add: set[tuple[int, int]] = set()
    seen_sub: set[tuple[int, int]] = set()

    # Dodawanie
    add_count = 0
    while add_count < target_add:
        a = random.randint(min_value, upper)
        b = random.randint(min_value, upper)
        if not has_carry(a, b):
            continue
        if unique:
            key = (a, b) if a <= b else (b, a)
            if key in seen_add:
                continue
            seen_add.add(key)
        problems.append(Problem(a, b, op="+"))
        add_count += 1

    # Odejmowanie
    sub_count = 0
    while sub_count < target_sub:
        a = random.randint(min_value, upper)
        b = random.randint(min_value, upper)
        if a < b:
            a, b = b, a
        if not has_borrow(a, b):
            continue
        if unique:
            key = (a, b)
            if key in seen_sub:
                continue
            seen_sub.add(key)
        problems.append(Problem(a, b, op="-"))
        sub_count += 1

    if mode == "mixed":
        random.shuffle(problems)

    return problems


# --- Formatowanie tekstu zadania --- #
def format_problem(a: int, b: int, width: int, op: str) -> Tuple[str, str, str]:
    """
    Zwraca krotkę trzech linii (górny składnik, dolny z operatorem, kreska).
    op: '+' albo '-'
    """
    sa = f"{a:>{width}d}"
    sb = f"{b:>{width}d}"
    top = "  " + sa
    mid = f"{op} " + sb
    line = "  " + "-" * width
    return top, mid, line


def infer_width(problems: Sequence[Problem]) -> int:
    """
    Określa ile znaków potrzeba do wyrównywania (na podstawie największego składnika).
    """
    max_val = max(max(p.a, p.b) for p in problems)
    return len(str(max_val))


# --- Rysowanie stron --- #
def draw_page(
    problems: Sequence[Problem],
    title: str,
    page_index: int,
    cols: int,
    rows: int,
    figsize: Tuple[float, float],
    start_number: int,
    *,
    problem_fontsize: int,
    number_fontsize: int,
    title_fontsize: int,
    subtitle_fontsize: int,
    show_subtitle: bool,
    answer_lines: int,
    answer_line_spacing: float,
    answer_line_width: float,
    answer_line_color: str,
    answer_line_thickness: float,
    compact_layout: bool,
    answer_line_spacing_mm: float,
    addition_gap_mm: float,
    post_bar_gap_factor: float,
    operation_bar_style: str,
    result_guide_style: str,
    result_guide_color: str,
    result_guide_thickness: float,
    digit_guides: bool,
    digit_guides_color: str,
    digit_guides_alpha: float,
    number_color: str,
    hide_numbers: bool,
) -> Figure:
    """
    Rysuje pojedynczą stronę z siatką zadań.

    answer_line_spacing – wielkość w jednostkach osi (0..1) jeśli > 0.
    answer_line_spacing_mm – jeżeli > 0, ignoruje answer_line_spacing i używa wartości w milimetrach.
    addition_gap_mm – jeżeli > 0, pionowy odstęp między pierwszym (a) i drugim (b) składnikiem w mm.
    post_bar_gap_factor – mnożnik zwiększający odstęp między kreską a pierwszą linią odpowiedzi.
    Gdy answer_line_spacing <= 0 i answer_line_spacing_mm <= 0, odstęp jest wyliczany automatycznie
    tak, aby linie wypełniły dostępne miejsce i na siebie nie nachodziły.
    """
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    digits = infer_width(problems)
    if show_subtitle:
        subtitle = f"Dodawanie sposobem pisemnym (do {digits} cyfr) — każde zadanie ma przeniesienie."
    else:
        subtitle = ""

    # Górne tytuły
    ax.text(
        0.5,
        0.965,
        title,
        ha="center",
        va="top",
        fontsize=title_fontsize,
        fontweight="bold",
    )
    if show_subtitle:
        ax.text(0.5, 0.94, subtitle, ha="center", va="top", fontsize=subtitle_fontsize)

    # Marginesy (osie w norm. współrzędnych 0..1)
    left = 0.08
    right = 0.92
    if compact_layout:
        top = 0.885 if show_subtitle else 0.93
    else:
        top = 0.90 if show_subtitle else 0.945
    bottom = 0.058  # minimalnie więcej miejsca na linie

    cell_w = (right - left) / cols
    cell_h = (top - bottom) / rows
    width = digits

    # Wysokość figury w mm (dla przeliczenia spacing_mm i addition_gap_mm)
    fig_height_mm = figsize[1] * 25.4

    # Offsety pionowe (domyślne)
    if compact_layout:
        offset_text_top = 0.072 * cell_h
        default_line_gap = 0.045 * cell_h
    else:
        offset_text_top = 0.082 * cell_h
        default_line_gap = 0.050 * cell_h  # ciut większy odstęp dla czytelności

    # Nadpisanie odstępu między składnikami jeśli podano wartość w mm
    if addition_gap_mm > 0:
        # Konwersja: mm / wysokość_figury_mm => jednostki osi
        line_gap = addition_gap_mm / fig_height_mm
    else:
        line_gap = default_line_gap

    for idx, problem in enumerate(problems):
        r = idx // cols
        c = idx % cols
        if r >= rows:
            break

        top_s, mid_s, line_s = format_problem(problem.a, problem.b, width, problem.op)

        x0 = left + c * cell_w
        y0 = top - r * cell_h  # górna krawędź komórki

        number = start_number + idx
        if not hide_numbers:
            ax.text(
                x0 + 0.005 * cell_w,
                y0 - 0.03 * cell_h,
                f"{number}.",
                ha="left",
                va="top",
                fontsize=number_fontsize,
                color=number_color,
                alpha=0.65 if number_color.lower() in {"#666666", "#777777", "#888888", "grey", "gray"} else 1.0,
            )

        # Pozycje linii dodawania
        text_x = x0 + 0.17 * cell_w
        a_y = y0 - offset_text_top
        b_y = a_y - line_gap
        bar_y = b_y - line_gap

        # Zwiększamy dystans między kreską a obszarem odpowiedzi (konfigurowalny mnożnik)
        first_answer_gap = line_gap * post_bar_gap_factor
        base_answer_y = bar_y - first_answer_gap

        ax.text(
            text_x,
            a_y,
            top_s,
            ha="left",
            va="top",
            fontsize=problem_fontsize,
            family="monospace",
        )
        ax.text(
            text_x,
            b_y,
            mid_s,
            ha="left",
            va="top",
            fontsize=problem_fontsize,
            family="monospace",
        )
        if operation_bar_style == "ascii":
            ax.text(
                text_x,
                bar_y,
                line_s,
                ha="left",
                va="top",
                fontsize=problem_fontsize,
                family="monospace",
            )
        elif operation_bar_style == "vector":
            ax.plot(
                [text_x, text_x + (cell_w * answer_line_width)],
                [bar_y, bar_y],
                color=result_guide_color,
                linewidth=result_guide_thickness,
                solid_capstyle="round",
            )
        # 'none' -> pomijamy kreskę całkowicie

        # --- Rezultat: wskazanie miejsca na wynik ---
        # Pozycja linii wyniku w połowie przerwy między kreską a pierwszą linią odpowiedzi.
        result_y = bar_y - (line_gap * 0.5)

        if result_guide_style == "line":
            ax.plot(
                [text_x, text_x + cell_w * answer_line_width],
                [result_y, result_y],
                color=result_guide_color,
                linewidth=result_guide_thickness,
                solid_capstyle="round",
            )
        elif result_guide_style == "underline":
            underline_str = "  " + "_" * width
            ax.text(
                text_x,
                result_y + 0.01 * cell_h,
                underline_str,
                ha="left",
                va="top",
                fontsize=problem_fontsize,
                family="monospace",
                color=result_guide_color,
            )
        elif result_guide_style == "none":
            # Brak dodatkowego oznaczenia miejsca na wynik
            pass

        # Opcjonalne pionowe prowadnice cyfr (digit guides) - delikatne linie
        if digit_guides and result_guide_style != "boxes":
            span_w = cell_w * answer_line_width
            for i in range(width):
                guide_x = text_x + (i + 0.5) * (span_w / max(width, 1))
                ax.plot(
                    [guide_x, guide_x],
                    [bar_y - line_gap * 0.2, result_y + line_gap * 0.2],
                    color=digit_guides_color,
                    alpha=digit_guides_alpha,
                    linewidth=0.6,
                )

        # Linie odpowiedzi
        if answer_lines <= 0:
            continue

        # Szerokość linii
        line_start_x = text_x
        usable_w = cell_w * answer_line_width

        bottom_limit = y0 - cell_h + 0.030 * cell_h  # dno obszaru na odpowiedzi
        available_space = base_answer_y - bottom_limit
        if available_space <= 0:
            continue  # brak miejsca, pomijamy

        # Wylicz spacing
        if answer_line_spacing_mm > 0:
            # przeliczenie mm na jednostki osi
            spacing = (answer_line_spacing_mm / fig_height_mm)
            # ograniczenia
            spacing = max(spacing, 0.02 * cell_h)
        elif answer_line_spacing > 0:
            spacing = answer_line_spacing
        else:
            # Automatyczne: rozkład równomierny między górą a dołem
            if answer_lines == 1:
                spacing = available_space * 0.5  # pojedyncza linia pośrodku
            else:
                spacing = available_space / (answer_lines - 1)
            # Minimalne i maksymalne widełki
            min_spacing = 0.038 * cell_h
            max_spacing = 0.070 * cell_h
            if spacing < min_spacing:
                spacing = min_spacing
            elif spacing > max_spacing:
                spacing = max_spacing

        # Rysowanie linii z obcięciem jeśli zabraknie miejsca
        for li in range(answer_lines):
            y_line = base_answer_y - li * spacing
            if y_line < bottom_limit:
                break
            ax.plot(
                [line_start_x, line_start_x + usable_w],
                [y_line, y_line],
                color=answer_line_color,
                linewidth=answer_line_thickness,
                solid_capstyle="round",
            )

    # Stopka
    ax.text(
        0.5,
        0.02,
        f"Strona {page_index}",
        ha="center",
        va="bottom",
        fontsize=9,
        alpha=0.7,
    )

    return fig


def draw_answers_page(
    problems: Sequence[Problem],
    title: str,
    figsize: Tuple[float, float],
    *,
    title_fontsize: int,
) -> Figure:
    """
    Generuje stronę z odpowiedziami (uwzględnia operator + / -).
    """
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.text(
        0.5,
        0.965,
        title,
        ha="center",
        va="top",
        fontsize=title_fontsize,
        fontweight="bold",
    )
    ax.text(0.5, 0.94, "Odpowiedzi", ha="center", va="top", fontsize=12)

    cols = 2
    rows = int(math.ceil(len(problems) / cols))
    left = 0.08
    right = 0.92
    top = 0.90
    bottom = 0.06
    col_w = (right - left) / cols
    row_h = (top - bottom) / rows

    for idx, pr in enumerate(problems):
        r = idx % rows
        c = idx // rows
        x = left + c * col_w
        y = top - r * row_h
        s = f"{idx+1:>3}. {pr.a} {pr.op} {pr.b} = {pr.answer()}"
        ax.text(
            x,
            y - 0.02,
            s,
            ha="left",
            va="top",
            fontsize=11,
            family="monospace",
        )

    return fig


# --- Budowa PDF --- #
def build_pdf(
    problems: Sequence[Problem],
    output_path: Path,
    cols: int,
    rows: int,
    include_answers: bool,
    paper: str,
    custom_size: Tuple[float, float] | None,
    title: str,
    *,
    problem_fontsize: int,
    number_fontsize: int,
    title_fontsize: int,
    subtitle_fontsize: int,
    show_subtitle: bool,
    answer_lines: int,
    answer_line_spacing: float,
    answer_line_width: float,
    answer_line_color: str,
    answer_line_thickness: float,
    compact_layout: bool,
    answer_line_spacing_mm: float,
    addition_gap_mm: float,
    post_bar_gap_factor: float,
    operation_bar_style: str,
    result_guide_style: str,
    result_guide_color: str,
    result_guide_thickness: float,
    digit_guides: bool,
    digit_guides_color: str,
    digit_guides_alpha: float,
    number_color: str,
    hide_numbers: bool,
) -> None:
    """
    Tworzy dokument PDF zawierający karty pracy i (opcjonalnie) stronę z odpowiedziami.
    """
    if paper.lower() == "a4":
        figsize = (8.27, 11.69)
    elif paper.lower() == "letter":
        figsize = (8.5, 11.0)
    elif paper.lower() == "custom":
        if not custom_size:
            raise ValueError("Dla 'custom' trzeba podać custom_size.")
        figsize = custom_size
    else:
        raise ValueError("Nieznany format papieru (użyj: A4, Letter, custom).")

    per_page = cols * rows
    total = len(problems)
    pages = math.ceil(total / per_page)

    with PdfPages(output_path) as pdf:
        for p in range(pages):
            start = p * per_page
            chunk = problems[start : start + per_page]
            fig = draw_page(
                chunk,
                title=title,
                page_index=p + 1,
                cols=cols,
                rows=rows,
                figsize=figsize,
                start_number=start + 1,
                problem_fontsize=problem_fontsize,
                number_fontsize=number_fontsize,
                title_fontsize=title_fontsize,
                subtitle_fontsize=subtitle_fontsize,
                show_subtitle=show_subtitle,
                answer_lines=answer_lines,
                answer_line_spacing=answer_line_spacing,
                answer_line_width=answer_line_width,
                answer_line_color=answer_line_color,
                answer_line_thickness=answer_line_thickness,
                compact_layout=compact_layout,
                answer_line_spacing_mm=answer_line_spacing_mm,
                addition_gap_mm=addition_gap_mm,
                post_bar_gap_factor=post_bar_gap_factor,
                operation_bar_style=operation_bar_style,
                result_guide_style=result_guide_style,
                result_guide_color=result_guide_color,
                result_guide_thickness=result_guide_thickness,
                digit_guides=digit_guides,
                digit_guides_color=digit_guides_color,
                digit_guides_alpha=digit_guides_alpha,
                number_color=number_color,
                hide_numbers=hide_numbers,
            )
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)

        if include_answers:
            ans_fig = draw_answers_page(
                problems,
                title=f"{title} (klucz)",
                figsize=figsize,
                title_fontsize=title_fontsize,
            )
            pdf.savefig(ans_fig, bbox_inches="tight")
            plt.close(ans_fig)


# --- Parser argumentów --- #
def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generator kart pracy: działania pisemne (+/-) z przeniesieniem/pożyczką oraz opcjami formatowania."
    )
    parser.add_argument(
        "--problems",
        "-n",
        type=int,
        default=18,
        help="Liczba zadań do wygenerowania (domyślnie 18).",
    )
    parser.add_argument(
        "--max-digits",
        type=int,
        default=2,
        help="Maksymalna liczba cyfr w składnikach (domyślnie 2).",
    )
    parser.add_argument(
        "--min-value",
        type=int,
        default=12,
        help="Minimalna wartość składnika (domyślnie 12).",
    )
    parser.add_argument(
        "--cols",
        type=int,
        default=2,
        help="Liczba kolumn na stronie (domyślnie 2).",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=9,
        help="Liczba wierszy na stronie (domyślnie 9).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=26,
        help="Seed generatora liczb losowych dla powtarzalności (domyślnie 26).",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="zeszyt_czysty.pdf",
        help="Ścieżka wyjściowa pliku PDF.",
    )
    parser.add_argument(
        "--no-answers",
        action="store_true",
        help="Nie dołączaj strony z odpowiedziami.",
    )
    parser.add_argument(
        "--unique",
        action="store_true",
        help="Wymuś unikalność par (a,b) (dla dodawania bez względu na kolejność; dla odejmowania zachowuje kolejność).",
    )
    parser.add_argument(
        "--paper",
        choices=["A4", "Letter", "custom"],
        default="A4",
        help="Format papieru (domyślnie A4).",
    )
    parser.add_argument(
        "--custom-width",
        type=float,
        default=None,
        help="Szerokość w calach dla paper=custom.",
    )
    parser.add_argument(
        "--custom-height",
        type=float,
        default=None,
        help="Wysokość w calach dla paper=custom.",
    )
    parser.add_argument(
        "--title",
        default="Karta pracy: Dodawanie pisemne z przeniesieniem",
        help="Tytuł umieszczany na stronach.",
        # ROTACJA ĆWICZEŃ (preset 'zeszyt_czysty'):
        # Bazowy styl (domyślne parametry po zmianach):
        # python main.py -n 18 --mode addition --max-digits 2 --cols 2 --rows 9 --problem-fontsize 26 \
        #   --operation-bar-style vector --result-guide-style none --addition-gap-mm 9 --post-bar-gap-factor 1.5 \
        #   --answer-lines 0 -o zeszyt_czysty.pdf
        #
        # Rotacja tygodniowa (zmienia seed, zachowuje wygląd):
        # Pon: python main.py -n 18 --seed 101 --mode mixed --mixed-ratio 0.5 -o zeszyt_czysty_pon.pdf
        # Wt : python main.py -n 18 --seed 102 --mode addition -o zeszyt_czysty_wt.pdf
        # Sr : python main.py -n 18 --seed 103 --mode subtraction -o zeszyt_czysty_sr.pdf
        # Czw: python main.py -n 18 --seed 104 --mode mixed --mixed-ratio 0.3 -o zeszyt_czysty_czw.pdf
        # Pt : python main.py -n 18 --seed 105 --mode mixed --mixed-ratio 0.7 -o zeszyt_czysty_pt.pdf
        #
        # Rotacja poziomu trudności (większa różnorodność działań):
        # python main.py -n 18 --seed 201 --mode mixed --mixed-ratio 0.5
        # python main.py -n 18 --seed 202 --mode mixed --mixed-ratio 0.4
        # python main.py -n 18 --seed 203 --mode mixed --mixed-ratio 0.6
        #
        # Rotacja ilości zadań (wersje skrócone / rozszerzone, dalej max 18 na stronę):
        # 12 zadań (więcej powietrza): python main.py -n 12 --rows 6
        # 15 zadań: python main.py -n 15 --rows 8
        # 18 zadań (pełna): python main.py -n 18 --rows 9
    )

    # --- Nowe opcje formatowania / linii odpowiedzi ---
    parser.add_argument(
        "--answer-lines",
        type=int,
        default=0,
        help="Liczba pustych linii na odpowiedź pod zadaniem (0 = brak).",
    )
    parser.add_argument(
        "--answer-line-spacing",
        type=float,
        default=0.028,
        help="Odstęp między liniami odpowiedzi (jednostki osi 0..1). 0 = automatyczny (ignorowane jeśli podano wartość w mm).",
    )
    parser.add_argument(
        "--answer-line-spacing-mm",
        type=float,
        default=9.0,
        help="Odstęp między liniami odpowiedzi w milimetrach. >0 nadpisuje --answer-line-spacing.",
    )
    parser.add_argument(
        "--addition-gap-mm",
        type=float,
        default=0.0,
        help="Odstęp pionowy między pierwszym i drugim składnikiem (a i b) w milimetrach. >0 nadpisuje domyślne.",
    )
    parser.add_argument(
        "--post-bar-gap-factor",
        type=float,
        default=1.5,
        help="Mnożnik odstępu między kreską a pierwszą linią odpowiedzi (domyślnie 1.4).",
    )
    parser.add_argument(
        "--answer-line-width",
        type=float,
        default=0.55,
        help="Szerokość linii odpowiedzi jako ułamek szerokości komórki (0..1, domyślnie 0.55).",
    )
    parser.add_argument(
        "--answer-line-color",
        default="#888888",
        help="Kolor linii odpowiedzi (np. #888888, gray, black).",
    )
    parser.add_argument(
        "--answer-line-thickness",
        type=float,
        default=1.0,
        help="Grubość linii odpowiedzi (domyślnie 1.0).",
    )
    parser.add_argument(
        "--result-guide-style",
        choices=["line", "underline", "none"],
        default="none",
        help="Styl miejsca na wynik: line (linia), underline (podkreślniki), none (bez oznaczenia).",
    )
    parser.add_argument(
        "--result-guide-color",
        default="#444444",
        help="Kolor linii / znaków miejsca na wynik (domyślnie #444444).",
    )
    parser.add_argument(
        "--result-guide-thickness",
        type=float,
        default=1.2,
        help="Grubość linii miejsca wyniku (dla stylu line).",
    )
    parser.add_argument(
        "--digit-guides",
        action="store_true",
        help="Rysuj pionowe delikatne prowadnice cyfr pod miejscem wyniku (ignorowane gdy result-guide-style none).",
    )
    parser.add_argument(
        "--digit-guides-color",
        default="#BBBBBB",
        help="Kolor pionowych prowadnic cyfr (domyślnie #BBBBBB).",
    )
    parser.add_argument(
        "--digit-guides-alpha",
        type=float,
        default=0.35,
        help="Przezroczystość pionowych prowadnic cyfr (domyślnie 0.35).",
    )
    parser.add_argument(
        "--operation-bar-style",
        choices=["ascii", "vector", "none"],
        default="vector",
        help="Styl kreski pod drugim składnikiem: vector (domyślnie, linia wektorowa), ascii (ciąg '-'), none (brak).",
    )
    parser.add_argument(
        "--problem-fontsize",
        type=int,
        default=26,
        help="Rozmiar czcionki liczb (domyślnie 14).",
    )
    parser.add_argument(
        "--number-fontsize",
        type=int,
        default=24,
        help="Rozmiar czcionki numerów zadań.",
    )
    parser.add_argument(
        "--number-color",
        default="#777777",
        help="Kolor numerów zadań (np. #777777 aby je przyciemnić, #000000 dla mocnych).",
    )
    parser.add_argument(
        "--hide-numbers",
        action="store_true",
        help="Ukryj numery zadań całkowicie.",
    )
    parser.add_argument(
        "--title-fontsize",
        type=int,
        default=16,
        help="Rozmiar czcionki tytułu (domyślnie 16).",
    )
    parser.add_argument(
        "--subtitle-fontsize",
        type=int,
        default=10,
        help="Rozmiar czcionki podtytułu.",
    )
    parser.add_argument(
        "--no-subtitle",
        action="store_true",
        help="Ukryj podtytuł opisowy pod tytułem.",
    )
    parser.add_argument(
        "--mode",
        choices=["addition", "subtraction", "mixed"],
        default="addition",
        help="Tryb generowanych działań: addition / subtraction / mixed.",
    )
    parser.add_argument(
        "--mixed-ratio",
        type=float,
        default=0.5,
        help="Ułamek zadań będących dodawaniem w trybie mixed (0..1).",
    )
    parser.add_argument(
        "--compact-layout",
        action="store_true",
        help="Ciaśniejszy układ (mniejsze pionowe marginesy w komórkach).",
    )

    parser.add_argument(
        "--seed-text",
        default=None,
        help="Tekstowy seed (SHA256 → liczba) jako alternatywa dla --seed; pozwala używać słów/etykiet.",
    )
    return parser.parse_args(argv)


# --- Funkcja główna --- #
def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if args.paper == "custom":
        if args.custom_width is None or args.custom_height is None:
            print(
                "Dla paper=custom musisz podać --custom-width oraz --custom-height.",
                file=sys.stderr,
            )
            return 2
        custom_size = (args.custom_width, args.custom_height)
    else:
        custom_size = None

    if args.answer_lines < 0:
        print("--answer-lines nie może być ujemne.", file=sys.stderr)
        return 1
    if not (0 < args.answer_line_width <= 1):
        print("--answer-line-width musi być w (0,1].", file=sys.stderr)
        return 1
    if args.answer_line_spacing < 0:
        print("--answer-line-spacing nie może być ujemne.", file=sys.stderr)
        return 1
    if args.answer_line_spacing_mm < 0:
        print("--answer-line-spacing-mm nie może być ujemne.", file=sys.stderr)
        return 1
    if args.addition_gap_mm < 0:
        print("--addition-gap-mm nie może być ujemne.", file=sys.stderr)
        return 1
    if args.post_bar_gap_factor <= 0:
        print("--post-bar-gap-factor musi być dodatnie.", file=sys.stderr)
        return 1

    try:
        # Wyliczenie efektywnego seed: liczbowy lub z tekstu
        if args.seed_text:
            seed_int = int.from_bytes(hashlib.sha256(args.seed_text.encode("utf-8")).digest()[:8], "big") & 0xFFFFFFFF
        else:
            seed_int = args.seed
        problems = generate_problems(
            n=args.problems,
            min_value=args.min_value,
            max_digits=args.max_digits,
            unique=args.unique,
            seed=seed_int,
            mode=args.mode,
            mixed_ratio=args.mixed_ratio,
        )
    except ValueError as e:
        print(f"Błąd parametrów: {e}", file=sys.stderr)
        return 1

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(
        f"[INFO] Generuję {len(problems)} zadań (max {args.max_digits} cyfry), zapis do: {output_path}"
    )
    if args.answer_lines:
        print(
            f"[INFO] Linie odpowiedzi: {args.answer_lines} (spacing={args.answer_line_spacing}, width={args.answer_line_width})"
        )

    try:
        build_pdf(
        problems=problems,
        output_path=output_path,
        cols=args.cols,
        rows=args.rows,
        include_answers=not args.no_answers,
        paper=args.paper,
        custom_size=custom_size,
        title=args.title,
        problem_fontsize=args.problem_fontsize,
        number_fontsize=args.number_fontsize,
        title_fontsize=args.title_fontsize,
        subtitle_fontsize=args.subtitle_fontsize,
        show_subtitle=not args.no_subtitle,
        answer_lines=args.answer_lines,
        answer_line_spacing=args.answer_line_spacing,
        answer_line_width=args.answer_line_width,
        answer_line_color=args.answer_line_color,
        answer_line_thickness=args.answer_line_thickness,
        compact_layout=args.compact_layout,
        answer_line_spacing_mm=args.answer_line_spacing_mm,
        addition_gap_mm=args.addition_gap_mm,
        post_bar_gap_factor=args.post_bar_gap_factor,
        operation_bar_style=args.operation_bar_style,
        result_guide_style=args.result_guide_style,
        result_guide_color=args.result_guide_color,
        result_guide_thickness=args.result_guide_thickness,
        digit_guides=args.digit_guides,
        digit_guides_color=args.digit_guides_color,
        digit_guides_alpha=args.digit_guides_alpha,
        number_color=args.number_color,
        hide_numbers=args.hide_numbers,
    )
    except Exception as e:  # pragma: no cover
        print(f"[ERROR] Generowanie PDF nie powiodło się: {e}", file=sys.stderr)
        return 3

    print("[OK] Gotowe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
