import inspect
from typing import Any, Union

from pydantic import BaseModel


def sphinx_autodoc(cls: type) -> type:
    """
    Decorator to generate Sphinx-compatible docstrings from Pydantic fields.
    Works seamlessly with sphinx.ext.autodoc.
    """
    if not issubclass(cls, BaseModel):
        return cls
    
    # Preserve existing docstring
    existing_doc = inspect.getdoc(cls) or ""
    
    # Generate field documentation
    field_docs = []
    
    for field_name, field_info in cls.model_fields.items():
        # Get field type and handle Optional/Union types
        field_type = field_info.annotation
        type_str = _format_type_for_sphinx(field_type)
        
        # Get description
        description = getattr(field_info, "description", "No description provided")
        
        # Get constraints/validation info
        constraints = _extract_field_constraints(field_info)
        if constraints:
            description += f" {constraints}"
        
        # Add param and type directives
        field_docs.append(f":param {field_name}: {description}")
        field_docs.append(f":type {field_name}: {type_str}")
    
    # Combine existing docstring with field documentation
    if existing_doc and not existing_doc.endswith("\n"):
        existing_doc += "\n"
    
    new_docstring = existing_doc
    if field_docs:
        new_docstring += "\n" + "\n".join(field_docs)
    
    cls.__doc__ = new_docstring
    return cls


def _format_type_for_sphinx(field_type: Any) -> str:
    """Format type annotations for Sphinx documentation."""
    # Handle Optional types (Union[T, None])
    origin = getattr(field_type, "__origin__", None)
    if origin is Union:
        args = getattr(field_type, "__args__", ())
        if len(args) == 2 and type(None) in args:
            non_none_type = next(arg for arg in args if arg is not type(None))
            return f"Optional[{_get_type_name(non_none_type)}]"
    
    return _get_type_name(field_type)


def _get_type_name(type_obj: Any) -> str:
    """Get a clean type name for documentation."""
    if hasattr(type_obj, "__name__"):
        return type_obj.__name__
    elif hasattr(type_obj, "_name"):  # For generic types
        return str(type_obj._name)
    else:
        return str(type_obj)


def _extract_field_constraints(field_info: Any) -> str:
    """Extract validation constraints from field info."""
    constraints = []
    
    # Handle common constraints
    if hasattr(field_info, "constraints"):
        for constraint in field_info.constraints:
            if hasattr(constraint, "ge") and constraint.ge is not None:
                constraints.append(f"minimum: {constraint.ge}")
            if hasattr(constraint, "le") and constraint.le is not None:
                constraints.append(f"maximum: {constraint.le}")
            if hasattr(constraint, "min_length") and constraint.min_length is not None:
                constraints.append(f"min length: {constraint.min_length}")
            if hasattr(constraint, "max_length") and constraint.max_length is not None:
                constraints.append(f"max length: {constraint.max_length}")
    
    return f"({', '.join(constraints)})" if constraints else "" 