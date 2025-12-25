from jinja2 import Environment, PackageLoader, select_autoescape

JENV: Environment = Environment(
    loader=PackageLoader(
        package_name="dependency.cli",
        package_path="templates",
    ),
    autoescape=select_autoescape(
        enabled_extensions=["j2"]
    )
)
