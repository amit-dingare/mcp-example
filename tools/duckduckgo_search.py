#!/usr/bin/env python3
"""
DuckDuckGo Search Tool for MCP Server

This tool provides web search capabilities using DuckDuckGo's instant answer API
and can extract company information for business analysis.

Requirements:
    pip install requests beautifulsoup4
"""

import requests
import json
import re
from typing import Dict, Any, Optional
from urllib.parse import quote_plus

# Tool metadata
TOOL_NAME = "duckduckgo_search"
TOOL_DESCRIPTION = "🔍 PREFERRED: Real-time web search for companies, businesses, and general information using DuckDuckGo"

def clean_text(text) -> str:
    """Clean and normalize text from web results"""
    if not text:
        return ""
    
    # Handle case where text might be a dict or other non-string type
    if not isinstance(text, str):
        text = str(text)
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    
    return text

def extract_company_info(query: str, results: Dict) -> Dict[str, str]:
    """Extract structured company information from search results"""
    info = {
        "company_name": "",
        "industry": "",
        "description": "",
        "founded": "",
        "headquarters": "",
        "website": "",
        "key_facts": ""
    }
    
    # Better company name extraction from query
    # Remove common search terms and extract the actual company name
    clean_query = query.lower()
    
    # Remove search-related terms
    search_terms = ['company', 'business', 'information', 'corp', 'corporation', 'inc', 'ltd', 'llc', 'analysis', 'report']
    for term in search_terms:
        clean_query = clean_query.replace(term, ' ')
    
    # Clean up and extract company name
    clean_query = re.sub(r'\s+', ' ', clean_query.strip())
    words = clean_query.split()
    
    # Use the first significant word(s) as company name
    if words:
        # For well-known companies, use the first word
        if words[0] in ['tesla', 'apple', 'google', 'microsoft', 'amazon', 'facebook', 'meta', 'netflix', 'uber', 'airbnb']:
            info["company_name"] = words[0].title()
        else:
            # For other companies, use first 1-2 words
            info["company_name"] = ' '.join(words[:2]).title() if len(words) > 1 else words[0].title()
    
    # Extract information from DuckDuckGo results
    if "Abstract" in results and results["Abstract"]:
        abstract = clean_text(results["Abstract"])
        info["description"] = abstract
        
        # Look for industry keywords in abstract
        industry_keywords = {
            "software": ["software", "technology", "tech", "app", "platform", "saas"],
            "finance": ["bank", "financial", "investment", "insurance", "fintech"],
            "retail": ["retail", "store", "shopping", "ecommerce", "marketplace"],
            "healthcare": ["healthcare", "medical", "pharmaceutical", "biotech"],
            "manufacturing": ["manufacturing", "automotive", "industrial"],
            "media": ["media", "entertainment", "streaming", "content"],
            "energy": ["energy", "oil", "renewable", "solar", "wind"]
        }
        
        abstract_lower = abstract.lower()
        for industry, keywords in industry_keywords.items():
            if any(keyword in abstract_lower for keyword in keywords):
                info["industry"] = industry.title()
                break
    
    # Extract other structured data
    if "Infobox" in results and results["Infobox"]:
        infobox = results["Infobox"]
        if "content" in infobox:
            for item in infobox["content"]:
                if "data_type" in item and "value" in item:
                    data_type = item["data_type"].lower()
                    value = clean_text(item["value"])
                    
                    if "founded" in data_type or "established" in data_type:
                        info["founded"] = value
                    elif "headquarters" in data_type or "location" in data_type:
                        info["headquarters"] = value
                    elif "industry" in data_type and not info["industry"]:
                        info["industry"] = value
    
    # Extract website URL
    if "AbstractURL" in results and results["AbstractURL"]:
        info["website"] = results["AbstractURL"]
    
    # Compile key facts from related topics
    key_facts = []
    if "RelatedTopics" in results:
        for topic in results["RelatedTopics"][:3]:  # Limit to first 3
            if "Text" in topic:
                fact = clean_text(topic["Text"])
                if fact and len(fact) > 20:  # Only include substantial facts
                    key_facts.append(fact)
    
    if key_facts:
        info["key_facts"] = " • ".join(key_facts)
    
    return info

