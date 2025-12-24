#!/usr/bin/env python
"""
Command line utilities for ViQi/BisQue API.
"""

import argparse
import logging
import os
import sys
from configparser import RawConfigParser

import urllib3

from .vqclass import VQSession

# Default configuration paths
if os.name == "nt":
    CONFIG_PATHS = [
        "~/config/viqi/profiles",
        "~/viqi/config",
        "~/bisque/config",  # Deprecated
    ]
else:
    CONFIG_PATHS = [
        "~/.config/viqi/profiles",
        "~/.viqi/config",
        "~/.bisque/config",  # Deprecated
    ]

log = logging.getLogger(__name__)


def viqi_argument_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    """
    Constructs or augments an ArgumentParser with standard ViQi/BisQue options.
    """
    if parser is None:
        parser = argparse.ArgumentParser()

    # Configuration
    parser.add_argument("-c", "--config", help="Path to config file", default=None)
    parser.add_argument("--profile", help="Profile to use from config", default="default")

    # Outputs
    parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Report actions without making changes", default=False
    )
    parser.add_argument("-d", "--debug", nargs="?", const="DEBUG", help="Set debug level: debug, info, warn, error")
    parser.add_argument("--debug-file", help="Output filename for debug messages", default=None)
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output", default=False)

    # Credentials
    parser.add_argument("--authtoken", help="Auth/Mex token", default=None)
    parser.add_argument("-a", "--credentials", help="Login creds in format id:secret", default=None)
    parser.add_argument("--host", help="BisQue server URL")
    parser.add_argument("--user", help="Username")
    parser.add_argument("--password", help="Password")
    parser.add_argument("--alias", help="Login as alias (requires admin credentials)")

    # Security
    parser.add_argument("--verify", help="Verify HTTPS credentials", default=True)
    parser.add_argument("--retries", help="Number of connection retries", type=int, default=10)

    return parser


# Alias for backward compatibility
bisque_argument_parser = viqi_argument_parser


def viqi_config(
    parser: argparse.ArgumentParser | None = None, args: list[str] | None = None, write_config: bool = False
) -> argparse.Namespace:
    """
    Parse arguments and manage ViQI configuration.
    Resolves configuration from files, arguments, and interactive input if needed.
    """
    if parser is None:
        parser = viqi_argument_parser()

    # Parse initial args
    pargs = parser.parse_args(args=args)
    # Store parser reference for error reporting later
    setattr(pargs, "_parser", parser)

    # 1. Locate Config File
    if pargs.config is None:
        for confd in CONFIG_PATHS:
            expanded_path = os.path.expanduser(confd)
            if os.path.exists(expanded_path):
                pargs.config = expanded_path
                break

    # 2. Read Profile from Config
    # Only if host/user/pass are not already fully provided via CLI
    if not (pargs.host and pargs.user and pargs.password) and pargs.config:
        config_path = os.path.expanduser(pargs.config)
        if os.path.exists(config_path):
            config = RawConfigParser()
            config.read(config_path)
            try:
                if pargs.profile in config:
                    profile_data = config[pargs.profile]
                    # Only overwrite if not provided on CLI
                    if not pargs.host:
                        pargs.host = profile_data.get("host")
                    if not pargs.user:
                        pargs.user = profile_data.get("user")
                    if not pargs.password:
                        pargs.password = profile_data.get("password")
                    if not pargs.alias:
                        pargs.alias = profile_data.get("alias", None)
            except KeyError:
                if not pargs.quiet:
                    print(f"No or incomplete profile named {pargs.profile}")

    # 3. Handle Credentials formats
    if pargs.credentials and not (pargs.user or pargs.password):
        if ":" in pargs.credentials:
            pargs.user, pargs.password = pargs.credentials.split(":", 1)
        else:
            print("Warning: Credentials must be in user:password format")

    # 4. Interactive Configuration (if missing host/auth)
    if pargs.authtoken and not pargs.host:
        parser.error("Authtoken requires --host")

    # If we still lack connection details and aren't using the default profile
    # (Checking !default avoids prompting for simple scripts unless explicit)
    missing_creds = not (pargs.host and (pargs.authtoken or (pargs.user and pargs.password)))
    if missing_creds and pargs.profile != "default":
        print(f"Please configure how to connect to bisque with profile {pargs.profile}")

        if not write_config:
            parser.error(f"Must provide login credentias, or unkown profile {pargs.profile} in {pargs.config}")

        # Interactive setup
        if pargs.config is None:
            pargs.config = os.path.expanduser(CONFIG_PATHS[0])

        pargs.host = input(f"BisQue URL [{pargs.host or ''}] ") or pargs.host
        pargs.user = input(f"username[{pargs.user or ''}] ") or pargs.user
        pargs.password = input(f"password[{pargs.password or ''}]: ") or pargs.password

        if input(f"Write profile {pargs.profile} to {pargs.config} [y/N]").lower() == "y":
            config_file = os.path.expanduser(pargs.config)
            os.makedirs(os.path.dirname(config_file), exist_ok=True)

            config = RawConfigParser()
            if os.path.exists(config_file):
                config.read(config_file)

            profile_data = {
                "host": (pargs.host or "").strip().rstrip("/") + "/",
                "user": (pargs.user or "").strip(),
                "password": (pargs.password or "").strip(),
            }
            # Filter out empty values for saving
            config[pargs.profile] = {k: v for k, v in profile_data.items() if v}

            with open(config_file, "w") as conf:
                config.write(conf)
                print(f"profile {pargs.profile} has been saved to {pargs.config}")
        else:
            print("No profile created")

    return pargs


