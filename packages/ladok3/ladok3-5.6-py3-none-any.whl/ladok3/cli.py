#!/bin/env python3
"""A command-line interface for LADOK 3"""

import appdirs
import argcomplete, argparse
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass
import json
import keyring
import ladok3
import os
import pickle
import re
import sys
import traceback
import weblogin
import weblogin.ladok
import weblogin.seamlessaccess as sa

import ladok3.data
import ladok3.report
import ladok3.student

dirs = appdirs.AppDirs("ladok", "dbosk@kth.se")


def err(rc, msg):
    """Print error message to stderr and exit with given return code.

    Args:
        rc (int): Return code to exit with.
        msg (str): Error message to display.
    """
    print(f"{sys.argv[0]}: error: {msg}", file=sys.stderr)
    sys.exit(rc)


def warn(msg):
    """Print warning message to stderr.

    Args:
        msg (str): Warning message to display.
    """
    print(f"{sys.argv[0]}: {msg}", file=sys.stderr)


def store_ladok_session(ls, credentials):
    """Store a LadokSession object to disk with encryption.

    Saves the session object as an encrypted pickle file in the user's cache directory.
    The credentials are used to derive an encryption key for security.

    Args:
        ls (LadokSession): The session object to store.
        credentials (tuple): Tuple of (institution, vars) used for key derivation.

    Raises:
        ValueError: If credentials are missing or invalid.
    """
    if not os.path.isdir(dirs.user_cache_dir):
        os.makedirs(dirs.user_cache_dir)

    file_path = dirs.user_cache_dir + "/LadokSession"

    pickled_ls = pickle.dumps(ls)
    if not credentials or len(credentials) < 2:
        raise ValueError(f"Missing credentials, see `ladok login -h`.")

    if isinstance(credentials, dict):
        try:
            salt = credentials["username"]
            passwd = credentials["password"]
        except KeyError:
            credentials = list(credentials.values())
            salt = credentials[0]
            passwd = credentials[1]
    else:
        salt = credentials[0]
        passwd = credentials[1]

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.encode("utf-8"),
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(passwd.encode("utf-8")))

    fernet_protocol = Fernet(key)
    encrypted_ls = fernet_protocol.encrypt(pickled_ls)

    with open(file_path, "wb") as file:
        file.write(encrypted_ls)


def restore_ladok_session(credentials):
    """Restore a LadokSession object from disk.

    Attempts to load and decrypt a previously stored session object. Returns None
    if no cached session exists or decryption fails.

    Args:
        credentials (tuple): Tuple of (institution, vars) used for key derivation.

    Returns:
        LadokSession or None: The restored session object, or None if unavailable.
    """
    file_path = dirs.user_cache_dir + "/LadokSession"

    if os.path.isfile(file_path):
        with open(file_path, "rb") as file:
            encrypted_ls = file.read()
            if not credentials or len(credentials) < 2:
                raise ValueError(f"Missing credentials, see `ladok login -h`.")

            if isinstance(credentials, dict):
                try:
                    salt = credentials["username"]
                    passwd = credentials["password"]
                except KeyError:
                    credentials = list(credentials.values())
                    salt = credentials[0]
                    passwd = credentials[1]
            else:
                salt = credentials[0]
                passwd = credentials[1]

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode("utf-8"),
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(passwd.encode("utf-8")))

            fernet_protocol = Fernet(key)
            try:
                pickled_ls = fernet_protocol.decrypt(encrypted_ls)
            except Exception as err:
                warn(f"cache was corrupted, cannot decrypt: {err}")
                pickled_ls = None
            if pickled_ls:
                return pickle.loads(pickled_ls)

    return None


