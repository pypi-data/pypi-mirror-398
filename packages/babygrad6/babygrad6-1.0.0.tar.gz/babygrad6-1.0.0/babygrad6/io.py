import sys
import os


class Scanner:
    def __init__(self):
        # Auto-detect: If a file argument is passed, read from it. Otherwise stdin.
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            sys.stdin = open(sys.argv[1], "r")
        self.tokens = self._generate_tokens()

    def _generate_tokens(self):
        """Lazy token generator."""
        try:
            for line in sys.stdin:
                # Allow CSV-style input by normalizing commas to spaces
                line = line.replace(",", " ")
                for token in line.split():
                    yield token
        except Exception:
            pass

    def next(self):
        return next(self.tokens, None)

    def int(self):
        t = self.next()
        return int(t) if t else None

    def str(self):
        return self.next()

    def list_fixed(self, n, transformer=int):
        """Reads exactly n elements."""
        res = []
        for _ in range(n):
            t = self.next()
            if t is None:
                break
            res.append(transformer(t))
        return res

    def matrix(self, rows, cols, transformer=int):
        """Reads a rows x cols matrix."""
        return [self.list_fixed(cols, transformer) for _ in range(rows)]

    def list_until(self, sentinel="-1", transformer=str):
        """
        Reads until sentinel is found.
        Automatically converts 'null'/'n' to None.
        """
        res = []
        while True:
            t = self.next()
            if not t or t == sentinel:
                break
            if t.lower() in ["null", "n", "none"]:
                res.append(None)
            else:
                try:
                    res.append(transformer(t) if transformer else t)
                except Exception:
                    res.append(t)
        return res


# Global instance
_scanner = Scanner()
read_int = _scanner.int
read_str = _scanner.str
