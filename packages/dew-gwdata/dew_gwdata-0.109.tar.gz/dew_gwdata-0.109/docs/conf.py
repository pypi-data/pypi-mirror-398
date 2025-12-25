import importlib.metadata

project_name = "dew_gwdata"

project = f"{project_name} documentation"
copyright = "2019-20 DEW"
author = "Kent Inverarity"

release = importlib.metadata.version(project_name)
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    # 'sphinxcontrib.fulltoc',
]

templates_path = ["_templates"]

source_suffix = ".rst"
master_doc = "index"
language = "en"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = None

html_theme = "sphinx_rtd_theme"

html_theme_options = {}

html_context = {
    "github_user": "dew-waterscience",
    "github_repo": project_name,
    "github_version": "main",
    "doc_path": "docs",
}

html_static_path = ["_static"]

html_css_files = [
    "css/custom.css",
]


html_sidebars = {
    "**": [
        "search-field",
        "navbar-nav",
        "parent_links",
    ]
}


# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True


def setup(app):
    app.add_css_file("custom.css")


with open("../requirements.txt") as f:
    for line in f:
        if line.strip().startswith("sageodata_db"):
            sageodata_db_version = line.strip().split(">=")[1]
            break

rst_epilog = "\n".join(
    [
        f".. |{tag_name}| replace:: {tag}"
        for tag_name, tag in [("sageodata_db_version", sageodata_db_version)]
    ]
)
