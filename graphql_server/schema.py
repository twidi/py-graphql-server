"""``schema`` module of ``graphql_server``.

A schema is the main entry point to solve graphql queries.

Simply create a schema, register classes with allowed attributes (which can also be
standalone functions), some entry points, and use the ``solve`` method to get the result value
from a main value and a resource.

"""


from dataql.solvers.registry import Registry


class Schema(Registry):
    """A special registry for graphql specifications."""

    def solve_query(self, value, query):
        """Solve a query that may hold many resources.

        Arguments
        ---------
        value : ?
            A value to be solved with the given query.
        query : .resources.Query
            An instance of ``Query`` to be solved with the given value.

        Returns
        -------
        dict
            A dict with one entry for each resource in the query, using the query's name as key
            and the solved result for this query as value.

        Example
        -------

        >>> from pprint import pprint
        >>> from dataql.solvers.registry import EntryPoints
        >>> from dataql.resources import Field, Filter, NamedArg, Object
        >>> from graphql_server.resources import Query

        # Create a class and some data
        >>> class Human:
        ...     by_id = {}
        ...     def __init__(self, id, name, homePlanet):
        ...         self.id, self.name, self.homePlanet = id, name, homePlanet
        ...         Human.by_id[self.id] = self
        >>> luke = Human(1000, 'luke', 'Tatooine')
        >>> leia = Human(1003, 'leia', 'Alderaan')

        # Our both sub queries
        >>> query1 = Object('luke',
        ...     filters=[Filter('human', args=[NamedArg('id', '=', 1000)])],
        ...     resources=[Field('name'), Field('homePlanet')]
        ... )
        >>> query2 = Object('leia',
        ...     filters=[Filter('human', args=[NamedArg('id', '=', 1003)])],
        ...     resources=[Field('name'), Field('homePlanet')]
        ... )

        # Create a schema
        >>> schema = Schema()
        >>> schema.register(Human, ('name', 'homePlanet'))
        >>> query_root = EntryPoints(schema, human=lambda id: Human.by_id[id])

        # Create and run the query
        >>> query = Query('default', [query1, query2])
        >>> pprint(schema.solve_query(query_root, query))
        {'leia': {'homePlanet': 'Alderaan', 'name': 'leia'},
         'luke': {'homePlanet': 'Tatooine', 'name': 'luke'}}
        """

        return {
            resource.name: self.solve_resource(value, resource)
            for resource in query.resources
        }
