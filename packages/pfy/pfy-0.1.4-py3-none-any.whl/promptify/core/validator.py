"""Input validation logic"""
from pathlib import Path
from promptify.utils.errors import (
    ValidationError,
    query_too_long_error,
    file_not_found_error
)

class InputValidator:
    """Validates CLI inputs"""
    
    @staticmethod
    def validate_query(query: str) -> str:
        """Validate and clean query"""
        if not query or not query.strip():
            raise ValidationError(
                "Query cannot be empty",
                hint="Provide a query as an argument or use --file to read from a file"
            )
        
        cleaned = query.strip()
        
        if len(cleaned) > 5000:
            raise query_too_long_error(len(cleaned))
        
        return cleaned
    
    @staticmethod
    def validate_file(file_path: Path) -> str:
        """Validate and read file"""
        if not file_path.exists():
            raise file_not_found_error(str(file_path))
        
        try:
            content = file_path.read_text(encoding='utf-8')
            return InputValidator.validate_query(content)
        except UnicodeDecodeError:
            raise ValidationError(
                f"Cannot read file {file_path}: Invalid encoding",
                hint="Ensure the file is UTF-8 encoded text"
            )
        except Exception as e:
            raise ValidationError(
                f"Error reading file: {e}",
                hint="Check file permissions and format"
            )
    
    @staticmethod
    def validate_api_key(api_key: str) -> None:
        """Validate API key exists"""
        from promptify.utils.errors import api_key_missing_error
        
        if not api_key:
            raise api_key_missing_error()
