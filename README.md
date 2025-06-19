# OpenAI-Orchestrated MCP Framework

A powerful demonstration of the **Model Context Protocol (MCP)** with intelligent OpenAI orchestration that automatically decides which tools, resources, and prompts to use based on user intent.

## 🌟 Overview

This repository showcases a complete MCP ecosystem where:
- **FastMCP Server** dynamically loads capabilities from folders
- **OpenAI Orchestration** intelligently decides which MCP functions to call
- **Smart Prompts** transform raw tool data into professional reports
- **No Manual Function Selection** - OpenAI handles everything automatically

## 🎯 Key Features

- **🤖 Intelligent Orchestration**: OpenAI analyzes user intent and automatically selects appropriate MCP capabilities
- **📁 Dynamic Loading**: Tools, resources, and prompts loaded from simple folder structures
- **🔄 Workflow Automation**: Automatic tool→prompt workflows for comprehensive responses
- **⚡ Zero Configuration**: Works out-of-the-box with sample tools and prompts
- **🎨 Professional Output**: Raw data transformed into polished reports and analyses

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  User Query     │───▶│ OpenAI           │───▶│ MCP Server      │
│ "Weather report │    │ Orchestrator     │    │                 │
│  for Tokyo"     │    │                  │    │ ├── tools/      │
└─────────────────┘    │ ┌──────────────┐ │    │ ├── resources/  │
                       │ │ Analyzes     │ │    │ └── prompts/    │
┌─────────────────┐    │ │ Intent       │ │    └─────────────────┘
│ Professional    │◀───│ │              │ │           │
│ Weather Report  │    │ │ Selects      │ │           │
│ with Analysis   │    │ │ Tools &      │ │    ┌──────▼──────┐
└─────────────────┘    │ │ Prompts      │ │    │ 1. weather   │
                       │ └──────────────┘ │    │ 2. weather_  │
                       └──────────────────┘    │    report    │
                                               └─────────────┘
```

## 📁 Project Structure

```
mcp-framework/
├── orchestrated_mcp_client.py    # OpenAI-powered orchestration client
├── mcp_server.py                 # FastMCP server with dynamic loading
├── .env                          # API keys and configuration
├── tools/                        # Tool implementations
│   ├── calculator.py            #   Safe mathematical calculations
│   ├── duckduckgo_search.py     #   Web search capabilities
│   ├── file_operations.py       #   File handling operations
│   └── weather.py               #   Weather data from OpenWeatherMap
├── resources/                    # Static resources and documents
│   ├── company_info.txt         #   Company information
│   ├── customer_data.json       #   Customer database
│   ├── monthly_report.txt       #   Business performance report
│   └── user_data.json           #   User information data
└── prompts/                      # Prompt templates
    ├── calculation_analysis.json#   Mathematical insights and analysis
    ├── company_research_report.json# Comprehensive business reports
    ├── system_prompt.txt         #   System instructions
    └── weather_report.json       #   Professional weather analysis
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp-framework

# Install dependencies
pip install mcp fastmcp openai python-dotenv aiohttp
```

### 2. Configuration

Create a `.env` file with your API keys:

```env
# Required for OpenAI orchestration
OPENAI_API_KEY=your_openai_api_key_here

# Required for weather tool
OPENWEATHER_API_KEY=your_openweather_api_key_here
```

### 3. Start the MCP Server

```bash
python mcp_server.py
```

### 4. Run the Orchestrated Client

```bash
# Interactive mode
python orchestrated_mcp_client.py --interactive

# Demo mode
python orchestrated_mcp_client.py
```

## 🎭 Demonstration: The Power of Prompts

### Basic Tool Usage vs. Enhanced Prompts

**Simple Query (Tool Only):**
```
You: What's the weather in Tokyo?
Assistant: 🌤️ Weather in Tokyo, Japan:
Temperature: 22°C (feels like 24°C)
Conditions: Clear Sky
Humidity: 65%
Pressure: 1013 hPa
Wind Speed: 3.2 m/s
```

**Enhanced Query (Tool + Prompt):**
```
You: Give me a detailed weather report for Tokyo
Assistant: # 🌤️ Weather Report for Tokyo

## Current Conditions
🌤️ Weather in Tokyo, Japan:
Temperature: 22°C (feels like 24°C)
Conditions: Clear Sky
Humidity: 65%
Pressure: 1013 hPa
Wind Speed: 3.2 m/s

## Detailed Analysis

### 🌡️ Temperature Assessment
The current temperature of 22°C is quite comfortable for most activities...

### 👕 Clothing Suggestions
- Light layers recommended
- T-shirt or light shirt with optional light jacket...

### 🚶 Activity Recommendations
- Perfect for outdoor walks or jogging
- Excellent conditions for sightseeing...

[... continues with comprehensive analysis ...]
```

### Calculator Example

**Basic Calculation:**
```
You: Calculate 144 + 25
Assistant: 📊 Result: 144 + 25 = 169
```

**Mathematical Analysis:**
```
You: Give me a detailed mathematical analysis of 144 + 25
Assistant: # 📊 Mathematical Analysis Report

## Calculation Summary
📊 Result: 144 + 25 = 169

## Detailed Analysis

### 🔢 Expression Breakdown
This is a basic arithmetic addition involving two perfect squares...

### 📈 Mathematical Insights
Interestingly, both numbers are perfect squares (12² and 5²)...

### 🎯 Result Interpretation
The result 169 is also a perfect square (13²), creating a 
Pythagorean relationship: 12² + 5² = 13²...

