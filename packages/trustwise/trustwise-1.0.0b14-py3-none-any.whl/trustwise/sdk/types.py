import json
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveFloat,
    PositiveInt,
    constr,
)

from trustwise.sdk.utils.docs_utils import sphinx_autodoc


class SDKBaseModel(BaseModel):
    """Base model for all SDK types with common functionality."""
    model_config = ConfigDict(extra="forbid")

    def to_json(self, **kwargs: dict[str, object]) -> str:
        """
        Return a JSON string representation of the model.
        Ensures valid JSON output regardless of Pydantic version.
        Always excludes None fields by default.
        """
        kwargs.setdefault("exclude_none", True)
        return self.model_dump_json(**kwargs)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump(exclude_none=True)

    @classmethod
    def validate_score_range(cls, v: float | int | list | dict, min_value: float, max_value: float, label: str) -> object:
        """Validate that a score or list/dict of scores falls within the specified range."""
        if isinstance(v, float) or isinstance(v, int):
            if not (min_value <= v <= max_value):
                raise ValueError(f"{label} score {v} must be between {min_value} and {max_value}")
        elif isinstance(v, list):
            for s in v:
                if not (min_value <= s <= max_value):
                    raise ValueError(f"{label} score {s} must be between {min_value} and {max_value}")
        elif isinstance(v, dict):
            for k, s in v.items():
                if not (min_value <= s <= max_value):
                    raise ValueError(f"{label} score for '{k}' was {s}, must be between {min_value} and {max_value}")
        return v

    @staticmethod
    def format_validation_error(model_cls: type, validation_error: Exception) -> str:
        """
        Format a Pydantic ValidationError into a user-friendly error message using field types and descriptions.
        Distinguishes between missing and invalid arguments, and sets the error prefix accordingly.
        """
        errors = validation_error.errors()
        model_fields = getattr(model_cls, "model_fields", getattr(model_cls, "__fields__", {}))
        messages = []
        error_types = set()
        def get_type_str(field_type: type) -> str:
            origin = getattr(field_type, "__origin__", None)
            args = getattr(field_type, "__args__", None)
            if origin and args:
                origin_name = getattr(origin, "__name__", str(origin))
                args_str = ", ".join(get_type_str(a) for a in args)
                return f"{origin_name}[{args_str}]"
            return getattr(field_type, "__name__", str(field_type))
        for err in errors:
            loc = err.get("loc", [])
            field = loc[0] if loc else None
            actual_value = err.get("input", None)
            actual_type = type(actual_value).__name__ if actual_value is not None else "NoneType"
            err_type = err.get("type", "")
            if err_type.startswith("missing"):
                error_types.add("missing")
            else:
                error_types.add("invalid")
            if field and field in model_fields:
                field_info = model_fields[field]
                field_type = getattr(field_info, "annotation", getattr(field_info, "type_", None))
                type_str = get_type_str(field_type) if field_type else "unknown"
                if err_type.startswith("missing"):
                    messages.append(f"'{field}' (missing required argument, expected type: {type_str})")
                else:
                    messages.append(
                        f"'{field}' (invalid value: expected type: {type_str}, got: {actual_type} [value: {actual_value!r}])"
                    )
            elif field:
                if err_type.startswith("missing"):
                    messages.append(f"'{field}' (missing required argument)")
                else:
                    messages.append(f"'{field}' (invalid value: got: {actual_type} [value: {actual_value!r}])")
            else:
                messages.append(str(err))
        model_name = getattr(model_cls, "__name__", str(model_cls))
        if error_types == {"missing"}:
            prefix = "Missing required arguments"
        elif error_types == {"invalid"}:
            prefix = "Invalid arguments"
        else:
            prefix = "Invalid or missing arguments"
        return f"Error in '{model_name}': {prefix}: {', '.join(messages)}. Refer to the documentation: https://trustwiseai.github.io/trustwise"

    def _get_field_description(self, field_name: str, field_info: object | None = None) -> str:
        """Get the description for a field from its field info."""
        if field_info and hasattr(field_info, "description") and field_info.description:
            return field_info.description
        return "No description available"

    def _format_output(self, indent: int = 0) -> str:
        """
        Format the model's output with proper indentation and descriptions.
        Used by both __repr__ and __str__ to ensure consistent output.
        """
        # Get all fields and their values
        fields = self.model_dump()
        
        # Check for dynamic _metadata attribute and include it if present
        if hasattr(self, "_metadata") and self._metadata is not None:
            fields["metadata"] = self._metadata
        
        # Start with the class name
        class_name = self.__class__.__name__
        prefix = " " * indent if indent > 0 else ""
        
        # Build the representation string
        lines = [f"{prefix}{class_name}:"]
        
        # Add each field and its value with explanation
        for field, value in fields.items():
            # Get field info from model
            field_info = self.model_fields.get(field)
            description = self._get_field_description(field, field_info)
            
            # Handle different types of values
            if isinstance(value, list):
                lines.append(f"{prefix}  {field}:")
                lines.append(f"{prefix}    Description: {description}")
                
                if value:  # Only process non-empty lists
                    # Get the expected type of list items if available
                    item_type = None
                    if field_info and hasattr(field_info.annotation, "__args__"):
                        item_type = field_info.annotation.__args__[0]
                    
                    # Process each item
                    if all(isinstance(x, int | float | str | bool) for x in value):
                        # For lists of simple values, print each on its own line without extra spacing
                        for item in value:
                            lines.append(f"{prefix}      - {item}")
                    else:
                        # For lists of complex objects, print each on its own line
                        for item in value:
                            if isinstance(item, SDKBaseModel):
                                # For nested model instances
                                item_lines = item._format_output(indent + 4)
                                lines.extend(item_lines.split("\n"))
                            elif isinstance(item, dict):
                                # For dictionaries, try to get the model class if available
                                model_class = item_type if isinstance(item_type, type) else None
                                item_lines = self._format_nested_dict(item, model_class, indent + 4)
                                lines.extend(item_lines)
                            else:
                                # For other values
                                lines.append(f"{prefix}    - {item}")
                            
                            if item != value[-1]:  # Add space between complex items except for the last one
                                lines.append("")
            elif isinstance(value, SDKBaseModel):
                # For nested models
                lines.append(f"{prefix}  {field}:")
                lines.append(f"{prefix}    Description: {description}")
                nested_lines = value._format_output(indent + 4)
                lines.extend(nested_lines.split("\n"))
            elif isinstance(value, dict):
                # For dictionaries
                lines.append(f"{prefix}  {field}:")
                lines.append(f"{prefix}    Description: {description}")
                # Try to get the model class if available
                field_type = field_info.annotation if field_info else None
                model_class = field_type if isinstance(field_type, type) else None
                if model_class and hasattr(model_class, "model_fields"):
                    # If we have a model class with field descriptions, use those
                    for k, v in value.items():
                        field_info = model_class.model_fields.get(k)
                        if field_info:
                            field_desc = self._get_field_description(k, field_info)
                            lines.append(f"{prefix}    {k}: {v}")
                            lines.append(f"{prefix}      Description: {field_desc}")
                else:
                    # Otherwise use the default nested dict formatting
                    nested_lines = self._format_nested_dict(value, model_class, indent + 4)
                    lines.extend(nested_lines)
            else:
                # For simple values
                lines.append(f"{prefix}  {field}: {value}")
                lines.append(f"{prefix}    Description: {description}")
        
        return "\n".join(lines)

    def _format_nested_dict(self, data: dict, model_class: type | None = None, indent: int = 0) -> list[str]:
        """
        Format a nested dictionary with field descriptions.
        If model_class is provided, it will be used to look up field descriptions.
        """
        lines = []
        prefix = " " * indent

        for field, value in data.items():
            # Try to get field info from the model class
            field_info = model_class.model_fields.get(field) if model_class else None
            description = self._get_field_description(field, field_info)

            if isinstance(value, dict):
                # For nested dictionaries
                lines.append(f"{prefix}{field}:")
                lines.append(f"{prefix}  Description: {description}")
                # Try to get the model class for nested dict if available
                nested_model = field_info.annotation if field_info and isinstance(field_info.annotation, type) else None
                nested_lines = self._format_nested_dict(value, nested_model, indent + 2)
                lines.extend(nested_lines)
            elif isinstance(value, list):
                lines.append(f"{prefix}{field}:")
                lines.append(f"{prefix}  Description: {description}")
                
                if value:  # Only process non-empty lists
                    # Try to get the expected type of list items
                    item_type = None
                    if field_info and hasattr(field_info.annotation, "__args__"):
                        item_type = field_info.annotation.__args__[0]
                    
                    # Process each item
                    if all(isinstance(x, int | float | str | bool) for x in value):
                        # For lists of simple values, print each on its own line without extra spacing
                        for item in value:
                            lines.append(f"{prefix}      - {item}")
                    else:
                        # For lists of complex objects, print each on its own line
                        for item in value:
                            if isinstance(item, dict):
                                # For dictionaries in lists
                                model_class = item_type if isinstance(item_type, type) else None
                                item_lines = self._format_nested_dict(item, model_class, indent + 4)
                                lines.extend(item_lines)
                            else:
                                # For simple values in lists
                                lines.append(f"{prefix}    - {item}")
                            
                            if item != value[-1] and not isinstance(item, int | float | str | bool):
                                # Add space between complex items except for the last one
                                lines.append("")
            else:
                # For simple values
                lines.append(f"{prefix}{field}: {value}")
                lines.append(f"{prefix}  Description: {description}")

        return lines

    def __repr__(self) -> str:
        """Return a detailed string representation."""
        return self._format_output()

    def _format_json_value(self, value: object) -> str:
        """Format a value for JSON display with syntax highlighting."""
        if isinstance(value, int | float | str | bool | type(None)):
            return json.dumps(value)
        elif isinstance(value, list | tuple):
            return f"[{', '.join(self._format_json_value(v) for v in value)}]"
        elif isinstance(value, dict):
            return f"{{{', '.join(f'{self._format_json_value(k)}: {self._format_json_value(v)}' for k, v in value.items())}}}"
        else:
            return str(value)

    def _repr_mimebundle_(self, include: object | None = None, exclude: object | None = None) -> dict[str, str]:
        """
        Return multiple representations of the object.
        This is the preferred way to provide multiple representations in Jupyter.
        """
        data = {
            "text/plain": str(self),
            "text/html": self._format_html()
        }
        return data, {}

    def _format_html(self, indent_level: int = 0) -> str:
        """
        Format the model's output as HTML with proper styling.
        Used by __repr_html__ to create a pretty representation in Jupyter notebooks.
        """
        # Define CSS styles
        styles = """
        <style>
            .tw-container { 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                padding: 12px;
                border: 1px solid #e1e4e8;
                border-radius: 6px;
                background: white;
            }
            .tw-title { 
                font-weight: bold;
                font-size: 1.1em;
                color: #2c3e50;
                margin-bottom: 12px;
                padding: 8px;
                background: #f6f8fa;
                border-radius: 4px;
            }
            .tw-field { 
                margin-left: 20px;
                margin-bottom: 16px;
                padding: 8px;
                border-left: 2px solid #e1e4e8;
            }
            .tw-field-name { 
                color: #0366d6;
                font-weight: 600;
                font-size: 1.0em;
            }
            .tw-description { 
                color: #586069;
                font-style: italic;
                font-size: 0.9em;
                margin-top: 4px;
                padding: 4px 0;
            }
            .tw-value { 
                margin-top: 6px;
                color: #24292e;
            }
            .tw-list-item { 
                margin-left: 24px;
                margin-top: 4px;
                display: flex;
                align-items: baseline;
            }
            .tw-nested { 
                margin-left: 20px;
                margin-top: 8px;
                padding-left: 12px;
                border-left: 1px solid #e1e4e8;
            }
            .tw-bullet { 
                color: #0366d6;
                margin-right: 8px;
            }
            .tw-value-number { 
                font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
                color: #005cc5;
            }
            .tw-value-string { 
                color: #24292e;
            }
            .tw-value-boolean { 
                color: #005cc5;
                font-weight: 600;
            }
        </style>
        """

        # Get all fields and their values
        fields = self.model_dump()
        
        # Check for dynamic _metadata attribute and include it if present
        if hasattr(self, "_metadata") and self._metadata is not None:
            fields["metadata"] = self._metadata
        
        # Start with container and class name
        html = [
            styles,
            '<div class="tw-container">',
            f'<div class="tw-title">{self.__class__.__name__}</div>'
        ]

        # Add each field and its value with explanation
        for field, value in fields.items():
            field_info = self.model_fields.get(field)
            description = self._get_field_description(field, field_info)
            
            html.append('<div class="tw-field">')
            html.append(f'<span class="tw-field-name">{field}</span>')
            html.append(f'<div class="tw-description">{description}</div>')
            
            # Handle different types of values
            if isinstance(value, list):
                html.append('<div class="tw-value">')
                if value:  # Only process non-empty lists
                    # Get the expected type of list items if available
                    item_type = None
                    if field_info and hasattr(field_info.annotation, "__args__"):
                        item_type = field_info.annotation.__args__[0]
                    
                    if all(isinstance(x, int | float | str | bool) for x in value):
                        # For lists of simple values
                        for item in value:
                            css_class = self._get_value_css_class(item)
                            html.append(f'<div class="tw-list-item"><span class="tw-bullet">•</span> <span class="{css_class}">{item}</span></div>')
                    else:
                        # For lists of complex objects
                        for item in value:
                            if isinstance(item, SDKBaseModel):
                                html.append('<div class="tw-nested">')
                                html.append(item._format_html(indent_level + 1))
                                html.append("</div>")
                            elif isinstance(item, dict):
                                html.append('<div class="tw-nested">')
                                # If we have a model class for list items, use it
                                if item_type and hasattr(item_type, "model_fields"):
                                    # Create a temporary instance of the model type
                                    temp_instance = item_type(**item)
                                    html.append(temp_instance._format_html(indent_level + 1))
                                else:
                                    html.append(self._format_dict_html(item, indent_level + 1))
                                html.append("</div>")
                            else:
                                css_class = self._get_value_css_class(item)
                                html.append(f'<div class="tw-list-item"><span class="tw-bullet">•</span> <span class="{css_class}">{item}</span></div>')
                html.append("</div>")
            elif isinstance(value, SDKBaseModel):
                html.append('<div class="tw-nested">')
                html.append(value._format_html(indent_level + 1))
                html.append("</div>")
            elif isinstance(value, dict):
                html.append('<div class="tw-nested">')
                # Try to get the model class for the dict if available
                dict_type = field_info.annotation if field_info else None
                if dict_type and hasattr(dict_type, "model_fields"):
                    # Create a temporary instance of the model type
                    temp_instance = dict_type(**value)
                    html.append(temp_instance._format_html(indent_level + 1))
                else:
                    html.append(self._format_dict_html(value, indent_level + 1))
                html.append("</div>")
            else:
                css_class = self._get_value_css_class(value)
                html.append(f'<div class="tw-value"><span class="{css_class}">{value}</span></div>')
            
            html.append("</div>")
        
        html.append("</div>")
        return "\n".join(html)

    def _get_value_css_class(self, value: object) -> str:
        """Return the appropriate CSS class for a value based on its type."""
        if isinstance(value, int | float):
            return "tw-value-number"
        elif isinstance(value, bool):
            return "tw-value-boolean"
        else:
            return "tw-value-string"

    def _format_dict_html(self, data: dict, indent_level: int = 0) -> str:
        """Format a dictionary as HTML with proper styling and field descriptions."""
        lines = []
        
        # Try to get the model class for the current dictionary
        model_class = None
        if hasattr(self, "model_fields"):
            for field_name, field_info in self.model_fields.items():
                field_value = getattr(self, field_name, None)
                if field_value == data:
                    # If this field's value matches our data dict, get its type
                    if hasattr(field_info.annotation, "__origin__") and field_info.annotation.__origin__ is list:
                        # For list types, get the item type
                        model_class = field_info.annotation.__args__[0]
                    else:
                        # For direct types
                        model_class = field_info.annotation
                    break

        for field, value in data.items():
            # Try to get field info and description from model class
            field_info = model_class.model_fields.get(field) if model_class and hasattr(model_class, "model_fields") else None
            description = self._get_field_description(field, field_info)
            
            # Start field div
            lines.append('<div class="tw-field">')
            lines.append(f'<span class="tw-field-name">{field}</span>')
            lines.append(f'<div class="tw-description">{description}</div>')
            lines.append('<div class="tw-value">')
            
            if isinstance(value, dict):
                # For nested dictionaries
                lines.append('<div class="tw-nested">')
                # Try to get the model class for nested dict if available
                nested_model = field_info.annotation if field_info else None
                if nested_model and hasattr(nested_model, "model_fields"):
                    # If we have a model class with field descriptions, use those
                    for k, v in value.items():
                        nested_field_info = nested_model.model_fields.get(k)
                        nested_desc = self._get_field_description(k, nested_field_info)
                        lines.append('<div class="tw-field">')
                        lines.append(f'<span class="tw-field-name">{k}</span>')
                        lines.append(f'<div class="tw-description">{nested_desc}</div>')
                        lines.append('<div class="tw-value">')
                        if isinstance(v, int | float):
                            lines.append(f'<span class="tw-value-number">{v}</span>')
                        elif isinstance(v, bool):
                            lines.append(f'<span class="tw-value-boolean">{str(v).lower()}</span>')
                        elif isinstance(v, str):
                            lines.append(f'<span class="tw-value-string">{v}</span>')
                        else:
                            lines.append(str(v))
                        lines.append("</div>")
                        lines.append("</div>")
                else:
                    # Otherwise use default dict formatting
                    lines.extend(self._format_dict_html(value, indent_level + 1).split("\n"))
                lines.append("</div>")
            elif isinstance(value, list):
                if all(isinstance(x, int | float | str | bool) for x in value):
                    # For lists of simple values
                    for item in value:
                        lines.append('<div class="tw-list-item">')
                        lines.append('<span class="tw-bullet">•</span>')
                        if isinstance(item, int | float):
                            lines.append(f'<span class="tw-value-number">{item}</span>')
                        elif isinstance(item, bool):
                            lines.append(f'<span class="tw-value-boolean">{str(item).lower()}</span>')
                        elif isinstance(item, str):
                            lines.append(f'<span class="tw-value-string">{item}</span>')
                        else:
                            lines.append(str(item))
                        lines.append("</div>")
                else:
                    # For lists of complex objects
                    for item in value:
                        if isinstance(item, dict):
                            lines.append('<div class="tw-nested">')
                            # Try to get the model class for list items if available
                            item_type = None
                            if field_info and hasattr(field_info.annotation, "__args__"):
                                item_type = field_info.annotation.__args__[0]
                            if item_type and hasattr(item_type, "model_fields"):
                                # If we have a model class with field descriptions, use those
                                for k, v in item.items():
                                    nested_field_info = item_type.model_fields.get(k)
                                    nested_desc = self._get_field_description(k, nested_field_info)
                                    lines.append('<div class="tw-field">')
                                    lines.append(f'<span class="tw-field-name">{k}</span>')
                                    lines.append(f'<div class="tw-description">{nested_desc}</div>')
                                    lines.append('<div class="tw-value">')
                                    if isinstance(v, int | float):
                                        lines.append(f'<span class="tw-value-number">{v}</span>')
                                    elif isinstance(v, bool):
                                        lines.append(f'<span class="tw-value-boolean">{str(v).lower()}</span>')
                                    elif isinstance(v, str):
                                        lines.append(f'<span class="tw-value-string">{v}</span>')
                                    else:
                                        lines.append(str(v))
                                    lines.append("</div>")
                                    lines.append("</div>")
                            else:
                                lines.extend(self._format_dict_html(item, indent_level + 1).split("\n"))
                            lines.append("</div>")
                        else:
                            lines.append('<div class="tw-list-item">')
                            lines.append('<span class="tw-bullet">•</span>')
                            lines.append(str(item))
                            lines.append("</div>")
            else:
                # For simple values
                if isinstance(value, int | float):
                    lines.append(f'<span class="tw-value-number">{value}</span>')
                elif isinstance(value, bool):
                    lines.append(f'<span class="tw-value-boolean">{str(value).lower()}</span>')
                elif isinstance(value, str):
                    lines.append(f'<span class="tw-value-string">{value}</span>')
                else:
                    lines.append(str(value))
            
            lines.append("</div>")
            lines.append("</div>")
        
        return "\n".join(lines)

    def __repr_html__(self) -> str:
        """Return an HTML representation for Jupyter notebooks."""
        return self._format_html()


