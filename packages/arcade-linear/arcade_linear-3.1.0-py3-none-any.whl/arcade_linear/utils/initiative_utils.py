"""Utilities for initiative tools."""

from collections.abc import Mapping, Sequence
from typing import Any, cast

from arcade_linear.models.mappers import map_initiative
from arcade_linear.models.tool_outputs.initiatives import (
    CreatedInitiativeOutput,
    CreateInitiativeOutput,
    InitiativeDetailsOutput,
    UpdateInitiativeOutput,
)
from arcade_linear.utils.fuzzy_utils import try_fuzzy_match_by_name
from arcade_linear.utils.response_utils import remove_none_values_recursive


def build_initiative_response(
    initiative_data: Mapping[str, Any],
    include_projects: bool,
) -> dict[str, Any]:
    """Build the initiative response with optional fields."""
    cleaned_initiative = map_initiative(initiative_data)

    if not include_projects:
        cleaned_initiative.pop("projects", None)

    result: InitiativeDetailsOutput = {
        "initiative": cleaned_initiative,
    }

    return cast(dict[str, Any], remove_none_values_recursive(result))


def filter_initiatives_by_status(
    initiatives: Sequence[Mapping[str, Any]],
    status: str,
) -> list[Mapping[str, Any]]:
    """Filter initiatives by status."""
    status_lower = status.lower()
    return [i for i in initiatives if (i.get("status") or "").lower() == status_lower]


def resolve_initiative_id(
    initiatives: Sequence[Mapping[str, Any]],
    initiative_input: str,
    auto_accept_matches: bool,
) -> tuple[str | None, dict[str, Any] | None]:
    """Resolve initiative by ID or name.

    Returns:
        Tuple of (initiative_id, fuzzy_info)
        - If found: (id, None)
        - If fuzzy suggestions: (None, fuzzy_info)
        - If not found: (None, None)
    """
    for init in initiatives:
        if init.get("id") == initiative_input:
            return str(init["id"]), None
        name = init.get("name")
        if name and name.lower() == initiative_input.lower():
            return str(init["id"]), None

    matched, fuzzy_info = try_fuzzy_match_by_name(
        list(initiatives), initiative_input, auto_accept_matches
    )

    if matched:
        return str(matched[0]["id"]), None

    return None, fuzzy_info


def resolve_project_id(
    projects: Sequence[Mapping[str, Any]],
    project_input: str,
    auto_accept_matches: bool,
) -> tuple[str | None, dict[str, Any] | None]:
    """Resolve project by ID or name.

    Returns:
        Tuple of (project_id, fuzzy_info)
        - If found: (id, None)
        - If fuzzy suggestions: (None, fuzzy_info)
        - If not found: (None, None)
    """
    for proj in projects:
        if proj.get("id") == project_input:
            return str(proj["id"]), None
        name = proj.get("name")
        if name and name.lower() == project_input.lower():
            return str(proj["id"]), None

    matched, fuzzy_info = try_fuzzy_match_by_name(
        list(projects), project_input, auto_accept_matches
    )

    if matched:
        return str(matched[0]["id"]), None

    return None, fuzzy_info


def build_create_initiative_response(
    initiative_data: Mapping[str, Any],
) -> CreateInitiativeOutput:
    """Build response for create_initiative."""
    document_content: dict[str, Any] = initiative_data.get("documentContent") or {}
    description = document_content.get("content") or initiative_data.get("description")

    initiative: CreatedInitiativeOutput = {
        "id": initiative_data.get("id", ""),
        "name": initiative_data.get("name", ""),
        "description": description,
        "status": initiative_data.get("status", ""),
        "target_date": initiative_data.get("targetDate"),
        "created_at": initiative_data.get("createdAt", ""),
        "updated_at": initiative_data.get("updatedAt", ""),
        "url": initiative_data.get("url", ""),
    }

    result: CreateInitiativeOutput = {"initiative": initiative}
    return cast(CreateInitiativeOutput, remove_none_values_recursive(result))


def build_update_initiative_response(
    initiative_data: Mapping[str, Any], fields_updated: list[str]
) -> UpdateInitiativeOutput:
    """Build response for update_initiative."""
    document_content: dict[str, Any] = initiative_data.get("documentContent") or {}
    description = document_content.get("content") or initiative_data.get("description")

    initiative: CreatedInitiativeOutput = {
        "id": initiative_data.get("id", ""),
        "name": initiative_data.get("name", ""),
        "description": description,
        "status": initiative_data.get("status", ""),
        "target_date": initiative_data.get("targetDate"),
        "created_at": initiative_data.get("createdAt", ""),
        "updated_at": initiative_data.get("updatedAt", ""),
        "url": initiative_data.get("url", ""),
    }

    result: UpdateInitiativeOutput = {
        "initiative": initiative,
        "fields_updated": fields_updated,
    }
    return cast(UpdateInitiativeOutput, remove_none_values_recursive(result))
