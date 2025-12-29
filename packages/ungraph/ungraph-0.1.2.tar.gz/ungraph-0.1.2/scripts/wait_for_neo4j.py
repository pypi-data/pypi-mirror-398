#!/usr/bin/env python3
"""
Wait for Neo4j to be ready.

This script repeatedly attempts to connect to Neo4j until it succeeds
or times out. Useful for CI/CD pipelines and Docker Compose setups.

Usage:
    python scripts/wait_for_neo4j.py
    python scripts/wait_for_neo4j.py --uri bolt://localhost:7687 --user neo4j --password testpassword123 --timeout 60
"""

import sys
import time
import argparse
from typing import Optional

try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable, AuthError
except ImportError:
    print("Error: neo4j package not installed. Install with: pip install neo4j", file=sys.stderr)
    sys.exit(1)


def check_neo4j_connection(uri: str, user: str, password: str) -> bool:
    """
    Check if Neo4j is ready by attempting a simple query.
    
    Args:
        uri: Neo4j connection URI
        user: Neo4j username
        password: Neo4j password
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        driver.close()
        return True
    except (ServiceUnavailable, AuthError, Exception):
        return False


def wait_for_neo4j(
    uri: str = "bolt://localhost:7687",
    user: str = "neo4j",
    password: str = "password",
    timeout: int = 60,
    interval: int = 2
) -> bool:
    """
    Wait for Neo4j to be ready.
    
    Args:
        uri: Neo4j connection URI
        user: Neo4j username
        password: Neo4j password
        timeout: Maximum time to wait in seconds
        interval: Time between retry attempts in seconds
        
    Returns:
        True if Neo4j is ready, False if timeout
    """
    start_time = time.time()
    attempt = 0
    
    print(f"Waiting for Neo4j at {uri}...", file=sys.stderr)
    
    while True:
        attempt += 1
        elapsed = time.time() - start_time
        
        if check_neo4j_connection(uri, user, password):
            print(f"Neo4j is ready! (attempt {attempt}, {elapsed:.1f}s)", file=sys.stderr)
            return True
        
        if elapsed >= timeout:
            print(f"Timeout: Neo4j not ready after {timeout}s", file=sys.stderr)
            return False
        
        time.sleep(interval)
        print(f"Attempt {attempt}: Neo4j not ready yet, retrying in {interval}s...", file=sys.stderr)
    
    return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Wait for Neo4j to be ready",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use defaults (bolt://localhost:7687, user=neo4j, password=password)
  python scripts/wait_for_neo4j.py
  
  # Specify connection details
  python scripts/wait_for_neo4j.py --uri bolt://localhost:7687 --user neo4j --password testpassword123
  
  # Custom timeout
  python scripts/wait_for_neo4j.py --timeout 120 --interval 5
        """
    )
    
    parser.add_argument(
        "--uri",
        default="bolt://localhost:7687",
        help="Neo4j connection URI (default: bolt://localhost:7687)"
    )
    parser.add_argument(
        "--user",
        default="neo4j",
        help="Neo4j username (default: neo4j)"
    )
    parser.add_argument(
        "--password",
        default="password",
        help="Neo4j password (default: password)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Maximum time to wait in seconds (default: 60)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=2,
        help="Time between retry attempts in seconds (default: 2)"
    )
    
    args = parser.parse_args()
    
    success = wait_for_neo4j(
        uri=args.uri,
        user=args.user,
        password=args.password,
        timeout=args.timeout,
        interval=args.interval
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

