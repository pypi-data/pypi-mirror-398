from typing import Optional, Tuple

import mlflow


def ensure_mlflow(tracking_uri: Optional[str], experiment_name: str) -> None:
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    # Ensure experiment exists
    mlflow.set_experiment(experiment_name)


def log_and_register_model(model, artifact_path: str, input_example, register_name: Optional[str]) -> Tuple[str, Optional[int]]:
    """Log sklearn pipeline and optionally register.

    Returns (model_uri, registered_version|None)
    """
    # sklearn flavor is the default for sklearn pipelines
    mlflow.sklearn.log_model(model, artifact_path=artifact_path, input_example=input_example)
    run_id = mlflow.active_run().info.run_id
    uri = f"runs:/{run_id}/{artifact_path}"
    version = None
    if register_name:
        try:
            mv = mlflow.register_model(uri, register_name)
            version = int(mv.version)
        except Exception as e:
            # Fallback: still return URI for direct loading
            print("Model register failed:", e)
    return uri, version

