# Generator kart pracy: działania pisemne (+ / -)

(Domyślny styl: „zeszyt_czysty” – 18 zadań dodawania, 2 kolumny × 9 wierszy, czcionka 26 pt, brak dodatkowych linii, brak oznaczenia miejsca wyniku (`--result-guide-style none`), kreska wektorowa (`--operation-bar-style vector`). Dostępny także tekstowy seed przez `--seed-text`.)

Skrypt `main.py` generuje PDF z zadaniami dodawania z przeniesieniem oraz odejmowania z pożyczką (lub mieszanką obu). Umożliwia estetyczne rozmieszczenie przykładów, konfigurowalne odstępy, linie na odpowiedź, różne rozmiary czcionek, a także tworzenie arkuszy odpowiadających poziomowi uczniów.

## Najważniejsze cechy

- Dodawanie z gwarantowanym co najmniej jednym przeniesieniem.
- Odejmowanie z gwarantowaną co najmniej jedną pożyczką.
- Tryb mieszany (procentowy udział dodawania vs odejmowania).
- Kontrola odstępu między składnikami (w mm).
- Regulacja odstępu pod kreską (większy „oddech” na wynik i notatki).
- Linie na odpowiedzi (ilość, szerokość, grubość, odstępy w jednostkach osi lub mm).
- Automatyczne wyliczanie odstępu jeśli nie podano jawnie.
- Format A4 / Letter / custom.
- Generowanie strony z odpowiedziami (można wyłączyć).
- Parametryzacja czcionek i układu (więcej lub mniej treści na stronę).
- Powtarzalność dzięki `--seed`.

## Wymagania

Plik `requirements.txt` (utwórz samodzielnie):

```
matplotlib
numpy
```

Instalacja:

```
pip install -r requirements.txt
```

## Uruchomienie podstawowe

Aktualne domyślne parametry (styl „zeszyt_czysty”):

- 18 zadań
- tryb addition
- 2 kolumny × 9 wierszy
- 2‑cyfrowe liczby (max-digits 2)
- czcionka działań 26 pt
- brak oznaczenia miejsca wyniku (result-guide-style none)
- kreska wektorowa pod drugim składnikiem (operation-bar-style vector)
- odstęp między składnikami: 9 mm
- odstęp pod kreską (post_bar_gap_factor): 1.5
- brak dodatkowych linii odpowiedzi

Uruchomienie z domyślną konfiguracją (wygeneruje zeszyt_czysty.pdf):

```
# (Linia usunięta – polecenie powtarza podstawowy przykład wyżej.)
```

(Przykład poniżej był starszą wersją domyślnych parametrów – usunięto; obecnie domyślnie generuje 18 zadań stylu „zeszyt_czysty”.)

```
python main.py
```

Określenie liczby zadań, maksymalnej liczby cyfr i wyjścia:

```
python main.py -n 60 --max-digits 4 -o arkusz.pdf
```

## Przykłady estetycznego wyglądu

### 1. Ładny arkusz dodawania (czytelne odstępy na pismo – styl zeszyt_czysty)

Domyślna wersja (bez dodatkowych flag):

```
python main.py
```

Wymuszenie identycznego stylu z jawnie podanymi parametrami (dla dokumentacji / porównania):

```
python main.py -n 18 --mode addition --max-digits 2 \
  --cols 2 --rows 9 --problem-fontsize 26 \
  --operation-bar-style vector --result-guide-style none \
  --addition-gap-mm 9 --post-bar-gap-factor 1.5 \
  --answer-lines 0 -o zeszyt_czysty.pdf
```

```
python main.py -n 36 --mode addition --max-digits 4 --cols 3 --rows 6 \
  --answer-lines 3 --answer-line-spacing-mm 9 \
  --addition-gap-mm 7 --post-bar-gap-factor 1.6 \
  --problem-fontsize 14 --number-fontsize 11 \
  -o dodawanie_czytelne.pdf
```

Parametry:

- `--rows 6` zmniejsza liczbę wierszy na stronę => większa wysokość komórki.
- `--addition-gap-mm 7` daje wyraźny odstęp między składnikami.
- `--post-bar-gap-factor 1.6` zwiększa przestrzeń pod kreską przed liniami.

