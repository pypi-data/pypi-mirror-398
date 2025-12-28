"""
Transpilador Py → IR → Rust (Fases 4 y 5).

Implementa un IR propio y validaciones de tipos simples para desacoplar el AST
de Python de la etapa de generación de Rust. El backend actual usa plantillas
sencillas para visualizar el IR y servir como base de la fase 5.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Protocol

from pyrust.analyzer import Rustyfiability


class IRValidationError(ValueError):
    """Error levantado cuando el AST contiene constructos no soportados en el IR."""


@dataclass(slots=True)
class IRNode:
    kind: str
    value: str | None = None
    children: List["IRNode"] = field(default_factory=list)

    def add_child(self, node: "IRNode") -> None:
        self.children.append(node)


@dataclass(slots=True)
class IRFunction:
    name: str
    args: List[str]
    body: List[IRNode]
    arg_types: Dict[str, str] = field(default_factory=dict)
    return_type: str | None = None
    issues: List[str] = field(default_factory=list)
    verdict: Optional[Rustyfiability] = None
    analysis_reasons: Optional[List[str]] = None


class TranspilerBackend(Protocol):
    def emit(self, func: IRFunction, *, release_gil: bool | None = None) -> str:
        ...


class Transpiler:
    """
    Convierte funciones Python a IR y luego a Rust.

    La implementación actual valida tipos simples en la firma, traduce un
    subconjunto del AST a nodos de IR y delega el renderizado a un backend de
    plantillas Rust.
    """

    _PRIMITIVE_TYPES = {"int", "float", "bool", "str", "None"}
    _VECTOR_ELEMENT_TYPES = {"int", "float", "bool", "str"}
    _SIMPLE_TYPES = _PRIMITIVE_TYPES | {f"list[{name}]" for name in _VECTOR_ELEMENT_TYPES}
    _SUPPORTED_CALLS = {"range", "len", "enumerate", "abs", "sum", "map", "filter", "zip"}

    def build_ir_skeleton(self, function_name: str, args: List[str]) -> IRFunction:
        """Método legado para conservar compatibilidad con el stub inicial."""
        root = IRNode(kind="body")
        return IRFunction(name=function_name, args=args, body=[root])

    def function_to_ir(
        self,
        node: ast.FunctionDef,
        *,
        verdict: Rustyfiability | None = None,
        analysis_reasons: Iterable[str] | None = None,
    ) -> IRFunction:
        arg_types: Dict[str, str] = {}
        issues: List[str] = []
        for arg in node.args.posonlyargs + node.args.args:
            arg_types[arg.arg] = self._validate_type_annotation(arg.annotation, f"argumento '{arg.arg}'")

        if node.args.vararg is not None or node.args.kwarg is not None:
            raise IRValidationError("Argumentos variádicos no soportados en el IR intermedio")
        if node.args.kwonlyargs:
            raise IRValidationError("Argumentos keyword-only no soportados en el IR intermedio")

        return_type: str | None = None
        if node.returns is None:
            issues.append("Retorno sin anotación; se asume None")
            return_type = "None"
        else:
            return_type = self._validate_type_annotation(node.returns, "retorno")

        body_nodes: List[IRNode] = []
        for stmt in node.body:
            if self._is_docstring(stmt):
                continue
            body_nodes.append(self._convert_statement(stmt))

        return IRFunction(
            name=node.name,
            args=list(arg_types.keys()),
            body=body_nodes,
            arg_types=arg_types,
            return_type=return_type,
            issues=issues,
            verdict=verdict,
            analysis_reasons=list(analysis_reasons or []),
        )

    def from_source(self, source: str, *, function_name: str | None = None) -> IRFunction:
        """
        Parsea código fuente y devuelve el IR de la función solicitada.

        Si ``function_name`` no se proporciona y solo hay una función en el
        módulo, se selecciona automáticamente.
        """

        tree = ast.parse(source)
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        if not functions:
            raise IRValidationError("No se encontró ninguna función en el código fuente")

        target: ast.FunctionDef | None = None
        if function_name is None:
            if len(functions) > 1:
                raise IRValidationError(
                    "Varias funciones encontradas; especifique function_name para desambiguar"
                )
            target = functions[0]
        else:
            for fn in functions:
                if fn.name == function_name:
                    target = fn
                    break
            if target is None:
                raise IRValidationError(f"No se encontró la función solicitada: {function_name}")

        return self.function_to_ir(target)

    def render(
        self, ir_func: IRFunction, backend: TranspilerBackend, *, release_gil: bool | None = None
    ) -> str:
        if ir_func.verdict is Rustyfiability.NO:
            raise IRValidationError(
                "La función está marcada como NO por el analizador y no puede renderizarse"
            )
        return backend.emit(ir_func, release_gil=release_gil)

    def _validate_type_annotation(self, annotation: ast.AST | None, context: str) -> str:
        if annotation is None:
            raise IRValidationError(f"Falta anotación de tipo para {context}")

        normalized = self._normalize_annotation(annotation)
        if normalized not in self._SIMPLE_TYPES:
            raise IRValidationError(
                f"Tipo no soportado en {context}: {normalized}. Solo se aceptan {sorted(self._SIMPLE_TYPES)}"
            )

        return normalized

    def _normalize_annotation(self, annotation: ast.AST) -> str:
        """
        Normaliza anotaciones de tipo simples y listas parametrizadas (``list[int]``).
        """

        if isinstance(annotation, ast.Name):
            return annotation.id
        if isinstance(annotation, ast.Attribute):
            return annotation.attr
        if isinstance(annotation, ast.Subscript):
            base = self._normalize_annotation(annotation.value)
            slice_node = annotation.slice
            if base.lower() == "list":
                inner = self._normalize_annotation(slice_node)  # type: ignore[arg-type]
                return f"list[{inner}]"
        try:
            text = ast.unparse(annotation)
        except Exception as exc:  # pragma: no cover - ast.unparse errores raros
            raise IRValidationError(f"No se pudo normalizar la anotación: {exc}") from exc
        return text.replace(" ", "")

    def _convert_statement(self, node: ast.stmt) -> IRNode:
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1:
                raise IRValidationError("Asignaciones múltiples no están soportadas")
            target_node = node.targets[0]
            if isinstance(target_node, ast.Subscript):
                list_name, index_expr = self._parse_subscript_target(target_node)
                value_expr = self._convert_expression(node.value)
                return IRNode(kind="list_setitem", value=list_name, children=[index_expr, value_expr])
            target = self._target_name(target_node)
            expr = self._convert_expression(node.value)
            return IRNode(kind="assign", value=target, children=[expr])

        if isinstance(node, ast.AnnAssign):
            target = self._target_name(node.target)
            expr = self._convert_expression(node.value) if node.value is not None else IRNode(kind="const", value="None")
            # Validamos la anotación local, aunque el tipo no se usa todavía.
            self._validate_type_annotation(node.annotation, f"variable local '{target}'")
            return IRNode(kind="assign", value=target, children=[expr])

        if isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Subscript):
                list_name, index_expr = self._parse_subscript_target(node.target)
                current_value = self._convert_expression(node.target)
                bin_expr = IRNode(
                    kind="binop",
                    value=self._binop_name(node.op),
                    children=[current_value, self._convert_expression(node.value)],
                )
                return IRNode(kind="list_setitem", value=list_name, children=[index_expr, bin_expr])
            target = self._target_name(node.target)
            expr = IRNode(
                kind="binop",
                value=self._binop_name(node.op),
                children=[self._convert_expression(node.target), self._convert_expression(node.value)],
            )
            return IRNode(kind="assign", value=target, children=[expr])

        if isinstance(node, ast.Return):
            child = self._convert_expression(node.value) if node.value is not None else None
            return IRNode(kind="return", children=[child] if child else [])

        if isinstance(node, ast.For):
            target = self._target_name(node.target)
            iter_expr = self._convert_expression(node.iter)
            body_nodes = [self._convert_statement(stmt) for stmt in self._filter_docstrings(node.body)]
            return IRNode(kind="for", value=target, children=[iter_expr, *body_nodes])

        if isinstance(node, ast.If):
            condition = self._convert_expression(node.test)
            body = IRNode(kind="block", children=[self._convert_statement(stmt) for stmt in self._filter_docstrings(node.body)])
            orelse = IRNode(
                kind="else",
                children=[self._convert_statement(stmt) for stmt in self._filter_docstrings(node.orelse)],
            )
            return IRNode(kind="if", children=[condition, body, orelse])

        if isinstance(node, ast.Expr):
            return IRNode(kind="expr", children=[self._convert_expression(node.value)])

        raise IRValidationError(f"Instrucción no soportada en el IR: {ast.dump(node, include_attributes=False)}")

    def _convert_expression(self, node: ast.AST) -> IRNode:
        if isinstance(node, ast.Constant):
            return IRNode(kind="const", value=repr(node.value))

        if isinstance(node, ast.List):
            return IRNode(kind="list_literal", children=[self._convert_expression(elt) for elt in node.elts])

        if isinstance(node, ast.Name):
            return IRNode(kind="var", value=node.id)

        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            return IRNode(kind="var", value=f"{node.value.id}.{node.attr}")

        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name):
                index_expr = self._convert_expression(node.slice)
                return IRNode(kind="subscript", value=node.value.id, children=[index_expr])
            raise IRValidationError("Solo se soportan índices sobre variables simples en el IR")

        if isinstance(node, ast.BinOp):
            return IRNode(
                kind="binop",
                value=self._binop_name(node.op),
                children=[self._convert_expression(node.left), self._convert_expression(node.right)],
            )

        if isinstance(node, ast.UnaryOp):
            return IRNode(
                kind="unaryop",
                value=self._unaryop_name(node.op),
                children=[self._convert_expression(node.operand)],
            )

        if isinstance(node, ast.BoolOp):
            return IRNode(
                kind="boolop",
                value=self._boolop_name(node.op),
                children=[self._convert_expression(value) for value in node.values],
            )

        if isinstance(node, ast.Compare):
            ops = [self._compare_op_name(op) for op in node.ops]
            terms = [node.left, *node.comparators]
            if len(ops) == 1:
                children = [self._convert_expression(term) for term in terms]
                return IRNode(kind="compare", value=ops[0], children=children)
            captured_terms = [
                IRNode(kind="capture", value=f"__cmp_term_{idx}", children=[self._convert_expression(term)])
                for idx, term in enumerate(terms)
            ]
            return IRNode(kind="chain_compare", value=",".join(ops), children=captured_terms)

        if isinstance(node, ast.Lambda):
            if node.args.vararg is not None or node.args.kwarg is not None:
                raise IRValidationError("Lambdas con argumentos variádicos no están soportadas en el IR")
            if node.args.kwonlyargs:
                raise IRValidationError("Lambdas con argumentos keyword-only no están soportadas en el IR")
            if node.args.defaults:
                raise IRValidationError("Lambdas con valores por defecto no están soportadas en el IR")
            arg_names = [arg.arg for arg in node.args.posonlyargs + node.args.args]
            body = self._convert_expression(node.body)
            return IRNode(kind="lambda", value=",".join(arg_names), children=[body])

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                list_name = func.value.id
                if func.attr == "append":
                    if len(node.args) != 1:
                        raise IRValidationError("append() espera exactamente un valor a añadir")
                    child = self._convert_expression(node.args[0])
                    return IRNode(kind="list_append", value=list_name, children=[child])
                if func.attr == "extend":
                    if len(node.args) != 1:
                        raise IRValidationError("extend() espera exactamente un iterable")
                    child = self._convert_expression(node.args[0])
                    return IRNode(kind="list_extend", value=list_name, children=[child])
                raise IRValidationError(f"Método no soportado en listas: {func.attr}")
            if isinstance(func, ast.Name) and func.id in self._SUPPORTED_CALLS:
                if func.id == "sum":
                    if len(node.args) not in (1, 2):
                        raise IRValidationError("sum() soporta un iterable y un start opcional")
                    children = [self._convert_expression(node.args[0])]
                    if len(node.args) == 2:
                        children.append(self._convert_expression(node.args[1]))
                    return IRNode(kind="sum", children=children)
                if func.id == "map":
                    if len(node.args) < 2:
                        raise IRValidationError("map() espera al menos una función y un iterable")
                    func_expr = self._convert_expression(node.args[0])
                    iterables = [self._convert_expression(arg) for arg in node.args[1:]]
                    if func_expr.kind == "lambda":
                        lambda_params = self._lambda_params_from_ir(func_expr)
                        if len(lambda_params) != len(iterables):
                            raise IRValidationError(
                                "La lambda de map() debe tener la misma cantidad de parámetros que iterables"
                            )
                    return IRNode(kind="map", children=[func_expr, *iterables])
                if func.id == "filter":
                    if len(node.args) != 2:
                        raise IRValidationError("filter() espera exactamente dos argumentos: predicado e iterable")
                    predicate = self._convert_expression(node.args[0])
                    if predicate.kind == "lambda":
                        lambda_params = self._lambda_params_from_ir(predicate)
                        if len(lambda_params) != 1:
                            raise IRValidationError("La lambda de filter() debe tener exactamente un parámetro")
                    return IRNode(
                        kind="filter",
                        children=[predicate, self._convert_expression(node.args[1])],
                    )
                if func.id == "zip":
                    if len(node.args) < 2:
                        raise IRValidationError("zip() requiere al menos dos iterables para encadenar")
                    return IRNode(kind="zip", children=[self._convert_expression(arg) for arg in node.args])
                return IRNode(
                    kind="call",
                    value=func.id,
                    children=[self._convert_expression(arg) for arg in node.args],
                )
            raise IRValidationError(f"Llamada no soportada en el IR: {ast.unparse(node)}")

        raise IRValidationError(f"Expresión no soportada en el IR: {ast.dump(node, include_attributes=False)}")

    @staticmethod
    def _target_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        raise IRValidationError(f"Destino de asignación no soportado: {ast.dump(node, include_attributes=False)}")

    def _parse_subscript_target(self, node: ast.Subscript) -> tuple[str, IRNode]:
        if not isinstance(node.value, ast.Name):
            raise IRValidationError("Solo se soportan asignaciones a índices de variables simples")
        return node.value.id, self._convert_expression(node.slice)

    @staticmethod
    def _binop_name(op: ast.AST) -> str:
        mapping = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "//",
            ast.Mod: "%",
        }
        for ast_type, label in mapping.items():
            if isinstance(op, ast_type):
                return label
        raise IRValidationError(f"Operador binario no soportado: {op}")

    @staticmethod
    def _unaryop_name(op: ast.AST) -> str:
        if isinstance(op, ast.USub):
            return "-"
        if isinstance(op, ast.UAdd):
            return "+"
        if isinstance(op, ast.Not):
            return "not"
        raise IRValidationError(f"Operador unario no soportado: {op}")

    @staticmethod
    def _boolop_name(op: ast.AST) -> str:
        if isinstance(op, ast.And):
            return "and"
        if isinstance(op, ast.Or):
            return "or"
        raise IRValidationError(f"Operador booleano no soportado: {op}")

    @staticmethod
    def _compare_op_name(op: ast.AST) -> str:
        mapping = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
        }
        for ast_type, label in mapping.items():
            if isinstance(op, ast_type):
                return label
        raise IRValidationError(f"Comparador no soportado: {op}")

    @staticmethod
    def _is_docstring(node: ast.AST) -> bool:
        return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)

    @staticmethod
    def _filter_docstrings(nodes: Iterable[ast.stmt]) -> List[ast.stmt]:
        return [node for node in nodes if not Transpiler._is_docstring(node)]

    @staticmethod
    def _lambda_params_from_ir(node: IRNode) -> List[str]:
        return node.value.split(",") if node.value else []


def _collect_mutations_from_expr(node: IRNode) -> set[str]:
    mutated: set[str] = set()
    if node.kind in {"list_append", "list_extend", "list_setitem"} and node.value:
        mutated.add(node.value)
    for child in node.children:
        mutated.update(_collect_mutations_from_expr(child))
    return mutated


def _collect_mutated_vars(nodes: List[IRNode]) -> set[str]:
    mutated: set[str] = set()
    for node in nodes:
        if node.kind in {"assign", "list_setitem", "list_append", "list_extend"} and node.value:
            mutated.add(node.value)
        if node.kind == "expr" and node.children:
            mutated.update(_collect_mutations_from_expr(node.children[0]))
        if node.kind == "for":
            if node.children:
                mutated.update(_collect_mutations_from_expr(node.children[0]))
                mutated.update(_collect_mutated_vars(node.children[1:]))
        if node.kind == "if" and len(node.children) >= 3:
            mutated.update(_collect_mutations_from_expr(node.children[0]))
            mutated.update(_collect_mutated_vars(node.children[1].children))
            mutated.update(_collect_mutated_vars(node.children[2].children))
    return mutated


class RustTemplateBackend:
    """
    Backend básico que renderiza IR a un esqueleto de función Rust.

    No produce código compilable en todos los casos, pero sirve como guía y
    punto de partida para la fase 5 (integración con pyo3).
    """

    _TYPE_MAP = {
        "int": "i64",
        "float": "f64",
        "bool": "bool",
        "str": "String",
        "None": "()",
        "list[int]": "Vec<i64>",
        "list[float]": "Vec<f64>",
        "list[bool]": "Vec<bool>",
        "list[str]": "Vec<String>",
    }

    def __init__(self, *, indent: str = "    "):
        self.indent = indent

    @staticmethod
    def _lambda_params(node: IRNode) -> List[str]:
        return node.value.split(",") if node.value else []

    @staticmethod
    def _zip_pattern(names: List[str]) -> str:
        if not names:
            return "()"
        pattern = names[0]
        for name in names[1:]:
            pattern = f"({pattern}, {name})"
        return pattern

    def _render_lambda(self, node: IRNode, *, param_pattern: str | None = None) -> str:
        params = param_pattern if param_pattern is not None else ", ".join(self._lambda_params(node))
        body = self._render_expr(node.children[0]) if node.children else "()"
        return f"|{params}| {body}"

    def emit(self, func: IRFunction, *, release_gil: bool | None = None) -> str:
        mutated = _collect_mutated_vars(func.body)
        args_sig = ", ".join(
            f"{'mut ' if name in mutated else ''}{name}: {self._map_type(func.arg_types.get(name, 'int'))}"
            for name in func.args
        )
        ret_sig = self._map_type(func.return_type or "None")
        lines = [
            "// Código generado por PyRust (fase 4)",
            f"// Veredicto de análisis: {func.verdict.name if func.verdict else 'desconocido'}",
        f"pub fn {func.name}({args_sig}) -> {ret_sig} {{",
        ]

        bindings: dict[str, bool] = {name: name in mutated for name in func.args}
        lines.extend(self._render_body(func.body, bindings, mutated, level=1))
        lines.append("}")
        return "\n".join(lines)

    def _render_body(
        self, nodes: List[IRNode], bindings: dict[str, bool], mutated: set[str], level: int
    ) -> List[str]:
        lines: List[str] = []
        for node in nodes:
            prefix = self.indent * level
            if node.kind == "assign":
                target = node.value or "_tmp"
                expr = self._render_expr(node.children[0])
                if target not in bindings:
                    is_mut = target in mutated
                    bindings[target] = is_mut
                    decl = "let mut " if is_mut else "let "
                    lines.append(f"{prefix}{decl}{target} = {expr};")
                else:
                    lines.append(f"{prefix}{target} = {expr};")
            elif node.kind == "list_setitem":
                target = node.value or "_vec"
                index = self._render_expr(node.children[0])
                value = self._render_expr(node.children[1])
                if target not in bindings:
                    bindings[target] = True
                    lines.append(f"{prefix}let mut {target}: Vec<_> = Vec::new();")
                elif not bindings[target] and target in mutated:
                    lines.append(f"{prefix}let mut {target} = {target};")
                    bindings[target] = True
                lines.append(f"{prefix}{target}[{index} as usize] = {value};")
            elif node.kind == "return":
                expr = self._render_expr(node.children[0]) if node.children else ""
                lines.append(f"{prefix}return {expr};")
            elif node.kind == "for":
                target = node.value or "_item"
                iter_expr = self._render_expr(node.children[0])
                lines.append(f"{prefix}for {target} in {iter_expr} {{")
                lines.extend(self._render_body(node.children[1:], bindings, mutated, level + 1))
                lines.append(f"{prefix}}}")
            elif node.kind == "if":
                condition = self._render_expr(node.children[0])
                lines.append(f"{prefix}if {condition} {{")
                lines.extend(self._render_body(node.children[1].children, bindings, mutated, level + 1))
                lines.append(f"{prefix}}}")
                else_block = node.children[2]
                if else_block.children:
                    lines.append(f"{prefix}else {{")
                    lines.extend(self._render_body(else_block.children, bindings, mutated, level + 1))
                    lines.append(f"{prefix}}}")
            elif node.kind == "expr":
                expr = self._render_expr(node.children[0])
                lines.append(f"{prefix}let _ = {expr};")
            else:  # pragma: no cover - guardia futura
                lines.append(f"{prefix}// nodo IR no renderizado: {node.kind}")
        return lines

    def _render_expr(self, node: IRNode) -> str:
        if node.kind == "const":
            return str(node.value)
        if node.kind == "var":
            return str(node.value)
        if node.kind == "list_literal":
            if not node.children:
                return "Vec::new()"
            items = ", ".join(self._render_expr(child) for child in node.children)
            return f"vec![{items}]"
        if node.kind == "subscript":
            index = self._render_expr(node.children[0])
            return f"{node.value}[{index} as usize]"
        if node.kind == "list_append":
            item = self._render_expr(node.children[0]) if node.children else "()"
            return f"{node.value}.push({item})"
        if node.kind == "list_extend":
            iterable = self._render_expr(node.children[0]) if node.children else "Vec::new()"
            return f"{node.value}.extend(({iterable}).into_iter())"
        if node.kind == "list_setitem":
            index = self._render_expr(node.children[0])
            value = self._render_expr(node.children[1])
            return f"{node.value}[{index} as usize] = {value}"
        if node.kind == "binop":
            left, right = node.children
            return f"({self._render_expr(left)} {node.value} {self._render_expr(right)})"
        if node.kind == "unaryop":
            return f"({node.value}{self._render_expr(node.children[0])})"
        if node.kind == "boolop":
            joined = f" {node.value} ".join(self._render_expr(child) for child in node.children)
            return f"({joined})"
        if node.kind == "compare":
            left, right = node.children
            return f"({self._render_expr(left)} {node.value} {self._render_expr(right)})"
        if node.kind == "chain_compare":
            ops = node.value.split(",") if node.value else []
            captures = node.children
            if not ops:
                return "true"
            rendered_terms: list[tuple[str, str]] = []
            for idx, capture in enumerate(captures):
                name = capture.value or f"__cmp_term_{idx}"
                expr = self._render_expr(capture.children[0]) if capture.children else "/* missing */"
                rendered_terms.append((name, expr))
            first_name, first_expr = rendered_terms[0]
            lines = [f"let {first_name} = {first_expr};", f"let mut __cmp_prev = {first_name};", "let mut __cmp_result = true;"]
            for op, (name, expr) in zip(ops, rendered_terms[1:]):
                lines.append("if __cmp_result {")
                lines.append(f"    let {name} = {expr};")
                lines.append(f"    __cmp_result = __cmp_result && (__cmp_prev {op} {name});")
                lines.append(f"    __cmp_prev = {name};")
                lines.append("}")
            lines.append("__cmp_result")
            joined = " ".join(lines)
            return f"({{ {joined} }})"
        if node.kind == "call":
            if node.value == "range":
                return self._render_range_call(node.children)
            if node.value == "len":
                arg = self._render_expr(node.children[0])
                return f"{arg}.len()"
            args = ", ".join(self._render_expr(child) for child in node.children)
            return f"{node.value}({args})"
        if node.kind == "sum":
            iterable = self._render_expr(node.children[0])
            iter_call = f"({iterable}).into_iter()"
            if len(node.children) > 1:
                start = self._render_expr(node.children[1])
                return f"{iter_call}.fold({start}, |acc, item| acc + item)"
            return f"{iter_call}.sum()"
        if node.kind == "map":
            func = node.children[0]
            iterables = [self._render_expr(child) for child in node.children[1:]]
            params = self._lambda_params(func) if func.kind == "lambda" else []
            if not params:
                params = [f"item{idx}" for idx in range(len(iterables))] or ["item"]
            base = f"({iterables[0]}).into_iter()"
            if len(iterables) == 1:
                if func.kind == "lambda":
                    closure = self._render_lambda(func, param_pattern=params[0])
                else:
                    rendered_func = self._render_expr(func)
                    closure = f"|{params[0]}| {rendered_func}({params[0]})"
                return f"{base}.map({closure})"
            for iterable in iterables[1:]:
                base += f".zip({iterable})"
            pattern = self._zip_pattern(params)
            if func.kind == "lambda":
                closure = self._render_lambda(func, param_pattern=pattern)
            else:
                rendered_func = self._render_expr(func)
                closure = f"|{pattern}| {rendered_func}({', '.join(params)})"
            return f"{base}.map({closure})"
        if node.kind == "filter":
            predicate = node.children[0]
            iterable = self._render_expr(node.children[1])
            iterable_call = f"({iterable}).into_iter()"
            if predicate.kind == "lambda":
                params = self._lambda_params(predicate)
                name = params[0] if params else "item"
                closure = self._render_lambda(predicate, param_pattern=name)
            else:
                name = "item"
                rendered_predicate = self._render_expr(predicate)
                closure = f"|{name}| {rendered_predicate}({name})"
            return f"{iterable_call}.filter({closure})"
        if node.kind == "zip":
            iterables = [self._render_expr(child) for child in node.children]
            if len(iterables) == 2:
                left, right = iterables
                return f"({left}).into_iter().zip({right})"
            zipped = f"({iterables[0]}).into_iter()"
            for iterable in iterables[1:]:
                zipped += f".zip({iterable})"
            return zipped
        if node.kind == "lambda":
            return self._render_lambda(node)
        return f"/* expr {node.kind} */"

    def _render_range_call(self, args: List[IRNode]) -> str:
        if len(args) == 1:
            upper = self._render_expr(args[0])
            return f"0..{upper}"
        if len(args) == 2:
            lower = self._render_expr(args[0])
            upper = self._render_expr(args[1])
            return f"{lower}..{upper}"
        rendered_args = ", ".join(self._render_expr(arg) for arg in args)
        return f"range({rendered_args})"

    def _map_type(self, type_name: str) -> str:
        return self._TYPE_MAP.get(type_name, "PyObject")


class RustPyo3Backend:
    """
    Backend de la fase 5 que genera funciones PyO3 compilables con control explícito del GIL.

    Produce una función anotada con ``#[pyfunction]``, la registra en un módulo y envuelve el
    cuerpo en ``allow_threads`` cuando ``release_gil`` es ``True`` para que el trabajo pesado
    pueda ejecutarse fuera del GIL o en ``Python::with_gil`` cuando es ``False`` para garantizar
    acceso seguro a la API de Python. También traduce bloques ``if``/``for`` que inicializan o
    mutan ``Vec<T>`` (``push``, asignaciones indexadas) a expresiones Rust válidas.
    """

    _TYPE_MAP = {
        "int": "i64",
        "float": "f64",
        "bool": "bool",
        "str": "String",
        "None": "()",
        "list[int]": "Vec<i64>",
        "list[float]": "Vec<f64>",
        "list[bool]": "Vec<bool>",
        "list[str]": "Vec<String>",
    }

    _DEFAULT_RETURN = {
        "int": "0i64",
        "float": "0.0",
        "bool": "false",
        "str": "String::new()",
        "None": "()",
        "list[int]": "Vec::<i64>::new()",
        "list[float]": "Vec::<f64>::new()",
        "list[bool]": "Vec::<bool>::new()",
        "list[str]": "Vec::<String>::new()",
    }

    def __init__(
        self,
        *,
        module_name: str = "pyrust_generated",
        indent: str = "    ",
        release_gil: bool = True,
    ):
        self.module_name = module_name
        self.indent = indent
        self.release_gil = release_gil
        self._return_label = "pyrust_return"

    def emit(self, func: IRFunction, *, release_gil: bool | None = None) -> str:
        """Renderiza la función IR como un módulo PyO3.

        Parameters
        ----------
        func:
            Función en forma de IR.
        release_gil:
            Política de GIL específica para esta función. ``True`` envuelve el
            cuerpo en ``allow_threads`` (libera el GIL durante el trabajo
            pesado); ``False`` lo ejecuta bajo ``Python::with_gil``. Si no se
            especifica, se usa ``self.release_gil``.
        """
        mutated = _collect_mutated_vars(func.body)
        gil_policy = self.release_gil if release_gil is None else release_gil
        args_sig = "".join(f", {name}: &Bound<'_, PyAny>" for name in func.args)
        ret_sig = "PyObject"
        lines = [
            "// Código generado por PyRust (fase 5)",
            "// Backend PyO3 + control del GIL",
            "use pyo3::prelude::*;",
            "use pyo3::types::PyAny;",
            "use pyo3::{IntoPy, PyObject};",
            "use pyo3::wrap_pyfunction;",
            "",
            "#[pyfunction]",
            f"pub fn {func.name}(py: Python<'_>{args_sig}) -> PyResult<{ret_sig}> {{",
        ]

        lines.extend(self._render_arg_conversions(func, mutated))

        bindings = {name: name in mutated for name in func.args}

        if gil_policy:
            lines.extend(self._render_allow_threads_block(func, bindings, mutated))
        else:
            lines.extend(self._render_with_gil_block(func, bindings, mutated))

        lines.append("}")
        lines.append("")
        lines.append("#[pymodule]")
        lines.append(f"pub fn {self.module_name}(_py: Python<'_>, m: &PyModule) -> PyResult<()> {{")
        lines.append(f"{self.indent}m.add_function(wrap_pyfunction!({func.name}, m)?)?;")
        lines.append(f"{self.indent}Ok(())")
        lines.append("}")
        return "\n".join(lines)

    def _render_with_gil_block(
        self, func: IRFunction, bindings: dict[str, bool], mutated: set[str]
    ) -> List[str]:
        lines = [f"{self.indent}let result = Python::with_gil(|_py| {{"]
        lines.extend(self._render_return_block(func, bindings, mutated, level=2))
        lines.append(f"{self.indent}}});")
        lines.append(f"{self.indent}Ok(result.into_py(py))")
        return lines

    def _render_allow_threads_block(
        self, func: IRFunction, bindings: dict[str, bool], mutated: set[str]
    ) -> List[str]:
        lines = [f"{self.indent}let result = py.allow_threads(|| {{"]
        lines.extend(self._render_return_block(func, bindings, mutated, level=2))
        lines.append(f"{self.indent}}});")
        lines.append(f"{self.indent}Ok(result.into_py(py))")
        return lines

    def _render_return_block(
        self,
        func: IRFunction,
        bindings: dict[str, bool],
        mutated: set[str],
        *,
        level: int,
    ) -> List[str]:
        ret_value = self._default_return_value(func.return_type or "None")
        prefix = self.indent * level
        lines = [f"{prefix}let result = '{self._return_label}: {{"]
        body = self._render_body(
            func.body,
            bindings,
            mutated,
            level=level + 1,
            return_label=self._return_label,
            return_type=func.return_type or "None",
        )
        lines.extend(body)
        lines.append(f"{prefix}{self.indent}break '{self._return_label} {ret_value};")
        lines.append(f"{prefix}}};")
        lines.append(f"{prefix}result")
        return lines

    def _render_arg_conversions(self, func: IRFunction, mutated: set[str]) -> List[str]:
        lines: List[str] = []
        for name in func.args:
            rust_type = self._map_type(func.arg_types.get(name, "int"))
            decl = "mut " if name in mutated else ""
            lines.append(f"{self.indent}let {decl}{name}: {rust_type} = {name}.extract()?;")
        return lines

    def _render_body(
        self,
        nodes: List[IRNode],
        bindings: dict[str, bool],
        mutated: set[str],
        *,
        level: int,
        return_label: str,
        return_type: str,
    ) -> List[str]:
        lines: List[str] = []
        for node in nodes:
            prefix = self.indent * level
            if node.kind == "assign":
                target = node.value or "_tmp"
                expr = self._render_expr(node.children[0])
                if target not in bindings:
                    is_mut = target in mutated
                    bindings[target] = is_mut
                    decl = "let mut " if is_mut else "let "
                    lines.append(f"{prefix}{decl}{target} = {expr};")
                else:
                    lines.append(f"{prefix}{target} = {expr};")
            elif node.kind == "list_setitem":
                target = node.value or "_vec"
                index = self._render_expr(node.children[0])
                value = self._render_expr(node.children[1])
                if target not in bindings:
                    bindings[target] = True
                    lines.append(f"{prefix}let mut {target}: Vec<_> = Vec::new();")
                elif not bindings[target] and target in mutated:
                    lines.append(f"{prefix}let mut {target} = {target};")
                    bindings[target] = True
                lines.append(f"{prefix}{target}[{index} as usize] = {value};")
            elif node.kind == "return":
                expr = self._render_expr(node.children[0]) if node.children else self._default_return_value(return_type)
                lines.append(f"{prefix}break '{return_label} {expr};")
            elif node.kind == "for":
                target = node.value or "_item"
                iter_expr = self._render_expr(node.children[0])
                lines.append(f"{prefix}for {target} in {iter_expr} {{")
                lines.extend(
                    self._render_body(
                        node.children[1:],
                        bindings,
                        mutated,
                        level=level + 1,
                        return_label=return_label,
                        return_type=return_type,
                    )
                )
                lines.append(f"{prefix}}}")
            elif node.kind == "if":
                condition = self._render_expr(node.children[0])
                lines.append(f"{prefix}if {condition} {{")
                lines.extend(
                    self._render_body(
                        node.children[1].children,
                        bindings,
                        mutated,
                        level=level + 1,
                        return_label=return_label,
                        return_type=return_type,
                    )
                )
                lines.append(f"{prefix}}}")
                else_block = node.children[2]
                if else_block.children:
                    lines.append(f"{prefix}else {{")
                    lines.extend(
                        self._render_body(
                            else_block.children,
                            bindings,
                            mutated,
                            level=level + 1,
                            return_label=return_label,
                            return_type=return_type,
                        )
                    )
                    lines.append(f"{prefix}}}")
            elif node.kind == "expr":
                expr = self._render_expr(node.children[0])
                lines.append(f"{prefix}{expr};")
            else:  # pragma: no cover - guardia futura
                lines.append(f"{prefix}// nodo IR no renderizado: {node.kind}")
        return lines

    def _render_expr(self, node: IRNode) -> str:
        if node.kind == "const":
            return self._render_const(node.value)
        if node.kind == "var":
            return str(node.value)
        if node.kind == "list_literal":
            if not node.children:
                return "Vec::new()"
            items = ", ".join(self._render_expr(child) for child in node.children)
            return f"vec![{items}]"
        if node.kind == "subscript":
            index = self._render_expr(node.children[0])
            return f"{node.value}[{index} as usize]"
        if node.kind == "list_append":
            item = self._render_expr(node.children[0]) if node.children else "()"
            return f"{node.value}.push({item})"
        if node.kind == "list_extend":
            iterable = self._render_expr(node.children[0]) if node.children else "Vec::new()"
            return f"{node.value}.extend(({iterable}).into_iter())"
        if node.kind == "list_setitem":
            index = self._render_expr(node.children[0])
            value = self._render_expr(node.children[1])
            return f"{node.value}[{index} as usize] = {value}"
        if node.kind == "binop":
            left, right = node.children
            return f"({self._render_expr(left)} {node.value} {self._render_expr(right)})"
        if node.kind == "unaryop":
            op = "!" if node.value == "not" else node.value
            return f"({op}{self._render_expr(node.children[0])})"
        if node.kind == "boolop":
            op = "&&" if node.value == "and" else "||"
            joined = f" {op} ".join(self._render_expr(child) for child in node.children)
            return f"({joined})"
        if node.kind == "compare":
            left, right = node.children
            return f"({self._render_expr(left)} {node.value} {self._render_expr(right)})"
        if node.kind == "chain_compare":
            ops = node.value.split(",") if node.value else []
            captures = node.children
            if not ops:
                return "true"
            rendered_terms: list[tuple[str, str]] = []
            for idx, capture in enumerate(captures):
                name = capture.value or f"__cmp_term_{idx}"
                expr = self._render_expr(capture.children[0]) if capture.children else "/* missing */"
                rendered_terms.append((name, expr))
            first_name, first_expr = rendered_terms[0]
            lines = [f"let {first_name} = {first_expr};", f"let mut __cmp_prev = {first_name};", "let mut __cmp_result = true;"]
            for op, (name, expr) in zip(ops, rendered_terms[1:]):
                lines.append("if __cmp_result {")
                lines.append(f"    let {name} = {expr};")
                lines.append(f"    __cmp_result = __cmp_result && (__cmp_prev {op} {name});")
                lines.append(f"    __cmp_prev = {name};")
                lines.append("}")
            lines.append("__cmp_result")
            joined = " ".join(lines)
            return f"({{ {joined} }})"
        if node.kind == "call":
            if node.value == "range":
                return self._render_range_call(node.children)
            if node.value == "len":
                arg = self._render_expr(node.children[0])
                return f"({arg}.len() as i64)"
            args = ", ".join(self._render_expr(child) for child in node.children)
            return f"{node.value}({args})"
        if node.kind == "sum":
            iterable = self._render_expr(node.children[0])
            iter_call = f"({iterable}).into_iter()"
            if len(node.children) > 1:
                start = self._render_expr(node.children[1])
                return f"{iter_call}.fold({start}, |acc, item| acc + item)"
            return f"{iter_call}.sum()"
        if node.kind == "map":
            func = node.children[0]
            iterables = [self._render_expr(child) for child in node.children[1:]]
            params = self._lambda_params(func) if func.kind == "lambda" else []
            if not params:
                params = [f"item{idx}" for idx in range(len(iterables))] or ["item"]
            base = f"({iterables[0]}).into_iter()"
            if len(iterables) == 1:
                if func.kind == "lambda":
                    closure = self._render_lambda(func, param_pattern=params[0])
                else:
                    rendered_func = self._render_expr(func)
                    closure = f"|{params[0]}| {rendered_func}({params[0]})"
                return f"{base}.map({closure})"
            for iterable in iterables[1:]:
                base += f".zip({iterable})"
            pattern = self._zip_pattern(params)
            if func.kind == "lambda":
                closure = self._render_lambda(func, param_pattern=pattern)
            else:
                rendered_func = self._render_expr(func)
                closure = f"|{pattern}| {rendered_func}({', '.join(params)})"
            return f"{base}.map({closure})"
        if node.kind == "filter":
            predicate = node.children[0]
            iterable = self._render_expr(node.children[1])
            iterable_call = f"({iterable}).into_iter()"
            if predicate.kind == "lambda":
                params = self._lambda_params(predicate)
                name = params[0] if params else "item"
                closure = self._render_lambda(predicate, param_pattern=name)
            else:
                name = "item"
                rendered_predicate = self._render_expr(predicate)
                closure = f"|{name}| {rendered_predicate}({name})"
            return f"{iterable_call}.filter({closure})"
        if node.kind == "zip":
            iterables = [self._render_expr(child) for child in node.children]
            if len(iterables) == 2:
                left, right = iterables
                return f"({left}).into_iter().zip({right})"
            zipped = f"({iterables[0]}).into_iter()"
            for iterable in iterables[1:]:
                zipped += f".zip({iterable})"
            return zipped
        if node.kind == "lambda":
            return self._render_lambda(node)
        return f"/* expr {node.kind} */"

    def _render_const(self, value: str | None) -> str:
        if value is None:
            return "()"
        if value == "None":
            return "()"
        if value in {"True", "False"}:
            return value.lower()
        try:
            literal = ast.literal_eval(value)
        except Exception:
            literal = value
        if isinstance(literal, str):
            escaped = literal.replace('"', '\\"')
            return f"String::from(\"{escaped}\")"
        if isinstance(literal, bool):
            return str(literal).lower()
        if literal is None:
            return "()"
        return str(literal)

    def _render_range_call(self, args: List[IRNode]) -> str:
        if len(args) == 1:
            upper = self._render_expr(args[0])
            return f"0..{upper}"
        if len(args) == 2:
            lower = self._render_expr(args[0])
            upper = self._render_expr(args[1])
            return f"{lower}..{upper}"
        rendered_args = ", ".join(self._render_expr(arg) for arg in args)
        return f"range({rendered_args})"

    def _render_lambda(self, node: IRNode, *, param_pattern: str | None = None) -> str:
        params = param_pattern if param_pattern is not None else ", ".join(self._lambda_params(node))
        body = self._render_expr(node.children[0]) if node.children else "()"
        return f"|{params}| {body}"

    @staticmethod
    def _lambda_params(node: IRNode) -> List[str]:
        return node.value.split(",") if node.value else []

    @staticmethod
    def _zip_pattern(names: List[str]) -> str:
        if not names:
            return "()"
        pattern = names[0]
        for name in names[1:]:
            pattern = f"({pattern}, {name})"
        return pattern

    def _default_return_value(self, type_name: str) -> str:
        return self._DEFAULT_RETURN.get(type_name, "()")

    def _map_type(self, type_name: str) -> str:
        return self._TYPE_MAP.get(type_name, "PyObject")


__all__ = [
    "IRFunction",
    "IRNode",
    "IRValidationError",
    "RustPyo3Backend",
    "RustTemplateBackend",
    "Transpiler",
    "TranspilerBackend",
]
