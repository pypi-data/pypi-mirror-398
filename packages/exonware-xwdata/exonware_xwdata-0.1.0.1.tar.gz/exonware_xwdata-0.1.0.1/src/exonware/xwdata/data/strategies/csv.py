#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/strategies/csv.py

CSV Format Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 15-Nov-2025
"""

from typing import Any, Optional, List, Dict
from pathlib import Path
import csv
import io

from ...base import AFormatStrategy
from ...errors import XWDataStrategyError


class CSVFormatStrategy(AFormatStrategy):
    """
    CSV format strategy.
    
    Supports CSV (Comma-Separated Values) format.
    """
    
    def __init__(self):
        """Initialize CSV format strategy."""
        super().__init__()
        self._name = 'csv'
        self._extensions = ['csv']
    
    @property
    def name(self) -> str:
        """Format name."""
        return self._name
    
    @property
    def extensions(self) -> list[str]:
        """Supported file extensions."""
        return [f".{ext}" for ext in self._extensions]
    
    @property
    def mime_types(self) -> list[str]:
        """Supported MIME types."""
        return ["text/csv", "application/csv"]
    
    def can_handle(self, path: Optional[Path] = None, mime_type: Optional[str] = None) -> bool:
        """Check if this strategy can handle the given path or MIME type."""
        if path:
            return path.suffix.lower() == ".csv"
        if mime_type:
            return mime_type.lower() in self.mime_types
        return False
    
    async def load(self, path: Path, **options) -> Any:
        """
        Load CSV file.
        
        Args:
            path: Path to CSV file
            **options: Options (delimiter, header, etc.)
            
        Returns:
            Loaded data (list of dicts if header=True, list of lists otherwise)
            
        Raises:
            XWDataStrategyError: If loading fails
        """
        delimiter = options.get('delimiter', ',')
        quotechar = options.get('quotechar', '"')
        header = options.get('header', True)
        
        try:
            with path.open('r', encoding='utf-8') as f:
                if header:
                    reader = csv.DictReader(f, delimiter=delimiter, quotechar=quotechar)
                    return list(reader)
                else:
                    reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
                    return list(reader)
        except Exception as e:
            raise XWDataStrategyError(f"Failed to load CSV file: {e}") from e
    
    async def save(self, data: Any, path: Path, **options) -> None:
        """
        Save data to CSV file.
        
        Args:
            data: Data to save (list of dicts or list of lists)
            path: Path to output file
            **options: Options (delimiter, header, etc.)
            
        Raises:
            XWDataStrategyError: If saving fails
        """
        delimiter = options.get('delimiter', ',')
        quotechar = options.get('quotechar', '"')
        header = options.get('header', True)
        
        try:
            with path.open('w', encoding='utf-8', newline='') as f:
                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], dict):
                        # List of dicts - use DictWriter
                        fieldnames = list(data[0].keys())
                        writer = csv.DictWriter(
                            f,
                            fieldnames=fieldnames,
                            delimiter=delimiter,
                            quotechar=quotechar
                        )
                        if header:
                            writer.writeheader()
                        writer.writerows(data)
                    else:
                        # List of lists - use writer
                        writer = csv.writer(
                            f,
                            delimiter=delimiter,
                            quotechar=quotechar
                        )
                        writer.writerows(data)
                elif isinstance(data, dict):
                    # Single dict
                    writer = csv.DictWriter(
                        f,
                        fieldnames=list(data.keys()),
                        delimiter=delimiter,
                        quotechar=quotechar
                    )
                    if header:
                        writer.writeheader()
                    writer.writerow(data)
                else:
                    raise ValueError(f"Unsupported data type for CSV: {type(data)}")
        except Exception as e:
            raise XWDataStrategyError(f"Failed to save CSV file: {e}") from e
    
    async def parse(self, content: str, **options) -> Any:
        """
        Parse CSV content.
        
        Args:
            content: CSV content string
            **options: Options (delimiter, header, etc.)
            
        Returns:
            Parsed data
        """
        delimiter = options.get('delimiter', ',')
        quotechar = options.get('quotechar', '"')
        header = options.get('header', True)
        
        try:
            input_stream = io.StringIO(content)
            if header:
                reader = csv.DictReader(input_stream, delimiter=delimiter, quotechar=quotechar)
                return list(reader)
            else:
                reader = csv.reader(input_stream, delimiter=delimiter, quotechar=quotechar)
                return list(reader)
        except Exception as e:
            raise XWDataStrategyError(f"Failed to parse CSV: {e}") from e
    
    async def serialize(self, data: Any, **options) -> str:
        """
        Serialize data to CSV.
        
        Args:
            data: Data to serialize
            **options: Options (delimiter, header, etc.)
            
        Returns:
            CSV string
        """
        delimiter = options.get('delimiter', ',')
        quotechar = options.get('quotechar', '"')
        header = options.get('header', True)
        
        try:
            output = io.StringIO()
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    fieldnames = list(data[0].keys())
                    writer = csv.DictWriter(
                        output,
                        fieldnames=fieldnames,
                        delimiter=delimiter,
                        quotechar=quotechar
                    )
                    if header:
                        writer.writeheader()
                    writer.writerows(data)
                else:
                    writer = csv.writer(output, delimiter=delimiter, quotechar=quotechar)
                    writer.writerows(data)
            elif isinstance(data, dict):
                writer = csv.DictWriter(
                    output,
                    fieldnames=list(data.keys()),
                    delimiter=delimiter,
                    quotechar=quotechar
                )
                if header:
                    writer.writeheader()
                writer.writerow(data)
            else:
                raise ValueError(f"Unsupported data type for CSV: {type(data)}")
            
            return output.getvalue()
        except Exception as e:
            raise XWDataStrategyError(f"Failed to serialize CSV: {e}") from e

