"""Minimal user context matching the service-style CRUD boundary."""

from pydantic import BaseModel


class UserContext(BaseModel):
    id: str
    customer_id: str
    default_sort: list[str] = ["created_at"]
    default_sort_dir: list[str] = ["desc"]
