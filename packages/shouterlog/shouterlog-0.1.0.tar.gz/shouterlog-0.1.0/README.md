# Reusables

<a><img src="https://raw.githubusercontent.com/Kiril-Mordan/reusables/refs/heads/main/.github/docs/reuse_logo.png" width="35%" height="35%" align="right" /></a>

Contains pieces of code that have been generalized to the extent that they can be reused in other projects. The repository is designed to shorten the development cycle of single-module packages from the initial idea to a functioning alpha version accessible through PyPI.

Its ci/cd pipeline contains tools to package not only simple python modules, but cli tools with click, static documnentation with mkdocs, routes for fastapi applications and files within a package as artifacts, that could be extracted from that package later.

## Usage

Modules in the reposity could be accessed from PyPI for the packages that reached that level. These meet the following criterias:

- passes linters threshold and unit tests if included
- passes vulnerability check of dependencies
- includes usage examples generated from corresponing .ipynb file
- contains short module level docstring
- contains `__package_metadata__` (won't package without it)
- falls under common [`license`](https://github.com/Kiril-Mordan/reusables/blob/main/LICENSE)



 
## Documentation
 
 
Links to the extended documentation of packaged modules, available through gh-pages:
 
- [![MkDocs](https://img.shields.io/static/v1?label=&message=Attrsx&color=darkgreen&logo=mkdocs)](https://kiril-mordan.github.io/reusables/attrsx) [![PyPiVersion](https://img.shields.io/pypi/v/attrsx)](https://pypi.org/project/attrsx/) 
- [![MkDocs](https://img.shields.io/static/v1?label=&message=Comparisonframe&color=darkgreen&logo=mkdocs)](https://kiril-mordan.github.io/reusables/comparisonframe) [![PyPiVersion](https://img.shields.io/pypi/v/comparisonframe)](https://pypi.org/project/comparisonframe/) 
- [![MkDocs](https://img.shields.io/static/v1?label=&message=Gridlooper&color=darkgreen&logo=mkdocs)](https://kiril-mordan.github.io/reusables/gridlooper) [![PyPiVersion](https://img.shields.io/pypi/v/gridlooper)](https://pypi.org/project/gridlooper/) 
- [![MkDocs](https://img.shields.io/static/v1?label=&message=Mocker-db&color=darkgreen&logo=mkdocs)](https://kiril-mordan.github.io/reusables/mocker_db) [![PyPiVersion](https://img.shields.io/pypi/v/mocker-db)](https://pypi.org/project/mocker-db/) [![Docker Hub](https://img.shields.io/docker/v/kyriosskia/mocker-db?label=dockerhub&logo=docker)](https://hub.docker.com/r/kyriosskia/mocker-db)
- [![MkDocs](https://img.shields.io/static/v1?label=&message=Package-auto-assembler&color=darkgreen&logo=mkdocs)](https://kiril-mordan.github.io/reusables/package_auto_assembler) [![PyPiVersion](https://img.shields.io/pypi/v/package-auto-assembler)](https://pypi.org/project/package-auto-assembler/) 
- [![MkDocs](https://img.shields.io/static/v1?label=&message=Parameterframe&color=darkgreen&logo=mkdocs)](https://kiril-mordan.github.io/reusables/parameterframe) [![PyPiVersion](https://img.shields.io/pypi/v/parameterframe)](https://pypi.org/project/parameterframe/) [![Docker Hub](https://img.shields.io/docker/v/kyriosskia/parameterframe?label=dockerhub&logo=docker)](https://hub.docker.com/r/kyriosskia/parameterframe)
- [![MkDocs](https://img.shields.io/static/v1?label=&message=Proompter&color=darkgreen&logo=mkdocs)](https://kiril-mordan.github.io/reusables/proompter) [![PyPiVersion](https://img.shields.io/pypi/v/proompter)](https://pypi.org/project/proompter/) 
- [![MkDocs](https://img.shields.io/static/v1?label=&message=Shouterlog&color=darkgreen&logo=mkdocs)](https://kiril-mordan.github.io/reusables/shouterlog) [![PyPiVersion](https://img.shields.io/pypi/v/shouterlog)](https://pypi.org/project/shouterlog/) 
