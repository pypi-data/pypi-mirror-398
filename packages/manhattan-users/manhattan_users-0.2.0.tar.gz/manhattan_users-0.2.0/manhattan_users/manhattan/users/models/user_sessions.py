import hashlib
from datetime import datetime

import flask
from manhattan.secure import random_token
from mongoframes import And, ASC, Frame, IndexModel, Q, SortBy
from ua_parser import user_agent_parser

__all__ = ['BaseUserSession']


class BaseUserSession(Frame):
    """
    The `BaseUserSession` collection implements device tracking for users
    in order to inform them when a new device is used and reduce the risk of
    session hijacking.

    By default the data we use to create a fingerprint is pretty broad,
    basically country (if available or IP address if not) and operating
    system. This data is return by the `discover_location` and
    `discover_platform` methods respectively. To tailor these to your needs
    simply overwrite these methods.

    NOTE: This is a **base** class and should not be used directly, instead
    define a new `UserSession` class for your project that inherits from this
    class.
    """

    _fields = {

        # The user the session relates to
        'user',

        # The location the session was created from
        'location',

        # The platform the session was created with
        'platform',

        # The date/time the user last signed in with this session
        'signed_in',

        # The date/time the user last used multi-factor authorization to
        # authorize the session.
        'mfa_authorized',

        # The date/time the user last access the app using this session
        'last_accessed',

        # A fingerprint created using the location and platform used to
        # uniquely identify the device used to create the session.
        'fingerprint_hash'
    }

    _recommended_indexes = [
        IndexModel([('user', ASC), ('fingerprint_hash', ASC)], unique=True)
    ]

    # Class methods

    @classmethod
    def discover_location(cls):
        """
        Return the location for the device (e.g country, town, lat/lng, IP
        address, etc.)
        """

        # Country
        if flask.request.headers.get('X-Country'):
            return flask.request.headers.get('X-Country')

        # IP address
        if flask.request.headers.get('X-Real-Ip', ''):
            return flask.request.headers.get('X-Real-Ip', '')

        return 'Unknown'

    @classmethod
    def discover_platform(cls):
        """
        Return the platform for the device (e.g the operating system, browser
        user agent, manufacturer, etc.)
        """
        user_agent = user_agent_parser.Parse(
            flask.request.headers.get('User-Agent', '')
        )
        return user_agent['os']['family'].lower()

    @classmethod
    def get_current_session(cls, user_id, projection=None):
        """Return the current session"""
        return cls.one(
            And(
                Q.user == user_id,
                Q.fingerprint_hash == cls.make_fingerprint()['hash']
            ),
            projection=projection
        )

    @classmethod
    def sign_in(cls, user_id):
        """
        Sign-in and return a user session and session status for the given
        user.

        We check to see if there is an an existing session for the device
        the user is signing in with or if this is a new device they
        haven't signed in with before.

        The session status returned determines if the session is a new (True)
        or existing (False) session, e.g:

            user_session, session_is_new = MyUserSessionClass.sign_in(...)
        """

        # Get a fingerprint for the session
        fingerprint = cls.make_fingerprint()

        # Check to see if a matching session already exists
        user_session = cls.one(
            And(
                Q.user == user_id,
                Q.fingerprint_hash == fingerprint['hash']
            )
        )

        new_session = False
        now = datetime.utcnow()
        if user_session:

            # Update the existing session with the new signed in date/time
            # and clear the Multi-factor authorization (MFA) authorized flag
            # to ensure MFA enabled user are required to authorize with MFA on
            # sign in.
            user_session.signed_in = now
            user_session.last_accessed = now
            user_session.mfa_authorized = None
            user_session.update(
                'signed_in',
                'last_accessed',
                'mfa_authorized'
            )

        else:

            # Create a new session (for a new device)
            user_session = cls(
                user=user_id,
                location=fingerprint['location'],
                platform=fingerprint['platform'],
                signed_in=now,
                last_accessed=now,
                mfa_authorized=None,
                fingerprint_hash=fingerprint['hash']
            )
            user_session.insert()
            new_session = True

            # Check if the maximum number of sessions (devices) for this user
            # has been exceeded.
            user_session_count = cls.count(Q.user == user_id)
            max_user_sessions = flask.current_app.config.get(
                'USER_MAX_SESSIONS',
                12
            )

            if user_session_count > max_user_sessions:

                # If there are more sessions (devices) than the maximum
                # allowed select the oldest session(s) based on their last
                # accessed date/time and remove them.
                remove_count = max_user_sessions - user_session_count
                sessions_to_remove = cls.many(
                    Q.user == user_id,
                    sort=SortBy(Q.last_accessed),
                    limit=remove_count
                )

                # Remove old sessions
                for session_to_remove in sessions_to_remove:
                    session_to_remove.delete()

        return (user_session, new_session)

    @classmethod
    def verify_access(cls, user_id, session_lifespan):
        """
        Verify a user is using a known session (device) and update the last
        accessed date/time for the user.

        The method returns True if a session was successfully found and
        updated, and False if the session (device) was not recognized for this
        user.
        """

        # Get a fingerprint for the session
        fingerprint = cls.make_fingerprint()

        # Attempt to update the last accessed value for the session
        cutoff = datetime.utcnow() - session_lifespan
        r = cls.get_collection().update_one(
            And(
                Q.user == user_id,
                Q.fingerprint_hash == fingerprint['hash'],
                Q.last_accessed >= cutoff
            ).to_dict(),
            {'$set': {'last_accessed': datetime.utcnow()}}
        )

        # Return True if we successfully updated a session, otherwise return
        # False.
        return r.matched_count > 0

    @classmethod
    def make_fingerprint(cls):
        """
        Generate a fingerprint for a session based on information about the
        user's device.
        """

        location = cls.discover_location()
        platform = cls.discover_platform()

        # Build the fingerprint
        h = hashlib.sha256()
        h.update(location.encode('utf-8'))
        h.update(platform.encode('utf-8'))

        return {
            'location': location,
            'platform': platform,
            'hash': h.hexdigest()
        }
