#!/usr/bin/env python3
"""
ContractIQ - Autonomous Contract-Driven Quality Engineering
Main entry point for the ContractIQ agentic QE framework.

Usage:
    python run_contractiq.py --mode api --spec ./specs/sample-openapi.yaml
    python run_contractiq.py --mode ui --target https://myapp.example.com --spec ./specs/sample-ui-spec.yaml
    python run_contractiq.py --mode full --spec ./specs/sample-openapi.yaml --target https://myapp.example.com
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path
from typing import Optional
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