class SDKRequestModel(SDKBaseModel):
    """Base model for all SDK request types."""
    metadata: dict[str, object] | None = Field(
        default=None,
        description="Optional metadata for the request that will be included in the response."
    )


class SDKResponseModel(SDKBaseModel):
    """Base model for all SDK response types."""
    # No metadata field - it will be attached as _metadata by the BaseMetric._parse_response method
    pass




@sphinx_autodoc
class CostResponseV3(SDKResponseModel):
    """
    Response type for cost evaluation.
    """
    cost_estimate_per_run: float = Field(..., description="Represents the expense for each individual LLM call. This is the cost of the model call, including the prompt and response tokens.")
    total_project_cost_estimate: float = Field(..., description="Cumulative cost for 10,000 LLM calls to help estimate costs over high-volume usage patterns.")



@sphinx_autodoc
class CostRequestV3(SDKRequestModel):
    """
    Request type for cost evaluation.
    """
    model_name: constr(strip_whitespace=True, min_length=1) = Field(..., description="Model name must be a non-empty string.")
    model_type: Literal["LLM", "Reranker"] = Field(..., description="Model type must be 'LLM' or 'Reranker'.")
    model_provider: constr(strip_whitespace=True, min_length=1) = Field(..., description="Model provider must be a non-empty string. Should be one of ['openai', 'togetherai', 'huggingface', 'nvidia', 'azure']")
    number_of_queries: PositiveInt = Field(..., description="Number of queries must be > 0.")
    total_prompt_tokens: PositiveInt = Field(..., description="(Optional)Total number of prompt tokens (must be > 0).")
    total_completion_tokens: PositiveInt = Field(..., description="(Optional)Total number of completion tokens (must be > 0).")
    total_tokens: PositiveInt | None = Field(None, description="(Optional) Total tokens (optional, must be > 0 if provided).")
    instance_type: str | None = Field(None, description="(Optional) Instance type required for Hugging Face models.")
    average_latency: PositiveFloat | None = Field(None, description="(Optional) Average latency in milliseconds, must be > 0 if provided.")


