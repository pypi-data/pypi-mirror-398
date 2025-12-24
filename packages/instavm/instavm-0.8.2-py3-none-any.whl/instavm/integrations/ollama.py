"""
Ollama integration utilities for InstaVM

Simple utilities to use InstaVM with Ollama local LLMs.
Perfect for privacy-focused, cost-effective, or offline development.
"""

import json
import requests
from typing import Dict, List, Any, Optional

def get_ollama_tools() -> List[Dict[str, Any]]:
    """Get function definitions for Ollama (OpenAI-compatible format)"""
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
                "name": "take_screenshot", 
                "description": "Take page screenshot",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "full_page": {"type": "boolean", "description": "Full page capture", "default": True}
                    }
                }
            }
        }
    ]

def execute_ollama_tool(instavm_client, function_name: str, arguments: Dict[str, Any], browser_session=None):
    """Execute tool for Ollama integration"""
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
            
        elif function_name == "execute_python_code":
            code = arguments["code"]
            result = instavm_client.execute(code, language="python")
            return {"success": True, "output": result}
            
        elif function_name == "take_screenshot":
            if not browser_session:
                return {"success": False, "error": "No browser session active"}
            full_page = arguments.get("full_page", True)
            screenshot = browser_session.screenshot(full_page=full_page)
            return {"success": True, "screenshot_length": len(screenshot), "screenshot": screenshot}
            
        else:
            return {"success": False, "error": f"Unknown function: {function_name}"}
            
    except Exception as e:
        return {"success": False, "error": f"Function {function_name} failed: {str(e)}"}