def update_credentials_in_keyring(ls, args):
    print(
        """
This login process is exactly the same as when you log in using
the web browser. You need three things:

  1) The name of your institution, so that it can be uniquely identified.

  2) Your username at your institution. This is sometimes a username (such as 
     `dbosk`) or an email address (such as `dbosk@kth.se`). However, 
     occasionally, you type in the username in the web browser and it is 
     actually complemented: for instance, at KTH, I type in my username `dbosk` 
     and then on the password screen, I can see it has been complemented to 
     `dbosk@ug.kth.se`. Be observant about that.

  3) Your password at your institution.

"""
    )
    while True:
        institution = input("Institution: ")
        matches = sa.find_entity_data_by_name(institution)

        if not matches:
            print("No match, try again.")
            continue

        if len(matches) > 1:
            print("More than one match. Which one?")
            for match in matches:
                print(f"- {match['title']}")
            continue

        match = matches[0]

        print(
            f"Matched uniquely, using {match['title']}\n"
            f"            with domain {match['domain']} and\n"
            f"      unique identifier {match['id']}."
        )

        institution = match["id"]
        break

    vars = {
        "username": input("Institution username: "),
        "password": getpass.getpass("Institution password: [input is hidden] "),
    }
    while True:
        temp_ls = ladok3.LadokSession(institution, vars=vars)

        try:
            temp_ls.user_info_JSON()
        except weblogin.AuthenticationError as err:
            adjust_vars(vars, err.variables)
        else:
            break

    try:
        keyring.set_password("ladok3", "institution", institution)
        keyring.set_password("ladok3", "vars", ";".join(vars.keys()))
        for key, value in vars.items():
            keyring.set_password("ladok3", key, value)
    except Exception as err:
        globals()["err"](
            -1,
            f"You don't seem to have a working keyring. "
            f"Use one of the other methods, see "
            f"`ladok login -h`: {err}.",
        )

    clear_cache(ls, args)


def adjust_vars(vars, form_variables):
    print(
        """
Some part of the authentication went wrong. Either you typed your username or 
password incorrectly, or your institution requires some adjustments. We'll 
guide you through it.

We will show you some variable names and values and give you the opportunity to 
change the values according to the name of the variable. For instance, we 
assume that the institution call the variable for the username `username`, but 
they might call it `användarnamn` instead. You'll have to figure this out.

Remember, the problem might also be that you entered your username as 'dbosk', 
when it should be 'dbosk@ug.kth.se' --- or something similar. Use your 
institution's login page to figure this out.

Note: Your password will be visible on screen during this process.
"""
    )
    input("\nPress return to continue.\n")

    for key, value in form_variables.items():
        key = key.casefold()
        new_val = input(f"{key} = '{value}' " f"[enter new value, blank to keep] ")
        if new_val:
            vars[key] = new_val


def load_credentials(filename="config.json"):
    """
    Loads credentials from environment or file named filename.
    Returns the tuple (instituation, credential dictionary) that
    can be passed to `LadokSession(instiution, credential dictionary)`.
    """

    try:
        institution = os.environ["LADOK_INST"]
    except:
        institution = "KTH Royal Institute of Technology"
    try:
        vars = {
            "username": os.environ["LADOK_USER"],
            "password": os.environ["LADOK_PASS"],
        }
        if institution and vars["username"] and vars["password"]:
            return institution, vars
    except:
        pass
    try:
        vars_keys = os.environ["LADOK_VARS"]

        vars = {}
        for key in vars_keys.split(":"):
            try:
                value = os.environ[key]
                if value:
                    vars[key] = value
            except KeyError:
                warn(f"Variable {key} not set, ignoring.")

        if institution and vars:
            return institution, vars
    except:
        pass
    try:
        with open(filename) as conf_file:
            config = json.load(conf_file)

        institution = config.pop("institution", "KTH Royal Institute of Technology")
        return institution, config
    except:
        pass
    try:
        institution = keyring.get_password("ladok3", "institution")
        vars_keys = keyring.get_password("ladok3", "vars")

        vars = {}
        for key in vars_keys.split(";"):
            value = keyring.get_password("ladok3", key)
            if value:
                vars[key] = value

        if institution and vars:
            return institution, vars
    except:
        pass
    try:
        institution = "KTH Royal Institute of Technology"
        username = keyring.get_password("ladok3", "username")
        password = keyring.get_password("ladok3", "password")
        if username and password:
            return institution, {"username": username, "password": password}
    except:
        pass

    return None, None


