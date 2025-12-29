# Eingebaute Funktionen

Eingebaute Funktionen eines Befehlszeilenprogramms

### sprache_wechseln sprache ⠀

Programmsprache ändern

* **Parameter:**
  **sprache** (*Zeichenkette*) – Ordnername under `locale` der die Wörterbücher enthält.Standard ist ‚‘ für die Rückfallsprache Englisch

### hilfe thema... ⠀

HIlfe bekommen

* **Parameter:**
  **thema** (*Zeichenkette*) – Funktion/Thema zum Nachschlagen. Wenn nicht angegeben, wird eine Liste allerFunktionen und Themen angezeigt.

### Beispiele

```default
Show list of all functions and topics
€ hilfe 
(...)
Show helptext on function `help`
€ hilfe 'help'
(...)
```

### sprachliste ⠀

Liste zugänglicher Programmsprachen anzeigen

### beenden ⠀

Programm beenden

* **Verursacht:**
  **SystemExit** – Immer
