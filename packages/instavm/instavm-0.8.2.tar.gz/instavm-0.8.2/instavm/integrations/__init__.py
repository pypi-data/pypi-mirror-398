"""
InstaVM LLM Integrations

Pre-built integrations with popular LLM frameworks to eliminate boilerplate code.

Available integrations:
- OpenAI (including Azure OpenAI)  
- LangChain
- LlamaIndex
- Ollama

Usage:
    from instavm.integrations.openai import get_tools, execute_tool
    from instavm.integrations.langchain import get_langchain_tools  
    from instavm.integrations.llamaindex import get_llamaindex_tools
    from instavm.integrations.ollama import OllamaAgent

Each integration provides simple utility functions - no complex classes needed!
"""