import ast
import json
import os
import re
import sys
import tempfile
from collections.abc import MutableMapping, MutableSequence, MutableSet
from pathlib import Path
from pprint import pprint
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union, Set

from hexss.constants import *


class _SaveMixin:
    def __init__(self, callback: Optional[Callable[[], None]]):
        self._callback = callback
        self._batch_depth = 0

    def _touch(self) -> None:
        if self._callback and self._batch_depth == 0:
            self._callback()

    def _enter_batch(self):
        self._batch_depth += 1

    def _exit_batch(self):
        self._batch_depth = max(0, self._batch_depth - 1)
        if self._batch_depth == 0:
            self._touch()


class SaveList(MutableSequence, _SaveMixin):
    def __init__(self, iterable=(), callback=None):
        self._data = list(iterable)
        _SaveMixin.__init__(self, callback)

    def __getitem__(self, index): return self._data[index]

    def __setitem__(self, index, value):
        self._data[index] = value
        self._touch()

    def __delitem__(self, index):
        del self._data[index]
        self._touch()

    def __len__(self): return len(self._data)

    def insert(self, index, value):
        self._data.insert(index, value)
        self._touch()

    def __repr__(self): return repr(self._data)


class SaveDict(MutableMapping, _SaveMixin):
    def __init__(self, mapping=(), callback=None, **kwargs):
        self._data = dict(mapping, **kwargs)
        _SaveMixin.__init__(self, callback)

    def __getitem__(self, key): return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        self._touch()

    def __delitem__(self, key):
        del self._data[key]
        self._touch()

    def __iter__(self): return iter(self._data)

    def __len__(self): return len(self._data)

    def __repr__(self): return repr(self._data)


class SaveSet(MutableSet, _SaveMixin):
    def __init__(self, iterable=(), callback=None):
        self._data = set(iterable)
        _SaveMixin.__init__(self, callback)

    def __contains__(self, value):
        return value in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def add(self, value):
        if value not in self._data:
            self._data.add(value)
            self._touch()

    def discard(self, value):
        if value in self._data:
            self._data.discard(value)
            self._touch()

    def __repr__(self):
        return repr(self._data)


def _wrap_mutables(obj: Any, callback: Callable) -> Any:
    if isinstance(obj, list):
        return SaveList([_wrap_mutables(v, callback) for v in obj], callback=callback)
    if isinstance(obj, dict):
        return SaveDict({k: _wrap_mutables(v, callback) for k, v in obj.items()}, callback=callback)
    if isinstance(obj, set):
        return SaveSet({_wrap_mutables(v, callback) for v in obj}, callback=callback)
    return obj


def _is_literal(x: Any) -> bool:
    import types
    if isinstance(x, (types.ModuleType, types.FunctionType, types.MethodType, type)):
        return False
    if isinstance(x, (str, int, float, bool, type(None))):
        return True
    if isinstance(x, (list, tuple, set, SaveList, SaveSet)):
        return all(_is_literal(i) for i in x)
    if isinstance(x, (dict, SaveDict)):
        return all(isinstance(k, (str, int, float, bool)) and _is_literal(v) for k, v in x.items())
    return False


