import json
import os
import sys
import tempfile
from pathlib import Path
import datetime as dt
from subprocess import call

import requests
import tomli
import humanize


CONFIG_DIRNAME = "lolbin"
CONFIG_FILENAME = "config.toml"
DEFAULT_DOMAIN = "api.omg.lol"

# TODO: Add type hints to all functions


def get_config():
    """
    Retrieve the config file from the user's home directory.
    Example: ~/.config/lolbin/config.toml

    Returns:
        dict: The config file as a dict.
    """
    config_path = (
        Path(
            os.environ["XDG_CONFIG_HOME"]
            if "XDG_CONFIG_HOME" in os.environ
            else (Path(os.environ["HOME"]) / ".config")
        )
        / CONFIG_DIRNAME
        / CONFIG_FILENAME
    )
    if not config_path.exists():
        print("Config file doesn't exists.", file=sys.stderr)
        print("Writting default config file.")

    with open(config_path, "rb") as f:
        return tomli.load(f)


def create_paste(paste, content, username, token, public):
    """
    Create a paste on omg.lol.

    Args:
        paste (str): The paste name (id). An string of characters (ASCII only without spaces).
        content (str): The content of the paste.
        username (str): The username of the user.
        token (str): The authentification token. You can get it from <https://home.omg.lol/account>
        public (bool): True to make the paste listed.
    """
    headers = {"Authorization": f"Bearer {token}"}
    data_send = {"title": paste, "content": content, "listed": "no"}
    if public:
        data_send["listed"] = "true"  # NOTE: It's a not documented feature
    response = requests.post(
        f"https://{DEFAULT_DOMAIN}/address/{username}/pastebin/",
        headers=headers,
        data=json.dumps(data_send),
    )
    data = response.json()

    if data["request"]["status_code"] != 200:
        print(f"Error status code {data['request']['status_code']}.", file=sys.stderr)
        if "response" in data:
            if "message" in data["response"]:
                print(data["response"]["message"], file=sys.stderr)

        if data["request"]["status_code"] >= 400:
            sys.exit(1)
        else:
            return

    if "response" in data:
        if "message" in data["response"]:
            print(data["response"]["message"])
        else:
            print("No message returned")
    else:
        print("No reponse returned")


def list_paste(username, token, public):
    """
    List all pastes for a user.

    Args:
        username (str): The username of the user.
        token (str): The authentification token. You can get it from <https://home.omg.lol/account>
        public (bool): Whether to list public pastes or not.
    """
    headers = {} if public else {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"https://{DEFAULT_DOMAIN}/address/{username}/pastebin", headers=headers
    )
    data = response.json()

    if data["request"]["status_code"] != 200:
        print(f"Error status code {data['request']['status_code']}.", file=sys.stderr)
        if "response" in data:
            if "message" in data["response"]:
                print(data["response"]["message"], file=sys.stderr)

        if data["request"]["status_code"] >= 400:
            sys.exit(1)
        else:
            return

    if "response" in data:
        if "message" in data["response"]:
            print(data["response"]["message"])
        else:
            print("No message returned")
    else:
        print("No reponse returned")

    for paste in data["response"]["pastebin"]:
        modified_on_date = dt.datetime.fromtimestamp(paste["modified_on"])
        modified_on_string = humanize.naturaltime(dt.datetime.now() - modified_on_date)
        print(f" - {paste['title']} ({modified_on_string})")


def get_paste(paste, username, token):
    """
    Get a paste.

    Returns:
        String: The paste content or None if an error occured.
        Boolean: True if the paste is public, False otherwise.
    """
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"https://{DEFAULT_DOMAIN}/address/{username}/pastebin/{paste}", headers=headers
    )
    data = response.json()

    if data["request"]["status_code"] != 200:
        return None, None

    if (
        "response" in data
        and "paste" in data["response"]
        and "content" in data["response"]["paste"]
    ):
        return data["response"]["paste"]["content"], "listed" in data["response"][
            "paste"
        ]

    return None, None


def show_paste(paste, username, token):
    """
    Show a paste.

    Args:
        paste (str): The paste name (id). An string of characters (ASCII only without spaces).
        username (str): The username of the user.
        token (str): The authentification token. You can get it from <https://home.omg.lol/account>
    """
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"https://{DEFAULT_DOMAIN}/address/{username}/pastebin/{paste}", headers=headers
    )
    data = response.json()

    if data["request"]["status_code"] != 200:
        print(f"Error status code {data['request']['status_code']}.", file=sys.stderr)

        if "response" in data:
            if "message" in data["response"]:
                print(f"Message: {data['response']['message']}")

        if data["request"]["status_code"] >= 400:
            sys.exit(1)
        else:
            return

    if (
        "response" in data
        and "paste" in data["response"]
        and "content" in data["response"]["paste"]
    ):
        print(data["response"]["paste"]["content"], end="")
    else:
        print("No content found for the paste.")


def delete_paste(paste, username, token):
    """
    Delete a paste.

    Args:
        paste (str): The paste name (id). An string of characters (ASCII only without spaces).
        username (str): The username of the user.
        token (str): The authentification token. You can get it from <https://home.omg.lol/account>
    """
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(
        f"https://{DEFAULT_DOMAIN}/address/{username}/pastebin/{paste}", headers=headers
    )
    data = response.json()

    if data["request"]["status_code"] != 200:
        print(f"Error status code {data['request']['status_code']}.", file=sys.stderr)
        if "response" in data:
            if "message" in data["response"]:
                print(data["response"]["message"], file=sys.stderr)
        if data["request"]["status_code"] >= 400:
            sys.exit(1)
        else:
            return

    if "response" in data:
        if "message" in data["response"]:
            print(data["response"]["message"])
        else:
            print("No message returned but the paste was succesfully deleted")
    else:
        print("No reponse found but the paste was succesfully deleted")


