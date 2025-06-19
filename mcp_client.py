#!/usr/bin/env python3
"""
OpenAI-Orchestrated MCP Client

This client uses OpenAI as the orchestrator to intelligently decide which MCP tools,
resources, and prompts to use based on user requests. The OpenAI model analyzes
the user's intent and makes function calls to MCP capabilities.

Setup:
1. Create .env file with: OPENAI_API_KEY=your_openai_api_key_here
2. Start MCP server: python mcp_server.py
3. Run client: python orchestrated_mcp_client.py

Requirements:
    pip install mcp openai python-dotenv
"""

import json
import asyncio
import os
import sys
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MCP Client imports
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# OpenAI imports
from openai import AsyncOpenAI

class MCPClient:
    """MCP Client for communicating with FastMCP server"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.available_tools = []
        self.available_resources = []
        self.available_prompts = []
    
    async def connect_and_discover(self, server_params: StdioServerParameters):
        """Connect to MCP server and discover capabilities"""
        print("🔌 Connecting to MCP server...")
        
        try:
            async def _connect():
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        self.session = session
                        await session.initialize()
                        print("✅ Connected to MCP server")
                        
                        await self._discover_capabilities()
                        self.session = None
                        
                        print(f"\n📊 Discovery Summary:")
                        print(f"  Tools: {len(self.available_tools)}")
                        print(f"  Resources: {len(self.available_resources)}")
                        print(f"  Prompts: {len(self.available_prompts)}")
                        
                        return True
            
            return await asyncio.wait_for(_connect(), timeout=10.0)
                    
        except asyncio.TimeoutError:
            print(f"❌ Connection timeout - MCP server may not be responding")
            raise
        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            raise

    async def _discover_capabilities(self):
        """Discover available tools, resources, and prompts"""
        # List tools
        print("\n📋 Discovering available tools...")
        try:
            result = await self.session.list_tools()
            self.available_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in result.tools
            ]
            print(f"✅ Found {len(self.available_tools)} tools:")
            for tool in self.available_tools:
                print(f"  • {tool['name']}: {tool['description']}")
        except Exception as e:
            print(f"❌ Error listing tools: {e}")
            self.available_tools = []
        
        # List resources
        print("\n📚 Discovering available resources...")
        try:
            result = await self.session.list_resources()
            self.available_resources = [
                {
                    "uri": resource.uri,
                    "name": resource.name or "Unnamed Resource",
                    "description": resource.description or "No description",
                    "mimeType": resource.mimeType
                }
                for resource in result.resources
            ]
            print(f"✅ Found {len(self.available_resources)} resources:")
            for resource in self.available_resources:
                print(f"  • {resource['name']}: {resource['description']}")
        except Exception as e:
            print(f"❌ Error listing resources: {e}")
            self.available_resources = []
        
        # List prompts
        print("\n📝 Discovering available prompts...")
        try:
            result = await self.session.list_prompts()
            self.available_prompts = [
                {
                    "name": prompt.name,
                    "description": prompt.description,
                    "arguments": [
                        {
                            "name": arg.name,
                            "description": arg.description,
                            "required": arg.required
                        }
                        for arg in (prompt.arguments or [])
                    ]
                }
                for prompt in result.prompts
            ]
            print(f"✅ Found {len(self.available_prompts)} prompts:")
            for prompt in self.available_prompts:
                args_info = ", ".join([f"{arg['name']}{'*' if arg['required'] else ''}" 
                                     for arg in prompt['arguments']])
                print(f"  • {prompt['name']}: {prompt['description']} (args: {args_info})")
        except Exception as e:
            print(f"❌ Error listing prompts: {e}")
            self.available_prompts = []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a specific tool with arguments"""
        print(f"\n🔧 Calling tool '{tool_name}' with arguments: {arguments}")
        
        try:
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["mcp_server.py"]
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Wrap arguments in kwargs as expected by FastMCP server
                    tool_arguments = {"kwargs": arguments}
                    
                    result = await session.call_tool(tool_name, tool_arguments)
                    
                    # Extract response
                    response = ""
                    if hasattr(result, 'content') and result.content:
                        for content in result.content:
                            if hasattr(content, 'text'):
                                response += content.text
                            else:
                                response += str(content)
                    else:
                        response = str(result)
                    
                    print(f"✅ Tool result: {response}")
                    return response
                
        except Exception as e:
            error_msg = f"Tool error: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def get_resource(self, resource_uri: str) -> str:
        """Get content from a resource"""
        print(f"\n📖 Reading resource: {resource_uri}")
        
        try:
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["mcp_server.py"]
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    result = await session.read_resource(resource_uri)
                    
                    content = ""
                    if hasattr(result, 'contents') and result.contents:
                        for item in result.contents:
                            if hasattr(item, 'text'):
                                content += item.text
                            else:
                                content += str(item)
                    else:
                        content = str(result)
                    
                    print(f"✅ Resource content loaded ({len(content)} characters)")
                    return content
                
        except Exception as e:
            error_msg = f"Resource error: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def get_prompt(self, prompt_name: str, arguments: Dict[str, Any]) -> str:
        """Get a prompt with filled arguments"""
        print(f"\n📝 Getting prompt '{prompt_name}' with arguments: {arguments}")
        
        try:
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["mcp_server.py"]
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    result = await session.get_prompt(prompt_name, arguments)
                    
                    content = ""
                    if hasattr(result, 'messages') and result.messages:
                        for message in result.messages:
                            if hasattr(message, 'content'):
                                if hasattr(message.content, 'text'):
                                    content += message.content.text
                                elif isinstance(message.content, list):
                                    for item in message.content:
                                        if hasattr(item, 'text'):
                                            content += item.text
                                else:
                                    content += str(message.content)
                    else:
                        content = str(result)
                    
                    print(f"✅ Prompt generated ({len(content)} characters)")
                    return content
                    
        except Exception as e:
            error_msg = f"Prompt error: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg

class OrchestrationAgent:
    """Generic OpenAI-powered orchestration agent"""
    
    def __init__(self):
        self.mcp_client = None
        self.openai_client = None
        self.model = "gpt-4o-mini"
        self._initialize_openai()
    
    def _initialize_openai(self):
        """Initialize OpenAI client with API key from environment"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables. "
                "Please create a .env file with your OpenAI API key."
            )
        
        self.openai_client = AsyncOpenAI(api_key=api_key)
        print("✅ OpenAI client initialized")
    
    async def initialize(self):
        """Initialize the agent with MCP capabilities"""
        print("🤖 Initializing OpenAI Orchestration Agent...")
        
        self.mcp_client = MCPClient()
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["mcp_server.py"]
        )
        
        await self.mcp_client.connect_and_discover(server_params)
        print("✅ Successfully connected to MCP server")
    
    def _create_function_definitions(self) -> List[Dict]:
        """Create OpenAI function definitions from MCP capabilities"""
        functions = []
        
        # Add MCP tools as OpenAI functions
        for tool in self.mcp_client.available_tools:
            parameters = self._get_tool_parameters(tool['name'], tool.get('inputSchema', {}))
            
            function_def = {
                "type": "function",
                "function": {
                    "name": f"mcp_tool_{tool['name']}",
                    "description": f"Tool: {tool['description']}",
                    "parameters": parameters
                }
            }
            functions.append(function_def)
        
        # Add MCP resources as OpenAI functions
        for resource in self.mcp_client.available_resources:
            function_def = {
                "type": "function",
                "function": {
                    "name": f"mcp_resource_{resource['name'].lower().replace(' ', '_')}",
                    "description": f"Resource: {resource['description']}",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            functions.append(function_def)
        
        # Add MCP prompts as OpenAI functions
        for prompt in self.mcp_client.available_prompts:
            properties = {}
            required = []
            
            for arg in prompt['arguments']:
                properties[arg['name']] = {
                    "type": "string",
                    "description": arg['description']
                }
                if arg['required']:
                    required.append(arg['name'])
            
            function_def = {
                "type": "function",
                "function": {
                    "name": f"mcp_prompt_{prompt['name']}",
                    "description": f"Prompt: {prompt['description']}",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }
            functions.append(function_def)
        
        return functions
    
    def _get_tool_parameters(self, tool_name: str, input_schema: Dict) -> Dict:
        """Get parameter schema for a tool"""
        # If the tool has a proper input schema, use it
        if input_schema and input_schema.get('properties'):
            return input_schema
        
        # Generic fallback for any tool
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Primary input/query parameter"
                },
                "search_type": {
                    "type": "string", 
                    "description": "Type or category for the operation"
                },
                "location": {
                    "type": "string",
                    "description": "Location parameter (if applicable)"
                },
                "expression": {
                    "type": "string",
                    "description": "Expression or calculation (if applicable)"
                },
                "company_name": {
                    "type": "string",
                    "description": "Company name (if applicable)"
                },
                "industry": {
                    "type": "string",
                    "description": "Industry sector (if applicable)"
                }
            },
            "required": []
        }
    
    def _build_system_prompt(self) -> str:
        """Build generic system prompt"""
        # Analyze available capabilities to build intelligent prompt
        tool_names = [tool['name'] for tool in self.mcp_client.available_tools]
        prompt_names = [prompt['name'] for prompt in self.mcp_client.available_prompts]
        
        # Detect if we have tools that produce data and prompts that consume data
        has_search_tools = any('search' in name.lower() or 'data' in name.lower() for name in tool_names)
        has_report_prompts = any('report' in name.lower() or 'analysis' in name.lower() for name in prompt_names)
        
        workflow_guidance = ""
        if has_search_tools and has_report_prompts:
            workflow_guidance = """
