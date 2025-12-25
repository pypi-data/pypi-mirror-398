from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Final

# avoid "magic numbers"
_PARTS_EXPECTED: Final[int] = 2


class _SafeDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return '{' + key + '}'


@dataclass
class Prompt:
    name: str
    system: str
    user: str

    def render_text(self, **kwargs: Any) -> str:
        data = _SafeDict(**kwargs)
        sys_txt = self.system.format_map(data)
        usr_txt = self.user.format_map(data)
        return f'{sys_txt}\n\n{usr_txt}'.strip()

    def render_messages(self, **kwargs: Any) -> list[dict[str, str]]:
        data = _SafeDict(**kwargs)
        return [
            {'role': 'system', 'content': self.system.format_map(data)},
            {'role': 'user', 'content': self.user.format_map(data)},
        ]


_prompt_cache: dict[str, Prompt] = {}


def _load_file(name: str, custom_path: Path | None = None) -> Prompt:
    if custom_path:
        path = custom_path
    else:
        base = Path(__file__).resolve().parent
        path = base / f'{name}.prompt'

    if not path.exists():
        msg = f"Prompt '{name}' not found at {path}"
        raise FileNotFoundError(msg)

    raw = path.read_text(encoding='utf-8')
    parts = raw.split('\n---\n', 1)
    if len(parts) == _PARTS_EXPECTED:
        system, user = parts
    else:
        system, user = raw, '{input}'
    return Prompt(name=name, system=system.strip(), user=user.strip())


def get_prompt(name: str, custom_path: str | Path | None = None) -> Prompt:
    """
    Load a prompt template by name or from a custom path.

    Args:
        name: Name of the prompt (without .prompt extension) or identifier
        custom_path: Optional path to custom prompt file. If provided, loads from this path instead.

    Returns:
        Prompt object with system and user templates
    """
    cache_key = str(custom_path) if custom_path else name

    if cache_key not in _prompt_cache:
        path_obj = Path(custom_path) if custom_path else None
        _prompt_cache[cache_key] = _load_file(name, path_obj)

    return _prompt_cache[cache_key]
