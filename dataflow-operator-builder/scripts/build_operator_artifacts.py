#!/usr/bin/env python3
"""Build DataFlow-KG operator artifacts from a JSON spec."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

VALID_MODULES = {
    "general_kg",
    "commonsense_kg",
    "temporal_kg",
    "hyper_relation_kg",
    "multi_model_kg",
    "graph_rag",
    "graph_reasoning",
    "domain_kg",
}
VALID_DOMAIN_SUBMODULES = {
    "financial_kg",
    "legal_kg",
    "medical_kg",
    "geospatial_kg",
    "scholar_kg",
}
VALID_OPERATOR_TYPES = {"generate", "filter", "eval", "refine", "refinement"}
VALID_OVERWRITE = {"ask-each", "overwrite-all", "skip-existing"}
VALID_VALIDATION = {"none", "basic", "full"}
IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build DataFlow-KG operator artifacts from skill templates")
    parser.add_argument("--spec", required=True, help="Path to JSON spec")
    parser.add_argument("--output-root", required=True, help="DataFlow-KG repository root")
    parser.add_argument("--skill-dir", default=None, help="Skill directory; default is script parent")
    parser.add_argument(
        "--overwrite",
        choices=sorted(VALID_OVERWRITE),
        default=None,
        help="Override overwrite strategy from spec",
    )
    parser.add_argument(
        "--validation-level",
        choices=sorted(VALID_VALIDATION),
        default=None,
        help="Override validation level from spec",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print file plan without writing")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y"}:
            return True
        if normalized in {"0", "false", "no", "n"}:
            return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def normalize_identifier(raw: Any, field_name: str) -> str:
    value = str(raw).strip().replace(".py", "")
    if not value:
        raise ValueError(f"{field_name} cannot be empty")
    if not IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"Invalid {field_name}: {value}")
    return value


def infer_operator_dir(operator_type: str, kg_module: str) -> str:
    if operator_type in {"generate", "filter", "eval"}:
        return operator_type
    if kg_module in {"general_kg", "temporal_kg"}:
        return "refinement"
    return "refine"


def kg_path_parts(spec: dict[str, Any]) -> list[str]:
    if spec["kg_module"] == "domain_kg":
        return ["domain_kg", spec["domain_submodule"]]
    return [spec["kg_module"]]


def validate_spec(raw_spec: dict[str, Any]) -> dict[str, Any]:
    required = [
        "kg_module",
        "operator_type",
        "operator_class_name",
        "operator_module_name",
        "input_key",
        "output_key",
        "uses_llm",
    ]
    missing = [field for field in required if field not in raw_spec or str(raw_spec[field]).strip() == ""]
    if missing:
        raise ValueError(f"Missing required spec fields: {missing}")

    kg_module = str(raw_spec["kg_module"]).strip()
    if kg_module not in VALID_MODULES:
        raise ValueError(f"kg_module must be one of {sorted(VALID_MODULES)}, got: {kg_module}")

    domain_submodule = raw_spec.get("domain_submodule")
    if kg_module == "domain_kg":
        if not domain_submodule:
            raise ValueError("domain_submodule is required when kg_module is 'domain_kg'")
        domain_submodule = str(domain_submodule).strip()
        if domain_submodule not in VALID_DOMAIN_SUBMODULES:
            raise ValueError(
                f"domain_submodule must be one of {sorted(VALID_DOMAIN_SUBMODULES)}, got: {domain_submodule}"
            )
    else:
        domain_submodule = None

    operator_type = str(raw_spec["operator_type"]).strip().lower()
    if operator_type not in VALID_OPERATOR_TYPES:
        raise ValueError(
            f"operator_type must be one of {sorted(VALID_OPERATOR_TYPES)}, got: {operator_type}"
        )

    operator_dir = str(raw_spec.get("operator_dir") or infer_operator_dir(operator_type, kg_module)).strip()
    if operator_dir not in {"generate", "filter", "eval", "refine", "refinement"}:
        raise ValueError(f"operator_dir must be one of generate/filter/eval/refine/refinement, got: {operator_dir}")

    operator_class_name = normalize_identifier(raw_spec["operator_class_name"], "operator_class_name")
    operator_module_name = normalize_identifier(raw_spec["operator_module_name"], "operator_module_name")
    test_file_prefix = normalize_identifier(raw_spec.get("test_file_prefix") or operator_module_name, "test_file_prefix")

    input_key = str(raw_spec["input_key"]).strip()
    output_key = str(raw_spec["output_key"]).strip()
    input_key_meta = raw_spec.get("input_key_meta")
    if input_key_meta is not None:
        input_key_meta = str(input_key_meta).strip()
        if not input_key_meta:
            input_key_meta = None

    overwrite_strategy = str(raw_spec.get("overwrite_strategy") or "ask-each").strip().lower()
    if overwrite_strategy not in VALID_OVERWRITE:
        raise ValueError(
            f"overwrite_strategy must be one of {sorted(VALID_OVERWRITE)}, got: {overwrite_strategy}"
        )

    validation_level = str(raw_spec.get("validation_level") or "basic").strip().lower()
    if validation_level not in VALID_VALIDATION:
        raise ValueError(
            f"validation_level must be one of {sorted(VALID_VALIDATION)}, got: {validation_level}"
        )

    prompt_class_name = raw_spec.get("prompt_class_name")
    if prompt_class_name is not None:
        prompt_class_name = normalize_identifier(prompt_class_name, "prompt_class_name")
    prompt_import_statement = raw_spec.get("prompt_import_statement")
    if prompt_class_name and not prompt_import_statement:
        raise ValueError("prompt_import_statement is required when prompt_class_name is provided")

    function_description = str(raw_spec.get("function_description") or "Generated DataFlow-KG operator scaffold.").strip()
    lang = str(raw_spec.get("lang") or "en").strip() or "en"

    normalized = {
        "kg_module": kg_module,
        "domain_submodule": domain_submodule,
        "operator_type": operator_type,
        "operator_dir": operator_dir,
        "operator_class_name": operator_class_name,
        "operator_module_name": operator_module_name,
        "input_key": input_key,
        "input_key_meta": input_key_meta,
        "output_key": output_key,
        "uses_llm": parse_bool(raw_spec["uses_llm"]),
        "prompt_class_name": prompt_class_name,
        "prompt_import_statement": str(prompt_import_statement).strip() if prompt_import_statement else "",
        "function_description_en": function_description,
        "function_description_zh": function_description,
        "lang": lang,
        "test_file_prefix": test_file_prefix,
        "overwrite_strategy": overwrite_strategy,
        "validation_level": validation_level,
    }
    normalized["public_import_path"] = ".".join(["dataflow", "operators", *kg_path_parts(normalized)])
    normalized["kg_public_relative_path"] = "/".join(kg_path_parts(normalized))
    return normalized


def template_flags(spec: dict[str, Any]) -> dict[str, bool]:
    return {
        "USES_LLM": bool(spec["uses_llm"]),
        "NOT_USES_LLM": not bool(spec["uses_llm"]),
        "HAS_META_INPUT": bool(spec["input_key_meta"]),
        "NOT_HAS_META_INPUT": not bool(spec["input_key_meta"]),
        "HAS_PROMPT_IMPORT": bool(spec["prompt_import_statement"]),
        "NOT_HAS_PROMPT_IMPORT": not bool(spec["prompt_import_statement"]),
        "HAS_PROMPT_RESTRICT": bool(spec["prompt_class_name"]),
    }


def render_conditionals(text: str, flags: dict[str, bool]) -> str:
    for name, enabled in flags.items():
        pattern = re.compile(rf"\[\[IF_{name}\]\](.*?)\[\[END_IF_{name}\]\]", re.DOTALL)
        text = pattern.sub(lambda match: match.group(1) if enabled else "", text)
    return text


def render_placeholders(text: str, mapping: dict[str, Any]) -> str:
    for key, value in mapping.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))
    return text


def read_template(path: Path, spec: dict[str, Any]) -> str:
    mapping = {
        "OPERATOR_CLASS_NAME": spec["operator_class_name"],
        "OPERATOR_MODULE_NAME": spec["operator_module_name"],
        "OPERATOR_DIR": spec["operator_dir"],
        "INPUT_KEY": spec["input_key"],
        "INPUT_KEY_META": spec["input_key_meta"] or "",
        "OUTPUT_KEY": spec["output_key"],
        "FUNCTION_DESCRIPTION_EN": spec["function_description_en"],
        "FUNCTION_DESCRIPTION_ZH": spec["function_description_zh"],
        "LANG": spec["lang"],
        "PROMPT_IMPORT_STATEMENT": spec["prompt_import_statement"],
        "PROMPT_CLASS_NAME": spec["prompt_class_name"] or "",
        "PUBLIC_IMPORT_PATH": spec["public_import_path"],
        "KG_PUBLIC_RELATIVE_PATH": spec["kg_public_relative_path"],
    }
    rendered = path.read_text(encoding="utf-8")
    rendered = render_conditionals(rendered, template_flags(spec))
    rendered = render_placeholders(rendered, mapping)
    lines = [line.rstrip() for line in rendered.splitlines()]
    normalized: list[str] = []
    blank_run = 0
    for line in lines:
        if not line.strip():
            blank_run += 1
            if blank_run <= 1:
                normalized.append("")
            continue
        blank_run = 0
        normalized.append(line)
    return "\n".join(normalized).strip() + "\n"


def operator_template_name(spec: dict[str, Any]) -> str:
    if spec["operator_type"] in {"refine", "refinement"}:
        return "refine_operator.py.tmpl"
    return f"{spec['operator_type']}_operator.py.tmpl"


def build_paths(output_root: Path, spec: dict[str, Any]) -> dict[str, Path]:
    kg_parts = kg_path_parts(spec)
    operators_root = output_root / "dataflow" / "operators" / Path(*kg_parts)
    tests_root = output_root / "test" / "cpu_only"
    return {
        "operator_file": operators_root / spec["operator_dir"] / f"{spec['operator_module_name']}.py",
        "module_init": operators_root / "__init__.py",
        "unit_test": tests_root / f"test_{spec['test_file_prefix']}_unit.py",
        "registry_test": tests_root / f"test_{spec['test_file_prefix']}_registry.py",
        "smoke_test": tests_root / f"test_{spec['test_file_prefix']}_smoke.py",
    }


def existing_or_new_init_content(skill_dir: Path, module_init_path: Path, spec: dict[str, Any]) -> str:
    import_line = f"    from .{spec['operator_dir']}.{spec['operator_module_name']} import {spec['operator_class_name']}"
    if module_init_path.exists():
        original = module_init_path.read_text(encoding="utf-8")
        if import_line in original:
            return original if original.endswith("\n") else original + "\n"

        lines = original.splitlines()
        if_index = next((index for index, line in enumerate(lines) if line.strip().startswith("if TYPE_CHECKING")), None)
        else_index = next(
            (index for index, line in enumerate(lines) if if_index is not None and index > if_index and line.strip() == "else:"),
            None,
        )
        if if_index is not None and else_index is not None:
            insertion_index = else_index
            while insertion_index > if_index and lines[insertion_index - 1].strip() == "":
                insertion_index -= 1
            lines.insert(insertion_index, import_line)
            return "\n".join(lines) + "\n"

    template_path = skill_dir / "assets" / "templates" / "package" / "module_init.py.tmpl"
    return read_template(template_path, spec)


def render_outputs(skill_dir: Path, output_root: Path, spec: dict[str, Any]) -> dict[Path, str]:
    paths = build_paths(output_root, spec)
    outputs = {
        paths["operator_file"]: read_template(
            skill_dir / "assets" / "templates" / "operators" / operator_template_name(spec),
            spec,
        ),
        paths["module_init"]: existing_or_new_init_content(skill_dir, paths["module_init"], spec),
        paths["unit_test"]: read_template(
            skill_dir / "assets" / "templates" / "tests" / "test_operator_unit.py.tmpl",
            spec,
        ),
        paths["registry_test"]: read_template(
            skill_dir / "assets" / "templates" / "tests" / "test_operator_registry.py.tmpl",
            spec,
        ),
        paths["smoke_test"]: read_template(
            skill_dir / "assets" / "templates" / "tests" / "test_operator_smoke.py.tmpl",
            spec,
        ),
    }
    return outputs


def print_plan(rendered_outputs: dict[Path, str], overwrite_mode: str) -> None:
    print("Planned outputs:")
    for path in rendered_outputs:
        tag = "UPDATE" if path.exists() else "CREATE"
        print(f"  - [{tag}] {path}")
    print(f"Effective overwrite strategy: {overwrite_mode}")


def choose_action(dest: Path, overwrite_mode: str) -> str:
    if not dest.exists():
        return "write"
    if overwrite_mode == "overwrite-all":
        return "write"
    if overwrite_mode == "skip-existing":
        return "skip"

    while True:
        answer = input(f"File exists: {dest}\nChoose [o]verwrite / [s]kip / [q]uit: ").strip().lower()
        if answer in {"o", "overwrite"}:
            return "write"
        if answer in {"s", "skip"}:
            return "skip"
        if answer in {"q", "quit"}:
            return "quit"


def write_outputs(rendered_outputs: dict[Path, str], overwrite_mode: str) -> dict[str, list[Path]]:
    summary: dict[str, list[Path]] = {"written": [], "skipped": []}
    for dest, content in rendered_outputs.items():
        action = choose_action(dest, overwrite_mode)
        if action == "quit":
            raise KeyboardInterrupt("User cancelled during overwrite selection")
        if action == "skip":
            summary["skipped"].append(dest)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        summary["written"].append(dest)
    return summary


def validate_python_syntax(paths: list[Path]) -> list[str]:
    checks: list[str] = []
    for path in paths:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))
        checks.append(f"Syntax OK: {path}")
    return checks


def validate_outputs(level: str, rendered_outputs: dict[Path, str], spec: dict[str, Any]) -> list[str]:
    if level == "none":
        return ["Validation skipped (none)."]

    checks = validate_python_syntax(list(rendered_outputs.keys()))
    if level == "full":
        module_init = next(path for path in rendered_outputs if path.name == "__init__.py")
        expected_line = f"from .{spec['operator_dir']}.{spec['operator_module_name']} import {spec['operator_class_name']}"
        content = module_init.read_text(encoding="utf-8")
        if expected_line not in content:
            raise RuntimeError(f"Missing TYPE_CHECKING registration line in {module_init}")
        checks.append("TYPE_CHECKING registration line found.")
    return checks


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    skill_dir = Path(args.skill_dir).resolve() if args.skill_dir else script_dir.parent
    output_root = Path(args.output_root).resolve()

    try:
        spec = validate_spec(load_json(Path(args.spec).resolve()))
        overwrite_mode = args.overwrite or spec["overwrite_strategy"]
        validation_level = args.validation_level or spec["validation_level"]
        rendered_outputs = render_outputs(skill_dir, output_root, spec)

        print("DataFlow-KG Operator Builder")
        print(f"Skill dir          : {skill_dir}")
        print(f"Output root        : {output_root}")
        print(f"KG module          : {spec['kg_module']}")
        print(f"Operator type      : {spec['operator_type']}")
        print(f"Operator directory : {spec['operator_dir']}")
        print(f"Validation level   : {validation_level}")
        print_plan(rendered_outputs, overwrite_mode)

        if args.dry_run:
            print("\nDry-run complete. No files were written.")
            return 0

        summary = write_outputs(rendered_outputs, overwrite_mode)
        print(f"\nWritten files ({len(summary['written'])}):")
        for path in summary["written"]:
            print(f"  - {path}")
        print(f"Skipped files ({len(summary['skipped'])}):")
        for path in summary["skipped"]:
            print(f"  - {path}")

        checks = validate_outputs(validation_level, rendered_outputs, spec)
        print("\nValidation results:")
        for check in checks:
            print(f"  - {check}")

        return 0
    except KeyboardInterrupt as exc:
        print(f"\nCancelled: {exc}")
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