### 2. Arkusz odejmowania (większy odstęp i mniej linii na wynik)

```
python main.py -n 30 --mode subtraction --max-digits 4 --cols 3 --rows 5 \
  --answer-lines 2 --answer-line-spacing-mm 10 \
  --addition-gap-mm 8 --post-bar-gap-factor 1.8 \
  -o odejmowanie_duzy_odstep.pdf
```

### 3. Mieszany arkusz (60% dodawania, 40% odejmowania)

```
python main.py -n 50 --mode mixed --mixed-ratio 0.6 --max-digits 2 \
  --cols 3 --rows 6 \
  --answer-lines 3 --answer-line-spacing-mm 8 \
  --addition-gap-mm 7 --post-bar-gap-factor 1.5 \
  -o mieszany.pdf
```

### 4. Gęstszy układ (więcej zadań, mniejsze odstępy – wersja kompakt)

```
python main.py -n 72 --mode addition --max-digits 3 --cols 4 --rows 9 \
  --answer-lines 1 --compact-layout \
  --problem-fontsize 12 --addition-gap-mm 5 \
  -o dodawanie_kompakt.pdf
```

### 5. Pełna szerokość linii odpowiedzi

```
python main.py -n 40 --mode subtraction --cols 2 --rows 8 \
  --answer-lines 3 --answer-line-width 0.9 --answer-line-spacing-mm 9 \
  --addition-gap-mm 7 \
  -o odejmowanie_szerokie_linie.pdf
```

### 6. Automatyczny spacing (nie podajesz mm ani spacing – wpisz 0)

```
python main.py -n 48 --mode addition --answer-lines 4 \
  --answer-line-spacing 0 --addition-gap-mm 7 \
  -o auto_spacing.pdf
```

### 7. Minimalna karta (bez dodatkowych linii odpowiedzi)

```
python main.py -n 54 --mode mixed --mixed-ratio 0.5 \
  --answer-lines 0 --addition-gap-mm 6 \
  -o minimalna.pdf
```

## Wybrane opcje CLI

