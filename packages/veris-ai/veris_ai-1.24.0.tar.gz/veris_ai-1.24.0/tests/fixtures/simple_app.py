from typing import List, Optional

import pytest
from fastapi import Body, FastAPI, HTTPException, Path, Query
from pydantic import BaseModel

from veris_ai import veris


class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    tags: List[str] = []


def make_simple_fastapi_app() -> FastAPI:
    app = FastAPI(
        title="Test API",
        description="A test API app for unit testing",
        version="0.1.0",
    )

    @veris.mock(mode="function")
    async def get_item(item_id: int) -> Item:
        return Item(
            id=item_id,
            name=f"Item {item_id}",
            price=item_id * 10.0,
            tags=[f"tag{item_id}"],
            description=f"Item {item_id} description",
        )

    items = [
        Item(
            id=1,
            name="Item 1",
            price=10.0,
            tags=["tag1", "tag2"],
            description="Item 1 description",
        ),
        Item(id=2, name="Item 2", price=20.0, tags=["tag2", "tag3"]),
        Item(
            id=3,
            name="Item 3",
            price=30.0,
            tags=["tag3", "tag4"],
            description="Item 3 description",
        ),
    ]

    @app.get("/items/{item_id}", response_model=Item, tags=["items"], operation_id="get_item")
    async def read_item(
        item_id: int = Path(..., description="The ID of the item to retrieve"),
        include_details: bool = Query(False, description="Include additional details"),
    ) -> Item:
        """Get a specific item by its ID with optional details."""
        return await get_item(item_id)

    return app


@pytest.fixture
def simple_fastapi_app(simulation_env) -> FastAPI:
    return make_simple_fastapi_app()
