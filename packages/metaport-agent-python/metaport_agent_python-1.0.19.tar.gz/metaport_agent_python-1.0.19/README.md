<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./metaport-logo.png" />
    <img alt="Metaport Logo" src="metaport-logo.png" />
  </picture>
</div>

[![Pipeline Status](https://gitlab.com/dcentrica/metaport/metaport-agent-python/badges/master/pipeline.svg?style=flat-square)](https://gitlab.com/dcentrica/metaport/metaport-agent-python/-/pipelines)
[![Latest Release](https://gitlab.com/dcentrica/metaport/metaport-agent-python/-/badges/release.svg?style=flat-square)](https://gitlab.com/dcentrica/metaport/metaport-agent-python/-/releases)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](#)
[![Software License](https://img.shields.io/badge/license-BSD3-brightgreen.svg?style=flat-square)](LICENSE.txt)
[![Test Coverage](https://gitlab.com/dcentrica/metaport/metaport-agent-python/badges/master/coverage.svg?style=flat-square)](#)
[![Docs](https://img.shields.io/badge/Docs-brightgreen.svg?style=flat-square)](https://docs.metaport.sh)

## What is this?

A client library which connects any Python app to a [Metaport](https://gitlab.com/dcentrica/metaport/metaport-server/) server using the [CycloneDX](https://cyclonedx.org/) SBOM standard for data interchange.

## How to use

### Introduction

The library will automatically generate an SBOM for your app, submit it to Metaport and subsequently delete it. Data can be sent using the `HTTP` or `Email` transports. See [the docs site](https://docs.metaport.sh) for example requests.

When installed in a Python project, the library provides a single executable `metaport`. It's designed to be invoked on a schedule via cron from within an application's production environment or as part of a CI/CD pipeline.

This library supports traditional Pip, Poetry, and Pipfile based projects. 

Vulnerabilities will be reported by this agent to your Metaport server by invoking the following commands (and in this order):

1. `poetry audit`
2. `pip-audit`

If neither command is available, no vulnerability data will be sent when using `--classic=1`. If however vulnerability data is required, consider running a side-by-side instance of [DependencyTrack](https://dependencytrack.org), and configuring Metaport with it for dependencies and vulnerabilties (without `--classic=1`).

### Requirements

This package requires Python 3.12+. If used as part of a CI/CD setup, it can be installed as a throwaway dependency via Poetry's `--dev` switch ala `poetry add --dev`, or as a permanent dependency of your application.

### Install

1. Poetry

As part of production apps:

```bash
poetry add metaport-agent-python
```

2. Pip

```bash
pip install metaport-agent-python
```

3. Environment Variables

There are some environment variables which need to be set before the lib will operate correctly. Please see [the docs site](https://docs.metaport.sh) for more detailed installation and configuration instructions and examples.

### Supported Frameworks and CMS's

Yours not listed? [Contributions](./CONTRIBUTING.md) are very welcome. Please [file an issue](https://gitlab.com/dcentrica/metaport/metaport-agent-python/-/issues/) and issue a Merge Request, it's a one-line file change!

* [Django](https://www.djangoproject.com/)
* [Wagtail](https://wagtail.org/)

The following frameworks do not currently share life-cycle information:

* [Flask](https://flask.palletsprojects.com/)
* [Quart](https://quart.palletsprojects.com/)
* [Pyramid](https://trypyramid.com/)
* [Bottle](https://bottlepy.org/)
* [Django CMS](https://www.django-cms.org/)
* [Pylons](https://www.pylonsproject.org/)
* [FastAPI](https://fastapi.tiangolo.com/)
* [Tornado](https://www.tornadoweb.org/)
* [CherryPy](https://cherrypy.dev/)
* [web2py](https://web2py.com/)
* [Falcon](https://falconframework.org/)
* [Sanic](https://sanic.dev/)
* [Starlette](https://starlette.dev/)
* [Molten](https://moltenframework.com/)
* [Klein](https://klein.readthedocs.io/)
* [wheezy](https://wheezyweb.readthedocs.io/)
* [turbogears](https://turbogears.org/)

## Development Setup

### Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### Using Poetry

```bash
# Install Poetry if not already installed
pip install poetry

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```
