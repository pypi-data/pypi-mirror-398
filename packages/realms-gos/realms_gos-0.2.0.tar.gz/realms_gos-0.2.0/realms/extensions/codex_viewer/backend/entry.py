"""
Codex Viewer Backend Extension
Provides API endpoints for viewing and browsing Codex automation scripts.
"""

import json
import traceback
from typing import Any, Dict, List

from ggg.codex import Codex
from kybra_simple_logging import get_logger

logger = get_logger("extensions.codex_viewer")


def extension_sync_call(method_name: str, args: dict):
    """
    Synchronous extension API calls for codex viewing operations
    """
    methods = {
        "get_all_codexes": get_all_codexes,
        "get_codex_details": get_codex_details,
    }

    if method_name not in methods:
        return json.dumps({"success": False, "error": f"Unknown method: {method_name}"})

    function = methods[method_name]

    try:
        return function(args)
    except Exception as e:
        logger.error(f"Error calling {method_name}: {str(e)}")
        logger.error(traceback.format_exc())
        return json.dumps(
            {"success": False, "error": f"Error calling {method_name}: {str(e)}"}
        )


def get_all_codexes(args: str = "{}"):
    """
    Get all codexes with basic info
    """
    try:
        codexes = []
        for codex in Codex.instances():
            codex_data = {
                "_id": str(codex._id),
                "name": codex.name if hasattr(codex, "name") else "",
                "description": (
                    codex.description if hasattr(codex, "description") else ""
                ),
                "created_at": (
                    codex.created_at if hasattr(codex, "created_at") else None
                ),
                "updated_at": (
                    codex.updated_at if hasattr(codex, "updated_at") else None
                ),
                "code_preview": (
                    (codex.code[:200] + "..." if len(codex.code) > 200 else codex.code)
                    if hasattr(codex, "code") and codex.code
                    else ""
                ),
            }
            codexes.append(codex_data)

        return json.dumps({"success": True, "codexes": codexes, "count": len(codexes)})
    except Exception as e:
        logger.error(f"Error getting codexes: {str(e)}")
        logger.error(traceback.format_exc())
        return json.dumps({"success": False, "error": str(e)})


def get_codex_details(args):
    """
    Get detailed information about a specific codex including full code
    """
    try:
        if isinstance(args, str):
            args = json.loads(args)
        codex_id = args.get("codex_id")
        if not codex_id:
            return json.dumps({"success": False, "error": "codex_id is required"})

        # Find codex
        codex = None
        for c in Codex.instances():
            if (
                str(c._id) == codex_id
                or str(c._id).startswith(codex_id)
                or c.name == codex_id
            ):
                codex = c
                break

        if not codex:
            return json.dumps(
                {"success": False, "error": f"Codex {codex_id} not found"}
            )

        codex_data = {
            "_id": str(codex._id),
            "name": codex.name if hasattr(codex, "name") else "",
            "description": codex.description if hasattr(codex, "description") else "",
            "code": codex.code if hasattr(codex, "code") else "",
            "created_at": codex.created_at if hasattr(codex, "created_at") else None,
            "updated_at": codex.updated_at if hasattr(codex, "updated_at") else None,
        }

        return json.dumps({"success": True, "codex": codex_data})
    except Exception as e:
        logger.error(f"Error getting codex details: {str(e)}")
        logger.error(traceback.format_exc())
        return json.dumps({"success": False, "error": str(e)})
