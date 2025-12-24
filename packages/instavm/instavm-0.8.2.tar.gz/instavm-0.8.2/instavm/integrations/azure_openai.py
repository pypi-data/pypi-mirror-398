"""
Azure OpenAI integration utilities for InstaVM

Simple utilities for Azure OpenAI with InstaVM - just import and use.
"""

import json
from typing import Dict, List, Any, Optional
from .openai import get_tools, execute_tool  # Reuse OpenAI tools

# Azure OpenAI uses same tool format as OpenAI
get_azure_tools = get_tools
execute_azure_tool = execute_tool

def get_system_prompt() -> str:
    """Get optimized system prompt for Azure OpenAI + InstaVM"""
    return """
You are a web automation assistant with access to browser and code execution tools.

Available capabilities:
- create_browser_session: Start browser automation
- navigate_to_url: Go to any website  
- extract_page_content: Get page text content
- extract_elements: Get specific elements by CSS selector
- click_element: Click page elements
- take_screenshot: Capture page images
- execute_python_code: Run Python/bash code (use !pip install for packages)
- scroll_page: Scroll to coordinates
- wait_for_element: Wait for elements to load

Tips:
- Always create browser session before navigation
- Install packages with !pip install before importing  
- Use screenshots when text extraction isn't enough
- Be systematic and handle errors gracefully
"""

# Simple usage example for Azure OpenAI:
"""
from instavm import InstaVM
from instavm.integrations.azure_openai import get_azure_tools, execute_azure_tool, get_system_prompt
from openai import AzureOpenAI

# Setup
instavm_client = InstaVM(api_key="instavm_key")
azure_client = AzureOpenAI(
    api_key="azure_key",
    api_version="2024-02-01", 
    azure_endpoint="https://your-resource.openai.azure.com"
)

# Simple automation
tools = get_azure_tools()
messages = [
    {"role": "system", "content": get_system_prompt()},
    {"role": "user", "content": "Go to example.com and extract the main headline"}
]

response = azure_client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

# Execute tools
browser_session = None
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        result = execute_azure_tool(instavm_client, tool_call, browser_session)
        if result.get("session"):
            browser_session = result["session"]
        print(result)
"""