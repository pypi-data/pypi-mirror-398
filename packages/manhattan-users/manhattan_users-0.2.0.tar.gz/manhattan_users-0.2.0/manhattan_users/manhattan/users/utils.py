import flask
from manhattan.forms import validators

__all__ = [

    # Factories
    'apply_password_rules',

    # Validators
    'password_validator'
]


# Factories

def apply_password_rules():
    """
    Apply the configured password rules to the form so that any
    `password_validator` will use them.
    """

    def apply_password_rules(state):
        user_cls = state.manage_config.frame_cls
        prefix = user_cls.get_settings_prefix()

        # Store the password rules against the form
        state.form._password_rules = flask\
            .current_app\
            .config[f'{prefix}_PASSWORD_RULES']

    return apply_password_rules

# Validators

def password_validator(form, field):
    """
    Wrapper for the password validator so that rules for passwords can be
    defined in the applications settings (config). See `password_validator`.
    """
    return validators.Password(**form._password_rules)(form, field)
