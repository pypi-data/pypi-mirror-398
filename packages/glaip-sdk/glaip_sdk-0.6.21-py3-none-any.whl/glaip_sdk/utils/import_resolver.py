"""Import resolution and categorization for tool bundling.

This module provides the ImportResolver class for handling Python import
analysis and resolution during tool bundling operations.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path


class ImportResolver:
    """Resolves and categorizes Python imports for tool bundling.

    This class handles the complex logic of determining which imports
    are local (and need to be inlined) versus external (and need to
    be preserved as import statements).

    Attributes:
        tool_dir: The directory containing the tool file being bundled.

    Example:
        >>> resolver = ImportResolver(Path("/path/to/tool/dir"))
        >>> local, external = resolver.categorize_imports(ast_tree)
    """

    # Modules to exclude from bundled code (only needed locally)
    EXCLUDED_MODULES: set[str] = {
        "glaip_sdk.agents",
        "glaip_sdk.tools",
        "glaip_sdk.mcps",
    }

    def __init__(self, tool_dir: Path) -> None:
        """Initialize the ImportResolver.

        Args:
            tool_dir: Directory containing the tool file being processed.
        """
        self.tool_dir = tool_dir
        self._processed_modules: set[str] = set()

    def categorize_imports(self, tree: ast.AST) -> tuple[list, list]:
        """Categorize imports into local and external.

        Args:
            tree: AST tree of the source file.

        Returns:
            Tuple of (local_imports, external_imports) where local_imports
            contains tuples of (module_name, file_path, import_node).
        """
        local_imports = []
        external_imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if self.is_local_import(node):
                    module_file = self.resolve_module_path(node.module)
                    local_imports.append((node.module, module_file, node))
                else:
                    external_imports.append(node)
            elif isinstance(node, ast.Import):
                external_imports.append(node)

        return local_imports, external_imports

    def is_local_import(self, node: ast.ImportFrom) -> bool:
        """Check if import is local to the tool directory.

        Args:
            node: Import node to check.

        Returns:
            True if import is local.
        """
        if not node.module:
            return False

        # Handle package imports
        if "." in node.module:
            return self._is_local_package_import(node.module)

        potential_file = self.tool_dir / f"{node.module}.py"
        return potential_file.exists()

    def _is_local_package_import(self, module: str) -> bool:
        """Check if a dotted module path is local.

        Args:
            module: Module path like 'tools.config' or 'sub.module'.

        Returns:
            True if the module is local to tool_dir.
        """
        parts = module.split(".")

        # Case 1: First part matches current directory name
        if parts[0] == self.tool_dir.name:
            remaining_parts = parts[1:]
            if len(remaining_parts) == 1:
                module_path = self.tool_dir / f"{remaining_parts[0]}.py"
                if module_path.exists():
                    return True
            elif len(remaining_parts) > 1:
                module_path = self.tool_dir / "/".join(remaining_parts[:-1]) / f"{remaining_parts[-1]}.py"
                if module_path.exists():
                    return True

        # Case 2: First part is a subdirectory of tool_dir
        package_dir = self.tool_dir / parts[0]
        if package_dir.is_dir():
            module_path = self.tool_dir / "/".join(parts[:-1]) / f"{parts[-1]}.py"
            if module_path.exists():
                return True
            module_path = self.tool_dir / "/".join(parts) / "__init__.py"
            return module_path.exists()

        return False

    def resolve_module_path(self, module_name: str) -> Path:
        """Resolve module name to file path.

        Args:
            module_name: Module name (e.g., 'config' or 'tools.config').

        Returns:
            Path to the module file.
        """
        if "." in module_name:
            return self._resolve_dotted_module_path(module_name)
        return self.tool_dir / f"{module_name}.py"

    def _resolve_dotted_module_path(self, module_name: str) -> Path:
        """Resolve a dotted module path to a file path.

        Args:
            module_name: Dotted module path like 'tools.config'.

        Returns:
            Path to the module file.
        """
        parts = module_name.split(".")

        # Case 1: First part matches current directory name
        if parts[0] == self.tool_dir.name:
            remaining_parts = parts[1:]
            if len(remaining_parts) == 1:
                module_path = self.tool_dir / f"{remaining_parts[0]}.py"
                if module_path.exists():
                    return module_path
            elif len(remaining_parts) > 1:
                module_path = self.tool_dir / "/".join(remaining_parts[:-1]) / f"{remaining_parts[-1]}.py"
                if module_path.exists():
                    return module_path

        # Case 2: Standard package/module.py
        module_path = self.tool_dir / "/".join(parts[:-1]) / f"{parts[-1]}.py"
        if module_path.exists():
            return module_path

        # Try package/__init__.py
        return self.tool_dir / "/".join(parts) / "__init__.py"

    def format_external_imports(self, external_imports: list) -> list[str]:
        """Format external imports as code strings.

        __future__ imports are placed first, then other imports.
        Excluded modules are filtered out.

        Args:
            external_imports: List of external import nodes.

        Returns:
            Formatted import statements.
        """
        future_imports, regular_imports = self._categorize_by_future(external_imports)
        return self._build_import_strings(future_imports, regular_imports)

    def _categorize_by_future(self, external_imports: list) -> tuple[list, list]:
        """Separate imports into __future__ and regular imports.

        Args:
            external_imports: List of import nodes.

        Returns:
            Tuple of (future_imports, regular_imports).
        """
        future_imports = []
        regular_imports = []

        for node in external_imports:
            if self._should_skip_import(node):
                continue

            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                future_imports.append(node)
            else:
                regular_imports.append(node)

        return future_imports, regular_imports

    def _should_skip_import(self, node: ast.Import | ast.ImportFrom) -> bool:
        """Check if import should be skipped (excluded modules).

        Args:
            node: Import node to check.

        Returns:
            True if import should be skipped.
        """
        if isinstance(node, ast.ImportFrom):
            return node.module and any(node.module.startswith(m) for m in self.EXCLUDED_MODULES)
        if isinstance(node, ast.Import):
            return any(alias.name.startswith(m) for m in self.EXCLUDED_MODULES for alias in node.names)
        return False

    @staticmethod
    def _build_import_strings(future_imports: list, regular_imports: list) -> list[str]:
        """Build formatted import strings from import nodes.

        Args:
            future_imports: List of __future__ import nodes.
            regular_imports: List of regular import nodes.

        Returns:
            Formatted import statements.
        """
        result = []

        if future_imports:
            result.append("# Future imports\n")
            for node in future_imports:
                result.append(ast.unparse(node) + "\n")
            result.append("\n")

        if regular_imports:
            result.append("# External imports\n")
            for node in regular_imports:
                result.append(ast.unparse(node) + "\n")
            result.append("\n")

        return result

    def inline_local_imports(
        self,
        local_imports: list,
        processed_modules: set[str] | None = None,
    ) -> tuple[list[str], list]:
        """Inline local imports into bundled code and collect their external imports.

        Recursively inlines nested local imports.

        Args:
            local_imports: List of (module_name, file_path, import_node) tuples.
            processed_modules: Set of already processed module paths to avoid duplicates.

        Returns:
            Tuple of (inlined_code_strings, collected_external_imports).
        """
        if not local_imports:
            return [], []

        if processed_modules is None:
            processed_modules = set()

        result = ["# Inlined local imports\n"]
        all_external_imports = []

        for module_name, file_path, _ in local_imports:
            if str(file_path) in processed_modules:
                continue
            processed_modules.add(str(file_path))

            # Recursively inline nested local imports
            nested_resolver = ImportResolver(file_path.parent)
            with open(file_path, encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            nested_local_imports, nested_external_imports = nested_resolver.categorize_imports(tree)

            if nested_local_imports:
                nested_code, nested_ext_imports = nested_resolver.inline_local_imports(
                    nested_local_imports, processed_modules
                )
                result.extend(nested_code)
                all_external_imports.extend(nested_ext_imports)

            # Inline this module's code
            result.append(f"# --- Inlined from {module_name}.py ---\n")
            code_lines, external_imports = self._extract_module_code(file_path, collect_imports=True)
            result.extend(code_lines)
            all_external_imports.extend(external_imports)
            all_external_imports.extend(nested_external_imports)
            result.append(f"# --- End of {module_name}.py ---\n\n")

        return result, all_external_imports

    def _extract_module_code(
        self,
        file_path: Path,
        *,
        collect_imports: bool = False,
    ) -> tuple[list[str], list] | list[str]:
        """Extract code from module, excluding imports and docstrings.

        Args:
            file_path: Path to the module file.
            collect_imports: If True, also return external imports.

        Returns:
            If collect_imports is True: tuple of (code_lines, external_import_nodes)
            Otherwise: list of code lines.
        """
        with open(file_path, encoding="utf-8") as f:
            local_source = f.read()

        local_tree = ast.parse(local_source)
        tool_dir = file_path.parent

        result, external_imports = self._process_module_nodes(local_tree, tool_dir, collect_imports)

        if collect_imports:
            return result, external_imports
        return result

    def _process_module_nodes(
        self,
        tree: ast.AST,
        tool_dir: Path,
        collect_imports: bool,
    ) -> tuple[list[str], list]:
        """Process AST nodes from a module.

        Args:
            tree: AST tree of the module.
            tool_dir: Directory containing the module.
            collect_imports: Whether to collect external imports.

        Returns:
            Tuple of (code_lines, external_imports).
        """
        result = []
        external_imports = []

        for local_node in tree.body:
            if isinstance(local_node, (ast.Import, ast.ImportFrom)):
                if collect_imports:
                    ext_import = self._get_external_import(local_node, tool_dir)
                    if ext_import:
                        external_imports.append(ext_import)
                continue

            if self._is_docstring(local_node):
                continue

            if isinstance(local_node, ast.ClassDef):
                local_node = self._remove_tool_plugin_decorator(local_node)

            result.append(ast.unparse(local_node) + "\n")

        return result, external_imports

    def _get_external_import(
        self,
        node: ast.Import | ast.ImportFrom,
        tool_dir: Path,
    ) -> ast.Import | ast.ImportFrom | None:
        """Get external import node if not local.

        Args:
            node: Import node to check.
            tool_dir: Directory containing the tool.

        Returns:
            The node if external, None if local.
        """
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("."):
                return None
            temp_resolver = ImportResolver(tool_dir)
            if temp_resolver.is_local_import(node):
                return None
            return node
        if isinstance(node, ast.Import):
            return node
        return None

    @staticmethod
    def _is_docstring(node: ast.stmt) -> bool:
        """Check if AST node is a docstring.

        Args:
            node: AST statement node.

        Returns:
            True if node is a docstring.
        """
        return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)

    @staticmethod
    def _remove_tool_plugin_decorator(node: ast.ClassDef) -> ast.ClassDef:
        """Remove @tool_plugin decorator and BaseTool inheritance from a class node.

        Args:
            node: AST ClassDef node.

        Returns:
            Modified ClassDef node with decorator and base class removed.
        """
        node.decorator_list = ImportResolver._filter_decorators(node.decorator_list)
        node.bases = ImportResolver._filter_bases(node.bases)
        return node

    @staticmethod
    def _filter_decorators(decorator_list: list) -> list:
        """Filter out @tool_plugin decorators.

        Args:
            decorator_list: List of decorator nodes.

        Returns:
            Filtered decorator list.
        """
        filtered = []
        for decorator in decorator_list:
            if ImportResolver._is_tool_plugin_decorator(decorator):
                continue
            filtered.append(decorator)
        return filtered

    @staticmethod
    def _is_tool_plugin_decorator(decorator: ast.expr) -> bool:
        """Check if decorator is @tool_plugin.

        Args:
            decorator: Decorator AST node.

        Returns:
            True if decorator is @tool_plugin.
        """
        if isinstance(decorator, ast.Name) and decorator.id == "tool_plugin":
            return True
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func.id == "tool_plugin"
        ):
            return True
        return False

    @staticmethod
    def _filter_bases(bases: list) -> list:
        """Filter out BaseTool from base classes.

        Args:
            bases: List of base class nodes.

        Returns:
            Filtered base class list.
        """
        filtered = []
        for base in bases:
            is_base_tool = isinstance(base, ast.Name) and base.id == "BaseTool"
            if not is_base_tool:
                filtered.append(base)
        return filtered if filtered else []


def load_class(import_path: str) -> type:
    """Dynamically load a class from its import path.

    Args:
        import_path: Python import path (e.g., 'package.module.ClassName').

    Returns:
        The loaded class.

    Raises:
        ImportError: If the module or class cannot be imported.
    """
    try:
        module_path, class_name = import_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ValueError, ImportError, AttributeError) as e:
        raise ImportError(f"Failed to load class from '{import_path}': {e}") from e
