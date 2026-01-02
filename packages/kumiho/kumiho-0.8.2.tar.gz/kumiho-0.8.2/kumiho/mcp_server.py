"""Kumiho MCP Server - Model Context Protocol integration for Kumiho Cloud.

This module provides an MCP (Model Context Protocol) server that exposes
Kumiho Cloud functionality to AI assistants like GitHub Copilot, Claude,
and other MCP-compatible clients.

The server enables AI assistants to:
- Query and navigate asset graphs
- Analyze dependencies and impact
- Search for items across projects
- Track AI lineage and provenance
- Manage revisions and artifacts

Usage:
    Run as a standalone server::

        python -m kumiho.mcp_server

    Or use the CLI entry point::

        kumiho-mcp

Configuration:
    The MCP server uses the same authentication as the Kumiho SDK.
    Run ``kumiho-auth login`` first to cache credentials.

Environment Variables:
    KUMIHO_MCP_LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR). Default: INFO

Example MCP client configuration (VS Code settings.json)::

    {
        "mcp": {
            "servers": {
                "kumiho": {
                    "command": "kumiho-mcp"
                }
            }
        }
    }
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        Resource,
        ResourceTemplate,
        Prompt,
        PromptMessage,
        PromptArgument,
        GetPromptResult,
        CallToolResult,
        ListToolsResult,
        ListResourcesResult,
        ListPromptsResult,
        ReadResourceResult,
        INVALID_PARAMS,
        INTERNAL_ERROR,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Kumiho imports
import kumiho
from kumiho import (
    Project,
    Space,
    Item,
    Revision,
    Artifact,
    Edge,
    Kref,
    EdgeType,
    EdgeDirection,
    DEPENDS_ON,
    DERIVED_FROM,
    REFERENCED,
    CONTAINS,
    CREATED_FROM,
)

# Configure logging
LOG_LEVEL = os.environ.get("KUMIHO_MCP_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("kumiho.mcp")


def _ensure_configured() -> bool:
    """Ensure Kumiho client is configured."""
    try:
        kumiho.auto_configure_from_discovery()
        return True
    except Exception as e:
        logger.warning(f"Auto-configure failed: {e}")
        return False


def _serialize_project(project: Project) -> Dict[str, Any]:
    """Serialize a Project to a JSON-friendly dict."""
    return {
        "project_id": project.project_id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "deprecated": project.deprecated,
        "allow_public": getattr(project, "allow_public", False),
    }


def _serialize_space(space: Space) -> Dict[str, Any]:
    """Serialize a Space to a JSON-friendly dict."""
    return {
        "path": space.path,
        "name": space.name,
        "type": space.type,
        "created_at": space.created_at,
        "author": space.author,
        "username": space.username,
        "metadata": dict(space.metadata) if space.metadata else {},
    }


def _serialize_item(item: Item) -> Dict[str, Any]:
    """Serialize an Item to a JSON-friendly dict."""
    return {
        "kref": item.kref.uri,
        "name": item.name,
        "item_name": item.item_name,
        "kind": item.kind,
        "created_at": item.created_at,
        "author": item.author,
        "username": item.username,
        "metadata": dict(item.metadata) if item.metadata else {},
        "deprecated": item.deprecated,
    }


def _serialize_revision(revision: Revision) -> Dict[str, Any]:
    """Serialize a Revision to a JSON-friendly dict."""
    return {
        "kref": revision.kref.uri,
        "item_kref": revision.item_kref.uri,
        "number": revision.number,
        "latest": revision.latest,
        "tags": list(revision._cached_tags),
        "metadata": dict(revision.metadata) if revision.metadata else {},
        "created_at": revision.created_at,
        "author": revision.author,
        "username": revision.username,
        "deprecated": revision.deprecated,
        "published": revision.published,
        "default_artifact": revision.default_artifact,
    }


def _serialize_artifact(artifact: Artifact) -> Dict[str, Any]:
    """Serialize an Artifact to a JSON-friendly dict."""
    return {
        "kref": artifact.kref.uri,
        "name": artifact.name,
        "location": artifact.location,
        "revision_kref": artifact.revision_kref.uri,
        "created_at": artifact.created_at,
        "metadata": dict(artifact.metadata) if artifact.metadata else {},
    }


def _serialize_edge(edge: Edge) -> Dict[str, Any]:
    """Serialize an Edge to a JSON-friendly dict."""
    return {
        "source_kref": edge.source_kref.uri,
        "target_kref": edge.target_kref.uri,
        "edge_type": edge.edge_type,
        "metadata": dict(edge.metadata) if edge.metadata else {},
        "created_at": edge.created_at,
    }


# ============================================================================
# Tool Implementations
# ============================================================================

def tool_list_projects() -> Dict[str, Any]:
    """List all projects accessible to the current user."""
    _ensure_configured()
    projects = kumiho.get_projects()
    return {
        "projects": [_serialize_project(p) for p in projects],
        "count": len(projects),
    }


def tool_get_project(name: str) -> Dict[str, Any]:
    """Get a project by name."""
    _ensure_configured()
    project = kumiho.get_project(name)
    if not project:
        return {"error": f"Project '{name}' not found"}
    return _serialize_project(project)


def tool_get_spaces(project_name: str, recursive: bool = False) -> Dict[str, Any]:
    """Get spaces within a project."""
    _ensure_configured()
    project = kumiho.get_project(project_name)
    if not project:
        return {"error": f"Project '{project_name}' not found"}
    
    spaces = project.get_spaces(recursive=recursive)
    return {
        "project": project_name,
        "spaces": [_serialize_space(s) for s in spaces],
        "count": len(spaces),
    }


def tool_get_space(space_path: str) -> Dict[str, Any]:
    """Get a space by its path."""
    _ensure_configured()
    try:
        path = space_path if space_path.startswith("/") else f"/{space_path}"
        # Parse project name from path: /project/space/... -> project
        parts = path.strip("/").split("/")
        if len(parts) < 1:
            return {"error": "Invalid space path"}
        project_name = parts[0]
        project = kumiho.get_project(project_name)
        if not project:
            return {"error": f"Project '{project_name}' not found"}
        space = project.get_space(path)
        return _serialize_space(space)
    except Exception as e:
        return {"error": str(e)}


def tool_get_item(kref: str) -> Dict[str, Any]:
    """Get an item by its kref URI."""
    _ensure_configured()
    try:
        item = kumiho.get_item(kref)
        return _serialize_item(item)
    except Exception as e:
        return {"error": str(e)}


def tool_get_revision(kref: str) -> Dict[str, Any]:
    """Get a revision by its kref URI."""
    _ensure_configured()
    try:
        revision = kumiho.get_revision(kref)
        return _serialize_revision(revision)
    except Exception as e:
        return {"error": str(e)}


def tool_get_artifacts(revision_kref: str) -> Dict[str, Any]:
    """Get all artifacts for a revision."""
    _ensure_configured()
    try:
        revision = kumiho.get_revision(revision_kref)
        artifacts = revision.get_artifacts()
        return {
            "revision_kref": revision_kref,
            "artifacts": [_serialize_artifact(a) for a in artifacts],
            "count": len(artifacts),
        }
    except Exception as e:
        return {"error": str(e)}


def tool_get_artifact(artifact_kref: str) -> Dict[str, Any]:
    """Get a single artifact by its kref URI."""
    _ensure_configured()
    try:
        artifact = kumiho.get_artifact(artifact_kref)
        return _serialize_artifact(artifact)
    except Exception as e:
        return {"error": str(e)}


def tool_get_bundle(bundle_kref: str) -> Dict[str, Any]:
    """Get a bundle by its kref URI."""
    _ensure_configured()
    try:
        bundle = kumiho.get_bundle(bundle_kref)
        return _serialize_item(bundle)  # Bundle is a specialized Item
    except Exception as e:
        return {"error": str(e)}


def tool_search_items(
    context_filter: str = "",
    name_filter: str = "",
    kind_filter: str = "",
    include_metadata: bool = False
) -> Dict[str, Any]:
    """Search for items across projects and spaces."""
    _ensure_configured()
    items = kumiho.item_search(
        context_filter=context_filter,
        name_filter=name_filter,
        kind_filter=kind_filter,
    )
    
    serialized = []
    for i in items:
        data = _serialize_item(i)
        if not include_metadata:
            data.pop("metadata", None)
        serialized.append(data)

    return {
        "items": serialized,
        "count": len(items),
        "filters": {
            "context": context_filter,
            "name": name_filter,
            "kind": kind_filter,
        },
    }


def tool_get_dependencies(
    revision_kref: str,
    max_depth: int = 5,
    edge_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get all dependencies of a revision (what it depends on)."""
    _ensure_configured()
    try:
        revision = kumiho.get_revision(revision_kref)
        result = revision.get_all_dependencies(
            edge_type_filter=edge_types,
            max_depth=max_depth,
        )
        return {
            "revision_kref": revision_kref,
            "dependencies": list(result.revision_krefs),
            "count": len(result.revision_krefs),
            "max_depth": max_depth,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_get_dependents(
    revision_kref: str,
    max_depth: int = 5,
    edge_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get all dependents of a revision (what depends on it)."""
    _ensure_configured()
    try:
        revision = kumiho.get_revision(revision_kref)
        result = revision.get_all_dependents(
            edge_type_filter=edge_types,
            max_depth=max_depth,
        )
        return {
            "revision_kref": revision_kref,
            "dependents": list(result.revision_krefs),
            "count": len(result.revision_krefs),
            "max_depth": max_depth,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_get_provenance_summary(
    revision_kref: str,
    max_depth: int = 10
) -> Dict[str, Any]:
    """Get provenance summary with AI metadata."""
    _ensure_configured()
    try:
        target = kumiho.get_revision(revision_kref)
        deps_result = target.get_all_dependencies(max_depth=max_depth, limit=50)
        
        summary = []
        
        # Helper to extract AI params
        def extract_params(rev):
            meta = rev.metadata or {}
            # Common keys in ComfyUI/Stable Diffusion
            keys = ["model", "seed", "resolution", "width", "height", "cfg", "steps", "sampler", "scheduler", "prompt", "negative_prompt", "denoise"]
            params = {k: meta[k] for k in keys if k in meta}
            return params

        # Process target
        summary.append({
            "kref": target.kref.uri,
            "role": "target",
            "params": extract_params(target)
        })

        # Process dependencies
        for kref in deps_result.revision_krefs:
            try:
                rev = kumiho.get_revision(kref.uri)
                params = extract_params(rev)
                if params: # Only include if it has relevant metadata
                    summary.append({
                        "kref": rev.kref.uri,
                        "role": "dependency",
                        "params": params
                    })
            except:
                pass # Skip if not found or error

        return {
            "revision_kref": revision_kref,
            "provenance_summary": summary,
            "dependency_count": len(deps_result.revision_krefs)
        }
    except Exception as e:
        return {"error": str(e)}


def tool_analyze_impact(
    revision_kref: str,
    max_depth: int = 10,
    edge_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Analyze the impact of changes to a revision."""
    _ensure_configured()
    try:
        revision = kumiho.get_revision(revision_kref)
        impacted = revision.analyze_impact(
            edge_type_filter=edge_types,
            max_depth=max_depth,
        )
        return {
            "revision_kref": revision_kref,
            "impacted_revisions": [
                {
                    "revision_kref": iv.revision_kref,
                    "impact_depth": iv.impact_depth,
                }
                for iv in impacted
            ],
            "count": len(impacted),
            "max_depth": max_depth,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_find_path(
    source_kref: str,
    target_kref: str,
    max_depth: int = 10,
    edge_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Find the shortest path between two revisions."""
    _ensure_configured()
    try:
        source = kumiho.get_revision(source_kref)
        target = kumiho.get_revision(target_kref)
        path = source.find_path_to(
            target,
            edge_type_filter=edge_types,
            max_depth=max_depth,
        )
        if not path:
            return {
                "source_kref": source_kref,
                "target_kref": target_kref,
                "path_found": False,
                "message": "No path found between revisions",
            }
        return {
            "source_kref": source_kref,
            "target_kref": target_kref,
            "path_found": True,
            "total_depth": path.total_depth,
            "steps": [
                {
                    "revision_kref": str(step.revision_kref),
                    "edge_type": step.edge_type,
                    "depth": step.depth,
                }
                for step in path.steps
            ],
        }
    except Exception as e:
        return {"error": str(e)}


def tool_get_edges(
    revision_kref: str,
    direction: str = "both",
    edge_type: Optional[str] = None
) -> Dict[str, Any]:
    """Get edges for a revision."""
    _ensure_configured()
    try:
        revision = kumiho.get_revision(revision_kref)
        
        # Map direction string to constant
        dir_map = {
            "outgoing": EdgeDirection.OUTGOING,
            "incoming": EdgeDirection.INCOMING,
            "both": EdgeDirection.BOTH,
        }
        direction_val = dir_map.get(direction.lower(), EdgeDirection.BOTH)
        
        edges = revision.get_edges(
            edge_type_filter=edge_type,
            direction=direction_val,
        )
        return {
            "revision_kref": revision_kref,
            "direction": direction,
            "edges": [_serialize_edge(e) for e in edges],
            "count": len(edges),
        }
    except Exception as e:
        return {"error": str(e)}


def tool_resolve_kref(kref: str) -> Dict[str, Any]:
    """Resolve a kref URI to a file location."""
    _ensure_configured()
    try:
        location = kumiho.resolve(kref)
        return {
            "kref": kref,
            "location": location,
            "resolved": location is not None,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_get_artifacts_by_location(location: str) -> Dict[str, Any]:
    """Find all artifacts at a specific file location (reverse lookup)."""
    _ensure_configured()
    try:
        artifacts = kumiho.get_artifacts_by_location(location)
        return {
            "location": location,
            "artifacts": [_serialize_artifact(a) for a in artifacts],
            "count": len(artifacts),
        }
    except Exception as e:
        return {"error": str(e)}


def tool_get_item_revisions(item_kref: str, include_metadata: bool = False) -> Dict[str, Any]:
    """Get all revisions for an item."""
    _ensure_configured()
    try:
        item = kumiho.get_item(item_kref)
        revisions = item.get_revisions()
        
        serialized = []
        for r in revisions:
            data = _serialize_revision(r)
            if not include_metadata:
                data.pop("metadata", None)
            serialized.append(data)
            
        return {
            "item_kref": item_kref,
            "revisions": serialized,
            "count": len(revisions),
        }
    except Exception as e:
        return {"error": str(e)}


def tool_get_revision_by_tag(item_kref: str, tag: str) -> Dict[str, Any]:
    """Get a revision by tag (e.g., 'latest', 'published', 'approved')."""
    _ensure_configured()
    try:
        item = kumiho.get_item(item_kref)
        revision = item.get_revision_by_tag(tag)
        if not revision:
            return {"error": f"No revision found with tag '{tag}'"}
        return _serialize_revision(revision)
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Write Operations (use with caution)
# ============================================================================

def tool_create_revision(
    item_kref: str,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create a new revision for an item."""
    _ensure_configured()
    try:
        item = kumiho.get_item(item_kref)
        revision = item.create_revision(metadata=metadata or {})
        return {
            "created": True,
            "revision": _serialize_revision(revision),
        }
    except Exception as e:
        return {"error": str(e)}


def tool_tag_revision(revision_kref: str, tag: str) -> Dict[str, Any]:
    """Apply a tag to a revision."""
    _ensure_configured()
    try:
        revision = kumiho.get_revision(revision_kref)
        revision.tag(tag)
        return {
            "tagged": True,
            "revision_kref": revision_kref,
            "tag": tag,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_create_edge(
    source_kref: str,
    target_kref: str,
    edge_type: str,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create an edge between two revisions."""
    _ensure_configured()
    try:
        source = kumiho.get_revision(source_kref)
        target = kumiho.get_revision(target_kref)
        edge = source.create_edge(target, edge_type, metadata=metadata)
        return {
            "created": True,
            "edge": _serialize_edge(edge),
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Create Operations
# ============================================================================

def tool_create_project(
    name: str,
    description: str = "",
    allow_public: bool = False
) -> Dict[str, Any]:
    """Create a new Kumiho project."""
    _ensure_configured()
    try:
        project = kumiho.create_project(name, description)
        if allow_public:
            project.set_public(True)
        return {
            "created": True,
            "project": _serialize_project(project),
        }
    except Exception as e:
        return {"error": str(e)}


def tool_create_space(
    project_name: str,
    space_name: str,
    parent_path: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new space within a project."""
    _ensure_configured()
    try:
        project = kumiho.get_project(project_name)
        if not project:
            return {"error": f"Project '{project_name}' not found"}
        space = project.create_space(space_name, parent_path=parent_path)
        return {
            "created": True,
            "space": _serialize_space(space),
        }
    except Exception as e:
        return {"error": str(e)}


def tool_create_item(
    space_path: str,
    item_name: str,
    kind: str,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create a new item within a space."""
    _ensure_configured()
    try:
        # space_path should be like "/project/space" or "project/space"
        path = space_path if space_path.startswith("/") else f"/{space_path}"
        # Parse project name from path
        parts = path.strip("/").split("/")
        if len(parts) < 1:
            return {"error": "Invalid space path"}
        project_name = parts[0]
        project = kumiho.get_project(project_name)
        if not project:
            return {"error": f"Project '{project_name}' not found"}
        space = project.get_space(path)
        item = space.create_item(item_name, kind)
        if metadata:
            item.set_metadata(metadata)
        return {
            "created": True,
            "item": _serialize_item(item),
        }
    except Exception as e:
        return {"error": str(e)}


def tool_create_artifact(
    revision_kref: str,
    name: str,
    location: str
) -> Dict[str, Any]:
    """Create an artifact for a revision."""
    _ensure_configured()
    try:
        revision = kumiho.get_revision(revision_kref)
        artifact = revision.create_artifact(name, location)
        return {
            "created": True,
            "artifact": _serialize_artifact(artifact),
        }
    except Exception as e:
        return {"error": str(e)}


def tool_create_bundle(
    space_path: str,
    bundle_name: str,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create a new bundle within a space."""
    _ensure_configured()
    try:
        path = space_path if space_path.startswith("/") else f"/{space_path}"
        # Parse project name from path
        parts = path.strip("/").split("/")
        if len(parts) < 1:
            return {"error": "Invalid space path"}
        project_name = parts[0]
        project = kumiho.get_project(project_name)
        if not project:
            return {"error": f"Project '{project_name}' not found"}
        space = project.get_space(path)
        bundle = space.create_bundle(bundle_name, metadata=metadata)
        return {
            "created": True,
            "bundle": _serialize_item(bundle),  # Bundle is a specialized Item
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Delete Operations
# ============================================================================

def tool_delete_project(project_name: str, force: bool = False) -> Dict[str, Any]:
    """Delete a project."""
    _ensure_configured()
    try:
        project = kumiho.get_project(project_name)
        if not project:
            return {"error": f"Project '{project_name}' not found"}
        project.delete(force=force)
        return {
            "deleted": True,
            "project_name": project_name,
            "force": force,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_delete_space(space_path: str, force: bool = False) -> Dict[str, Any]:
    """Delete a space."""
    _ensure_configured()
    try:
        path = space_path if space_path.startswith("/") else f"/{space_path}"
        # Parse project name from path
        parts = path.strip("/").split("/")
        if len(parts) < 1:
            return {"error": "Invalid space path"}
        project_name = parts[0]
        project = kumiho.get_project(project_name)
        if not project:
            return {"error": f"Project '{project_name}' not found"}
        space = project.get_space(path)
        space.delete(force=force)
        return {
            "deleted": True,
            "space_path": space_path,
            "force": force,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_delete_item(item_kref: str, force: bool = False) -> Dict[str, Any]:
    """Delete an item."""
    _ensure_configured()
    try:
        item = kumiho.get_item(item_kref)
        item.delete(force=force)
        return {
            "deleted": True,
            "item_kref": item_kref,
            "force": force,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_delete_revision(revision_kref: str) -> Dict[str, Any]:
    """Delete a revision."""
    _ensure_configured()
    try:
        revision = kumiho.get_revision(revision_kref)
        revision.delete()
        return {
            "deleted": True,
            "revision_kref": revision_kref,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_delete_artifact(artifact_kref: str) -> Dict[str, Any]:
    """Delete an artifact."""
    _ensure_configured()
    try:
        artifact = kumiho.get_artifact(artifact_kref)
        artifact.delete()
        return {
            "deleted": True,
            "artifact_kref": artifact_kref,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_delete_edge(
    source_kref: str,
    target_kref: str,
    edge_type: str
) -> Dict[str, Any]:
    """Delete an edge between two revisions."""
    _ensure_configured()
    try:
        source = kumiho.get_revision(source_kref)
        target = kumiho.get_revision(target_kref)
        source.delete_edge(target, edge_type)
        return {
            "deleted": True,
            "source_kref": source_kref,
            "target_kref": target_kref,
            "edge_type": edge_type,
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Update Operations
# ============================================================================

def tool_untag_revision(revision_kref: str, tag: str) -> Dict[str, Any]:
    """Remove a tag from a revision."""
    _ensure_configured()
    try:
        revision = kumiho.get_revision(revision_kref)
        revision.untag(tag)
        return {
            "untagged": True,
            "revision_kref": revision_kref,
            "tag": tag,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_set_metadata(
    kref: str,
    metadata: Dict[str, str]
) -> Dict[str, Any]:
    """Set metadata on an item or revision."""
    _ensure_configured()
    try:
        # Determine if this is an item or revision kref
        if "?r=" in kref:
            obj = kumiho.get_revision(kref)
        else:
            obj = kumiho.get_item(kref)
        obj.set_metadata(metadata)
        return {
            "updated": True,
            "kref": kref,
            "metadata": metadata,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_deprecate_item(item_kref: str, deprecated: bool = True) -> Dict[str, Any]:
    """Set the deprecated status of an item."""
    _ensure_configured()
    try:
        item = kumiho.get_item(item_kref)
        item.set_deprecated(deprecated)
        return {
            "updated": True,
            "item_kref": item_kref,
            "deprecated": deprecated,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_add_bundle_member(
    bundle_kref: str,
    item_kref: str
) -> Dict[str, Any]:
    """Add an item to a bundle."""
    _ensure_configured()
    try:
        bundle = kumiho.get_bundle(bundle_kref)
        item = kumiho.get_item(item_kref)
        bundle.add_member(item)
        return {
            "added": True,
            "bundle_kref": bundle_kref,
            "item_kref": item_kref,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_remove_bundle_member(
    bundle_kref: str,
    item_kref: str
) -> Dict[str, Any]:
    """Remove an item from a bundle."""
    _ensure_configured()
    try:
        bundle = kumiho.get_bundle(bundle_kref)
        item = kumiho.get_item(item_kref)
        bundle.remove_member(item)
        return {
            "removed": True,
            "bundle_kref": bundle_kref,
            "item_kref": item_kref,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_get_bundle_members(bundle_kref: str) -> Dict[str, Any]:
    """Get all members of a bundle."""
    _ensure_configured()
    try:
        bundle = kumiho.get_bundle(bundle_kref)
        members = bundle.get_members()
        return {
            "bundle_kref": bundle_kref,
            "members": [
                {
                    "item_kref": m.item_kref.uri if hasattr(m.item_kref, 'uri') else str(m.item_kref),
                    "added_at": m.added_at,
                    "added_by": m.added_by,
                    "added_by_username": m.added_by_username,
                    "added_in_revision": m.added_in_revision,
                }
                for m in members
            ],
            "count": len(members),
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# MCP Server Definition
# ============================================================================

TOOLS: List[Dict[str, Any]] = [
    # Read operations - Projects
    {
        "name": "kumiho_list_projects",
        "description": "List all Kumiho projects accessible to the current user. Returns project names, descriptions, and metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "kumiho_get_project",
        "description": "Get details about a specific Kumiho project by name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the project to retrieve",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "kumiho_get_spaces",
        "description": "Get spaces (organizational folders) within a Kumiho project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "The name of the project",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "If true, include nested spaces. Default: false",
                    "default": False,
                },
            },
            "required": ["project_name"],
        },
    },
    {
        "name": "kumiho_get_space",
        "description": "Get a space by its path. Example: /project/space or project/space",
        "inputSchema": {
            "type": "object",
            "properties": {
                "space_path": {
                    "type": "string",
                    "description": "The path of the space (e.g., '/project/space' or 'project/space')",
                },
            },
            "required": ["space_path"],
        },
    },
    # Read operations - Items
    {
        "name": "kumiho_get_item",
        "description": "Get a Kumiho item (versioned asset) by its kref URI. Example: kref://project/space/item.kind",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kref": {
                    "type": "string",
                    "description": "The kref URI of the item (e.g., kref://project/space/item.kind)",
                },
            },
            "required": ["kref"],
        },
    },
    {
        "name": "kumiho_search_items",
        "description": "Search for items across Kumiho projects and spaces. Supports filtering by context (project/space path), name, and kind (model, texture, workflow, etc.).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "context_filter": {
                    "type": "string",
                    "description": "Filter by project or space path. Supports wildcards like 'project-*' or '*/characters/*'",
                    "default": "",
                },
                "name_filter": {
                    "type": "string",
                    "description": "Filter by item name. Supports wildcards like 'hero*'",
                    "default": "",
                },
                "kind_filter": {
                    "type": "string",
                    "description": "Filter by item kind (e.g., 'model', 'texture', 'workflow')",
                    "default": "",
                },
                "include_metadata": {
                    "type": "boolean",
                    "description": "Whether to include full metadata for each item. Default: false",
                    "default": False,
                },
            },
            "required": [],
        },
    },
    {
        "name": "kumiho_get_item_revisions",
        "description": "Get all revisions for a Kumiho item. Shows version history with tags.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_kref": {
                    "type": "string",
                    "description": "The kref URI of the item",
                },
                "include_metadata": {
                    "type": "boolean",
                    "description": "Whether to include full metadata for each revision. Default: false",
                    "default": False,
                },
            },
            "required": ["item_kref"],
        },
    },
    # Read operations - Revisions
    {
        "name": "kumiho_get_revision",
        "description": "Get a specific revision by its kref URI. Example: kref://project/space/item.kind?r=1",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kref": {
                    "type": "string",
                    "description": "The kref URI of the revision (e.g., kref://project/space/item.kind?r=1)",
                },
            },
            "required": ["kref"],
        },
    },
    {
        "name": "kumiho_get_revision_by_tag",
        "description": "Get a revision by its tag (e.g., 'latest', 'published', 'approved').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_kref": {
                    "type": "string",
                    "description": "The kref URI of the item",
                },
                "tag": {
                    "type": "string",
                    "description": "The tag to look for (e.g., 'latest', 'published', 'approved')",
                },
            },
            "required": ["item_kref", "tag"],
        },
    },
    # Read operations - Artifacts
    {
        "name": "kumiho_get_artifacts",
        "description": "Get all artifacts (file references) for a revision. Shows file paths/locations without uploading files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "revision_kref": {
                    "type": "string",
                    "description": "The kref URI of the revision",
                },
            },
            "required": ["revision_kref"],
        },
    },
    {
        "name": "kumiho_get_artifact",
        "description": "Get a single artifact by its kref URI. Example: kref://project/space/item.kind?r=1&a=mesh.fbx",
        "inputSchema": {
            "type": "object",
            "properties": {
                "artifact_kref": {
                    "type": "string",
                    "description": "The kref URI of the artifact",
                },
            },
            "required": ["artifact_kref"],
        },
    },
    {
        "name": "kumiho_get_bundle",
        "description": "Get a bundle by its kref URI. Bundles group related items together.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bundle_kref": {
                    "type": "string",
                    "description": "The kref URI of the bundle (e.g., kref://project/space/name.bundle)",
                },
            },
            "required": ["bundle_kref"],
        },
    },
    {
        "name": "kumiho_resolve_kref",
        "description": "Resolve a kref URI to a file location. Returns the actual file path for an artifact or revision's default artifact.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kref": {
                    "type": "string",
                    "description": "The kref URI to resolve",
                },
            },
            "required": ["kref"],
        },
    },
    {
        "name": "kumiho_get_artifacts_by_location",
        "description": "Find all Kumiho artifacts that reference a specific file location. Useful for reverse lookups.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The file path or URI to search for",
                },
            },
            "required": ["location"],
        },
    },
    # Graph traversal - Dependencies and Lineage
    {
        "name": "kumiho_get_dependencies",
        "description": "Get all dependencies of a revision (what it depends on). Traverses the graph to find direct and indirect dependencies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "revision_kref": {
                    "type": "string",
                    "description": "The kref URI of the revision",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum traversal depth (1-20). Default: 5",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                },
                "edge_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by edge types (e.g., ['DEPENDS_ON', 'DERIVED_FROM']). Default: all types",
                },
            },
            "required": ["revision_kref"],
        },
    },
    {
        "name": "kumiho_get_dependents",
        "description": "Get all dependents of a revision (what depends on it). Useful for understanding downstream impact.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "revision_kref": {
                    "type": "string",
                    "description": "The kref URI of the revision",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum traversal depth (1-20). Default: 5",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                },
                "edge_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by edge types. Default: all types",
                },
            },
            "required": ["revision_kref"],
        },
    },
    {
        "name": "kumiho_get_provenance_summary",
        "description": "Get a summary of the provenance (lineage) of a revision, including used models, seeds, and parameters from upstream dependencies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "revision_kref": {
                    "type": "string",
                    "description": "The kref URI of the revision to analyze",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum traversal depth. Default: 10",
                    "default": 10,
                },
            },
            "required": ["revision_kref"],
        },
    },
    {
        "name": "kumiho_analyze_impact",
        "description": "Analyze the impact of changes to a revision. Returns all revisions that would be affected, sorted by proximity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "revision_kref": {
                    "type": "string",
                    "description": "The kref URI of the revision to analyze",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum traversal depth. Default: 10",
                    "default": 10,
                },
                "edge_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by edge types. Default: all types",
                },
            },
            "required": ["revision_kref"],
        },
    },
    {
        "name": "kumiho_find_path",
        "description": "Find the shortest path between two revisions in the dependency graph. Useful for understanding how assets are connected.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_kref": {
                    "type": "string",
                    "description": "The kref URI of the source revision",
                },
                "target_kref": {
                    "type": "string",
                    "description": "The kref URI of the target revision",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum path length to search. Default: 10",
                    "default": 10,
                },
                "edge_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by edge types. Default: all types",
                },
            },
            "required": ["source_kref", "target_kref"],
        },
    },
    {
        "name": "kumiho_get_edges",
        "description": "Get edges (relationships) for a revision. Can filter by direction and edge type.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "revision_kref": {
                    "type": "string",
                    "description": "The kref URI of the revision",
                },
                "direction": {
                    "type": "string",
                    "enum": ["outgoing", "incoming", "both"],
                    "description": "Edge direction: 'outgoing' (what this depends on), 'incoming' (what depends on this), or 'both'. Default: 'both'",
                    "default": "both",
                },
                "edge_type": {
                    "type": "string",
                    "description": "Filter by edge type (e.g., 'DEPENDS_ON', 'DERIVED_FROM')",
                },
            },
            "required": ["revision_kref"],
        },
    },
    # Write operations
    {
        "name": "kumiho_create_revision",
        "description": "Create a new revision for an item. Use this to version an asset.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_kref": {
                    "type": "string",
                    "description": "The kref URI of the item to create a revision for",
                },
                "metadata": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Optional metadata key-value pairs (e.g., {'artist': 'name', 'software': 'maya'})",
                },
            },
            "required": ["item_kref"],
        },
    },
    {
        "name": "kumiho_tag_revision",
        "description": "Apply a tag to a revision. Common tags: 'approved', 'published', 'ready-for-review'.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "revision_kref": {
                    "type": "string",
                    "description": "The kref URI of the revision to tag",
                },
                "tag": {
                    "type": "string",
                    "description": "The tag to apply",
                },
            },
            "required": ["revision_kref", "tag"],
        },
    },
    {
        "name": "kumiho_create_edge",
        "description": "Create an edge (relationship) between two revisions. Use edge types: DEPENDS_ON, DERIVED_FROM, REFERENCED, CONTAINS, CREATED_FROM.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_kref": {
                    "type": "string",
                    "description": "The kref URI of the source revision",
                },
                "target_kref": {
                    "type": "string",
                    "description": "The kref URI of the target revision",
                },
                "edge_type": {
                    "type": "string",
                    "enum": ["DEPENDS_ON", "DERIVED_FROM", "REFERENCED", "CONTAINS", "CREATED_FROM", "BELONGS_TO"],
                    "description": "The type of relationship",
                },
                "metadata": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Optional metadata for the edge",
                },
            },
            "required": ["source_kref", "target_kref", "edge_type"],
        },
    },
    # Create operations
    {
        "name": "kumiho_create_project",
        "description": "Create a new Kumiho project. Projects are top-level containers for spaces and items.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the project (URL-safe, e.g., 'my-vfx-project')",
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the project",
                    "default": "",
                },
                "allow_public": {
                    "type": "boolean",
                    "description": "Whether to allow public access. Default: false",
                    "default": False,
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "kumiho_create_space",
        "description": "Create a new space (folder) within a project. Spaces organize items hierarchically.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "The name of the project",
                },
                "space_name": {
                    "type": "string",
                    "description": "The name of the space to create",
                },
                "parent_path": {
                    "type": "string",
                    "description": "Optional parent path for nested spaces (e.g., '/project/parent-space')",
                },
            },
            "required": ["project_name", "space_name"],
        },
    },
    {
        "name": "kumiho_create_item",
        "description": "Create a new item (versioned asset) within a space. Items can be models, textures, workflows, etc.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "space_path": {
                    "type": "string",
                    "description": "The path to the space (e.g., 'project/space' or '/project/space')",
                },
                "item_name": {
                    "type": "string",
                    "description": "The name of the item (e.g., 'hero-character')",
                },
                "kind": {
                    "type": "string",
                    "description": "The kind of item (e.g., 'model', 'texture', 'workflow', 'rig')",
                },
                "metadata": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Optional metadata key-value pairs",
                },
            },
            "required": ["space_path", "item_name", "kind"],
        },
    },
    {
        "name": "kumiho_create_artifact",
        "description": "Create an artifact (file reference) for a revision. Files stay on your storage - only the path is tracked.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "revision_kref": {
                    "type": "string",
                    "description": "The kref URI of the revision to add the artifact to",
                },
                "name": {
                    "type": "string",
                    "description": "The name of the artifact (e.g., 'mesh', 'textures', 'hero.fbx')",
                },
                "location": {
                    "type": "string",
                    "description": "The file path or URI (e.g., '/assets/hero.fbx', 'smb://server/assets/hero.fbx')",
                },
            },
            "required": ["revision_kref", "name", "location"],
        },
    },
    {
        "name": "kumiho_create_bundle",
        "description": "Create a bundle to group related items together. Bundles track membership history.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "space_path": {
                    "type": "string",
                    "description": "The path to the space (e.g., 'project/space')",
                },
                "bundle_name": {
                    "type": "string",
                    "description": "The name of the bundle",
                },
                "metadata": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Optional metadata key-value pairs",
                },
            },
            "required": ["space_path", "bundle_name"],
        },
    },
    # Delete operations
    {
        "name": "kumiho_delete_project",
        "description": "Delete a project. Use force=true to permanently delete with all contents.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "The name of the project to delete",
                },
                "force": {
                    "type": "boolean",
                    "description": "If true, permanently delete. If false, soft-delete (deprecate). Default: false",
                    "default": False,
                },
            },
            "required": ["project_name"],
        },
    },
    {
        "name": "kumiho_delete_space",
        "description": "Delete a space. Use force=true to delete even if it contains items.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "space_path": {
                    "type": "string",
                    "description": "The path of the space to delete (e.g., '/project/space')",
                },
                "force": {
                    "type": "boolean",
                    "description": "If true, force delete with contents. Default: false",
                    "default": False,
                },
            },
            "required": ["space_path"],
        },
    },
    {
        "name": "kumiho_delete_item",
        "description": "Delete an item. Use force=true to delete even if it has revisions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_kref": {
                    "type": "string",
                    "description": "The kref URI of the item to delete",
                },
                "force": {
                    "type": "boolean",
                    "description": "If true, force delete with all revisions. Default: false",
                    "default": False,
                },
            },
            "required": ["item_kref"],
        },
    },
    {
        "name": "kumiho_delete_revision",
        "description": "Delete a specific revision of an item.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "revision_kref": {
                    "type": "string",
                    "description": "The kref URI of the revision to delete",
                },
            },
            "required": ["revision_kref"],
        },
    },
    {
        "name": "kumiho_delete_artifact",
        "description": "Delete an artifact from a revision.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "artifact_kref": {
                    "type": "string",
                    "description": "The kref URI of the artifact to delete",
                },
            },
            "required": ["artifact_kref"],
        },
    },
    {
        "name": "kumiho_delete_edge",
        "description": "Delete an edge (relationship) between two revisions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_kref": {
                    "type": "string",
                    "description": "The kref URI of the source revision",
                },
                "target_kref": {
                    "type": "string",
                    "description": "The kref URI of the target revision",
                },
                "edge_type": {
                    "type": "string",
                    "enum": ["DEPENDS_ON", "DERIVED_FROM", "REFERENCED", "CONTAINS", "CREATED_FROM", "BELONGS_TO"],
                    "description": "The type of relationship to delete",
                },
            },
            "required": ["source_kref", "target_kref", "edge_type"],
        },
    },
    # Update operations
    {
        "name": "kumiho_untag_revision",
        "description": "Remove a tag from a revision.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "revision_kref": {
                    "type": "string",
                    "description": "The kref URI of the revision",
                },
                "tag": {
                    "type": "string",
                    "description": "The tag to remove",
                },
            },
            "required": ["revision_kref", "tag"],
        },
    },
    {
        "name": "kumiho_set_metadata",
        "description": "Set or update metadata on an item or revision.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kref": {
                    "type": "string",
                    "description": "The kref URI of the item or revision",
                },
                "metadata": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Metadata key-value pairs to set",
                },
            },
            "required": ["kref", "metadata"],
        },
    },
    {
        "name": "kumiho_deprecate_item",
        "description": "Set the deprecated status of an item. Deprecated items are hidden from searches.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_kref": {
                    "type": "string",
                    "description": "The kref URI of the item",
                },
                "deprecated": {
                    "type": "boolean",
                    "description": "True to deprecate, False to restore. Default: true",
                    "default": True,
                },
            },
            "required": ["item_kref"],
        },
    },
    # Bundle operations
    {
        "name": "kumiho_add_bundle_member",
        "description": "Add an item to a bundle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bundle_kref": {
                    "type": "string",
                    "description": "The kref URI of the bundle",
                },
                "item_kref": {
                    "type": "string",
                    "description": "The kref URI of the item to add",
                },
            },
            "required": ["bundle_kref", "item_kref"],
        },
    },
    {
        "name": "kumiho_remove_bundle_member",
        "description": "Remove an item from a bundle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bundle_kref": {
                    "type": "string",
                    "description": "The kref URI of the bundle",
                },
                "item_kref": {
                    "type": "string",
                    "description": "The kref URI of the item to remove",
                },
            },
            "required": ["bundle_kref", "item_kref"],
        },
    },
    {
        "name": "kumiho_get_bundle_members",
        "description": "Get all items in a bundle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bundle_kref": {
                    "type": "string",
                    "description": "The kref URI of the bundle",
                },
            },
            "required": ["bundle_kref"],
        },
    },
]


