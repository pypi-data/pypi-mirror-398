from dyngle.error import DyngleError


class Interface:
    """Validates and processes data against a custom interface definition.
    
    The interface always defines properties of a root object. It validates
    data types, enforces required fields, and applies default values.
    """

    TYPE_VALIDATORS = {
        "string": lambda v: isinstance(v, str),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "boolean": lambda v: isinstance(v, bool),
        "array": lambda v: isinstance(v, list),
        "object": lambda v: isinstance(v, dict),
    }

    def __init__(self, definition: dict):
        """Initialize with interface definition (properties dict)."""
        self.definition = definition or {}
        self._validate_schema(self.definition)

    def _validate_schema(self, schema: dict, path: str = ""):
        """Validate that the schema definition itself is valid."""
        if not isinstance(schema, dict):
            raise DyngleError(
                f"Invalid schema at {path or 'root'}: must be dict"
            )
        
        for field_name, field_def in schema.items():
            field_path = f"{path}.{field_name}" if path else field_name
            
            if field_def is None:
                # None is valid - means use all defaults
                continue
            
            if not isinstance(field_def, dict):
                raise DyngleError(
                    f"Invalid field definition at {field_path}: "
                    f"must be dict or None"
                )
            
            # Validate type if present
            if "type" in field_def:
                valid_types = [
                    "string", "number", "integer", 
                    "boolean", "array", "object"
                ]
                if field_def["type"] not in valid_types:
                    raise DyngleError(
                        f"Invalid type at {field_path}: "
                        f"must be one of {', '.join(valid_types)}"
                    )
            
            # Recursively validate nested properties
            if "properties" in field_def:
                if not isinstance(field_def["properties"], dict):
                    raise DyngleError(
                        f"Invalid properties at {field_path}: must be dict"
                    )
                self._validate_schema(
                    field_def["properties"], 
                    field_path
                )
            
            # Validate items if present
            if "items" in field_def:
                if not isinstance(field_def["items"], dict):
                    raise DyngleError(
                        f"Invalid items at {field_path}: must be dict"
                    )
                # Recursively validate the items schema
                items_path = f"{field_path}[items]"
                self._validate_schema({"_": field_def["items"]}, items_path)

    def process(self, data: dict):
        """Validate data and apply defaults (mutates data in place)."""
        self._process_object(data, self.definition, "")

    def _infer_type(self, field_def: dict | None) -> str:
        """Infer type from field definition using precedence rules."""
        if field_def is None:
            return "string"
        
        if "type" in field_def:
            return field_def["type"]
        if "properties" in field_def:
            return "object"
        if "items" in field_def:
            return "array"
        return "string"

    def to_json_schema(self) -> dict:
        """Convert interface definition to JSON Schema format.
        
        This ensures all fields have proper 'type' attributes, inferring
        types for fields without explicit types (None or {}).
        """
        properties = {}
        for field_name, field_def in self.definition.items():
            properties[field_name] = self._field_to_json_schema(field_def)
        return properties

    def get_required_fields(self) -> list[str]:
        """Get list of required field names for MCP schema.
        
        Uses the same logic as runtime default handling to ensure
        MCP schema matches actual behavior (DRY).
        """
        required = []
        for field_name, field_def in self.definition.items():
            field_type = self._infer_type(field_def)
            has_default, _ = self._get_default_for_type(field_def, field_type)
            
            # Field is required if:
            # - No default AND
            # - required is not explicitly False
            if not has_default:
                if field_def is None or field_def.get("required", True):
                    required.append(field_name)
        return required

    def _field_to_json_schema(self, field_def: dict | None) -> dict:
        """Convert a single field definition to JSON Schema format."""
        field_type = self._infer_type(field_def)
        
        # Start with the inferred type
        schema = {"type": field_type}
        
        # If field_def is None or empty, just return the type
        if not field_def:
            return schema
        
        # Copy over other JSON Schema properties
        for key, value in field_def.items():
            if key == "properties" and field_type == "object":
                # Recursively convert nested properties
                schema["properties"] = {}
                for prop_name, prop_def in value.items():
                    schema["properties"][prop_name] = \
                        self._field_to_json_schema(prop_def)
            elif key == "items" and field_type == "array":
                # Recursively convert array items
                schema["items"] = self._field_to_json_schema(value)
            elif key != "type":  # Don't duplicate the type key
                schema[key] = value
        
        return schema

    def _get_default_for_type(
        self, field_def: dict | None, field_type: str
    ):
        """Get default value for a field based on its type.
        
        Returns (has_default, default_value) tuple.
        Strings without explicit required/default get blank string.
        """
        if field_def is None:
            # No definition = string with blank default
            return (True, "")
        
        if "default" in field_def:
            return (True, field_def["default"])
        
        # String types without explicit required get blank default
        if field_type == "string" and "required" not in field_def:
            return (True, "")
        
        return (False, None)

    def _process_object(self, data: dict, schema: dict, path: str):
        """Process object data against schema."""
        for field_name, field_def in schema.items():
            field_path = f"{path}.{field_name}" if path else field_name
            field_type = self._infer_type(field_def)
            
            if field_name not in data:
                # Field is missing - check for default or required
                has_default, default_val = self._get_default_for_type(
                    field_def, field_type
                )
                
                if has_default:
                    data[field_name] = default_val
                elif field_def is None or field_def.get("required", True):
                    raise DyngleError(
                        f"Field '{field_name}' is required at "
                        f"{path or 'root'}"
                    )
                continue
            
            # Field exists, validate its type and process
            self._validate_and_process_value(
                data[field_name], 
                field_def, 
                field_type, 
                field_path,
                data,
                field_name
            )

    def _validate_and_process_value(
        self, 
        value, 
        field_def: dict | None, 
        expected_type: str, 
        path: str,
        parent_data: dict = None,
        field_name: str = None
    ):
        """Validate value type and recursively process if needed."""
        # Validate type using TYPE_VALIDATORS mapping
        validator = self.TYPE_VALIDATORS.get(expected_type)
        if validator and not validator(value):
            raise DyngleError(
                f"Field '{path}' must be {expected_type}, got "
                f"{type(value).__name__}"
            )
        
        # Handle recursive processing for complex types
        if expected_type == "array" and field_def and "items" in field_def:
            items_def = field_def["items"]
            items_type = self._infer_type(items_def)
            for i, item in enumerate(value):
                item_path = f"{path}[{i}]"
                self._validate_and_process_value(
                    item, items_def, items_type, item_path
                )
        elif expected_type == "object" and field_def and "properties" in field_def:
            self._process_object(value, field_def["properties"], path)
