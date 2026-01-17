#!/usr/bin/env python
"""Flow Guardian - Return to flow state in 30 seconds."""
from dotenv import load_dotenv
load_dotenv()

from flow.cli import app

if __name__ == "__main__":
    app()
