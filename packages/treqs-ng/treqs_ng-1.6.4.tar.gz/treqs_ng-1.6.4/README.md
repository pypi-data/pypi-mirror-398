# TReqs

**Lightweight, Git-native requirements management for agile system development**

[![Pipeline Status](https://gitlab.com/treqs-on-git/treqs-ng/badges/master/pipeline.svg)](https://gitlab.com/treqs-on-git/treqs-ng/-/pipelines)
[![PyPI](https://img.shields.io/pypi/v/treqs-ng)](https://pypi.org/project/treqs-ng/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitLab](https://img.shields.io/badge/GitLab-treqs--ng-orange?logo=gitlab)](https://gitlab.com/treqs-on-git/treqs-ng)

TReqs-NG brings requirements management into your development workflow by storing requirements as text files alongside your code. No vendor lock-in, no expensive licenses, no context switching between tools.

## What is TReqs?

TReqs (Textual Requirements) is a command-line tool that enables agile teams to manage system requirements directly in Git. It treats requirements as first-class citizens in your repository, allowing you to:

- **Write requirements in plain text** - Use Markdown files that live alongside your code
- **Track changes with Git** - Requirements are versioned, reviewed, and merged just like code
- **Maintain traceability** - Create and validate links between requirements, tests, and code
- **Scale with your team** - Multiple developers can work on requirements in parallel

## Why TReqs?

Traditional requirements tools don't integrate well with modern agile workflows:

| Challenge                                              | TReqs Solution                                       |
| ------------------------------------------------------ | ---------------------------------------------------- |
| Requirements tools are separate from development tools | Requirements live in Git, reviewed in merge requests |
| Requirements become outdated quickly                   | Teams update requirements alongside code changes     |
| Poor version control and traceability                  | Full Git history and automated traceability checking |
| Expensive licenses and vendor lock-in                  | Open source, text-based, works with any editor       |
| Doesn't scale for multiple teams                       | Git-based parallel development and peer review       |

## Quick Start

### Installation

Install TReqs via pip:

```bash
pip install treqs-ng
```

Or install from source:

```bash
git clone https://github.com/treqs-on-git/treqs-ng.git
cd treqs-ng
pip install -e .
```

### Basic Usage

1. **List all requirements** in your project:

   ```bash
   treqs list
   ```

2. **Create a new requirement**:

   ```bash
   treqs create --type requirement --prefix REQ >> requirements.md
   ```

3. **Check requirements validity**:

   ```bash
   treqs check
   ```

### Your First Requirement

Create a file `requirements.md` with:

```markdown
## User Authentication

<treqs-element type="requirement" id="a3f2c8d14b5e4c9a8d7e1f2a3b4c5d6e">
The system shall authenticate users via username and password.
</treqs-element>
```

Run `treqs list` to see your requirement, and `treqs check` to validate it.

## Key Features

### Traceability Management

Link requirements to other requirements, tests, and code:

```markdown
<treqs-element type="requirement" id="b8e9d2f36c7a4d1b9e8f2a3b4c5d6e7f">
User passwords shall be encrypted using bcrypt.
<treqs-link type="addresses" target="a3f2c8d14b5e4c9a8d7e1f2a3b4c5d6e"/>
</treqs-element>
```

TReqs validates that all links point to existing elements and follow your defined traceability rules.

### Custom Validation Rules

Define your traceability model in `ttim.yaml`:

```yaml
types:
  - name: requirement
    outlinks:
      - type: addresses
        target: stakeholderRequirement
      - type: hasParent
        target: requirement
    inlinks:
      - type: tests
        source: unittest
```

TReqs checks that your requirements conform to your model.

### Git-Native Workflow

```bash
# Create feature branch
git checkout -b feature/new-auth

# Add requirement
echo "<treqs-element type='requirement' id='c9f1e3d47a8b4e2c9f1a3b4c5d6e7f8a'>..." >> requirements.md

# Commit and push
git add requirements.md
git commit -m "Add authentication requirement"
git push origin feature/new-auth

# Create merge request - requirements are reviewed alongside code
```

### Flexible Element Types

TReqs supports any element types you define in your `ttim.yaml` configuration file. Common examples include stakeholder requirements, system requirements, tests, and documentation elements.

## Documentation

- **[Getting Started Guide](https://gitlab.com/treqs-on-git/treqs-ng/-/blob/master/documentation/getting-starting.md)** - Installation and setup
- **[Demo Tutorial](https://gitlab.com/treqs-on-git/treqs-ng/-/blob/master/documentation/demo.md)** - Step-by-step examples
- **[Traceability Strategy](https://gitlab.com/treqs-on-git/treqs-ng/-/blob/master/documentation/traceability-strategy.md)** - Configure traceability rules
- **[Comparison with Other Tools](https://gitlab.com/treqs-on-git/treqs-ng/-/blob/master/documentation/comparison.md)** - How TReqs compares to alternatives

## Architecture

TReqs elements are embedded in text files using XML-like tags:

```xml
<treqs-element type="requirement" id="d1e2f3a48b9c4d5eaf1b2c3d4e5f6a7b">
Requirement text goes here.
<treqs-link type="addresses" target="e2f3a4b59c1d4e6fba2c3d4e5f6a7b8c"/>
</treqs-element>
```

- Works in any text file: Markdown, source code comments, test files
- Elements are identified by unique IDs
- Traceability links are validated against your model (`ttim.yaml`)

## Comparison with Alternatives

| Tool                   | TReqs          | Doorstop    | JIRA        | Traditional RE Tools |
| ---------------------- | -------------- | ----------- | ----------- | -------------------- |
| Git Integration        | Native         | Partial     | Via commits | None                 |
| Human-Readable Storage | Yes (Markdown) | No (YAML)   | No          | No                   |
| Traceability Links     | Full support   | Basic       | Limited     | Full                 |
| License Cost           | Free (MIT)     | Free (LGPL) | Paid        | Expensive            |
| Parallel Development   | Yes            | Yes         | Limited     | No                   |
| Custom Validation      | Per-project    | Limited     | No          | Per-instance         |

[Full comparison table](https://gitlab.com/treqs-on-git/treqs-ng/-/blob/master/documentation/comparison.md)

## Requirements

- Python 3.9 or higher
- Git (for version control integration)

## Contributing

We welcome contributions! TReqs-NG is the consolidated version of TReqs, integrating features from various variants. See [CONTRIBUTING.md](https://gitlab.com/treqs-on-git/treqs-ng/-/blob/master/CONTRIBUTING.md) for details on previous versions and contributors.

## Versioning

TReqs follows [Semantic Versioning](https://semver.org/):

## License

TReqs is released under the [MIT License](https://gitlab.com/treqs-on-git/treqs-ng/-/blob/master/LICENSE).

## Research Background

TReqs is based on research into requirements engineering for large-scale agile system development:

- [Requirements Challenges in Large-Scale Agile](https://oerich.wordpress.com/2017/06/28/re-for-large-scale-agile-system-development/)
- [T-Reqs: Key Idea and User Stories (arXiv)](https://arxiv.org/abs/1805.02769)
- Research conducted at Chalmers University of Technology and University of Gothenburg

The tool has been validated in industrial settings and continues to evolve based on real-world usage.

**Get started today**: `pip install treqs-ng`
