"""
OpenAI integration utilities for InstaVM

Simple utilities to use InstaVM with OpenAI function calling.
No complex classes - just plug-and-play functions.
"""

import json
from typing import Dict, List, Any, Optional

def get_tools() -> List[Dict[str, Any]]:
    """Get OpenAI function calling tool definitions for InstaVM"""
    return [
        {
            "type": "function",
            "function": {
                "name": "create_browser_session",
                "description": "Create a new browser session for web automation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "width": {"type": "integer", "description": "Browser width", "default": 1920},
                        "height": {"type": "integer", "description": "Browser height", "default": 1080}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "navigate_to_url", 
                "description": "Navigate browser to URL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to navigate to"}
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "extract_page_content",
                "description": "Extract text content from page",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector", "default": "body"},
                        "max_length": {"type": "integer", "description": "Max content length", "default": 10000}
                    }
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "extract_elements",
                "description": "Extract elements using CSS selector",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"},
                        "attributes": {"type": "array", "items": {"type": "string"}, "description": "Attributes to extract", "default": ["text"]},
                        "max_results": {"type": "integer", "description": "Max results", "default": 10}
                    },
                    "required": ["selector"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "click_element",
                "description": "Click a page element",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"},
                        "timeout": {"type": "integer", "description": "Timeout ms", "default": 10000}
                    },
                    "required": ["selector"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "take_screenshot",
                "description": "Take page screenshot", 
                "parameters": {
                    "type": "object",
                    "properties": {
                        "full_page": {"type": "boolean", "description": "Full page capture", "default": True}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_python_code",
                "description": "Execute Python code. Use !command for bash (e.g., !pip install pandas)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python/bash code to execute"}
                    },
                    "required": ["code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "scroll_page",
                "description": "Scroll page",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "x": {"type": "integer", "default": 0},
                        "y": {"type": "integer", "default": 500}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "wait_for_element",
                "description": "Wait for element to appear",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"},
                        "timeout": {"type": "integer", "default": 10000}
                    },
                    "required": ["selector"]
                }
            }
        }
    ]

def execute_tool(instavm_client, tool_call, browser_session=None):
    """Execute an OpenAI tool call using InstaVM client"""
    function_name = tool_call.function.name
    
    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        arguments = {}
    
    try:
        if function_name == "create_browser_session":
            width = arguments.get("width", 1920)
            height = arguments.get("height", 1080)
            session = instavm_client.browser.create_session(width, height)
            return {
                "success": True,
                "session_id": session.session_id,
                "session": session,
                "message": f"Created browser session {session.session_id}"
            }
            
        elif function_name == "navigate_to_url":
            if not browser_session:
                return {"success": False, "error": "No browser session. Create one first."}
            url = arguments["url"]
            result = browser_session.navigate(url)
            return {"success": True, "message": f"Navigated to {url}", "result": result}
            
        elif function_name == "extract_page_content":
            if not browser_session:
                return {"success": False, "error": "No browser session active"}
            selector = arguments.get("selector", "body")
            max_length = arguments.get("max_length", 10000)
            elements = browser_session.extract_elements(selector, ["text"])
            if elements:
                content = elements[0].get("text", "")[:max_length]
                return {"success": True, "content": content, "length": len(content)}
            return {"success": False, "error": "No content found"}
            
        elif function_name == "extract_elements":
            if not browser_session:
                return {"success": False, "error": "No browser session active"}
            selector = arguments["selector"]
            attributes = arguments.get("attributes", ["text"])
            max_results = arguments.get("max_results", 10)
            elements = browser_session.extract_elements(selector, attributes)
            return {
                "success": True,
                "elements": elements[:max_results],
                "count": len(elements)
            }
            
        elif function_name == "click_element":
            if not browser_session:
                return {"success": False, "error": "No browser session active"}
            selector = arguments["selector"]
            timeout = arguments.get("timeout", 10000)
            result = browser_session.click(selector, timeout=timeout)
            return {"success": True, "message": f"Clicked {selector}", "result": result}
            
        elif function_name == "take_screenshot":
            if not browser_session:
                return {"success": False, "error": "No browser session active"}
            full_page = arguments.get("full_page", True)
            screenshot = browser_session.screenshot(full_page=full_page)
            return {"success": True, "screenshot_length": len(screenshot), "screenshot": screenshot}
            
        elif function_name == "execute_python_code":
            code = arguments["code"]
            result = instavm_client.execute(code, language="python")
            return {"success": True, "output": result}
            
        elif function_name == "scroll_page":
            if not browser_session:
                return {"success": False, "error": "No browser session active"}
            x = arguments.get("x", 0)
            y = arguments.get("y", 500)
            result = browser_session.scroll(x=x, y=y)
            return {"success": True, "message": f"Scrolled to ({x}, {y})", "result": result}
            
        elif function_name == "wait_for_element":
            if not browser_session:
                return {"success": False, "error": "No browser session active"}
            selector = arguments["selector"]
            timeout = arguments.get("timeout", 10000)
            result = browser_session.wait_for("visible", selector, timeout)
            return {"success": True, "message": f"Element {selector} visible", "result": result}
            
        else:
            return {"success": False, "error": f"Unknown function: {function_name}"}
            
    except Exception as e:
        return {"success": False, "error": f"Function {function_name} failed: {str(e)}"}

# Simple usage example for developers:
"""
from instavm import InstaVM
from instavm.integrations.openai import get_tools, execute_tool
from openai import OpenAI

# Setup
instavm_client = InstaVM(api_key="your_key")
openai_client = OpenAI(api_key="your_key")

# Get tools
tools = get_tools()

# Use in OpenAI chat
response = openai_client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Navigate to google.com and take a screenshot"}],
    tools=tools,
    tool_choice="auto"
)

# Execute tool calls
browser_session = None
for tool_call in response.choices[0].message.tool_calls:
    result = execute_tool(instavm_client, tool_call, browser_session)
    if result.get("session"):
        browser_session = result["session"]
    print(result)
"""