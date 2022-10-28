import random
from typing import List, Optional


class gameSolver:
    numbers: List[int]
    Ans: Optional[str]

    def __init__(self, _range: int = 13):
        self.numbers = []
        _range = 10 if _range < 10 else _range
        while True:
            self.numbers.clear()
            for i in range(4):
                self.numbers.append(random.randint(1, _range))
            if s := self.check_numbers():
                self.Ans = s
                break

    def check_numbers(self) -> Optional[str]:
        symbols = ["+", "-", "*", "/"]
        a, b, c, d = self.numbers[0], self.numbers[1], self.numbers[2], self.numbers[3]
        for s1 in symbols:
            for s2 in symbols:
                for s3 in symbols:
                    exp = [
                        f"({a}{s1}{b}){s2}{c}{s3}{d}",
                        f"({a}{s1}{b}{s2}{c}){s3}{d}",
                        f"({a}{s1}{b}{s2}{c}{s3}{d})",
                        f"{a}{s1}({b}{s2}{c}){s3}{d}",
                        f"{a}{s1}({b}{s2}{c}{s3}{d})",
                        f"{a}{s1}({b}{s2}{c}{s3}{d})",
                        f"(({a}{s1}{b}){s2}{c}){s3}{d}",
                        f"({a}{s1}{b}){s2}({c}{s3}{d})",
                        f"({a}{s1}({b}{s2}{c})){s3}{d}",
                        f"{a}{s1}(({b}{s2}{c}){s3}{d})",
                        f"{a}{s1}({b}{s2}({c}{s3}{d}))"
                    ]
                    for e in exp:
                        try:
                            if round(eval(e), 7) == 24:
                                return e
                        except Exception:
                            pass
