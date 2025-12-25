# -*- coding: utf-8 -*-
# Author: fallingmeteorite
"""
Initialize available methods
"""

import sys

# Prevent errors during multi-process initialization
try:
    from task_scheduling.client.rpc_client import RPCClient
    from task_scheduling.client.submit import submit_task
except KeyboardInterrupt:
    sys.exit(0)

__all__ = ['RPCClient', 'submit_task']
