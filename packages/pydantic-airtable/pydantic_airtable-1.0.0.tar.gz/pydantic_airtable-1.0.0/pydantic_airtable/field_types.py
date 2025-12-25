"""
Streamlined field type system with field type detection and minimal boilerplate
"""

import re
from typing import Any, Dict, Optional, Type, Union, get_origin, get_args
from datetime import datetime, date, timedelta
from enum import Enum
from pydantic import Field
from pydantic.fields import FieldInfo

from .fields import AirtableFieldType


class FieldTypeResolver:
    """
    Unified field type detection and conversion
    Eliminates duplication and provides defaults
    """
    
    # Core type mappings
    PYTHON_TO_AIRTABLE = {
        str: AirtableFieldType.SINGLE_LINE_TEXT,
        int: AirtableFieldType.NUMBER,
        float: AirtableFieldType.NUMBER,
        bool: AirtableFieldType.CHECKBOX,
        datetime: AirtableFieldType.DATETIME,
        date: AirtableFieldType.DATE,
        timedelta: AirtableFieldType.DURATION,
        list: AirtableFieldType.MULTI_SELECT,
    }
    
    # Field name patterns for field type detection
    # Using anchors and boundaries to avoid false substring matches
    # Patterns use: ^ (start), $ (end), _ (word separator) to be more precise
    
    EMAIL_PATTERNS = [
        r'email',           # Contains 'email' anywhere
        r'e_mail',          # e_mail format
        r'_mail$',          # Ends with _mail
        r'^mail_',          # Starts with mail_
    ]
    
    URL_PATTERNS = [
        r'website',         # Contains 'website'
        r'homepage',        # Contains 'homepage'
        r'_url$',           # Ends with _url
        r'^url_',           # Starts with url_
        r'_url_',           # Contains _url_
        r'_link$',          # Ends with _link
        r'^link_',          # Starts with link_
        r'_href',           # Contains _href
    ]
    
    PHONE_PATTERNS = [
        r'phone',           # Contains 'phone'
        r'telephone',       # Contains 'telephone'
        r'mobile',          # Contains 'mobile'
        r'cellphone',       # Contains 'cellphone'
        r'cell_phone',      # cell_phone format
        r'^tel$',           # Exactly 'tel'
        r'_tel$',           # Ends with _tel
        r'^tel_',           # Starts with tel_
    ]
    
    LONG_TEXT_PATTERNS = [
        r'description',     # Contains 'description'
        r'comment',         # Contains 'comment'
        r'summary',         # Contains 'summary'
        r'content',         # Contains 'content'
        r'message',         # Contains 'message'
        r'^bio$',           # Exactly 'bio'
        r'_bio$',           # Ends with _bio
        r'^bio_',           # Starts with bio_
        r'^notes?$',        # Exactly 'note' or 'notes'
        r'_notes?$',        # Ends with _note or _notes
        r'^notes?_',        # Starts with note_ or notes_
        r'_body$',          # Ends with _body
        r'_detail',         # Contains _detail
    ]
    
    CURRENCY_PATTERNS = [
        r'price',           # Contains 'price'
        r'^cost$',          # Exactly 'cost'
        r'_cost$',          # Ends with _cost
        r'^cost_',          # Starts with cost_
        r'salary',          # Contains 'salary'
        r'wage',            # Contains 'wage'
        r'revenue',         # Contains 'revenue'
        r'budget',          # Contains 'budget'
        r'payment',         # Contains 'payment'
        r'^amount$',        # Exactly 'amount'
        r'_amount$',        # Ends with _amount
        r'^fee$',           # Exactly 'fee'
        r'_fee$',           # Ends with _fee
    ]
    
    PERCENT_PATTERNS = [
        r'percent',         # Contains 'percent' (also matches 'percentage')
        r'^rate$',          # Exactly 'rate'
        r'_rate$',          # Ends with _rate (e.g., conversion_rate)
        r'^ratio$',         # Exactly 'ratio'
        r'_ratio$',         # Ends with _ratio
    ]
    
    DURATION_PATTERNS = [
        r'duration',        # Contains 'duration'
        r'elapsed',         # Contains 'elapsed'
        r'time_spent',      # Contains 'time_spent'
        r'time_taken',      # Contains 'time_taken'
        r'^span$',          # Exactly 'span'
        r'_span$',          # Ends with _span
        r'^interval$',      # Exactly 'interval'
        r'_interval$',      # Ends with _interval
    ]
    
    RATING_PATTERNS = [
        r'rating',          # Contains 'rating' (won't match 'rate' due to 'ing')
        r'^stars?$',        # Exactly 'star' or 'stars'
        r'_stars?$',        # Ends with _star or _stars
        r'^score$',         # Exactly 'score'
        r'_score$',         # Ends with _score
        r'^rank$',          # Exactly 'rank'
        r'_rank$',          # Ends with _rank
        r'_ranking$',       # Ends with _ranking
    ]
    
    @classmethod
    def resolve_field_type(
        cls,
        field_name: str,
        python_type: Type,
        field_info: Optional[FieldInfo] = None,
        explicit_type: Optional[AirtableFieldType] = None
    ) -> AirtableFieldType:
        """
        Resolve Airtable field type from multiple sources
        
        Priority:
        1. Explicit type specification
        2. Field info metadata
        3. Field type detection from field name
        4. Python type mapping
        5. Default fallback
        
        Args:
            field_name: Python field name
            python_type: Python type annotation
            field_info: Pydantic field info
            explicit_type: Explicitly specified Airtable type
            
        Returns:
            Resolved Airtable field type
        """
        # 1. Explicit type takes precedence
        if explicit_type:
            return explicit_type
        
        # 2. Check field info for existing type specification
        if field_info and hasattr(field_info, 'json_schema_extra'):
            extra = field_info.json_schema_extra or {}
            if isinstance(extra, dict) and 'airtable_field_type' in extra:
                return extra['airtable_field_type']
        
        # 3. Type detection from field name (for string types)
        if cls._is_string_type(python_type):
            auto_type = cls._detect_from_field_name(field_name)
            if auto_type:
                return auto_type
        
        # 4. Python type mapping
        base_type = cls._extract_base_type(python_type)
        if base_type in cls.PYTHON_TO_AIRTABLE:
            airtable_type = cls.PYTHON_TO_AIRTABLE[base_type]
            
            # Further refinement for numbers
            if airtable_type == AirtableFieldType.NUMBER:
                return cls._refine_number_type(field_name)
            
            return airtable_type
        
        # 5. Handle enums
        if cls._is_enum_type(python_type):
            return AirtableFieldType.SELECT
        
        # 6. Default fallback
        return AirtableFieldType.SINGLE_LINE_TEXT
    
    @classmethod
    def _is_string_type(cls, python_type: Type) -> bool:
        """Check if type is string-based"""
        base_type = cls._extract_base_type(python_type)
        return base_type == str
    
    @classmethod
    def _is_enum_type(cls, python_type: Type) -> bool:
        """Check if type is enum-based"""
        base_type = cls._extract_base_type(python_type)
        return (isinstance(base_type, type) and 
                issubclass(base_type, Enum))
    
    @classmethod
    def _extract_base_type(cls, python_type: Type) -> Type:
        """
        Extract base type from complex type annotations
        
        Handles:
        - Optional[T] -> T
        - Union[T, None] -> T  
        - List[T] -> list
        - etc.
        """
        # Handle Optional and Union types
        origin = get_origin(python_type)
        if origin is Union:
            args = get_args(python_type)
            non_none_args = [arg for arg in args if arg != type(None)]
            if non_none_args:
                return cls._extract_base_type(non_none_args[0])
        
        # Handle generic types (List, Dict, etc.)
        if origin:
            return origin
        
        return python_type
    
    @classmethod
    def _detect_from_field_name(cls, field_name: str) -> Optional[AirtableFieldType]:
        """
        Field type detection based on field name patterns
        
        Args:
            field_name: Field name to analyze
            
        Returns:
            Detected field type or None
        """
        name_lower = field_name.lower()
        
        # Email detection
        if any(re.search(pattern, name_lower) for pattern in cls.EMAIL_PATTERNS):
            return AirtableFieldType.EMAIL
        
        # URL detection  
        if any(re.search(pattern, name_lower) for pattern in cls.URL_PATTERNS):
            return AirtableFieldType.URL
        
        # Phone detection
        if any(re.search(pattern, name_lower) for pattern in cls.PHONE_PATTERNS):
            return AirtableFieldType.PHONE
        
        # Long text detection
        if any(re.search(pattern, name_lower) for pattern in cls.LONG_TEXT_PATTERNS):
            return AirtableFieldType.LONG_TEXT
        
        return None
    
    @classmethod
    def _refine_number_type(cls, field_name: str) -> AirtableFieldType:
        """
        Refine number type based on field name
        
        Args:
            field_name: Field name to analyze
            
        Returns:
            Refined number field type
        """
        name_lower = field_name.lower()
        
        # Currency detection
        if any(re.search(pattern, name_lower) for pattern in cls.CURRENCY_PATTERNS):
            return AirtableFieldType.CURRENCY
        
        # Percentage detection
        if any(re.search(pattern, name_lower) for pattern in cls.PERCENT_PATTERNS):
            return AirtableFieldType.PERCENT
        
        # Duration detection (for int/float fields named like durations)
        if any(re.search(pattern, name_lower) for pattern in cls.DURATION_PATTERNS):
            return AirtableFieldType.DURATION
        
        # Rating detection (for int fields named like ratings)
        if any(re.search(pattern, name_lower) for pattern in cls.RATING_PATTERNS):
            return AirtableFieldType.RATING
        
        return AirtableFieldType.NUMBER
    
    @classmethod
    def get_field_options(cls, field_type: AirtableFieldType, **kwargs) -> Dict[str, Any]:
        """
        Generate field options for specific Airtable field types
        
        Args:
            field_type: Airtable field type
            **kwargs: Additional options
            
        Returns:
            Field options dictionary
        """
        options = {}
        
        if field_type == AirtableFieldType.CHECKBOX:
            options.update({
                "icon": kwargs.get("icon", "check"),
                "color": kwargs.get("color", "greenBright")
            })
        
        elif field_type == AirtableFieldType.SELECT:
            choices = kwargs.get("choices", [])
            if choices:
                options["choices"] = [{"name": choice} for choice in choices]
        
        elif field_type == AirtableFieldType.MULTI_SELECT:
            choices = kwargs.get("choices", [])
            if choices:
                options["choices"] = [{"name": choice} for choice in choices]
        
        elif field_type == AirtableFieldType.CURRENCY:
            options.update({
                "precision": kwargs.get("precision", 2),
                "symbol": kwargs.get("symbol", "$")
            })
        
        elif field_type == AirtableFieldType.PERCENT:
            options.update({
                "precision": kwargs.get("precision", 1)
            })
        
        elif field_type == AirtableFieldType.DURATION:
            # Duration format options: h:mm, h:mm:ss, h:mm:ss.S, h:mm:ss.SS, h:mm:ss.SSS
            options.update({
                "durationFormat": kwargs.get("duration_format", "h:mm")
            })
        
        elif field_type == AirtableFieldType.RATING:
            # Rating options: max value (1-10), icon (star, heart, thumbs-up, flag, dot)
            options.update({
                "max": kwargs.get("max", 5),
                "icon": kwargs.get("icon", "star"),
                "color": kwargs.get("color", "yellowBright")
            })
        
        elif field_type == AirtableFieldType.LINKED_RECORD:
            # Linked record requires the table ID to link to
            linked_table_id = kwargs.get("linked_table_id")
            if linked_table_id:
                options["linkedTableId"] = linked_table_id
            # Optional: prefer single record link
            if kwargs.get("single_record"):
                options["prefersSingleRecordLink"] = True
            # Optional: inverse link field
            inverse_field = kwargs.get("inverse_link_field_id")
            if inverse_field:
                options["inverseLinkFieldId"] = inverse_field
        
        elif field_type == AirtableFieldType.USER:
            # User/Collaborator field options
            options.update({
                "shouldNotify": kwargs.get("should_notify", False)
            })
        
        elif field_type == AirtableFieldType.BUTTON:
            # Button field options - typically read-only, triggers actions
            label = kwargs.get("label", "Click")
            options.update({
                "label": label
            })
        
        elif field_type == AirtableFieldType.BARCODE:
            # Barcode field - no special options needed for creation
            pass
        
        return options


