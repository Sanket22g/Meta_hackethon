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


def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
