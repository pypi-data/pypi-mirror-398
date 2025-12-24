# ============================================================================
# File: agentapps/tools.py
# ============================================================================

"""Tool implementations for AgentApps"""

from typing import Any, Dict, Optional, Callable
from abc import ABC, abstractmethod
import json


class Tool(ABC):
    """Base class for agent tools"""
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        """
        Initialize a tool
        
        Args:
            name: Tool name (defaults to class name)
            description: Tool description
        """
        self.name = name or self.__class__.__name__
        self.description = description or "No description provided"
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the tool"""
        pass
    
    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert tool to OpenAI function calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters()
            }
        }
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters schema"""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class WebSearchTool(Tool):
    """Tool for searching the web using DuckDuckGo"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for current information, news, and answers to questions"
        )
    
    def execute(self, query: str, max_results: int = 5) -> str:
        """
        Execute web search
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Formatted search results as string
        """
        try:
            # Try new package name first
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                try:
                    from ddgs import DDGS
                except ImportError:
                    return "Error: DuckDuckGo search package not installed. Install with: pip install -U duckduckgo-search"
            
            results = []
            
            try:
                # Use the DDGS context manager
                ddgs = DDGS()
                search_results = list(ddgs.text(query, max_results=max_results))
                
                if not search_results:
                    # Try alternative search method
                    search_results = list(ddgs.text(query, region='wt-wt', max_results=max_results))
                
                for idx, result in enumerate(search_results, 1):
                    title = result.get('title', 'No title')
                    href = result.get('href', result.get('link', 'No URL'))
                    body = result.get('body', result.get('snippet', 'No description'))
                    
                    results.append(
                        f"{idx}. {title}\n"
                        f"   URL: {href}\n"
                        f"   {body}\n"
                    )
                
            except Exception as search_error:
                return f"Search error: {str(search_error)}. Try rephrasing your query."
            
            if results:
                return "\n".join(results)
            else:
                return "No results found. Try a different search query or be more specific."
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on the web"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }


class WebScraperTool(Tool):
    """Tool for scraping content from a URL"""
    
    def __init__(self):
        super().__init__(
            name="web_scraper",
            description="Fetch and extract text content from a specific URL"
        )
    
    def execute(self, url: str) -> str:
        """
        Scrape content from URL
        
        Args:
            url: The URL to scrape
            
        Returns:
            Text content from the URL
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            import time
            
            # Better headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Try to fetch the URL with retries
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
                    response.raise_for_status()
                    break
                except requests.RequestException as e:
                    if attempt == max_retries - 1:
                        return f"Error accessing URL after {max_retries} attempts: {str(e)}"
                    time.sleep(2)
            
            # Check if we got actual content
            if len(response.content) < 100:
                return "Error: The page appears to be empty or blocked."
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
                element.decompose()
            
            # Try to find main content areas first
            main_content = None
            for selector in ['main', 'article', '[role="main"]', '.content', '#content', '.main-content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # If no main content found, use body
            if not main_content:
                main_content = soup.find('body')
            
            if not main_content:
                return "Error: Could not extract content from the page."
            
            # Get text
            text = main_content.get_text(separator=' ', strip=True)
            
            # Clean up text - remove extra whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Remove very short words and clean up
            words = text.split()
            text = ' '.join(words)
            
            if len(text) < 50:
                return "Error: Not enough content extracted from the page. The page may require JavaScript or have anti-scraping measures."
            
            # Limit to reasonable size (increased from 2000 to 3000)
            if len(text) > 3000:
                text = text[:3000] + "... (content truncated for length)"
            
            return text
            
        except ImportError:
            return "Error: Required packages not installed. Install with: pip install requests beautifulsoup4"
        except Exception as e:
            return f"Error scraping URL: {str(e)}"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to scrape content from"
                }
            },
            "required": ["url"]
        }


