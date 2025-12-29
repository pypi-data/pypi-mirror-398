#!/usr/bin/env python3
"""
CostGov Test CLI

A simple test script to verify your CostGov SDK setup.
This script reads from environment variables and sends a single test event.

Usage:
    1. Set up your .env file with COSTGOV_API_KEY, COSTGOV_PROJECT_ID, COSTGOV_API_URL
    2. Run: python -m costgov.test
    Or: costgov-test (if installed via pip)

Security:
    - This script only reads environment variables YOU set
    - It only makes a single HTTPS request to the CostGov ingest endpoint
    - No file system access, no other network calls
    - Open source and auditable
"""

import os
import sys
import time

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    DIM = '\033[2m'


def log(color: str, message: str) -> None:
    print(f"{color}{message}{Colors.RESET}")


def main() -> None:
    log(Colors.BLUE, '🔍 CostGov SDK Test\n')
    
    # Check required environment variables
    api_key = os.environ.get('COSTGOV_API_KEY')
    project_id = os.environ.get('COSTGOV_PROJECT_ID')
    api_url = os.environ.get('COSTGOV_API_URL', 'https://ingest.costgov.com')
    
    if not api_key:
        log(Colors.RED, '❌ Missing COSTGOV_API_KEY environment variable')
        log(Colors.DIM, '\nMake sure to set these environment variables:')
        log(Colors.DIM, '  export COSTGOV_API_KEY=cg_prod_...')
        log(Colors.DIM, '  export COSTGOV_PROJECT_ID=proj_...')
        log(Colors.DIM, '  export COSTGOV_API_URL=http://localhost:3001  (or https://ingest.costgov.com)')
        log(Colors.DIM, '\nThen run: python -m costgov.test')
        sys.exit(1)
    
    if not project_id:
        log(Colors.RED, '❌ Missing COSTGOV_PROJECT_ID environment variable')
        sys.exit(1)
    
    # Show configuration (mask sensitive parts)
    log(Colors.DIM, f'API Key: {api_key[:12]}...{api_key[-4:]}')
    log(Colors.DIM, f'Project: {project_id}')
    log(Colors.DIM, f'API URL: {api_url}\n')
    
    try:
        # Import here to avoid import errors if package not installed correctly
        from costgov import CostGov
        
        # Initialize the client
        client = CostGov(
            api_key=api_key,
            project_id=project_id,
            api_url=api_url,
        )
        
        log(Colors.YELLOW, '📤 Sending test event...')
        
        # Track a test event
        client.track('costgov.test', 1)
        
        # Wait for the event to be sent (the SDK batches events)
        time.sleep(2.5)
        
        # Shutdown gracefully
        client.shutdown()
        
        log(Colors.GREEN, '\n✅ Test event sent successfully!')
        log(Colors.DIM, '\nYour CostGov integration is working. You should see this event')
        log(Colors.DIM, 'in your CostGov dashboard within a few seconds.')
        
    except ImportError as e:
        log(Colors.RED, f'\n❌ Import error: {e}')
        log(Colors.DIM, '\nMake sure you have installed the costgov package:')
        log(Colors.DIM, '  pip install costgov')
        sys.exit(1)
    except Exception as e:
        log(Colors.RED, f'\n❌ Test failed: {e}')
        log(Colors.DIM, '\nCommon issues:')
        log(Colors.DIM, '  • Check that your API key is correct')
        log(Colors.DIM, '  • Ensure the ingest service is running (if using localhost)')
        log(Colors.DIM, '  • Verify your network connection')
        sys.exit(1)


if __name__ == '__main__':
    main()
