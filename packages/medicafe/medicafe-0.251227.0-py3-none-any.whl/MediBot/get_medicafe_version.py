#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MediCafe Version Detection Script
Compatible with Python 3.4.4 and Windows XP
"""

import sys
import pkg_resources

def get_medicafe_version():
    """Get the installed MediCafe package version."""
    try:
        version = pkg_resources.get_distribution('medicafe').version
        print('MediCafe=={}'.format(version))
        return 0
    except pkg_resources.DistributionNotFound:
        print('MediCafe package not found', file=sys.stderr)
        return 1
    except Exception as e:
        print('Error detecting MediCafe version: {}'.format(e), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(get_medicafe_version()) 