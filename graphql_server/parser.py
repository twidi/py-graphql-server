"""``parser`` module of ``graphql_server``.

It provides the ``GraphQLParser`` that is able to parse the GraphQL language and
convert it in dataql "resources".

"""

from dataql.parsers.base import BaseParser, rule
from dataql.parsers.mixins import NamedArgsParserMixin
from dataql.resources import Field, Filter, Object

from graphql_server.resources import Query

class ArgumentsMixin(NamedArgsParserMixin):
    """Overwrite the default mixin to only accept colons as name/value separator

    Example
    -------

    >>> ArgumentsMixin(r'foo: 1').data
    [foo=1]
    >>> ArgumentsMixin(r'foo  : 1, bar:"BAZ"').data
    [foo=1, bar="BAZ"]
    >>> ArgumentsMixin(r'foo:TRUE, bar :"BAZ",quz:null').data
    [foo=True, bar="BAZ", quz=None]

    """

    @rule('COL')
    def visit_args_oper(self, node, children):
        """Operator to separate argument name and value.

        Here, accepts only colon.

        Arguments
        ---------
        node : parsimonious.nodes.Node.
        _ (children) : list, unused

        -------
        str
            The '=' character.

        Example
        -------

        >>> ArgumentsMixin(':', default_rule='ARGS_OPER').data
        '='
        >>> ArgumentsMixin('=', default_rule='ARGS_OPER').data   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        dataql.parsers.exceptions.ParserError:...

        """

        return '='


