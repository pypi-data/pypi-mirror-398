from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Counts:
    patch: int
    async_mock: int
    magic_mock: int
    mock: int
    monkeypatch: int
    no_auto_mock: int


def count_patterns(text: str) -> Counts:
    patterns = {
        "patch": re.compile(r"\bpatch\("),
        "AsyncMock": re.compile(r"\bAsyncMock\b"),
        "MagicMock": re.compile(r"\bMagicMock\b"),
        "Mock": re.compile(r"\bMock\b"),
        "monkeypatch": re.compile(r"\bmonkeypatch\b"),
        "no_auto_mock": re.compile(r"no_auto_mock"),
    }
    return Counts(
        patch=len(patterns["patch"].findall(text)),
        async_mock=len(patterns["AsyncMock"].findall(text)),
        magic_mock=len(patterns["MagicMock"].findall(text)),
        mock=len(patterns["Mock"].findall(text)),
        monkeypatch=len(patterns["monkeypatch"].findall(text)),
        no_auto_mock=len(patterns["no_auto_mock"].findall(text)),
    )


def main() -> None:
    root = Path("tests")
    rows: list[tuple[str, Counts]] = []

    for path in root.rglob("test_*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        rows.append((path.as_posix(), count_patterns(text)))

    rows.sort(key=lambda r: (r[1].patch, r[1].mock), reverse=True)

    print("Top 25 test files by patch() usage:")
    for path, c in rows[:25]:
        if c.patch == 0:
            break
        print(
            f"{path:75} patch={c.patch:3d} Mock={c.mock:3d} MagicMock={c.magic_mock:3d} "
            f"AsyncMock={c.async_mock:3d} no_auto_mock={c.no_auto_mock}"
        )

    total = len(rows)
    no_auto = sum(1 for _, c in rows if c.no_auto_mock > 0)
    heavy = [(p, c) for p, c in rows if c.patch >= 10]

    print(f"\nFiles with no_auto_mock marker: {no_auto}/{total}")
    print(f"Files with patch()>=10: {len(heavy)}")
    for p, c in heavy[:20]:
        print(f"  {p} (patch={c.patch})")


if __name__ == "__main__":
    main()
