from dataclasses import dataclass, fields
from functools import wraps


def kebab_to_snake(name: str) -> str:
    """Convert kebab-case string to snake_case"""
    return name.replace("-", "_")


def accept_kebab_case(cls):
    """Decorator to allow dataclasses to accept kebab-case kwargs"""

    original_init = cls.__init__

    @wraps(original_init)
    def new_init(self, *args, **kwargs):
        transformed_kwargs = {
            kebab_to_snake(key): value for key, value in kwargs.items()
        }

        valid_fields = {f.name for f in fields(cls)}
        filtered_kwargs = {
            key: value
            for key, value in transformed_kwargs.items()
            if key in valid_fields
        }

        original_init(self, *args, **filtered_kwargs)

    cls.__init__ = new_init
    return cls


@accept_kebab_case
@dataclass(kw_only=True)
class Project:
    """Dataclass model defining [project] section of pyproject.toml"""

    name: str
    version: str
    description: str | None

    urls: dict[str, str] | None

    readme: str | None
    license: str | None
    license_files: str | None

    requires_python: str | None
    classifiers: list[str] | None
    dependencies: list[str] | None
