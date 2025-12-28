"""
Analizador de rustificabilidad (Fase 3).

Recorre el AST de cada función y aplica reglas conservadoras:

- Solo se permiten expresiones aritméticas/booleanas sencillas y bucles sobre
  ``range``/``enumerate`` o colecciones simples.
- Las anotaciones de tipo deben ser primitivas o contenedores simples; tipos
  ambiguos o personalizados degradan a ``PARTIAL`` o ``NO``.
- Operaciones dinámicas (IO, reflexión, async/await, mutaciones complejas) se
  consideran no rustyficables.

La política es pesimista: ante duda, el veredicto se degrada y se registran
las razones para que el usuario pueda refactorizar.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set


class Rustyfiability(Enum):
    FULL = auto()
    PARTIAL = auto()
    NO = auto()


@dataclass(slots=True)
class AnalysisResult:
    target: str
    verdict: Rustyfiability
    reasons: List[str]

    def is_rustyfiable(self) -> bool:
        return self.verdict in (Rustyfiability.FULL, Rustyfiability.PARTIAL)


class Analyzer:
    """
    Analiza código Python para decidir si puede rustyficarse.

    Próximo paso: recorrer AST y aplicar reglas conservadoras.
    """

    def analyze_path(
        self, path: Path, *, excluded_dirs: Iterable[str] | None = None
    ) -> List[AnalysisResult]:
        if not path.exists():
            raise FileNotFoundError(f"No se puede analizar; ruta inexistente: {path}")

        exclusions = {dir_name for dir_name in (excluded_dirs or [])}
        py_files: List[Path] = []

        if path.is_file() and path.suffix == ".py":
            if not self._is_excluded(path, exclusions):
                py_files.append(path)
        elif path.is_dir():
            for candidate in path.rglob("*.py"):
                if candidate.is_file() and not self._is_excluded(candidate, exclusions):
                    py_files.append(candidate)
        else:
            raise ValueError(f"Ruta no soportada para análisis: {path}")

        results: List[AnalysisResult] = []
        for file_path in py_files:
            results.extend(self._analyze_file(file_path))

        return self._merge_results_by_target(results)

    def _analyze_file(self, file_path: Path) -> List[AnalysisResult]:
        try:
            source = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            return [
                AnalysisResult(
                    target=str(file_path),
                    verdict=Rustyfiability.NO,
                    reasons=[f"No se pudo leer el archivo: {exc}"],
                )
            ]

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as exc:
            return [
                AnalysisResult(
                    target=str(file_path),
                    verdict=Rustyfiability.NO,
                    reasons=[f"Error de sintaxis: {exc}"],
                )
            ]

        imports = self._collect_imports(tree)
        external_imports = self._detect_external_imports(imports)
        results: List[AnalysisResult] = []

        class _TargetVisitor(ast.NodeVisitor):
            def __init__(self, external_imports: Set[str]):
                self.external_imports = external_imports
                self.context_stack: List[str] = []

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                self.context_stack.append(node.name)
                self.generic_visit(node)
                self.context_stack.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self._analyze_function(node)
                self.context_stack.append(node.name)
                self.generic_visit(node)
                self.context_stack.pop()

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                self._analyze_function(node)
                self.context_stack.append(node.name)
                self.generic_visit(node)
                self.context_stack.pop()

            def _analyze_function(
                self, node: ast.FunctionDef | ast.AsyncFunctionDef
            ) -> None:
                visitor = _FunctionAnalyzer(self.external_imports)
                visitor.visit(node)

                reasons = list(visitor.reasons)
                if not reasons:
                    reasons.append(
                        "Sin hallazgos restrictivos; solo estructuras aritméticas/booleanas y control simple"
                    )

                qualified_name = ".".join([*self.context_stack, node.name])
                results.append(
                    AnalysisResult(
                        target=f"{file_path}:{qualified_name}",
                        verdict=visitor.verdict,
                        reasons=reasons,
                    )
                )

        _TargetVisitor(external_imports).visit(tree)

        if not results:
            reasons = ["No se encontraron funciones; análisis limitado"]
            if external_imports:
                reasons.append(
                    "Dependencias externas detectadas sin ámbito de función para evaluar"
                )
            results.append(
                AnalysisResult(
                    target=str(file_path),
                    verdict=Rustyfiability.NO
                    if external_imports
                    else Rustyfiability.PARTIAL,
                    reasons=reasons,
                )
            )

        return results

    def _is_excluded(self, file_path: Path, exclusions: Set[str]) -> bool:
        return any(part in exclusions for part in file_path.parts)

    def _merge_results_by_target(
        self, results: Sequence[AnalysisResult]
    ) -> List[AnalysisResult]:
        merged: Dict[str, AnalysisResult] = {}

        for result in results:
            if result.target not in merged:
                merged[result.target] = AnalysisResult(
                    target=result.target,
                    verdict=result.verdict,
                    reasons=list(result.reasons),
                )
                continue

            existing = merged[result.target]
            existing.verdict = self._worst_verdict(existing.verdict, result.verdict)
            existing.reasons.extend(reason for reason in result.reasons if reason not in existing.reasons)

        return list(merged.values())

    @staticmethod
    def _worst_verdict(left: Rustyfiability, right: Rustyfiability) -> Rustyfiability:
        order = {Rustyfiability.FULL: 0, Rustyfiability.PARTIAL: 1, Rustyfiability.NO: 2}
        return left if order[left] >= order[right] else right

    @staticmethod
    def _collect_imports(tree: ast.AST) -> Set[str]:
        modules: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module.split(".")[0])
        return modules

    @staticmethod
    def _detect_external_imports(modules: Set[str]) -> Set[str]:
        allowed = {
            "typing",
            "types",
            "dataclasses",
            "enum",
            "collections",
            "functools",
            "itertools",
            "math",
            "pathlib",
            "builtins",
        }

        return {module for module in modules if module not in allowed}


class _FunctionAnalyzer(ast.NodeVisitor):
    _ALLOWED_BIN_OPS = (
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
    )
    _ALLOWED_UNARY_OPS = (ast.UAdd, ast.USub, ast.Not)
    _ALLOWED_BOOL_OPS = (ast.And, ast.Or)
    _ALLOWED_COMPARE_OPS = (
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
    )
    _BASIC_ITER_CALLS = {"range", "enumerate"}
    _BASIC_NUMERIC_CALLS = {"len", "abs"}
    _PRIMITIVE_ANNOTATIONS = {
        "int",
        "float",
        "str",
        "bool",
        "bytes",
        "None",
        "NoneType",
    }
    _CONTAINER_ANNOTATIONS = {
        "list",
        "dict",
        "set",
        "tuple",
        "List",
        "Dict",
        "Set",
        "Tuple",
        "Sequence",
        "Mapping",
        "Iterable",
    }
    _AMBIGUOUS_ANNOTATIONS = {"Any", "object"}
    _OPTIONAL_ANNOTATIONS = {"Optional", "Union"}
    _MUTATING_METHODS = {
        "append",
        "extend",
        "insert",
        "pop",
        "remove",
        "clear",
        "update",
        "add",
        "discard",
        "setdefault",
    }

    def __init__(self, external_imports: Set[str]):
        self.verdict: Rustyfiability = Rustyfiability.FULL
        self.reasons: List[str] = []
        self.external_imports = external_imports
        for module in external_imports:
            self._note_no(f"Dependencia externa no tipificada detectada: {module}")

    def _note_no(self, reason: str) -> None:
        if reason not in self.reasons:
            self.reasons.append(reason)
        self.verdict = Rustyfiability.NO

    def _note_partial(self, reason: str) -> None:
        if reason not in self.reasons:
            self.reasons.append(reason)
        if self.verdict is Rustyfiability.FULL:
            self.verdict = Rustyfiability.PARTIAL

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_signature(node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name) and func.id in {"open", "print"}:
            self._note_no(f"IO detectado mediante llamada a {func.id}()")
        elif isinstance(func, ast.Name) and func.id in {"getattr", "setattr", "eval", "exec"}:
            self._note_no(f"Reflexión/dinamicidad detectada: {func.id}()")
        elif isinstance(func, ast.Attribute):
            attr_name = func.attr
            if attr_name in self._MUTATING_METHODS:
                self._note_partial(f"Mutación de contenedor mediante {attr_name}()")
            if isinstance(func.value, ast.Name):
                qualifier = func.value.id
                if qualifier in {"os", "subprocess"}:
                    self._note_no(f"IO/sistema operativo detectado: {qualifier}.{attr_name}()")
                elif qualifier == "inspect":
                    self._note_no("Reflexión mediante inspect.*")
                elif attr_name in {"eval", "exec", "__getattr__"}:
                    self._note_no(f"Reflexión indirecta mediante {qualifier}.{attr_name}()")
            if attr_name == "__dict__":
                self._note_no("Acceso dinámico a __dict__")
            elif attr_name in {"eval", "exec", "__getattr__"}:
                self._note_no(f"Reflexión indirecta mediante atributo {attr_name}()")

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_signature(node)
        self._note_no("Función async/await detectada; requiere runtime/concurrencia no cubierta")
        self.generic_visit(node)

    def visit_Await(self, node: ast.Await) -> None:
        self._note_no("Uso de await detectado; modelo async no soportado")
        self.generic_visit(node)

    def visit_Yield(self, node: ast.Yield) -> None:
        self._note_partial("Generador con yield; necesita soporte de iteradores")
        self.generic_visit(node)

    def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
        self._note_partial("Generador con yield from; requiere soporte de iteradores")
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        if not self._is_basic_iterable(node.iter):
            self._note_partial(
                "Bucle for con iterable no permitido; solo range/enumerate o colecciones simples"
            )
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        if not self._is_simple_condition(node.test):
            self._note_partial(
                "Condición while fuera del allowlist (comparaciones/aritmética simple)"
            )
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        if not self._is_simple_condition(node.test):
            self._note_partial(
                "Condición if fuera del allowlist (comparaciones/booleanos sencillos)"
            )
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        if node.exc is not None:
            self._note_no("Manejo de excepciones dinámico mediante raise no literal")
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self._note_partial("Bloque try/except/finally; mapeo a Result/error handling requerido")
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self._note_partial("Uso de with/context manager; traducir a RAII/manual")
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        self._note_no("Declaración global detectada; estado compartido no seguro")
        self.generic_visit(node)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self._note_no("Declaración nonlocal detectada; captura de cierre mutable")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr == "__dict__":
            self._note_no("Acceso dinámico a __dict__")
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._note_partial("Comprensión de listas detectada; podría requerir soporte adicional")
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._note_partial("Comprensión de conjuntos detectada; compatibilidad parcial")
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._note_partial("Comprensión de diccionarios detectada; compatibilidad parcial")
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._note_partial("Expresión generadora detectada; compatibilidad parcial")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if any(isinstance(target, ast.Subscript) for target in node.targets):
            self._note_partial("Mutación de contenedores por subscripción")
        if any(isinstance(target, ast.Attribute) for target in node.targets):
            self._note_partial("Asignación a atributos de objetos externos; puede requerir mutabilidad explícita")
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._note_partial("Asignación aumentada detectada; mutación in-situ")
        if isinstance(node.target, ast.Attribute):
            self._note_partial("Asignación aumentada sobre atributos externos; requiere traducción manual")
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        if not isinstance(node.op, self._ALLOWED_BOOL_OPS) or not all(
            self._is_simple_condition(value) for value in node.values
        ):
            self._note_partial(
                "Expresión booleana compleja; operadores fuera del allowlist"
            )
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        if not self._is_allowed_binop(node):
            self._note_partial(
                "Operación aritmética no permitida o con operandos complejos"
            )
        self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        if not self._is_allowed_unary(node):
            self._note_partial(
                "Operación unaria no permitida; solo -, +, not sobre valores simples"
            )
        self.generic_visit(node)

    def visit_Break(self, node: ast.Break) -> None:
        self.generic_visit(node)

    def visit_Continue(self, node: ast.Continue) -> None:
        self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._note_no("Expresión lambda detectada; requiere traducción manual")
        self.generic_visit(node)

    def visit_Call_mutation(self, node: ast.Call) -> None:
        """Hook reservado si se quisieran distinguir mutaciones explícitas."""
        self.generic_visit(node)

    def _check_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        arguments = node.args

        for arg in [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]:
            self._classify_parameter(arg)

        if arguments.vararg is not None:
            self._classify_variadic(arguments.vararg, variadic_label="*args")

        if arguments.kwarg is not None:
            self._classify_variadic(arguments.kwarg, variadic_label="**kwargs")

        quality, detail = self._classify_annotation(node.returns)
        if quality == "missing":
            self._note_partial("Retorno sin anotación de tipo")
        elif quality == "ambiguous":
            self._note_partial(f"Anotación de retorno ambigua: {detail}")
        elif quality == "complex":
            self._note_no(f"Tipo de retorno complejo o personalizado: {detail}")

    def _classify_parameter(self, arg: ast.arg) -> None:
        quality, detail = self._classify_annotation(arg.annotation)
        if quality == "missing":
            self._note_partial(f"Argumento '{arg.arg}' sin anotación de tipo")
        elif quality == "ambiguous":
            self._note_partial(f"Anotación ambigua para '{arg.arg}': {detail}")
        elif quality == "complex":
            self._note_no(f"Tipo complejo o personalizado en argumento '{arg.arg}': {detail}")

    def _classify_variadic(self, arg: ast.arg, *, variadic_label: str) -> None:
        quality, detail = self._classify_annotation(arg.annotation)
        if quality == "missing":
            self._note_no(f"{variadic_label} sin anotación de tipo; potencial mutabilidad/opacidad")
        elif quality == "ambiguous":
            self._note_partial(f"{variadic_label} con anotación ambigua: {detail}")
        elif quality == "complex":
            self._note_no(f"{variadic_label} con tipo complejo o personalizado: {detail}")

    def _classify_annotation(self, annotation: ast.AST | None) -> tuple[str, str]:
        if annotation is None:
            return "missing", "sin anotación"

        if isinstance(annotation, ast.Constant) and annotation.value is None:
            return "ok", "None"

        if isinstance(annotation, ast.Name):
            if annotation.id in self._PRIMITIVE_ANNOTATIONS:
                return "ok", annotation.id
            if annotation.id in self._CONTAINER_ANNOTATIONS:
                return "ambiguous", annotation.id
            if annotation.id in self._AMBIGUOUS_ANNOTATIONS:
                return "ambiguous", annotation.id
            return "complex", annotation.id

        if isinstance(annotation, ast.Attribute):
            simple_name = self._get_annotation_simple_name(annotation)
            if simple_name in self._PRIMITIVE_ANNOTATIONS:
                return "ok", self._annotation_to_str(annotation)
            if simple_name in self._CONTAINER_ANNOTATIONS:
                return "ambiguous", self._annotation_to_str(annotation)
            if simple_name in self._AMBIGUOUS_ANNOTATIONS:
                return "ambiguous", self._annotation_to_str(annotation)
            return "complex", self._annotation_to_str(annotation)

        if isinstance(annotation, ast.Subscript):
            base_name = self._get_annotation_simple_name(annotation.value)
            children = self._get_subscript_args(annotation.slice)

            if base_name in self._OPTIONAL_ANNOTATIONS:
                aggregated = self._aggregate_annotation_quality(children)
                if aggregated == "complex":
                    return "complex", self._annotation_to_str(annotation)
                if aggregated == "ambiguous":
                    return "ambiguous", self._annotation_to_str(annotation)
                return "ok", self._annotation_to_str(annotation)

            if base_name in self._CONTAINER_ANNOTATIONS:
                if not children:
                    return "ambiguous", self._annotation_to_str(annotation)
                aggregated = self._aggregate_annotation_quality(children)
                if aggregated == "complex":
                    return "complex", self._annotation_to_str(annotation)
                if aggregated == "ambiguous":
                    return "ambiguous", self._annotation_to_str(annotation)
                return "ok", self._annotation_to_str(annotation)

            return "complex", self._annotation_to_str(annotation)

        return "complex", self._annotation_to_str(annotation)

    def _aggregate_annotation_quality(self, children: List[ast.AST]) -> str:
        worst = "ok"
        for child in children:
            quality, _ = self._classify_annotation(child)
            worst = self._worst_annotation_quality(worst, quality)
        return worst

    @staticmethod
    def _worst_annotation_quality(left: str, right: str) -> str:
        order = {"ok": 0, "ambiguous": 1, "missing": 1, "complex": 2}
        return left if order.get(left, 2) >= order.get(right, 2) else right

    @staticmethod
    def _get_subscript_args(node: ast.AST) -> List[ast.AST]:
        if isinstance(node, ast.Tuple):
            return list(node.elts)
        return [node]

    @staticmethod
    def _get_annotation_simple_name(node: ast.AST) -> str | None:
        try:
            text = ast.unparse(node)
        except Exception:
            return None
        return text.split(".")[-1]

    @staticmethod
    def _annotation_to_str(node: ast.AST) -> str:
        try:
            return ast.unparse(node)
        except Exception:
            return repr(node)

    def _is_allowed_binop(self, node: ast.BinOp) -> bool:
        return isinstance(node.op, self._ALLOWED_BIN_OPS) and self._is_simple_numeric(node.left) and self._is_simple_numeric(node.right)

    def _is_allowed_unary(self, node: ast.UnaryOp) -> bool:
        return isinstance(node.op, self._ALLOWED_UNARY_OPS) and self._is_simple_numeric(node.operand)

    def _is_simple_numeric(self, node: ast.AST) -> bool:
        if isinstance(node, (ast.Constant, ast.Name)):
            return True
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            return True
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, self._ALLOWED_UNARY_OPS):
            return self._is_simple_numeric(node.operand)
        if isinstance(node, ast.BinOp) and isinstance(node.op, self._ALLOWED_BIN_OPS):
            return self._is_simple_numeric(node.left) and self._is_simple_numeric(node.right)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return (
                node.func.id in self._BASIC_NUMERIC_CALLS
                and not node.keywords
                and all(self._is_simple_numeric(arg) for arg in node.args)
            )
        return False

    def _is_simple_condition(self, node: ast.AST) -> bool:
        if isinstance(node, (ast.Constant, ast.Name)):
            return True
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return self._is_simple_condition(node.operand)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, self._ALLOWED_BOOL_OPS):
            return all(self._is_simple_condition(value) for value in node.values)
        if isinstance(node, ast.Compare):
            return all(isinstance(op, self._ALLOWED_COMPARE_OPS) for op in node.ops) and self._is_simple_numeric(node.left) and all(
                self._is_simple_numeric(comparator) for comparator in node.comparators
            )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return (
                node.func.id in self._BASIC_NUMERIC_CALLS
                and not node.keywords
                and all(self._is_simple_numeric(arg) for arg in node.args)
            )
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            return True
        return False

    def _is_basic_iterable(self, node: ast.AST) -> bool:
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return all(self._is_simple_numeric(elt) for elt in node.elts)
        if isinstance(node, (ast.Name, ast.Attribute)):
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return (
                node.func.id in self._BASIC_ITER_CALLS
                and not node.keywords
                and all(self._is_simple_numeric(arg) for arg in node.args)
            )
        return False



__all__ = ["Analyzer", "AnalysisResult", "Rustyfiability"]
