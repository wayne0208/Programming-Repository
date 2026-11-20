"""Universal SPEC architecture and safety guardrail tests for all modules under src/."""

import ast
import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"

UPPER_CONSTANT_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
DUNDER_RE = re.compile(r"^__[a-z0-9_]+__$")
CLI_FILE_NAMES = {"cli.py", "main.py"}
PROTECTED_EXC_NAMES = {"ValueError", "Exception", "BaseException"}


def _discover_src_files() -> list[Path]:
    """Return all Python source files under src/, excluding __pycache__."""
    files = [path for path in SRC_DIR.rglob("*.py") if "__pycache__" not in path.parts]
    return sorted(files)


def _discover_local_module_names() -> set[str]:
    """Return top-level module and package names located inside src/."""
    names: set[str] = set()
    for item in SRC_DIR.iterdir():
        if item.name == "__pycache__":
            continue
        if item.is_file() and item.suffix == ".py" and item.stem != "__init__":
            names.add(item.stem)
        elif item.is_dir():
            names.add(item.name)
    return names


def _rel_id(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _parse_ast(path: Path) -> ast.Module:
    source = path.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(path))


def _is_cli_function(name: str) -> bool:
    return name == "main" or name.startswith(("cli_", "menu")) or name.endswith("_cli")


def _is_main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    if len(node.test.ops) != 1 or not isinstance(node.test.ops[0], ast.Eq) or len(node.test.comparators) != 1:
        return False
    left, right = node.test.left, node.test.comparators[0]
    is_left_name = isinstance(left, ast.Name) and left.id == "__name__"
    is_right_main = isinstance(right, ast.Constant) and right.value == "__main__"
    is_right_name = isinstance(right, ast.Name) and right.id == "__name__"
    is_left_main = isinstance(left, ast.Constant) and left.value == "__main__"
    return (is_left_name and is_right_main) or (is_right_name and is_left_main)


def _extract_target_names(target: ast.AST) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        names: list[str] = []
        for elt in target.elts:
            names.extend(_extract_target_names(elt))
        return names
    return []


def _is_input_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name) and node.func.id == "input":
        return True
    return (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "builtins"
        and node.func.attr == "input"
    )


def _contains_input_call(node: ast.AST) -> bool:
    return any(_is_input_call(child) for child in ast.walk(node))


