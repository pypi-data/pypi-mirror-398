"""
pytest configuration for ai-git-messages tests.
"""

import sys
from pathlib import Path

# Add src to path so all tests can import ai_git_messages
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
