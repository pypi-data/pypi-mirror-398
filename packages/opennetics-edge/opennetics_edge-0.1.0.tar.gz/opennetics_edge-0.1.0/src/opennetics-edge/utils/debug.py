
# utils/errors.py

#- Imports -----------------------------------------------------------------------------------------

import os
import sys
import inspect
from enum import Enum
from typing import Any, Optional

from colorama import init, Fore


#- Private Defines ---------------------------------------------------------------------------------

# Initialise colorama
init()

class AlertLevel(Enum):
    ALERT = "alert"
    WARNING = "warning"
    ERROR = "error"


#- Public Methods ----------------------------------------------------------------------------------

# Print where this procedure was called, with optional message.
def alert(prompt: Any = "", backtrack: int = 1, level: AlertLevel = AlertLevel.ALERT) -> None:
    #========================================
    # get caller info
    #========================================

    # Immediate caller frame.
    # 0 is this function, 1 is what called it.
    # backtrack = 2, is the code block that called the function that called alert()

    stack = inspect.stack()
    if len(stack) > (backtrack+1):
        caller = stack[backtrack]
        caller_file = os.path.abspath(caller.filename)
        caller_line = caller.lineno

        # Attempt to find the project root by looking for common repo/project markers.
        def _find_project_root(start_path: str) -> Optional[str]:
            cur = os.path.dirname(start_path)

            while True:
                candidate = os.path.join(cur, "opennetics-edge")
                if os.path.exists(candidate):
                    return cur

                parent = os.path.dirname(cur)
                if parent == cur:
                    return None

                cur = parent

        project_root = _find_project_root(caller_file)

        if project_root:
            rel_path = os.path.relpath(caller_file, project_root)
        else:
            # fallback to current working directory if no project root found
            try:
                rel_path = os.path.relpath(caller_file, os.getcwd())
            except Exception:
                rel_path = caller_file

        caller_info: str = Fore.YELLOW + f"{rel_path}:{caller_line}" + Fore.RESET

    else:
        caller_info: str = Fore.YELLOW + "<unknown>" + Fore.RESET

    #========================================
    # print alert
    #========================================
    print(Fore.RED + f"[{level}] {caller_info} {prompt}", file=sys.stderr)

