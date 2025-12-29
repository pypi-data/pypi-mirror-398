# Commit Message Guidelines

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated semantic versioning and changelog generation.

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

## Types

- **feat**: A new feature (triggers MINOR version bump)
- **fix**: A bug fix (triggers PATCH version bump)
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning (formatting, etc.)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvements (triggers PATCH version bump)
- **test**: Adding or updating tests
- **build**: Changes to build system or dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

## Breaking Changes

To trigger a MAJOR version bump, add `BREAKING CHANGE:` in the commit footer or add `!` after the type:

```
feat!: remove deprecated API endpoint

BREAKING CHANGE: The /api/v1/old-endpoint has been removed. Use /api/v2/endpoint instead.
```

## Examples

### Feature (Minor bump)
```
feat(rabbitmq): add support for message priority

Implements message priority handling for RabbitMQ queues.
Closes #123
```

### Bug Fix (Patch bump)
```
fix(connection): handle connection timeout gracefully

Previously, connection timeouts would crash the application.
Now they are caught and logged properly.
```

### Breaking Change (Major bump)
```
feat(api)!: redesign tool discovery interface

BREAKING CHANGE: The search-ids tool now returns a different schema.
Update your client code to use the new response format.
```

### Documentation
```
docs(readme): update installation instructions

Add information about Python 3.12 requirement.
```

## Scopes

Common scopes for this project:
- `rabbitmq`: RabbitMQ operations
- `mcp`: MCP protocol handling
- `tools`: Tool implementations
- `schemas`: Schema definitions
- `vector-db`: Vector database operations
- `config`: Configuration management
- `docs`: Documentation
- `ci`: CI/CD workflows

## Tips

1. Use the imperative, present tense: "change" not "changed" nor "changes"
2. Don't capitalize the first letter of the subject
3. No period (.) at the end of the subject
4. Separate subject from body with a blank line
5. Wrap body at 72 characters
6. Use the body to explain what and why vs. how