def airtable_field(
    *,
    field_type: Optional[AirtableFieldType] = None,
    field_name: Optional[str] = None,
    read_only: bool = False,
    choices: Optional[list] = None,
    linked_table_id: Optional[str] = None,
    single_record: bool = False,
    inverse_link_field_id: Optional[str] = None,
    **field_kwargs
) -> Any:
    """
    Streamlined Airtable field with defaults
    
    Args:
        field_type: Explicit Airtable field type (auto-detected if None)
        field_name: Airtable field name (uses Python name if None) 
        read_only: Whether field is read-only
        choices: For select/multi-select fields
        linked_table_id: For LINKED_RECORD fields, the ID of the table to link to
        single_record: For LINKED_RECORD fields, prefer single record link
        inverse_link_field_id: For LINKED_RECORD fields, ID of inverse link field
        **field_kwargs: Additional Pydantic Field() arguments
        
    Returns:
        Pydantic Field with Airtable metadata
    """
    # Build Airtable metadata
    airtable_metadata = {}
    
    if field_type:
        airtable_metadata['airtable_field_type'] = field_type
    
    if field_name:
        airtable_metadata['airtable_field_name'] = field_name
    
    if read_only:
        airtable_metadata['airtable_read_only'] = True
    
    if choices:
        airtable_metadata['airtable_choices'] = choices
    
    # Linked record options
    if linked_table_id:
        airtable_metadata['linked_table_id'] = linked_table_id
    
    if single_record:
        airtable_metadata['single_record'] = True
    
    if inverse_link_field_id:
        airtable_metadata['inverse_link_field_id'] = inverse_link_field_id
    
    # Merge with existing json_schema_extra
    existing_extra = field_kwargs.get('json_schema_extra', {})
    if callable(existing_extra):
        # If it's a function, we can't easily merge, so replace
        field_kwargs['json_schema_extra'] = airtable_metadata
    else:
        # Merge dictionaries
        merged_extra = {**(existing_extra or {}), **airtable_metadata}
        field_kwargs['json_schema_extra'] = merged_extra
    
    return Field(**field_kwargs)
