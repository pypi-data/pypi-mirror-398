from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml
from openapi_schema_validator import OAS30Validator
from openapi_spec_validator import validate as validate_openapi_spec

from simple_automated_testing.contracts.models import Diff


class OpenApiError(RuntimeError):
    pass


_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def load_openapi_spec(path: str) -> Dict[str, Any]:
    spec_path = Path(path)
    if not spec_path.exists():
        raise OpenApiError(f"找不到 OpenAPI 規格檔案：{path}")

    raw = spec_path.read_text(encoding="utf-8")
    spec = _parse_content(raw)
    _ensure_openapi_3(spec)
    _ensure_internal_refs(spec)
    _validate_spec(spec)
    return spec


def summarize_endpoints(spec: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    paths = spec.get("paths") or {}
    if not isinstance(paths, dict):
        return lines

    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, definition in methods.items():
            if method.lower() not in _HTTP_METHODS or not isinstance(definition, dict):
                continue
            responses = _summarize_responses(definition.get("responses") or {})
            summary = ", ".join(responses) if responses else "無回應定義"
            lines.append(f"{method.upper()} {path} -> {summary}")
    return lines


def select_response_schema(spec: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
    path = target.get("path")
    method = str(target.get("method", "")).lower()
    status_code = str(target.get("statusCode"))
    content_type = target.get("contentType")

    paths = spec.get("paths") or {}
    if path not in paths:
        raise OpenApiError("規格中缺少指定端點")
    operation = (paths.get(path) or {}).get(method)
    if not isinstance(operation, dict):
        raise OpenApiError("規格中缺少指定方法")
    responses = operation.get("responses") or {}
    response = responses.get(status_code) or responses.get(str(status_code))
    if not isinstance(response, dict):
        raise OpenApiError("規格中缺少指定狀態碼的回應定義")
    content = response.get("content") or {}
    if content_type not in content:
        raise OpenApiError("規格中缺少指定 content-type 的回應定義")
    content_def = content.get(content_type) or {}
    schema = content_def.get("schema")
    if not isinstance(schema, dict):
        raise OpenApiError("規格中缺少回應 schema")
    return schema


def validate_response_body(spec: Dict[str, Any], target: Dict[str, Any], body: Any) -> List[Diff]:
    schema = select_response_schema(spec, target)
    resolved_schema = _resolve_schema_refs(schema, spec)
    validator = OAS30Validator(resolved_schema)

    diffs: List[Diff] = []
    for error in validator.iter_errors(body):
        path = _format_json_path(error.path)
        diffs.append(
            Diff(
                rule="openapi.schema",
                message=error.message,
                expected=_summarize_expected(error.schema),
                actual=path,
            )
        )

    diffs.extend(_collect_extra_fields(resolved_schema, body, "$"))
    return diffs


def _parse_content(raw: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = yaml.safe_load(raw)

    if not isinstance(parsed, dict):
        raise OpenApiError("OpenAPI 規格內容必須為物件")
    return parsed


def _ensure_openapi_3(spec: Dict[str, Any]) -> None:
    version = str(spec.get("openapi", "")).strip()
    if not version.startswith("3."):
        raise OpenApiError("僅支援 OpenAPI 3.x 規格")


def _ensure_internal_refs(node: Any) -> None:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if ref is not None:
            if not isinstance(ref, str):
                raise OpenApiError("規格中的 $ref 必須為字串")
            if not ref.startswith("#/"):
                raise OpenApiError(f"不支援外部 $ref：{ref}")
        for value in node.values():
            _ensure_internal_refs(value)
    elif isinstance(node, list):
        for item in node:
            _ensure_internal_refs(item)


def _validate_spec(spec: Dict[str, Any]) -> None:
    try:
        validate_openapi_spec(spec)
    except Exception as exc:  # pragma: no cover - depends on validator error type
        raise OpenApiError(f"OpenAPI 規格驗證失敗：{exc}") from exc


def _summarize_responses(responses: Dict[str, Any]) -> List[str]:
    items: List[str] = []
    if not isinstance(responses, dict):
        return items
    for status_code, response in responses.items():
        content = (response or {}).get("content") or {}
        if not content:
            items.append(str(status_code))
            continue
        for content_type in content.keys():
            items.append(f"{status_code} {content_type}")
    return items


def _format_json_path(parts: Iterable[Any]) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def _summarize_expected(schema: Any) -> str | None:
    if isinstance(schema, dict):
        schema_type = schema.get("type")
        if schema_type:
            return str(schema_type)
    return None


def _collect_extra_fields(schema: Dict[str, Any], data: Any, path: str) -> List[Diff]:
    resolved = schema
    diffs: List[Diff] = []

    if isinstance(data, dict) and _looks_like_object_schema(resolved):
        allowed = _collect_allowed_properties(resolved)
        for key, value in data.items():
            if key not in allowed:
                diffs.append(
                    Diff(
                        rule="openapi.extra",
                        message="回應包含規格未定義欄位",
                        expected="not allowed",
                        actual=f"{path}.{key}",
                    )
                )
            else:
                next_schema = _resolve_property_schema(resolved, key)
                if next_schema is not None:
                    diffs.extend(_collect_extra_fields(next_schema, value, f"{path}.{key}"))
        return diffs

    if isinstance(data, list) and _looks_like_array_schema(resolved):
        item_schema = resolved.get("items")
        if isinstance(item_schema, dict):
            for idx, item in enumerate(data):
                diffs.extend(_collect_extra_fields(item_schema, item, f"{path}[{idx}]"))

    return diffs


def _looks_like_object_schema(schema: Dict[str, Any]) -> bool:
    return schema.get("type") == "object" or "properties" in schema or "allOf" in schema or "oneOf" in schema or "anyOf" in schema


def _looks_like_array_schema(schema: Dict[str, Any]) -> bool:
    return schema.get("type") == "array" or "items" in schema


def _collect_allowed_properties(schema: Dict[str, Any]) -> set[str]:
    resolved = schema
    allowed = set(resolved.get("properties", {}).keys())

    for keyword in ("allOf", "oneOf", "anyOf"):
        for subschema in resolved.get(keyword, []) or []:
            if isinstance(subschema, dict):
                allowed.update(_collect_allowed_properties(subschema))

    return allowed


def _resolve_property_schema(schema: Dict[str, Any], key: str) -> Dict[str, Any] | None:
    props = schema.get("properties")
    if isinstance(props, dict) and key in props and isinstance(props.get(key), dict):
        return props.get(key)
    return None


def _resolve_schema_refs(schema: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    return _resolve_schema_node(schema, spec, [])


def _resolve_schema_node(node: Any, spec: Dict[str, Any], ref_stack: List[str]) -> Any:
    if isinstance(node, dict):
        if "$ref" in node:
            ref = node.get("$ref")
            if not isinstance(ref, str):
                raise OpenApiError("規格中的 $ref 必須為字串")
            if ref in ref_stack:
                raise OpenApiError(f"偵測到循環 $ref：{ref}")
            resolved = _resolve_ref(ref, spec)
            return _resolve_schema_node(resolved, spec, ref_stack + [ref])
        return {key: _resolve_schema_node(value, spec, ref_stack) for key, value in node.items()}
    if isinstance(node, list):
        return [_resolve_schema_node(item, spec, ref_stack) for item in node]
    return node


def _resolve_ref(ref: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    if not ref.startswith("#/"):
        raise OpenApiError(f"不支援外部 $ref：{ref}")
    node: Any = spec
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise OpenApiError(f"$ref 無法解析：{ref}")
        node = node[part]
    if not isinstance(node, dict):
        raise OpenApiError(f"$ref 無法解析：{ref}")
    return node
