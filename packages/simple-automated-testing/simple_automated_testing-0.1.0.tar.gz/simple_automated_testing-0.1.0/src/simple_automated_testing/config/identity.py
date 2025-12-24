from __future__ import annotations

from typing import Any, Dict, List, Tuple


class IdentityResolutionError(ValueError):
    pass


def get_identities(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    identities = config.get("identities") or []
    if not isinstance(identities, list):
        return []
    return identities


def build_identity_index(identities: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], str | None]:
    identity_map: Dict[str, Dict[str, Any]] = {}
    default_name: str | None = None
    for identity in identities:
        if not isinstance(identity, dict):
            continue
        name = identity.get("name")
        if isinstance(name, str) and name.strip():
            identity_map[name] = identity
            if identity.get("isDefault") is True:
                default_name = name
    return identity_map, default_name


def resolve_identity_name(test_def: Dict[str, Any], default_name: str | None) -> str | None:
    identity_name = test_def.get("identity")
    if isinstance(identity_name, str) and identity_name.strip():
        return identity_name
    return default_name


def resolve_identity(
    test_def: Dict[str, Any],
    identity_map: Dict[str, Dict[str, Any]],
    default_name: str | None,
) -> Dict[str, Any] | None:
    identity_name = resolve_identity_name(test_def, default_name)
    if identity_name is None:
        return None
    return identity_map.get(identity_name)


def resolve_identity_or_error(
    test_def: Dict[str, Any],
    identity_map: Dict[str, Dict[str, Any]],
    default_name: str | None,
) -> Tuple[str, Dict[str, Any]]:
    identity_name = resolve_identity_name(test_def, default_name)
    if identity_name is None:
        raise IdentityResolutionError("未指定 Identity 且沒有預設 Identity")
    identity = identity_map.get(identity_name)
    if identity is None:
        raise IdentityResolutionError(f"Identity 不存在：{identity_name}")
    return identity_name, identity