def _catches_value_error(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    if isinstance(handler.type, ast.Name):
        return handler.type.id in PROTECTED_EXC_NAMES
    if isinstance(handler.type, ast.Tuple):
        return any(isinstance(elt, ast.Name) and elt.id in PROTECTED_EXC_NAMES for elt in handler.type.elts)
    return False


class _UnprotectedNumericInputVisitor(ast.NodeVisitor):
    """Detect int(input(...)) / float(input(...)) outside try/except ValueError blocks."""

    def __init__(self) -> None:
        self._protected_depth = 0
        self._func_stack: list[str] = []
        self.violations: list[tuple[int, str, str]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._func_stack.append(node.name)
        self.generic_visit(node)
        self._func_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._func_stack.append(node.name)
        self.generic_visit(node)
        self._func_stack.pop()

    def visit_Try(self, node: ast.Try) -> None:  # noqa: N802
        is_protected = any(_catches_value_error(handler) for handler in node.handlers)
        if is_protected:
            self._protected_depth += 1
            for stmt in node.body:
                self.visit(stmt)
            self._protected_depth -= 1
            for handler in node.handlers:
                self.visit(handler)
            for stmt in node.orelse:
                self.visit(stmt)
            for stmt in node.finalbody:
                self.visit(stmt)
        else:
            self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        conv_name = None
        if isinstance(node.func, ast.Name) and node.func.id in {"int", "float"}:
            conv_name = node.func.id
        elif (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "builtins"
            and node.func.attr in {"int", "float"}
        ):
            conv_name = node.func.attr

        if conv_name is not None and self._protected_depth == 0:
            arg_nodes = [*node.args, *(kw.value for kw in node.keywords)]
            if any(_contains_input_call(arg) for arg in arg_nodes):
                scope = self._func_stack[-1] if self._func_stack else "<module>"
                self.violations.append((node.lineno, scope, conv_name))

        self.generic_visit(node)


SRC_FILES = _discover_src_files()


def _walk_sorted(node: ast.AST) -> list[ast.AST]:
    """Return AST descendants sorted deterministically by source location."""
    return sorted(ast.walk(node), key=lambda n: (getattr(n, "lineno", 0), getattr(n, "col_offset", 0)))


@pytest.mark.parametrize("src_file", SRC_FILES, ids=_rel_id)
def test_no_global_keyword_or_mutable_global_state(src_file: Path) -> None:
    """SPEC 基本規範第 3 條：不得使用全域變數傳遞系統資料。"""
    tree = _parse_ast(src_file)
    local_modules = _discover_local_module_names()
    rel_path = _rel_id(src_file)
    violations: list[str] = []

    for node in _walk_sorted(tree):
        if isinstance(node, ast.Global):
            names = ", ".join(node.names)
            violations.append(f"第 {node.lineno} 行使用 global 關鍵字 ({names})")

    for stmt in tree.body:
        if _is_main_guard(stmt):
            continue
        targets: list[ast.AST] = []
        if isinstance(stmt, ast.Assign):
            targets = stmt.targets
        elif isinstance(stmt, ast.AnnAssign):
            targets = [stmt.target]
        elif isinstance(stmt, ast.AugAssign):
            targets = [stmt.target]

        for target in targets:
            for name in _extract_target_names(target):
                if not UPPER_CONSTANT_RE.match(name) and not DUNDER_RE.match(name):
                    violations.append(f"第 {stmt.lineno} 行定義模組層級全域變數 '{name}'（僅允許全大寫常數）")

    imported_local_aliases: set[str] = set()
    for node in _walk_sorted(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                if root_pkg in local_modules:
                    imported_local_aliases.add(alias.asname or root_pkg)

    if imported_local_aliases and src_file.name not in CLI_FILE_NAMES:
        for stmt in tree.body:
            if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) or _is_cli_function(stmt.name):
                continue
            nodes = _walk_sorted(stmt)
            direct_call_func_ids = {id(n.func) for n in nodes if isinstance(n, ast.Call)}
            for node in nodes:
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id in imported_local_aliases
                    and id(node) not in direct_call_func_ids
                    and not UPPER_CONSTANT_RE.match(node.attr)
                ):
                    violations.append(
                        f"第 {node.lineno} 行核心函式 {stmt.name}() 直接存取跨模組全域資料 "
                        f"'{node.value.id}.{node.attr}'"
                    )
                elif (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in {"getattr", "setattr"}
                    and node.args
                    and isinstance(node.args[0], ast.Name)
                    and node.args[0].id in imported_local_aliases
                ):
                    violations.append(
                        f"第 {node.lineno} 行核心函式 {stmt.name}() 透過 {node.func.id}({node.args[0].id}, ...) "
                        "存取跨模組全域資料"
                    )

    assert not violations, f"{rel_path} 違反全域變數規範（SPEC 基本規範第 3 條）：\n- " + "\n- ".join(violations)


@pytest.mark.parametrize("src_file", SRC_FILES, ids=_rel_id)
def test_core_functions_do_not_call_input(src_file: Path) -> None:
    """SPEC 基本規範第 8 條：核心函式應能獨立測試，不得依賴人工輸入操作。"""
    if src_file.name in CLI_FILE_NAMES:
        return

    tree = _parse_ast(src_file)
    rel_path = _rel_id(src_file)
    violations: list[str] = []

    for stmt in tree.body:
        if _is_main_guard(stmt):
            continue
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_cli_function(stmt.name):
                continue
            for node in _walk_sorted(stmt):
                if _is_input_call(node):
                    violations.append(f"第 {node.lineno} 行核心函式 {stmt.name}() 呼叫了 input()")
        elif isinstance(stmt, ast.ClassDef):
            for item in stmt.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_cli_function(item.name):
                    continue
                for node in _walk_sorted(item):
                    if _is_input_call(node):
                        scope = f"{stmt.name}.{item.name}()" if hasattr(item, "name") else stmt.name
                        violations.append(f"第 {node.lineno} 行 {scope} 呼叫了 input()")
        else:
            for node in _walk_sorted(stmt):
                if _is_input_call(node):
                    violations.append(f"第 {node.lineno} 行模組頂層程式碼呼叫了 input()")

    assert not violations, (
        f"{rel_path} 違反獨立測試規範（SPEC 基本規範第 8 條，請將互動輸入移至 main() 或 cli_*()）：\n- "
        + "\n- ".join(violations)
    )


@pytest.mark.parametrize("src_file", SRC_FILES, ids=_rel_id)
def test_module_safe_import_without_stdin(src_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """確保各模組在封鎖人工輸入的情況下可安全匯入，不產生語法或頂層執行錯誤。"""

    def _forbid_input(*_args: object, **_kwargs: object) -> str:
        raise RuntimeError("模組匯入期間禁止呼叫 input()")

    monkeypatch.setattr("builtins.input", _forbid_input)
    monkeypatch.syspath_prepend(str(SRC_DIR))

    rel_path = _rel_id(src_file)
    temp_module_name = f"_guardrail_import_{src_file.stem}_{abs(hash(rel_path))}"
    spec = importlib.util.spec_from_file_location(temp_module_name, src_file)
    assert spec is not None and spec.loader is not None, f"無法建立模組規格：{rel_path}"

    module = importlib.util.module_from_spec(spec)
    sys.modules[temp_module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        pytest.fail(f"{rel_path} 匯入時發生非預期例外：{type(exc).__name__}: {exc}")
    finally:
        sys.modules.pop(temp_module_name, None)


@pytest.mark.parametrize("src_file", SRC_FILES, ids=_rel_id)
def test_no_bare_or_silent_except_handlers(src_file: Path) -> None:
    """SPEC 基本規範第 4 條：禁止使用裸 except 或靜默吞掉例外（except: pass）。"""
    tree = _parse_ast(src_file)
    rel_path = _rel_id(src_file)
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                violations.append(f"第 {node.lineno} 行使用未指定例外型別的裸 except:")
            is_silent_pass = all(
                isinstance(stmt, ast.Pass)
                or (
                    isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis
                )
                for stmt in node.body
            )
            if is_silent_pass:
                violations.append(f"第 {node.lineno} 行在 except 區塊中僅使用 pass/... 靜默忽略例外")

    assert not violations, f"{rel_path} 違反錯誤處理規範（SPEC 基本規範第 4 條）：\n- " + "\n- ".join(violations)


@pytest.mark.parametrize("src_file", SRC_FILES, ids=_rel_id)
def test_no_unprotected_numeric_input_conversion(src_file: Path) -> None:
    """確保 int(input(...)) / float(input(...)) 有適當例外保護，避免輸入非數字直接崩潰。"""
    tree = _parse_ast(src_file)
    rel_path = _rel_id(src_file)

    visitor = _UnprotectedNumericInputVisitor()
    visitor.visit(tree)

    violations = [
        f"第 {lineno} 行 {scope}() 的 {conv}(input(...)) 缺少 try/except ValueError 保護"
        for lineno, scope, conv in visitor.violations
    ]
    assert not violations, f"{rel_path} 存在未受保護的數值輸入轉換，可能導致程式非預期中斷：\n- " + "\n- ".join(
        violations
    )