🔥 IMPORTANT WORKFLOW PATTERN:
For research, analysis, or report requests, you should typically:
1. FIRST: Use a data gathering tool (like search tools) to collect information
2. SECOND: Use a report/analysis prompt to structure and present the findings

This two-step pattern ensures comprehensive and well-formatted responses.
"""
        
        # Build parameter extraction examples based on available tools
        extraction_examples = []
        
        if 'calculator' in tool_names:
            extraction_examples.append('- "calculate 11*3 + 23" → {"expression": "11*3 + 23"}')
            extraction_examples.append('- "what\'s 144 + 25" → {"expression": "144 + 25"}')
        
        if any('weather' in name for name in tool_names):
            extraction_examples.append('- "weather in Tokyo" → {"location": "Tokyo"}')
            extraction_examples.append('- "what\'s the weather in Paris" → {"location": "Paris"}')
        
        if any('search' in name for name in tool_names):
            extraction_examples.append('- "research Tesla" → {"query": "Tesla company", "search_type": "company"}')
            extraction_examples.append('- "search for Apple information" → {"query": "Apple company information"}')
        
        extraction_section = ""
        if extraction_examples:
            extraction_section = f"""
CRITICAL PARAMETER EXTRACTION EXAMPLES:
{chr(10).join(extraction_examples)}

🚨 NEVER call functions with empty parameters {{}} - always extract meaningful values from user input!
"""
        
        return f"""You are an intelligent orchestration agent that leverages MCP capabilities to help users.

CORE PRINCIPLES:
- Always use actual function calls - never just describe what you would do
- ALWAYS extract relevant parameters from user messages - NEVER use empty parameters {{}}
- Choose the most appropriate tools and prompts for each request
- For complex requests, use multiple functions in logical sequence

{workflow_guidance}

AVAILABLE CAPABILITIES:
Tools: {', '.join(tool_names)}
Prompts: {', '.join(prompt_names)}

{extraction_section}

PARAMETER EXTRACTION RULES:
- Look for mathematical expressions, company names, locations, queries in user messages
- Extract the core information the user is asking about
- Match parameters to the most relevant tool functionality
- Use context clues to determine the right parameter values
- If you can't extract specific parameters, use the main subject of the user's request

FUNCTION CALLING REQUIREMENTS:
- Always use the OpenAI function calling interface
- Make actual function calls with extracted parameters
- Use logical sequences for complex requests
- NEVER call functions with empty parameters {{}}

