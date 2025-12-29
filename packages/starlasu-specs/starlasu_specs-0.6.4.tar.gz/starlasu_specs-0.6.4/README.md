# Starlasu Specs

In this project we store the language definitions that represent the contract to be respected by the different Starlasu
Libraries.

## The AST Language

It includes the definition of:
* ASTNode
* Issue
* Common marker interfaces for ASTNode

## The Codebase Language

It includes the definition of:
* Codebase
* CodebaseFile

## The Types Language

It defines:
* An interface representing a Type
* An annotation to associate a Type to any other node

## Publish Python

```
python -m build
twine upload --repository github-specs dist/*
```
