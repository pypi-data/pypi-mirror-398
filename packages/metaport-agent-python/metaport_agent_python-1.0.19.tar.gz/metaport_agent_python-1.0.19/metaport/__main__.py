#!/usr/bin/env python3
"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

Main entry point for executing metaport as a module.

This allows the package to be executed with:
    python -m metaport [arguments]
"""

import sys
from .metaport import main

if __name__ == '__main__':
    sys.exit(main())
