"""
Base Airtable model that integrates with Pydantic
"""

import os
from typing import Any, Dict, List, Optional, ClassVar
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from .client import AirtableClient
from .fields import AirtableField, TypeMapper, AirtableFieldType
from .exceptions import ConfigurationError


class AirtableConfig:
    """Configuration for Airtable connection"""

    def __init__(
        self,
        access_token: Optional[str] = None,
        base_id: Optional[str] = None,
        table_name: Optional[str] = None,
        api_key: Optional[str] = None  # DEPRECATED - for backward compatibility
    ):
        # Handle backward compatibility and deprecation
        if api_key is not None and access_token is None:
            import warnings
            warnings.warn(
                "The 'api_key' parameter is deprecated. Use 'access_token' instead. "
                "API keys are deprecated by Airtable in favor of Personal Access Tokens (PATs). "
                "See: https://airtable.com/developers/web/api/authentication",
                DeprecationWarning,
                stacklevel=2
            )
            access_token = api_key
        elif api_key is not None and access_token is not None:
            raise ValueError("Cannot specify both 'access_token' and 'api_key'. Use 'access_token' only.")

        # Try new environment variable first, then fall back to old one for compatibility
        self.access_token = (
            access_token or 
            os.getenv("AIRTABLE_ACCESS_TOKEN") or 
            os.getenv("AIRTABLE_API_KEY")  # Backward compatibility
        )
        
        self.base_id = base_id or os.getenv("AIRTABLE_BASE_ID")
        self.table_name = table_name

        if not self.access_token:
            raise ConfigurationError(
                "Airtable Personal Access Token not provided. Set AIRTABLE_ACCESS_TOKEN "
                "environment variable or pass access_token parameter. "
                "Get your PAT from: https://airtable.com/developers/web/api/authentication"
            )
        if not self.base_id:
            raise ConfigurationError(
                "Airtable Base ID not provided. Set AIRTABLE_BASE_ID "
                "environment variable or pass base_id parameter."
            )

        # Also warn if using deprecated environment variable
        if not access_token and not api_key and os.getenv("AIRTABLE_API_KEY") and not os.getenv("AIRTABLE_ACCESS_TOKEN"):
            import warnings
            warnings.warn(
                "AIRTABLE_API_KEY environment variable is deprecated. "
                "Use AIRTABLE_ACCESS_TOKEN instead with a Personal Access Token (PAT). "
                "See: https://airtable.com/developers/web/api/authentication",
                DeprecationWarning,
                stacklevel=2
            )


class AirtableModelMeta(type(BaseModel)):
    """Metaclass for Airtable models to handle configuration"""

    def __new__(cls, name, bases, namespace, **kwargs):
        # Get configuration from class attributes
        config = namespace.get('AirtableConfig')
        if config and hasattr(config, 'table_name') and not config.table_name:
            # Auto-generate table name from class name if not provided
            config.table_name = name

        return super().__new__(cls, name, bases, namespace, **kwargs)


