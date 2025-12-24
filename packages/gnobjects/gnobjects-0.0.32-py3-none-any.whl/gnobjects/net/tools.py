




import re


class DomainMatcher:
    __slots__ = ("_cache",)


    

    def __init__(self):
        self._cache: dict[str, re.Pattern] = {}

    def _compile_internal(self, pattern: str) -> re.Pattern:
        """
        Компиляция паттерна в regex.

        Правила:
        *  → 1+ любых символов, кроме '.' и '~'          → [^.~]+
        ** → "хвост", всё что угодно до конца строки    → .*
             (всё, что после ** в паттерне, игнорируется, как и раньше)
        остальное → буквенные символы, экранируются через re.escape

        Матч всегда по всей строке: ^...$
        """
        regex = self._cache.get(pattern)
        if regex is not None:
            return regex

        i = 0
        n = len(pattern)
        parts: list[str] = ["^"]

        while i < n:
            c = pattern[i]
            if c == "*":
                # проверяем на **
                if i + 1 < n and pattern[i + 1] == "*":
                    # TAIL: ** → .*
                    parts.append(".*")
                    i += 2
                    # как в старой реализации: всё после ** игнорируем
                    break
                else:
                    # ONE: * → 1+ символов, кроме '.' и '~'
                    parts.append("[^.~]+")
                    i += 1
            else:
                # литерал
                parts.append(re.escape(c))
                i += 1

        parts.append("$")
        regex_str = "".join(parts)
        regex = re.compile(regex_str)
        self._cache[pattern] = regex
        return regex

    # внешний API, совместимый с твоим кодом
    def compile(self, pattern: str):
        return self._compile_internal(pattern)

    def match_compiled(self, compiled: re.Pattern, s: str) -> bool:
        return bool(compiled.match(s))

    def match(self, pattern: str, domain: str) -> bool:
        return bool(self._compile_internal(pattern).match(domain))


class DomainMatcherList:
    __slots__ = ("dm", "literal", "regex_list")

    def __init__(self, patterns: list[str]):
        self.dm = DomainMatcher()

        self.literal: set[str] = set()     # паттерны без '*'
        self.regex_list: list[re.Pattern] = []  # с масками

        for p in patterns:
            if "*" not in p:
                self.literal.add(p)
            else:
                self.regex_list.append(self.dm.compile(p))

    def match_any(self, domain: str) -> bool:
        # 1. точное совпадение
        if domain in self.literal:
            return True

        # 2. масочные паттерны
        for rx in self.regex_list:
            if rx.match(domain):
                return True

        return False


if __name__ == "__main__":
    dm = DomainMatcher()

    print(dm.match("*.a.com", "x.a.com"))             # True
    print(dm.match("ab**", "abzzz.zz"))               # True
    print(dm.match("a*b*c", "aXbYc"))                 # True
    print(dm.match("ab*", "ab."))                     # False
    print(dm.match("*~rcms.gn", "moscow~rcms.gn"))    # True
    print(dm.match("<*>~gwis", "<123>~gwis"))    # True