class OllamaAgent:
    """Simple agent for Ollama + InstaVM integration
    
    Supports both OpenAI-compatible function calling (recommended) and fallback text parsing.
    Function calling is more robust and works with newer Ollama models.
    """
    
    def __init__(self, instavm_client, ollama_base_url: str = "http://localhost:11434", model: str = "llama2", prefer_function_calling: bool = True):
        self.instavm_client = instavm_client
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.model = model
        self.browser_session = None
        self.prefer_function_calling = prefer_function_calling
        
    def chat(self, message: str, system_prompt: Optional[str] = None, use_function_calling: bool = True) -> Dict[str, Any]:
        """Chat with Ollama model and execute tools as needed
        
        Args:
            message: User message
            system_prompt: Optional custom system prompt
            use_function_calling: Use OpenAI-compatible function calling if supported (default: True)
        """
        
        default_system = """You are a web automation assistant with access to browser and code execution tools.
Be systematic and help the user accomplish their web automation tasks."""

        system = system_prompt or default_system
        
        try:
            # Try OpenAI-compatible function calling first (more robust)
            if use_function_calling and self.prefer_function_calling:
                return self._chat_with_function_calling(message, system)
            else:
                return self._chat_with_text_parsing(message, system)
            
        except Exception as e:
            # Fallback to text parsing if function calling fails
            if use_function_calling:
                print(f"Function calling failed, falling back to text parsing: {e}")
                return self._chat_with_text_parsing(message, system)
            return {"error": f"Ollama chat failed: {str(e)}"}
    
    def _chat_with_function_calling(self, message: str, system: str) -> Dict[str, Any]:
        """Use OpenAI-compatible function calling (recommended for newer models)"""
        tools = get_ollama_tools()
        
        response = requests.post(f"{self.ollama_base_url}/api/chat", json={
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": message}
            ],
            "tools": tools,
            "stream": False
        })
        response.raise_for_status()
        
        result = response.json()
        ollama_response = result["message"]
        
        # Check for tool calls in OpenAI-compatible format
        if ollama_response.get("tool_calls"):
            tool_call = ollama_response["tool_calls"][0]  # Take first tool call
            function_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            
            # Execute tool
            tool_result = execute_ollama_tool(self.instavm_client, function_name, arguments, self.browser_session)
            
            # Update browser session reference if created
            if tool_result.get("session"):
                self.browser_session = tool_result["session"]
            
            # Get follow-up response with tool result
            followup_response = requests.post(f"{self.ollama_base_url}/api/chat", json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": ollama_response.get("content", ""), "tool_calls": ollama_response["tool_calls"]},
                    {"role": "tool", "content": json.dumps(tool_result), "name": function_name}
                ],
                "tools": tools,
                "stream": False
            })
            
            if followup_response.status_code == 200:
                final_response = followup_response.json()["message"]["content"]
                return {
                    "response": final_response,
                    "tool_used": function_name,
                    "tool_result": tool_result
                }
        
        return {"response": ollama_response.get("content", str(ollama_response))}
    
    def _chat_with_text_parsing(self, message: str, system: str) -> Dict[str, Any]:
        """Fallback text parsing method (for older models or when function calling fails)"""
        
        text_system = system + """\n\nAvailable tools:
- create_browser_session: Start browser automation
- navigate_to_url: Go to websites  
- extract_page_content: Get page text content
- extract_elements: Get specific elements by selector
- execute_python_code: Run Python/bash code (use !pip install for packages)  
- take_screenshot: Capture page images

When you want to use a tool, respond with:
TOOL_CALL: function_name
ARGUMENTS: {"arg1": "value1", "arg2": "value2"}"""
        
        response = requests.post(f"{self.ollama_base_url}/api/chat", json={
            "model": self.model,
            "messages": [
                {"role": "system", "content": text_system},
                {"role": "user", "content": message}
            ],
            "stream": False
        })
        response.raise_for_status()
        
        ollama_response = response.json()["message"]["content"]
        
        # Check if model wants to use a tool (brittle text parsing)
        if "TOOL_CALL:" in ollama_response and "ARGUMENTS:" in ollama_response:
            lines = ollama_response.strip().split("\n")
            function_name = None
            arguments = {}
            
            for line in lines:
                if line.startswith("TOOL_CALL:"):
                    function_name = line.replace("TOOL_CALL:", "").strip()
                elif line.startswith("ARGUMENTS:"):
                    try:
                        args_str = line.replace("ARGUMENTS:", "").strip()
                        arguments = json.loads(args_str)
                    except json.JSONDecodeError:
                        pass
            
            if function_name:
                # Execute tool
                result = execute_ollama_tool(self.instavm_client, function_name, arguments, self.browser_session)
                
                # Update browser session reference if created
                if result.get("session"):
                    self.browser_session = result["session"]
                
                # Get follow-up response from Ollama with tool result
                followup_response = requests.post(f"{self.ollama_base_url}/api/chat", json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": text_system},
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": ollama_response},
                        {"role": "user", "content": f"Tool result: {json.dumps(result)}"}
                    ],
                    "stream": False
                })
                
                if followup_response.status_code == 200:
                    final_response = followup_response.json()["message"]["content"]
                    return {
                        "response": final_response,
                        "tool_used": function_name,
                        "tool_result": result
                    }
        
        return {"response": ollama_response}
    
    def cleanup(self):
        """Clean up browser session"""
        if self.browser_session:
            try:
                self.browser_session.close()
            except:
                pass

# Simple usage examples:
"""
# Basic usage with requests
from instavm import InstaVM
from instavm.integrations.ollama import get_ollama_tools, execute_ollama_tool
import requests

instavm_client = InstaVM(api_key="your_key")
tools = get_ollama_tools()

# Manual tool execution
result = execute_ollama_tool(instavm_client, "create_browser_session", {"width": 1920, "height": 1080})
print(result)

# Agent usage (easier)
from instavm.integrations.ollama import OllamaAgent

agent = OllamaAgent(
    instavm_client=InstaVM(api_key="your_key"),
    ollama_base_url="http://localhost:11434",
    model="llama2:13b"  # or codellama, mistral, etc.
)

response = agent.chat("Go to example.com and tell me what the main headline is")
print(response)

# Cleanup
agent.cleanup()
"""