def clear_cache(ls, args):
    """Clear the cached LADOK session data.

    Removes the stored encrypted session file from the user's cache directory.
    Silently ignores if the file doesn't exist.

    Args:
        ls (LadokSession): The LADOK session (unused but required by interface).
        args: Command line arguments (unused).
    """
    try:
        os.remove(dirs.user_cache_dir + "/LadokSession")
    except FileNotFoundError as err:
        pass

    sys.exit(0)


def main():
    """Run the command-line interface for the ladok command"""
    argp = argparse.ArgumentParser(
        description="This is a CLI-ification of LADOK3's web GUI.",
        epilog="Web: https://github.com/dbosk/ladok3",
    )
    argp.add_argument(
        "-f",
        "--config-file",
        default=f"{dirs.user_config_dir}/config.json",
        help="Path to configuration file "
        f"(default: {dirs.user_config_dir}/config.json) "
        "or set LADOK_USER and LADOK_PASS environment variables.",
    )
    subp = argp.add_subparsers(title="commands", dest="command", required=True)
    login_parser = subp.add_parser(
        "login",
        help="Manage login credentials",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"""
  Manages the user's LADOK login credentials. There are three ways to supply the 
  login credentials, in order of priority:

  1) Through the environment: Just set the environment variables

     a) LADOK_INST, the name of the institution, e.g. KTH Royal Institute of
        Technology;

     b) LADOK_VARS, a colon-separated list of environment variables, similarly to
        what's done in `ladok login` --- most don't need this, but can rather set 
        LADOK_USER (the username, e.g. dbosk@ug.kth.se) and LADOK_PASS (the 
        password) instead.

  2) Through the configuration file: Just write

        {{
          "institution": "the name of the university"
          "username": "the actual username",
          "password": "the actual password"
        }}

     to the file {dirs.user_config_dir}/config.json (default, or use the -f 
     option). (The keys 'username' and 'password' can be renamed to correspond to 
     the necessary values if the university login system uses other names.)

  3) Through the system keyring: Just run `ladok login` and you'll be asked to
     enter the credentials and they will be stored in the keyring. Note that for 
     this to work on the WSL platform (and possibly on Windows), you need to 
     install the `keyrings.alt` package: `python3 -m pip install keyrings.alt`.

  The keyring is the most secure. However, sometimes one want to try different 
  credentials, so the environment should override the keyring. Also, on WSL the 
  keyring might require you to enter a password in the terminal---this is very 
  inconvenient in scripts. However, when logging in, we first try to store the 
  credentials in the keyring.

  """,
    )

    login_parser.set_defaults(func=update_credentials_in_keyring)
    cache_parser = subp.add_parser(
        "cache", help="Manage cache", description="Manages the cache of LADOK data"
    )
    cache_subp = cache_parser.add_subparsers(
        title="subcommands", dest="subcommand", required=True
    )
    cache_clear = cache_subp.add_parser(
        "clear", help="Clear the cache", description="Clears everything from the cache"
    )
    cache_clear.set_defaults(func=clear_cache)
    ladok3.data.add_command_options(subp)
    ladok3.report.add_command_options(subp)
    ladok3.student.add_command_options(subp)
    argcomplete.autocomplete(argp)
    args = argp.parse_args()
    LADOK_INST, LADOK_VARS = load_credentials(args.config_file)
    try:
        ls = restore_ladok_session(LADOK_VARS)
    except ValueError as error:
        err(-1, f"Couldn't restore LADOK session: {error}")
    if not ls:
        ls = ladok3.LadokSession(LADOK_INST, vars=LADOK_VARS)
    if "func" in args:
        args.func(ls, args)
    store_ladok_session(ls, LADOK_VARS)


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        err(-1, e)
