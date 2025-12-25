"""
Delete a user.
"""

from manhattan.manage.views import generic

__all__ = ['delete_chains']


# Chains
delete_chains = generic.delete.copy()

