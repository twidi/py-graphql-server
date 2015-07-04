# py-graphql-server

Python server for [GraphQL](http://facebook.github.io/graphql/), based on [py-dataql](https://github.com/twidi/py-dataql)

Current status: nothing yet ;) See plan below.

## Plan

![And they have a plan](http://i.imgur.com/JvpKysP.png)

Here is the plan I think I will follow to have a complete (read "following the whole specifications") GraphQL server.

I may change my plan while working on it but, for now...

### Queries

- parser for simple "SelectionSet" using "resources" from `dataql`
- specific registry and new resources (for graphql "Type" system, but no "interfaces")
- multiple queries in the same document
- interfaces and fragments
- variables
- full validation and errors (works needed on dataql for better errors)

### Mutations

- no ideas for now (a lot related to the storage backend, so I have to think a lot about it)
