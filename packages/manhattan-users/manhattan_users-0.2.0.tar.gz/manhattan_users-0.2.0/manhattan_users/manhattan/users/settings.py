from datetime import timedelta
from manhattan.utils.cache import MemoryCache


__all__ = [

    # Factories
    'createDefaultConfig',

    # Classes
    'DefaultConfig'
]


def createDefaultConfig(prefix='USER'):
    """Return a default config mixin class for the blueprint"""

    class DefaultConfig:
        """
        Default settings for the the user access / control set up.
        """

    # Invites

    # The time before an invite to a user to join the application expires
    setattr(
        DefaultConfig,
        f'{prefix}_INVITE_LIFESPAN',
        timedelta(days=14)
    )

    # Sessions

    # The maximum number of sessions (devices) a user can have registered at
    # any one time.
    setattr(DefaultConfig, f'{prefix}_MAX_SESSIONS', 12)

    # The time before a user's session expires (from the last time the user
    # accessed the application).
    setattr(
        DefaultConfig,
        f'{prefix}_SESSION_LIFESPAN',
        timedelta(days=14)
    )

    # Passwords

    # The number of iterations used when hashing a user's password. You might
    # want to configure this to a low number in local development environments
    # to ensure generating users from fixtures doesn't take too long. We don't
    # recommend less that 100,000 in production.
    #
    # NOTE: This setting is no longer used since we switched to using Argon2
    # for generating password hashes.
    #
    setattr(
        DefaultConfig,
        f'{prefix}_PASSWORD_HASH_ITERATIONS',
        100000
    )

    # The number of previous password that any new password will be checked
    # against to ensure that previous passwords are not reused.
    setattr(
        DefaultConfig,
        f'{prefix}_PREVIOUS_PASSWORDS',
        10
    )

    # The time before a reset password link for a user expires
    setattr(
        DefaultConfig,
        f'{prefix}_PASSWORD_RESET_LIFESPAN',
        timedelta(days=14)
    )

    # The set of rules for users when setting a password
    setattr(
        DefaultConfig,
        f'{prefix}_PASSWORD_RULES',
        dict(
            min_length=12,
            max_length=128,
            min_lower=1,
            min_upper=1,
            min_digits=1,
            min_specials=0
        )
    )


    # Failed sign-in attempts and lockouts

    # The cache used to store the number of failed attempts to sign-in for a
    # user identified (e.g an email).
    setattr(
        DefaultConfig,
        f'{prefix}_FAILED_SIGN_IN_CACHE',
        MemoryCache()
    )

    # The period of time a user is locked out for after too many failed
    # sign-in attempts.
    setattr(
        DefaultConfig,
        f'{prefix}_FAILED_SIGN_IN_LOCKOUT',
        timedelta(minutes=30)
    )

    # The window of time during which failed attempts are tallied before the
    # the tally is reset (the user can make `USER_MAX_FAILED_SIGN_IN_ATTEMPTS`
    # number of failed attempts within this window).
    setattr(
        DefaultConfig,
        f'{prefix}_FAILED_SIGN_IN_WINDOW',
        timedelta(minutes=10)
    )

    # The maximum number of times a user can fail to sign-in before being
    # locked out.
    setattr(
        DefaultConfig,
        f'{prefix}_MAX_FAILED_SIGN_IN_ATTEMPTS',
        3
    )


    # MFA (Multi-factor authorization)

    # The cache used to store the number of failed attempts to authorize using
    # multi-factor authentication.
    setattr(
        DefaultConfig,
        f'{prefix}_MFA_FAILED_AUTH_CACHE',
        MemoryCache()
    )

    # The duration a user is locked out of MFA after failing to authorize,
    # this should be a short period (less than 30 seconds) set to throttle
    # the number of attempts that can be made for the time-based one time
    # password (TOTP).
    setattr(
        DefaultConfig,
        f'{prefix}_MFA_FAILED_AUTH_LOCKOUT',
        timedelta(seconds=10)
    )

    # The MFA provisioning issuer
    setattr(DefaultConfig, f'{prefix}_MFA_ISSUER', 'NOT SET')

    # The number of times a user can incorrectly enter their time-based one
    # time password (TOPT) before we temporarily block their account from MFA.
    setattr(
        DefaultConfig,
        f'{prefix}_MFA_MAX_FAILED_AUTH_ATTEMPTS',
        3
    )

    # The length of MFA recovery codes generated for a user
    setattr(
        DefaultConfig,
        f'{prefix}_MFA_RECOVERY_CODE_LENGTH',
        12
    )

    # The number of MFA recovery codes to generate for a user
    setattr(
        DefaultConfig,
        f'{prefix}_MFA_RECOVERY_CODES',
        8
    )

    # Flag indicating if MFA is required for users
    setattr(DefaultConfig, f'{prefix}_MFA_REQUIRED', False)

    # The cache used to store scoped session tokens
    setattr(
        DefaultConfig,
        f'{prefix}_MFA_SCOPED_SESSION_CACHE',
        MemoryCache()
    )

    # The period of time a scoped authorized session lasts (we recommended
    # under 30 minutes).
    setattr(
        DefaultConfig,
        f'{prefix}_MFA_SCOPED_SESSION_LIFESPAN',
        timedelta(minutes=5)
    )

    return DefaultConfig


DefaultConfig = createDefaultConfig()