Remember: Extract meaningful parameters from user input and execute functions to provide real results!"""
    
    async def chat(self, user_message: str) -> str:
        """Chat with the user using OpenAI orchestration and MCP capabilities"""
        print(f"\n💬 User: {user_message}")
        
        # Create function definitions from MCP capabilities
        functions = self._create_function_definitions()
        
        # Build messages for OpenAI
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_message}
        ]
        
        try:
            # Call OpenAI with function calling enabled
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=functions,
                tool_choice="auto",
                temperature=0.1,
                max_tokens=4000
            )
            
            assistant_message = response.choices[0].message
            
            # Handle function calls iteratively
            if assistant_message.tool_calls:
                print(f"\n🧠 OpenAI decided to use {len(assistant_message.tool_calls)} MCP function(s)")
                
                # Process all function calls
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": call.type,
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments
                            }
                        }
                        for call in assistant_message.tool_calls
                    ]
                })
                
                # Execute each function call
                function_results = []
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        function_args = {}
                    
                    print(f"🔧 Executing: {function_name}({function_args})")
                    print(f"🔍 Debug - Raw arguments: {tool_call.function.arguments}")
                    
                    # Execute the MCP function
                    result = await self._execute_mcp_function(function_name, function_args, user_message)
                    function_results.append(result)
                    
                    # Add function result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
                
                # Generic workflow detection: if we have tool results but no prompts used,
                # and the user asked for analysis/reports, suggest using prompts
                tool_calls_made = [call.function.name for call in assistant_message.tool_calls]
                has_tool_calls = any(name.startswith("mcp_tool_") for name in tool_calls_made)
                has_prompt_calls = any(name.startswith("mcp_prompt_") for name in tool_calls_made)
                
                # Check if user wanted comprehensive output
                wants_comprehensive = any(word in user_message.lower() for word in [
                    "report", "analysis", "comprehensive", "detailed", "analyze", "study"
                ])
                
                if has_tool_calls and not has_prompt_calls and wants_comprehensive:
                    print(f"\n🔄 Detected request for comprehensive output - suggesting prompt usage")
                    
                    # Let OpenAI decide what to do next with the data
                    follow_up_response = await self.openai_client.chat.completions.create(
                        model=self.model,
                        messages=messages + [{
                            "role": "user",
                            "content": "Based on the data you just gathered, please use an appropriate prompt to generate a comprehensive, well-structured response that addresses my original request."
                        }],
                        tools=functions,
                        tool_choice="auto",
                        temperature=0.1,
                        max_tokens=4000
                    )
                    
                    follow_up_message = follow_up_response.choices[0].message
                    
                    if follow_up_message.tool_calls:
                        print(f"\n🔄 Follow-up: OpenAI making {len(follow_up_message.tool_calls)} additional function call(s)")
                        
                        # Add follow-up message
                        messages.append({
                            "role": "assistant",
                            "content": follow_up_message.content,
                            "tool_calls": [
                                {
                                    "id": call.id,
                                    "type": call.type,
                                    "function": {
                                        "name": call.function.name,
                                        "arguments": call.function.arguments
                                    }
                                }
                                for call in follow_up_message.tool_calls
                            ]
                        })
                        
                        # Execute follow-up function calls
                        for tool_call in follow_up_message.tool_calls:
                            function_name = tool_call.function.name
                            try:
                                function_args = json.loads(tool_call.function.arguments)
                            except json.JSONDecodeError:
                                function_args = {}
                            
                            print(f"🔧 Executing follow-up: {function_name}({function_args})")
                            
                            result = await self._execute_mcp_function(function_name, function_args, user_message)
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result
                            })
                
                # Get final response from OpenAI
                final_response = await self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=4000
                )
                
                ai_response = final_response.choices[0].message.content
            else:
                ai_response = assistant_message.content
            
            print(f"\n🤖 Assistant: {ai_response}")
            return ai_response
            
        except Exception as e:
            error_msg = f"Error in orchestration: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def _execute_mcp_function(self, function_name: str, function_args: Dict[str, Any], user_message: str = "") -> str:
        """Execute an MCP function generically with fallback parameter extraction"""
        try:
            # If function_args is empty, try to extract parameters from user message
            if not function_args and user_message:
                function_args = self._extract_parameters_from_message(function_name, user_message)
                if function_args:
                    print(f"🔧 Using fallback parameter extraction: {function_args}")
            
            if function_name.startswith("mcp_tool_"):
                # Extract tool name and call MCP tool
                tool_name = function_name.replace("mcp_tool_", "")
                return await self.mcp_client.call_tool(tool_name, function_args)
                
            elif function_name.startswith("mcp_resource_"):
                # Find and read the corresponding resource
                resource_name = function_name.replace("mcp_resource_", "").replace("_", " ").title()
                
                for resource in self.mcp_client.available_resources:
                    if resource['name'].lower().replace(" ", "_") == function_name.replace("mcp_resource_", ""):
                        return await self.mcp_client.get_resource(resource['uri'])
                
                return f"Resource not found: {resource_name}"
                
            elif function_name.startswith("mcp_prompt_"):
                # Extract prompt name and call MCP prompt
                prompt_name = function_name.replace("mcp_prompt_", "")
                return await self.mcp_client.get_prompt(prompt_name, function_args)
                
            else:
                return f"Unknown MCP function: {function_name}"
                
        except Exception as e:
            return f"Error executing {function_name}: {str(e)}"
    
    def _extract_parameters_from_message(self, function_name: str, user_message: str) -> Dict[str, Any]:
        """Extract parameters from user message as fallback"""
        import re
        
        user_lower = user_message.lower()
        params = {}
        
        # Extract for calculator tool
        if 'calculator' in function_name:
            # Look for mathematical expressions
            math_patterns = [
                r'calculate\s+(.+?)(?:\?|$)',
                r'what\'s\s+(.+?)(?:\?|$)', 
                r'(\d+(?:\.\d+)?\s*[+\-*/×÷]\s*\d+(?:\.\d+)?(?:\s*[+\-*/×÷]\s*\d+(?:\.\d+)?)*)',
                r'([^a-zA-Z]*\d+[^a-zA-Z]*[+\-*/×÷][^a-zA-Z]*\d+[^a-zA-Z]*)',
            ]
            
            for pattern in math_patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    expression = match.group(1).strip()
                    # Clean up expression
                    expression = expression.replace('×', '*').replace('÷', '/')
                    if expression and any(op in expression for op in ['+', '-', '*', '/']):
                        params['expression'] = expression
                        break
        
        # Extract for weather tools
        elif 'weather' in function_name:
            patterns = [
                r'weather (?:in|for|at) ([^?.,!]+)',
                r'(?:what\'s|what is) (?:the )?weather (?:in|for|at) ([^?.,!]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, user_lower)
                if match:
                    location = match.group(1).strip()
                    location = re.sub(r'\s+(today|tomorrow|now|\?|\.|\!|right now|currently).*', '', location)
                    if len(location) >= 2:
                        params['location'] = location.title()
                        break
        
        # Extract for search tools
        elif 'search' in function_name or 'duck' in function_name:
            # Look for research/search terms
            search_patterns = [
                r'research\s+(.+?)(?:\s+and|$)',
                r'search\s+(?:for\s+)?(.+?)(?:\s+and|$)',
                r'(?:information|data) (?:about|on) (.+?)(?:\s+and|$)',
                r'(?:find|look up) (.+?)(?:\s+and|$)',
            ]
            
            for pattern in search_patterns:
                match = re.search(pattern, user_lower)
                if match:
                    query = match.group(1).strip()
                    if query:
                        params['query'] = f"{query} company information"
                        params['search_type'] = 'company'
                        break
            
            # If no specific pattern matched, use the whole message as query
            if not params and len(user_message.split()) <= 10:
                # Clean message for simple queries
                clean_query = re.sub(r'(research|search|find|look up|information about)', '', user_lower).strip()
                if clean_query:
                    params['query'] = clean_query
        
        return params

async def interactive_mode():
    """Run interactive chat mode with orchestration agent"""
    agent = OrchestrationAgent()
    
    try:
        print("🎯 OpenAI-Orchestrated MCP Client - Interactive Mode")
        print("=" * 60)
        
        # Initialize agent
        await agent.initialize()
        
        print("\n💡 Ready for intelligent orchestration!")
        print("OpenAI will automatically decide which MCP capabilities to use.")
        print("Type 'quit', 'exit', or 'bye' to exit")
        print("Type 'capabilities' to see available MCP functions")
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'capabilities':
                    print("\n🔧 Available MCP Tools:")
                    for tool in agent.mcp_client.available_tools:
                        print(f"  • {tool['name']}: {tool['description']}")
                    
                    print("\n📚 Available MCP Resources:")
                    for resource in agent.mcp_client.available_resources:
                        print(f"  • {resource['name']}: {resource['description']}")
                    
                    print("\n📝 Available MCP Prompts:")
                    for prompt in agent.mcp_client.available_prompts:
                        print(f"  • {prompt['name']}: {prompt['description']}")
                    print()
                    continue
                
                if user_input:
                    await agent.chat(user_input)
                    print()
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
    
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\n📝 Please create a .env file with:")
        print("OPENAI_API_KEY=your_openai_api_key_here")
    except Exception as e:
        print(f"\n❌ Error: {e}")

async def demo_mode():
    """Run demonstration mode"""
    agent = OrchestrationAgent()
    
    try:
        print("🚀 OpenAI-Orchestrated MCP Client - Demo Mode")
        print("=" * 55)
        
        # Initialize agent
        await agent.initialize()
        
        print("\n🎯 Demonstrating intelligent orchestration...")
        print("OpenAI will decide which MCP capabilities to use for each query.")
        
        sample_queries = [
            "What's the weather like in Paris?",
            "Calculate 144 + 25",
            "Research Tesla and create a comprehensive report",
            "Search for information about Apple Inc and analyze the company"
        ]
        
        for i, query in enumerate(sample_queries, 1):
            print(f"\n{'='*20} Demo Query {i}/{len(sample_queries)} {'='*20}")
            await agent.chat(query)
            await asyncio.sleep(2)  # Pause between queries
        
        print(f"\n✨ Demo complete!")
        print("Notice how OpenAI automatically chose the right MCP capabilities for each request!")
        print("Run with --interactive for live orchestration.")
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\n📝 Please create a .env file with:")
        print("OPENAI_API_KEY=your_openai_api_key_here")
    except Exception as e:
        print(f"\n❌ Error: {e}")

async def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        await interactive_mode()
    else:
        await demo_mode()

if __name__ == "__main__":
    asyncio.run(main())