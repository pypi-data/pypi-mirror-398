"""
Main converter module for JSON to CSV conversion.

This module provides the core JSONConverter class with methods for converting
JSON data to CSV format with various options and configurations.
"""

import json
import csv
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from .exceptions import ConversionError, FileNotFoundError as CustomFileNotFoundError
from .utils import flatten_json, detect_delimiter
from .validator import DataValidator


class JSONConverter:
    """
    A comprehensive JSON to CSV converter with advanced features.
    
    This class provides methods to convert JSON data to CSV format with support
    for nested JSON, custom delimiters, data validation, and various output options.
    
    Attributes:
        validator (DataValidator): Data validation instance
        
    Example:
        >>> from json2csv_pro import JSONConverter
        >>> converter = JSONConverter()
        >>> data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        >>> converter.convert_to_csv(data=data, output_file="output.csv")
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the JSONConverter.
        
        Args:
            **kwargs: Optional configuration parameters
                - validate (bool): Enable data validation (default: True)
                - strict_mode (bool): Enable strict validation (default: False)
        
        Example:
            >>> converter = JSONConverter(validate=True, strict_mode=False)
        """
        self.validator = DataValidator()
        self.validate = kwargs.get('validate', True)
        self.strict_mode = kwargs.get('strict_mode', False)
    
    def convert_to_csv(self, **kwargs) -> Optional[str]:
        """
        Convert JSON data to CSV format.
        
        This is the main conversion method that handles various input types
        and converts them to CSV format with customizable options.
        
        Args:
            **kwargs: Conversion parameters
                - data (Union[List[Dict], Dict, str]): JSON data or file path
                - output_file (str): Output CSV file path (optional)
                - delimiter (str): CSV delimiter (default: ',')
                - flatten_nested (bool): Flatten nested JSON (default: True)
                - max_depth (int): Maximum depth for flattening (default: 10)
                - encoding (str): File encoding (default: 'utf-8')
                - include_index (bool): Include row index (default: False)
                - custom_headers (List[str]): Custom column headers (optional)
        
        Returns:
            Optional[str]: CSV string if output_file not specified, None otherwise
        
        Raises:
            ConversionError: If conversion fails
            ValidationError: If data validation fails
            
        Example:
            >>> converter = JSONConverter()
            >>> data = [
            ...     {"name": "John", "age": 30, "address": {"city": "NYC"}},
            ...     {"name": "Jane", "age": 25, "address": {"city": "LA"}}
            ... ]
            >>> converter.convert_to_csv(
            ...     data=data,
            ...     output_file="output.csv",
            ...     flatten_nested=True,
            ...     delimiter=','
            ... )
        """
        data = kwargs.get('data')
        output_file = kwargs.get('output_file')
        delimiter = kwargs.get('delimiter', ',')
        flatten_nested = kwargs.get('flatten_nested', True)
        max_depth = kwargs.get('max_depth', 10)
        encoding = kwargs.get('encoding', 'utf-8')
        include_index = kwargs.get('include_index', False)
        custom_headers = kwargs.get('custom_headers')
        
        try:
            # Load data if it's a file path
            if isinstance(data, str):
                data = self.load_json_file(file_path=data, encoding=encoding)
            
            # Ensure data is a list
            if isinstance(data, dict):
                data = [data]
            
            # Validate data
            if self.validate:
                self.validator.validate_data(data=data, strict=self.strict_mode)
            
            # Flatten nested JSON if required
            if flatten_nested:
                data = [flatten_json(item, max_depth=max_depth) for item in data]
            
            # Get headers
            headers = custom_headers if custom_headers else self._extract_headers(data)
            
            if include_index:
                headers = ['index'] + headers
            
            # Convert to CSV
            if output_file:
                self._write_csv_file(
                    data=data,
                    headers=headers,
                    output_file=output_file,
                    delimiter=delimiter,
                    encoding=encoding,
                    include_index=include_index
                )
                return None
            else:
                return self._generate_csv_string(
                    data=data,
                    headers=headers,
                    delimiter=delimiter,
                    include_index=include_index
                )
        
        except Exception as e:
            raise ConversionError(f"Conversion failed: {str(e)}")
    
    def load_json_file(self, **kwargs) -> Union[List[Dict], Dict]:
        """
        Load JSON data from a file.
        
        Args:
            **kwargs: Loading parameters
                - file_path (str): Path to JSON file
                - encoding (str): File encoding (default: 'utf-8')
        
        Returns:
            Union[List[Dict], Dict]: Loaded JSON data
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ConversionError: If JSON parsing fails
            
        Example:
            >>> converter = JSONConverter()
            >>> data = converter.load_json_file(file_path="data.json")
        """
        file_path = kwargs.get('file_path')
        encoding = kwargs.get('encoding', 'utf-8')
        
        path = Path(file_path)
        if not path.exists():
            raise CustomFileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ConversionError(f"Invalid JSON file: {str(e)}")
    
    def convert_batch(self, **kwargs) -> None:
        """
        Convert multiple JSON files to CSV in batch.
        
        Args:
            **kwargs: Batch conversion parameters
                - input_files (List[str]): List of input JSON file paths
                - output_dir (str): Output directory for CSV files
                - **other: Additional parameters for convert_to_csv
        
        Raises:
            ConversionError: If batch conversion fails
            
        Example:
            >>> converter = JSONConverter()
            >>> converter.convert_batch(
            ...     input_files=["file1.json", "file2.json"],
            ...     output_dir="output/",
            ...     flatten_nested=True
            ... )
        """
        input_files = kwargs.get('input_files', [])
        output_dir = kwargs.get('output_dir', '.')
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        conversion_params = {k: v for k, v in kwargs.items() 
                           if k not in ['input_files', 'output_dir']}
        
        for input_file in input_files:
            input_path = Path(input_file)
            output_file = output_path / f"{input_path.stem}.csv"
            
            self.convert_to_csv(
                data=input_file,
                output_file=str(output_file),
                **conversion_params
            )
    
    def preview_conversion(self, **kwargs) -> str:
        """
        Preview CSV output without writing to file.
        
        Args:
            **kwargs: Preview parameters
                - data (Union[List[Dict], Dict, str]): JSON data
                - rows (int): Number of rows to preview (default: 5)
                - **other: Additional parameters for convert_to_csv
        
        Returns:
            str: Preview of CSV output
            
        Example:
            >>> converter = JSONConverter()
            >>> data = [{"name": "John", "age": 30}] * 10
            >>> preview = converter.preview_conversion(data=data, rows=3)
            >>> print(preview)
        """
        rows = kwargs.get('rows', 5)
        data = kwargs.get('data')
        
        # Load and process data
        if isinstance(data, str):
            data = self.load_json_file(file_path=data)
        
        if isinstance(data, dict):
            data = [data]
        
        # Limit rows for preview
        preview_data = data[:rows]
        
        # Remove 'rows' and 'data' from kwargs before passing
        conversion_params = {k: v for k, v in kwargs.items() 
                           if k not in ['rows', 'data', 'output_file']}
        
        return self.convert_to_csv(data=preview_data, **conversion_params)
    
    def _extract_headers(self, data: List[Dict]) -> List[str]:
        """Extract all unique headers from data."""
        headers = set()
        for item in data:
            headers.update(item.keys())
        return sorted(list(headers))
    
    def _write_csv_file(self, **kwargs) -> None:
        """Write data to CSV file."""
        data = kwargs['data']
        headers = kwargs['headers']
        output_file = kwargs['output_file']
        delimiter = kwargs['delimiter']
        encoding = kwargs['encoding']
        include_index = kwargs['include_index']
        
        with open(output_file, 'w', newline='', encoding=encoding) as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=delimiter)
            writer.writeheader()
            
            for idx, row in enumerate(data):
                if include_index:
                    row['index'] = idx
                writer.writerow(row)
    
    def _generate_csv_string(self, **kwargs) -> str:
        """Generate CSV string from data."""
        import io
        
        data = kwargs['data']
        headers = kwargs['headers']
        delimiter = kwargs['delimiter']
        include_index = kwargs['include_index']
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers, delimiter=delimiter)
        writer.writeheader()
        
        for idx, row in enumerate(data):
            if include_index:
                row['index'] = idx
            writer.writerow(row)
        
        return output.getvalue()