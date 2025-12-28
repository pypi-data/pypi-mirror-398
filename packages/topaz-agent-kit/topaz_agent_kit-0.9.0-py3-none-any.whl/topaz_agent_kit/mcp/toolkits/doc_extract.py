"""
Docling-based Document Data Extraction Toolkit
Provides structured data extraction without storage
"""

from typing import Dict, Any, List, Optional, Union
import json
from pathlib import Path
import tempfile

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

from topaz_agent_kit.core.exceptions import MCPError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.json_utils import JSONUtils
from topaz_agent_kit.utils.mcp_utils import invoke_llm
from topaz_agent_kit.mcp.decorators import tool_metadata, ToolTimeout

from fastmcp import FastMCP


class DocExtractMCPTools:
    """
    Document data extraction tools using Docling.
    Extract structured data from forms, invoices, reports without storage.
    """
    
    def __init__(self, llm=None, **kwargs):
        """Initialize DocExtract toolkit with optional LLM client"""
        self._logger = Logger("MCP.DocExtract")
        self._converter = None  # Lazy initialization
        self._llm = llm  # LLM client from MCP server

        
        if self._llm:
            self._logger.success("DocExtract toolkit initialized with LLM client")
        else:
            self._logger.success("DocExtract toolkit initialized (LLM-free mode)")
    
    def _get_converter(self) -> DocumentConverter:
        """Lazy initialization of Docling converter"""
        if self._converter is None:
            self._logger.info("Initializing Docling converter for data extraction...")
            
            # Configure for optimal extraction with MPS acceleration
            pdf_options = PdfPipelineOptions()
            pdf_options.do_table_structure = True  # Critical for forms (MPS supported)
            pdf_options.do_ocr = True  # Handle scanned forms (MPS supported)
            # Note: Formula and code enrichment disabled for MPS compatibility
            # pdf_options.do_formula_enrichment = True  # Disabled - forces CPU fallback
            # pdf_options.do_code_enrichment = True  # Disabled - forces CPU fallback
            
            self._converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)
                }
            )
            
            self._logger.success("Docling converter initialized")
        
        return self._converter
    
    def _safe_export_to_markdown(self, doc) -> str:
        """
        Safely export document to markdown with UTF-8 error handling.
        
        Handles encoding errors gracefully by replacing invalid UTF-8 characters
        instead of failing completely.
        
        Args:
            doc: Docling document object
            
        Returns:
            str: Markdown text with invalid UTF-8 characters replaced
        """
        try:
            raw_text = doc.export_to_markdown()
            # Ensure UTF-8 encoding - replace invalid characters if needed
            if isinstance(raw_text, bytes):
                raw_text = raw_text.decode('utf-8', errors='replace')
            elif isinstance(raw_text, str):
                # Re-encode to handle any invalid UTF-8 sequences
                raw_text = raw_text.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            return raw_text
        except UnicodeDecodeError as e:
            self._logger.warning("UTF-8 encoding error in export_to_markdown, using fallback: {}", e)
            # Try to get text with error handling
            try:
                raw_text = doc.export_to_markdown()
                raw_text = raw_text.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                return raw_text
            except Exception as fallback_error:
                self._logger.error("Fallback text extraction also failed: {}", fallback_error)
                return ""  # Empty text if all extraction fails
        except Exception as e:
            self._logger.warning("Error extracting full text: {}, returning empty string", e)
            return ""  # Empty text if extraction fails
    
    def register(self, mcp: FastMCP) -> None:
        
        @tool_metadata(timeout=ToolTimeout.LONG)
        @mcp.tool(name="doc_extract_structured_data")
        def extract_structured_data(
            file_path: str,
            extraction_schema: Optional[Union[str, Dict[str, str]]] = None
        ) -> Dict[str, Any]:
            """
            Extract structured data from a document (PDF, DOCX, PPTX).
            
            This tool uses Docling's advanced document understanding to extract:
            - Tables (with structure preservation)
            - Form fields and values
            - Key-value pairs
            - Sections and hierarchies
            
            Perfect for claims forms, invoices, applications, etc.
            
            Parameters:
                file_path: Path to document file
                extraction_schema: Optional schema defining what to extract
                    Example: {
                        "claim_number": "text field labeled 'Claim #'",
                        "claim_amount": "currency in 'Amount' field",
                        "claimant_name": "text in 'Name' field"
                    }
            
            Returns:
                Dict containing:
                - success: bool
                - data: Extracted structured data
                - tables: List of tables (with structure)
                - metadata: Document metadata
                - raw_text: Full text (if needed)
            """
            self._logger.input("extract_structured_data INPUT: file_path={}, schema={}", 
                             file_path, extraction_schema)
            
            try:
                # Parse extraction_schema if it's a string (JSON)
                parsed_schema: Optional[Dict[str, str]] = None
                if extraction_schema:
                    if isinstance(extraction_schema, str):
                        # Try to parse JSON string
                        try:
                            parsed = json.loads(extraction_schema)
                            if isinstance(parsed, dict):
                                parsed_schema = parsed
                            else:
                                self._logger.warning("extraction_schema JSON string did not parse to dict, ignoring")
                        except json.JSONDecodeError:
                            # Try JSONUtils for more lenient parsing
                            try:
                                parsed = JSONUtils.parse_json_from_text(extraction_schema)
                                if isinstance(parsed, dict):
                                    parsed_schema = parsed
                                else:
                                    self._logger.warning("extraction_schema did not parse to dict, ignoring")
                            except Exception as e:
                                self._logger.warning("Failed to parse extraction_schema string: {}, ignoring", e)
                    elif isinstance(extraction_schema, dict):
                        parsed_schema = extraction_schema
                
                # Validate file exists
                if not Path(file_path).exists():
                    raise MCPError(f"File not found: {file_path}")
                
                # Convert document
                converter = self._get_converter()
                result = converter.convert(file_path)
                doc = result.document
                
                # Extract metadata
                metadata = {
                    "num_pages": len(doc.pages),
                    "has_tables": any(hasattr(item_tuple[0], 'type') and item_tuple[0].type == 'table' for item_tuple in doc.iterate_items()),
                    "num_tables": sum(1 for item_tuple in doc.iterate_items() if hasattr(item_tuple[0], 'type') and item_tuple[0].type == 'table'),
                    "num_sections": sum(1 for item_tuple in doc.iterate_items() if hasattr(item_tuple[0], 'type') and item_tuple[0].type == 'heading'),
                }
                
                # Extract tables with structure
                tables = []
                for item_tuple in doc.iterate_items():
                    item = item_tuple[0]  # Extract item from tuple
                    page_number = item_tuple[1]  # Extract page number from tuple (1-based)
                    if hasattr(item, 'type') and item.type == 'table':
                        
                        table_data = {
                            "page": page_number,  # Use extracted page number
                            "text": item.text,
                            "rows": getattr(item, 'num_rows', 0),
                            "cols": getattr(item, 'num_cols', 0),
                        }
                        
                        # Try to extract structured table data
                        if hasattr(item, 'table_data'):
                            table_data["structured"] = item.table_data
                        
                        tables.append(table_data)
                
                # Extract key-value pairs (form fields)
                extracted_data = {}
                
                if parsed_schema:
                    # Use schema to guide extraction
                    for field_name, field_description in parsed_schema.items():
                        # Simple keyword-based extraction (can be enhanced with LLM)
                        value = self._extract_field_value(doc, field_name, field_description)
                        extracted_data[field_name] = value
                else:
                    # Auto-extract common patterns
                    extracted_data = self._auto_extract_patterns(doc)
                
                # Get full text for fallback/context
                # Handle UTF-8 encoding errors gracefully
                raw_text = self._safe_export_to_markdown(doc)
                
                result = {
                    "success": True,
                    "data": extracted_data,
                    "tables": tables,
                    "metadata": metadata,
                    "raw_text": raw_text,  # Full text with UTF-8 error handling
                }
                
                self._logger.output("extract_structured_data OUTPUT: {}", {
                    "success": True,
                    "num_fields": len(extracted_data),
                    "num_tables": len(tables),
                    "metadata": metadata
                })
                
                return result
                
            except Exception as e:
                error_msg = f"Failed to extract data: {str(e)}"
                self._logger.error("extract_structured_data ERROR: {}", error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "data": {},
                    "tables": [],
                    "metadata": {}
                }
        
        @tool_metadata(timeout=ToolTimeout.MEDIUM)
        @mcp.tool(name="doc_extract_tables")
        def extract_tables(file_path: str) -> List[Dict[str, Any]]:
            """
            Extract all tables from a document with structure preserved.
            
            Optimized for financial reports, invoices, data sheets.
            
            Parameters:
                file_path: Path to document file
            
            Returns:
                List of tables, each containing:
                - page: Page number
                - text: Table as text
                - rows: Number of rows
                - cols: Number of columns
                - structured: Structured table data (if available)
            """
            self._logger.input("extract_tables INPUT: file_path={}", file_path)
            
            try:
                # Validate file
                if not Path(file_path).exists():
                    raise MCPError(f"File not found: {file_path}")
                
                # Convert document
                converter = self._get_converter()
                result = converter.convert(file_path)
                doc = result.document
                
                # Extract all tables
                tables = []
                for item_tuple in doc.iterate_items():
                    item = item_tuple[0]  # Extract item from tuple
                    page_number = item_tuple[1]  # Extract page number from tuple (1-based)
                    if hasattr(item, 'type') and item.type == 'table':
                        table_data = {
                            "page": page_number,  # Use extracted page number
                            "text": item.text,
                            "rows": getattr(item, 'num_rows', 0),
                            "cols": getattr(item, 'num_cols', 0),
                        }
                        
                        if hasattr(item, 'table_data'):
                            table_data["structured"] = item.table_data
                        
                        tables.append(table_data)
                
                self._logger.output("extract_tables OUTPUT: {} tables extracted", len(tables))
                return tables
                
            except Exception as e:
                error_msg = f"Failed to extract tables: {str(e)}"
                self._logger.error("extract_tables ERROR: {}", error_msg)
                return []
        
        @tool_metadata(timeout=ToolTimeout.QUICK)
        @mcp.tool(name="doc_extract_metadata")
        def extract_metadata(file_path: str) -> Dict[str, Any]:
            """
            Extract document metadata and structure information.
            
            Parameters:
                file_path: Path to document file
            
            Returns:
                Dict containing document metadata:
                - num_pages: Total pages
                - has_tables: Boolean
                - num_tables: Count
                - num_sections: Count
                - num_images: Count
                - file_size: Bytes
            """
            self._logger.input("extract_metadata INPUT: file_path={}", file_path)
            
            try:
                # Validate file
                if not Path(file_path).exists():
                    raise MCPError(f"File not found: {file_path}")
                
                # Get file stats
                file_path_obj = Path(file_path)
                file_size = file_path_obj.stat().st_size
                
                # Convert document (lightweight - only structure)
                converter = self._get_converter()
                result = converter.convert(file_path)
                doc = result.document
                
                # Extract metadata with safe type checking
                metadata = {
                    "num_pages": len(doc.pages),
                    "has_tables": any(hasattr(item_tuple[0], 'type') and item_tuple[0].type == 'table' for item_tuple in doc.iterate_items()),
                    "num_tables": sum(1 for item_tuple in doc.iterate_items() if hasattr(item_tuple[0], 'type') and item_tuple[0].type == 'table'),
                    "num_sections": sum(1 for item_tuple in doc.iterate_items() if hasattr(item_tuple[0], 'type') and item_tuple[0].type == 'heading'),
                    "num_images": sum(1 for item_tuple in doc.iterate_items() if hasattr(item_tuple[0], 'type') and item_tuple[0].type == 'image'),
                    "file_size": file_size,
                }
                
                self._logger.output("extract_metadata OUTPUT: {}", metadata)
                return metadata
                
            except Exception as e:
                error_msg = f"Failed to extract metadata: {str(e)}"
                self._logger.error("extract_metadata ERROR: {}", error_msg)
                return {"error": error_msg}
    
    def _extract_field_value(self, doc, field_name: str, field_description: str) -> Any:
        """Extract specific field value using LLM-based extraction for better accuracy"""
        try:
            # Get document text and structure
            full_text = self._safe_export_to_markdown(doc)
            
            # Try LLM-based extraction first
            llm_result = self._extract_with_llm(field_name, field_description, full_text)
            if llm_result:
                return llm_result
            
            # Fallback to keyword search if LLM fails
            return self._extract_with_keywords(field_name, full_text)
            
        except Exception as e:
            self._logger.warning("LLM extraction failed, falling back to keywords: {}", e)
            return self._extract_with_keywords(field_name, self._safe_export_to_markdown(doc))
    
    def _extract_with_llm(self, field_name: str, field_description: str, document_text: str) -> Any:
        """Use LLM to extract specific field value with high accuracy"""
        try:
            # Use LLM client passed from MCP server
            if not self._llm:
                self._logger.debug("No LLM client available, skipping LLM extraction")
                return None
            
            # Create extraction prompt
            prompt = f"""
                Extract the value for "{field_name}" from the document below.

                Field Description: {field_description}

                Document Text:
                {document_text}  # Limit to avoid token limits

                Instructions:
                1. Find the exact value for "{field_name}" in the document
                2. Return ONLY the extracted value, nothing else
                3. If not found, return "NOT_FOUND"
                4. For dates, use format: YYYY-MM-DD
                5. For amounts, include currency symbol if present
                6. For names, use full name as written

                Extracted Value:
                """

            # Call LLM using centralized utility
            result = invoke_llm(self._llm, prompt)
            
            # Validate result
            if result and result != "NOT_FOUND" and len(result) < 200:  # Reasonable length check
                self._logger.debug("LLM extracted {}: {}", field_name, result)
                return result
            
            return None
            
        except Exception as e:
            self._logger.warning("LLM extraction failed for {}: {}", field_name, e)
            return None
    
    def _extract_with_keywords(self, field_name: str, document_text: str) -> Any:
        """Fallback keyword-based extraction"""
        keywords = field_name.replace("_", " ").split()
        
        for keyword in keywords:
            if keyword.lower() in document_text.lower():
                # Find context around keyword
                idx = document_text.lower().find(keyword.lower())
                context = document_text[max(0, idx-50):min(len(document_text), idx+100)]
                return context.strip()
        
        return None
    
    def _auto_extract_patterns(self, doc) -> Dict[str, Any]:
        """Auto-extract common patterns using LLM + regex for better accuracy"""
        import re
        
        full_text = self._safe_export_to_markdown(doc)
        
        # Try LLM-based pattern extraction first
        llm_patterns = self._extract_patterns_with_llm(full_text)
        
        # Fallback to regex patterns
        regex_patterns = self._extract_patterns_with_regex(full_text)
        
        # Combine results (LLM takes precedence)
        combined = {**regex_patterns, **llm_patterns}
        
        return combined
    
    def _extract_patterns_with_llm(self, document_text: str) -> Dict[str, Any]:
        """Use LLM to extract common patterns with better context understanding"""
        try:
            prompt = f"""
                Extract the following information from the document below. Return a JSON object with the extracted data.

                Document Text:
                {document_text}

                Extract:
                1. All dates (format as YYYY-MM-DD)
                2. All monetary amounts (include currency)
                3. All email addresses
                4. All phone numbers
                5. All ID numbers (SSN, account numbers, etc.)
                6. All names (person names, company names)

                Return format:
                {{
                    "dates": ["2024-01-15", "2024-02-20"],
                    "amounts": ["$1,250.00", "€500.00"],
                    "emails": ["john@example.com"],
                    "phones": ["(555) 123-4567"],
                    "ids": ["123-45-6789", "ACC-789456"],
                    "names": ["John Smith", "Acme Corp"]
                }}

                If no items found for a category, use empty array [].

                Extracted Data:
                """

            result = invoke_llm(self._llm, prompt)
            
            # Use JSONUtils for robust JSON parsing with automatic fixes
            try:
                parsed = JSONUtils.parse_json_from_text(result, expect_json=True)
                self._logger.debug("LLM extracted patterns using JSONUtils: {}", list(parsed.keys()) if isinstance(parsed, dict) else "non-dict result")
                return parsed if isinstance(parsed, dict) else {}
            except ValueError as e:
                # If JSONUtils fails with expect_json=True, log debug info and return empty dict
                self._logger.debug("Failed to parse LLM pattern extraction JSON using JSONUtils: {}. Raw response: {}", e, result[:200])
                return {}
                
        except Exception as e:
            self._logger.warning("LLM pattern extraction failed: {}", e)
            return {}
    
    def _extract_patterns_with_regex(self, document_text: str) -> Dict[str, Any]:
        """Fallback regex-based pattern extraction"""
        import re
        
        patterns = {
            "dates": r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            "amounts": r'\$[\d,]+\.?\d*',
            "emails": r'[\w\.-]+@[\w\.-]+\.\w+',
            "phones": r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        }
        
        extracted = {}
        for field_type, pattern in patterns.items():
            matches = re.findall(pattern, document_text)
            if matches:
                extracted[field_type] = matches
        
        return extracted