| Opcja                                                                             | Opis                                                                                      |
| --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `--mode {addition,subtraction,mixed}`                                             | Wybór rodzaju działań.                                                                    |
| `--mixed-ratio R`                                                                 | Ułamek zadań typu dodawanie w trybie mixed (0..1).                                        |
| `--max-digits N`                                                                  | Maksymalna liczba cyfr składników (np. 4 => do 9999).                                     |
| `--min-value N`                                                                   | Minimalna wartość składników.                                                             |
| `--cols`, `--rows`                                                                | Siatka układu na stronie.                                                                 |
| `--answer-lines N`                                                                | Ilość pustych linii pod zadaniem (0 = brak).                                              |
| `--answer-line-spacing S`                                                         | Odstęp między liniami (jednostki osi 0..1) jeśli > 0 i brak wartości mm.                  |
| `--answer-line-spacing-mm MM`                                                     | Odstęp między liniami w mm (nadpisuje spacing).                                           |
| `--answer-line-width FRACTION`                                                    | Szerokość linii jako ułamek szerokości komórki.                                           |
| `--answer-line-color COLOR`                                                       | Kolor linii (np. #888888).                                                                |
| `--answer-line-thickness PT`                                                      | Grubość linii.                                                                            |
| `--addition-gap-mm MM`                                                            | Odstęp pionowy między składnikami (a i b).                                                |
| `--post-bar-gap-factor F`                                                         | Mnożnik odstępu między kreską a pierwszą linią odpowiedzi.                                |
| `--problem-fontsize / --number-fontsize / --title-fontsize / --subtitle-fontsize` | Rozmiary czcionek.                                                                        |
| `--compact-layout`                                                                | Ciaśniejszy układ pionowy.                                                                |
| `--no-subtitle`                                                                   | Ukrycie podtytułu pod tytułem.                                                            |
| `--paper {A4,Letter,custom}`                                                      | Format papieru.                                                                           |
| `--custom-width`, `--custom-height`                                               | Wymiary w calach dla paper=custom.                                                        |
| `--seed SEED`                                                                     | Powtarzalność losowania.                                                                  |
| `--seed-text TXT`                                                                 | Tekstowy seed (hash SHA256 → liczba); wygodne etykiety np. "tydzien_12", "grupa_A".        |
| `--unique`                                                                        | Unikalność par (dla dodawania bez względu na kolejność; odejmowanie zachowuje kolejność). |
| `--no-answers`                                                                    | Pominięcie strony z odpowiedziami.                                                        |

## Logika przeniesień i pożyczek

- Przeniesienie (carry) w dodawaniu: skrypt sprawdza każdą kolumnę dziesiętną – jeśli suma cyfr + wcześniejsze przeniesienie ≥ 10, zadanie jest akceptowane.
- Pożyczka (borrow) w odejmowaniu: dla każdej kolumny weryfikowane jest czy bieżąca cyfra minuendu po uwzględnieniu wcześniejszej pożyczki jest < cyfrą subtrahendu; jeśli tak – występuje pożyczka.

To gwarantuje, że każde działanie nadaje się do ćwiczenia pisemnego algorytmu (nie są to „bezprzeniesieniowe” wersje).

## Typowe problemy i rozwiązania

1. Linie odpowiedzi nachodzą na działanie:
   - Zmniejsz `--answer-lines`.
   - Zwiększ `--post-bar-gap-factor`.
   - Zmniejsz liczbę wierszy (np. `--rows 6` zamiast 8).
   - Użyj `--answer-line-spacing-mm` z wartością 8–10.

2. Za mały odstęp między składnikami a i b:
   - Ustaw `--addition-gap-mm 7` (lub więcej).

3. Za mało miejsca na wynik przy dużych liczbach:
   - Zmniejsz `--problem-fontsize`.
   - Zwiększ `--cols` żeby liczby były węższe, albo odwrotnie zmniejsz `--cols` by zyskać miejsce.

4. Zbyt ciemne linie:
   - Zmień na `--answer-line-color "#AAAAAA"`.

5. Za dużo przeniesień w dodawaniu (za trudne):
   - Obniż `--max-digits`.
   - Zwiększ `--min-value` aby liczby miały mniej niż maksymalną liczbę cyfr.

## Porady dla druku

- Warto testowo wygenerować jedną stronę i wydrukować w skali 100%.
- Jasnoszare linie (#888888 – #AAAAAA) wyglądają lepiej przy pisaniu ołówkiem.
- Nie używaj zbyt cienkich linii (<0.3 pt); przy słabych drukarkach mogą znikać.
- Jeśli drukarka ucina górę/dół strony – zwiększ wewnętrzne marginesy zmniejszając `--rows`.

## Rozszerzenia możliwe do dodania (pomysły)

- Wymuszanie wielu przeniesień/pożyczek (poziom trudności).
- Tryb „bez przeniesień” / „bez pożyczek” dla wprowadzania tematu.
- Eksport listy zadań do CSV/JSON.
- Generowanie wariantu z pustymi miejscami na cyfry (szablon do uzupełniania w kolumnach).
- Kolorowe wyróżnienie kolumn z przeniesieniem/pożyczką (paints w PDF – wymaga dodatkowego rysowania).

Jeśli potrzebujesz którejś z tych funkcji – dopisz ją w kodzie lub rozbuduj generator według wzorca istniejących modułów.

## Strona z odpowiedziami

Domyślnie generowana (chyba że podasz `--no-answers`). Pokazuje operator zgodny z każdym zadaniem. Przy mieszanym trybie zadania są zshuffle’owane, ale numery i odpowiedzi są zgodne.

## Powtarzalność / testowanie

- Użycie `--seed` pozwala uzyskać identyczny zestaw przy kolejnych uruchomieniach.
- Zmiana `--mixed-ratio` przy tym samym seedzie da inny układ proporcji.
- Alternatywnie możesz użyć `--seed-text`, np.:
  - `--seed-text "tydzien_01"` – arkusz dla pierwszego tygodnia
  - `--seed-text "tydzien_01_add"` vs `--seed-text "tydzien_01_sub"` aby rozdzielić tryby
  - `--seed-text "grupa_A"` / `--seed-text "grupa_B"` dla różnych poziomów
  Tekst zamieniany jest przez SHA256 na 64‑bitową liczbę, dzięki czemu dowolny ciąg daje stabilny wynik bez zapamiętywania wartości liczbowych.

## Rotacyjne generowanie arkuszy (przykłady)

Poniższe przykłady pokazują jak tworzyć serię arkuszy na kolejne dni / tygodnie zachowując spójny wygląd przy zmieniających się działaniach.

### Tygodniowa rotacja (liczbowe seedy)

Wspólny styl „zeszyt_czysty” (18 zadań, 2×9, duża czcionka, brak linii odpowiedzi):

```
python main.py -n 18 --mode mixed --mixed-ratio 0.5 --seed 101 -o tydzien_pon.pdf
python main.py -n 18 --mode addition                --seed 102 -o tydzien_wt.pdf
python main.py -n 18 --mode subtraction             --seed 103 -o tydzien_sr.pdf
python main.py -n 18 --mode mixed --mixed-ratio 0.3 --seed 104 -o tydzien_czw.pdf
python main.py -n 18 --mode mixed --mixed-ratio 0.7 --seed 105 -o tydzien_pt.pdf
```

### Tygodniowa rotacja (tekstowe seedy)

Tekstowe etykiety łatwiejsze do zapamiętania niż liczby:

```
python main.py -n 18 --mode mixed --mixed-ratio 0.5 --seed-text "tydzien_01_pon" -o tydzien_01_pon.pdf
python main.py -n 18 --mode addition                --seed-text "tydzien_01_wt"  -o tydzien_01_wt.pdf
python main.py -n 18 --mode subtraction             --seed-text "tydzien_01_sr"  -o tydzien_01_sr.pdf
python main.py -n 18 --mode mixed --mixed-ratio 0.3 --seed-text "tydzien_01_czw" -o tydzien_01_czw.pdf
python main.py -n 18 --mode mixed --mixed-ratio 0.7 --seed-text "tydzien_01_pt"  -o tydzien_01_pt.pdf
```

Zmieniając tylko sufiks tygodnia otrzymujesz spójne serie:
`"tydzien_02_pon"`, `"tydzien_02_wt"`, … itd.

### Poziomy trudności (tekstowe seedy dla grup)

```
python main.py -n 18 --mode mixed --mixed-ratio 0.5 --max-digits 2 --seed-text "grupa_A" -o grupa_A.pdf
python main.py -n 18 --mode mixed --mixed-ratio 0.5 --max-digits 3 --seed-text "grupa_B" -o grupa_B.pdf
python main.py -n 18 --mode mixed --mixed-ratio 0.5 --max-digits 4 --seed-text "grupa_C" -o grupa_C.pdf
```

### Cykliczna zmiana proporcji działań (utrzymanie seeda)

Przy stałym `--seed` lub `--seed-text` zmiana `--mixed-ratio` nadaje arkuszowi inną mieszankę:

```
python main.py -n 18 --mode mixed --mixed-ratio 0.4 --seed-text "blok_01" -o blok_01_ratio_40.pdf
python main.py -n 18 --mode mixed --mixed-ratio 0.6 --seed-text "blok_01" -o blok_01_ratio_60.pdf
```

### Warianty stylu z identycznym zbiorem działań

Ten sam zestaw działań, dwa różne wyglądy (np. wersja ucznia i wersja korekcyjna):

```
python main.py -n 18 --seed-text "tydzien_05_pon" -o uczniowie.pdf
python main.py -n 18 --seed-text "tydzien_05_pon" --answer-lines 3 --answer-line-spacing-mm 9 --result-guide-style line -o korekta.pdf
```

## Minimalny przykład (bez linii odpowiedzi, szybki arkusz)

```
python main.py -n 20 --mode subtraction --max-digits 3 --rows 4 --cols 2 --answer-lines 0 -o szybki.pdf
```

## Licencja

Dodaj własną licencję (np. MIT / CC-BY-SA) jeśli chcesz udostępniać arkusze publicznie.

## Kontakt / Autorstwo

Projekt edukacyjny – możesz dopisać w nagłówku PDF własne dane poprzez zmianę parametru `--title`.

Miłej pracy nad kartami! Jeśli chcesz dołożyć nowy typ działania (np. mnożenie pisemne), analogia do obecnych funkcji losowania jest prosta: dodaj funkcję wykrywającą obecność „trudności” (np. przeniesienia), generator i poszerz `Problem.op`.

## Przykłady dużej czcionki i szerokich odstępów (dla młodszych uczniów)

Poniższe konfiguracje zwiększają czytelność: większa czcionka, mniej zadań na stronę, większe odstępy pionowe (mm) i szersze linie na odpowiedź.

### Duże dodawanie (wysokie odstępy, 3 cyfry)

```
python main.py -n 24 --mode addition --max-digits 3 --cols 2 --rows 6 \
  --problem-fontsize 18 --number-fontsize 13 \
  --answer-lines 3 --answer-line-spacing-mm 11 \
  --addition-gap-mm 9 --post-bar-gap-factor 1.8 \
  --answer-line-width 0.85 \
  --title "Duże dodawanie" \
  -o duze_dodawanie.pdf
```

Zastosowane parametry:

- Duża czcionka: 18 pt (liczby), 13 pt (numer).
- Mniej zadań: 2 kolumny × 6 wierszy = 12 zadań na stronę (przy 24 zadaniach dwie strony).
- Odstęp między składnikami: 9 mm (`--addition-gap-mm 9`).
- Odstęp pod kreską: czynnik 1.8 (`--post-bar-gap-factor 1.8`).
- Linie odpowiedzi: 3 linie po 11 mm.

### Duże odejmowanie (większy dystans pod kreską)

```
python main.py -n 24 --mode subtraction --max-digits 3 --cols 2 --rows 6 \
  --problem-fontsize 18 --number-fontsize 13 \
  --answer-lines 2 --answer-line-spacing-mm 12 \
  --addition-gap-mm 10 --post-bar-gap-factor 2.0 \
  --answer-line-width 0.85 \
  --title "Duże odejmowanie" \
  -o duze_odejmowanie.pdf
```

Dlaczego tak:

- Większy odstęp między a i b (10 mm) ułatwia zaznaczanie pożyczek.
- `--post-bar-gap-factor 2.0` jeszcze bardziej oddziela część wyniku od działania.
- Tylko 2 linie odpowiedzi, ale szerokie (85% szerokości komórki).

### Wskazówki dla dużych czcionek

- Jeśli cyfry „schodzą” z komórki: zmniejsz `--rows` albo czcionkę do 17.
- Jeśli brakuje miejsca na linie odpowiedzi: zmniejsz `--answer-lines` lub zwiększ `--post-bar-gap-factor`.
- Dla bardzo młodszych uczniów (1–2 klasa) rozważ `--answer-line-spacing-mm 12` i `--addition-gap-mm 10–11`.

### Szybka modyfikacja pod jeszcze większe odstępy

Zwiększenie odstępu linii odpowiedzi do 13 mm:

```
python main.py -n 18 --mode addition --max-digits 2 --cols 2 --rows 5 \
  --problem-fontsize 18 --answer-lines 3 --answer-line-spacing-mm 13 \
  --addition-gap-mm 10 --post-bar-gap-factor 2.0 \
  -o ekstra_duze_dodawanie.pdf
```

W razie potrzeby można zestawić te przykłady w README jako sekcję edukacyjną dla różnych poziomów trudności (np. „Poziom 1 – duże odstępy”, „Poziom 2 – standard”, „Poziom 3 – kompakt”).

## Styl kreski pod działaniem i miejsce na wynik

Domyślnie (bez „-----”) używany jest styl wektorowy kreski pod drugim składnikiem: `--operation-bar-style vector`. Daje czystą, równą linię niezależną od szerokości cyfrowej reprezentacji. Możesz zmienić wygląd:

- `--operation-bar-style vector` (domyślnie) – pojedyncza cienka linia wektorowa.
- `--operation-bar-style ascii` – tradycyjny ciąg znaków `-----` (monospace).
- `--operation-bar-style none` – brak kreski.

### Styl miejsca na wynik

Parametr `--result-guide-style` definiuje pomoc dla wpisania wyniku (bez pól/pudełek):

- `line` – pojedyncza linia do wpisania (domyślna).
- `underline` – wynik wpisujesz nad ciągiem podkreślników `_`.
- `none` – brak dodatkowego oznaczenia (wpisujesz wynik tuż pod kreską działania).

Dodatkowe parametry:

- `--result-guide-color` – kolor linii / znaków (np. #444444).
- `--result-guide-thickness` – grubość linii (dla stylu `line` lub wektorowej kreski działania).

### Prowadnice cyfr (digit guides)

Flaga `--digit-guides` dodaje pionowe, półprzezroczyste linie wyśrodkowane pod każdą spodziewaną cyfrą wyniku (działa dla stylów line oraz underline):

- `--digit-guides-color` (np. `#BBBBBB`)
- `--digit-guides-alpha` (np. `0.35`)

Nie są rysowane dla stylu `boxes` (bo pudełka już prowadzą wzrok).

### Przykłady (bez „-----”, domyślna kreska wektorowa)

Prosty arkusz dodawania z czytelną linią wynikową:

```
python main.py -n 24 --mode addition --max-digits 2 \
  --cols 3 --rows 6 \
  --operation-bar-style vector --result-guide-style line \
  --answer-lines 0 \
  --addition-gap-mm 8 --post-bar-gap-factor 1.6 \
  -o dodawanie_czyste.pdf
```

Odejmowanie z podkreśleniem miejsca wyniku (bez ascii kreski):

```
python main.py -n 24 --mode subtraction --max-digits 2 \
  --operation-bar-style vector --result-guide-style underline \
  --addition-gap-mm 8 --post-bar-gap-factor 1.7 \
  --problem-fontsize 18 --answer-lines 0 \
  -o odejmowanie_czyste.pdf
```

Mixed z prowadnicami cyfr (podkreślenie wyniku):

```
python main.py -n 30 --mode mixed --mixed-ratio 0.5 --max-digits 2 \
  --operation-bar-style vector --result-guide-style underline \
  --digit-guides --digit-guides-color "#AAAAAA" --digit-guides-alpha 0.3 \
  --answer-lines 0 \
  --addition-gap-mm 8 --post-bar-gap-factor 1.5 \
  -o mieszane_czyste.pdf
```

Brak dodatkowego oznaczenia miejsca wyniku (styl none):

```
python main.py -n 18 --mode addition --max-digits 2 \
  --operation-bar-style none --result-guide-style none \
  --addition-gap-mm 9 --post-bar-gap-factor 1.8 \
  --problem-fontsize 18 \
  -o bez_kreski_clean.pdf
```

### Kiedy używać którego stylu?

- `vector + line`: Ogólny, czytelny arkusz dla większości klas.
- `vector + underline`: Nauka wyrównania cyfr (klasy młodsze).
- `vector + line`: Standardowy przejrzysty wygląd.
- `none + none`: Gdy chcesz maksymalnie prosty wygląd (uczeń wpisuje wynik tuż pod działaniem).
- `ascii`: Retro wygląd lub wymuszenie czysto monospace’owego układu (opcjonalne – nie jest domyślne).

### Dodatkowe wskazówki

- Jeśli wynik „wchodzi” na prowadnice cyfr – zmniejsz `--problem-fontsize` albo zwiększ `--post-bar-gap-factor`.
- Styl `underline` przy bardzo długich liczbach: rozważ zwiększenie `--cols` aby komórki były węższe (łatwiejsze wyrównanie).
- Dla jasnych prowadnic używaj większej przezroczystości (`--digit-guides-alpha 0.25–0.35`) i koloru zbliżonego do tła (#CCCCCC–#DDDDDD).

Sekcja odzwierciedla bieżące domyślne ustawienie (brak „-----” dzięki `--operation-bar-style vector`). Jeśli potrzebujesz retro wyglądu, dodaj `--operation-bar-style ascii`. Styl pól pudełkowych został usunięty – używaj `line`, `underline` lub `none`.
