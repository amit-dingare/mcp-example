#!/usr/bin/env python3
"""
FastMCP Server

This server loads tools, resources, and prompts from folders and serves them via MCP.

Folder structure:
- tools/ - Python files with tool implementations
- resources/ - Text files, JSON files, documents  
- prompts/ - JSON files with prompt templates
- .env - Environment variables (API keys, etc.)

Usage:
    python mcp_server.py

Requirements:
    pip install mcp fastmcp aiohttp python-dotenv
"""

import json
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util
from dataclasses import dataclass

# MCP imports
from mcp.server.fastmcp import FastMCP

@dataclass
class MCPConfig:
    """Configuration for MCP setup"""
    tools_dir: str = "tools"
    resources_dir: str = "resources" 
    prompts_dir: str = "prompts"
    server_name: str = "fastmcp-example"
    server_version: str = "0.1.0"

class FastMCPServer:
    """FastMCP server that loads capabilities from folders"""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.mcp = FastMCP(config.server_name)
        self._setup_server()
    
    def _setup_server(self):
        """Setup the FastMCP server with capabilities from folders"""
        self._load_tools()
        self._load_resources()
        self._load_prompts()
    
    def _load_tools(self):
        """Load tools from the tools directory"""
        tools_path = Path(self.config.tools_dir)
        
        if not tools_path.exists():
            print(f"⚠️  Tools directory '{self.config.tools_dir}' not found, creating sample tools...")
            self._create_sample_tools()
            self._create_env_file()
            tools_path = Path(self.config.tools_dir)  # Refresh path after creation
        
        print(f"📁 Loading tools from {tools_path}")
        
        # Keep track of loaded tools to avoid duplicates
        loaded_tools = set()
        
        for tool_file in tools_path.glob("*.py"):
            if tool_file.name.startswith("__") or tool_file.stem in loaded_tools:
                continue
                
            try:
                # Load tool module
                spec = importlib.util.spec_from_file_location(tool_file.stem, tool_file)
                if spec is None or spec.loader is None:
                    print(f"  ⚠️  Could not load spec for {tool_file}")
                    continue
                    
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Register tool if it has the required attributes
                if hasattr(module, 'TOOL_NAME') and hasattr(module, 'tool_function'):
                    tool_name = module.TOOL_NAME
                    tool_desc = getattr(module, 'TOOL_DESCRIPTION', f"Tool: {tool_name}")
                    
                    # Create a simple wrapper that handles kwargs
                    def create_tool_function(mod):
                        async def tool_wrapper(kwargs: dict) -> str:
                            """Wrapper that accepts kwargs dict and unpacks it"""
                            try:
                                print(f"Calling {mod.TOOL_NAME} with kwargs: {kwargs}")
                                
                                # Call the tool function with unpacked kwargs
                                if asyncio.iscoroutinefunction(mod.tool_function):
                                    return await mod.tool_function(**kwargs)
                                else:
                                    return mod.tool_function(**kwargs)
                                    
                            except Exception as e:
                                return f"Tool error: {str(e)}"
                        
                        return tool_wrapper
                    
                    # Register the tool with FastMCP
                    tool_function = create_tool_function(module)
                    self.mcp.tool(name=tool_name, description=tool_desc)(tool_function)
                    
                    loaded_tools.add(tool_file.stem)
                    print(f"  ✅ Loaded tool: {tool_name}")
                else:
                    print(f"  ⚠️  Tool {tool_file} missing required attributes (TOOL_NAME, tool_function)")
                    
            except Exception as e:
                print(f"  ❌ Failed to load tool {tool_file}: {e}")
                import traceback
                traceback.print_exc()
        
        if not loaded_tools:
            print("  ⚠️  No tools loaded, creating sample tools...")
            self._create_sample_tools()
            self._create_env_file()
            # Try loading again after creating samples
            self._load_tools_retry()

    def _load_tools_retry(self):
        """Retry loading tools after creating samples"""
        tools_path = Path(self.config.tools_dir)
        loaded_tools = set()
        
        for tool_file in tools_path.glob("*.py"):
            if tool_file.name.startswith("__") or tool_file.stem in loaded_tools:
                continue
                
            try:
                spec = importlib.util.spec_from_file_location(tool_file.stem, tool_file)
                if spec is None or spec.loader is None:
                    continue
                    
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'TOOL_NAME') and hasattr(module, 'tool_function'):
                    tool_name = module.TOOL_NAME
                    tool_desc = getattr(module, 'TOOL_DESCRIPTION', f"Tool: {tool_name}")
                    
                    def create_tool_function(mod):
                        """Create a tool function wrapper for FastMCP"""
                        async def tool_wrapper(**kwargs):
                            try:
                                if asyncio.iscoroutinefunction(mod.tool_function):
                                    return await mod.tool_function(**kwargs)
                                else:
                                    return mod.tool_function(**kwargs)
                            except Exception as e:
                                return f"Tool error: {str(e)}"
                        return tool_wrapper
                    
                    tool_function = create_tool_function(module)
                    self.mcp.tool(name=tool_name, description=tool_desc)(tool_function)
                    loaded_tools.add(tool_file.stem)
                    print(f"  ✅ Loaded tool: {tool_name}")
                    
            except Exception as e:
                print(f"  ❌ Failed to load tool {tool_file}: {e}")
    
    def _load_resources(self):
        """Load resources from the resources directory"""
        resources_path = Path(self.config.resources_dir)
        
        if not resources_path.exists():
            print(f"⚠️  Resources directory '{self.config.resources_dir}' not found, creating sample resources...")
            self._create_sample_resources()
            resources_path = Path(self.config.resources_dir)  # Refresh path
        
        print(f"📁 Loading resources from {resources_path}")
        
        loaded_resources = set()
        
        for resource_file in resources_path.iterdir():
            if (resource_file.is_file() and 
                not resource_file.name.startswith(".") and 
                resource_file.name not in loaded_resources):
                try:
                    resource_uri = f"file://{resource_file.absolute()}"
                    resource_name = resource_file.stem.replace('_', ' ').title()
                    
                    # Create a closure to capture the file path
                    def make_resource_reader(file_path):
                        async def read_resource() -> str:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    return f.read()
                            except Exception as e:
                                return f"Error reading resource: {str(e)}"
                        return read_resource
                    
                    # Register the resource
                    self.mcp.resource(
                        uri=resource_uri,
                        name=resource_name,
                        description=f"Resource: {resource_name}"
                    )(make_resource_reader(resource_file))
                    
                    loaded_resources.add(resource_file.name)
                    print(f"  ✅ Loaded resource: {resource_file.name}")
                    
                except Exception as e:
                    print(f"  ❌ Failed to load resource {resource_file}: {e}")
        
        if not loaded_resources:
            print("  ⚠️  No resources loaded")

    def _load_prompts(self):
        """Load prompts from the prompts directory"""
        prompts_path = Path(self.config.prompts_dir)
        
        if not prompts_path.exists():
            print(f"⚠️  Prompts directory '{self.config.prompts_dir}' not found, creating sample prompts...")
            self._create_sample_prompts()
            prompts_path = Path(self.config.prompts_dir)  # Refresh path
        
        print(f"📁 Loading prompts from {prompts_path}")
        
        loaded_prompts = set()
        
        for prompt_file in prompts_path.glob("*.json"):
            if prompt_file.stem in loaded_prompts:
                continue
                
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_data = json.load(f)
                
                prompt_name = prompt_data.get('name', prompt_file.stem)
                prompt_desc = prompt_data.get('description', f"Prompt: {prompt_name}")
                prompt_template = prompt_data.get('template', '')
                prompt_args = prompt_data.get('arguments', [])
                
                # FastMCP uses a simpler prompt registration
                def make_prompt_handler(template):
                    async def prompt_handler(**kwargs) -> str:
                        try:
                            # Simple template substitution
                            result = template
                            for key, value in kwargs.items():
                                result = result.replace(f"{{{key}}}", str(value))
                            return result
                        except Exception as e:
                            return f"Prompt error: {str(e)}"
                    return prompt_handler
                
                # Register the prompt with FastMCP
                self.mcp.prompt(
                    name=prompt_name, 
                    description=prompt_desc
                )(make_prompt_handler(prompt_template))
                
                loaded_prompts.add(prompt_file.stem)
                print(f"  ✅ Loaded prompt: {prompt_name}")
                
            except Exception as e:
                print(f"  ❌ Failed to load prompt {prompt_file}: {e}")
        
        if not loaded_prompts:
            print("  ⚠️  No prompts loaded")
    
    def _create_env_file(self):
        """Create sample .env file"""
        env_path = Path(".env")
        if not env_path.exists():
            env_content = """# Environment Variables for MCP Server
# OpenWeatherMap API Key - Get free key from https://openweathermap.org/api
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Add other API keys or configuration here
# ANOTHER_API_KEY=your_key_here
"""
            env_path.write_text(env_content)
            print(f"  ✅ Created sample .env file - please add your API keys")
    
    def _create_sample_tools(self):
        """Create sample tools directory and files"""
        tools_path = Path(self.config.tools_dir)
        tools_path.mkdir(exist_ok=True)
        print(f"  ✅ Created sample tools in {tools_path}")
    
    def _create_sample_resources(self):
        """Create sample resources directory and files"""
        resources_path = Path(self.config.resources_dir)
        resources_path.mkdir(exist_ok=True)
        
        # Sample document
        sample_doc = """Monthly Performance Report
==========================

Key Metrics:
- Revenue: $125,000 (+12% from last month)
- New Customers: 45
- Customer Satisfaction: 4.2/5.0
- Support Tickets: 23 (-8% from last month)

Summary:
Strong performance across all metrics this month.
Revenue growth continues to exceed expectations.
Customer acquisition is on track with quarterly goals.

Action Items:
1. Continue current marketing strategy
2. Focus on customer retention programs
3. Optimize support response times
"""
        
        # Sample data file
        sample_data = {
            "customers": [
                {"id": 1, "name": "Acme Corp", "revenue": 25000, "status": "active"},
                {"id": 2, "name": "Tech Solutions", "revenue": 18000, "status": "active"},
                {"id": 3, "name": "Global Industries", "revenue": 32000, "status": "pending"},
                {"id": 4, "name": "Innovation Labs", "revenue": 15000, "status": "active"}
            ],
            "summary": {
                "total_customers": 4,
                "total_revenue": 90000,
                "active_customers": 3,
                "pending_customers": 1
            }
        }
        
        # Company information
        company_info = """Company Information
==================

Name: Example Corp
Founded: 2020
Employees: 150
Headquarters: San Francisco, CA

Mission: To provide innovative solutions that help businesses grow.

Core Values:
- Innovation
- Customer Focus
- Transparency
- Quality

Products:
- Enterprise Software Platform
- Data Analytics Tools
- Customer Support Solutions
"""
        
        (resources_path / "monthly_report.txt").write_text(sample_doc)
        (resources_path / "customer_data.json").write_text(json.dumps(sample_data, indent=2))
        (resources_path / "company_info.txt").write_text(company_info)
        print(f"  ✅ Created sample resources in {resources_path}")
    
    def _create_sample_prompts(self):
        """Create sample prompts directory and files"""
        prompts_path = Path(self.config.prompts_dir)
        prompts_path.mkdir(exist_ok=True)
        
        # Code review prompt
        code_review_prompt = {
            "name": "code_review",
            "description": "Template for conducting code reviews",
            "template": """Code Review Checklist for {language}

Reviewing: {code_description}
Complexity Level: {complexity}

Please review the following aspects:
1. Code correctness and logic
2. Performance considerations
3. Security implications
4. Code style and conventions
5. Documentation and comments
6. Test coverage

Focus areas for {language}:
- Language-specific best practices
- Framework conventions
- Error handling patterns

Additional Notes:
{additional_notes}
""",
            "arguments": [
                {"name": "language", "description": "Programming language", "required": True},
                {"name": "code_description", "description": "Brief description of the code", "required": True},
                {"name": "complexity", "description": "Code complexity level (low/medium/high)", "required": False},
                {"name": "additional_notes", "description": "Additional review notes", "required": False}
            ]
        }
        
        # Email draft prompt
        email_prompt = {
            "name": "email_draft",
            "description": "Template for drafting professional emails",
            "template": """Subject: {subject}

Dear {recipient},

{opening}

{main_content}

{closing}

Best regards,
{sender_name}
{sender_title}
""",
            "arguments": [
                {"name": "recipient", "description": "Email recipient name", "required": True},
                {"name": "subject", "description": "Email subject line", "required": True},
                {"name": "opening", "description": "Email opening", "required": False},
                {"name": "main_content", "description": "Main email content", "required": True},
                {"name": "closing", "description": "Email closing", "required": False},
                {"name": "sender_name", "description": "Sender name", "required": False},
                {"name": "sender_title", "description": "Sender title", "required": False}
            ]
        }
        
        # Meeting notes prompt
        meeting_prompt = {
            "name": "meeting_notes",
            "description": "Template for meeting notes and action items",
            "template": """Meeting Notes: {meeting_title}
Date: {date}
Attendees: {attendees}

Agenda:
{agenda}

Discussion Summary:
{discussion}

Decisions Made:
{decisions}

Action Items:
{action_items}

Next Meeting: {next_meeting}
""",
            "arguments": [
                {"name": "meeting_title", "description": "Title of the meeting", "required": True},
                {"name": "date", "description": "Meeting date", "required": True},
                {"name": "attendees", "description": "List of attendees", "required": True},
                {"name": "agenda", "description": "Meeting agenda", "required": False},
                {"name": "discussion", "description": "Summary of discussion", "required": False},
                {"name": "decisions", "description": "Decisions made", "required": False},
                {"name": "action_items", "description": "Action items and assignments", "required": False},
                {"name": "next_meeting", "description": "Next meeting date/time", "required": False}
            ]
        }
        
        (prompts_path / "code_review.json").write_text(json.dumps(code_review_prompt, indent=2))
        (prompts_path / "email_draft.json").write_text(json.dumps(email_prompt, indent=2))
        (prompts_path / "meeting_notes.json").write_text(json.dumps(meeting_prompt, indent=2))
        print(f"  ✅ Created sample prompts in {prompts_path}")
    
    def run_server_sync(self):
        """Run the FastMCP server synchronously"""
        print(f"🚀 Starting FastMCP server: {self.config.server_name}")
        print(f"📁 Tools directory: {self.config.tools_dir}")
        print(f"📁 Resources directory: {self.config.resources_dir}")
        print(f"📁 Prompts directory: {self.config.prompts_dir}")
        print()
        
        try:
            # FastMCP.run() should be called synchronously, not from within async context
            self.mcp.run()
                
        except Exception as e:
            print(f"❌ Server runtime error: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise

def main():
    """Main entry point for the server"""
    print("🖥️  FastMCP Server")
    print("=" * 40)
    
    try:
        config = MCPConfig()
        server = FastMCPServer(config)
        
        print("🎯 Server initialized successfully")
        # Run synchronously since FastMCP handles its own event loop
        server.run_server_sync()
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("💡 Make sure you have installed: pip install mcp fastmcp aiohttp python-dotenv")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        # Provide helpful debugging info
        print("\n🔍 Debugging Information:")
        print(f"  Python version: {sys.version}")
        print(f"  Current directory: {os.getcwd()}")
        
        # Check if directories exist
        for dir_name in ["tools", "resources", "prompts"]:
            dir_path = Path(dir_name)
            if dir_path.exists():
                files = list(dir_path.glob("*"))
                print(f"  {dir_name}/ directory: ✅ ({len(files)} files)")
            else:
                print(f"  {dir_name}/ directory: ❌ (not found)")
        
        # Check if .env file exists
        env_path = Path(".env")
        if env_path.exists():
            print(f"  .env file: ✅")
        else:
            print(f"  .env file: ❌ (not found)")
        
        print("\n💡 Try running the client in simulated mode: python mcp_client.py")

if __name__ == "__main__":
    main()  # Call synchronously, not with asyncio.run()