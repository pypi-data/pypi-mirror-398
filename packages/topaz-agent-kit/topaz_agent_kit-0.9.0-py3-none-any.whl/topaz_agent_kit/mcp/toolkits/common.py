import re
from topaz_agent_kit.utils.logger import Logger
from fastmcp import FastMCP
import os
import json
import urllib.parse
import urllib.request
import yaml
import pytesseract
from PIL import Image
import pdfplumber
from amadeus import Client, ResponseError
from dotenv import load_dotenv, find_dotenv

class CommonMCPTools:
    def __init__(self, **kwargs):
        self._logger = Logger("MCP.Common")
    
    def _load_amadeus_client(self) -> Client:
        """Load Amadeus client configuration from environment variables"""

        # Load environment variables
        env_file = find_dotenv()
        if env_file:
            self._logger.debug(f"Loading environment from: {env_file}")
            load_dotenv(env_file)
        else:
            self._logger.debug("No .env file found")
            raise ValueError("No .env file found")

        client_id = os.getenv("AMADEUS_CLIENT_ID")
        client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
        if not client_id or not client_secret:
            self._logger.error("Missing AMADEUS_CLIENT_ID/AMADEUS_CLIENT_SECRET env vars")
            raise RuntimeError("Missing AMADEUS_CLIENT_ID/AMADEUS_CLIENT_SECRET env vars")
        amadeus = Client(client_id=client_id, client_secret=client_secret)
        return amadeus

    def _log_response_error(self, tool_name: str, e: ResponseError) -> None:
        """Helper method to log detailed ResponseError information."""
        error_details = {
            "status_code": getattr(e, "status_code", None),
            "description": getattr(e, "description", None),
            "response": getattr(e, "response", None),
            "code": getattr(e, "code", None),
        }
        # Try to extract response body if available
        response_body = None
        try:
            if hasattr(e, "response") and e.response:
                response_body = getattr(e.response, "body", None)
        except Exception:
            pass
        
        self._logger.error("SDK {} failed: status={} code={} description={} response={} body={}", 
                          tool_name,
                          error_details.get("status_code"), 
                          error_details.get("code"),
                          error_details.get("description"),
                          error_details.get("response"),
                          response_body)

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool(name="common_ocr_reader")
        def ocr_reader(file_path: str) -> str:
            """Extract text from PDF or Image file. [roles: intake, parser]"""
            self._logger.input("ocr_reader INPUT: file_path={}", file_path)
            try:
                if file_path.lower().endswith(".pdf"):
                    text = ""
                    with pdfplumber.open(file_path) as pdf:
                        for page in pdf.pages:
                            text += page.extract_text() + "\n"
                    self._logger.output("ocr_reader OUTPUT: {}", text.strip())
                    return text.strip()
                else:
                    image = Image.open(file_path)
                    text = pytesseract.image_to_string(image)
                    result = text.strip()
                    self._logger.output("ocr_reader OUTPUT: {}", result)
                    return result
            except Exception as e:
                self._logger.error("ocr_reader failed: {}", e)
                return ""

        @mcp.tool(name="common_form_parser")
        def form_parser(text: str) -> dict:
            """Extract structured claim fields from raw text. [roles: intake, parser]"""
            self._logger.debug("form_parser INPUT: text_len={}", len(text or ""))
            # Simple regex-based extraction as example
            policy_number_match = re.search(r"Policy\s*Number[:\s]*([A-Z0-9]+)", text, re.I)
            incident_date_match = re.search(r"Date\s*of\s*Incident[:\s]*(\d{4}-\d{2}-\d{2})", text, re.I)
            amount_match = re.search(r"Amount\s*Requested[:\s]*\$?([\d,]+\.?\d*)", text, re.I)
            result = {
                "policyholder_name": "John Doe",  # Could improve with NER
                "policy_number": policy_number_match.group(1) if policy_number_match else "",
                "incident_date": incident_date_match.group(1) if incident_date_match else "",
                "claim_type": "Auto",  # placeholder
                "amount_requested": float(amount_match.group(1).replace(",", "")) if amount_match else 0.0,
                "description": text[:200]  # first 200 chars as summary
            }
            self._logger.output("form_parser OUTPUT: {}", result)
            return result

        @mcp.tool(name="common_entity_normalizer")
        def entity_normalizer(entity_type: str, value: str) -> str:
            """Normalize names, dates, addresses, etc. [roles: intake, cleaner]"""
            self._logger.input("entity_normalizer INPUT: entity_type={}, value={}", entity_type, value)
            if entity_type.lower() == "date":
                # Simple YYYY-MM-DD check
                if re.match(r"\d{4}-\d{2}-\d{2}", value):
                    self._logger.output("entity_normalizer OUTPUT: {}", value)
                    return value
                self._logger.output("entity_normalizer OUTPUT: 1970-01-01")
                return "1970-01-01"
            self._logger.output("entity_normalizer OUTPUT: {}", value.strip().title())
            return value.strip().title()

        @mcp.tool(name="common_read_image")
        def read_image(file_path: str) -> dict:
            """Read image file and return data with metadata. [roles: intake, parser]"""
            from topaz_agent_kit.utils.file_utils import FileUtils
            self._logger.input("read_image INPUT: file_path={}", file_path)
            try:
                result = FileUtils.read_image_file(file_path)
                # Remove raw bytes field for JSON serialization (keep base64 instead)
                # The 'data' field contains binary bytes which can't be serialized to JSON
                json_safe_result = {
                    "path": result["path"],
                    "name": result["name"],
                    "base64": result.get("base64", ""),  # base64-encoded data for JSON serialization
                    "metadata": result["metadata"]
                }
                self._logger.output("read_image OUTPUT: image={}, size={} bytes", 
                                  json_safe_result["name"], json_safe_result["metadata"]["size_bytes"])
                return json_safe_result
            except Exception as e:
                self._logger.error("read_image failed: {}", e)
                raise

        @mcp.tool(name="common_read_document")
        def read_document(file_path: str) -> dict:
            """Read document file and return text with metadata. [roles: intake, parser]"""
            from topaz_agent_kit.utils.file_utils import FileUtils
            self._logger.input("read_document INPUT: file_path={}", file_path)
            try:
                result = FileUtils.read_document_file(file_path)
                # Remove raw bytes field for JSON serialization (keep base64 instead)
                # The 'data' field contains binary bytes which can't be serialized to JSON
                json_safe_result = {
                    "path": result["path"],
                    "name": result["name"],
                    "base64": result.get("base64", ""),  # base64-encoded data for JSON serialization
                    "text": result.get("text", ""),  # extracted text (if available)
                    "metadata": result["metadata"]
                }
                self._logger.output("read_document OUTPUT: document={}, size={} bytes", 
                                  json_safe_result["name"], json_safe_result["metadata"]["size_bytes"])
                return json_safe_result
            except Exception as e:
                self._logger.error("read_document failed: {}", e)
                raise