class AirtableModel(BaseModel, metaclass=AirtableModelMeta):
    """
    Base model for Airtable records that integrates Pydantic validation
    with Airtable CRUD operations.
    """

    # Use extra='ignore' to allow fields from Airtable that aren't defined in the model
    # This is important because Airtable can have auto-generated fields (like inverse
    # LINKED_RECORD fields) that the model doesn't need to know about
    model_config = ConfigDict(
        extra='ignore',
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )

    # Airtable-specific fields
    id: Optional[str] = AirtableField(
        default=None,
        airtable_field_name="id",
        airtable_field_type=AirtableFieldType.AUTO_NUMBER,
        read_only=True,
        description="Airtable record ID"
    )

    created_time: Optional[datetime] = AirtableField(
        default=None,
        airtable_field_name="createdTime",
        airtable_field_type=AirtableFieldType.CREATED_TIME,
        read_only=True,
        description="When the record was created"
    )

    # Configuration (to be set in subclasses)
    AirtableConfig: ClassVar[Optional[AirtableConfig]] = None

    def __init__(self, **data):
        super().__init__(**data)
        self._client: Optional[AirtableClient] = None

    @classmethod
    def _get_client(cls) -> AirtableClient:
        """Get or create Airtable client"""
        if not cls.AirtableConfig:
            raise ConfigurationError(
                f"AirtableConfig not set for {cls.__name__}"
            )

        return AirtableClient(
            access_token=cls.AirtableConfig.access_token,
            base_id=cls.AirtableConfig.base_id,
            table_name=cls.AirtableConfig.table_name or cls.__name__
        )
    
    @classmethod
    def create_table_in_airtable(
        cls,
        table_name: Optional[str] = None,
        description: Optional[str] = None,
        base_id: Optional[str] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an Airtable table based on this Pydantic model
        
        Args:
            table_name: Optional table name (defaults to class name)
            description: Optional table description
            base_id: Optional base ID (defaults to config)
            access_token: Optional access token (defaults to config)
            
        Returns:
            Created table information
        """
        from .table_manager import TableManager
        
        # Use provided values or fall back to class config
        if not cls.AirtableConfig:
            raise ConfigurationError(f"AirtableConfig not set for {cls.__name__}")
        
        final_base_id = base_id or cls.AirtableConfig.base_id
        final_access_token = access_token or cls.AirtableConfig.access_token
        final_table_name = table_name or cls.AirtableConfig.table_name or cls.__name__
        
        if not final_base_id or not final_access_token:
            raise ConfigurationError("base_id and access_token are required")
        
        table_manager = TableManager(final_access_token, final_base_id)
        result = table_manager.create_table_from_pydantic(
            cls, 
            table_name=final_table_name,
            description=description
        )
        
        # Update the class config with the table name if it was auto-generated
        if not cls.AirtableConfig.table_name:
            cls.AirtableConfig.table_name = final_table_name
        
        return result
    
    @classmethod
    def sync_table_schema(
        cls,
        table_id_or_name: Optional[str] = None,
        create_missing_fields: bool = True,
        update_field_types: bool = False
    ) -> Dict[str, Any]:
        """
        Synchronize this Pydantic model with an existing Airtable table
        
        Args:
            table_id_or_name: Table to sync with (defaults to config table_name)
            create_missing_fields: Whether to create fields missing in Airtable
            update_field_types: Whether to update field types (use with caution)
            
        Returns:
            Sync results
        """
        from .table_manager import TableManager
        
        if not cls.AirtableConfig:
            raise ConfigurationError(f"AirtableConfig not set for {cls.__name__}")
        
        table_target = table_id_or_name or cls.AirtableConfig.table_name or cls.__name__
        
        table_manager = TableManager(cls.AirtableConfig.access_token, cls.AirtableConfig.base_id)
        return table_manager.sync_pydantic_model_to_table(
            cls,
            table_target,
            create_missing_fields=create_missing_fields,
            update_field_types=update_field_types
        )
    
    @classmethod
    def validate_table_schema(cls, table_id_or_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate that this Pydantic model matches an existing Airtable table
        
        Args:
            table_id_or_name: Table to validate against (defaults to config table_name)
            
        Returns:
            Validation results
        """
        from .table_manager import TableManager
        
        if not cls.AirtableConfig:
            raise ConfigurationError(f"AirtableConfig not set for {cls.__name__}")
        
        table_target = table_id_or_name or cls.AirtableConfig.table_name or cls.__name__
        
        table_manager = TableManager(cls.AirtableConfig.access_token, cls.AirtableConfig.base_id)
        return table_manager.validate_pydantic_model_against_table(cls, table_target)

    @classmethod
    def _get_field_mappings(cls) -> Dict[str, Dict[str, Any]]:
        """Get field mappings between Python and Airtable field names"""
        mappings = {}

        for field_name, field_info in cls.model_fields.items():
            json_schema_extra = getattr(field_info, 'json_schema_extra', {}) or {}

            airtable_field_name = json_schema_extra.get('airtable_field_name') or field_name
            airtable_field_type = json_schema_extra.get('airtable_field_type')
            read_only = json_schema_extra.get('airtable_read_only', False)

            # Auto-detect field type if not specified
            if not airtable_field_type:
                field_type = field_info.annotation
                if hasattr(field_type, '__origin__'):  # Handle Optional types
                    args = getattr(field_type, '__args__', ())
                    if len(args) > 0:
                        field_type = args[0]

                airtable_field_type = TypeMapper.get_airtable_type(field_type)

            mappings[field_name] = {
                'airtable_name': airtable_field_name,
                'airtable_type': airtable_field_type,
                'read_only': read_only
            }

        return mappings

    def _to_airtable_fields(self, exclude_readonly: bool = True) -> Dict[str, Any]:
        """Convert model instance to Airtable fields format"""
        field_mappings = self._get_field_mappings()
        airtable_fields = {}

        for field_name, value in self.__dict__.items():
            if field_name.startswith('_'):  # Skip private attributes
                continue

            mapping = field_mappings.get(field_name)
            if not mapping:
                continue

            if exclude_readonly and mapping['read_only']:
                continue

            if value is not None:
                formatted_value = TypeMapper.format_value_for_airtable(
                    value, mapping['airtable_type']
                )
                airtable_fields[mapping['airtable_name']] = formatted_value

        return airtable_fields

    @classmethod
    def _from_airtable_record(cls, record_data: Dict[str, Any]) -> 'AirtableModel':
        """Create model instance from Airtable record data"""
        field_mappings = cls._get_field_mappings()

        # Create reverse mapping (Airtable name -> Python name)
        reverse_mappings = {
            mapping['airtable_name']: {
                'python_name': field_name,
                'airtable_type': mapping['airtable_type']
            }
            for field_name, mapping in field_mappings.items()
        }

        # Extract fields from record
        model_data = {}

        # Add record ID
        model_data['id'] = record_data.get('id')
        model_data['created_time'] = record_data.get('createdTime')

        # Process fields
        fields = record_data.get('fields', {})
        for airtable_name, value in fields.items():
            mapping = reverse_mappings.get(airtable_name)
            if mapping:
                parsed_value = TypeMapper.parse_value_from_airtable(
                    value, mapping['airtable_type']
                )
                model_data[mapping['python_name']] = parsed_value

        return cls(**model_data)

    # CRUD Operations

    def save(self) -> 'AirtableModel':
        """Save the record to Airtable (create or update)"""
        client = self._get_client()
        airtable_fields = self._to_airtable_fields()

        if self.id:
            # Update existing record
            response = client.update_record(self.id, airtable_fields)
        else:
            # Create new record
            response = client.create_record(airtable_fields)

        # Update instance with response data
        updated_instance = self._from_airtable_record(response)
        for field_name, value in updated_instance.__dict__.items():
            if not field_name.startswith('_') and field_name != 'AirtableConfig':
                setattr(self, field_name, value)

        return self

    def delete(self) -> bool:
        """Delete the record from Airtable"""
        if not self.id:
            raise ValueError("Cannot delete record without ID")

        client = self._get_client()
        client.delete_record(self.id)
        self.id = None
        return True

    @classmethod
    def get(cls, record_id: str) -> 'AirtableModel':
        """Get a record by ID"""
        client = cls._get_client()
        record_data = client.get_record(record_id)
        return cls._from_airtable_record(record_data)

    @classmethod
    def create(cls, **kwargs) -> 'AirtableModel':
        """Create and save a new record"""
        instance = cls(**kwargs)
        return instance.save()

    @classmethod
    def all(cls, **kwargs) -> List['AirtableModel']:
        """Get all records"""
        return cls.filter(**kwargs)

    @classmethod
    def filter(
        cls,
        filter_by_formula: Optional[str] = None,
        max_records: Optional[int] = None,
        sort: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> List['AirtableModel']:
        """
        Filter records based on criteria

        Args:
            filter_by_formula: Airtable formula for filtering
            max_records: Maximum number of records to return
            sort: List of sort specifications
            **kwargs: Additional parameters passed to client.list_records
        """
        client = cls._get_client()

        records_data = client.list_records(
            filter_by_formula=filter_by_formula,
            max_records=max_records,
            sort=sort,
            **kwargs
        )

        return [cls._from_airtable_record(record) for record in records_data]

    @classmethod
    def find_by(cls, **field_filters) -> List['AirtableModel']:
        """
        Find records by field values

        Args:
            **field_filters: Field name to value mappings for filtering
        """
        if not field_filters:
            return cls.all()

        # Build Airtable formula
        conditions = []
        field_mappings = cls._get_field_mappings()

        for python_field, value in field_filters.items():
            mapping = field_mappings.get(python_field)
            if not mapping:
                continue

            airtable_field = mapping['airtable_name']

            if isinstance(value, str):
                condition = f"{{{{field_name}}}} = '{value}'"
            elif isinstance(value, bool):
                # Airtable checkbox fields need special handling
                if value:
                    condition = "{{field_name}}"  # True condition
                else:
                    condition = "NOT({{field_name}})"  # False condition
            else:
                condition = f"{{{{field_name}}}} = {value}"

            conditions.append(condition.replace('{field_name}', airtable_field))

        if not conditions:
            return cls.all()

        formula = "AND(" + ", ".join(conditions) + ")" if len(conditions) > 1 else conditions[0]

        return cls.filter(filter_by_formula=formula)

    @classmethod
    def first(cls, **field_filters) -> Optional['AirtableModel']:
        """Get the first record matching the criteria"""
        results = cls.find_by(**field_filters)
        return results[0] if results else None

    @classmethod
    def bulk_create(cls, records_data: List[Dict[str, Any]]) -> List['AirtableModel']:
        """Create multiple records in batch"""
        client = cls._get_client()

        # Convert to Airtable format
        airtable_records = []
        for data in records_data:
            instance = cls(**data)
            airtable_fields = instance._to_airtable_fields()
            airtable_records.append(airtable_fields)

        # Batch create
        created_records = client.batch_create(airtable_records)

        return [cls._from_airtable_record(record) for record in created_records]

    def refresh(self) -> 'AirtableModel':
        """Refresh the instance from Airtable"""
        if not self.id:
            raise ValueError("Cannot refresh record without ID")

        fresh_instance = self.get(self.id)
        for field_name, value in fresh_instance.__dict__.items():
            if not field_name.startswith('_'):
                setattr(self, field_name, value)

        return self