[... continues with educational content ...]
```

## 🧠 How the Intelligence Works

The OpenAI orchestrator automatically detects user intent:

### Trigger Words for Enhanced Analysis:
- **"detailed"** → Uses prompts for comprehensive output
- **"report"** → Generates professional reports  
- **"analysis"** → Provides analytical insights
- **"comprehensive"** → Creates thorough documentation

### Simple Queries:
- Basic questions → Uses tools only
- Quick lookups → Returns raw data

## 🛠️ Available Tools

### Weather Tool
- **Function**: Get current weather for any location
- **API**: OpenWeatherMap integration
- **Usage**: `"What's the weather in [city]?"`

### Calculator Tool
- **Function**: Safe mathematical calculations
- **Features**: Basic arithmetic, functions (sqrt, sin, cos, etc.)
- **Usage**: `"Calculate [expression]"`

### DuckDuckGo Search Tool
- **Function**: Web search capabilities
- **Features**: Real-time web search results
- **Usage**: `"Search for [query]"` or `"Research [topic]"`

### File Operations Tool
- **Function**: File handling and management
- **Features**: Read, write, and manipulate files
- **Usage**: `"Read file [filename]"` or `"Create file with [content]"`

## 📝 Available Prompts

### Weather Report
- **Purpose**: Transform weather data into professional reports
- **Includes**: Analysis, recommendations, comfort ratings
- **Trigger**: `"detailed weather report"`

### Calculation Analysis  
- **Purpose**: Educational mathematical analysis
- **Includes**: Step-by-step solutions, number properties, applications
- **Trigger**: `"mathematical analysis"`

### Company Research Report
- **Purpose**: Comprehensive business analysis and reports
- **Includes**: Market analysis, financial insights, strategic recommendations
- **Trigger**: `"company research report"` or `"business analysis"`

### System Prompt
- **Purpose**: Core system instructions and behavior
- **Usage**: Internal system guidance

## 🎯 Example Queries

Try these to see the orchestration in action:

```bash
# Weather Examples
"What's the weather in Paris?"                          # Tool only
"Give me a comprehensive weather report for London"     # Tool + Prompt

# Calculator Examples  
"Calculate sqrt(144)"                                   # Tool only
"Provide detailed analysis of sqrt(144)"               # Tool + Prompt

# Search Examples
"Search for Python tutorials"                          # Tool only  
"Research artificial intelligence and create a report" # Tool + Prompt

# File Examples
"Read the company info file"                           # Resource access
"Show me customer data and create an analysis"        # Resource + Prompt

# Business Examples
"Research Tesla"                                        # Tool only
"Research Tesla and create a comprehensive report"     # Tool + Prompt
```

### Adding Resources

1. Place any text/JSON file in `resources/`
2. Access via: `"Show me the [filename] resource"`

## 🔧 Adding New Capabilities

### Adding a New Tool

1. Create `tools/my_tool.py`:
```python
TOOL_NAME = "my_tool"
TOOL_DESCRIPTION = "Description of what this tool does"

async def tool_function(param: str) -> str:
    """Tool implementation"""
    return f"Result: {param}"
```

2. Restart the server - automatically loaded!

### Adding a New Prompt

1. Create `prompts/my_prompt.json`:
```json
{
  "name": "my_prompt",
  "description": "What this prompt creates",
  "template": "# {title}\n\n{content}",
  "arguments": [
    {"name": "title", "description": "Report title", "required": true},
    {"name": "content", "description": "Main content", "required": true}
  ]
}
```

2. Restart the server - automatically loaded!

## 📚 Available Resources

### Company Information
- **File**: `company_info.txt`
- **Content**: Company overview, mission, values, products
- **Usage**: `"Show me company information"`

### Customer Data
- **File**: `customer_data.json`
- **Content**: Customer database with metrics and status
- **Usage**: `"Access customer data"` or `"Show customer information"`

### Monthly Report
- **File**: `monthly_report.txt`
- **Content**: Business performance metrics and analysis
- **Usage**: `"Display monthly report"`

### User Data
- **File**: `user_data.json`
- **Content**: User information and preferences
- **Usage**: `"Retrieve user data"`

## 🎨 Customization

### Modify System Prompt
Edit the `_build_system_prompt()` method in `orchestrated_mcp_client.py` to customize OpenAI's behavior.

### Adjust Workflow Detection
Modify the trigger words in the workflow detection logic to change when prompts are used.

### API Configuration
Add new API keys and settings to `.env` for additional tools.

## 🔍 Troubleshooting

### Common Issues

**"OpenAI API key not found"**
- Ensure `OPENAI_API_KEY` is set in `.env`

**"Weather API key not configured"**  
- Get free API key from [OpenWeatherMap](https://openweathermap.org/api)
- Add `OPENWEATHER_API_KEY` to `.env`

**"Connection timeout"**
- Check that MCP server is running
- Verify no port conflicts

**"No tools/prompts loaded"**
- Check file permissions
- Verify folder structure
- Review server startup logs

### Debug Mode

Enable verbose logging by modifying the print statements in both client and server files.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Add new tools/prompts following the existing patterns
4. Test with the orchestrated client
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Anthropic** for the Model Context Protocol
- **FastMCP** for the simplified server framework
- **OpenAI** for intelligent orchestration capabilities

## 🚀 What's Next?

This framework demonstrates the future of AI interactions:
- **No manual function selection** - AI decides everything
- **Professional output** - Raw data becomes polished reports  
- **Extensible architecture** - Easy to add new capabilities
- **Real-world applications** - Ready for production use

Try it out and see how MCP + OpenAI orchestration transforms simple tools into intelligent, comprehensive AI assistants! 🎉
