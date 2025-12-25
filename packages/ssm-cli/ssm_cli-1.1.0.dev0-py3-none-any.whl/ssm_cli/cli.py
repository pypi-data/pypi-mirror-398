import sys
from typing import List
from ssm_cli.xdg import get_log_file
from ssm_cli.aws import AWSAuthError, AWSAccessDeniedError
from ssm_cli.ui import console
from ssm_cli.logging import setup_logging, set_log_level
from rich.markup import escape
from ssm_cli.app import app

import logging
logger = logging.getLogger(__name__)

def cli(argv:List[str]=None) -> int:
    """ Entry point for ssm-cli, we use this wrapper to put all the aws errors in one place. Otherwise we would need to exit in the aws class and avoid finally statements being hit. """
    if argv is None:
        argv = sys.argv[1:]
    
    setup_logging()

    # Manually set the log level now, so we get accurate logging during startup
    for i, arg in enumerate(argv):
        if arg == '--log-level':
            set_log_level(argv[i+1])
        if arg.startswith('--log-level='):
            set_log_level(arg.split('=')[1])

    logger.info(f"ssm cli called")
    logger.debug(f"sys.argv {sys.argv}")

    try:
        app(argv)
        logger.info(f"Command completed successfully")
        return 0
    except AWSAuthError as e:
        console.print(f"AWS Authentication error: {e}", style="red")
        return 1
    except AWSAccessDeniedError as e:
        logger.error(f"access denied: {e}")
        console.print(f"Access denied, see README for details on required permissions", style="bold red")
        console.print(escape(str(e.__cause__)), style="grey50")
        return 1
    except Exception as e:
        logger.error(f"Unhandled exception")
        log_path = str(get_log_file())
        console.print(f"Unhandled exception, check [link=file://{log_path}]{log_path}[/link] for more information", style="red")
        console.print(f"Error: {e}", style="red bold")
        logger.exception(e, stack_info=True, stacklevel=20)
        return 1
    
