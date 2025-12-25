"""
Authentication utilities and decorators for ServerAPI.
"""

import time
import threading
from functools import wraps
from typing import Callable

from flask import request, jsonify

from SharedData.API.constants import AUTH_FAILURE_SLEEP_SECONDS
from SharedData.Users import get_user_table

# Thread-safe user cache
user_by_token: dict = {}
user_by_token_lock = threading.Lock()


def check_permissions(reqpath: list, permissions: dict, method: str) -> bool:
    """
    Check if a given request path and HTTP method are permitted based on a nested permissions dictionary.
    
    This function iteratively traverses the permissions tree according to the segments in reqpath.
    It supports wildcard segments ('*') and checks if the specified method is allowed at the final node.
    
    Parameters:
        reqpath (list[str]): A list of path segments representing the requested resource path.
        permissions (dict): A nested dictionary representing permission rules.
        method (str): The HTTP method (e.g., 'GET', 'POST') to check permission for.
    
    Returns:
        bool: True if the method is permitted for the given path, False otherwise.
    """
    node = permissions
    for segment in reqpath:
        if segment in node:
            node = node[segment]
        elif '*' in node:
            node = node['*']
        else:
            return False
        # If leaf is not dict (wildcard or method list)
        if not isinstance(node, dict):
            if '*' in node or (isinstance(node, list) and method in node):
                return True
            return False
    # At the end, check at current node
    if '*' in node:
        return True
    if method in node:
        return True
    return False


def authenticate(request, shdata) -> bool:
    """
    Authenticate an incoming HTTP request by validating a token and verifying permissions.
    
    Parameters:
        request (flask.Request): The incoming HTTP request object.
        shdata: SharedData instance for accessing user table.
    
    Returns:
        bool: True if authenticated and authorized; False otherwise.
    """
    global user_by_token
    
    try:
        user_table = get_user_table(shdata)

        email = request.args.get('email')  # Optional
        if email:
            userdata = user_table.loc[email]
            if len(userdata) == 0:
                time.sleep(AUTH_FAILURE_SLEEP_SECONDS)
                return False
            userdata = userdata[0]
        else:
            token = request.args.get('token')  # Not Optional
            if not token:
                token = request.headers.get('X-Custom-Authorization')
            if not token:
                token = request.headers.get('x-api-key')
            
            if token is None:
                time.sleep(AUTH_FAILURE_SLEEP_SECONDS)
                return False
            
            if token not in user_by_token:
                # Load all users into cache
                users_list = user_table.get_dict_list(user_table[:])
                with user_by_token_lock:
                    for user in users_list:
                        user_by_token[user['token']] = user

            userdata = user_by_token.get(token)
            if userdata is None:
                time.sleep(AUTH_FAILURE_SLEEP_SECONDS)
                return False
        
        reqpath = str(request.path).split('/')[1:]
        user = request.args.get('user', 'master')
        if user:
            reqpath = [user] + reqpath

        tablesubfolder = request.args.get('tablesubfolder')
        if tablesubfolder:
            reqpath = reqpath + [tablesubfolder]

        permissions = userdata['permissions']
        method = str(request.method).upper()
        
        return check_permissions(reqpath, permissions, method)
    except Exception:
        return False


def require_auth(shdata):
    """
    Decorator factory that creates an authentication decorator.
    
    Parameters:
        shdata: SharedData instance for authentication.
    
    Returns:
        Decorator function that enforces authentication.
    
    Usage:
        @require_auth(shdata)
        def my_route():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not authenticate(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401
            return f(*args, **kwargs)
        return decorated_function
    return decorator
