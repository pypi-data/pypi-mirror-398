"""Base resource class for Kobana API resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Self

if TYPE_CHECKING:
    from kobana.connection import Connection


class PaginatedList(list[Any]):
    """List with pagination metadata."""

    def __init__(
        self,
        items: list[Any],
        total_count: int = 0,
        total_pages: int = 0,
        current_page: int = 1,
        per_page: int = 25,
    ) -> None:
        super().__init__(items)
        self.total_count = total_count
        self.total_pages = total_pages
        self.current_page = current_page
        self.per_page = per_page

    @property
    def has_next_page(self) -> bool:
        """Check if there's a next page."""
        return self.current_page < self.total_pages

    @property
    def has_previous_page(self) -> bool:
        """Check if there's a previous page."""
        return self.current_page > 1


class BaseResource:
    """Base class for all Kobana API resources."""

    _connection: ClassVar[Connection | None] = None
    _endpoint: ClassVar[str] = ""

    def __init__(self, **attributes: Any) -> None:
        """Initialize resource with attributes."""
        self._attributes = attributes
        self._persisted = False

    @classmethod
    def set_connection(cls, connection: Connection) -> None:
        """Set the connection for this resource class."""
        cls._connection = connection

    @classmethod
    def get_connection(cls) -> Connection:
        """Get the connection for this resource class."""
        if cls._connection is None:
            raise RuntimeError(
                "Connection not set. Use kobana.configure() or create a KobanaClient instance."
            )
        return cls._connection

    @classmethod
    def create(cls, **attributes: Any) -> Self:
        """Create a new resource on the API."""
        connection = cls.get_connection()
        data = connection.post(cls._endpoint, data=attributes)
        instance = cls(**data)
        instance._persisted = True
        return instance

    @classmethod
    def find(cls, id: int | str) -> Self:
        """Find a resource by ID."""
        connection = cls.get_connection()
        data = connection.get(f"{cls._endpoint}/{id}")
        instance = cls(**data)
        instance._persisted = True
        return instance

    @classmethod
    def all(cls, **params: Any) -> PaginatedList[Self]:
        """List all resources with optional filters."""
        connection = cls.get_connection()
        items, pagination = connection.get_list(cls._endpoint, params=params)
        resources = [cls(**item) for item in items]
        for resource in resources:
            resource._persisted = True
        return PaginatedList(
            resources,
            total_count=pagination.get("total_count", 0),
            total_pages=pagination.get("total_pages", 0),
            current_page=pagination.get("current_page", 1),
            per_page=pagination.get("per_page", 25),
        )

    @classmethod
    def find_by(cls, **params: Any) -> Self | None:
        """Find first resource matching params."""
        params["per_page"] = 1
        results = cls.all(**params)
        return results[0] if results else None

    @classmethod
    def find_or_create_by(cls, search_params: dict[str, Any], **create_attrs: Any) -> Self:
        """Find first matching resource or create a new one."""
        existing = cls.find_by(**search_params)
        if existing:
            return existing
        return cls.create(**{**search_params, **create_attrs})

    def save(self) -> bool:
        """Save the resource (create or update)."""
        connection = self.get_connection()
        if self._persisted and self.id:
            data = connection.put(f"{self._endpoint}/{self.id}", data=self._attributes)
        else:
            data = connection.post(self._endpoint, data=self._attributes)
            self._persisted = True
        self._attributes.update(data)
        return True

    def update(self, **attributes: Any) -> bool:
        """Update the resource with new attributes."""
        if not self._persisted or not self.id:
            raise ValueError("Cannot update a resource that hasn't been persisted.")
        connection = self.get_connection()
        self._attributes.update(attributes)
        data = connection.put(f"{self._endpoint}/{self.id}", data=self._attributes)
        self._attributes.update(data)
        return True

    def delete(self) -> bool:
        """Delete the resource."""
        if not self._persisted or not self.id:
            raise ValueError("Cannot delete a resource that hasn't been persisted.")
        connection = self.get_connection()
        connection.delete(f"{self._endpoint}/{self.id}")
        self._persisted = False
        return True

    @property
    def id(self) -> int | None:
        """Get the resource ID."""
        return self._attributes.get("id")

    @property
    def new_record(self) -> bool:
        """Check if this is a new (unpersisted) record."""
        return not self._persisted

    @property
    def persisted(self) -> bool:
        """Check if this record has been persisted."""
        return self._persisted

    def to_dict(self) -> dict[str, Any]:
        """Convert resource to dictionary."""
        return dict(self._attributes)

    def __getattr__(self, name: str) -> Any:
        """Get attribute value."""
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
        return self._attributes.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute value."""
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self._attributes[name] = value

    def __repr__(self) -> str:
        """String representation of the resource."""
        id_str = f" id={self.id}" if self.id else ""
        return f"<{type(self).__name__}{id_str}>"
