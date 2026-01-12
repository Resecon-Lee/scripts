"""
title: DIDE Complete Suite
author: Lehem Felican Jr - Resolution Economics
author_url: https://resecon.com
version: 4.0.0
license: MIT
description: Complete DocuInsight Data Engine (DIDE) - Unified tool combining file handling, core analysis, advanced statistics, and intelligence reporting for comprehensive data analysis
requirements: pandas, openpyxl, xlrd
"""

from pydantic import BaseModel, Field
from typing import Callable, Any, Optional, List, Dict, Tuple
import pandas as pd
import io
import base64
import json
import re

# Global storage for dataframes (persists across function calls)
_GLOBAL_DATAFRAMES = {}
_GLOBAL_METADATA = {}
_GLOBAL_LOGS = {}
_GLOBAL_RAW_FILES = {}  # Store raw file content and paths
_GLOBAL_ANALYSIS_HISTORY = {}  # Track analysis history for audit trail


class Tools:
    """
    DIDE Complete Suite - DocuInsight Data Engine

    Comprehensive data analysis tool combining:
    - File handling & parsing (CSV, Excel, key-value)
    - Core analysis (query, filter, count, statistics)
    - Advanced statistics (trends, correlations, anomalies)
    - Intelligence reporting (summaries, risk assessment, key extraction)
    """

    class Valves(BaseModel):
        """Configuration options"""

        MAX_FILE_SIZE_MB: int = Field(default=50, description="Maximum file size in MB")
        MAX_ROWS_DISPLAY: int = Field(
            default=100, description="Maximum number of rows to display"
        )
        AUTO_FIX_ERRORS: bool = Field(
            default=True, description="Automatically attempt to fix malformed files"
        )
        SKIP_BAD_ROWS: bool = Field(
            default=True, description="Skip malformed rows instead of failing"
        )
        MAX_ERROR_ROWS: int = Field(
            default=1000, description="Maximum number of error rows to report"
        )

    def __init__(self):
        self.valves = self.Valves()
        # Use global storage instead of instance variables
        self.dataframes = _GLOBAL_DATAFRAMES
        self.file_metadata = _GLOBAL_METADATA
        self.parsing_logs = _GLOBAL_LOGS
        self.raw_files = _GLOBAL_RAW_FILES
        self.analysis_history = _GLOBAL_ANALYSIS_HISTORY

    async def extract_and_store_file(
        self,
        __files__: List[dict] = [],
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Extract and store raw file content without processing.
        This is a separate function that just handles file extraction and storage.

        Args:
            __files__: Files uploaded through Open WebUI interface
            file_id: Identifier for storing the file (default: "default")

        Returns:
            str: File extraction details and available processing options
        """
        try:
            if not __files__ or len(__files__) == 0:
                return "❌ No files uploaded. Please attach a file to your message."

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Extracting file information...",
                            "done": False,
                        },
                    }
                )

            # Extract file data
            file_data = __files__[0]

            # Get filename
            filename = file_data.get(
                "name", file_data.get("file", {}).get("filename", "uploaded_file")
            )
            file_ext = filename.lower().split(".")[-1] if "." in filename else "unknown"

            # Get file content
            file_content = None
            content_source = "unknown"

            if "file" in file_data and "data" in file_data["file"]:
                file_content = file_data["file"]["data"].get("content")
                content_source = "file.data.content"
            if not file_content and "content" in file_data:
                file_content = file_data["content"]
                content_source = "direct content field"

            if not file_content:
                return f"❌ Could not extract file content.\n\n**Available fields:** {list(file_data.keys())}"

            # Decode file content
            file_bytes = None
            encoding_method = "unknown"

            if isinstance(file_content, str):
                try:
                    file_bytes = base64.b64decode(file_content)
                    encoding_method = "base64 decoded"
                except:
                    file_bytes = file_content.encode("utf-8")
                    encoding_method = "UTF-8 encoded string"
            else:
                file_bytes = file_content
                encoding_method = "raw bytes"

            # Store raw file information
            self.raw_files[file_id] = {
                "filename": filename,
                "extension": file_ext,
                "content_bytes": file_bytes,
                "content_source": content_source,
                "encoding_method": encoding_method,
                "size_bytes": len(file_bytes),
                "size_mb": len(file_bytes) / (1024 * 1024),
                "file_data_structure": list(file_data.keys()),
            }

            # Generate detailed report
            result = f"✅ **File Extracted and Stored Successfully!**\n\n"
            result += f"📁 **File Information:**\n"
            result += f"- **Filename:** {filename}\n"
            result += f"- **Extension:** .{file_ext}\n"
            result += f"- **Size:** {len(file_bytes):,} bytes ({len(file_bytes)/(1024*1024):.2f} MB)\n"
            result += f"- **File ID:** `{file_id}`\n\n"

            result += f"🔍 **Extraction Details:**\n"
            result += f"- **Content source:** {content_source}\n"
            result += f"- **Encoding method:** {encoding_method}\n"
            result += f"- **Available data fields:** {', '.join(file_data.keys())}\n\n"

            # Show first 200 bytes preview
            try:
                preview_text = file_bytes[:200].decode("utf-8", errors="replace")
                result += f"📄 **Content Preview (first 200 bytes):**\n```\n{preview_text}\n```\n\n"
            except:
                result += (
                    f"📄 **Content Preview:** Binary data (cannot display as text)\n\n"
                )

            # Suggest next steps
            result += f"🎯 **Next Steps - Choose a processing method:**\n\n"
            result += f"1. **Auto-analyze:** `analyze_uploaded_file()` - Smart detection & parsing\n"
            result += f"2. **Direct processing:** Use `process_stored_file('{file_id}')` - Process without re-upload\n"
            result += f"3. **Manual inspection:** Check the preview above to verify format\n\n"

            result += f"💡 **File is now stored and ready for processing!**\n"
            result += f"The file content is cached in memory with ID: `{file_id}`"

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "File extracted successfully!",
                            "done": True,
                        },
                    }
                )

            return result

        except Exception as e:
            return f"❌ Error extracting file: {str(e)}"

    async def process_stored_file(
        self,
        file_id: str = "default",
        force_format: Optional[str] = None,
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Process a previously stored file using the extracted raw content.
        This allows re-processing without re-uploading.

        Args:
            file_id: Identifier of the stored file (default: "default")
            force_format: Force a specific format ('csv', 'excel', 'key-value') or None for auto-detect

        Returns:
            str: Processing results
        """
        try:
            # Check if file exists
            if file_id not in self.raw_files:
                available = list(self.raw_files.keys())
                return f"❌ No stored file with ID '{file_id}'.\n\n**Available IDs:** {', '.join(available) if available else 'None'}\n\n💡 Use `extract_and_store_file()` first to store a file."

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Processing stored file...",
                            "done": False,
                        },
                    }
                )

            # Get stored file
            stored_file = self.raw_files[file_id]
            filename = stored_file["filename"]
            file_bytes = stored_file["content_bytes"]

            # Detect or use forced format
            if force_format:
                format_info = {
                    "format": force_format,
                    "confidence": 1.0,
                    "details": f"Format forced by user: {force_format}",
                }
            else:
                format_info = self._detect_file_format(filename, file_bytes)

            # Parse based on format
            df = None
            warnings = []
            skipped_rows = []

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Parsing as {format_info['format']}...",
                            "done": False,
                        },
                    }
                )

            try:
                if format_info["format"] == "excel":
                    df, warnings = self._parse_excel(file_bytes, filename)

                elif format_info["format"] == "csv":
                    df, warnings, skipped_rows = self._parse_csv_robust(
                        file_bytes, filename
                    )

                elif format_info["format"] == "key-value":
                    df, warnings = self._parse_key_value(file_bytes, filename)

                else:
                    warnings.append("⚠️ Unknown format, attempting CSV parsing...")
                    df, csv_warnings, skipped_rows = self._parse_csv_robust(
                        file_bytes, filename
                    )
                    warnings.extend(csv_warnings)

            except Exception as parse_error:
                return f"❌ **Parsing Failed**\n\n**File:** {filename}\n**Format:** {format_info['format']}\n**Error:** {str(parse_error)}\n\n💡 Try using `force_format` parameter:\n- `process_stored_file('{file_id}', 'csv')`\n- `process_stored_file('{file_id}', 'excel')`"

            if df is None or len(df) == 0:
                return f"❌ Parsing resulted in empty dataset.\n\n💡 Try a different format or check the file content."

            # Store dataframe (this is what makes it available to other functions)
            self.dataframes[file_id] = df

            # Store metadata
            self.file_metadata[file_id] = {
                "filename": filename,
                "format": format_info["format"],
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "warnings": warnings,
                "skipped_rows": len(skipped_rows),
            }

            # Store parsing log
            self.parsing_logs[file_id] = {
                "format_detection": format_info,
                "warnings": warnings,
                "skipped_rows": skipped_rows,
            }

            # Generate result
            result = f"✅ **File Processed Successfully!**\n\n"
            result += f"📁 **File:** {filename}\n"
            result += f"🔍 **Format:** {format_info['format'].upper()} ({format_info['details']})\n"
            result += f"📊 **Result:** {len(df):,} rows × {len(df.columns)} columns\n\n"

            if warnings:
                result += f"⚠️ **Processing notes:**\n"
                for warning in warnings:
                    result += f"- {warning}\n"
                result += "\n"

            if skipped_rows:
                result += (
                    f"⚠️ **Data Quality:** {len(skipped_rows)} rows skipped/fixed\n\n"
                )

            result += f"📋 **Columns:** {', '.join(list(df.columns)[:10])}"
            if len(df.columns) > 10:
                result += f"... ({len(df.columns)} total)"
            result += "\n\n"

            result += f"📄 **Preview:**\n\n"
            result += df.head(3).to_markdown(index=False)

            result += f"\n\n✅ **Data is now available to all analysis functions!**\n"
            result += f"Use file_id `{file_id}` for:\n"
            result += f"- query_data()\n"
            result += f"- count_by_column()\n"
            result += f"- get_statistics()\n"
            result += f"- All other analysis functions"

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "Processing complete!", "done": True},
                    }
                )

            return result

        except Exception as e:
            return f"❌ Error processing file: {str(e)}"

    async def list_stored_files(
        self, __user__: dict = {}, __event_emitter__: Callable[[dict], Any] = None
    ) -> str:
        """
        List all files currently stored in memory (both raw and processed).

        Returns:
            str: List of stored files with their status
        """
        try:
            result = f"📦 **Stored Files in Memory**\n\n"

            # Check raw files
            if not self.raw_files and not self.dataframes:
                return f"❌ No files currently stored in memory.\n\n💡 Upload a file using `extract_and_store_file()` or `analyze_uploaded_file()`"

            # Show raw files
            if self.raw_files:
                result += f"**📁 Raw Files (extracted but not processed):**\n"
                for file_id, file_info in self.raw_files.items():
                    result += f"\n**ID:** `{file_id}`\n"
                    result += f"- Filename: {file_info['filename']}\n"
                    result += f"- Size: {file_info['size_mb']:.2f}MB\n"
                    result += f"- Extension: .{file_info['extension']}\n"

                    # Check if processed
                    if file_id in self.dataframes:
                        result += f"- Status: ✅ **Processed** ({self.file_metadata[file_id]['rows']:,} rows loaded)\n"
                    else:
                        result += f"- Status: ⚠️ **Not processed yet** - Use `process_stored_file('{file_id}')`\n"
                result += "\n"

            # Show processed dataframes
            if self.dataframes:
                result += f"**📊 Processed Dataframes (ready for analysis):**\n"
                for file_id, df in self.dataframes.items():
                    meta = self.file_metadata.get(file_id, {})
                    result += f"\n**ID:** `{file_id}`\n"
                    result += f"- Filename: {meta.get('filename', 'Unknown')}\n"
                    result += f"- Format: {meta.get('format', 'Unknown')}\n"
                    result += (
                        f"- Dimensions: {len(df):,} rows × {len(df.columns)} columns\n"
                    )
                    result += f"- Status: ✅ **Ready for analysis**\n"
                result += "\n"

            result += f"💡 **Available Commands:**\n"
            result += f"- Analyze: `analyze_uploaded_file()`\n"
            result += f"- Process: `process_stored_file('file_id')`\n"
            result += f"- Verify: `verify_data_loaded('file_id')`\n"
            result += f"- Query: Use any analysis function with the file_id"

            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def _detect_file_format(self, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Intelligently detect file format and structure

        Returns:
            dict: {
                'format': 'csv' | 'excel' | 'key-value' | 'unknown',
                'confidence': float (0-1),
                'details': str
            }
        """
        file_ext = filename.lower().split(".")[-1] if "." in filename else ""

        # Check by extension first
        if file_ext in ["xlsx", "xls"]:
            return {
                "format": "excel",
                "confidence": 0.95,
                "details": f"Excel file detected by .{file_ext} extension",
            }

        # For CSV or unknown, analyze content
        try:
            # Try to decode first 5000 bytes
            sample = file_bytes[:5000].decode("utf-8", errors="replace")
            lines = sample.split("\n")[:20]

            # Check for key-value format
            kv_pattern = re.compile(r"^[^:]+:\s*.+$")
            kv_matches = sum(1 for line in lines if kv_pattern.match(line.strip()))

            if kv_matches > len(lines) * 0.7:
                return {
                    "format": "key-value",
                    "confidence": 0.9,
                    "details": f"Key-value format detected ({kv_matches}/{len(lines)} lines match pattern)",
                }

            # Check for CSV format
            comma_count = sample.count(",")
            semicolon_count = sample.count(";")
            tab_count = sample.count("\t")

            if comma_count > semicolon_count and comma_count > tab_count:
                return {
                    "format": "csv",
                    "confidence": 0.85,
                    "details": "CSV format detected (comma-separated)",
                }
            elif semicolon_count > comma_count:
                return {
                    "format": "csv",
                    "confidence": 0.85,
                    "details": "CSV format detected (semicolon-separated)",
                }
            elif tab_count > comma_count:
                return {
                    "format": "csv",
                    "confidence": 0.85,
                    "details": "CSV format detected (tab-separated)",
                }

        except Exception as e:
            pass

        # Default to CSV if extension suggests it
        if file_ext == "csv":
            return {
                "format": "csv",
                "confidence": 0.7,
                "details": "CSV format assumed by extension",
            }

        return {
            "format": "unknown",
            "confidence": 0.0,
            "details": "Could not determine file format",
        }

    def _parse_excel(
        self, file_bytes: bytes, filename: str
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Parse Excel file with error handling

        Returns:
            (DataFrame, list of warning messages)
        """
        warnings = []

        try:
            # Try to read with openpyxl (for .xlsx)
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
            warnings.append(f"✅ Successfully parsed with openpyxl engine")
            return df, warnings
        except Exception as e1:
            warnings.append(f"⚠️ openpyxl failed: {str(e1)[:100]}")

            # Try xlrd for older .xls files
            try:
                df = pd.read_excel(io.BytesIO(file_bytes), engine="xlrd")
                warnings.append(
                    f"✅ Successfully parsed with xlrd engine (older Excel format)"
                )
                return df, warnings
            except Exception as e2:
                warnings.append(f"❌ xlrd also failed: {str(e2)[:100]}")
                raise Exception(f"Could not parse Excel file: {str(e1)}")

    def _parse_csv_robust(
        self, file_bytes: bytes, filename: str
    ) -> Tuple[pd.DataFrame, List[str], List[Dict]]:
        """
        Parse CSV with multiple strategies and error recovery

        Returns:
            (DataFrame, list of warnings, list of skipped row info)
        """
        warnings = []
        skipped_rows = []
        encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252", "utf-16"]
        delimiters = [",", ";", "\t", "|"]

        # Strategy 1: Try strict parsing with different encodings
        for encoding in encodings:
            for delimiter in delimiters:
                try:
                    df = pd.read_csv(
                        io.BytesIO(file_bytes),
                        encoding=encoding,
                        delimiter=delimiter,
                        encoding_errors="replace",
                    )

                    # Validate we got reasonable data
                    if len(df.columns) > 1 and len(df) > 0:
                        warnings.append(
                            f"✅ Successfully parsed (encoding: {encoding}, delimiter: '{delimiter}')"
                        )
                        return df, warnings, skipped_rows

                except Exception as e:
                    continue

        # Strategy 2: Flexible parsing with error skipping
        if self.valves.SKIP_BAD_ROWS:
            warnings.append("⚠️ Strict parsing failed, attempting flexible parsing...")

            for encoding in encodings:
                try:
                    # Track bad lines
                    bad_lines_info = []
                    line_counter = [
                        0
                    ]  # Use list to allow modification in nested function

                    def track_bad_lines(bad_line):
                        line_counter[0] += 1
                        if len(bad_lines_info) < self.valves.MAX_ERROR_ROWS:
                            bad_lines_info.append(
                                {
                                    "line_num": line_counter[0],
                                    "content": (
                                        str(bad_line)[:200]
                                        if bad_line
                                        else "Empty line"
                                    ),
                                    "issue": "Malformed row",
                                    "action": "Skipped",
                                }
                            )
                        return None  # Skip the line

                    df = pd.read_csv(
                        io.BytesIO(file_bytes),
                        encoding=encoding,
                        encoding_errors="replace",
                        on_bad_lines=track_bad_lines,
                        engine="python",
                    )

                    if len(df.columns) > 0 and len(df) > 0:
                        skipped_rows = bad_lines_info
                        warnings.append(
                            f"⚠️ Flexible parsing succeeded (encoding: {encoding})"
                        )
                        if len(bad_lines_info) > 0:
                            warnings.append(
                                f"⚠️ Skipped {len(bad_lines_info)} malformed rows"
                            )
                        return df, warnings, skipped_rows

                except Exception as e:
                    continue

        # Strategy 3: Try to detect and fix common issues
        if self.valves.AUTO_FIX_ERRORS:
            warnings.append("🔧 Attempting automatic repair...")
            try:
                # Decode and clean the data
                text = file_bytes.decode("utf-8", errors="replace")
                lines = text.split("\n")

                if len(lines) < 2:
                    raise Exception("File has insufficient data")

                # Get expected column count from header
                header_line = lines[0].strip()
                header_cols = len(header_line.split(","))

                fixed_lines = [header_line]  # Keep header
                fixed_count = 0

                for i, line in enumerate(lines[1:], start=2):
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue

                    cols = line.split(",")

                    if len(cols) == header_cols:
                        fixed_lines.append(line)
                    elif len(cols) > header_cols:
                        # Too many columns - truncate extras
                        merged_line = ",".join(cols[:header_cols])
                        fixed_lines.append(merged_line)
                        fixed_count += 1
                        if len(skipped_rows) < self.valves.MAX_ERROR_ROWS:
                            skipped_rows.append(
                                {
                                    "line_num": i,
                                    "issue": f"Too many columns ({len(cols)} vs {header_cols})",
                                    "action": "Truncated extra columns",
                                }
                            )
                    elif len(cols) < header_cols and len(cols) > 0:
                        # Too few columns - pad with empty values
                        padded_cols = cols + [""] * (header_cols - len(cols))
                        padded_line = ",".join(padded_cols)
                        fixed_lines.append(padded_line)
                        fixed_count += 1
                        if len(skipped_rows) < self.valves.MAX_ERROR_ROWS:
                            skipped_rows.append(
                                {
                                    "line_num": i,
                                    "issue": f"Too few columns ({len(cols)} vs {header_cols})",
                                    "action": "Padded with empty values",
                                }
                            )
                    else:
                        # Completely empty row - skip
                        fixed_count += 1
                        if len(skipped_rows) < self.valves.MAX_ERROR_ROWS:
                            skipped_rows.append(
                                {
                                    "line_num": i,
                                    "issue": "Empty row",
                                    "action": "Skipped",
                                }
                            )

                # Try to parse fixed data
                fixed_csv = "\n".join(fixed_lines)
                df = pd.read_csv(io.StringIO(fixed_csv))

                if len(df) > 0:
                    warnings.append(
                        f"🔧 Auto-repair succeeded! Fixed/skipped {fixed_count} rows"
                    )
                    warnings.append(f"✅ Corrected data is now available for analysis")
                    return df, warnings, skipped_rows

            except Exception as e:
                warnings.append(f"❌ Auto-repair failed: {str(e)[:100]}")

        # All strategies failed
        raise Exception(
            "All parsing strategies failed. File may be severely corrupted or in unsupported format."
        )

    def _parse_key_value(
        self, file_bytes: bytes, filename: str
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Parse key-value format files

        Returns:
            (DataFrame, list of warnings)
        """
        warnings = []

        try:
            text = file_bytes.decode("utf-8", errors="replace")
            lines = text.split("\n")

            records = []
            current_record = {}
            record_count = 0

            for line_num, line in enumerate(lines, 1):
                line = line.strip()

                # Skip empty lines or separators
                if not line or line in ["---", "===", "***"]:
                    if current_record:
                        records.append(current_record)
                        current_record = {}
                        record_count += 1
                    continue

                # Parse key-value pair
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        current_record[key] = value

            # Add last record
            if current_record:
                records.append(current_record)
                record_count += 1

            if not records:
                raise Exception("No valid key-value pairs found")

            df = pd.DataFrame(records)
            warnings.append(f"✅ Parsed {record_count} records from key-value format")

            return df, warnings

        except Exception as e:
            raise Exception(f"Key-value parsing failed: {str(e)}")

    async def analyze_uploaded_file(
        self,
        __files__: List[dict] = [],
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Intelligently analyze uploaded files with automatic format detection and error recovery.
        Supports CSV, Excel (XLSX/XLS), and key-value formats.

        Args:
            __files__: Files uploaded through Open WebUI interface
            file_id: Identifier for the loaded file (default: "default")

        Returns:
            str: Comprehensive analysis with warnings about any issues
        """
        try:
            if file_id not in self.dataframes:
                return "❌ No file loaded. Please upload a file first."

            df = self.dataframes[file_id]

            if column_name not in df.columns:
                return f"❌ Column '{column_name}' not found."

            # Apply filter
            if operator == "contains":
                filtered = df[
                    df[column_name]
                    .astype(str)
                    .str.contains(value, case=False, na=False)
                ]
            elif operator == "==":
                filtered = df[df[column_name] == value]
            elif operator == "!=":
                filtered = df[df[column_name] != value]
            elif operator in [">", "<", ">=", "<="]:
                value_num = float(value)
                if operator == ">":
                    filtered = df[df[column_name] > value_num]
                elif operator == "<":
                    filtered = df[df[column_name] < value_num]
                elif operator == ">=":
                    filtered = df[df[column_name] >= value_num]
                else:
                    filtered = df[df[column_name] <= value_num]
            else:
                return f"❌ Invalid operator: {operator}"

            result = f"🔍 **Filter Results**\n\n"
            result += f"**Condition:** {column_name} {operator} {value}\n"
            result += f"**Matches:** {len(filtered):,} rows\n\n"

            if len(filtered) > 0:
                preview = min(len(filtered), 20)
                result += filtered.head(preview).to_markdown(index=False)
                if len(filtered) > preview:
                    result += (
                        f"\n\n*Showing first {preview} of {len(filtered):,} results*"
                    )
            else:
                result += "No matches found."

            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def group_and_aggregate(
        self,
        group_by: str,
        aggregate_column: str,
        operation: str = "count",
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Group data and calculate aggregates.

        Args:
            group_by: Column to group by
            aggregate_column: Column to aggregate
            operation: Aggregation (count, sum, mean, min, max, median)
            file_id: File identifier (default: "default")

        Returns:
            str: Aggregation results
        """
        try:
            if file_id not in self.dataframes:
                return "❌ No file loaded. Please upload a file first."

            df = self.dataframes[file_id]

            if group_by not in df.columns:
                return f"❌ Column '{group_by}' not found."

            if aggregate_column not in df.columns:
                return f"❌ Column '{aggregate_column}' not found."

            # Perform aggregation
            ops = {
                "count": "count",
                "sum": "sum",
                "mean": "mean",
                "min": "min",
                "max": "max",
                "median": "median",
            }

            if operation not in ops:
                return f"❌ Invalid operation. Use: {', '.join(ops.keys())}"

            grouped = (
                df.groupby(group_by)[aggregate_column].agg(ops[operation]).reset_index()
            )
            grouped.columns = [group_by, f"{operation}_{aggregate_column}"]
            grouped = grouped.sort_values(
                by=f"{operation}_{aggregate_column}", ascending=False
            )

            result = f"📊 **Aggregation Results**\n\n"
            result += f"**Operation:** {operation.upper()}\n"
            result += f"**Grouped by:** {group_by}\n"
            result += f"**Aggregate column:** {aggregate_column}\n\n"
            result += grouped.to_markdown(index=False)

            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def show_columns(
        self,
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Show all columns in the loaded file with metadata.

        Args:
            file_id: File identifier (default: "default")

        Returns:
            str: List of columns with details
        """
        try:
            if file_id not in self.file_metadata:
                return "❌ No file loaded. Please upload a file first."

            meta = self.file_metadata[file_id]
            df = self.dataframes[file_id]

            result = f"📋 **File Information: {meta['filename']}**\n\n"
            result += f"**Format:** {meta.get('format', 'Unknown').upper()}\n"
            result += f"**Rows:** {meta['rows']:,}\n"
            result += f"**Columns:** {meta['columns']}\n"

            if meta.get("skipped_rows", 0) > 0:
                result += f"**Skipped Rows:** {meta['skipped_rows']:,}\n"

            result += "\n**Column Details:**\n\n"

            for i, (col, dtype) in enumerate(meta["dtypes"].items(), 1):
                col_data = df[col]
                null_count = col_data.isna().sum()
                unique_count = col_data.nunique()

                result += f"{i}. **{col}**\n"
                result += f"   - Type: {dtype}\n"
                result += f"   - Unique values: {unique_count:,}\n"
                result += f"   - Missing: {null_count:,}\n"

                # Add sample values for non-numeric columns
                if not pd.api.types.is_numeric_dtype(col_data) and unique_count <= 10:
                    samples = col_data.dropna().unique()[:5]
                    result += f"   - Examples: {', '.join(map(str, samples))}\n"

                result += "\n"

            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def export_summary(
        self,
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Generate a comprehensive summary report of the loaded data.

        Args:
            file_id: File identifier (default: "default")

        Returns:
            str: Comprehensive data summary
        """
        try:
            if file_id not in self.dataframes:
                return "❌ No file loaded. Please upload a file first."

            df = self.dataframes[file_id]
            meta = self.file_metadata[file_id]

            result = f"📊 **Comprehensive Data Summary Report**\n\n"
            result += f"{'='*50}\n\n"

            # File information
            result += f"## File Information\n\n"
            result += f"- **Filename:** {meta['filename']}\n"
            result += f"- **Format:** {meta.get('format', 'Unknown').upper()}\n"
            result += f"- **Total Rows:** {len(df):,}\n"
            result += f"- **Total Columns:** {len(df.columns)}\n"

            if meta.get("skipped_rows", 0) > 0:
                result += f"- **Skipped Rows:** {meta['skipped_rows']:,} ⚠️\n"

            result += "\n"

            # Data quality
            result += f"## Data Quality\n\n"
            total_cells = len(df) * len(df.columns)
            missing_cells = df.isna().sum().sum()
            completeness = (
                ((total_cells - missing_cells) / total_cells) * 100
                if total_cells > 0
                else 0
            )

            result += f"- **Total Cells:** {total_cells:,}\n"
            result += f"- **Missing Cells:** {missing_cells:,}\n"
            result += f"- **Completeness:** {completeness:.2f}%\n\n"

            # Column summary
            result += f"## Column Summary\n\n"

            numeric_cols = df.select_dtypes(include=["number"]).columns
            text_cols = df.select_dtypes(include=["object"]).columns
            datetime_cols = df.select_dtypes(include=["datetime"]).columns

            result += f"- **Numeric columns:** {len(numeric_cols)}\n"
            result += f"- **Text columns:** {len(text_cols)}\n"
            result += f"- **Datetime columns:** {len(datetime_cols)}\n\n"

            # Numeric statistics
            if len(numeric_cols) > 0:
                result += f"## Numeric Columns Statistics\n\n"

                for col in numeric_cols[:5]:  # Show first 5 numeric columns
                    col_stats = df[col].describe()
                    result += f"### {col}\n"
                    result += f"- Mean: {col_stats['mean']:,.2f}\n"
                    result += f"- Median: {col_stats['50%']:,.2f}\n"
                    result += f"- Std Dev: {col_stats['std']:,.2f}\n"
                    result += f"- Range: [{col_stats['min']:,.2f}, {col_stats['max']:,.2f}]\n\n"

                if len(numeric_cols) > 5:
                    result += (
                        f"*...and {len(numeric_cols) - 5} more numeric columns*\n\n"
                    )

            # Categorical summary
            if len(text_cols) > 0:
                result += f"## Categorical Columns\n\n"

                for col in text_cols[:5]:  # Show first 5 text columns
                    unique_count = df[col].nunique()
                    most_common = df[col].value_counts().head(3)

                    result += f"### {col}\n"
                    result += f"- Unique values: {unique_count:,}\n"
                    result += f"- Top 3 values:\n"
                    for val, count in most_common.items():
                        pct = (count / len(df)) * 100
                        result += f"  - {val}: {count:,} ({pct:.1f}%)\n"
                    result += "\n"

                if len(text_cols) > 5:
                    result += (
                        f"*...and {len(text_cols) - 5} more categorical columns*\n\n"
                    )

            # Parsing warnings
            if meta.get("warnings"):
                result += f"## Parsing Notes\n\n"
                for warning in meta["warnings"]:
                    result += f"- {warning}\n"
                result += "\n"

            result += f"{'='*50}\n"
            result += f"\n*Report generated successfully*"

            return result

        except Exception as e:
            return f"❌ Error generating summary: {str(e)}"

    async def get_row_count(
        self,
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Get the total row count of the loaded file.

        Args:
            file_id: File identifier (default: "default")

        Returns:
            str: Row count information
        """
        try:
            if file_id not in self.dataframes:
                return "❌ No file loaded. Please upload a file first."

            df = self.dataframes[file_id]
            meta = self.file_metadata[file_id]

            result = f"🔢 **Row Count Information**\n\n"
            result += f"**File:** {meta['filename']}\n"
            result += f"**Successfully loaded rows:** {len(df):,}\n"

            if meta.get("skipped_rows", 0) > 0:
                result += f"**Skipped rows:** {meta['skipped_rows']:,}\n"
                result += f"**Original total (estimated):** {len(df) + meta['skipped_rows']:,}\n"

            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def export_corrected_csv(
        self,
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Export the corrected/cleaned data as CSV text that can be saved.

        Args:
            file_id: File identifier (default: "default")

        Returns:
            str: CSV data as text
        """
        try:
            if file_id not in self.dataframes:
                return "❌ No file loaded. Please upload a file first."

            df = self.dataframes[file_id]
            meta = self.file_metadata[file_id]

            # Convert to CSV string
            csv_output = df.to_csv(index=False)

            result = f"📥 **Corrected CSV Data Export**\n\n"
            result += f"**Original file:** {meta['filename']}\n"
            result += f"**Rows in corrected data:** {len(df):,}\n"

            if meta.get("skipped_rows", 0) > 0:
                result += f"**Rows skipped/fixed:** {meta['skipped_rows']:,}\n"

            result += f"\n**Instructions:**\n"
            result += f"1. Copy the CSV data below\n"
            result += f"2. Save it as a new .csv file\n"
            result += (
                f"3. The corrected data is already loaded and ready for analysis\n\n"
            )

            result += f"**📋 Corrected CSV Data:**\n\n"
            result += f"```csv\n"
            result += csv_output[:5000]  # Show first 5000 characters
            if len(csv_output) > 5000:
                result += (
                    f"\n... (truncated, total size: {len(csv_output)} characters)\n"
                )
            result += f"```\n\n"

            result += f"💡 **Note:** This corrected data is already available to all analysis functions.\n"
            result += (
                f"You don't need to re-upload unless you want to save a clean copy."
            )

            return result

        except Exception as e:
            return f"❌ Error exporting data: {str(e)}"

    async def verify_data_loaded(
        self,
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Verify that data is loaded and accessible to all functions.

        Args:
            file_id: File identifier (default: "default")

        Returns:
            str: Verification status
        """
        try:
            result = f"🔍 **Data Accessibility Check**\n\n"

            # Debug: Show what's in memory
            result += f"**Debug Info:**\n"
            result += f"- Requested file_id: `{file_id}`\n"
            result += f"- Loaded file_ids: {list(self.dataframes.keys())}\n"
            result += f"- Number of loaded files: {len(self.dataframes)}\n\n"

            # Check if file_id exists
            if file_id not in self.dataframes:
                result += f"❌ **Status:** No data loaded for file_id '{file_id}'\n\n"

                available_ids = list(self.dataframes.keys())
                if available_ids:
                    result += f"**Available file IDs:** {', '.join(available_ids)}\n\n"
                    result += (
                        f"💡 **Try using one of these file IDs in your commands**\n"
                    )
                    result += f"   Example: `count_by_column('column_name', '{available_ids[0]}')`\n"
                else:
                    result += f"**Available file IDs:** None\n\n"
                    result += f"⚠️ **Issue:** No data is currently loaded in memory\n\n"
                    result += f"**Possible reasons:**\n"
                    result += f"1. File upload failed\n"
                    result += f"2. analyze_uploaded_file() was not called\n"
                    result += f"3. The tool was restarted and lost memory\n\n"
                    result += f"**Solution:**\n"
                    result += f"1. Upload your file again\n"
                    result += (
                        f"2. Make sure `analyze_uploaded_file()` runs successfully\n"
                    )
                    result += f"3. Check for error messages during upload\n"

                return result

            # Data exists - verify it
            df = self.dataframes[file_id]
            meta = self.file_metadata[file_id]

            result += f"✅ **Status:** Data is loaded and accessible\n\n"
            result += f"**File ID:** `{file_id}`\n"
            result += f"**Filename:** {meta['filename']}\n"
            result += f"**Format:** {meta.get('format', 'Unknown')}\n"
            result += f"**Rows available:** {len(df):,}\n"
            result += f"**Columns available:** {len(df.columns)}\n\n"

            if meta.get("skipped_rows", 0) > 0:
                result += f"⚠️ **Data was corrected:** {meta['skipped_rows']} rows were fixed/skipped\n"
                result += f"✅ **Corrected data is accessible** to all functions\n\n"

            result += f"**Sample columns:** {', '.join(list(df.columns)[:5])}\n\n"

            result += f"**Available functions can now access this data:**\n"
            result += f"- ✅ query_data()\n"
            result += f"- ✅ count_by_column()\n"
            result += f"- ✅ get_statistics()\n"
            result += f"- ✅ filter_data()\n"
            result += f"- ✅ group_and_aggregate()\n"
            result += f"- ✅ show_columns()\n"
            result += f"- ✅ export_summary()\n\n"

            result += f"💡 **You can now run any analysis without re-uploading!**"

            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def load_from_text(
        self,
        csv_text: str,
        filename: str = "manual_input.csv",
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Load CSV data directly from pasted text. Use this as a backup when file upload fails.

        Args:
            csv_text: CSV content as plain text
            filename: Name for the data (default: "manual_input.csv")
            file_id: Identifier for the file (default: "default")

        Returns:
            str: Confirmation message

        Example:
            load_from_text("col1,col2\\nval1,val2\\nval3,val4")
        """
        try:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "Parsing CSV text...", "done": False},
                    }
                )

            # Try to parse the text
            try:
                df = pd.read_csv(io.StringIO(csv_text))
            except Exception as e:
                return f"❌ Failed to parse CSV text: {str(e)}\n\n💡 Make sure the text is in proper CSV format with comma-separated values."

            if len(df) == 0:
                return "❌ Parsed data is empty. Please check your CSV text."

            # Store the dataframe
            self.dataframes[file_id] = df

            # Store metadata
            self.file_metadata[file_id] = {
                "filename": filename,
                "format": "csv",
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "warnings": ["Loaded from pasted text"],
                "skipped_rows": 0,
            }

            # Store empty parsing log
            self.parsing_logs[file_id] = {
                "format_detection": {
                    "format": "csv",
                    "confidence": 1.0,
                    "details": "Loaded from pasted text",
                },
                "warnings": ["Loaded from pasted text"],
                "skipped_rows": [],
            }

            result = f"✅ **CSV Data Loaded from Text!**\n\n"
            result += f"📁 **Name:** {filename}\n"
            result += (
                f"📊 **Dimensions:** {len(df):,} rows × {len(df.columns)} columns\n\n"
            )

            result += "📋 **Columns:**\n"
            for i, (col, dtype) in enumerate(df.dtypes.items(), 1):
                result += f"{i}. **{col}** ({dtype})\n"

            result += f"\n📄 **Preview (first 3 rows):**\n\n"
            result += df.head(3).to_markdown(index=False)

            result += f"\n\n✅ **Data is now accessible to all analysis functions!**"

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Data loaded successfully!",
                            "done": True,
                        },
                    }
                )

            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"
            if not __files__ or len(__files__) == 0:
                return "❌ No files uploaded. Please attach a file to your message."

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "Analyzing file...", "done": False},
                    }
                )

            # Extract file data
            file_data = __files__[0]
            filename = file_data.get(
                "name", file_data.get("file", {}).get("filename", "uploaded_file")
            )

            # Get file content
            file_content = None
            if "file" in file_data and "data" in file_data["file"]:
                file_content = file_data["file"]["data"].get("content")
            if not file_content and "content" in file_data:
                file_content = file_data["content"]

            if not file_content:
                return "❌ Could not extract file content. Please try uploading again."

            # Decode file content
            if isinstance(file_content, str):
                try:
                    file_bytes = base64.b64decode(file_content)
                except:
                    file_bytes = file_content.encode("utf-8")
            else:
                file_bytes = file_content

            # Check file size
            file_size_mb = len(file_bytes) / (1024 * 1024)
            if file_size_mb > self.valves.MAX_FILE_SIZE_MB:
                return f"❌ File size ({file_size_mb:.2f}MB) exceeds limit ({self.valves.MAX_FILE_SIZE_MB}MB)"

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Detecting file format...",
                            "done": False,
                        },
                    }
                )

            # Detect format
            format_info = self._detect_file_format(filename, file_bytes)

            # Parse based on detected format
            df = None
            warnings = []
            skipped_rows = []

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Parsing as {format_info['format']}...",
                            "done": False,
                        },
                    }
                )

            try:
                if format_info["format"] == "excel":
                    df, warnings = self._parse_excel(file_bytes, filename)

                elif format_info["format"] == "csv":
                    df, warnings, skipped_rows = self._parse_csv_robust(
                        file_bytes, filename
                    )

                elif format_info["format"] == "key-value":
                    df, warnings = self._parse_key_value(file_bytes, filename)

                else:
                    # Unknown format - try CSV as fallback
                    warnings.append("⚠️ Unknown format, attempting CSV parsing...")
                    df, csv_warnings, skipped_rows = self._parse_csv_robust(
                        file_bytes, filename
                    )
                    warnings.extend(csv_warnings)

            except Exception as parse_error:
                return f"❌ **Parsing Failed**\n\n**File:** {filename}\n**Detected format:** {format_info['format']}\n**Error:** {str(parse_error)}\n\n**Suggestions:**\n1. Check if file is corrupted\n2. Try opening in Excel and re-saving\n3. Verify the file format matches the extension\n4. Contact support with this error message"

            if df is None or len(df) == 0:
                return f"❌ Parsing resulted in empty dataset. File may be corrupted or empty."

            # Store dataframe
            self.dataframes[file_id] = df

            # Store metadata
            self.file_metadata[file_id] = {
                "filename": filename,
                "format": format_info["format"],
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "warnings": warnings,
                "skipped_rows": len(skipped_rows),
            }

            # Store parsing log
            self.parsing_logs[file_id] = {
                "format_detection": format_info,
                "warnings": warnings,
                "skipped_rows": skipped_rows,
            }

            # Debug confirmation
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Data stored with file_id: {file_id}",
                            "done": False,
                        },
                    }
                )

            # Generate comprehensive summary
            summary = ""

            # Show debug info at the top
            summary += debug_info
            summary += f"{'='*60}\n\n"

            # Header with status indicator
            if len(skipped_rows) > 0:
                summary += "⚠️ **File Loaded with Warnings**\n\n"
            else:
                summary += "✅ **File Loaded Successfully!**\n\n"

            # File info
            summary += f"📁 **Filename:** {filename}\n"
            summary += f"🔍 **Detected Format:** {format_info['format'].upper()} ({format_info['details']})\n"
            summary += (
                f"📊 **Dimensions:** {len(df):,} rows × {len(df.columns)} columns\n"
            )
            summary += f"💾 **Size:** {file_size_mb:.2f}MB\n\n"

            # Warnings section
            if warnings:
                summary += "📋 **Parsing Details:**\n"
                for warning in warnings:
                    summary += f"{warning}\n"
                summary += "\n"

            # Skipped rows section
            if skipped_rows:
                summary += f"⚠️ **Data Quality Issues:**\n"
                summary += f"- Skipped/fixed {len(skipped_rows)} problematic rows\n"

                if len(skipped_rows) <= 10:
                    summary += "\n**Affected rows:**\n"
                    for skip_info in skipped_rows[:10]:
                        if "line_num" in skip_info:
                            summary += f"- Line {skip_info['line_num']}: {skip_info.get('issue', skip_info.get('action', 'Error'))}\n"
                else:
                    summary += f"\n**Sample of affected rows (first 10 of {len(skipped_rows)}):**\n"
                    for skip_info in skipped_rows[:10]:
                        if "line_num" in skip_info:
                            summary += f"- Line {skip_info['line_num']}: {skip_info.get('issue', 'Error')}\n"
                    summary += f"\n*Use `show_parsing_log()` to see all {len(skipped_rows)} issues*\n"

                summary += "\n"

            # Columns section
            summary += "📋 **Columns:**\n"
            for i, (col, dtype) in enumerate(df.dtypes.items(), 1):
                null_count = df[col].isna().sum()
                null_pct = (null_count / len(df)) * 100 if len(df) > 0 else 0
                summary += f"{i}. **{col}** ({dtype})"
                if null_count > 0:
                    summary += f" - {null_count:,} nulls ({null_pct:.1f}%)"
                summary += "\n"

            # Quick stats
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                summary += f"\n🔢 **Found {len(numeric_cols)} numeric columns**\n"

            # Preview
            summary += f"\n📄 **Data Preview (first 3 rows):**\n\n"
            summary += df.head(3).to_markdown(index=False)

            summary += f"\n\n✨ **Ready for analysis!** You can now:\n"
            summary += "- Query and filter data\n"
            summary += "- Calculate statistics\n"
            summary += "- Count and aggregate values\n"
            summary += "- Export results\n"

            if len(skipped_rows) > 0:
                summary += "\n💡 **Note:** Some rows were skipped. Your analysis will be based on the successfully loaded data."

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "File loaded successfully!",
                            "done": True,
                        },
                    }
                )

            return summary

        except Exception as e:
            return (
                f"❌ Unexpected error: {str(e)}\n\nPlease try again or contact support."
            )

    async def show_parsing_log(
        self,
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Show detailed parsing log including all skipped rows and warnings.

        Args:
            file_id: File identifier (default: "default")

        Returns:
            str: Detailed parsing log
        """
        try:
            if file_id not in self.parsing_logs:
                return "❌ No parsing log found. File may not be loaded yet."

            log = self.parsing_logs[file_id]
            meta = self.file_metadata.get(file_id, {})

            result = f"📋 **Parsing Log: {meta.get('filename', 'Unknown')}**\n\n"

            # Format detection
            result += "🔍 **Format Detection:**\n"
            fmt = log["format_detection"]
            result += f"- Detected as: {fmt['format'].upper()}\n"
            result += f"- Confidence: {fmt['confidence']*100:.1f}%\n"
            result += f"- Details: {fmt['details']}\n\n"

            # Warnings
            if log["warnings"]:
                result += "⚠️ **Warnings:**\n"
                for warning in log["warnings"]:
                    result += f"{warning}\n"
                result += "\n"

            # Skipped rows
            skipped = log["skipped_rows"]
            if skipped:
                result += f"🚫 **Skipped/Fixed Rows ({len(skipped)} total):**\n\n"

                for i, skip_info in enumerate(skipped[:50], 1):
                    if "line_num" in skip_info:
                        result += f"{i}. **Line {skip_info['line_num']}**\n"
                        if "issue" in skip_info:
                            result += f"   Issue: {skip_info['issue']}\n"
                        if "action" in skip_info:
                            result += f"   Action: {skip_info['action']}\n"
                        if "content" in skip_info:
                            result += f"   Content: `{skip_info['content'][:100]}...`\n"
                        result += "\n"

                if len(skipped) > 50:
                    result += f"\n*Showing first 50 of {len(skipped)} issues*\n"
            else:
                result += "✅ **No rows were skipped** - clean parse!\n"

            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def query_data(
        self,
        query: str,
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Query data using pandas query syntax.

        Args:
            query: Query condition (e.g., "`Gender Code` == 'F' and `Race Code` == 'W'")
            file_id: File identifier (default: "default")

        Returns:
            str: Query results
        """
        try:
            if file_id not in self.dataframes:
                return "❌ No file loaded. Please upload a file first."

            df = self.dataframes[file_id]
            result_df = df.query(query)

            result = f"🔍 **Query Results**\n\n"
            result += f"**Query:** `{query}`\n"
            result += (
                f"**Matches:** {len(result_df):,} rows (out of {len(df):,} total)\n\n"
            )

            if len(result_df) == 0:
                result += "No rows match the query."
            else:
                preview = min(len(result_df), 20)
                result += result_df.head(preview).to_markdown(index=False)
                if len(result_df) > preview:
                    result += (
                        f"\n\n*Showing first {preview} of {len(result_df):,} results*"
                    )

            return result

        except Exception as e:
            return f"❌ Query error: {str(e)}\n\n💡 Use backticks for column names with spaces: \\`Column Name\\`"

    async def count_by_column(
        self,
        column_name: str,
        file_id: str = "default",
        top_n: int = 20,
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Count unique values in a column.

        Args:
            column_name: Column to count
            file_id: File identifier (default: "default")
            top_n: Number of top values to show (default: 20)

        Returns:
            str: Value counts with percentages
        """
        try:
            if file_id not in self.dataframes:
                return "❌ No file loaded. Please upload a file first."

            df = self.dataframes[file_id]

            if column_name not in df.columns:
                available = "', '".join(df.columns[:10])
                return f"❌ Column '{column_name}' not found.\n\n**First 10 columns:** '{available}...'"

            value_counts = df[column_name].value_counts().head(top_n)
            total_unique = df[column_name].nunique()

            result = f"🔢 **Value Counts: {column_name}**\n\n"
            result += f"**Total unique values:** {total_unique:,}\n"
            result += f"**Showing top {min(top_n, len(value_counts))}:**\n\n"

            for idx, (val, count) in enumerate(value_counts.items(), 1):
                pct = (count / len(df)) * 100
                result += f"{idx}. **{val}**: {count:,} ({pct:.1f}%)\n"

            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def get_statistics(
        self,
        column_name: str,
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Calculate statistics for a column.

        Args:
            column_name: Column to analyze
            file_id: File identifier (default: "default")

        Returns:
            str: Statistical summary
        """
        try:
            if file_id not in self.dataframes:
                return "❌ No file loaded. Please upload a file first."

            df = self.dataframes[file_id]

            if column_name not in df.columns:
                return f"❌ Column '{column_name}' not found."

            col = df[column_name]
            result = f"📊 **Statistics: {column_name}**\n\n"

            if pd.api.types.is_numeric_dtype(col):
                stats = col.describe()
                result += f"- **Count:** {int(stats['count']):,}\n"
                result += f"- **Mean:** {stats['mean']:,.2f}\n"
                result += f"- **Std Dev:** {stats['std']:,.2f}\n"
                result += f"- **Min:** {stats['min']:,.2f}\n"
                result += f"- **25%:** {stats['25%']:,.2f}\n"
                result += f"- **Median:** {stats['50%']:,.2f}\n"
                result += f"- **75%:** {stats['75%']:,.2f}\n"
                result += f"- **Max:** {stats['max']:,.2f}\n"
                result += f"- **Sum:** {col.sum():,.2f}\n"
            else:
                result += f"- **Count:** {col.count():,}\n"
                result += f"- **Unique:** {col.nunique():,}\n"
                result += f"- **Missing:** {col.isna().sum():,}\n"

                if not col.mode().empty:
                    result += f"- **Most Common:** {col.mode().values[0]}\n"

                result += "\n**Top 5 values:**\n"
                for val, cnt in col.value_counts().head(5).items():
                    pct = (cnt / len(df)) * 100
                    result += f"- {val}: {cnt:,} ({pct:.1f}%)\n"

            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def filter_data(
        self,
        column_name: str,
        value: str,
        operator: str = "==",
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Filter data by column value.

        Args:
            column_name: Column to filter
            value: Value to match
            operator: Comparison operator (==, !=, >, <, >=, <=, contains)
            file_id: File identifier (default: "default")

        Returns:
            str: Filtered results
        """
        try:
            if file_id not in self.dataframes:
                return "❌ No file loaded. Please upload a file first."

            df = self.dataframes[file_id]

            if column_name not in df.columns:
                return f"❌ Column '{column_name}' not found."

            # Apply filter
            if operator == "contains":
                filtered = df[
                    df[column_name]
                    .astype(str)
                    .str.contains(value, case=False, na=False)
                ]
            elif operator == "==":
                filtered = df[df[column_name] == value]
            elif operator == "!=":
                filtered = df[df[column_name] != value]
            elif operator in [">", "<", ">=", "<="]:
                value_num = float(value)
                if operator == ">":
                    filtered = df[df[column_name] > value_num]
                elif operator == "<":
                    filtered = df[df[column_name] < value_num]
                elif operator == ">=":
                    filtered = df[df[column_name] >= value_num]
                else:
                    filtered = df[df[column_name] <= value_num]
            else:
                return f"❌ Invalid operator: {operator}"

            result = f"🔍 **Filter Results**\n\n"
            result += f"**Condition:** {column_name} {operator} {value}\n"
            result += f"**Matches:** {len(filtered):,} rows\n\n"

            if len(filtered) > 0:
                preview = min(len(filtered), 20)
                result += filtered.head(preview).to_markdown(index=False)
                if len(filtered) > preview:
                    result += (
                        f"\n\n*Showing first {preview} of {len(filtered):,} results*"
                    )
            else:
                result += "No matches found."

            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def statistical_trend_analysis(
        self,
        column_name: str,
        group_by: Optional[str] = None,
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None
    ) -> str:
        """
        Statistical trend analysis with anomaly detection.
        DIDE Core Capability: Quantitative Analysis
        
        Args:
            column_name: Column to analyze
            group_by: Optional grouping column
            file_id: File identifier
            
        Returns:
            str: Statistical analysis report
        """
        try:
            if file_id not in self.dataframes:
                return "❌ **ERROR:** No data loaded.\n\n**DIDE Protocol:** Data extraction mandatory."
            
            df = self.dataframes[file_id]
            meta = self.file_metadata[file_id]
            
            if column_name not in df.columns:
                return f"❌ Column '{column_name}' not found."
            
            result = f"## 📈 STATISTICAL TREND ANALYSIS\n\n"
            result += f"**Document:** {meta['filename']}\n"
            result += f"**Column:** {column_name}\n"
            if group_by:
                result += f"**Grouped By:** {group_by}\n"
            result += f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            result += f"---\n\n"
            
            col_data = df[column_name].dropna()
            
            if not pd.api.types.is_numeric_dtype(col_data):
                return f"❌ Column '{column_name}' is not numeric.\n\n**Data Type:** {col_data.dtype}"
            
            result += f"### 📊 Descriptive Statistics\n\n"
            result += f"| Metric | Value |\n"
            result += f"|--------|-------|\n"
            result += f"| **Count** | {len(col_data):,} |\n"
            result += f"| **Mean** | {col_data.mean():,.4f} |\n"
            result += f"| **Median** | {col_data.median():,.4f} |\n"
            result += f"| **Std Dev** | {col_data.std():,.4f} |\n"
            result += f"| **Variance** | {col_data.var():,.4f} |\n"
            result += f"| **Min** | {col_data.min():,.4f} |\n"
            result += f"| **Max** | {col_data.max():,.4f} |\n"
            result += f"| **Range** | {(col_data.max() - col_data.min()):,.4f} |\n"
            result += f"| **Skewness** | {col_data.skew():,.4f} |\n"
            result += f"| **Kurtosis** | {col_data.kurtosis():,.4f} |\n\n"
            
            # Distribution
            result += f"### 📉 Distribution\n\n"
            result += f"| Percentile | Value |\n"
            result += f"|------------|-------|\n"
            for pct in [10, 25, 50, 75, 90, 95, 99]:
                result += f"| {pct}th | {col_data.quantile(pct/100):,.4f} |\n"
            result += "\n"
            
            # Anomaly detection
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            
            outliers = col_data[(col_data < lower) | (col_data > upper)]
            
            result += f"### ⚠️ Anomaly Detection (IQR Method)\n\n"
            result += f"- **Lower Threshold:** {lower:,.4f}\n"
            result += f"- **Upper Threshold:** {upper:,.4f}\n"
            result += f"- **Outliers:** {len(outliers):,} ({(len(outliers)/len(col_data)*100):.2f}%)\n\n"
            
            if len(outliers) > 0:
                result += f"**Outlier Range:** [{outliers.min():,.4f}, {outliers.max():,.4f}]\n\n"
            
            # Grouped analysis
            if group_by and group_by in df.columns:
                result += f"### 📊 Grouped Analysis by {group_by}\n\n"
                grouped = df.groupby(group_by)[column_name].agg(['count', 'mean', 'median', 'std', 'min', 'max'])
                grouped.columns = ['Count', 'Mean', 'Median', 'Std Dev', 'Min', 'Max']
                result += grouped.to_markdown()
                result += "\n\n"
            
            result += f"---\n\n"
            result += f"**📋 Data Integrity:** Based on {len(col_data):,} valid entries from {len(df):,} total records.\n\n"
            result += f"**⚠️ DISCLAIMER:** Analytical tool only. Not a substitute for professional statistical consulting.\n"
            
            # Log
            self.analysis_history[file_id] = self.analysis_history.get(file_id, [])
            self.analysis_history[file_id].append({
                'timestamp': pd.Timestamp.now(),
                'analysis_type': 'statistical_trend_analysis',
                'column': column_name,
                'outliers_found': len(outliers)
            })
            
            return result
        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def comparative_analysis(
        self,
        columns: List[str],
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None
    ) -> str:
        """
        Compare multiple columns.
        DIDE Core Capability: Comparative Analysis
        """
        try:
            if file_id not in self.dataframes:
                return "❌ No data loaded."
            
            df = self.dataframes[file_id]
            meta = self.file_metadata[file_id]
            
            if len(columns) < 2:
                return "❌ Need at least 2 columns.\n\n**Example:** `comparative_analysis(['col1', 'col2'])`"
            
            missing = [c for c in columns if c not in df.columns]
            if missing:
                return f"❌ Columns not found: {', '.join(missing)}"
            
            result = f"## 🔄 COMPARATIVE ANALYSIS\n\n"
            result += f"**Document:** {meta['filename']}\n"
            result += f"**Comparing:** {' vs '.join(columns)}\n"
            result += f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            result += f"---\n\n"
            
            # Comparison table
            result += f"### 📊 Side-by-Side\n\n"
            result += f"| Metric | " + " | ".join(columns) + " |\n"
            result += f"|--------|" + "|".join(["--------"] * len(columns)) + "|\n"
            
            result += f"| **Data Type** | " + " | ".join([str(df[c].dtype) for c in columns]) + " |\n"
            result += f"| **Valid Count** | " + " | ".join([f"{df[c].notna().sum():,}" for c in columns]) + " |\n"
            result += f"| **Missing** | " + " | ".join([f"{df[c].isna().sum():,}" for c in columns]) + " |\n"
            result += f"| **Unique** | " + " | ".join([f"{df[c].nunique():,}" for c in columns]) + " |\n"
            
            # Numeric stats
            numeric_cols = [c for c in columns if pd.api.types.is_numeric_dtype(df[c])]
            if numeric_cols:
                result += f"| **Mean** | " + " | ".join([f"{df[c].mean():,.2f}" if c in numeric_cols else "N/A" for c in columns]) + " |\n"
                result += f"| **Median** | " + " | ".join([f"{df[c].median():,.2f}" if c in numeric_cols else "N/A" for c in columns]) + " |\n"
                result += f"| **Min** | " + " | ".join([f"{df[c].min():,.2f}" if c in numeric_cols else "N/A" for c in columns]) + " |\n"
                result += f"| **Max** | " + " | ".join([f"{df[c].max():,.2f}" if c in numeric_cols else "N/A" for c in columns]) + " |\n"
            
            result += "\n"
            
            # Correlations
            if len(numeric_cols) >= 2:
                result += f"### 📈 Correlation Matrix\n\n"
                corr = df[numeric_cols].corr()
                result += corr.to_markdown()
                result += "\n\n"
                
                result += f"**Notable Correlations:**\n"
                for i in range(len(numeric_cols)):
                    for j in range(i+1, len(numeric_cols)):
                        corr_val = corr.iloc[i, j]
                        if abs(corr_val) > 0.7:
                            strength = "Strong positive" if corr_val > 0 else "Strong negative"
                            result += f"- {numeric_cols[i]} vs {numeric_cols[j]}: {strength} ({corr_val:.3f})\n"
            
            result += f"\n---\n\n"
            result += f"**📋 Basis:** All comparisons from document data only.\n"
            
            return result
        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def identify_data_gaps(
        self,
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None
    ) -> str:
        """Identify missing data and gaps"""
        try:
            if file_id not in self.dataframes:
                return "❌ No data loaded."
            
            df = self.dataframes[file_id]
            meta = self.file_metadata[file_id]
            
            result = f"## 🔍 DATA GAP ANALYSIS\n\n"
            result += f"**Document:** {meta['filename']}\n"
            result += f"**Total Records:** {len(df):,}\n"
            result += f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            result += f"---\n\n"
            
            # Overall completeness
            total_cells = len(df) * len(df.columns)
            missing_cells = df.isna().sum().sum()
            completeness = ((total_cells - missing_cells) / total_cells) * 100
            
            result += f"### 📊 Overall Completeness\n\n"
            result += f"| Metric | Value |\n"
            result += f"|--------|-------|\n"
            result += f"| **Total Cells** | {total_cells:,} |\n"
            result += f"| **Populated** | {(total_cells - missing_cells):,} |\n"
            result += f"| **Missing** | {missing_cells:,} |\n"
            result += f"| **Completeness** | {completeness:.2f}% |\n\n"
            
            # Per-field
            result += f"### 📋 Missing Data by Field\n\n"
            
            missing_by_col = df.isna().sum().sort_values(ascending=False)
            
            if missing_by_col.sum() == 0:
                result += f"✅ No missing data. All fields 100% complete.\n\n"
            else:
                result += f"| Field | Missing | % | Complete | % |\n"
                result += f"|-------|---------|---|----------|---|\n"
                
                for col, missing_count in missing_by_col.items():
                    if missing_count > 0:
                        missing_pct = (missing_count / len(df)) * 100
                        complete_count = len(df) - missing_count
                        complete_pct = 100 - missing_pct
                        result += f"| **{col}** | {missing_count:,} | {missing_pct:.1f}% | {complete_count:,} | {complete_pct:.1f}% |\n"
                
                result += "\n"
                
                # Critical gaps
                critical = missing_by_col[missing_by_col / len(df) > 0.5]
                if len(critical) > 0:
                    result += f"### ⚠️ Critical Gaps (>50% missing)\n\n"
                    for col, count in critical.items():
                        pct = (count / len(df)) * 100
                        result += f"- **{col}**: {pct:.1f}% missing\n"
                    result += "\n"
            
            result += f"---\n\n"
            result += f"**📋 Recommendation:** {'Data quality excellent' if missing_cells == 0 else 'Consider data enrichment for fields with gaps'}\n"
            
            return result
        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def get_analysis_history(
        self,
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None
    ) -> str:
        """View analysis audit trail"""
        result = f"## 📜 ANALYSIS HISTORY\n\n"
        
        if file_id not in self.analysis_history or len(self.analysis_history[file_id]) == 0:
            return f"{result}No history for '{file_id}'."
        
        if file_id in self.file_metadata:
            result += f"**Document:** {self.file_metadata[file_id]['filename']}\n\n"
        
        result += f"**Total:** {len(self.analysis_history[file_id])}\n\n"
        result += f"| # | Time | Type | Details |\n"
        result += f"|---|------|------|----------|\n"
        
        for idx, analysis in enumerate(self.analysis_history[file_id], 1):
            timestamp = analysis['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            atype = analysis['analysis_type'].replace('_', ' ').title()
            
            details = []
            if 'column' in analysis:
                details.append(f"Col: {analysis['column']}")
            if 'outliers_found' in analysis:
                details.append(f"{analysis['outliers_found']} outliers")
            
            details_str = ', '.join(details) if details else '-'
            result += f"| {idx} | {timestamp} | {atype} | {details_str} |\n"
        
        result += f"\n**💡 Audit Trail:** All DIDE operations logged for transparency.\n"
        
    async def extract_key_information(
        self,
        columns: Optional[List[str]] = None,
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None
    ) -> str:
        """
        Extract key entities, facts, and critical data points.
        DIDE Core: Key Information Extraction
        """
        try:
            if file_id not in self.dataframes:
                return "❌ **ERROR:** No data loaded.\n\n**DIDE Protocol:** Extract and store document first."
            
            df = self.dataframes[file_id]
            meta = self.file_metadata[file_id]
            
            result = f"## 🔍 KEY INFORMATION EXTRACTION\n\n"
            result += f"**Document:** {meta['filename']}\n"
            result += f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            result += f"---\n\n"
            
            cols_to_analyze = columns if columns else list(df.columns)
            
            result += f"### 📊 Data Overview\n\n"
            result += f"- **Records:** {len(df):,}\n"
            result += f"- **Fields:** {len(df.columns)}\n"
            result += f"- **Completeness:** {((1 - df.isna().sum().sum() / (len(df) * len(df.columns))) * 100):.1f}%\n\n"
            
            result += f"### 📋 Critical Data Points\n\n"
            
            for col in cols_to_analyze:
                if col not in df.columns:
                    continue
                
                result += f"#### **{col}**\n\n"
                col_data = df[col]
                
                result += f"- **Type:** {col_data.dtype}\n"
                result += f"- **Valid:** {col_data.notna().sum():,} ({(col_data.notna().sum()/len(df)*100):.1f}%)\n"
                result += f"- **Missing:** {col_data.isna().sum():,}\n"
                result += f"- **Unique:** {col_data.nunique():,}\n"
                
                if pd.api.types.is_numeric_dtype(col_data):
                    result += f"- **Range:** [{col_data.min():,.2f}, {col_data.max():,.2f}]\n"
                    result += f"- **Mean:** {col_data.mean():,.2f}\n"
                    
                    # Anomalies
                    Q1, Q3 = col_data.quantile(0.25), col_data.quantile(0.75)
                    IQR = Q3 - Q1
                    outliers = col_data[(col_data < Q1 - 1.5*IQR) | (col_data > Q3 + 1.5*IQR)]
                    if len(outliers) > 0:
                        result += f"- **⚠️ Anomalies:** {len(outliers)} outliers\n"
                else:
                    top_vals = col_data.value_counts().head(5)
                    result += f"- **Top 5:**\n"
                    for val, count in top_vals.items():
                        result += f"  - `{val}`: {count:,} ({(count/len(df)*100):.1f}%)\n"
                
                result += "\n"
            
            result += f"---\n\n"
            result += f"**⚠️ IMPORTANT:** Based solely on document data. No external data or assumptions.\n"
            
            # Log
            self.analysis_history[file_id] = self.analysis_history.get(file_id, [])
            self.analysis_history[file_id].append({
                'timestamp': pd.Timestamp.now(),
                'analysis_type': 'key_information_extraction',
                'columns_analyzed': len(cols_to_analyze)
            })
            
            return result
        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def generate_executive_summary(
        self,
        focus_areas: Optional[List[str]] = None,
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None
    ) -> str:
        """
        Generate executive summary.
        DIDE Core: Summarization
        """
        try:
            if file_id not in self.dataframes:
                return "❌ No data loaded."
            
            df = self.dataframes[file_id]
            meta = self.file_metadata[file_id]
            
            result = f"# 📄 EXECUTIVE SUMMARY\n\n"
            result += f"**Document:** {meta['filename']}\n"
            result += f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            result += f"**Format:** {meta.get('format', 'Unknown').upper()}\n\n"
            result += f"---\n\n"
            
            # Overview
            result += f"## 📊 Overview\n\n"
            result += f"- **Records:** {len(df):,}\n"
            result += f"- **Fields:** {len(df.columns)}\n"
            
            completeness = (1 - df.isna().sum().sum() / (len(df) * len(df.columns))) * 100
            result += f"- **Completeness:** {completeness:.1f}%\n"
            
            if meta.get('skipped_rows', 0) > 0:
                result += f"- **Note:** {meta['skipped_rows']:,} rows skipped during processing\n"
            
            result += "\n"
            
            # Key insights
            result += f"## 🔑 Key Insights\n\n"
            
            cols = focus_areas if focus_areas else list(df.columns)[:10]
            
            numeric_cols = df[cols].select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                result += f"### Quantitative\n\n"
                for col in numeric_cols[:5]:
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        result += f"**{col}:** Avg {col_data.mean():,.2f} | Range [{col_data.min():,.2f}-{col_data.max():,.2f}]\n"
                result += "\n"
            
            text_cols = df[cols].select_dtypes(include=['object']).columns
            if len(text_cols) > 0:
                result += f"### Categorical\n\n"
                for col in text_cols[:5]:
                    if df[col].notna().sum() > 0:
                        top = df[col].value_counts().index[0]
                        top_count = df[col].value_counts().values[0]
                        result += f"**{col}:** {df[col].nunique():,} unique | Most common: `{top}` ({top_count:,})\n"
                result += "\n"
            
            # Data quality
            result += f"## ⚠️ Data Quality\n\n"
            
            missing = df.isna().sum()
            problems = missing[missing > 0]
            
            if len(problems) > 0:
                result += f"**Fields with missing data:**\n"
                for col, count in problems.items():
                    pct = (count / len(df)) * 100
                    result += f"- {col}: {count:,} ({pct:.1f}%)\n"
            else:
                result += f"✅ No missing data.\n"
            
            result += f"\n---\n\n"
            result += f"## 📌 Summary\n\n"
            result += f"Document contains **{len(df):,} records** across **{len(df.columns)} fields** "
            result += f"with **{completeness:.1f}% completeness**. "
            
            result += f"\n\n**⚠️ BASIS:** Derived exclusively from loaded document data.\n\n"
            result += f"**📋 DISCLAIMER:** Analytical tool. Not professional analysis/advice substitute.\n"
            
            return result
        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def risk_compliance_assessment(
        self,
        criteria: Dict[str, Any],
        file_id: str = "default",
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None
    ) -> str:
        """
        Identify potential risks, anomalies, or deviations from expected patterns.
        DIDE Core Capability: Risk/Compliance Assessment

        Args:
            criteria: Dictionary of assessment criteria (e.g., {'column': 'value_threshold'})
            file_id: File identifier (default: "default")

        Returns:
            str: Risk and compliance assessment report

        Example:
            criteria = {
                'Age': {'min': 18, 'max': 65},
                'Salary': {'min': 30000},
                'Status': {'required_values': ['Active', 'Pending']}
            }
        """
        try:
            if file_id not in self.dataframes:
                return "❌ **ERROR:** No data loaded. Data extraction required."

            df = self.dataframes[file_id]
            meta = self.file_metadata[file_id]

            result = f"## ⚠️ RISK & COMPLIANCE ASSESSMENT REPORT\n\n"
            result += f"**Document:** {meta['filename']}\n"
            result += f"**Assessment Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            result += f"**Total Records Assessed:** {len(df):,}\n\n"
            result += f"---\n\n"

            total_issues = 0

            result += f"### 🔍 Findings by Criterion\n\n"

            for column, rules in criteria.items():
                if column not in df.columns:
                    result += f"#### ❌ **{column}**\n"
                    result += f"- **Status:** Column not found in document\n\n"
                    continue

                result += f"#### 📋 **{column}**\n\n"
                col_data = df[column]
                column_issues = 0

                # Check for null values
                null_count = col_data.isna().sum()
                if null_count > 0:
                    result += f"- **Missing Data:** {null_count:,} records ({(null_count/len(df)*100):.1f}%) ⚠️\n"
                    column_issues += null_count

                # Numeric checks
                if 'min' in rules and pd.api.types.is_numeric_dtype(col_data):
                    below_min = col_data[col_data < rules['min']]
                    if len(below_min) > 0:
                        result += f"- **Below Minimum ({rules['min']}):** {len(below_min):,} records ⚠️\n"
                        result += f"  Range: [{below_min.min():,.2f} to {below_min.max():,.2f}]\n"
                        column_issues += len(below_min)

                if 'max' in rules and pd.api.types.is_numeric_dtype(col_data):
                    above_max = col_data[col_data > rules['max']]
                    if len(above_max) > 0:
                        result += f"- **Above Maximum ({rules['max']}):** {len(above_max):,} records ⚠️\n"
                        result += f"  Range: [{above_max.min():,.2f} to {above_max.max():,.2f}]\n"
                        column_issues += len(above_max)

                # Categorical checks
                if 'required_values' in rules:
                    invalid = col_data[~col_data.isin(rules['required_values'])]
                    if len(invalid) > 0:
                        result += f"- **Invalid Values:** {len(invalid):,} records not in {rules['required_values']} ⚠️\n"
                        unique_invalid = invalid.value_counts().head(5)
                        result += f"  Top invalid values: {', '.join([f'`{v}`({c})' for v, c in unique_invalid.items()])}\n"
                        column_issues += len(invalid)

                if column_issues == 0:
                    result += f"- **Status:** ✅ No issues detected\n"
                else:
                    result += f"- **Total Issues:** {column_issues:,}\n"

                total_issues += column_issues
                result += "\n"

            # Summary
            result += f"### 📊 Assessment Summary\n\n"
            result += f"| Metric | Value |\n"
            result += f"|--------|-------|\n"
            result += f"| **Total Records** | {len(df):,} |\n"
            result += f"| **Criteria Assessed** | {len(criteria)} |\n"
            result += f"| **Issues Found** | {total_issues:,} |\n"
            result += f"| **Compliance Rate** | {((len(df) - total_issues) / len(df) * 100):.2f}% |\n\n"

            if total_issues == 0:
                result += f"✅ **RESULT:** All records comply with specified criteria.\n\n"
            else:
                result += f"⚠️ **RESULT:** {total_issues:,} potential compliance issues identified.\n\n"

            result += f"---\n\n"
            result += f"**⚠️ IMPORTANT DISCLAIMER:**\n"
            result += f"- This is an informational assessment tool, NOT legal or compliance advice.\n"
            result += f"- Results are based solely on criteria provided and data in the document.\n"
            result += f"- Consult qualified professionals for official compliance determinations.\n"

            return result

        except Exception as e:
            return f"❌ Error during risk assessment: {str(e)}"