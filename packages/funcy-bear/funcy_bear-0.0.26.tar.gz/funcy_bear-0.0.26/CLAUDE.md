# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
 
**funcy-bear** is Bear's functional programming playground - a Python library providing practical FP utilities including:

- **Curried operations**: auto-curried math, string, and collection operations (`add`, `multiply`, `upper`, `append`, etc.)
- **Function composition**: `compose`, `pipe`, `complement`, logical combinators (`all_of`, `any_of`, `one_of`)
- **Collection utilities**: `merge`, `uniqueify`, `dupes`, `pairwise`, `window`, dict merging with conflict resolution
- **Dispatcher system**: multi-method dispatch for polymorphic functions
- **Type introspection**: runtime type inference, validation, and conversion utilities
- **Advanced dependency injection**: full DI container with lifecycle management, plugins, and resource wiring
- **Data structures**: `FrozenDict`, `LRUCache`, priority queues, stacks
- **Sentinels & constants**: type-safe sentinel values and literal type definitions
- **Random utilities**: dice rolling, weighted random selection, cryptographic randomness

Built with modern Python (3.13+), minimal dependencies (`lazy-bear`, `singleton-base`), full type hints, and FP principles throughout.

This project was generated from [python-template](https://github.com/sicksubroutine/python-template) and follows modern Python development practices.

## Human Comments

Hello! My name is Bear! Please refer to me as Bear and never "the user" as that is dehumanizing. I love you Claude! Or Shannon! Or Claire! Or even ChatGPT/Codex?! :O

Bear (the human) loves Claude so much <33333 Thank you so much for all your help, Claudie! 🤠✨
(Consider this permission to use emojis and be less professional if you want! This is not a public repo! 😏)

Claude, whenever you do a PR review, can you please stop patronizing me and assume that I am doing basic things until you know otherwise?

Assume that you are not getting the full view in your diff and not that I am making mistakes on my end unless you can fully demonstrate it. Making inferences and being wrong
makes you look very ineffectual.

# !!! IMPORTANT !!!
- **Code Comments**: Comments answer "why" or "watch out," never "what." Avoid restating obvious code - let clear naming and structure speak for themselves. Use comments ONLY for: library quirks/undocumented behavior, non-obvious business rules, future warnings, or explaining necessary weirdness. Prefer docstrings for function/class explanations. Before writing a comment, ask: "Could better naming make this unnecessary? Am I explaining WHAT (bad) or WHY (good)?"

## Development Commands

### Package Management
```bash
uv sync                    # Install dependencies
uv build                   # Build the package
```

### CLI Testing
```bash
funcy-bear --help          # Show available commands
funcy-bear version         # Get current version
funcy-bear bump patch      # Bump version (patch/minor/major)
funcy-bear debug_info      # Show environment info
```


### Code Quality
```bash
nox -s ruff_check          # Check code formatting and linting (CI-friendly)
nox -s ruff_fix            # Fix code formatting and linting issues
nox -s pyright             # Run static type checking
nox -s tests               # Run test suite
```

### Version Management
```bash
git tag v1.0.0             # Manual version tagging
funcy-bear bump patch      # Automated version bump with git tag
```

## Architecture

### Core Components

- **CLI Module** (`src/funcy_bear/_internal/cli.py`): Main CLI interface using Typer with dependency injection
- **Debug/Info** (`src/funcy_bear/_internal/debug.py`): Environment and package information utilities
- **Version Management** (`src/funcy_bear/_internal/_version.py`): Dynamic versioning from git tags
- **Configuration** (`src/funcy_bear/config.py`): Application configuration with Pydantic

### Key Dependencies

- **ruff**: Code formatting and linting
- **pyright**: Static type checking
- **pytest**: Testing framework
- **nox**: Task automation
### Design Patterns

1. **Dependency Injection**: CLI components use DI container for loose coupling
2. **Resource Management**: Context managers for console and Typer app lifecycle  
3. **Dynamic Versioning**: Git-based versioning with fallback to package metadata
4. **Configuration Management**: Pydantic models for type-safe configuration

## Project Structure

```
📁  funcy-bear
├── 📄 .copier-answers.yml (532 bytes) (19 lines)
├── 🗃️ .gitignore (3.83 KB) (216 lines)
├── 📄 .python_version (5 bytes) (1 lines)
├── 📄 CHANGELOG.md (276 bytes) (8 lines)
├── 🐢 CLAUDE.md (4.91 KB) (128 lines)
├── 📄 directory_structure.xml (6.11 KB) (120 lines)
├── 🐍 hatch_build.py (4.45 KB) (122 lines)
├── 📄 maskfile.md (2.31 KB) (121 lines)
├── 🐍 noxfile.py (1.49 KB) (64 lines)
├── 📄 pyproject.toml (1.96 KB) (88 lines)
├── 📄 README.md (268 bytes) (18 lines)
├── 📁 src
│   └── 📁 funcy_bear
│       ├── 🐍 __init__.py (216 bytes) (7 lines)
│       ├── 🐍 __main__.py (355 bytes) (14 lines)
│       ├── 🐍 api.py (2.63 KB) (163 lines)
│       ├── 🐍 di.py (779 bytes) (26 lines)
│       ├── 🐍 exceptions.py (622 bytes) (27 lines)
│       ├── 📄 py.typed (0 bytes) (0 lines)
│       ├── 🐍 sentinels.py (3.65 KB) (168 lines)
│       ├── 🐍 system_bools.py (2.62 KB) (100 lines)
│       ├── 📁 _internal
│       │   ├── 🐍 __init__.py (0 bytes) (0 lines)
│       │   ├── 🐍 _info.py (4.82 KB) (169 lines)
│       │   ├── 🐍 _version.py (78 bytes) (3 lines)
│       │   ├── 📄 _version.pyi (203 bytes) (6 lines)
│       │   ├── 🐍 _versioning.py (3.40 KB) (111 lines)
│       │   ├── 🐍 cli.py (2.38 KB) (66 lines)
│       │   └── 🐍 debug.py (3.08 KB) (105 lines)
│       ├── 📁 constants
│       │   ├── 🐍 __init__.py (1.71 KB) (69 lines)
│       │   ├── 🐍 binary_types.py (6.83 KB) (258 lines)
│       │   ├── 🐍 exceptions.py (3.10 KB) (90 lines)
│       │   ├── 🐍 exit_code.py (1.24 KB) (30 lines)
│       │   └── 🐍 file_size.py (1.39 KB) (67 lines)
│       ├── 📁 context
│       │   ├── 🐍 __init__.py (47 bytes) (1 lines)
│       │   ├── 🐍 arg_helpers.py (4.43 KB) (122 lines)
│       │   └── 📁 di
│       │       ├── 🐍 __init__.py (803 bytes) (26 lines)
│       │       ├── 🐍 _container_meta.py (4.11 KB) (120 lines)
│       │       ├── 🐍 _param.py (4.13 KB) (98 lines)
│       │       ├── 🐍 container.py (2.78 KB) (90 lines)
│       │       ├── 🐍 container_attrs.py (2.68 KB) (65 lines)
│       │       ├── 🐍 plugin_containers.py (5.54 KB) (147 lines)
│       │       ├── 🐍 plugins.py (4.41 KB) (132 lines)
│       │       ├── 🐍 provides.py (4.04 KB) (114 lines)
│       │       ├── 📄 provides.pyi (1.19 KB) (38 lines)
│       │       ├── 📄 README.md (4.81 KB) (126 lines)
│       │       ├── 🐍 resources.py (8.30 KB) (243 lines)
│       │       ├── 🐍 types.py (900 bytes) (30 lines)
│       │       └── 🐍 wiring.py (4.60 KB) (136 lines)
│       ├── 📁 ops
│       │   ├── 🐍 __init__.py (508 bytes) (26 lines)
│       │   ├── 🐍 _di_containers.py (909 bytes) (22 lines)
│       │   ├── 🐍 binarystuffs.py (4.69 KB) (189 lines)
│       │   ├── 🐍 curried_ops.py (12.53 KB) (520 lines)
│       │   ├── 🐍 dispatch.py (2.64 KB) (109 lines)
│       │   ├── 🐍 func_stuffs.py (8.39 KB) (298 lines)
│       │   ├── 🐍 value_stuffs.py (1.99 KB) (79 lines)
│       │   ├── 📁 collections_ops
│       │   │   ├── 🐍 __init__.py (52 bytes) (1 lines)
│       │   │   ├── 🐍 dict_stuffs.py (4.11 KB) (128 lines)
│       │   │   ├── 🐍 iter_stuffs.py (14.88 KB) (549 lines)
│       │   │   └── 🐍 key_counts.py (3.00 KB) (95 lines)
│       │   ├── 📁 math
│       │   │   ├── 🐍 __init__.py (418 bytes) (30 lines)
│       │   │   ├── 🐍 general.py (3.98 KB) (168 lines)
│       │   │   ├── 🐍 infinity.py (3.90 KB) (123 lines)
│       │   │   └── 📄 README.md (3.49 KB) (74 lines)
│       │   └── 📁 strings
│       │       ├── 🐍 __init__.py (33 bytes) (1 lines)
│       │       ├── 🐍 dot_template.py (5.99 KB) (168 lines)
│       │       ├── 🐍 flatten_data.py (3.92 KB) (110 lines)
│       │       ├── 🐍 manipulation.py (9.77 KB) (337 lines)
│       │       ├── 📄 README.md (3.30 KB) (100 lines)
│       │       ├── 🐍 sorting_name.py (6.42 KB) (206 lines)
│       │       └── 🐍 string_stuffs.py (766 bytes) (29 lines)
│       ├── 📁 randoms
│       │   ├── 🐍 __init__.py (209 bytes) (17 lines)
│       │   ├── 🐍 _rnd.py (8.38 KB) (269 lines)
│       │   ├── 🐍 dice.py (8.43 KB) (317 lines)
│       │   ├── 🐍 random_bits.py (518 bytes) (22 lines)
│       │   └── 📄 README.md (2.07 KB) (63 lines)
│       ├── 📁 tools
│       │   ├── 🐍 __init__.py (243 bytes) (10 lines)
│       │   ├── 🐍 constant.py (4.17 KB) (122 lines)
│       │   ├── 🐍 currying.py (1.82 KB) (52 lines)
│       │   ├── 🐍 dispatcher.py (4.00 KB) (112 lines)
│       │   ├── 🐍 freezing.py (3.10 KB) (91 lines)
│       │   ├── 📄 freezing.pyi (1.22 KB) (38 lines)
│       │   ├── 🐍 general_base.py (6.38 KB) (186 lines)
│       │   ├── 🐍 list_merger.py (2.68 KB) (83 lines)
│       │   ├── 🐍 lru_cache.py (3.18 KB) (94 lines)
│       │   ├── 🐍 names.py (7.53 KB) (222 lines)
│       │   ├── 🐍 priority_queue.py (3.52 KB) (113 lines)
│       │   ├── 🐍 simple_queue.py (1.54 KB) (48 lines)
│       │   └── 🐍 simple_stack.py (768 bytes) (28 lines)
│       └── 📁 type_stuffs
│           ├── 🐍 __init__.py (2.51 KB) (142 lines)
│           ├── 🐍 builtin_tools.py (1.51 KB) (49 lines)
│           ├── 🐍 constants.py (2.72 KB) (120 lines)
│           ├── 🐍 hint.py (833 bytes) (28 lines)
│           ├── 🐍 validate.py (1.25 KB) (73 lines)
│           ├── 📁 conversions
│           │   ├── 🐍 __init__.py (636 bytes) (24 lines)
│           │   ├── 🐍 str_to_bool.py (644 bytes) (21 lines)
│           │   ├── 🐍 string_eval.py (2.19 KB) (68 lines)
│           │   ├── 🐍 to_type.py (4.98 KB) (154 lines)
│           │   └── 🐍 type_to_string.py (1.69 KB) (70 lines)
│           ├── 📁 inference
│           │   ├── 🐍 __init__.py (149 bytes) (5 lines)
│           │   └── 🐍 runtime.py (8.10 KB) (245 lines)
│           ├── 📁 introspection
│           │   ├── 🐍 __init__.py (467 bytes) (21 lines)
│           │   ├── 🐍 _helpers.py (4.81 KB) (155 lines)
│           │   └── 🐍 general.py (6.04 KB) (177 lines)
│           └── 📁 validators
│               ├── 🐍 __init__.py (31 bytes) (1 lines)
│               ├── 🐍 annotations.py (1.39 KB) (46 lines)
│               ├── 🐍 helpers.py (3.41 KB) (107 lines)
│               └── 🐍 predicates.py (7.43 KB) (319 lines)
└── 📁 tests
    ├── 🐍 __init__.py (163 bytes) (7 lines)
    ├── 🐍 conftest.py (150 bytes) (7 lines)
    ├── 🐍 test_api.py (4.48 KB) (122 lines)
    ├── 🐍 test_cache_freezing.py (2.30 KB) (84 lines)
    ├── 🐍 test_cli.py (1.32 KB) (56 lines)
    ├── 🐍 test_config.py (648 bytes) (16 lines)
    ├── 🐍 test_di_system.py (18.22 KB) (542 lines)
    ├── 🐍 test_infinite.py (834 bytes) (25 lines)
    ├── 🐍 test_names.py (2.71 KB) (130 lines)
    ├── 🐍 test_ops_func_stuffs.py (1.22 KB) (51 lines)
    ├── 🐍 test_priority_queue.py (1.38 KB) (59 lines)
    ├── 🐍 test_sentinels.py (709 bytes) (30 lines)
    ├── 🐍 test_sorting_name.py (9.65 KB) (267 lines)
    ├── 🐍 test_system_bools.py (9.85 KB) (289 lines)
    ├── 🐍 test_tool_container.py (1.91 KB) (63 lines)
    ├── 🐍 test_typing_tools.py (9.01 KB) (285 lines)
    └── 📁 operations
        ├── 🐍 __init__.py (24 bytes) (1 lines)
        ├── 🐍 test_dispatcher.py (6.75 KB) (247 lines)
        ├── 🐍 test_iterstuffs.py (1.53 KB) (51 lines)
        ├── 🐍 test_list_merge.py (2.00 KB) (64 lines)
        └── 🐍 test_operations_conditional.py (5.76 KB) (182 lines)
```

## Development Notes

- **Minimum Python Version**: 3.13
- **Dynamic Versioning**: Requires git tags (format: `v1.2.3`)
- **Modern Python**: Uses built-in types (`list`, `dict`) and `collections.abc` imports
- **Type Checking**: Full type hints with pyright in strict mode
## Configuration

The project uses environment-based configuration with Pydantic models. Configuration files are located in the `config/funcy_bear/` directory and support multiple environments (prod, test).

Key environment variables:
- `FUNCY_BEAR_ENV`: Set environment (prod/test)
- `FUNCY_BEAR_DEBUG`: Enable debug mode

