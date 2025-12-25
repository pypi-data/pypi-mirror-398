"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

Metaport Python Agent Package

A Python implementation of the Metaport agent for generating Software Bill of Materials (SBOM)
documents and reporting application metadata to Metaport instances.

This package supports requirements.txt, Pipfile and Poetry-based Python projects, maintaining
compatibility with Python 3.10+.
"""

__version__ = "1.0.19"
__author__ = "Dcentrica Solutions 2025"

# Import the main function to make it available at package level
from .metaport import main

# Make main available when importing the package
__all__ = ['main']
