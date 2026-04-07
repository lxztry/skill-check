#!/usr/bin/env python3
"""
File Processor - Example file processing script
"""

import os
import json
import csv
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of file processing"""
    success: bool
    input_path: str
    output_path: Optional[str] = None
    records_processed: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class FileProcessor:
    """Example file processor with multiple format support"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.encoding = self.config.get('encoding', 'utf-8')
        self.buffer_size = self.config.get('buffer_size', 8192)
        self.error_handling = self.config.get('error_handling', 'skip')
        self.output_dir = Path(self.config.get('output_dir', './output'))
        
        # Create output directory if needed
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process(self, input_path: Union[str, Path]) -> ProcessingResult:
        """Process a single file based on extension"""
        input_path = Path(input_path)
        
        if not input_path.exists():
            return ProcessingResult(
                success=False,
                input_path=str(input_path),
                error=f"File not found: {input_path}"
            )
        
        ext = input_path.suffix.lower()
        
        try:
            if ext == '.txt':
                return self._process_text(input_path)
            elif ext == '.csv':
                return self._process_csv(input_path)
            elif ext == '.json':
                return self._process_json(input_path)
            else:
                return ProcessingResult(
                    success=False,
                    input_path=str(input_path),
                    error=f"Unsupported format: {ext}"
                )
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return ProcessingResult(
                success=False,
                input_path=str(input_path),
                error=str(e)
            )
    
    def _process_text(self, input_path: Path) -> ProcessingResult:
        """Process text file"""
        with open(input_path, 'r', encoding=self.encoding) as f:
            content = f.read()
        
        # Example: count lines, words, chars
        lines = content.split('\n')
        words = content.split()
        
        metadata = {
            'lines': len(lines),
            'words': len(words),
            'chars': len(content),
            'size_bytes': input_path.stat().st_size
        }
        
        # Example output: create summary file
        output_path = self.output_dir / f"{input_path.stem}_summary.txt"
        with open(output_path, 'w', encoding=self.encoding) as f:
            f.write(f"File: {input_path.name}\n")
            f.write(f"Lines: {metadata['lines']}\n")
            f.write(f"Words: {metadata['words']}\n")
            f.write(f"Characters: {metadata['chars']}\n")
        
        return ProcessingResult(
            success=True,
            input_path=str(input_path),
            output_path=str(output_path),
            records_processed=metadata['lines'],
            metadata=metadata
        )
    
    def _process_csv(self, input_path: Path) -> ProcessingResult:
        """Process CSV file"""
        records = []
        
        with open(input_path, 'r', encoding=self.encoding, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        
        # Example: convert to JSON
        output_path = self.output_dir / f"{input_path.stem}.json"
        with open(output_path, 'w', encoding=self.encoding) as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        
        return ProcessingResult(
            success=True,
            input_path=str(input_path),
            output_path=str(output_path),
            records_processed=len(records),
            metadata={'record_count': len(records), 'columns': list(records[0].keys()) if records else []}
        )
    
    def _process_json(self, input_path: Path) -> ProcessingResult:
        """Process JSON file"""
        with open(input_path, 'r', encoding=self.encoding) as f:
            data = json.load(f)
        
        # Example: flatten and save as CSV
        if isinstance(data, list) and data and isinstance(data[0], dict):
            output_path = self.output_dir / f"{input_path.stem}.csv"
            
            with open(output_path, 'w', encoding=self.encoding, newline='') as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
            
            return ProcessingResult(
                success=True,
                input_path=str(input_path),
                output_path=str(output_path),
                records_processed=len(data),
                metadata={'record_count': len(data), 'keys': list(data[0].keys())}
            )
        
        return ProcessingResult(
            success=True,
            input_path=str(input_path),
            records_processed=1,
            metadata={'type': type(data).__name__}
        )
    
    def batch_process(self, input_dir: Union[str, Path], pattern: str = "*") -> List[ProcessingResult]:
        """Batch process files matching pattern"""
        input_dir = Path(input_dir)
        results = []
        
        for path in input_dir.glob(pattern):
            if path.is_file():
                result = self.process(path)
                results.append(result)
        
        return results


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='File processor')
    parser.add_argument('--input', help='Input file path')
    parser.add_argument('--dir', help='Input directory for batch processing')
    parser.add_argument('--pattern', default='*', help='File pattern for batch (e.g., *.txt)')
    parser.add_argument('--config', help='Config YAML file')
    
    args = parser.parse_args()
    
    config = {}
    if args.config:
        import yaml
        with open(args.config) as f:
            config = yaml.safe_load(f) or {}
    
    processor = FileProcessor(config)
    
    if args.input:
        result = processor.process(args.input)
        print(json.dumps(result.__dict__, indent=2, default=str))
    elif args.dir:
        results = processor.batch_process(args.dir, args.pattern)
        for r in results:
            status = "✓" if r.success else "✗"
            print(f"{status} {r.input_path} -> {r.output_path or r.error}")
    else:
        print("Specify --input or --dir")
