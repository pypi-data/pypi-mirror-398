import sys

from .ziti_router_auto_enroll import main

def cli() -> None:
    """
    Command Line Interface (CLI) entry point for the application.
    
    This function retrieves command-line arguments and passes them to the main function
    of the ziti_router_auto_enroll module for processing.
    """
    args = sys.argv[1:]
    main(args)