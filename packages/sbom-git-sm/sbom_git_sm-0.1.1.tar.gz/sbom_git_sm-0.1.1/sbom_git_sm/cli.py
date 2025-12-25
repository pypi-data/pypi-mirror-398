#!/usr/bin/env python3
"""
Command-line interface for sbom-git-sm.

Copyright (c) 2025 Janosch Meyer (janosch.code@proton.me)
This project is licensed under the MIT License - see the LICENSE file for details.
This project was created with the assistance of artificial intelligence.

This module provides the command-line interface for the sbom-git-sm tool.
"""

import sys
import json
import argparse
from pathlib import Path

# --- magic so that "from .main ..." auch als direktes Skript klappt ---
if __name__ == "__main__" and (not __package__):
    # Pfad so setzen, dass das Parent-Verzeichnis importierbar ist
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "sbom_git_sm"
# ----------------------------------------------------------------------

from .main import create_sbom


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description='Create a Software Bill of Materials (SBOM) from a git repository based on its submodules.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Basic arguments
    parser.add_argument('repo', 
                        help='Path to the git repository', 
                        nargs='?', 
                        default='.')
    
    parser.add_argument('--output', '-o',
                        help='Path to save the SBOM to. If not provided, the SBOM will be printed to stdout.')
    
    parser.add_argument('--version', '-v',
                        action='store_true', 
                        help='Show version information and exit')
    
    # Format options
    format_group = parser.add_argument_group('Format Options')
    format_group.add_argument('--format', 
                             choices=['cyclonedx'], 
                             default='cyclonedx',
                             help='Output format for the SBOM')
    
    format_group.add_argument('--spec-version',
                             choices=['1.4'], 
                             default='1.4',
                             help='CycloneDX specification version (currently only 1.4 is supported)')
    
    format_group.add_argument('--pretty', '-p',
                             action='store_true',
                             help='Pretty-print the JSON output')
                             
    format_group.add_argument('--component-type',
                             choices=['application', 'library', 'framework', 'container', 'operating-system', 'device', 'firmware', 'file'],
                             help='Override the default component type for the main repository (default: "application")')
    
    format_group.add_argument('--nested-components', '-n',
                             action='store_true',
                             help='Use nested components instead of dependencies structure')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show version information if requested
    if args.version:
        from . import __version__
        print(f"sbom-git-sm version {__version__}")
        return 0
    
    # Process repository
    try:
        # Resolve paths
        repo_path = Path(args.repo).resolve()
        output_path = Path(args.output).resolve() if args.output else None
        
        # Create SBOM
        sbom = create_sbom(repo_path, output_path, component_type=args.component_type, use_nested_components=args.nested_components)
        
        # If no output path was provided, print to stdout
        if not output_path:
            if args.pretty:
                print(json.dumps(sbom, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(sbom, ensure_ascii=False))
        
        return 0
    except Exception as e:
        print(f"Error creating SBOM: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())