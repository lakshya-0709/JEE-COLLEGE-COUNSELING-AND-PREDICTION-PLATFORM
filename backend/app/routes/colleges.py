"""Colleges API route — GET /api/colleges"""

from fastapi import APIRouter, Query
from app.database import data_store

router = APIRouter()


@router.get("/colleges")
async def list_colleges(
    type: str = Query(None, description="Filter by type: IIT, NIT, IIIT, GFTI"),
    search: str = Query(None, description="Search query for autocomplete"),
):
    """List colleges, optionally filtered by type or search query."""
    if search:
        return data_store.search_institutes(search)
    return data_store.get_institutes(type)


@router.get("/colleges/programs")
async def get_programs(
    institute: str = Query(..., description="Full institute name"),
):
    """Get all programs offered by an institute."""
    return data_store.get_programs_for_institute(institute)


@router.get("/colleges/branches")
async def get_branches(
    types: str = Query(None, description="Comma-separated institute types to filter by (e.g., IIT,NIT)")
):
    """Get all available normalized branch names."""
    type_list = [t.strip() for t in types.split(",")] if types else None
    return data_store.get_branches(type_list)


@router.get("/colleges/metadata")
async def get_metadata():
    """Get metadata about the dataset (states, categories, etc.)."""
    return data_store.metadata
