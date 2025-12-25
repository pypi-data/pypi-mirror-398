"""
Main entry point for sbom-git-sm when run as a module.

Copyright (c) 2025 Janosch Meyer (janosch.code@proton.me)
This project is licensed under the MIT License - see the LICENSE file for details.
This project was created with the assistance of artificial intelligence.

This module allows the package to be executed directly with the -m flag:
python -m sbom_git_sm
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())