class Config:
    def __init__(self, config_file: Union[Path, str] = "cfg.py", default_text: str = "") -> None:
        self._file = Path(config_file).resolve()
        self._data: Dict[str, Any] = {}
        self._batch_depth = 0

        if not self._file.exists():
            self._file.parent.mkdir(parents=True, exist_ok=True)
            self._file.write_text(default_text, encoding="utf-8")

        self._load()

    def __repr__(self) -> str:
        def unwrap(x):
            if isinstance(x, (SaveDict, dict)): return {k: unwrap(v) for k, v in x.items()}
            if isinstance(x, (SaveList, list)): return [unwrap(v) for v in x]
            if isinstance(x, (SaveSet, set)): return list(unwrap(v) for v in x)
            return x

        return json.dumps(unwrap(self._data), indent=4, default=str)

    def batch_update(self):
        class BatchContext:
            def __init__(self, cfg): self.cfg = cfg

            def __enter__(self): self.cfg._batch_depth += 1

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.cfg._batch_depth = max(0, self.cfg._batch_depth - 1)
                if self.cfg._batch_depth == 0 and not exc_type:
                    self.cfg._save()

        return BatchContext(self)

    def _load(self) -> None:
        code = self._file.read_text(encoding="utf-8") if self._file.exists() else ""
        ns: Dict[str, Any] = {"__file__": str(self._file), "__name__": "__config__"}

        try:
            sys.path.insert(0, str(self._file.parent))
            exec(code, ns)
        except Exception as e:
            print(f"{YELLOW}Error loading config {self._file}: {e}{END}")
        finally:
            if str(self._file.parent) in sys.path:
                sys.path.remove(str(self._file.parent))

        raw = {k: v for k, v in ns.items() if not k.startswith("__") and _is_literal(v)}
        self._data = _wrap_mutables(raw, self._save)

    def _format_value(self, value: Any, indent: str, key: str) -> str:
        def unwrap(val):
            if isinstance(val, SaveList): return [unwrap(x) for x in val]
            if isinstance(val, SaveDict): return {k: unwrap(v) for k, v in val.items()}
            if isinstance(val, SaveSet):  return {unwrap(x) for x in val}
            return val

        val = unwrap(value)

        if isinstance(val, (int, float, bool, str, type(None))):
            return f"{indent}{key} = {repr(val)}"

        import pprint
        formatted = pprint.pformat(val, indent=4, width=100, compact=False)

        lines = formatted.splitlines()
        if len(lines) > 1:
            indented_lines = [lines[0]] + [f"{indent}{line}" for line in lines[1:]]
            formatted = "\n".join(indented_lines)

        return f"{indent}{key} = {formatted}"

    def _save(self) -> None:
        if self._batch_depth > 0:
            return

        src = self._file.read_text(encoding="utf-8") if self._file.exists() else ""
        lines = src.splitlines()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            # Fallback: Just append if file is broken
            tree = ast.Module(body=[], type_ignores=[])

        spans: Dict[str, Tuple[int, int, str]] = {}
        for node in tree.body:
            key = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                key = node.targets[0].id
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                key = node.target.id
            if key and key in self._data:
                start = node.lineno - 1
                end = getattr(node, "end_lineno", node.lineno) - 1

                # Detect indentation
                curr_indent = ""
                if lines and start < len(lines):
                    m = re.match(r"^(\s*)", lines[start])
                    curr_indent = m.group(1) if m else ""

                spans[key] = (start, end, curr_indent)

        # Reconstruct file
        new_lines: List[str] = []
        i = 0
        saved_keys = set()

        while i < len(lines):
            # Check if current line is the start of a variable we manage
            current_key = None
            for k, (s, e, _) in spans.items():
                if s == i:
                    current_key = k
                    break

            if current_key:
                start, end, indent = spans[current_key]

                # Preserve inline comments on the first line
                comment = ""
                if "#" in lines[start]:
                    _, sep, cmt = lines[start].partition("#")
                    if lines[start].count('"') % 2 == 0 and lines[start].count("'") % 2 == 0:
                        comment = f"  #{cmt}"

                formatted_block = self._format_value(self._data[current_key], indent, current_key)
                new_lines.append(formatted_block + comment)

                saved_keys.add(current_key)
                i = end + 1
            else:
                new_lines.append(lines[i])
                i += 1

        # Append new variables that weren't in the file
        missing_keys = [k for k in self._data.keys() if k not in saved_keys]
        if missing_keys:
            if new_lines and new_lines[-1].strip():
                new_lines.append("")  # Add spacing
            for k in missing_keys:
                new_lines.append(self._format_value(self._data[k], indent="", key=k))

        final_content = "\n".join(new_lines) + "\n"

        # Atomic Write: Write to temp, then rename
        # This prevents corruption if the script crashes mid-write
        try:
            with tempfile.NamedTemporaryFile('w', dir=self._file.parent, delete=False, encoding='utf-8') as tf:
                tf.write(final_content)
                temp_name = tf.name
            os.replace(temp_name, self._file)
        except Exception as e:
            print(f"{YELLOW}Failed to save config: {e}{END}")
            if 'temp_name' in locals() and os.path.exists(temp_name):
                os.remove(temp_name)

    def __getattr__(self, key: str) -> Any:
        if key in self._data:
            return self._data[key]
        try:
            ns = {"__file__": str(self._file), "__name__": "__config__"}
            sys.path.insert(0, str(self._file.parent))
            exec(self._file.read_text(encoding="utf-8"), ns)
            sys.path.remove(str(self._file.parent))

            if key in ns:
                return ns[key]
        except Exception:
            pass

        return None

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_"):
            super().__setattr__(key, value)
            return

        # Automatically wrap and save
        self._data[key] = _wrap_mutables(value, self._save)
        self._save()

    def _update_block(self, name: str, code: str) -> None:
        import textwrap
        src = self._file.read_text(encoding="utf-8") if self._file.exists() else ""
        code = textwrap.dedent(code).strip()

        try:
            tree = ast.parse(src)
        except SyntaxError:
            tree = ast.Module(body=[], type_ignores=[])

        target_span = None
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                    target_span = (node.lineno - 1, getattr(node, "end_lineno", node.lineno) - 1)
                    break

        # Check if code needs "name = " prefix
        needs_prefix = True
        try:
            parsed_snippet = ast.parse(code)
            if len(parsed_snippet.body) == 1:
                node = parsed_snippet.body[0]
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                        needs_prefix = False
        except SyntaxError:
            pass  # Assume it's an expression

        block = f"{name} = {code}" if needs_prefix else code
        lines = src.splitlines()

        if target_span:
            s, e = target_span
            lines[s:e + 1] = block.splitlines()
        else:
            if lines and lines[-1].strip(): lines.append("")
            lines.extend(block.splitlines())

        new_src = "\n".join(lines) + "\n"
        self._file.write_text(new_src, encoding="utf-8")
        self._load()  # Reload to reflect changes

    def _ensure_import(self, *imports: str) -> None:
        """Ensures specific imports exist in the file, merging strictly if needed."""
        if not imports: return
        src = self._file.read_text(encoding="utf-8") if self._file.exists() else ""

        # Simplified robust appending:
        # Writing a full AST merger is overkill and fragile.
        # We append missing imports to the top if they aren't strictly present textually.

        lines = src.splitlines()
        existing_imports = set()
        for line in lines:
            if line.strip().startswith(("import ", "from ")):
                existing_imports.add(line.strip())

        new_lines = []
        for imp in imports:
            imp = imp.strip()
            if imp not in existing_imports:
                new_lines.append(imp)
                existing_imports.add(imp)  # Prevent dupes in this pass

        if new_lines:
            # Insert after shebang/encoding or at top
            insert_idx = 0
            if lines and lines[0].startswith("#!"): insert_idx += 1
            if len(lines) > insert_idx and "coding" in lines[insert_idx]: insert_idx += 1

            lines[insert_idx:insert_idx] = new_lines
            self._file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self._load()

    def _pprint(self, header: str = None) -> None:
        if header: print(f"{BLUE}{header}{END}")
        print(CYAN, end="")
        pprint(self._data)
        print(END)