class GraphQLParser(ArgumentsMixin, BaseParser):
    """A parser of the GraphQL language.

    Example
    -------

    >>> GraphQLParser(r'''{
    ...     human(id: 1000) {
    ...         id
    ...         name
    ...         friends {
    ...             name
    ...         }
    ...     }
    ... }
    ... ''').data
    <Query[default]>
      <Object[human] .human(id=1000)>
        <Field[id] />
        <Field[name] />
        <Object[friends]>
          <Field[name] />
        </Object[friends]>
      </Object[human]>
    </Query[default]>

    """

    base_grammar = r"""
        # At least one white space
        SPACE     =  ~"\s+"
        # Commas are optional in GraphQL, so a comma or at least one space
        COM = (WS "," WS) / SPACE
    """

    default_rule = 'ROOT'

    @rule('WS UNNAMED_QUERY WS')
    def visit_root(self, _, children):
        """The root of a GraphQL query.

        It can currently only handle one simple unnamed query.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``WS`` (optional whitespace): ``None``
            - 1: for ``UNNAMED_QUERY``: 1 list of instances of subclasses of
                ``dataql.resources.Resource``, with ``is_root`` set to ``True``.
            - 1: for ``WS`` (optional whitespace): ``None``

        Returns
        -------
        .resources.Query
            A ``Query`` resource with "default" as name.

        Example
        -------

        >>> GraphQLParser(r'''
        ... {
        ...     hero {
        ...         name
        ...     }
        ... }
        ... ''').data
        <Query[default]>
          <Object[hero]>
            <Field[name] />
          </Object[hero]>
        </Query[default]>

        >>> GraphQLParser(r'''
        ... {
        ...     luke: human(id: "1000") {
        ...         name
        ...         homePlanet
        ...     }
        ...     leia: human(id: "1003") {
        ...         name
        ...         homePlanet
        ...     }
        ... }
        ... ''').data
        <Query[default]>
          <Object[luke] .human(id="1000")>
            <Field[name] />
            <Field[homePlanet] />
          </Object[luke]>
          <Object[leia] .human(id="1003")>
            <Field[name] />
            <Field[homePlanet] />
          </Object[leia]>
        </Query[default]>

        """

        return children[1]

    @rule('SELECTION_SET')
    def visit_unnamed_query(self, _, children):
        """A unnamed query is just a selection set.

        The specs implies that there could be many sub-requests in a single request.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``SELECTION_SET``: a list of instance of a subclass of
            ``dataql.resources.Resource``.

        Returns
        -------
        .resources.Query
            A ``Query`` resource with "default" as name.

        Example
        -------

        >>> GraphQLParser(r'''{
        ...     hero {
        ...         name
        ...     }
        ... }''', default_rule='UNNAMED_QUERY').data
        <Query[default]>
          <Object[hero]>
            <Field[name] />
          </Object[hero]>
        </Query[default]>

        >>> GraphQLParser(r'''{
        ...     luke: human(id: "1000") {
        ...         name
        ...         homePlanet
        ...     }
        ...     leia: human(id: "1003") {
        ...         name
        ...         homePlanet
        ...     }
        ... }''', default_rule='UNNAMED_QUERY').data
        <Query[default]>
          <Object[luke] .human(id="1000")>
            <Field[name] />
            <Field[homePlanet] />
          </Object[luke]>
          <Object[leia] .human(id="1003")>
            <Field[name] />
            <Field[homePlanet] />
          </Object[leia]>
        </Query[default]>

        """

        resources = children[0]
        for resource in resources:
            resource.is_root = True

        return Query('default', resources)

    @rule('CUR_O SELECTIONS CUR_C')
    def visit_selection_set(self, _, children):
        """A selection set is a list of selections surrounded by curly brackets.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``CUR_O`` (opening curly): ``None``
            - 1: for ``SELECTIONS``: a list of instance of a subclass of
                 ``dataql.resources.Resource``.
            - 2: for ``CUR_C``, (closing curly): ``None``

        Returns
        -------
        list(dataql.resources.Resource)
            A list of instances of subclasses of ``dataql.resources.Resource``.

        Example
        -------

        >>> GraphQLParser(r'''{
        ...     name
        ... }''', default_rule='SELECTION_SET').data
        [<Field[name] />]

        >>> GraphQLParser(r'''{
        ...     name
        ...     homePlanet
        ... }''', default_rule='SELECTION_SET').data
        [<Field[name] />, <Field[homePlanet] />]

        >>> GraphQLParser(r'''{
        ...     name
        ...     homePlanet
        ...     friends { name }
        ... }''', default_rule='SELECTION_SET').data
        [<Field[name] />, <Field[homePlanet] />, <Object[friends]>
          <Field[name] />
        </Object[friends]>]

        """

        return children[1]

    @rule('SELECTION_SET?')
    def visit_optional_selection_set(self, _, children):
        """A selection set may be optional in some case.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            -0: for ``SELECTIONS_SET?``: a list of instance of a subclass of
                ``dataql.resources.Resource``, or None if nothing.

        Returns
        -------
        list(dataql.resources.Resource), or None
            A list of instances of subclasses of ``dataql.resources.Resource`` if anything,
            ``None`` otherwise.

        Example
        -------

        >>> GraphQLParser('', default_rule='OPTIONAL_SELECTION_SET').data

        >>> GraphQLParser(r'''{
        ...     name
        ... }''', default_rule='OPTIONAL_SELECTION_SET').data
        [<Field[name] />]

        >>> GraphQLParser(r'''{
        ...     name,
        ...     homePlanet
        ... }''', default_rule='OPTIONAL_SELECTION_SET').data
        [<Field[name] />, <Field[homePlanet] />]

        >>> GraphQLParser(r'''{
        ...     name
        ...     homePlanet
        ...     friends { name }
        ... }''', default_rule='OPTIONAL_SELECTION_SET').data
        [<Field[name] />, <Field[homePlanet] />, <Object[friends]>
          <Field[name] />
        </Object[friends]>]

        """

        return children[0] if children else None

    @rule('SELECTION+')
    def visit_selections(self, _, children):
        """A list of selections.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``SELECTIONS+``: a list of instance of a subclass of
                 ``dataql.resources.Resource``.

        Returns
        -------
        list(dataql.resources.Resource)
            A list of instances of subclasses of ``dataql.resources.Resource``.

        Example
        -------

        >>> GraphQLParser(r'''
        ...     name
        ... ''', default_rule='SELECTIONS').data
        [<Field[name] />]

        >>> GraphQLParser(r'''
        ...     name
        ...     homePlanet
        ... ''', default_rule='SELECTIONS').data
        [<Field[name] />, <Field[homePlanet] />]

        >>> GraphQLParser(r'''
        ...     name
        ...     homePlanet
        ...     friends { name }
        ... ''', default_rule='SELECTIONS').data
        [<Field[name] />, <Field[homePlanet] />, <Object[friends]>
          <Field[name] />
        </Object[friends]>]

        """

        return children

    @rule('FIELD')
    def visit_selection(self, _, children):
        """A selection can currently only be a field (no fragments yet)

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``FIELD``: an instance of a subclass of ``dataql.resources.Resource``.

        Returns
        -------
        dataql.resources.Resource
            An instance of a subclass of ``dataql.resources.Resource``.

        Example
        -------

        >>> GraphQLParser(r'''
        ...     name
        ... ''', default_rule='SELECTION').data
        <Field[name] />

        >>> GraphQLParser(r'''
        ...     friends { name }
        ... ''', default_rule='SELECTION').data
        <Object[friends]>
          <Field[name] />
        </Object[friends]>

        """

        return children[0]

    @rule('WS OPTIONAL_FIELD_ALIAS FIELD_NAME WS OPTIONAL_FIELD_ARGUMENTS '
          'OPTIONAL_SELECTION_SET COM?')
    def visit_field(self, _, children):
        """A field is the main component of a query. Could be a simple field or a parent field.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``WS`` (optional whitespace): ``None``
            - 1: for ``OPTIONAL_FIELD_ALIAS``: optional string to use at the result name of the
                 field
            - 2: for ``FIELD_NAME``: string defining the field to retrieve from the parent resource
            - 3: for ``WS`` (optional whitespace): ``None``
            - 4: for ``OPTIONAL_FIELD_ARGUMENTS``: optional list of ``dataql.resources.NamedArg``
                 to use as named arguments when calling the field.
            - 5: for ``OPTIONAL_SELECTION_SET``: optional selection set (list of instances of
                 subclasses of ``resources.Resource``) if the field is a parent field
            - 6: for ``COM?`` (coma or space): ``None``

        Returns
        -------
        dataql.resources.Field or dataql.resources.Object
            Instance of ``Object`` if it's a parent field, of ``Field`` otherwise.

        Example
        -------

        >>> GraphQLParser(r'''
        ...     name
        ... ''', default_rule='FIELD').data
        <Field[name] />

        >>> GraphQLParser(r'''
        ...     name,
        ... ''', default_rule='FIELD').data
        <Field[name] />

        >>> GraphQLParser(r'''
        ...     luke: human,
        ... ''', default_rule='FIELD').data
        <Field[luke] .human />

        >>> GraphQLParser(r'''
        ...     human(id: 1000)
        ... ''', default_rule='FIELD').data
        <Field[human] .human(id=1000) />

        >>> GraphQLParser(r'''
        ...     luke: human(id: 1000) {
        ...         name
        ...     }
        ... ''', default_rule='FIELD').data
        <Object[luke] .human(id=1000)>
          <Field[name] />
        </Object[luke]>

        """

        name = children[1] or children[2]
        filter_ = Filter(name=children[2], args=children[4])
        if children[5]:
            return Object(name=name, filters=[filter_], resources=children[5])
        else:
            return Field(name=name, filters=[filter_])

    @rule('IDENT WS COL WS')
    def visit_field_alias(self, _, children):
        """An alias to a field, to use as a key name in the result.

        Arguments
        ---------
            - 0: for ``IDENT``: the string to use as alias
            - 1: for ``WS`` (optional whitespace): ``None``
            - 2: for ``COL`` (colon): ``None``
            - 3: for ``WS`` (optional whitespace): ``None``

        Returns
        -------
        string
            The string to use as alias.

        Example
        -------

        >>> GraphQLParser('luke:', default_rule='FIELD_ALIAS').data
        'luke'
        >>> GraphQLParser('luke :', default_rule='FIELD_ALIAS').data
        'luke'
        >>> GraphQLParser('luke: ', default_rule='FIELD_ALIAS').data
        'luke'
        >>> GraphQLParser('luke : ', default_rule='FIELD_ALIAS').data
        'luke'

        """

        return children[0]

    @rule('FIELD_ALIAS?')
    def visit_optional_field_alias(self, _, children):
        """An optional alias to a field, to use as a key name in the result.

        Arguments
        ---------
            - 0: for ``FIELD_ALIAS?``: the optional string to use as alias

        Returns
        -------
        string or None
            The string to use as alias if defined, ``None`` otherwise.

        Example
        -------

        >>> GraphQLParser('', default_rule='OPTIONAL_FIELD_ALIAS').data

        >>> GraphQLParser('luke:', default_rule='OPTIONAL_FIELD_ALIAS').data
        'luke'

        """

        return children[0] if children else None

    @rule('IDENT')
    def visit_field_name(self, _, children):
        """The name of the field to retrieve for the parent resource.

        Arguments
        ---------
            - 0: for ``IDENT``: the name of the field

        Returns
        -------
        string
            The string to use.

        Example
        -------

        >>> GraphQLParser('luke', default_rule='FIELD_NAME').data
        'luke'
        >>> GraphQLParser('__type', default_rule='FIELD_NAME').data
        '__type'

        """

        return children[0]

    @rule('PAR_O NAMED_ARGS PAR_C')
    def visit_field_arguments(self, _, children):
        """The arguments of a field, surrounded by parentheses.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``PAR_O`` (opening parenthesis): ``None``.
            - 1: for ``NAMED_ARGS`` list of instances of ``dataql.resources.NamedArg``.
            - 2: for ``PAR_C`` (closing parenthesis): ``None``.

        Returns
        -------
        list(dataql.resources.NamedArg)
            List of  instances of ``dataql.resources.NamedArg``.

        Example
        -------

        >>> GraphQLParser(r'(id:1000)', default_rule='FIELD_ARGUMENTS').data
        [id=1000]
        >>> GraphQLParser(r'(name: "Luke", homePlanet: "Tatooine")',
        ... default_rule='FIELD_ARGUMENTS').data
        [name="Luke", homePlanet="Tatooine"]

        """

        return children[1]

    @rule('FIELD_ARGUMENTS?')
    def visit_optional_field_arguments(self, _, children):
        """The optional arguments of a field, surrounded by parentheses.

        Arguments
        ---------
        _ (node) : parsimonious.nodes.Node.
        children : list
            - 0: for ``FIELD_ARGUMENTS`` list of instances of ``dataql.resources.NamedArg``.

        Returns
        -------
        list(dataql.resources.NamedArg) or None
            List of  instances of ``dataql.resources.NamedArg`` if any, or ``None``.

        Example
        -------

        >>> GraphQLParser(r'', default_rule='OPTIONAL_FIELD_ARGUMENTS').data

        >>> GraphQLParser(r'(id:1000)', default_rule='OPTIONAL_FIELD_ARGUMENTS').data
        [id=1000]
        >>> GraphQLParser(r'(name: "Luke", homePlanet: "Tatooine")',
        ... default_rule='OPTIONAL_FIELD_ARGUMENTS').data
        [name="Luke", homePlanet="Tatooine"]

        """

        return children[0] if children else None
