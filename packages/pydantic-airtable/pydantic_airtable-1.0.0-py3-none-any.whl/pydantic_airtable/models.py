"""
Streamlined model system with decorators and defaults
"""

from typing import Any, Dict, List, Optional, Type, ClassVar, get_type_hints
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from .config import AirtableConfig, get_global_config
from .manager import AirtableManager
from .field_types import FieldTypeResolver
from .exceptions import ConfigurationError


class AirtableModel(BaseModel):
    """
    Streamlined base class for Airtable models
    
    Provides CRUD operations with minimal configuration required
    """
    
    # Configuration will be set by decorator or class definition
    _airtable_config: ClassVar[Optional[AirtableConfig]] = None
    _airtable_manager: ClassVar[Optional[AirtableManager]] = None
    
    # Standard Airtable fields
    id: Optional[str] = None
    created_time: Optional[datetime] = None
    
    # Pydantic configuration
    # Use extra='ignore' to allow fields from Airtable that aren't defined in the model
    # This is important because Airtable can have auto-generated fields (like inverse
    # LINKED_RECORD fields) that the model doesn't need to know about
    model_config = ConfigDict(
        extra='ignore',
        validate_assignment=True,
        use_enum_values=True
    )
    
    @classmethod
    def _get_config(cls) -> AirtableConfig:
        """Get configuration for this model"""
        if cls._airtable_config:
            return cls._airtable_config
        
        # Fall back to global config
        try:
            return get_global_config()
        except ConfigurationError:
            raise ConfigurationError(
                f"No Airtable configuration found for {cls.__name__}. "
                "Use @airtable_model decorator or set global config."
            )
    
    @classmethod
    def _get_manager(cls) -> AirtableManager:
        """Get Airtable manager for this model"""
        if not cls._airtable_manager:
            config = cls._get_config()
            cls._airtable_manager = AirtableManager(config)
        return cls._airtable_manager
    
    @classmethod
    def _get_table_name(cls) -> str:
        """Get table name for this model"""
        config = cls._get_config()
        return config.table_name or cls.__name__
    
    # =================================================================
    # CRUD OPERATIONS
    # =================================================================
    
    @classmethod
    def create(cls, **data) -> 'AirtableModel':
        """
        Create a new record
        
        Args:
            **data: Field values
            
        Returns:
            Created model instance
        """
        # Convert Python field names to Airtable field names
        airtable_data = cls._to_airtable_fields(data)
        
        manager = cls._get_manager()
        table_name = cls._get_table_name()
        
        response = manager.create_record(airtable_data, table_name)
        
        # Convert response back to model
        return cls._from_airtable_record(response)
    
    @classmethod  
    def get(cls, record_id: str) -> 'AirtableModel':
        """
        Get a record by ID
        
        Args:
            record_id: Airtable record ID
            
        Returns:
            Model instance
            
        Raises:
            RecordNotFoundError: If record not found
        """
        manager = cls._get_manager()
        table_name = cls._get_table_name()
        
        response = manager.get_record(record_id, table_name)
        return cls._from_airtable_record(response)
    
    @classmethod
    def all(cls, **filters) -> List['AirtableModel']:
        """
        Get all records
        
        Args:
            **filters: Query parameters
            
        Returns:
            List of model instances
        """
        manager = cls._get_manager()
        table_name = cls._get_table_name()
        
        response = manager.get_records(table_name, **filters)
        
        records = []
        for record_data in response.get('records', []):
            records.append(cls._from_airtable_record(record_data))
        
        return records
    
    @classmethod
    def find_by(cls, **filters) -> List['AirtableModel']:
        """
        Find records by field values
        
        Args:
            **filters: Field name -> value filters
            
        Returns:
            List of matching model instances
        """
        # Convert filters to Airtable formula
        formula_parts = []
        for field_name, value in filters.items():
            airtable_field_name = cls._get_airtable_field_name(field_name)
            
            if isinstance(value, bool):
                # Handle boolean fields - use just the field name for true, empty for false
                if value:
                    formula_parts.append(f"{{{airtable_field_name}}}")
                else:
                    formula_parts.append(f"NOT({{{airtable_field_name}}})")
            elif isinstance(value, str):
                formula_parts.append(f"{{{airtable_field_name}}} = '{value}'")
            else:
                formula_parts.append(f"{{{airtable_field_name}}} = {value}")
        
        if formula_parts:
            formula = " AND ".join(formula_parts)
            return cls.all(filterByFormula=formula)
        
        return cls.all()
    
    @classmethod
    def first(cls, **filters) -> Optional['AirtableModel']:
        """
        Get first record matching filters
        
        Args:
            **filters: Field name -> value filters
            
        Returns:
            First matching model instance or None
        """
        results = cls.find_by(**filters)
        return results[0] if results else None
    
    @classmethod
    def bulk_create(cls, data_list: List[Dict[str, Any]]) -> List['AirtableModel']:
        """
        Create multiple records in batch
        
        Args:
            data_list: List of field value dictionaries
            
        Returns:
            List of created model instances
        """
        created_records = []
        
        # Airtable API supports up to 10 records per batch
        batch_size = 10
        
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            
            for data in batch:
                # For now, create records individually
                # Could be optimized to use batch API
                record = cls.create(**data)
                created_records.append(record)
        
        return created_records
    
    def save(self) -> 'AirtableModel':
        """
        Save changes to this record
        
        Returns:
            Updated model instance
        """
        if not self.id:
            raise ValueError("Cannot save record without ID. Use create() for new records.")
        
        # Get changed fields
        changed_data = self.model_dump(exclude={'id', 'created_time'})
        airtable_data = self._to_airtable_fields(changed_data)
        
        manager = self._get_manager()
        table_name = self._get_table_name()
        
        response = manager.update_record(self.id, airtable_data, table_name)
        
        # Update self with response data
        updated_instance = self._from_airtable_record(response)
        for field, value in updated_instance.model_dump().items():
            setattr(self, field, value)
        
        return self
    
    def delete(self) -> Dict[str, Any]:
        """
        Delete this record
        
        Returns:
            Deletion response
        """
        if not self.id:
            raise ValueError("Cannot delete record without ID")
        
        manager = self._get_manager()
        table_name = self._get_table_name()
        
        return manager.delete_record(self.id, table_name)
    
    # =================================================================
    # TABLE MANAGEMENT
    # =================================================================
    
    @classmethod
    def create_table(cls, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create Airtable table for this model
        
        Args:
            table_name: Table name (uses model name if None)
            
        Returns:
            Created table information
        """
        manager = cls._get_manager()
        name = table_name or cls._get_table_name()
        
        return manager.create_table_from_model(cls, name)
    
    @classmethod
    def sync_table(
        cls, 
        table_name: Optional[str] = None,
        create_missing_fields: bool = True,
        update_field_types: bool = False
    ) -> Dict[str, Any]:
        """
        Synchronize table schema with model
        
        Args:
            table_name: Table name (uses model name if None)
            create_missing_fields: Whether to create missing fields
            update_field_types: Whether to update field types
            
        Returns:
            Synchronization results
        """
        manager = cls._get_manager()
        name = table_name or cls._get_table_name()
        
        return manager.sync_model_to_table(
            cls, name, 
            create_missing_fields=create_missing_fields,
            update_field_types=update_field_types
        )
    
    # =================================================================
    # FIELD CONVERSION UTILITIES
    # =================================================================
    
    @classmethod
    def _get_field_mappings(cls) -> Dict[str, Dict[str, Any]]:
        """Get field mappings for this model"""
        mappings = {}
        type_hints = get_type_hints(cls)
        
        for field_name, field_info in cls.model_fields.items():
            if field_name in ('id', 'created_time'):
                continue
            
            json_schema_extra = getattr(field_info, 'json_schema_extra', {}) or {}
            
            airtable_field_name = json_schema_extra.get('airtable_field_name', field_name)
            airtable_field_type = json_schema_extra.get('airtable_field_type')
            read_only = json_schema_extra.get('airtable_read_only', False)
            
            # Auto-detect field type if not specified
            if not airtable_field_type:
                python_type = type_hints.get(field_name, str)
                airtable_field_type = FieldTypeResolver.resolve_field_type(
                    field_name, python_type, field_info
                )
            
            mappings[field_name] = {
                'airtable_name': airtable_field_name,
                'airtable_type': airtable_field_type,
                'read_only': read_only,
                'python_type': type_hints.get(field_name)
            }
        
        return mappings
    
    @classmethod
    def _get_airtable_field_name(cls, python_field_name: str) -> str:
        """Get Airtable field name for Python field name"""
        mappings = cls._get_field_mappings()
        return mappings.get(python_field_name, {}).get('airtable_name', python_field_name)
    
    @classmethod
    def _to_airtable_fields(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Python field names/values to Airtable format"""
        airtable_data = {}
        mappings = cls._get_field_mappings()
        
        for python_name, value in data.items():
            if python_name in ('id', 'created_time'):
                continue
            
            mapping = mappings.get(python_name, {})
            if mapping.get('read_only'):
                continue
            
            airtable_name = mapping.get('airtable_name', python_name)
            # Convert value to Airtable-compatible format
            airtable_data[airtable_name] = cls._serialize_value(value)
        
        return airtable_data
    
    @classmethod
    def _serialize_value(cls, value: Any) -> Any:
        """
        Serialize Python values to Airtable-compatible format
        
        Args:
            value: Python value to serialize
            
        Returns:
            Airtable-compatible value
        """
        if value is None:
            return None
        
        # Handle datetime objects
        if isinstance(value, datetime):
            return value.isoformat()
        
        # Handle enums
        if hasattr(value, 'value'):
            return value.value
        
        # Handle lists (for multi-select fields)
        if isinstance(value, list):
            return [cls._serialize_value(item) for item in value]
        
        # Handle dictionaries
        if isinstance(value, dict):
            return {k: cls._serialize_value(v) for k, v in value.items()}
        
        # Return as-is for basic types
        return value
    
    @classmethod
    def _from_airtable_record(cls, record: Dict[str, Any]) -> 'AirtableModel':
        """Convert Airtable record to model instance"""
        fields = record.get('fields', {})
        mappings = cls._get_field_mappings()
        
        # Reverse mapping: Airtable name -> Python name
        reverse_mappings = {
            mapping['airtable_name']: python_name 
            for python_name, mapping in mappings.items()
        }
        
        # Convert field names
        python_data = {'id': record.get('id')}
        
        if 'createdTime' in record:
            python_data['created_time'] = record['createdTime']
        
        for airtable_name, value in fields.items():
            python_name = reverse_mappings.get(airtable_name, airtable_name)
            python_data[python_name] = value
        
        # Handle missing fields with defaults
        for python_name, mapping in mappings.items():
            if python_name not in python_data:
                # Set default value for missing fields
                field_info = cls.model_fields.get(python_name)
                if field_info and hasattr(field_info, 'default'):
                    if field_info.default is not ...:  # Ellipsis means required field
                        python_data[python_name] = field_info.default
                    elif hasattr(field_info, 'default_factory') and field_info.default_factory:
                        python_data[python_name] = field_info.default_factory()
        
        return cls(**python_data)


def airtable_model(
    *,
    table_name: Optional[str] = None,
    config: Optional[AirtableConfig] = None,
    access_token: Optional[str] = None,
    base_id: Optional[str] = None
):
    """
    Decorator to configure a model for Airtable integration
    
    Args:
        table_name: Airtable table name (uses class name if None)
        config: Airtable configuration (creates from other params if None)
        access_token: Airtable access token
        base_id: Airtable base ID
        
    Usage:
        @airtable_model(table_name="Users")
        class User(BaseModel):
            name: str
            email: str
            age: Optional[int] = None
    """
    def decorator(cls: Type[BaseModel]) -> Type[AirtableModel]:
        # Create configuration
        if config:
            model_config = config
        elif access_token and base_id:
            model_config = AirtableConfig(
                access_token=access_token,
                base_id=base_id,
                table_name=table_name or cls.__name__
            )
        else:
            # Use global config with table name override
            try:
                global_config = get_global_config()
                model_config = global_config.with_table(table_name or cls.__name__)
            except ConfigurationError:
                # Create empty config, will try to load from env at runtime
                model_config = None
        
        # Create a new class that inherits from both the original class and AirtableModel
        # This preserves all field definitions and methods properly
        
        # Build class dictionary with Airtable-specific attributes
        class_dict = {
            '__module__': cls.__module__,
            '__qualname__': getattr(cls, '__qualname__', cls.__name__),
            '_airtable_config': model_config,
            '_airtable_manager': None,
        }
        
        # Create new class with multiple inheritance
        # This ensures all methods and fields are properly inherited
        new_cls = type(cls.__name__, (cls, AirtableModel), class_dict)
        
        # Add Airtable-specific fields to annotations if not present
        if hasattr(cls, '__annotations__'):
            annotations = cls.__annotations__.copy()
        else:
            annotations = {}
            
        if 'id' not in annotations:
            annotations['id'] = Optional[str]
        if 'created_time' not in annotations:
            annotations['created_time'] = Optional[datetime]
        
        new_cls.__annotations__ = annotations
        
        # Rebuild the Pydantic model to include new fields
        try:
            new_cls.model_rebuild()
        except AttributeError:
            pass  # Older Pydantic versions
        
        return new_cls
    
    return decorator
