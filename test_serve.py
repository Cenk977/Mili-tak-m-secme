#!/usr/bin/env python3
"""Test server startup and basic operations."""

import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

try:
    logger.info("Importing database...")
    from database import init_db

    logger.info("Initializing database...")
    init_db()
    logger.info("✓ Database initialized")

    logger.info("Importing serve...")
    from panel.serve import main

    logger.info("Starting server...")
    main()
except Exception as e:
    logger.exception(f"✗ Error: {e}")
    sys.exit(1)
