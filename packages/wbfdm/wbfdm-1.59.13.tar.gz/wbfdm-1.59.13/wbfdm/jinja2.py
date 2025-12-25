from jinja2 import Environment
from jinjasql import JinjaSql  # type: ignore


def get_environment(**options):
    # we except only SQL template, so we need to not escape special characters (possible XSS attack for HTML template)
    env = Environment(**options)  # noqa: S701
    return JinjaSql(env=env, param_style="format").env
