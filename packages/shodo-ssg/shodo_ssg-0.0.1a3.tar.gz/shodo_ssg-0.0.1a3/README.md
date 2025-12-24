 <p align="right">
 <img alt="Netlify Status" src="https://api.netlify.com/api/v1/badges/1ed945fb-7aa0-4ebd-89c0-45450ead70aa/deploy-status">
 <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/shodo-ssg">
 <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/shodo-ssg">
 <img alt="GitHub License" src="https://img.shields.io/github/license/ryanmphill/shodo-static-gen?color=purple">
 <img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/ryanmphill/shodo-static-gen/python-package.yml?label=Tests">
</p>

# Shodo Static Site Generator 🪶✒️📜

Shodo is a framework for rapidly building a static site from markdown files, json, and Jinja templates. Simply make changes to your site in the `src` directory, run the build command, and access the build in the `dist` directory. [Easily deploy to Netlify](https://shodo.dev/docs/deployment/#netlify) in just a few clicks. 


Check out [shodo.dev](https://shodo.dev) for the latest project updates and documentation!

## Why Shodo?
There is no shortage of options out there for building websites and apps, but they can quickly feel overcomplicated when all you need is a simple website with a few reusable components, or a quick solution to setting up a blog with an RSS feed. The goal of Shodo is to make publishing content to the web as simple and elegant as possible for developers, whether it's a personal blog, a portfolio, documentation, or a professional marketing site. 

**Key Features:**

- ✅ Write content in Markdown with front matter support
- ✅ Powerful Jinja2 templating with custom API functions
- ✅ Query JSON data with filtering, sorting, and pagination
- ✅ Automatic page generation from markdown articles
- ✅ Built-in pagination for article listings
- ✅ RSS/Atom feed generation support
- ✅ Nested layouts and partial templates
- ✅ Fast build times with automatic asset compilation

## Getting Started

### Installing the package

1. Create a new project directory and start a virtual environment using your preferred method

2. Install the `shodo_ssg` package by running one of the following commands:

**Via pip**:
```bash
pip install shodo-ssg
```

**Via pipenv**:
```bash
pipenv install shodo-ssg
```

**Via Poetry**:
```bash
poetry add shodo-ssg
```

**Via uv**:
```bash
uv add shodo-ssg
```

3. Once the package is installed, you can scaffold a new project using the command

```bash
start-shodo-project <name of project directory>
```

To create the project in the current directory, run

```bash
start-shodo-project .
```

4. Build the starter site and serve it to localhost by running the following command from the root directory of the project:

```bash
python serve.py
```

You should now be able to view the site on localhost and can start by making changes to `home.jinja`. When you simply want to build the static site, run the following command from the root directory:

```bash
python site_builder.py
```

and you can find your static site located in the `dist/` directory

## Docs

Visit [shodo.dev/docs](https://shodo.dev/docs) to learn more!


## Project Conventions

#### Jinja templates

For all jinja templates, use the `.jinja` file extension. Other extensions such as `.j2` or `.jinja2` are not fully supported at this time.

###### Syntax Highlighting
If you're using VSCode, the [Better Jinja](https://marketplace.visualstudio.com/items?itemName=samuelcolvin.jinjahtml) extension is recommended for full syntax highlighting out of the box using the `.jinja` extension. Other extensions will work, although you might need to configure the settings to look for the `.jinja` extension.

#### For Contributors
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This project uses the [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter) and follows the [current style guide](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html)

##### Pulling down the repository and installing locally

1. Start up a virtual environment and install the dev dependencies using your preferred method after pulling down the repository

2. Once your virtual environment is activated, in the root of the project directory run `pip install -e .`

3. Upon successful install, navigate to an entirely separate directory and run 

```bash
start-shodo-project <name of new project directory>
```

Upon success, a new starter project template should have been set up in the specified directory