# Tool handler dispatch
TOOL_HANDLERS = {
    "kumiho_list_projects": lambda args: tool_list_projects(),
    "kumiho_get_project": lambda args: tool_get_project(args["name"]),
    "kumiho_get_spaces": lambda args: tool_get_spaces(
        args["project_name"],
        args.get("recursive", False),
    ),
    "kumiho_get_space": lambda args: tool_get_space(args["space_path"]),
    "kumiho_get_item": lambda args: tool_get_item(args["kref"]),
    "kumiho_search_items": lambda args: tool_search_items(
        args.get("context_filter", ""),
        args.get("name_filter", ""),
        args.get("kind_filter", ""),
        args.get("include_metadata", False),
    ),
    "kumiho_get_item_revisions": lambda args: tool_get_item_revisions(
        args["item_kref"],
        args.get("include_metadata", False),
    ),
    "kumiho_get_revision": lambda args: tool_get_revision(args["kref"]),
    "kumiho_get_revision_by_tag": lambda args: tool_get_revision_by_tag(
        args["item_kref"],
        args["tag"],
    ),
    "kumiho_get_artifacts": lambda args: tool_get_artifacts(args["revision_kref"]),
    "kumiho_get_artifact": lambda args: tool_get_artifact(args["artifact_kref"]),
    "kumiho_get_bundle": lambda args: tool_get_bundle(args["bundle_kref"]),
    "kumiho_resolve_kref": lambda args: tool_resolve_kref(args["kref"]),
    "kumiho_get_artifacts_by_location": lambda args: tool_get_artifacts_by_location(
        args["location"]
    ),
    "kumiho_get_dependencies": lambda args: tool_get_dependencies(
        args["revision_kref"],
        args.get("max_depth", 5),
        args.get("edge_types"),
    ),
    "kumiho_get_dependents": lambda args: tool_get_dependents(
        args["revision_kref"],
        args.get("max_depth", 5),
        args.get("edge_types"),
    ),
    "kumiho_get_provenance_summary": lambda args: tool_get_provenance_summary(
        args["revision_kref"],
        args.get("max_depth", 10),
    ),
    "kumiho_analyze_impact": lambda args: tool_analyze_impact(
        args["revision_kref"],
        args.get("max_depth", 10),
        args.get("edge_types"),
    ),
    "kumiho_find_path": lambda args: tool_find_path(
        args["source_kref"],
        args["target_kref"],
        args.get("max_depth", 10),
        args.get("edge_types"),
    ),
    "kumiho_get_edges": lambda args: tool_get_edges(
        args["revision_kref"],
        args.get("direction", "both"),
        args.get("edge_type"),
    ),
    "kumiho_create_revision": lambda args: tool_create_revision(
        args["item_kref"],
        args.get("metadata"),
    ),
    "kumiho_tag_revision": lambda args: tool_tag_revision(
        args["revision_kref"],
        args["tag"],
    ),
    "kumiho_create_edge": lambda args: tool_create_edge(
        args["source_kref"],
        args["target_kref"],
        args["edge_type"],
        args.get("metadata"),
    ),
    # Create operations
    "kumiho_create_project": lambda args: tool_create_project(
        args["name"],
        args.get("description", ""),
        args.get("allow_public", False),
    ),
    "kumiho_create_space": lambda args: tool_create_space(
        args["project_name"],
        args["space_name"],
        args.get("parent_path"),
    ),
    "kumiho_create_item": lambda args: tool_create_item(
        args["space_path"],
        args["item_name"],
        args["kind"],
        args.get("metadata"),
    ),
    "kumiho_create_artifact": lambda args: tool_create_artifact(
        args["revision_kref"],
        args["name"],
        args["location"],
    ),
    "kumiho_create_bundle": lambda args: tool_create_bundle(
        args["space_path"],
        args["bundle_name"],
        args.get("metadata"),
    ),
    # Delete operations
    "kumiho_delete_project": lambda args: tool_delete_project(
        args["project_name"],
        args.get("force", False),
    ),
    "kumiho_delete_space": lambda args: tool_delete_space(
        args["space_path"],
        args.get("force", False),
    ),
    "kumiho_delete_item": lambda args: tool_delete_item(
        args["item_kref"],
        args.get("force", False),
    ),
    "kumiho_delete_revision": lambda args: tool_delete_revision(
        args["revision_kref"],
    ),
    "kumiho_delete_artifact": lambda args: tool_delete_artifact(
        args["artifact_kref"],
    ),
    "kumiho_delete_edge": lambda args: tool_delete_edge(
        args["source_kref"],
        args["target_kref"],
        args["edge_type"],
    ),
    # Update operations
    "kumiho_untag_revision": lambda args: tool_untag_revision(
        args["revision_kref"],
        args["tag"],
    ),
    "kumiho_set_metadata": lambda args: tool_set_metadata(
        args["kref"],
        args["metadata"],
    ),
    "kumiho_deprecate_item": lambda args: tool_deprecate_item(
        args["item_kref"],
        args.get("deprecated", True),
    ),
    # Bundle operations
    "kumiho_add_bundle_member": lambda args: tool_add_bundle_member(
        args["bundle_kref"],
        args["item_kref"],
    ),
    "kumiho_remove_bundle_member": lambda args: tool_remove_bundle_member(
        args["bundle_kref"],
        args["item_kref"],
    ),
    "kumiho_get_bundle_members": lambda args: tool_get_bundle_members(
        args["bundle_kref"],
    ),
}


