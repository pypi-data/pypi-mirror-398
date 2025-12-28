#!/usr/bin/env python3
"""
Snyk MCP Server - Fetch vulnerability data from Snyk REST API
"""

import os
import asyncio
from typing import List
from dotenv import load_dotenv
from fastmcp import FastMCP
from .snyk.client import SnykClient, SnykAPIError
from .snyk.models import Vulnerability

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP("Snyk Vulnerability Server")

# Global client instance
_client: SnykClient = None


async def get_client() -> SnykClient:
    """Get or create Snyk client instance"""
    global _client
    if _client is None:
        api_token = os.getenv("SNYK_API_TOKEN")
        api_version = os.getenv("SNYK_API_VERSION", "2024-06-21")
        
        if not api_token:
            raise ValueError("SNYK_API_TOKEN environment variable is required")
        
        _client = SnykClient(api_token, api_version)
    
    return _client


@mcp.tool()
async def fetch_org_vulnerabilities(org_id: str) -> List[dict]:
    """
    Fetch all vulnerabilities for a Snyk organization.
    
    Args:
        org_id: The Snyk organization ID
        
    Returns:
        List of normalized vulnerability objects
        
    Raises:
        ValueError: If org_id is invalid
        SnykAPIError: If API request fails
    """
    try:
        client = await get_client()
        async with client:
            vulnerabilities = await client.fetch_org_vulnerabilities(org_id)
            return [vuln.model_dump() for vuln in vulnerabilities]
    except SnykAPIError as e:
        raise Exception(f"Snyk API error: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")


@mcp.tool()
async def fetch_package_vulnerabilities(org_id: str, purl: str) -> List[dict]:
    """
    Fetch direct vulnerabilities for a specific package.
    
    Args:
        org_id: The Snyk organization ID
        purl: Package URL (e.g., pkg:npm/lodash@4.17.20)
        
    Returns:
        List of normalized vulnerability objects for the package
        
    Raises:
        ValueError: If org_id or purl is invalid
        SnykAPIError: If API request fails
    """
    try:
        client = await get_client()
        async with client:
            vulnerabilities = await client.fetch_package_vulnerabilities(org_id, purl)
            return [vuln.model_dump() for vuln in vulnerabilities]
    except SnykAPIError as e:
        raise Exception(f"Snyk API error: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")


def main():
    """Entry point for the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()