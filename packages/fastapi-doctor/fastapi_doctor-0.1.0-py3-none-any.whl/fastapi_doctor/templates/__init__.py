from .api_templates import (
    get_api_init_template,
    get_api_routes_template,
    get_auth_router_template,
    get_v1_init_template,
    get_v1_router_template,
)
from .core_templates import (
    get_config_template,
    get_core_init_template,
    get_logging_template,
    get_main_template,
)
from .db_templates import get_session_template
from .frontend_templates import (
    get_index_html_template,
    get_root_route_template,
    get_templates_init_template,
    get_visual_template,
)
from .middleware_templates import (
    get_cors_middleware_template,
    get_middlewares_init_template,
)
from .misc_templates import (
    get_dev_template,
    get_env_template,
    get_lifespan_template,
    get_utils_init_template,
)

__all__ = [
    # Core
    "get_main_template",
    "get_config_template",
    "get_logging_template",
    "get_core_init_template",
    # API
    "get_api_init_template",
    "get_api_routes_template",
    "get_v1_init_template",
    "get_v1_router_template",
    "get_auth_router_template",
    # Database
    "get_session_template",
    # Middleware
    "get_middlewares_init_template",
    "get_cors_middleware_template",
    # Frontend
    "get_templates_init_template",
    "get_index_html_template",
    "get_root_route_template",
    "get_visual_template",
    # Misc
    "get_env_template",
    "get_dev_template",
    "get_utils_init_template",
    "get_lifespan_template",
]

