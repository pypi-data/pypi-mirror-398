"""
LlamaIndex integration utilities for InstaVM

Simple utilities to use InstaVM with LlamaIndex function tools and agents.
"""

import json
from typing import Any, Dict, List, Optional

try:
    from llama_index.core.tools import FunctionTool
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    try:
        from llama_index.tools import FunctionTool
        LLAMAINDEX_AVAILABLE = True
    except ImportError:
        LLAMAINDEX_AVAILABLE = False
        # Dummy class when not available
        class FunctionTool:
            pass

def get_llamaindex_tools(instavm_client) -> List:
    """Get LlamaIndex function tools for InstaVM"""
    if not LLAMAINDEX_AVAILABLE:
        raise ImportError("LlamaIndex not installed. Run: pip install llama-index")
    
    # Shared browser session reference
    browser_session = {"current": None}
    
    def create_browser_session(width: int = 1920, height: int = 1080) -> str:
        """Create a new browser session for web automation"""
        try:
            session = instavm_client.browser.create_session(width, height)
            browser_session["current"] = session
            return f"Created browser session {session.session_id}"
        except Exception as e:
            return f"Error creating browser session: {str(e)}"
    
    def navigate_to_url(url: str) -> str:
        """Navigate browser to a URL"""
        if not browser_session["current"]:
            return "Error: No browser session. Create one first with create_browser_session"
        try:
            browser_session["current"].navigate(url)
            return f"Navigated to {url}"
        except Exception as e:
            return f"Error navigating to {url}: {str(e)}"
    
    def extract_page_content(selector: str = "body", max_length: int = 10000) -> str:
        """Extract text content from current page"""
        if not browser_session["current"]:
            return "Error: No browser session active"
        try:
            elements = browser_session["current"].extract_elements(selector, ["text"])
            if elements:
                content = elements[0].get("text", "")[:max_length]
                return content
            return "No content found"
        except Exception as e:
            return f"Error extracting content: {str(e)}"
    
    def extract_elements(selector: str, attributes: Optional[List[str]] = None, max_results: int = 10) -> str:
        """Extract elements using CSS selectors"""
        if not browser_session["current"]:
            return "Error: No browser session active"
        if attributes is None:
            attributes = ["text"]
        try:
            elements = browser_session["current"].extract_elements(selector, attributes)
            limited = elements[:max_results]
            return json.dumps({"elements": limited, "count": len(elements)})
        except Exception as e:
            return f"Error extracting elements: {str(e)}"
    
    def click_element(selector: str, timeout: int = 10000) -> str:
        """Click a page element"""
        if not browser_session["current"]:
            return "Error: No browser session active"
        try:
            browser_session["current"].click(selector, timeout=timeout)
            return f"Clicked element {selector}"
        except Exception as e:
            return f"Error clicking element: {str(e)}"
    
    def take_screenshot(full_page: bool = True) -> str:
        """Take a screenshot of current page"""
        if not browser_session["current"]:
            return "Error: No browser session active"
        try:
            screenshot = browser_session["current"].screenshot(full_page=full_page)
            return f"Screenshot taken ({len(screenshot)} chars)"
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"
    
    def execute_python_code(code: str) -> str:
        """Execute Python code in the cloud. Use !command for bash commands like !pip install"""
        try:
            result = instavm_client.execute(code, language="python")
            return str(result)
        except Exception as e:
            return f"Error executing code: {str(e)}"
    
    def scroll_page(x: int = 0, y: int = 500) -> str:
        """Scroll the page to coordinates"""
        if not browser_session["current"]:
            return "Error: No browser session active"
        try:
            browser_session["current"].scroll(x=x, y=y)
            return f"Scrolled to ({x}, {y})"
        except Exception as e:
            return f"Error scrolling: {str(e)}"
    
    def wait_for_element(selector: str, timeout: int = 10000) -> str:
        """Wait for element to become visible"""
        if not browser_session["current"]:
            return "Error: No browser session active"
        try:
            browser_session["current"].wait_for("visible", selector, timeout)
            return f"Element {selector} is now visible"
        except Exception as e:
            return f"Error waiting for element: {str(e)}"
    
    # Create function tools
    tools = [
        FunctionTool.from_defaults(fn=create_browser_session),
        FunctionTool.from_defaults(fn=navigate_to_url),
        FunctionTool.from_defaults(fn=extract_page_content),
        FunctionTool.from_defaults(fn=extract_elements),
        FunctionTool.from_defaults(fn=click_element),
        FunctionTool.from_defaults(fn=take_screenshot),
        FunctionTool.from_defaults(fn=execute_python_code),
        FunctionTool.from_defaults(fn=scroll_page),
        FunctionTool.from_defaults(fn=wait_for_element)
    ]
    
    return tools

# Simple usage example:
"""
from instavm import InstaVM
from instavm.integrations.llamaindex import get_llamaindex_tools  
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import ReActAgent

# Setup
instavm_client = InstaVM(api_key="your_key")
llm = OpenAI(api_key="your_key", model="gpt-4")

# Get tools
tools = get_llamaindex_tools(instavm_client)

# Create agent (direct initialization, not from_tools)
agent = ReActAgent(tools=tools, llm=llm, verbose=True)

# Use agent
response = agent.chat("Go to example.com and tell me what the main content is")
print(response)
"""