class SimpleWebSearchTool(Tool):
    """Simplified web search using direct HTTP requests (fallback)"""
    
    def __init__(self):
        super().__init__(
            name="simple_web_search",
            description="Search the web for information using a simple HTTP-based search"
        )
    
    def execute(self, query: str) -> str:
        """
        Execute simple web search
        
        Args:
            query: Search query
            
        Returns:
            Search results as formatted text
        """
        try:
            import requests
            from urllib.parse import quote
            
            # Use DuckDuckGo HTML version (no API needed)
            encoded_query = quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse results (basic HTML parsing)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            result_divs = soup.find_all('div', class_='result')[:5]
            
            for idx, div in enumerate(result_divs, 1):
                title_tag = div.find('a', class_='result__a')
                snippet_tag = div.find('a', class_='result__snippet')
                
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    url = title_tag.get('href', 'No URL')
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else "No description"
                    
                    results.append(
                        f"{idx}. {title}\n"
                        f"   URL: {url}\n"
                        f"   {snippet}\n"
                    )
            
            if results:
                return "\n".join(results)
            else:
                return "No results found. The search service may be temporarily unavailable."
                
        except ImportError:
            return "Error: Required packages not installed. Install with: pip install requests beautifulsoup4"
        except Exception as e:
            return f"Search error: {str(e)}"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }


class SearchSummaryTool(Tool):
    """Get detailed search results with snippets (no scraping needed)"""
    
    def __init__(self):
        super().__init__(
            name="search_with_snippets",
            description="Search the web and get detailed snippets from search results without needing to scrape individual pages. Good for financial data, news, and quick facts."
        )
    
    def execute(self, query: str, max_results: int = 5) -> str:
        """
        Execute search and return detailed snippets
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            Detailed search results with snippets
        """
        try:
            # Try new package first
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                from ddgs import DDGS
            
            ddgs = DDGS()
            
            # Get text results with snippets
            results = []
            search_results = list(ddgs.text(query, max_results=max_results))
            
            for idx, result in enumerate(search_results, 1):
                title = result.get('title', 'No title')
                href = result.get('href', result.get('link', 'No URL'))
                body = result.get('body', result.get('snippet', 'No description'))
                
                # Format with more detail
                results.append(
                    f"Result {idx}:\n"
                    f"Title: {title}\n"
                    f"URL: {href}\n"
                    f"Summary: {body}\n"
                    f"{'-'*50}\n"
                )
            
            if results:
                return "\n".join(results)
            else:
                return "No results found. Try rephrasing your query."
                
        except Exception as e:
            return f"Search error: {str(e)}"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }


class PythonTool(Tool):
    """Tool for executing Python code"""
    
    def __init__(self):
        super().__init__(
            name="python_executor",
            description="Execute Python code and return the result"
        )
    
    def execute(self, code: str) -> str:
        """Execute Python code safely"""
        try:
            # Create a restricted namespace
            namespace = {"__builtins__": __builtins__}
            exec(code, namespace)
            return f"Code executed successfully. Namespace: {list(namespace.keys())}"
        except Exception as e:
            return f"Error executing code: {str(e)}"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute"
                }
            },
            "required": ["code"]
        }


class CalculatorTool(Tool):
    """Tool for mathematical calculations"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform mathematical calculations and return the result"
        )
    
    def execute(self, expression: str) -> str:
        """
        Evaluate a mathematical expression
        
        Args:
            expression: Mathematical expression to evaluate
            
        Returns:
            Result of the calculation
        """
        try:
            # Use eval with restricted namespace for safety
            allowed_names = {
                k: v for k, v in __builtins__.__dict__.items()
                if k in ['abs', 'min', 'max', 'sum', 'round', 'pow']
            }
            
            # Add math functions
            import math
            allowed_names.update({
                'sqrt': math.sqrt,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'pi': math.pi,
                'e': math.e
            })
            
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return f"Result: {result}"
            
        except Exception as e:
            return f"Error calculating: {str(e)}"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/2)')"
                }
            },
            "required": ["expression"]
        }


class CustomTool(Tool):
    """Custom tool with user-defined function"""
    
    def __init__(
        self, 
        name: str, 
        description: str,
        function: Callable,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Create a custom tool
        
        Args:
            name: Tool name
            description: Tool description
            function: Function to execute
            parameters: Parameter schema
        """
        super().__init__(name, description)
        self.function = function
        self.parameters = parameters or {"type": "object", "properties": {}}
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute the custom function"""
        return self.function(*args, **kwargs)
    
    def get_parameters(self) -> Dict[str, Any]:
        return self.parameters