async def tool_function(query: str = "", search_type: str = "company") -> str:
    """
    Search DuckDuckGo and optionally extract company information
    
    Args:
        query: Search query (company name, topic, etc.)
        search_type: Type of search - "company" for structured company info, "general" for raw results
    
    Returns:
        JSON string with search results or company information
    """
    try:
        if not query:
            return json.dumps({
                "error": "Query parameter is required",
                "usage": "Provide a search query, e.g., 'Apple Inc company' or 'Tesla business information'"
            }, indent=2)
        
        print(f"🔍 Searching for: {query}")
        
        # Prepare search query - try multiple variations for better results
        search_queries = [
            query,
            f"{query.split()[0]} company" if query.split() else query,
            f"{query} wikipedia" if not "wikipedia" in query.lower() else query
        ]
        
        best_result = None
        best_score = 0
        
        # Try different search variations to get the best results
        for search_query in search_queries[:2]:  # Limit to 2 attempts to avoid rate limiting
            encoded_query = quote_plus(search_query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            # Make request with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                results = response.json()
                
                # Score the results based on content quality
                score = 0
                if results.get("Abstract"):
                    score += len(results["Abstract"])
                if results.get("RelatedTopics"):
                    score += len(results["RelatedTopics"]) * 10
                if results.get("Infobox"):
                    score += 50
                
                print(f"🔍 Search '{search_query}' scored: {score}")
                
                if score > best_score:
                    best_score = score
                    best_result = results
                    
            except Exception as e:
                print(f"⚠️ Search attempt failed for '{search_query}': {e}")
                continue
        
        if not best_result:
            # Fallback - create a basic response with the company name
            fallback_info = extract_company_info(query, {})
            fallback_info.update({
                "search_query": query,
                "results_found": False,
                "description": f"Search data for {fallback_info['company_name']} was not available from DuckDuckGo. This could be due to rate limiting or the company being private/less publicly known.",
                "industry": "Information not available",
                "key_facts": "No specific details retrieved from search"
            })
            
            print(f"⚠️ Using fallback response for {fallback_info['company_name']}")
            return json.dumps(fallback_info, indent=2)
        
        if search_type == "company":
            # Extract structured company information
            company_info = extract_company_info(query, best_result)
            
            # Add raw search metadata
            company_info["search_query"] = query
            company_info["results_found"] = bool(best_result.get("Abstract") or best_result.get("RelatedTopics"))
            
            # Add additional context if available
            if best_result.get("Answer"):
                company_info["quick_answer"] = clean_text(best_result["Answer"])
            
            # If we still have minimal data, try to provide some useful defaults
            if not company_info["description"] and not company_info["results_found"]:
                company_name = company_info["company_name"]
                company_info["description"] = f"{company_name} is a company that operates in various business sectors. Detailed information was not available from current search results."
                company_info["industry"] = "Information not available"
                company_info["key_facts"] = "Company details require additional research from official sources"
            
            print(f"✅ Extracted info for: {company_info['company_name']}")
            return json.dumps(company_info, indent=2)
        
        else:
            # Return general search results
            general_results = {
                "query": query,
                "abstract": clean_text(results.get("Abstract", "")),
                "answer": clean_text(results.get("Answer", "")),
                "abstract_url": results.get("AbstractURL", ""),
                "image": results.get("Image", ""),
                "related_topics": [],
                "search_successful": True
            }
            
            # Add related topics
            if "RelatedTopics" in results:
                for topic in results["RelatedTopics"][:5]:
                    if "Text" in topic:
                        topic_info = {
                            "text": clean_text(topic["Text"]),
                            "url": topic.get("FirstURL", "")
                        }
                        general_results["related_topics"].append(topic_info)
            
            return json.dumps(general_results, indent=2)
    
    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": f"Network error: {str(e)}",
            "suggestion": "Check your internet connection and try again",
            "search_successful": False
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": f"Search error: {str(e)}",
            "query": query,
            "search_type": search_type,
            "search_successful": False
        }, indent=2)

# Synchronous wrapper for compatibility
def tool_function_sync(*args, **kwargs):
    """Synchronous wrapper for the tool function"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(tool_function(*args, **kwargs))
    except RuntimeError:
        # If no event loop exists, create one
        return asyncio.run(tool_function(*args, **kwargs))

# For direct testing
if __name__ == "__main__":
    import asyncio
    
    async def test_tool():
        print("Testing DuckDuckGo Search Tool")
        print("=" * 40)
        
        # Test company search
        print("\n1. Company Search Test:")
        result = await tool_function("Apple Inc company", "company")
        print(result)
        
        print("\n2. General Search Test:")
        result = await tool_function("Python programming language", "general")
        print(result)
        
        print("\n3. Business Search Test:")
        result = await tool_function("Tesla business information", "company")
        print(result)
    
    asyncio.run(test_tool())