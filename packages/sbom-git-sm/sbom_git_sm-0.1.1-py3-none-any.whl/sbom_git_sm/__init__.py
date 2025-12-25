"""
sbom-git-sm - A tool to create a Software Bill of Materials (SBOM) from a git repository based on its submodules.

Copyright (c) 2025 Janosch Meyer (janosch.code@proton.me)
This project is licensed under the MIT License - see the LICENSE file for details.
This project was created with the assistance of artificial intelligence.

This package provides tools to create a Software Bill of Materials (SBOM) from a git repository
based on its submodules.
"""

__version__ = '0.1.1'

# Import and expose public functions
from .main import (
    create_sbom
)

__all__ = [
    'create_sbom'
]