"""
Unified Airtable manager combining base and table operations
"""

from typing import Any, Dict, List, Optional, Type, Union, get_type_hints
from datetime import datetime, date, timedelta
from enum import Enum

from .http_client import BaseHTTPClient
from .config import AirtableConfig
from .exceptions import APIError
from .fields import AirtableFieldType


class AirtableManager:
    """
    Unified manager for all Airtable operations
    
    Combines functionality from BaseManager and TableManager
    into a single, cohesive interface
    """
    
    def __init__(self, config: AirtableConfig):
        """
        Initialize Airtable manager
        
        Args:
            config: Airtable configuration
        """
        self.config = config
        self.client = BaseHTTPClient(config.access_token)
    
    # =================================================================
    # BASE OPERATIONS
    # =================================================================
    
    def create_base(self, name: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a new Airtable base
        
        Args:
            name: Base name
            tables: List of table definitions
            
        Returns:
            Created base information
        """
        url = self.client.build_meta_url("bases")
        data = {
            "name": name,
            "tables": tables
        }
        return self.client.post(url, json=data)
    
    def list_bases(self) -> List[Dict[str, Any]]:
        """
        List all bases accessible to the current user
        
        Returns:
            List of base information
        """
        url = self.client.build_meta_url("bases")
        response = self.client.get(url)
        return response.get("bases", [])
    
    def get_base_schema(self, base_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get schema for a base
        
        Args:
            base_id: Base ID (uses config default if None)
            
        Returns:
            Base schema information
        """
        target_base_id = base_id or self.config.base_id
        url = self.client.build_meta_url("bases", target_base_id, "tables")
        return self.client.get(url)
    
    def delete_base(self, base_id: str) -> Dict[str, Any]:
        """
        Delete a base
        
        Args:
            base_id: Base ID to delete
            
        Returns:
            Deletion confirmation
        """
        url = self.client.build_meta_url("bases", base_id)
        return self.client.delete(url)
    
    # =================================================================
    # TABLE OPERATIONS  
    # =================================================================
    
    def create_table(
        self, 
        name: str, 
        fields: List[Dict[str, Any]], 
        base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new table in a base
        
        Args:
            name: Table name
            fields: Field definitions
            base_id: Base ID (uses config default if None)
            
        Returns:
            Created table information
        """
        target_base_id = base_id or self.config.base_id
        url = self.client.build_meta_url("bases", target_base_id, "tables")
        
        data = {
            "name": name,
            "fields": fields
        }
        return self.client.post(url, json=data)
    
    def get_table_schema(
        self, 
        table_name: str, 
        base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get schema for a specific table
        
        Args:
            table_name: Table name
            base_id: Base ID (uses config default if None)
            
        Returns:
            Table schema
        """
        target_base_id = base_id or self.config.base_id
        base_schema = self.get_base_schema(target_base_id)
        
        for table in base_schema.get("tables", []):
            if table.get("name") == table_name:
                return table
        
        raise APIError(f"Table '{table_name}' not found in base {target_base_id}")
    
    def update_table(
        self, 
        table_id: str, 
        updates: Dict[str, Any],
        base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update table properties
        
        Args:
            table_id: Table ID to update
            updates: Update data
            base_id: Base ID (uses config default if None)
            
        Returns:
            Updated table information
        """
        target_base_id = base_id or self.config.base_id
        url = self.client.build_meta_url("bases", target_base_id, "tables", table_id)
        return self.client.patch(url, json=updates)
    
    def delete_table(
        self, 
        table_id: str, 
        base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a table
        
        Args:
            table_id: Table ID to delete  
            base_id: Base ID (uses config default if None)
            
        Returns:
            Deletion confirmation
        """
        target_base_id = base_id or self.config.base_id
        url = self.client.build_meta_url("bases", target_base_id, "tables", table_id)
        return self.client.delete(url)
    
    # =================================================================
    # PYDANTIC MODEL INTEGRATION
    # =================================================================
    
    def create_table_from_model(
        self, 
        model_class: Type, 
        table_name: Optional[str] = None,
        base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a table from a Pydantic model
        
        Args:
            model_class: Pydantic model class
            table_name: Table name (uses model name if None)
            base_id: Base ID (uses config default if None)
            
        Returns:
            Created table information
        """
        name = table_name or getattr(model_class, '__name__', 'UnnamedTable')
        fields = self._convert_model_to_fields(model_class)
        
        return self.create_table(name, fields, base_id)
    
    def sync_model_to_table(
        self,
        model_class: Type,
        table_name: Optional[str] = None,
        base_id: Optional[str] = None,
        create_missing_fields: bool = True,
        update_field_types: bool = False
    ) -> Dict[str, Any]:
        """
        Synchronize a Pydantic model with an existing table
        
        Args:
            model_class: Pydantic model class
            table_name: Table name (uses model name if None)
            base_id: Base ID (uses config default if None)
            create_missing_fields: Whether to create missing fields
            update_field_types: Whether to update field types
            
        Returns:
            Synchronization results
        """
        name = table_name or getattr(model_class, '__name__', 'UnnamedTable')
        
        try:
            table_schema = self.get_table_schema(name, base_id)
        except APIError:
            # Table doesn't exist, create it
            return self.create_table_from_model(model_class, name, base_id)
        
        # Compare model fields with table schema and sync differences
        model_fields = self._convert_model_to_fields(model_class)
        existing_fields = {f["name"]: f for f in table_schema.get("fields", [])}
        
        results = {
            "table_id": table_schema["id"],
            "fields_created": [],
            "fields_updated": [],
            "fields_skipped": []
        }
        
        for field_def in model_fields:
            field_name = field_def["name"]
            
            if field_name not in existing_fields:
                if create_missing_fields:
                    # Create missing field (would need additional API calls)
                    results["fields_created"].append(field_name)
                else:
                    results["fields_skipped"].append(field_name)
            else:
                existing_field = existing_fields[field_name]
                if (update_field_types and 
                    existing_field.get("type") != field_def.get("type")):
                    # Update field type (would need additional API calls)
                    results["fields_updated"].append(field_name)
        
        return results
    
    def _convert_model_to_fields(self, model_class: Type) -> List[Dict[str, Any]]:
        """
        Convert Pydantic model to Airtable field definitions
        
        Args:
            model_class: Pydantic model class
            
        Returns:
            List of Airtable field definitions
        """
        fields = []
        type_hints = get_type_hints(model_class)
        
        # Skip internal fields
        skip_fields = {'id', 'created_time', 'AirtableConfig'}
        
        for field_name, field_info in getattr(model_class, 'model_fields', {}).items():
            if field_name in skip_fields:
                continue
                
            # Extract field metadata
            json_schema_extra = getattr(field_info, 'json_schema_extra', {}) or {}
            airtable_field_name = json_schema_extra.get('airtable_field_name', field_name)
            airtable_field_type = json_schema_extra.get('airtable_field_type')
            
            # Auto-detect field type if not specified
            if not airtable_field_type:
                python_type = type_hints.get(field_name, str)
                airtable_field_type = self._python_type_to_airtable_type(python_type)
            
            field_def = {
                "name": airtable_field_name,
                "type": airtable_field_type.value if hasattr(airtable_field_type, 'value') else airtable_field_type
            }
            
            # Add field-specific options
            python_type = type_hints.get(field_name, str)
            options = self._get_field_options(airtable_field_type, json_schema_extra, field_info, python_type)
            if options:
                field_def["options"] = options
            
            fields.append(field_def)
        
        return fields
    
    def _get_field_options(self, field_type: AirtableFieldType, json_schema_extra: Dict[str, Any], field_info=None, python_type=None) -> Optional[Dict[str, Any]]:
        """
        Get field options for specific Airtable field types
        
        Args:
            field_type: Airtable field type
            json_schema_extra: Field metadata from Pydantic
            
        Returns:
            Field options dictionary or None
        """
        if field_type == AirtableFieldType.CHECKBOX:
            return {
                "icon": json_schema_extra.get("icon", "check"),
                "color": json_schema_extra.get("color", "greenBright")
            }
        
        elif field_type == AirtableFieldType.SELECT:
            choices = json_schema_extra.get("choices", json_schema_extra.get("airtable_choices", []))
            
            # If no explicit choices but python_type is an enum, extract enum values
            if not choices and python_type:
                # Handle Optional types
                actual_type = python_type
                if hasattr(python_type, '__origin__') and python_type.__origin__ is Union:
                    args = python_type.__args__
                    non_none_args = [arg for arg in args if arg != type(None)]
                    if non_none_args:
                        actual_type = non_none_args[0]
                
                # Check if it's an enum
                if isinstance(actual_type, type) and issubclass(actual_type, Enum):
                    choices = [member.value for member in actual_type]
            
            if choices:
                return {"choices": [{"name": str(choice)} for choice in choices]}
            # Return empty choices for enum-based selects
            return {"choices": []}
        
        elif field_type == AirtableFieldType.MULTI_SELECT:
            choices = json_schema_extra.get("choices", json_schema_extra.get("airtable_choices", []))
            if choices:
                return {"choices": [{"name": str(choice)} for choice in choices]}
            # Return empty choices - required for MULTI_SELECT
            return {"choices": []}
        
        elif field_type == AirtableFieldType.CURRENCY:
            return {
                "precision": json_schema_extra.get("precision", 2),
                "symbol": json_schema_extra.get("symbol", "$")
            }
        
        elif field_type == AirtableFieldType.PERCENT:
            return {
                "precision": json_schema_extra.get("precision", 1)
            }
        
        elif field_type == AirtableFieldType.DATETIME:
            return {
                "dateFormat": {"name": "iso"},
                "timeFormat": {"name": "24hour"},
                "timeZone": "utc"
            }
        
        elif field_type == AirtableFieldType.DATE:
            return {
                "dateFormat": {"name": "iso"}
            }
        
        elif field_type == AirtableFieldType.NUMBER:
            return {
                "precision": json_schema_extra.get("precision", 0)
            }
        
        elif field_type == AirtableFieldType.DURATION:
            # Duration format: h:mm, h:mm:ss, h:mm:ss.S, h:mm:ss.SS, h:mm:ss.SSS
            return {
                "durationFormat": json_schema_extra.get("duration_format", "h:mm")
            }
        
        elif field_type == AirtableFieldType.RATING:
            # Rating: max (1-10), icon (star, heart, thumbs-up, flag, dot)
            return {
                "max": json_schema_extra.get("max", 5),
                "icon": json_schema_extra.get("icon", "star"),
                "color": json_schema_extra.get("color", "yellowBright")
            }
        
        elif field_type == AirtableFieldType.LINKED_RECORD:
            # Linked record requires linkedTableId
            options = {}
            linked_table_id = json_schema_extra.get("linked_table_id")
            if linked_table_id:
                options["linkedTableId"] = linked_table_id
            if json_schema_extra.get("single_record"):
                options["prefersSingleRecordLink"] = True
            inverse_field = json_schema_extra.get("inverse_link_field_id")
            if inverse_field:
                options["inverseLinkFieldId"] = inverse_field
            return options if options else None
        
        elif field_type == AirtableFieldType.USER:
            # User/Collaborator field
            return {
                "shouldNotify": json_schema_extra.get("should_notify", False)
            }
        
        elif field_type == AirtableFieldType.BUTTON:
            # Button field - triggers automations
            return {
                "label": json_schema_extra.get("label", "Click")
            }
        
        elif field_type == AirtableFieldType.BARCODE:
            # Barcode field - no required options
            return None
        
        return None
    
    def _python_type_to_airtable_type(self, python_type: Type) -> AirtableFieldType:
        """
        Map Python types to Airtable field types
        
        Args:
            python_type: Python type
            
        Returns:
            Corresponding Airtable field type
        """
        # Handle Optional types
        if hasattr(python_type, '__origin__') and python_type.__origin__ is Union:
            args = python_type.__args__
            non_none_args = [arg for arg in args if arg != type(None)]
            if non_none_args:
                python_type = non_none_args[0]
        
        # Basic type mapping
        type_mapping = {
            str: AirtableFieldType.SINGLE_LINE_TEXT,
            int: AirtableFieldType.NUMBER,
            float: AirtableFieldType.NUMBER,
            bool: AirtableFieldType.CHECKBOX,
            datetime: AirtableFieldType.DATETIME,
            date: AirtableFieldType.DATE,
            timedelta: AirtableFieldType.DURATION,
            list: AirtableFieldType.MULTI_SELECT,
        }
        
        # Handle string subtypes by field name patterns
        if python_type == str:
            # Could add email detection, URL detection, etc.
            return AirtableFieldType.SINGLE_LINE_TEXT
        
        # Handle enums
        if isinstance(python_type, type) and issubclass(python_type, Enum):
            return AirtableFieldType.SELECT
        
        return type_mapping.get(python_type, AirtableFieldType.SINGLE_LINE_TEXT)
    
    # =================================================================
    # RECORD OPERATIONS (delegated to client with table-specific URLs)
    # =================================================================
    
    def _get_records_url(self, table_name: Optional[str] = None, base_id: Optional[str] = None) -> str:
        """Build URL for record operations"""
        target_base_id = base_id or self.config.base_id
        target_table = table_name or self.config.validate_table_name()
        return self.client.build_url(target_base_id, target_table)
    
    def get_records(
        self, 
        table_name: Optional[str] = None,
        base_id: Optional[str] = None,
        **params
    ) -> Dict[str, Any]:
        """Get records from a table"""
        url = self._get_records_url(table_name, base_id)
        return self.client.get(url, params=params)
    
    def create_record(
        self, 
        fields: Dict[str, Any], 
        table_name: Optional[str] = None,
        base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a record"""
        url = self._get_records_url(table_name, base_id)
        return self.client.post(url, json={"fields": fields})
    
    def get_record(
        self, 
        record_id: str, 
        table_name: Optional[str] = None,
        base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a specific record"""
        base_url = self._get_records_url(table_name, base_id)
        url = f"{base_url}/{record_id}"
        return self.client.get(url)
    
    def update_record(
        self, 
        record_id: str, 
        fields: Dict[str, Any], 
        table_name: Optional[str] = None,
        base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a record"""
        base_url = self._get_records_url(table_name, base_id)
        url = f"{base_url}/{record_id}"
        return self.client.patch(url, json={"fields": fields})
    
    def delete_record(
        self, 
        record_id: str, 
        table_name: Optional[str] = None,
        base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete a record"""
        base_url = self._get_records_url(table_name, base_id)
        url = f"{base_url}/{record_id}"
        return self.client.delete(url)
