# Schachprojekt – Codeübersicht

## Inhaltsverzeichnis
- [Übersicht](#übersicht)
- [Klassen und ihre Aufgaben](#klassen-und-ihre-aufgaben)
  - [Color](#color)
  - [Player](#player)
  - [Board](#board)
  - [Move](#move)
  - [Piece und abgeleitete Klassen](#piece-und-abgeleitete-klassen)
- [Spielablauf und Beispiele](#spielablauf-und-beispiele)
- [Hinweise und mögliche Erweiterungen](#hinweise-und-mögliche-erweiterungen)

---

## Übersicht

Dieses Projekt bildet die Grundlage für ein Schachspiel in Python. Mittels objektorientierter Programmierung werden zentrale Bausteine wie das Spielbrett, die Figuren, Spieler und Züge modelliert. Jede Figur besitzt eine Referenz auf das zugehörige Board, sodass Methoden der Figuren direkt den Zustand des Spielbretts abfragen können. Ein zentrales Element ist die Simulation von Zügen über eine Deepcopy des Boards, um zu prüfen, ob ein Zug den eigenen König gefährdet.

---

## Klassen und ihre Aufgaben

### Color
- **Beschreibung:**  
  Eine Enum-Klasse, die die beiden Spielerfarben definiert: `WHITE` und `BLACK`.
- **Verwendung:**  
  Dient zur Farbzuteilung von Spielern und Figuren.

### Player
- **Beschreibung:**  
  Repräsentiert einen Spieler.
- **Attribute:**  
  - `name`: Name des Spielers.  
  - `color`: Zugewiesene Farbe (vom Typ `Color`).

### Board
- **Beschreibung:**  
  Repräsentiert das Schachbrett und verwaltet den Zustand des Spiels.
- **Wichtige Attribute und Methoden:**  
  - `grid`: Ein 8×8-Array, das die Positionen der Figuren speichert.  
  - `pieces_on_board`: Liste aller aktiven Figuren.  
  - `setup_pieces(color)`: Platziert Figuren der übergebenen Farbe an den festgelegten Startpositionen.  
  - `reset_grid()` und `update_grid()`: Aktualisieren die Darstellung des Brettes, indem das Raster neu belegt wird.  
  - `initialize()`: Führt die initiale Einrichtung des Brettes durch (Befüllen der Figuren für beide Farben und Aktualisieren des Grids).  
  - `is_empty(square_coords)`: Prüft, ob ein bestimmtes Feld leer ist.  
  - `in_bounds(square_coords)`: Stellt sicher, dass angegebene Koordinaten innerhalb der Brettgrenzen liegen.  
  - `clone()`: Erstellt über `copy.deepcopy` eine Kopie des Boards, um Zugsimulationen zu ermöglichen.  
  - `is_under_attack(color)`: (Platzhalter) Prüft, ob der König der angegebenen Farbe angegriffen wird.

### Move
- **Beschreibung:**  
  Repräsentiert einen Zug im Spiel.
- **Attribute:**  
  - `captured_pieces`: Liste von Figuren, die durch den Zug geschlagen wurden.  
  - `move_history`: Historie der bisher ausgeführten Züge.

### Piece und abgeleitete Klassen
- **Basis-Klasse (Piece):**
  - **Beschreibung:**  
    Abstrakte Klasse, von der alle Schachfiguren erben.
  - **Attribute:**  
    - `_color`: Farbe der Figur.  
    - `_position`: Aktuelle Position als Tupel (x, y).  
    - `_has_moved`: Gibt an, ob die Figur bereits bewegt wurde (wichtig für spezielle Züge wie Rochade oder den doppelten Bauernzug).  
    - `board`: Referenz auf das zugehörige Board.
  - **Wichtige Methoden:**  
    - `get_pseudo_legal_moves()`: (Abstract) Gibt alle möglichen Züge gemäß den Bewegungsregeln der Figur zurück, ohne Berücksichtigung von Schachbedingungen.  
    - `get_legal_moves()`: Filtert die pseudo-legalen Züge, indem für jeden Zug eine Simulation (über `clone()`) durchgeführt wird, um zu prüfen, ob der eigene König damit in Schach gerät.  
    - `move(end_position)`: Führt einen Zug aus, wenn dieser als legal erkannt wird.
- **Spezialisierte Klassen (z. B. Pawn, Rook, Knight, Bishop, Queen, King):**
  - Jede dieser Klassen implementiert in der Methode `get_pseudo_legal_moves()` die spezifische Zuglogik.
  - **Beispiel – Pawn:**
    - Berechnet Standardzüge (ein Feld vorwärts), den Doppelzug vom Startfeld, diagonale Schläge und den en passant-Zug.
    - Verwendet das Flag `_en_passant_vulnerability` zur Kennzeichnung spezieller en passant-Situationen.

---

## Spielablauf und Beispiele

Das Spiel wird über die **Board**-Klasse initialisiert. Dabei werden alle Figuren an ihre Startpositionen gesetzt und das interne Grid aktualisiert. Züge werden direkt über die Figuren-Methoden ausgeführt.

### Beispiel: Erster Bauernzug

```python
# Initialisiere das Spielbrett und setze die Figuren
board = Board()
board.initialize()

# Bewege den Bauern an Position (0, 1) (das Feld links vom weißen Bauern) nach (0, 2)
board.grid[1][0].move((0, 2))

# Aktualisiere das Brett, um die neue Position anzuzeigen
board.update_grid()
