import random
import sys
from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

import logfire
import requests
from tldextract import extract


def extract_domain(url: str) -> str:
    """
    Extract the domain from a url. We dedicate a function here to make sure we do it the same way everywhere.

    ex: https://www.inoopa.com/contact -> inoopa.com
    """
    # if http is not present, we can't parse the domain
    if not url.startswith("https://") and not url.startswith("http://"):
        url = f"https://{url}"
    return extract(url).top_domain_under_public_suffix


def extract_base_url(url: str) -> str:
    """Extract the base url from a url. Ex: https://www.inoopa.com/contact -> https://www.inoopa.com"""
    if not url.startswith("https://") and not url.startswith("http://"):
        url = f"https://{url}"
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


@lru_cache()
def get_all_latest_user_agents() -> list[str]:
    """
    Daily updated list of user agents

    :return: A list of user agents.
    """
    url = "https://jnrbsn.github.io/user-agents/user-agents.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()


def get_random_user_agent() -> str:
    """Get a random user agent. the user agents list is cached."""
    return random.choice(get_all_latest_user_agents())


def get_latest_user_agent(
    operating_system: Literal["macintosh", "windows", "x11"] = "macintosh",
    browser: Literal["version", "chrome", "firefox"] = "version",
) -> str:
    """
    General function to fetch the latest user agent for a given operating system and browser.

    :param operating_system: The operating system to search for. Default is macintosh, X11 is Linux.
    :param browser: The browser to search for. Version is the latest Safari.
    :return: The latest user agent for the given operating system and browser.
    """
    user_agents = get_all_latest_user_agents()
    for user_agent in user_agents:
        user_agent_lower = user_agent.lower()
        if operating_system.lower() in user_agent_lower and browser.lower() in user_agent_lower:
            return user_agent
    raise ValueError(f"No user-agent found for OS: {operating_system} and browser: {browser}")


def DEBUG_get_variable_memory_usage(name: str, limit: int = 5) -> None:
    """
    Log the memory usage of the 5 most memory-consuming variables. Usefull to identify memory leaks.

    :pram name: The name of the logger to use.
    :param limit: The number of variables to print. (Only log the top X)
    """
    # Access local and global variables
    variables = {**globals(), **locals()}  # Combine both scopes

    # Calculate sizes of all variables
    variable_sizes = []
    for var_name, var_value in variables.items():
        try:
            size = sys.getsizeof(var_value)
            variable_sizes.append((var_name, size))
        except Exception:
            variable_sizes.append((var_name, 0))

    # Sort variables by size and get the top ones
    top_variables = sorted(variable_sizes, key=lambda x: x[1], reverse=True)[:limit]

    # Print the results in KB
    logfire.debug(f"{'Variable Name':<30} {'Size (KB)':>15}")
    logfire.debug("-" * 50)
    for var_name, size in top_variables:
        size_kb = size / 1024  # Convert bytes to KB
        logfire.debug(f"{var_name:<30} {size_kb:>15.2f}")
