"""``resources`` module of ``graphql_server``.

It provides the different classes that are used to store a usable structure from a document
parsed by the ``GraphQLParser``.

"""

from abc import ABCMeta

from dataql.resources import WithParent


class Operation(WithParent, metaclass=ABCMeta):
    """An operation in a GraphQL document."""
    pass


class Query(Operation):
    """A query asking for data represented as ``dataql.resources.Resource``.

    A resource is a name and some filters.
    The name will be used as the entry point in the output, and the filters will be
    applied to a value (each filter applied to the result of the previous filter)

    Attributes
    ----------
    name : string
        The name of the query.
    resources : list
        List of instances of subclasses of ``dataql.resources.Resource`` .
        Each resource must be `root` and will be run independently.

    """

    __slots__ = Operation.__slots__ + (
        'name',
        'resources',
    )

    def __init__(self, name, resources):
        """Save attributes and set ``self`` as parent for the given resources.

        See the definition of the attributes on the class for more information about
        the arguments.

        Arguments
        ---------
        name : string
        resources : list

        """

        super().__init__()

        self.name = name
        self.resources = resources

        for resource in self.resources:
            resource.set_parent(self)

    def __repr__(self):
        """String representation of a ``Query`` instance.

        Returns
        -------
        str
            The string representation of the current ``Query`` instance.

        Example
        -------

        >>> from dataql.resources import Field
        >>> resources = [Field('name'), Field('homePlanet')]
        >>> Query('info', resources)
        <Query[info]>
          <Field[name] />
          <Field[homePlanet] />
        </Query[info]>

        """

        return (
            '<Query[%(name)s]>\n'
            '%(resources)s\n'
            '</Query[%(name)s]>'
        ) % {
            'name': self.name,
            'resources': '\n'.join(str(r) for r in self.resources)
        }
