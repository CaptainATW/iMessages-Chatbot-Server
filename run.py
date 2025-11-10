#!/usr/bin/env python3
"""
Echo Server Launcher

Run this script to start the iMessage AI conversation server.
Usage: python3 run.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.server import main
import asyncio

if __name__ == '__main__':
    asyncio.run(main())