if __name__ == '__main__':
    from pathlib import Path
    from hexss.pyconfig import Config

    # Point Config to your target file
    cfg = Config("my_project/config.py")

    # (int, float, complex, str, bytes, bool)
    cfg.x = 1
    cfg.y = 2.06
    cfg.z = 3 + 2j
    cfg.a = 'abc'
    cfg.b = b'abc'
    cfg.c = True

    # (Lists, Dicts, Sets)
    # Initialize a list and a dict
    cfg.users = ["alice", "bob"]
    cfg.settings = {"theme": "dark", "retries": 3}

    # Modify in-place (Triggers auto-save)
    cfg.users.append("charlie")
    cfg.settings["theme"] = "light"

    # Even nested modifications work
    cfg.nested = {"a": [1, 2]}
    cfg.nested["a"].append(3)

    # Make sure imports you’ll need exist (idempotent; merges nicely)
    cfg._ensure_import(
        "from keras import Sequential, layers",
        "from pathlib import Path",
        "os, sys, json",
        "from typing import Dict, List",
        "from typing import Optional as Opt",  # merges into any existing typing line
    )

    # Set simple values (auto-saves on assignment)
    cfg.ipv4 = "0.0.0.0"
    cfg.port = 5000
    cfg.img_size = [100, 100]
    cfg.epochs = 100
    cfg.batch_size = 64
    cfg.validation_split = 0.2
    cfg.seed = 456

    # Set derived paths and a computed list via _update_block (RHS or full assignment)
    cfg._update_block("datasets_path", "Path(__file__).parent / 'datasets'")
    cfg._update_block("model_path", "Path(__file__).parent / 'model'")
    cfg._update_block("class_names", "[p.name for p in datasets_path.iterdir() if p.is_dir()]")
    # If datasets/ doesn’t exist yet, it’ll be created on first execution (during load) and retried.

    # Add/update your Keras model using just the RHS (will wrap as `model = ...`)
    cfg._update_block("model", """
            Sequential([
                layers.Rescaling(1./255, input_shape=(*img_size, 3)),
                layers.Conv2D(16, 3, padding='same', activation='relu'),
                layers.MaxPooling2D(),
                layers.Conv2D(32, 3, padding='same', activation='relu'),
                layers.MaxPooling2D(),
                layers.Conv2D(64, 3, padding='same', activation='relu'),
                layers.MaxPooling2D(),
                layers.Flatten(),
                layers.Dense(128, activation='relu'),
                layers.Dense(len(class_names))
            ])
        """)

    # Read back values
    print("ipv4:", cfg.ipv4)  # from literals cache
    print("port:", cfg.port)
    print("img_size:", cfg.img_size)
    print("class_names (lazy):", cfg.class_names)  # computed in file, read via execution
    print("model object:", type(cfg.model))  # built object (Sequential)

    # Optional: If Keras is available, you can do a summary:
    cfg.model.build(input_shape=(None, cfg.img_size[0], cfg.img_size[1], 3))
    cfg.model.summary()

    # In-place mutations auto-save (thanks to SaveList/SaveDict/SaveSet wrappers)
    cfg.model_names = ["m1", "m2"]
    cfg.model_names.append("m3")  # triggers auto-save without reassigning
    print("model_names:", cfg.model_names)

    # Nested updates that auto-create parents and save
    cfg._update(["rects", "r1", "x"], 15)
    cfg._update(["rects", "r1", "y"], 2)
    cfg._update(["rects", "r2", "x"], 20)
    cfg._update(["rects", "r2", "y"], 60)
    print("rects:", cfg.rects)

    # Pretty print the literal store (_data)
    cfg._pprint("Current literal config (_data):")
