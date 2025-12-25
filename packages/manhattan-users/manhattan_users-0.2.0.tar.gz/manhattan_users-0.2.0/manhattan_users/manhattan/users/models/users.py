from datetime import datetime
import hmac
import secrets

import flask
from manhattan.comparable import ComparableFrame
from manhattan.formatters.text import remove_accents
from manhattan.secure import (
    encrypt_password,
    hash_password,
    random_code,
    random_token,
    verify_password
)
from mongoframes import ASC, In, IndexModel, Q, SortBy
import pyotp

__all__ = ['BaseUser']


class BaseUser(ComparableFrame):
    """
    The `BaseUser` collection provides user access / control to manhattan
    manage applications.

    NOTE: This is a **base** class and should not be used directly, instead
    define a new `User` class for your project that inherits from this class.
    """

    _fields = {

        # The name of the user
        'first_name',
        'last_name',

        # A lowercase version of the user's full name (for searching)
        'full_name_lower',

        # The user's email address
        'email',

        # A lowercase version of the user's email (for lookup and indexing)
        'email_lower',

        # Flag indicating the date/time a user was last sent an invite to the
        # application.
        'invited',

        # A unique token assigned to the user when invited, the token is used
        # to identify the user (as a parameter) to accept their invite.
        'invite_token',

        # Flag indicating the date/time a user accepted their invite
        'invite_accepted',

        # A hashed version of the user's password used in combination with the
        # user's salt to verify a password when supplied by the user.
        'password_hash',

        # A random string used
        'password_salt',

        # A flag indicating the date/time a user requested a reset password
        # link.
        'password_reset_requested',

        # A unique token assigned to the user when they request a password
        # reset link, the token is used to identify the user (as a parameter)
        # to set a new password.
        'password_reset_token',

        # A list of previous password hashes (used to prevent users from
        # reusing previous passwords).
        'previous_password_hashes',

        # The session token identifying the user to the manage application
        # (the session token is generated when the user signs-in and stored
        # in the secure session cookie).
        'session_token',

        # MFA (Multi-factor authentication) fields

        # Flag indicating if MFA has been enabled for this user
        'mfa_enabled',

        # The secret used to generate and verify MFA time-based one time
        # passwords (TOTP) for this user. This key is registered with an
        # authentication device (such as a mobile phone app) and then used by
        # both the app and the device to generate a TOTP.
        'mfa_otp_secret',

        # A list of emergency one time passwords for the user created when
        # multi-factor authentication is enabled.
        #
        # NOTE: This is a legacy field and is no longer used. MFA recovery
        # codes are now stored as hashes in `mfa_recovery_codes_hashes`.
        #
        'mfa_recovery_codes',

        # A list of MFA recovery code hashes for the user.
        'mfa_recovery_code_hashes',

        # A list of masked (first 2 characters only) MFA recovery codes for
        # the user.
        'mfa_recovery_code_masks'
    }

    _private_fields = ComparableFrame._private_fields | {
        'email_lower',
        'full_name_lower',
        'invited',
        'invite_accepted',
        'invite_token',
        'mfa_recovery_codes',
        'mfa_recovery_code_hashes',
        'mfa_recovery_code_masks',
        'mfa_otp_secret',
        'password_hash',
        'password_reset_requested',
        'password_reset_token',
        'password_salt',
        'previous_password_hashes',
        'session_token'
    }

    _uncompared_fields = ComparableFrame._uncompared_fields | {
        'email_lower',
        'full_name_lower',
        'invited',
        'invite_accepted',
        'invite_token',
        'mfa_recovery_codes',
        'mfa_recovery_code_hashes',
        'mfa_recovery_code_masks',
        'mfa_otp_secret',
        'password_reset_requested',
        'password_reset_token',
        'password_salt',
        'previous_password_hashes',
        'session_token'
    }

    _recommended_indexes = [
        IndexModel([('email_lower', ASC)], unique=True),
        IndexModel([('invite_token', ASC)], unique=True, sparse=True),
        IndexModel(
            [('password_reset_token', ASC)],
            unique=True,
            sparse=True
            ),
        IndexModel([('session_token', ASC)], unique=True, sparse=True)
    ]

    def __str__(self):
        return f'{self.full_name} <{self.email}>'

    # Properties

    @property
    def current_session(self):
        return self.get_session_cls().get_current_session(self._id)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def last_accessed(self):
        user_session = self.get_session_cls().one(
            Q.user == self._id,
            sort=SortBy(Q.last_accessed.desc),
            projection={'last_accessed': True}
        )
        if user_session:
            return user_session.last_accessed

    @property
    def mfa_authorized(self):
        current_session = self.get_session_cls().get_current_session(
            self._id,
            projection={'mfa_authorized': True}
        )
        return current_session and current_session.mfa_authorized is not None

    @property
    def password(self):
        # The 'password' property however be used to retrieve a password only
        # to set one.
        return ''

    @password.setter
    def password(self, value):
        # Requests to set the password to a none value (e.g '', or None) will
        # be ignored.
        if value in [None, '']:
            return

        # Store the old password in the previous password hashes list
        self.add_previous_password_hash(self.password_hash)

        # Set the password
        self.password_salt = None
        self.password_hash = hash_password(value)

        # Set the user as having accepted an invite
        if not self.invited:
            self.invited = datetime.utcnow()
        self.invite_accepted = self.invited

    @property
    def password_is_legacy(self):
        return self.password_hash[0:1] == 'b'

    # Methods

    def add_previous_password_hash(self, password_hash):
        """Add the given password hash to the previous password hashes"""

        prefix = self.get_settings_prefix()
        max_previous_passwords \
                = flask.current_app.config[f'{prefix}_PREVIOUS_PASSWORDS']

        if max_previous_passwords < 1:
            return

        # If not yet defined default previous password hashes to an empty
        # list.
        self._document.setdefault('previous_password_hashes', [])

        # Add the password hash to the previous hashes
        self.previous_password_hashes.append(password_hash)

        # Cull the list to the maximum number defined for previous passwords
        del self.previous_password_hashes[:-max_previous_passwords]

    def generate_mfa_otp_provisioning_uri(self):
        """
        Generate a URI for provisioning multi-factor autentication for this
        user (this URL is used to generate a QR code that can be scanned by
        an authentication app such as Google authenticator).
        """
        prefix = self.get_settings_prefix()
        return pyotp.TOTP(self.mfa_otp_secret).provisioning_uri(
            self.email,
            issuer_name=current_app.config[f'{prefix}_MFA_ISSUER']
        )

    def generate_mfa_recovery_codes(self):
        """Generate a list of MFA recovery codes for the user"""

        prefix = self.get_settings_prefix()
        count = flask.current_app.config[f'{prefix}_MFA_RECOVERY_CODES']
        length = flask.current_app.config[f'{prefix}_MFA_RECOVERY_CODE_LENGTH']

        # Generate the new recovery codes
        codes = [random_code(length) for i in range(0, count)]
        hashes = [hash_password(c) for c in codes]
        masks = [c[0:2] for c in codes]

        return (codes, hashes, masks)

    def is_previous_password(self, password):
        """Check if the given password is a previous password"""

        if self.password_eq(password):

            # Check the new password doesn't match the current password
            return True

        if self.previous_password_hashes:

            # Check the new password hasn't been previously used by this user
            for previous_password_hash in self.previous_password_hashes:
                if verify_password(previous_password_hash, password):
                    return True

        return False

    def mfa_topt_eq(self, password):
        """Verify a time-based one time password for the user"""
        return pyotp.TOTP(self.mfa_otp_secret).verify(password)

    def password_eq(self, password):
        """Check if a password is equal to the user's password"""

        if self.password_is_legacy:

            prefix = self.get_settings_prefix()
            iterations = flask\
                .current_app\
                .config[f'{prefix}_PASSWORD_HASH_ITERATIONS']
            password_hash = encrypt_password(
                password,
                self.password_salt,
                iterations=iterations
            )

            return hmac.compare_digest(self.password_hash, password_hash)

        return verify_password(self.password_hash, password)

    def sign_in(self, force_new_token=False):
        """
        Sign a user in. The function returns the user session and a flag
        indicating if a new session (device) was created (True) or an existing
        known session (device) was used (False).
        """

        # Sign the user in against a session
        user_session, new_session = self.get_session_cls().sign_in(self._id)

        # Re-use an existing session token if available and not expired
        last_accessed = self.last_accessed
        if last_accessed:

            age = datetime.utcnow() - last_accessed
            prefix = self.get_settings_prefix()

            if age > flask.current_app.config[f'{prefix}_SESSION_LIFESPAN']:

                # The session token has expired remove it so a new one is
                # generated.
                self.session_token = None

        if not self.session_token or force_new_token:

            # No existing session token so create a new one
            self.session_token = random_token()

        self.update('session_token')

        return (user_session, new_session)

    # Class methods

    # Sessions management

    @classmethod
    def from_session(cls, projection=None):
        """Return a user from the current session token"""

        # Do we have session token?
        session_token = flask.session.get(cls.get_session_token_key())
        if not session_token:
            return None

        # Is the session token valid?
        user = cls.one(
            Q.session_token == session_token,
            projection=projection
        )
        if not user:
            return None

        # Verify the session/device
        prefix = cls.get_settings_prefix()
        lifespan = flask.current_app.config[f'{prefix}_SESSION_LIFESPAN']
        if not cls.get_session_cls().verify_access(user._id, lifespan):
            return None

        return user

    @classmethod
    def get_g_key(cls):
        """
        Return the key used to store an instance of the user against the
        global context (`flask.g`).
        """
        return 'user'

    @classmethod
    def get_session_cls(cls):
        """Return the session class that will be used by the user"""
        raise NotImplemented()

    @classmethod
    def get_session_token_key(cls):
        """
        Get the session token key used to store/retrieve the user's session
        token in the flask session.
        """
        return 'manage_session_token'

    @classmethod
    def get_settings_prefix(cls):
        """Return the prefix for settings properties for the user"""
        return 'USER'

    @classmethod
    def retrieve_mfa_recovery_codes(cls, retrieve_key):
        """Retrive and at the same time remove stowed mfa recovery codes"""
        prefix = cls.get_settings_prefix()
        cache = flask.current_app.config[f'{prefix}_MFA_SCOPED_SESSION_CACHE']
        cache_key = f'{prefix.lower()}_mfa_recovery_codes:{retrieve_key}'
        recovery_codes = cache.get(cache_key)
        if recovery_codes:
            cache.delete(cache_key)
        return recovery_codes

    @classmethod
    def stow_mfa_recovery_codes(cls, codes):
        """
        Stow the given mfa recovery codes temporarily so they can be retrieved
        to show once before being forgotten. The codes are stowed for a short
        period (60 seconds) as they should be relayed to the user as part of
        the next request/redirect.
        """
        prefix = cls.get_settings_prefix()
        cache = flask.current_app.config[f'{prefix}_MFA_SCOPED_SESSION_CACHE']
        retrieve_key = random_token()
        cache.set(
            f'{prefix.lower()}_mfa_recovery_codes:{retrieve_key}',
            codes,
            60
        )
        return retrieve_key

    # Failed sign-ins

    @classmethod
    def get_sign_in_attempt_key(cls, email):
        """
        Return a key that can be used to store and retrieve the number of
        failed sign-in attempts for a given email against this application.
        """
        server_name = flask.current_app.config['SERVER_NAME']
        return f'user_failed_login:{server_name}:{email.lower()}'

    @classmethod
    def is_locked_out(cls, email):
        """
        Return True if the given email is locked out (cannot be used to
        sign-in until the lock is removed or expires.)
        """
        config = flask.current_app.config
        prefix = cls.get_settings_prefix()
        cache = config[f'{prefix}_FAILED_SIGN_IN_CACHE']
        return (cache.get(cls.get_sign_in_attempt_key(email)) or 0) \
                >= config[f'{prefix}_MAX_FAILED_SIGN_IN_ATTEMPTS']

    # Static methods

    @staticmethod
    def _on_upsert(sender, frames):
        for frame in frames:

            if frame.email:

                # Store lowercase email
                frame.email_lower = frame.email.lower()

            if frame.first_name and frame.last_name:

                # Store lowercase full name
                frame.full_name_lower = frame.full_name.replace(',','').lower()
                frame.full_name_lower = remove_accents(frame.full_name_lower)

    @staticmethod
    def _on_delete(sender, frames):

        # Delete any associated user sessions
        user_cls = sender.get_session_cls()
        user_cls.delete_many(
            user_cls.many(In(Q.user, [f._id for f in frames]))
        )

