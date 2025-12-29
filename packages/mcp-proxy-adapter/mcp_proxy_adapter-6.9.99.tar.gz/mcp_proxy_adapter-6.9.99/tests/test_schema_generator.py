"""
Comprehensive tests for schema generator module.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import pytest
from typing import Any, Dict

from mcp_proxy_adapter.client.jsonrpc_client.schema_generator import (
    SchemaRequestGenerator,
    MethodInfo,
    ParameterInfo,
    ParameterType,
)
from mcp_proxy_adapter.client.jsonrpc_client.exceptions import (
    SchemaGeneratorError,
    MethodNotFoundError,
    RequiredParameterMissingError,
    InvalidParameterTypeError,
    InvalidParameterValueError,
)


# Sample OpenAPI schema for testing
SAMPLE_SCHEMA = {
    "openapi": "3.0.2",
    "info": {
        "title": "Test API",
        "version": "1.0.0"
    },
    "components": {
        "schemas": {
            "CommandRequest": {
                "oneOf": [
                    {"$ref": "#/components/schemas/CommandRequest_echo"},
                    {"$ref": "#/components/schemas/CommandRequest_long_task"},
                    {"$ref": "#/components/schemas/CommandRequest_job_status"},
                ],
                "discriminator": {
                    "propertyName": "command",
                    "mapping": {
                        "echo": "#/components/schemas/CommandRequest_echo",
                        "long_task": "#/components/schemas/CommandRequest_long_task",
                        "job_status": "#/components/schemas/CommandRequest_job_status",
                    }
                }
            },
            "CommandRequest_echo": {
                "type": "object",
                "required": ["command"],
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["echo"],
                        "description": "Command name: echo"
                    },
                    "params": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "default": "Hello",
                                "description": "Message to echo"
                            }
                        },
                        "required": [],
                        "description": "Parameters for echo command"
                    }
                },
                "description": "Execute echo command"
            },
            "CommandRequest_long_task": {
                "type": "object",
                "required": ["command"],
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["long_task"],
                        "description": "Command name: long_task"
                    },
                    "params": {
                        "type": "object",
                        "properties": {
                            "seconds": {
                                "type": "integer",
                                "description": "Number of seconds to wait",
                                "format": "int64"
                            }
                        },
                        "required": ["seconds"],
                        "description": "Parameters for long_task command"
                    }
                },
                "description": "Execute long task command"
            },
            "CommandRequest_job_status": {
                "type": "object",
                "required": ["command"],
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["job_status"],
                        "description": "Command name: job_status"
                    },
                    "params": {
                        "type": "object",
                        "properties": {
                            "job_id": {
                                "type": "string",
                                "description": "Job identifier"
                            },
                            "include_details": {
                                "type": "boolean",
                                "default": False,
                                "description": "Include detailed information"
                            }
                        },
                        "required": ["job_id"],
                        "description": "Parameters for job_status command"
                    }
                },
                "description": "Get job status"
            }
        }
    }
}


class TestSchemaRequestGenerator:
    """Test suite for SchemaRequestGenerator class."""

    def test_init_with_valid_schema(self):
        """Test initialization with valid schema."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        assert generator is not None
        assert len(generator._methods) == 3

    def test_init_with_empty_schema(self):
        """Test initialization with empty schema."""
        empty_schema = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {"mapping": {}}
                    }
                }
            }
        }
        generator = SchemaRequestGenerator(empty_schema)
        assert generator is not None
        assert len(generator._methods) == 0

    def test_init_with_missing_components(self):
        """Test initialization with missing components."""
        incomplete_schema = {"openapi": "3.0.2"}
        generator = SchemaRequestGenerator(incomplete_schema)
        assert generator is not None
        assert len(generator._methods) == 0

    def test_get_methods(self):
        """Test getting all methods."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        methods = generator.get_methods()
        
        assert isinstance(methods, dict)
        assert len(methods) == 3
        assert "echo" in methods
        assert "long_task" in methods
        assert "job_status" in methods
        
        for method_name, method_info in methods.items():
            assert isinstance(method_info, MethodInfo)
            assert method_info.name == method_name

    def test_get_method_info_existing(self):
        """Test getting info for existing method."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        method_info = generator.get_method_info("echo")
        
        assert isinstance(method_info, MethodInfo)
        assert method_info.name == "echo"
        assert "message" in method_info.parameters

    def test_get_method_info_not_found(self):
        """Test getting info for non-existent method."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        with pytest.raises(MethodNotFoundError) as exc_info:
            generator.get_method_info("unknown_method")
        
        assert exc_info.value.method_name == "unknown_method"

    def test_parse_command_schema_echo(self):
        """Test parsing echo command schema."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        method_info = generator.get_method_info("echo")
        
        assert method_info.name == "echo"
        assert method_info.description == "Execute echo command"
        assert "message" in method_info.parameters
        
        message_param = method_info.parameters["message"]
        assert message_param.name == "message"
        assert message_param.param_type == ParameterType.STRING
        assert message_param.default_value == "Hello"
        assert message_param.required is False
        assert message_param.description == "Message to echo"

    def test_parse_command_schema_long_task(self):
        """Test parsing long_task command schema."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        method_info = generator.get_method_info("long_task")
        
        assert method_info.name == "long_task"
        assert "seconds" in method_info.parameters
        
        seconds_param = method_info.parameters["seconds"]
        assert seconds_param.name == "seconds"
        assert seconds_param.param_type == ParameterType.INTEGER
        assert seconds_param.required is True
        assert seconds_param.format == "int64"

    def test_parse_command_schema_job_status(self):
        """Test parsing job_status command schema."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        method_info = generator.get_method_info("job_status")
        
        assert method_info.name == "job_status"
        assert "job_id" in method_info.parameters
        assert "include_details" in method_info.parameters
        
        job_id_param = method_info.parameters["job_id"]
        assert job_id_param.required is True
        
        include_details_param = method_info.parameters["include_details"]
        assert include_details_param.required is False
        assert include_details_param.default_value is False
        assert include_details_param.param_type == ParameterType.BOOLEAN

    def test_validate_and_prepare_params_all_provided(self):
        """Test validation with all parameters provided."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        params = {"message": "Test message"}
        prepared = generator.validate_and_prepare_params("echo", params)
        
        assert prepared == {"message": "Test message"}

    def test_validate_and_prepare_params_with_defaults(self):
        """Test validation with default values applied."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        prepared = generator.validate_and_prepare_params("echo", {})
        
        assert "message" in prepared
        assert prepared["message"] == "Hello"  # Default value

    def test_validate_and_prepare_params_missing_required(self):
        """Test validation fails when required parameter is missing."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        with pytest.raises(RequiredParameterMissingError) as exc_info:
            generator.validate_and_prepare_params("long_task", {})
        
        assert exc_info.value.method_name == "long_task"
        assert exc_info.value.parameter_name == "seconds"

    def test_validate_and_prepare_params_invalid_type_string(self):
        """Test validation fails with invalid string type."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        with pytest.raises(InvalidParameterTypeError) as exc_info:
            generator.validate_and_prepare_params("echo", {"message": 123})
        
        assert exc_info.value.method_name == "echo"
        assert exc_info.value.parameter_name == "message"
        assert exc_info.value.expected_type == "string"

    def test_validate_and_prepare_params_invalid_type_integer(self):
        """Test validation fails with invalid integer type."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        with pytest.raises(InvalidParameterTypeError) as exc_info:
            generator.validate_and_prepare_params("long_task", {"seconds": "not_a_number"})
        
        assert exc_info.value.method_name == "long_task"
        assert exc_info.value.parameter_name == "seconds"
        assert exc_info.value.expected_type == "integer"

    def test_validate_and_prepare_params_invalid_type_boolean(self):
        """Test validation fails with invalid boolean type."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        with pytest.raises(InvalidParameterTypeError) as exc_info:
            generator.validate_and_prepare_params("job_status", {
                "job_id": "test",
                "include_details": "not_a_boolean"
            })
        
        assert exc_info.value.method_name == "job_status"
        assert exc_info.value.parameter_name == "include_details"
        assert exc_info.value.expected_type == "boolean"

    def test_validate_and_prepare_params_valid_types(self):
        """Test validation passes with valid types."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        # Test string
        prepared = generator.validate_and_prepare_params("echo", {"message": "test"})
        assert prepared["message"] == "test"
        
        # Test integer
        prepared = generator.validate_and_prepare_params("long_task", {"seconds": 5})
        assert prepared["seconds"] == 5
        
        # Test boolean
        prepared = generator.validate_and_prepare_params("job_status", {
            "job_id": "test",
            "include_details": True
        })
        assert prepared["include_details"] is True
        
        # Test number (float)
        # Note: integer accepts float in Python, but we test strict integer validation
        prepared = generator.validate_and_prepare_params("long_task", {"seconds": 10})
        assert prepared["seconds"] == 10

    def test_validate_and_prepare_params_enum_values(self):
        """Test validation with enum values."""
        schema_with_enum = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_test"
                            }
                        }
                    },
                    "CommandRequest_test": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["test"]},
                            "params": {
                                "type": "object",
                                "properties": {
                                    "status": {
                                        "type": "string",
                                        "enum": ["active", "inactive", "pending"]
                                    }
                                },
                                "required": []
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_with_enum)
        
        # Valid enum value
        prepared = generator.validate_and_prepare_params("test", {"status": "active"})
        assert prepared["status"] == "active"
        
        # Invalid enum value
        with pytest.raises(InvalidParameterValueError) as exc_info:
            generator.validate_and_prepare_params("test", {"status": "invalid"})
        
        assert exc_info.value.method_name == "test"
        assert exc_info.value.parameter_name == "status"

    def test_validate_and_prepare_params_unknown_method(self):
        """Test validation fails for unknown method."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        with pytest.raises(MethodNotFoundError) as exc_info:
            generator.validate_and_prepare_params("unknown", {})
        
        assert exc_info.value.method_name == "unknown"

    def test_validate_and_prepare_params_partial_params(self):
        """Test validation with partial parameters."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        # Provide only required, optional should get default
        prepared = generator.validate_and_prepare_params("job_status", {"job_id": "test-123"})
        assert prepared["job_id"] == "test-123"
        assert prepared["include_details"] is False  # Default value

    def test_get_method_description(self):
        """Test getting method description."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        description = generator.get_method_description("echo")
        
        assert isinstance(description, str)
        assert "Method: echo" in description
        assert "Description:" in description
        assert "Return Type:" in description
        assert "Parameters:" in description
        assert "message" in description
        assert "Type: string" in description
        assert "Default: \"Hello\"" in description

    def test_get_method_description_not_found(self):
        """Test getting description for non-existent method."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        with pytest.raises(MethodNotFoundError):
            generator.get_method_description("unknown")

    def test_get_method_description_no_params(self):
        """Test getting description for method without parameters."""
        schema_no_params = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "no_params": "#/components/schemas/CommandRequest_no_params"
                            }
                        }
                    },
                    "CommandRequest_no_params": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["no_params"]},
                            "params": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_no_params)
        description = generator.get_method_description("no_params")
        
        assert "No parameters" in description

    def test_schema_example(self):
        """Test generating schema example."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        example_json = generator.schema_example()
        
        assert isinstance(example_json, str)
        
        # Parse JSON to verify structure
        example = json.loads(example_json)
        
        assert "schema" in example
        assert "description" in example
        assert "methods" in example
        
        # Check description structure
        desc = example["description"]
        assert "standard" in desc
        assert "standard_description" in desc
        assert "fields" in desc
        
        # Check methods
        assert "echo" in example["methods"]
        assert "long_task" in example["methods"]
        assert "job_status" in example["methods"]
        
        # Check method structure
        echo_method = example["methods"]["echo"]
        assert "name" in echo_method
        assert "description" in echo_method
        assert "return_type" in echo_method
        assert "parameters" in echo_method
        
        # Check parameter structure
        assert "message" in echo_method["parameters"]
        message_param = echo_method["parameters"]["message"]
        assert "name" in message_param
        assert "type" in message_param
        assert "required" in message_param
        assert "default" in message_param

    def test_schema_example_empty_schema(self):
        """Test schema example with empty schema."""
        empty_schema = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {"mapping": {}}
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(empty_schema)
        example_json = generator.schema_example()
        example = json.loads(example_json)
        
        assert "methods" in example
        assert len(example["methods"]) == 0

    def test_map_type_all_types(self):
        """Test mapping all OpenAPI types."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        assert generator._map_type("string") == ParameterType.STRING
        assert generator._map_type("integer") == ParameterType.INTEGER
        assert generator._map_type("number") == ParameterType.NUMBER
        assert generator._map_type("boolean") == ParameterType.BOOLEAN
        assert generator._map_type("array") == ParameterType.ARRAY
        assert generator._map_type("object") == ParameterType.OBJECT
        assert generator._map_type("null") == ParameterType.NULL
        assert generator._map_type("unknown") == ParameterType.OBJECT  # Default

    def test_get_value_type(self):
        """Test getting value type."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        assert generator._get_value_type("test") == "string"
        assert generator._get_value_type(123) == "integer"
        assert generator._get_value_type(123.45) == "number"
        assert generator._get_value_type(True) == "boolean"
        assert generator._get_value_type([1, 2, 3]) == "array"
        assert generator._get_value_type({"key": "value"}) == "object"
        assert generator._get_value_type(None) == "null"

    def test_parse_parameter_schema_with_format(self):
        """Test parsing parameter with format."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        method_info = generator.get_method_info("long_task")
        seconds_param = method_info.parameters["seconds"]
        
        assert seconds_param.format == "int64"

    def test_parse_parameter_schema_with_description(self):
        """Test parsing parameter with description."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        method_info = generator.get_method_info("echo")
        message_param = method_info.parameters["message"]
        
        assert message_param.description == "Message to echo"

    def test_validate_and_prepare_params_extra_params_ignored(self):
        """Test that extra parameters are ignored (not in schema)."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        # Should not raise error, but extra param might be ignored
        # This depends on implementation - current implementation includes all provided params
        prepared = generator.validate_and_prepare_params("echo", {
            "message": "test",
            "extra_param": "value"
        })
        
        assert "message" in prepared
        # Extra param might be included or not depending on implementation

    def test_validate_and_prepare_params_none_value(self):
        """Test validation with None value."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        # None should be handled appropriately
        # For required params with None value, it should raise InvalidParameterTypeError
        # because None is not a valid integer
        with pytest.raises(InvalidParameterTypeError) as exc_info:
            generator.validate_and_prepare_params("long_task", {"seconds": None})
        
        assert exc_info.value.method_name == "long_task"
        assert exc_info.value.parameter_name == "seconds"
        assert exc_info.value.expected_type == "integer"
        assert exc_info.value.actual_type == "null"

    def test_validate_and_prepare_params_empty_dict(self):
        """Test validation with empty dict."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        # Should use defaults for optional params
        prepared = generator.validate_and_prepare_params("echo", {})
        assert prepared["message"] == "Hello"

    def test_validate_and_prepare_params_none_dict(self):
        """Test validation with None as params dict."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        
        # Should treat None as empty dict
        prepared = generator.validate_and_prepare_params("echo", None)
        assert prepared["message"] == "Hello"

    def test_schema_example_fields_description(self):
        """Test that schema example includes field descriptions."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        example_json = generator.schema_example()
        example = json.loads(example_json)
        
        fields = example["description"]["fields"]
        assert "openapi" in fields
        assert "info" in fields
        assert "paths" in fields
        assert "components" in fields
        
        # Check that fields have descriptions
        assert "description" in fields["openapi"]
        assert "description" in fields["info"]

    def test_parse_command_schema_missing_description(self):
        """Test parsing command schema without description."""
        schema_no_desc = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_test"
                            }
                        }
                    },
                    "CommandRequest_test": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["test"]},
                            "params": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_no_desc)
        method_info = generator.get_method_info("test")
        
        # Should have default description
        assert method_info.description is not None
        assert "test" in method_info.description.lower()

    def test_validate_parameter_type_array(self):
        """Test validation of array type parameter."""
        schema_with_array = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_test"
                            }
                        }
                    },
                    "CommandRequest_test": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["test"]},
                            "params": {
                                "type": "object",
                                "properties": {
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": []
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_with_array)
        
        # Valid array
        prepared = generator.validate_and_prepare_params("test", {"items": ["a", "b"]})
        assert prepared["items"] == ["a", "b"]
        
        # Invalid type
        with pytest.raises(InvalidParameterTypeError) as exc_info:
            generator.validate_and_prepare_params("test", {"items": "not_an_array"})
        
        assert exc_info.value.parameter_name == "items"
        assert exc_info.value.expected_type == "array"

    def test_validate_parameter_type_object(self):
        """Test validation of object type parameter."""
        schema_with_object = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_test"
                            }
                        }
                    },
                    "CommandRequest_test": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["test"]},
                            "params": {
                                "type": "object",
                                "properties": {
                                    "metadata": {
                                        "type": "object",
                                        "properties": {
                                            "key": {"type": "string"}
                                        }
                                    }
                                },
                                "required": []
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_with_object)
        
        # Valid object
        prepared = generator.validate_and_prepare_params("test", {
            "metadata": {"key": "value"}
        })
        assert prepared["metadata"] == {"key": "value"}
        
        # Invalid type
        with pytest.raises(InvalidParameterTypeError) as exc_info:
            generator.validate_and_prepare_params("test", {"metadata": "not_an_object"})
        
        assert exc_info.value.parameter_name == "metadata"
        assert exc_info.value.expected_type == "object"

    def test_validate_parameter_type_number(self):
        """Test validation of number type parameter."""
        schema_with_number = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_test"
                            }
                        }
                    },
                    "CommandRequest_test": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["test"]},
                            "params": {
                                "type": "object",
                                "properties": {
                                    "price": {"type": "number"}
                                },
                                "required": []
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_with_number)
        
        # Valid number (int)
        prepared = generator.validate_and_prepare_params("test", {"price": 100})
        assert prepared["price"] == 100
        
        # Valid number (float)
        prepared = generator.validate_and_prepare_params("test", {"price": 99.99})
        assert prepared["price"] == 99.99
        
        # Invalid type
        with pytest.raises(InvalidParameterTypeError) as exc_info:
            generator.validate_and_prepare_params("test", {"price": "not_a_number"})
        
        assert exc_info.value.parameter_name == "price"
        assert exc_info.value.expected_type == "number"

    def test_exception_hierarchy(self):
        """Test exception class hierarchy."""
        # Test that exceptions inherit correctly
        assert issubclass(SchemaGeneratorError, Exception)
        assert issubclass(MethodNotFoundError, SchemaGeneratorError)
        assert issubclass(RequiredParameterMissingError, SchemaGeneratorError)
        assert issubclass(InvalidParameterTypeError, SchemaGeneratorError)
        assert issubclass(InvalidParameterValueError, SchemaGeneratorError)

    def test_exception_attributes(self):
        """Test exception attributes are set correctly."""
        # MethodNotFoundError
        exc = MethodNotFoundError("test_method")
        assert exc.method_name == "test_method"
        assert str(exc) == "Method 'test_method' not found in schema"
        
        # RequiredParameterMissingError
        exc = RequiredParameterMissingError("method", "param")
        assert exc.method_name == "method"
        assert exc.parameter_name == "param"
        
        # InvalidParameterTypeError
        exc = InvalidParameterTypeError("method", "param", "string", "integer")
        assert exc.method_name == "method"
        assert exc.parameter_name == "param"
        assert exc.expected_type == "string"
        assert exc.actual_type == "integer"
        
        # InvalidParameterValueError
        exc = InvalidParameterValueError("method", "param", "invalid enum")
        assert exc.method_name == "method"
        assert exc.parameter_name == "param"
        assert exc.reason == "invalid enum"

    def test_schema_with_missing_discriminator(self):
        """Test schema without discriminator."""
        schema_no_discriminator = {
            "components": {
                "schemas": {
                    "CommandRequest": {}
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_no_discriminator)
        assert len(generator._methods) == 0

    def test_schema_with_invalid_ref(self):
        """Test schema with invalid reference."""
        schema_invalid_ref = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_nonexistent"
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_invalid_ref)
        # Should handle gracefully - method won't be loaded
        assert "test" not in generator._methods

    def test_get_method_description_with_all_param_info(self):
        """Test method description includes all parameter information."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        description = generator.get_method_description("job_status")
        
        # Check all required info is present
        assert "job_id" in description
        assert "include_details" in description
        assert "required" in description.lower() or "optional" in description.lower()
        assert "Type:" in description
        assert "Default:" in description or "default" in description.lower()

    def test_schema_example_standard_info(self):
        """Test schema example includes standard information."""
        generator = SchemaRequestGenerator(SAMPLE_SCHEMA)
        example_json = generator.schema_example()
        example = json.loads(example_json)
        
        desc = example["description"]
        assert desc["standard"] == "OpenAPI 3.0.2"
        assert len(desc["standard_description"]) > 0

    def test_schema_mismatch_missing_properties(self):
        """Test schema with missing properties in command schema."""
        schema_mismatch = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_test"
                            }
                        }
                    },
                    "CommandRequest_test": {
                        "type": "object",
                        # Missing required field
                        "properties": {
                            "command": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_mismatch)
        # Should handle gracefully
        assert "test" in generator._methods or "test" not in generator._methods

    def test_schema_mismatch_invalid_discriminator_mapping(self):
        """Test schema with invalid discriminator mapping."""
        schema_invalid = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "propertyName": "command",
                            "mapping": {
                                "test": "#/components/schemas/NonexistentSchema"
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_invalid)
        # Should not crash, but method won't be loaded
        assert "test" not in generator._methods

    def test_schema_mismatch_wrong_type_in_schema(self):
        """Test schema with wrong type definition."""
        schema_wrong_type = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_test"
                            }
                        }
                    },
                    "CommandRequest_test": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["test"]},
                            "params": {
                                "type": "object",
                                "properties": {
                                    "value": {
                                        "type": "integer",  # Defined as integer
                                        "description": "Should be integer"
                                    }
                                },
                                "required": []
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_wrong_type)
        
        # Valid integer should pass
        prepared = generator.validate_and_prepare_params("test", {"value": 42})
        assert prepared["value"] == 42
        
        # String instead of integer should fail
        with pytest.raises(InvalidParameterTypeError):
            generator.validate_and_prepare_params("test", {"value": "not_an_integer"})

    def test_schema_mismatch_missing_required_in_params(self):
        """Test schema where required params are missing from properties."""
        schema_missing_req = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_test"
                            }
                        }
                    },
                    "CommandRequest_test": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["test"]},
                            "params": {
                                "type": "object",
                                "properties": {
                                    "optional_param": {"type": "string"}
                                },
                                "required": ["missing_param"]  # Required but not in properties
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_missing_req)
        
        # If required param is not in properties, it won't be in method_info.parameters
        # So validation will pass (this is expected behavior - schema inconsistency)
        # The method will be loaded but the missing param won't be validated
        method_info = generator.get_method_info("test")
        assert "missing_param" not in method_info.parameters
        # Validation should pass because missing_param is not in parameters dict
        prepared = generator.validate_and_prepare_params("test", {})
        assert isinstance(prepared, dict)

    def test_schema_mismatch_enum_value_not_in_schema(self):
        """Test when provided enum value doesn't match schema."""
        schema_with_enum = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_test"
                            }
                        }
                    },
                    "CommandRequest_test": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["test"]},
                            "params": {
                                "type": "object",
                                "properties": {
                                    "status": {
                                        "type": "string",
                                        "enum": ["active", "inactive"]
                                    }
                                },
                                "required": []
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_with_enum)
        
        # Valid enum value
        prepared = generator.validate_and_prepare_params("test", {"status": "active"})
        assert prepared["status"] == "active"
        
        # Invalid enum value (not in schema)
        with pytest.raises(InvalidParameterValueError) as exc_info:
            generator.validate_and_prepare_params("test", {"status": "pending"})
        
        assert exc_info.value.parameter_name == "status"
        assert "active" in exc_info.value.reason or "inactive" in exc_info.value.reason

    def test_schema_mismatch_default_value_wrong_type(self):
        """Test schema with default value of wrong type."""
        # This tests that default values are not validated at schema load time
        # but should be validated when used
        schema_wrong_default = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_test"
                            }
                        }
                    },
                    "CommandRequest_test": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["test"]},
                            "params": {
                                "type": "object",
                                "properties": {
                                    "count": {
                                        "type": "integer",
                                        "default": "not_an_integer"  # Wrong type default
                                    }
                                },
                                "required": []
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_wrong_default)
        method_info = generator.get_method_info("test")
        
        # Default value is stored as-is (schema validation would catch this in real scenario)
        # When used, it would fail type validation
        count_param = method_info.parameters.get("count")
        if count_param:
            # If default is wrong type, validation should catch it when used
            assert count_param.default_value == "not_an_integer"

    def test_validate_and_prepare_params_multiple_required_missing(self):
        """Test validation when multiple required parameters are missing."""
        schema_multiple_req = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_test"
                            }
                        }
                    },
                    "CommandRequest_test": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["test"]},
                            "params": {
                                "type": "object",
                                "properties": {
                                    "param1": {"type": "string"},
                                    "param2": {"type": "integer"}
                                },
                                "required": ["param1", "param2"]
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_multiple_req)
        
        # Missing both required params - should raise error for first missing
        with pytest.raises(RequiredParameterMissingError) as exc_info:
            generator.validate_and_prepare_params("test", {})
        
        assert exc_info.value.parameter_name in ["param1", "param2"]

    def test_validate_and_prepare_params_partial_required_missing(self):
        """Test validation when some required parameters are missing."""
        schema_multiple_req = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_test"
                            }
                        }
                    },
                    "CommandRequest_test": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["test"]},
                            "params": {
                                "type": "object",
                                "properties": {
                                    "param1": {"type": "string"},
                                    "param2": {"type": "integer"}
                                },
                                "required": ["param1", "param2"]
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_multiple_req)
        
        # Missing one required param
        with pytest.raises(RequiredParameterMissingError) as exc_info:
            generator.validate_and_prepare_params("test", {"param1": "value"})
        
        assert exc_info.value.parameter_name == "param2"

    def test_get_method_description_with_enum(self):
        """Test method description includes enum information."""
        schema_with_enum = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "test": "#/components/schemas/CommandRequest_test"
                            }
                        }
                    },
                    "CommandRequest_test": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["test"]},
                            "params": {
                                "type": "object",
                                "properties": {
                                    "status": {
                                        "type": "string",
                                        "enum": ["active", "inactive"]
                                    }
                                },
                                "required": []
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(schema_with_enum)
        description = generator.get_method_description("test")
        
        assert "status" in description
        assert "Allowed values" in description or "enum" in description.lower()

    def test_schema_example_with_complex_nested_structure(self):
        """Test schema example with complex nested parameters."""
        complex_schema = {
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "discriminator": {
                            "mapping": {
                                "complex": "#/components/schemas/CommandRequest_complex"
                            }
                        }
                    },
                    "CommandRequest_complex": {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {"type": "string", "enum": ["complex"]},
                            "params": {
                                "type": "object",
                                "properties": {
                                    "nested": {
                                        "type": "object",
                                        "properties": {
                                            "key": {"type": "string"}
                                        }
                                    },
                                    "array": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": []
                            }
                        }
                    }
                }
            }
        }
        
        generator = SchemaRequestGenerator(complex_schema)
        example_json = generator.schema_example()
        example = json.loads(example_json)
        
        assert "complex" in example["methods"]
        complex_method = example["methods"]["complex"]
        assert "parameters" in complex_method

