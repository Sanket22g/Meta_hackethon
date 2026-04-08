"""
FastAPI application for MediaOps-CRM-Env.
Exposes: POST /reset, POST /step, GET /state, GET /schema, WS /ws
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError("openenv-core is required. Run: uv sync") from e

try:
    from ..models import MediaOpsAction, MediaOpsObservation
    from .mediaops_environment import MediaOpsCRMEnvironment
except (ImportError, ModuleNotFoundError):
    from models import MediaOpsAction, MediaOpsObservation
    from server.mediaops_environment import MediaOpsCRMEnvironment


app = create_app(
    MediaOpsCRMEnvironment,
    MediaOpsAction,
    MediaOpsObservation,
    env_name="mediaops_crm_env",
    max_concurrent_envs=4,
)


def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
