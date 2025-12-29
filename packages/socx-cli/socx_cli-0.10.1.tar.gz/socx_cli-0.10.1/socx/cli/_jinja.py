from __future__ import annotations

from jinja2 import Environment, PrefixLoader, PackageLoader

loader: PrefixLoader = PrefixLoader(
    {"": PackageLoader("socx"), "config": PackageLoader("socx.config")}
)

env: Environment = Environment(loader=loader)