def debug_action(action, paste_name, content, username, token, public):
    """
    Print debug information about the action being performed.

    Args:
        action (str): The action being performed.
        paste_name (str): The name of the paste.
        content (str): The content of the paste.
        username (str): The username of the user.
        token (str): The authentification token. You can get it from <https://home.omg.lol/account>
        public (bool): Whether the paste is public or not.
    """
    print(f"Debug: Action = {action}")
    print(f"Paste Name: {paste_name}")
    print(f"Username: {username}")
    print(f"Bearer Token: {token}")
    print(f"Public: {public}")
    if content is not None:
        print(
            f"Content: {content[:100]}..."
        )  # Print first 100 characters of the content


def edit_paste(paste, username, token):
    """
    Edit a paste: It opens it in your default editor, then updates it on paste.lol.

    Args:
        paste (str): The paste name (id). An string of characters (ASCII only without spaces).
        username (str): The username of the user.
        token (str): The authentification token. You can get it from <https://home.omg.lol/account>
    """
    # TODO: Implement this

    editor = os.environ.get("EDITOR", "vim")  # that easy!
    content, is_listed = get_paste(paste, username, token)

    with tempfile.NamedTemporaryFile(prefix=f"lolbin-{paste}", suffix=".tmp") as tf:
        tf.write(content.encode("utf-8"))
        tf.flush()
        call([editor, tf.name])
        with open(tf.name, "r") as f:
            new_content = f.read()
            create_paste(
                paste=paste,
                content=new_content,
                username=username,
                token=token,
                public=is_listed,
            )


def help_message():
    print("Usage:")
    print("lolbin [--debug] [--help | -h]")
    print("lolbin [--debug] [--list | -l]")
    print("lolbin [--debug] [--paste | -p] title [--file <file>]")
    print("lolbin [--debug] [--show | -s] title")
    print("lolbin [--debug] [--delete | -d] title")


def app():
    action = None
    paste_name = None
    content = None
    is_debug = False
    is_public = False
    config = get_config()

    # TODO: Add an edit action
    #       The edit action will write the paste to /tmp/{id-bin}, open it with EDITOR then push it back to paste.lol (and delete the temporary file).

    to_pass = 0
    for i, arg in enumerate(sys.argv[1:]):
        if to_pass:
            to_pass -= 1

            continue

        match arg:
            case "--help" | "-h":
                if action is None:
                    action = "help"
                else:
                    print("Multiple actions specified")
                    sys.exit(1)

            case "--list" | "-l":
                if action is None:
                    action = "list"
                else:
                    print("Multiple actions specified")
                    sys.exit(1)

            case "--listed" | "-L" | "--public" | "-P":
                is_public = True

            case "--paste" | "-p":
                if action is None:
                    action = "paste"
                else:
                    print("Multiple actions specified")
                    sys.exit(1)

            case "--file" | "-f":
                if action is None:
                    action = "paste"
                    with open(sys.argv[i + 2]) as f:
                        content = f.read()
                    to_pass = 1
                else:
                    print("Multiple actions specified")
                    sys.exit(1)

            case "--show" | "-s":
                if action is None:
                    action = "show"

            case "--delete" | "-d":
                if action is None:
                    action = "delete"
                else:
                    print("Multiple actions specified")
                    sys.exit(1)

            case "--edit" | "-e":
                if action is None:
                    action = "edit"
                else:
                    print("Multiple actions specified")
                    sys.exit(1)

            case "--debug":
                is_debug = True

            case name:
                if paste_name is None:
                    paste_name = name
                else:
                    print(
                        f"Ambiguous paste name. Aborting. {name} or {paste_name}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

    if not sys.stdin.isatty():
        if content is None:
            content = sys.stdin.read()
            if action is None:
                action = "paste"
            elif action != "paste":
                print(
                    f"Content was send to lolbin but the action {action} doesn't use it.",
                    file=sys.stderr,
                )
        else:
            print("Ambiguous paste content source. Aborting.", file=sys.stderr)
            sys.exit(1)

    if action is None:
        if paste_name is None:
            action = "list"
        else:
            action = "show"

    if is_debug:
        debug_action(
            action,
            paste_name,
            content,
            config["username"],
            config["bearer_token"],
            is_public,
        )
        return

    match action:
        case "list":
            list_paste(config["username"], config["bearer_token"], is_public)
        case "paste":
            if paste_name is None:
                print("You must specify a paste name to paste.", file=sys.stderr)
                sys.exit(1)
            create_paste(
                paste_name,
                content,
                config["username"],
                config["bearer_token"],
                is_public,
            )
        case "delete":
            if paste_name is None:
                print("You must specify a paste name to delete.", file=sys.stderr)
                sys.exit(1)
            delete_paste(paste_name, config["username"], config["bearer_token"])
        case "show":
            if paste_name is None:
                print("You must specify a paste name to show.", file=sys.stderr)
                sys.exit(1)
            show_paste(paste_name, config["username"], config["bearer_token"])
        case "help":
            help_message()

        case "edit":
            if paste_name is None:
                print("You must specify a paste name to edit.", file=sys.stderr)
                sys.exit(1)
            edit_paste(paste_name, config["username"], config["bearer_token"])
        case _:
            print(f"Unknown action: {action}", file=sys.stderr)
            sys.exit(1)
