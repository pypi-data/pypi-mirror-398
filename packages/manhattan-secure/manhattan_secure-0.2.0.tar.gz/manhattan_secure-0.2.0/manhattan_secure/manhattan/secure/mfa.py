"""
Utils for implementing multi-factor authentication.
"""

from datetime import timedelta
import secrets

__all__ = [
    'create_scoped_session',
    'delete_scoped_session',
    'verify_scoped_session'
]


def create_scoped_session(cache, scope, expire_after=None):
    """
    Create a scoped session (a session which has been authenticated to perform
    the given scope of work.

    The scope should describe the actor and the action, for example:

        (user, request_full_path)

    The function returns a session token that along with the scope can be used
    to verify the session.
    """

    # Generate the token
    session_token = secrets.token_urlsafe(32)

    # Store the token
    if isinstance(expire_after, timedelta):
        expire_after = int(expire_after.total_seconds())

    cache.set(f'mfa_scoped_session:{session_token}', scope, expire_after)

    return session_token

def delete_scoped_session(cache, session_token):
    """Clear a scoped session"""
    cache.delete(f'mfa_scoped_session:{session_token}')

def verify_scoped_session(cache, session_token, scope):
    """Verify a scoped session"""
    return cache.get(f'mfa_scoped_session:{session_token}') == scope