# Alias for backward compatibility
bisque_config = viqi_config


def _parse_session_args(
    largs: tuple,
    parser: argparse.ArgumentParser | None,
    args: argparse.Namespace | list[str] | None,
    kwargs: dict,
) -> argparse.Namespace:
    """
    Helper to parse arguments for viqi_session without creating a session.
    Useful for testing.
    """
    if isinstance(args, argparse.Namespace):
        return args

    # Use provided parser or create default
    if parser is None:
        parser = viqi_argument_parser()

    cmd_args_for_parsing: list[str] = []

    # 1. Add positional args (*largs) if present
    if largs:
        cmd_args_for_parsing.extend(list(largs))

    # 2. Map kwargs to parser flags
    # Build a map of dest -> Action for introspection
    dest_map = {a.dest: a for a in parser._actions if a.dest is not argparse.SUPPRESS}

    for k, v in kwargs.items():
        if k not in dest_map:
            log.warning("Argument '%s' is not a valid parameter for this parser. Ignoring.", k)
            continue

        action = dest_map[k]
        # Find the best option string (prefer long --opt over short -o)
        option_string = next((opt for opt in action.option_strings if opt.startswith("--")), None)
        if not option_string and action.option_strings:
            option_string = action.option_strings[0]

        if not option_string:
            # Positional argument?
            cmd_args_for_parsing.append(str(v))
            continue

        if v is None:
            continue

        # Handle boolean flags (nargs=0 usually means store_true/store_false)
        if action.nargs == 0:
            if isinstance(v, bool):
                if v:
                    cmd_args_for_parsing.append(option_string)
            else:
                # Fallback if someone passed non-bool to a flag
                cmd_args_for_parsing.append(option_string)
        else:
            cmd_args_for_parsing.append(option_string)
            cmd_args_for_parsing.append(str(v))

    # 3. Add 'args' if it's a list of strings, or default to sys.argv[1:] if None
    if args is None:
        cmd_args_for_parsing.extend(sys.argv[1:])
    elif isinstance(args, list):
        cmd_args_for_parsing.extend(args)

    return viqi_config(parser=parser, args=cmd_args_for_parsing)


def viqi_session(
    *largs,
    parser: argparse.ArgumentParser | None = None,
    args: argparse.Namespace | list[str] | None = None,
    root_logger: logging.Logger | None = None,
    **kwargs,
) -> VQSession | None:
    """
    Get a session for command line tools using arguments and ~/.config/viqi/profiles files.

    Args:
        largs : command line like args
        parser: a configured ArgumentParser
        args: List of strings or an already parsed Namespace.
              If None, defaults to sys.argv[1:].
        root_logger: logger to use

    Returns:
        initialized session

    Examples:
        Create a file ~/.config/viqi/profiles with content::

           [testing-admin]
           host=https://testing.viqiai.dev
           user=admin
           password=secret

           [science-user2]
           host=https://science.viqiai.cloud
           user=myuser2
           password=mysecret2


        Usage Examples::

            >>> from vqapi import bisque_session
            >>> session = viqi_session()  # Read the command line args
            >>> session = viqi_session(args=["--user", "admin", "--password=secret"])
            >>> session = viqi_session(user="admin", password="secret")
            >>> session = viqi_session(profile="testing-admin")
            >>> session = viqi_session(authtoken="atoken")
            >>
            # Old style
            >>> session = bisque_session(args=["--profile=science-user2"])
    """

    pargs = _parse_session_args(largs, parser, args, kwargs)

    # 3. Configure Logging
    if pargs.debug:
        logging.captureWarnings(True)
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warn": logging.WARNING,
            "warning": logging.WARNING,
            "error": logging.ERROR,
        }
        level = level_map.get(str(pargs.debug).lower(), logging.DEBUG)

        if root_logger is None:
            # Only configure basicConfig if we are owning the logger setup
            if pargs.debug_file:
                logging.basicConfig(filename=pargs.debug_file, filemode="w", level=level)
            else:
                logging.basicConfig(level=level)
            root_logger = logging.getLogger("vqapi")

        root_logger.setLevel(level)

    # 4. Initialize Session
    if not pargs.host:
        pargs._parser.error("Unknown connection host")
        return None

    session = VQSession()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session.c.verify = pargs.verify

    if not pargs.quiet:
        # Mask password for printing
        pwd_len = len(pargs.password) if pargs.password else 0
        print(f"connecting {pargs.host} with {pargs.user} and {'*' * pwd_len}")

    if pargs.user and pargs.password:
        session = session.init_local(
            bisque_root=pargs.host,
            user=pargs.user,
            pwd=pargs.password,
            create_mex=False,
            as_user=pargs.alias,
            retries=pargs.retries,
        )
    elif pargs.authtoken:
        session = session.init_mex(bisque_root=pargs.host, token=pargs.authtoken, retries=pargs.retries)
    else:
        pargs._parser.error("Please provide user/password or authtoken")

    if session.user is None:
        if not pargs.quiet:
            print(f"Could not create session with host={pargs.host} user={pargs.user}. Check your config")
        return session

    if not pargs.quiet and session.user:
        print("Session for  ", pargs.host, " for user ", session.user, " created")

    delattr(pargs, "_parser")  # No longer needed
    session.parse_args = pargs
    session.server_version = "viqi1"
    return session


# Alias for backward compatibility
bisque_session = viqi_session
