"""
Airtable Table Management - Create, update, and manage Airtable tables
"""

import requests
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel
from enum import Enum

from .exceptions import APIError
from .fields import AirtableFieldType, TypeMapper


class TableManager:
    """
    Manager for Airtable table operations using the Airtable API
    """
    
    META_API_URL = "https://api.airtable.com/v0/meta"
    
    def __init__(self, access_token: str, base_id: str):
        """
        Initialize Table Manager
        
        Args:
            access_token: Airtable Personal Access Token
            base_id: Airtable base ID
        """
        self.access_token = access_token
        self.base_id = base_id
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions"""
        try:
            data = response.json()
        except:
            data = {"error": {"message": response.text}}
        
        if not response.ok:
            error_message = data.get("error", {}).get("message", f"HTTP {response.status_code}")
            raise APIError(
                message=error_message,
                status_code=response.status_code,
                response_data=data
            )
        
        return data
    
    def list_tables(self) -> List[Dict[str, Any]]:
        """
        List all tables in the base
        
        Returns:
            List of table information
        """
        response = self.session.get(f"{self.META_API_URL}/bases/{self.base_id}/tables")
        data = self._handle_response(response)
        return data.get("tables", [])
    
    def get_table_schema(self, table_id_or_name: str) -> Dict[str, Any]:
        """
        Get schema for a specific table
        
        Args:
            table_id_or_name: Table ID or name
            
        Returns:
            Table schema information
        """
        tables = self.list_tables()
        for table in tables:
            if table.get("id") == table_id_or_name or table.get("name") == table_id_or_name:
                return table
        raise APIError(f"Table {table_id_or_name} not found", status_code=404)
    
    def create_table_from_pydantic(
        self, 
        model_class: Type[BaseModel], 
        table_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an Airtable table based on a Pydantic model
        
        Args:
            model_class: Pydantic model class to create table from
            table_name: Optional table name (defaults to class name)
            description: Optional table description
            
        Returns:
            Created table information
        """
        table_name = table_name or model_class.__name__
        fields = self._convert_pydantic_to_airtable_fields(model_class)
        
        table_config = {
            "name": table_name,
            "fields": fields
        }
        
        if description:
            table_config["description"] = description
        
        return self.create_table(table_config)
    
    def create_table(self, table_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new table in the base
        
        Args:
            table_config: Table configuration including name, fields, etc.
            
        Returns:
            Created table information
        """
        response = self.session.post(
            f"{self.META_API_URL}/bases/{self.base_id}/tables",
            json=table_config
        )
        return self._handle_response(response)
    
    def update_table(self, table_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing table
        
        Args:
            table_id: Table ID to update
            updates: Updates to apply to the table
            
        Returns:
            Updated table information
        """
        response = self.session.patch(
            f"{self.META_API_URL}/bases/{self.base_id}/tables/{table_id}",
            json=updates
        )
        return self._handle_response(response)
    
    def delete_table(self, table_id: str) -> Dict[str, Any]:
        """
        Delete a table
        
        Args:
            table_id: Table ID to delete
            
        Returns:
            Deletion confirmation
        """
        response = self.session.delete(
            f"{self.META_API_URL}/bases/{self.base_id}/tables/{table_id}"
        )
        return self._handle_response(response)
    
    def sync_pydantic_model_to_table(
        self, 
        model_class: Type[BaseModel], 
        table_id_or_name: str,
        create_missing_fields: bool = True,
        update_field_types: bool = False
    ) -> Dict[str, Any]:
        """
        Synchronize a Pydantic model with an existing Airtable table
        
        Args:
            model_class: Pydantic model to sync
            table_id_or_name: Existing table ID or name
            create_missing_fields: Whether to create fields missing in Airtable
            update_field_types: Whether to update field types (dangerous)
            
        Returns:
            Sync results and any updates made
        """
        # Get current table schema
        current_table = self.get_table_schema(table_id_or_name)
        table_id = current_table["id"]
        current_fields = {f["name"]: f for f in current_table.get("fields", [])}
        
        # Get Pydantic model fields
        desired_fields = self._convert_pydantic_to_airtable_fields(model_class)
        
        updates = {"fields": []}
        sync_results = {
            "fields_added": [],
            "fields_updated": [],
            "fields_unchanged": [],
            "warnings": []
        }
        
        # Process each field from the Pydantic model
        for field_config in desired_fields:
            field_name = field_config["name"]
            
            if field_name in current_fields:
                # Field exists - check if update needed
                current_field = current_fields[field_name]
                if update_field_types and current_field["type"] != field_config["type"]:
                    updates["fields"].append({
                        "id": current_field["id"],
                        **field_config
                    })
                    sync_results["fields_updated"].append(field_name)
                else:
                    sync_results["fields_unchanged"].append(field_name)
            else:
                # Field missing - add if requested
                if create_missing_fields:
                    updates["fields"].append(field_config)
                    sync_results["fields_added"].append(field_name)
                else:
                    sync_results["warnings"].append(f"Field '{field_name}' missing in table but not created")
        
        # Apply updates if any
        result = None
        if updates["fields"]:
            result = self.update_table(table_id, updates)
        
        return {
            "sync_results": sync_results,
            "table_update_result": result
        }
    
    def _convert_pydantic_to_airtable_fields(self, model_class: Type[BaseModel]) -> List[Dict[str, Any]]:
        """
        Convert Pydantic model fields to Airtable field configurations
        
        Args:
            model_class: Pydantic model class
            
        Returns:
            List of Airtable field configurations
        """
        fields = []
        model_fields = model_class.model_fields
        
        for field_name, field_info in model_fields.items():
            # Skip Airtable internal fields
            json_schema_extra = getattr(field_info, 'json_schema_extra', {}) or {}
            if json_schema_extra.get('airtable_read_only'):
                continue
            
            # Get field configuration from AirtableField if present
            airtable_field_name = json_schema_extra.get('airtable_field_name') or field_name
            airtable_field_type = json_schema_extra.get('airtable_field_type')
            
            # Auto-detect field type if not specified
            if not airtable_field_type:
                field_type = field_info.annotation
                # Handle Optional types
                if hasattr(field_type, '__origin__') and field_type.__origin__ is type(Optional[str].__origin__):
                    args = getattr(field_type, '__args__', ())
                    if len(args) > 0:
                        field_type = args[0]
                
                airtable_field_type = TypeMapper.get_airtable_type(field_type)
            
            field_config = {
                "name": airtable_field_name,
                "type": airtable_field_type.value
            }
            
            # Add field-specific options based on type
            field_config.update(self._get_field_type_options(field_info, airtable_field_type))
            
            # Add description if available
            description = field_info.description or json_schema_extra.get('description')
            if description:
                field_config["description"] = description
            
            fields.append(field_config)
        
        return fields
    
    def _get_field_type_options(self, field_info, field_type: AirtableFieldType) -> Dict[str, Any]:
        """
        Get field-specific options based on the Airtable field type
        
        Args:
            field_info: Pydantic field info
            field_type: Airtable field type
            
        Returns:
            Dictionary of field options
        """
        options = {}
        
        # Handle select fields
        if field_type in [AirtableFieldType.SELECT, AirtableFieldType.MULTI_SELECT]:
            # Try to extract choices from Enum or constraints
            annotation = field_info.annotation
            
            if hasattr(annotation, '__origin__'):
                # Handle Optional[Enum] or Union types
                args = getattr(annotation, '__args__', ())
                for arg in args:
                    if isinstance(arg, type) and issubclass(arg, Enum):
                        annotation = arg
                        break
            
            if isinstance(annotation, type) and issubclass(annotation, Enum):
                choices = [{"name": choice.value} for choice in annotation]
                options["options"] = {"choices": choices}
        
        # Handle number fields
        elif field_type in [AirtableFieldType.NUMBER, AirtableFieldType.CURRENCY, AirtableFieldType.PERCENT]:
            # Could add precision, format options here
            options["options"] = {"precision": 0}
        
        # Handle checkbox fields
        elif field_type == AirtableFieldType.CHECKBOX:
            options["options"] = {
                "icon": "check",
                "color": "greenBright"
            }
        
        # Handle date/datetime fields
        elif field_type == AirtableFieldType.DATETIME:
            options["options"] = {
                "dateFormat": {"name": "iso"},
                "timeFormat": {"name": "24hour"},
                "timeZone": "utc"
            }
        elif field_type == AirtableFieldType.DATE:
            options["options"] = {"dateFormat": {"name": "iso"}}
        
        return options
    
    def validate_pydantic_model_against_table(
        self, 
        model_class: Type[BaseModel], 
        table_id_or_name: str
    ) -> Dict[str, Any]:
        """
        Validate that a Pydantic model matches an existing Airtable table
        
        Args:
            model_class: Pydantic model to validate
            table_id_or_name: Table ID or name to validate against
            
        Returns:
            Validation results with any mismatches
        """
        table_schema = self.get_table_schema(table_id_or_name)
        table_fields = {f["name"]: f for f in table_schema.get("fields", [])}
        
        model_fields = self._convert_pydantic_to_airtable_fields(model_class)
        model_field_names = {f["name"] for f in model_fields}
        table_field_names = set(table_fields.keys())
        
        validation_results = {
            "is_valid": True,
            "missing_in_table": list(model_field_names - table_field_names),
            "missing_in_model": list(table_field_names - model_field_names),
            "type_mismatches": [],
            "warnings": []
        }
        
        # Check for type mismatches
        for model_field in model_fields:
            field_name = model_field["name"]
            if field_name in table_fields:
                table_field = table_fields[field_name]
                if table_field["type"] != model_field["type"]:
                    validation_results["type_mismatches"].append({
                        "field_name": field_name,
                        "model_type": model_field["type"],
                        "table_type": table_field["type"]
                    })
        
        # Set overall validity
        validation_results["is_valid"] = (
            len(validation_results["missing_in_table"]) == 0 and
            len(validation_results["missing_in_model"]) == 0 and
            len(validation_results["type_mismatches"]) == 0
        )
        
        return validation_results

