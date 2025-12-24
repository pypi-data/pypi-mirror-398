"""Form handling and validation"""
import threading
from typing import Dict, List, Tuple, Optional, Callable, Union
from ..input.input import InputField, SelectField, CheckboxField


class Form:
    """Thread-safe form with validation"""
    
    def __init__(self, name: str = "Form") -> None:
        """Initialize form
        
        Args:
            name: Form name
        """
        self.name: str = name
        self.fields: Dict[str, Union[InputField, SelectField, CheckboxField]] = {}
        self.field_order: List[str] = []
        self.current_field_idx: int = 0
        self.lock: threading.RLock = threading.RLock()
        self.on_submit: Optional[Callable] = None
    
    def add_field(self, field: Union[InputField, SelectField, CheckboxField]) -> None:
        """Add field to form (thread-safe)
        
        Args:
            field: Field to add
        """
        with self.lock:
            self.fields[field.name] = field
            self.field_order.append(field.name)
            if len(self.field_order) == 1:
                self._focus_field(0)
    
    def _focus_field(self, index: int) -> None:
        """Focus field at index (internal, no lock)"""
        # Unfocus current
        current_field_name = self.field_order[self.current_field_idx]
        self.fields[current_field_name].set_focus(False)
        
        # Focus new
        self.current_field_idx = max(0, min(index, len(self.field_order) - 1))
        current_field_name = self.field_order[self.current_field_idx]
        self.fields[current_field_name].set_focus(True)
    
    def next_field(self) -> None:
        """Focus next field (thread-safe)"""
        with self.lock:
            if self.field_order:
                self._focus_field(self.current_field_idx + 1)
    
    def previous_field(self) -> None:
        """Focus previous field (thread-safe)"""
        with self.lock:
            if self.field_order:
                self._focus_field(self.current_field_idx - 1)
    
    def get_current_field(self) -> Optional[Union[InputField, SelectField, CheckboxField]]:
        """Get currently focused field (thread-safe)"""
        with self.lock:
            if self.field_order:
                field_name = self.field_order[self.current_field_idx]
                return self.fields[field_name]
            return None
    
    def get_field(self, name: str) -> Optional[Union[InputField, SelectField, CheckboxField]]:
        """Get field by name (thread-safe)
        
        Args:
            name: Field name
            
        Returns:
            Field or None
        """
        with self.lock:
            return self.fields.get(name)
    
    def validate(self) -> Tuple[bool, Dict[str, str]]:
        """Validate all fields (thread-safe)
        
        Returns:
            (is_valid, errors_dict)
        """
        with self.lock:
            errors = {}
            
            for field_name, field in self.fields.items():
                is_valid, error_msg = field.validate()
                if not is_valid:
                    errors[field_name] = error_msg
            
            return len(errors) == 0, errors
    
    def get_values(self) -> Dict[str, str]:
        """Get all field values (thread-safe)
        
        Returns:
            Dict of field_name -> value
        """
        with self.lock:
            values = {}
            
            for field_name, field in self.fields.items():
                if isinstance(field, InputField):
                    values[field_name] = field.get_value()
                elif isinstance(field, SelectField):
                    values[field_name] = field.get_value()
                elif isinstance(field, CheckboxField):
                    values[field_name] = str(field.is_checked())
            
            return values
    
    def set_values(self, values: Dict[str, str]) -> None:
        """Set multiple field values (thread-safe)
        
        Args:
            values: Dict of field_name -> value
        """
        with self.lock:
            for field_name, value in values.items():
                if field_name in self.fields:
                    field = self.fields[field_name]
                    if isinstance(field, InputField):
                        field.set_value(value)
                    elif isinstance(field, SelectField):
                        try:
                            field.set_option(field.options.index(value))
                        except ValueError:
                            pass
                    elif isinstance(field, CheckboxField):
                        field.set_checked(value.lower() in ("true", "1", "yes"))
    
    def reset(self) -> None:
        """Reset all fields (thread-safe)"""
        with self.lock:
            for field in self.fields.values():
                if isinstance(field, InputField):
                    field.clear()
                elif isinstance(field, SelectField):
                    field.set_option(0)
                elif isinstance(field, CheckboxField):
                    field.set_checked(False)
    
    def submit(self) -> Optional[Dict[str, str]]:
        """Submit form with validation (thread-safe)
        
        Returns:
            Form values if valid, None otherwise
        """
        is_valid, errors = self.validate()
        
        if not is_valid:
            return None
        
        values = self.get_values()
        
        if self.on_submit:
            self.on_submit(values)
        
        return values
    
    def get_field_count(self) -> int:
        """Get number of fields (thread-safe)"""
        with self.lock:
            return len(self.fields)
    
    def get_current_field_index(self) -> int:
        """Get current field index (thread-safe)"""
        with self.lock:
            return self.current_field_idx


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
