import json
import os
import requests
from dotenv import load_dotenv, find_dotenv
from topaz_agent_kit.utils.logger import Logger

from fastmcp import FastMCP

class SerperApiMCPTools():
    def __init__(self, **kwargs):
        self._logger = Logger("MCP.SerperApi")
        self._serper_api_key = None
        self._top_result_to_return = 0
        self._load_serper_config() # Load config when the class is initialized
    
    def _load_serper_config(self):
        """Load Serper configuration from environment variables"""
        # Load environment variables
        env_file = find_dotenv()
        if env_file:
            self._logger.debug(f"Loading environment from: {env_file}")
            load_dotenv(env_file)
        else:
            self._logger.debug("No .env file found")
            raise ValueError("No .env file found")
        
        # Load SERPER_API_KEY
        if self._serper_api_key is None:
            self._serper_api_key = os.environ.get("SERPER_API_KEY")
            if not self._serper_api_key:
                self._logger.warning("SERPER_API_KEY not found in environment variables")
                raise ValueError("SERPER_API_KEY not found in environment variables")
            else:
                self._logger.debug("SERPER_API_KEY loaded successfully")
        
        # Load TOP_RESULTS_TO_RETURN (default to 5 if not specified)
        if self._top_result_to_return == 0:
            top_results_str = os.environ.get("TOP_RESULTS_TO_RETURN", "5")
            try:
                self._top_result_to_return = int(top_results_str)
                self._logger.debug(f"TOP_RESULTS_TO_RETURN set to: {self._top_result_to_return}")
            except ValueError:
                self._logger.warning(f"Invalid TOP_RESULTS_TO_RETURN value '{top_results_str}', using default: 5")
                self._top_result_to_return = 5

    def search_internet(self, query: str) -> str:
        """Search the internet about a given topic and return relevant results"""
        self._logger.input("search_internet INPUT: query={}", query)
        top_result_to_return = self._top_result_to_return
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': self._serper_api_key,
            'content-type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        results = response.json()['organic']
        string = []
        for result in results[:top_result_to_return]:
            try:
                string.append('\n'.join([
                    f"Title: {result['title']}", 
                    f"Link: {result['link']}",
                    f"Snippet: {result['snippet']}", "--------------------------------------"
                ]))
            except KeyError:
                next
        result = '\n'.join(string)
        self._logger.output("search_internet OUTPUT: {}", result)
        return result

    def search_news(self, query: str) -> str:
        """Search news about a given topic and return relevant results"""
        self._logger.input("search_news INPUT: query={}", query)
        top_result_to_return = self._top_result_to_return
        url = "https://google.serper.dev/news"
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': self._serper_api_key,
            'content-type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        results = response.json()['news']
        string = []
        for result in results[:top_result_to_return]:
            try:
                string.append('\n'.join([
                    f"Title: {result['title']}", 
                    f"Link: {result['link']}",
                    f"Snippet: {result['snippet']}", "--------------------------------------"
                ]))
            except KeyError:
                next
        result = '\n'.join(string)
        self._logger.output("search_news OUTPUT: {}", result)
        return result

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool(name="serper_api_search_internet")
        def search_internet(query):
            """Useful to search the internet about a a given topic and return relevant results"""
            return self.search_internet(query)

        @mcp.tool(name="serper_api_search_news")
        def search_news(query):
            """Useful to search news about a given topic and return relevant results"""
            return self.search_news(query)
