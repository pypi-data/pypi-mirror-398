import sys
import time
import shutil
import itertools

class LuxPrint:
    BAR_STYLES = {
        "blocks":  ("█", "░"),
        "classic": ("#", "-"),
        "dots":    ("●", "○"),
        "arrows":  (">", "-"),
        "lines":   ("━", "─"),
        "pipes":   ("|", "."),
        "circles": ("◉", "◯"),
    }

    def __init__(self, stream=None):
        self.stream = stream or sys.stdout
        self.text = ""

    def _write(self, text):
        self.stream.write(text)
        self.stream.flush()

    def clear(self):
        width = shutil.get_terminal_size((80, 20)).columns
        self._write("\r" + " " * width + "\r")

    def show(self, text):
        self.clear()
        self.text = str(text)
        self._write(self.text)

    def add(self, text):
        self.show(self.text + str(text))

    def wait(self, seconds):
        time.sleep(seconds)

    def cycle(self, texts, delay=0.5, repeat=1):
        for _ in range(repeat):
            for t in texts:
                self.show(t)
                time.sleep(delay)

    def spin(self, label="Loading", steps=12, delay=0.1):
        for c in itertools.islice(itertools.cycle("|/-\\"), steps):
            self.show(f"{label} {c}")
            time.sleep(delay)

    def bar(self, total=20, delay=0.15, label="Progress", style="blocks", width=20):
        for i in range(total + 1):
            progress = i / total

            if style == "orbit":
                symbols = ("c", "o", "C", "o")
                track = ["-"] * width
                pos = i % width
                track[pos] = symbols[i % len(symbols)]
                bar = " ".join(track)

            elif style == "pulse":
                seq = ["░", "▒", "▓", "▒"]
                bar = seq[i % len(seq)] * width

            elif style == "wave":
                wave = ["~", "~", "≈", "~"]
                bar = "".join(wave[(i + j) % len(wave)] for j in range(width))

            else:
                fill, empty = self.BAR_STYLES.get(style, self.BAR_STYLES["blocks"])
                filled = int(progress * width)
                bar = fill * filled + empty * (width - filled)

            self.show(f"{label} [{bar}] {i}/{total}")
            time.sleep(delay)

    def done(self, text="Done"):
        self.show(text)
        self._write("\n")