@sphinx_autodoc
class GuardrailResponse(SDKResponseModel):
    """
    Response type for guardrail evaluation. 
    """
    passed: bool = Field(..., description="Whether all metrics passed.")
    blocked: bool = Field(..., description="Whether the response is blocked due to failure.")
    results: dict = Field(..., description="Dictionary of metric results, each containing 'passed' and 'result'.")

    def to_json(self, **kwargs: dict[str, object]) -> str:
        """
        Return a JSON string representation of the guardrail evaluation, recursively serializing all nested SDK types.
        Use this for logging, API responses, or storage.
        """
        def serialize(obj: object) -> object:
            if hasattr(obj, "to_json"):
                return obj.model_dump()
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize(i) for i in obj]
            return obj
        data = {
            "passed": self.passed,
            "blocked": self.blocked,
            "results": serialize(self.results)
        }
        return json.dumps(data, **kwargs)

    def to_dict(self) -> dict:
        """
        Return a Python dict representation of the guardrail evaluation, recursively serializing all nested SDK types.
        Use this for programmatic access, further processing, or conversion to JSON via json.dumps().
        """
        def serialize(obj: object) -> object:
            if hasattr(obj, "to_json"):
                return obj.model_dump()
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize(i) for i in obj]
            return obj
        return {
            "passed": self.passed,
            "blocked": self.blocked,
            "results": serialize(self.results)
        }

