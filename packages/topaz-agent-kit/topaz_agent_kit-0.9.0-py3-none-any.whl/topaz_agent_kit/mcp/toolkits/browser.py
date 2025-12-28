import json
import os
import requests
from dotenv import load_dotenv, find_dotenv
from topaz_agent_kit.utils.logger import Logger

from fastmcp import FastMCP

class BrowserMCPTools:
    def __init__(self, **kwargs):
        self._logger = Logger("MCP.Browser")
        self._browserless_api_key = None
        self._load_browserless_config() # Load config when the class is initialized

    def _load_browserless_config(self):
        """Load Browserless configuration lazily when needed"""
        
        # Load environment variables
        env_file = find_dotenv()
        if env_file:
            self._logger.debug(f"Loading environment from: {env_file}")
            load_dotenv(env_file)
        else:
            self._logger.debug("No .env file found")
            raise ValueError("No .env file found")
        
        # Load BROWSERLESS_API_KEY
        if self._browserless_api_key is None:
            self._browserless_api_key = os.environ.get("BROWSERLESS_API_KEY")
            if not self._browserless_api_key:
                self._logger.warning("BROWSERLESS_API_KEY not found in environment variables")
                raise ValueError("BROWSERLESS_API_KEY not found in environment variables")
            else:
                self._logger.debug("BROWSERLESS_API_KEY loaded successfully")

    def _extract_main_text(self, html: str) -> str:
        """Extract readable main content from HTML using readability, fallback to BeautifulSoup."""
        # Try readability first (usually produces article-like main content)
        try:
            from readability import Document  # type: ignore
            from bs4 import BeautifulSoup  # type: ignore

            doc = Document(html)
            summary_html = doc.summary(html_partial=True)
            soup = BeautifulSoup(summary_html, "lxml")
            text = soup.get_text(separator="\n", strip=True)
            if text:
                return text
        except Exception:
            pass
        # Fallback: strip scripts/styles and return full-page text
        try:
            from bs4 import BeautifulSoup  # type: ignore
            soup = BeautifulSoup(html, "lxml")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)
        except Exception:
            return html

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool(name="browser_scrape_website_content")
        def scrape_website_content(website):
            """Scrape a website's content using Browserless API."""
            self._logger.input(f"scrape_website_content INPUT: website={website}")
            
            try:
                # Construct the API URL (mask token in logs)
                token_masked = self._browserless_api_key[:4] + "***"
                api_url = f"https://production-sfo.browserless.io/content?token={self._browserless_api_key}"
                self._logger.debug(f"Preparing request to Browserless API: https://.../content?token={token_masked}")
                
                # Prepare request data
                payload = json.dumps({"url": website})
                headers = {
                    "cache-control": "no-cache",
                    "content-type": "application/json"
                }
                
                # Make the request (SSL verification enabled; rely on OS/ENV trust)
                self._logger.debug("Sending request to Browserless API...")
                response = requests.post(
                    api_url,
                    headers=headers,
                    data=payload,
                    timeout=30
                )
                
                # Check for HTTP errors
                response.raise_for_status()
                self._logger.output("scrape_website_content OUTPUT: Successfully received response from Browserless API")
                
                # Process the response
                self._logger.debug("Processing HTML content with readability/BeautifulSoup...")
                content = self._extract_main_text(response.text)
                
                if not content.strip():
                    self._logger.warning("No content could be extracted from the website.")
                    return "No content could be extracted from the website."
                
                self._logger.output(f"scrape_website_content OUTPUT: {content}")
                return content
                
            except requests.exceptions.SSLError as e:
                error_msg = f"SSL Error occurred while connecting to {website}: {str(e)}"
                self._logger.error(error_msg)
                return error_msg
            except requests.exceptions.RequestException as e:
                error_msg = f"Error occurred while fetching {website}: {str(e)}"
                self._logger.error(error_msg)
                return error_msg
            except Exception as e:
                error_msg = f"An unexpected error occurred while processing {website}: {str(e)}"
                self._logger.error(error_msg, exc_info=True)  # Include stack trace
                return error_msg