# ============================================================================
# MCP Server Implementation
# ============================================================================

def create_mcp_server() -> "Server":
    """Create and configure the Kumiho MCP server."""
    if not MCP_AVAILABLE:
        raise ImportError(
            "MCP SDK not installed. Install with: pip install mcp"
        )
    
    server = Server("kumiho-mcp")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List all available Kumiho tools."""
        return [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["inputSchema"],
            )
            for t in TOOLS
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
        """Handle tool invocations."""
        logger.debug(f"Tool call: {name} with args: {arguments}")
        
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}),
            )]
        
        try:
            # Run the tool handler (may be blocking gRPC call)
            # Use asyncio.to_thread to propagate contextvars (like kumiho.use_client)
            result = await asyncio.to_thread(handler, arguments)
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str),
            )]
        except Exception as e:
            logger.exception(f"Tool {name} failed")
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e)}),
            )]
    
    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """List available resources (projects as resources)."""
        try:
            _ensure_configured()
            projects = kumiho.get_projects()
            return [
                Resource(
                    uri=f"kumiho://project/{p.name}",
                    name=p.name,
                    description=p.description or f"Kumiho project: {p.name}",
                    mimeType="application/json",
                )
                for p in projects
            ]
        except Exception as e:
            logger.warning(f"Failed to list resources: {e}")
            return []
    
    @server.read_resource()
    async def read_resource(uri: str) -> str:
        """Read a resource by URI."""
        if uri.startswith("kumiho://project/"):
            project_name = uri[len("kumiho://project/"):]
            # Use asyncio.to_thread to propagate contextvars
            result = await asyncio.to_thread(tool_get_project, project_name)
            return json.dumps(result, indent=2, default=str)
        
        raise ValueError(f"Unknown resource URI: {uri}")
    
    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        """List available prompts."""
        return [
            Prompt(
                name="analyze_asset",
                description="Analyze a Kumiho asset's dependencies and impact",
                arguments=[
                    PromptArgument(
                        name="kref",
                        description="The kref URI of the asset to analyze",
                        required=True,
                    ),
                ],
            ),
            Prompt(
                name="find_assets",
                description="Find assets matching criteria",
                arguments=[
                    PromptArgument(
                        name="kind",
                        description="Asset kind (model, texture, workflow, etc.)",
                        required=False,
                    ),
                    PromptArgument(
                        name="project",
                        description="Project name to search in",
                        required=False,
                    ),
                ],
            ),
        ]
    
    @server.get_prompt()
    async def get_prompt(name: str, arguments: Optional[dict] = None) -> GetPromptResult:
        """Get a prompt by name."""
        args = arguments or {}
        
        if name == "analyze_asset":
            kref = args.get("kref", "")
            return GetPromptResult(
                description=f"Analyze asset: {kref}",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"""Analyze the Kumiho asset at {kref}:

1. First, get the revision details using kumiho_get_revision
2. Get all artifacts using kumiho_get_artifacts  
3. Analyze dependencies using kumiho_get_dependencies
4. Check impact using kumiho_analyze_impact
5. Summarize the asset's role in the dependency graph"""
                        ),
                    ),
                ],
            )
        
        if name == "find_assets":
            kind = args.get("kind", "")
            project = args.get("project", "")
            return GetPromptResult(
                description=f"Find assets: kind={kind}, project={project}",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"""Find Kumiho assets with these criteria:
- Kind: {kind or 'any'}
- Project: {project or 'all projects'}

Use kumiho_search_items to find matching assets and summarize the results."""
                        ),
                    ),
                ],
            )
        
        raise ValueError(f"Unknown prompt: {name}")
    
    return server


async def run_server() -> None:
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        print(
            "Error: MCP SDK not installed.\n"
            "Install with: pip install 'kumiho[mcp]' or pip install mcp",
            file=sys.stderr,
        )
        sys.exit(1)
    
    logger.info("Starting Kumiho MCP server...")
    server = create_mcp_server()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """Entry point for the MCP server CLI."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
