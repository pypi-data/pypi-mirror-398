"""
List users.
"""

from manhattan.forms import BaseForm, fields
from manhattan.forms.utils import sort_by_choices
from manhattan.manage.views import factories, generic

__all__ = ['list_chains']


# Forms

class ListForm(BaseForm):

    page = fields.IntegerField('Page', default=1)

    q = fields.StringField('Search')

    sort_by = fields.SelectField(
        'Sort by',
        choices=sort_by_choices([
            ('full_name_lower', 'Name')
        ]),
        default='full_name_lower'
    )


# Chains
list_chains = generic.list.copy()

# Factory overrides
list_chains.set_link(
    factories.config(
        collation=None,
        form_cls=ListForm,
        hint=None,
        orphans=2,
        per_page=20,
        projection={
            'first_name': True,
            'last_name': True
        },
        search_fields=['full_name_lower']
    )
)
