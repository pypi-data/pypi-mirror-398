"""
Handles any authentication-realted functionality.
Largely just checking if the required environment variables are set.
"""

import os


class Decorators:
    @staticmethod
    def check_env_vars(decorated):
        """
        Decorator to check if the required environment variables are set
        """

        def wrapper(*args, **kwargs):
            """
            Wrapper function
            """
            if "EZO_SUBDOMAIN" not in os.environ:
                raise Exception("EZO_SUBDOMAIN not found in environment variables.")
            if "EZO_TOKEN" not in os.environ:
                raise Exception("EZO_TOKEN not found in environment variables.")
            return decorated(*args, **kwargs)

        wrapper.__name__ = decorated.__name__
        return wrapper
