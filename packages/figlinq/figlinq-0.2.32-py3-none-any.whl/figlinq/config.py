"""
Merges and prioritizes file/session config and credentials.

This is promoted to its own module to simplify imports.

"""

from __future__ import absolute_import

from figlinq import session, tools


def get_credentials():
    """Returns the credentials that will be sent to plotly."""
    # Start with credentials from the environment
    credentials = tools.get_credentials_env()

    # Override with credentials from the file
    file_credentials = tools.get_credentials_file()
    credentials.update({key: value for key, value in file_credentials.items() if value})

    # Finally, override with credentials from the session
    session_credentials = session.get_session_credentials()
    credentials.update(
        {
            key: value
            for key, value in session_credentials.items()
            if value is not False and value
        }
    )

    return credentials


def get_config():
    """Returns either module config or file config."""
    # Start with config from the environment
    config = tools.get_config_env()

    # Override with config from the file
    file_config = tools.get_config_file()
    config.update({key: value for key, value in file_config.items() if value})

    # Finally, override with config from the session
    session_config = session.get_session_config()
    config.update(
        {
            key: value
            for key, value in session_config.items()
            if value is not False and value
        }
    )

    return config
