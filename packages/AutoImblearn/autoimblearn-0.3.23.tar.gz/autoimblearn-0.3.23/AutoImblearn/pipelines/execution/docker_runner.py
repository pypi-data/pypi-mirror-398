import logging
import os
import time
import socket

import docker
import numpy as np
import pandas as pd

from AutoImblearn.components.exceptions import DockerContainerError

from AutoImblearn.components.model_client.image_spec import ImageSpec

logger = logging.getLogger(__name__)


def _resolve_mounts(model):
    # Path resolution lives here (runner), not in the base/model.
    mounts = model.get_volume_mounts()
    resolved = {}
    for host_path, cfg in mounts.items():
        resolved[str(host_path)] = cfg
    return resolved


def ensure_container_running(model):
    """
    Ensure the Docker container is running. Build/start if needed.
    """
    client = docker.from_env()
    try:
        container = client.containers.get(model.container_name)
        if container.status == 'running':
            # reuse host_port/api_url from container mapping
            ports = container.attrs['NetworkSettings']['Ports']
            internal = f"{model.container_port}/tcp"
            host_info = ports.get(internal)
            if host_info:
                model.host_port = int(host_info[0]['HostPort'])
                model.api_url = f"http://localhost:{model.host_port}"
                logger.info("Reusing running container %s (id=%s) on port %s", container.name, container.id, model.host_port)
                return
            else:
                raise RuntimeError("Could not find port mapping for the running container.")

        # Not running: start it
        logger.info("Starting stopped container %s (id=%s)", container.name, container.id)
        container.start()
        container.reload()
        ports = container.attrs['NetworkSettings']['Ports']
        internal = f"{model.container_port}/tcp"
        host_info = ports.get(internal)
        if host_info:
            model.host_port = int(host_info[0]['HostPort'])
            model.api_url = f"http://localhost:{model.host_port}"
            logger.info("Container %s started on port %s", container.name, model.host_port)
            return
        else:
            raise RuntimeError("Could not find port mapping for the restarted container.")

    except docker.errors.NotFound:
        # Start new container
        spec = model.get_image_spec()
        mounts = _resolve_mounts(model)
        ports = {f"{model.container_port}/tcp": None}
        logger.info("Creating new container %s from image %s", model.container_name, spec.image)
        container = client.containers.run(
            image=spec.image,
            name=model.container_name,
            ports=ports,
            volumes=mounts,
            entrypoint=["python3","-m", "app"],
            working_dir='/code/AutoImblearn/Docker',
            detach=True
        )
        model.container_id = container.id
        container.reload()
        ports = container.attrs['NetworkSettings']['Ports']
        internal = f"{model.container_port}/tcp"
        host_info = ports.get(internal)
        if host_info:
            model.host_port = int(host_info[0]['HostPort'])
            model.api_url = f"http://localhost:{model.host_port}"
            logger.info("Container %s (id=%s) started on port %s", container.name, container.id, model.host_port)
            return
        raise RuntimeError("Could not determine port mapping after starting container.")


def save_training_data(model, args, X_train, y_train=None, X_test=None, y_test=None):
    """
    Persist training/eval data to the interim folder so the container can read it.
    """
    base_root = getattr(args, "container_data_root", None)
    if base_root is None:
        raise ValueError("container_data_root is required to save training data")
    base_dir = os.path.join(base_root, "interim", args.dataset)
    os.makedirs(base_dir, exist_ok=True)

    def _to_dataframe(data):
        if isinstance(data, pd.DataFrame):
            return data
        return pd.DataFrame(data)

    def _save(data, filename):
        if data is None:
            return
        try:
            df = _to_dataframe(data)
            df.to_csv(os.path.join(base_dir, filename), index=False, header=True)
        except Exception as e:
            raise DockerContainerError(
                f"Failed to save training data file {filename}: {e}",
                container_id=getattr(model, "container_id", None),
                image_name=model.image_name,
                operation="save_data",
            ) from e

    cname = model.container_name
    _save(X_train, f"X_train_{cname}.csv")
    if y_train is not None:
        _save(y_train, f"y_train_{cname}.csv")
    if X_test is not None:
        _save(X_test, f"X_test_{cname}.csv")
    if y_test is not None:
        _save(y_test, f"y_test_{cname}.csv")


def _detect_api_host():
    """
    Choose the host to reach Docker-exposed ports.
    - When inside a container, prefer host.docker.internal, fall back to gateway.
    - Default to localhost for host-based execution.
    """
    try:
        socket.gethostbyname("host.docker.internal")
        return "host.docker.internal"
    except Exception:
        pass
    try:
        with open("/proc/net/route") as f:
            for line in f.readlines()[1:]:
                parts = line.strip().split()
                if len(parts) < 3:
                    continue
                if parts[1] != "00000000":
                    continue
                gateway = int(parts[2], 16)
                return socket.inet_ntoa(gateway.to_bytes(4, "little"))
    except Exception:
        pass
    return "localhost"


def run_fit(model):
    """
    Start container (if needed) and call the /fit endpoint with the model payload.

    Expected: model.payload returns JSON-serializable dict and model.args is set.
    """
    import requests
    from AutoImblearn.components.exceptions import DockerContainerError

    ensure_container_running(model)

    # Wait for container API to be ready before calling /fit
    _wait_for_api(model)

    try:
        api_host = _detect_api_host()
        headers = {"Content-Type": "application/json"}
        payload = model.payload

        # Set parameters first (if endpoint exists)
        logger.info("Posting /set then /train to container %s (id=%s)", getattr(model, "container_name", "?"), getattr(model, "container_id", None))
        set_resp = requests.post(f"http://{api_host}:{model.host_port}/set", json=payload, headers=headers)
        if set_resp.status_code not in (200, 201, 204):
            set_resp.raise_for_status()

        # Train endpoint
        response = requests.post(f"http://{api_host}:{model.host_port}/train", json=payload, headers=headers)
        response.raise_for_status()

        return response.json() if response.headers.get("Content-Type", "").startswith("application/json") else None
    except Exception as e:
        logs = get_container_logs(model)
        raise DockerContainerError(
            f"Fit API request failed: {e}",
            container_id=getattr(model, "container_id", None),
            image_name=model.image_name,
            logs=logs,
            operation="fit",
        ) from e
    finally:
        # Estimators typically stop after fit; transformers may keep_alive
        if not getattr(model, "keep_container_alive", False):
            stop_container(model)


def run_predict_proba(model, payload):
    """
    Call the /predict_proba endpoint for a fitted model.
    """
    import requests
    from AutoImblearn.components.exceptions import DockerContainerError

    ensure_container_running(model)
    _wait_for_api(model)

    try:
        api_host = _detect_api_host()
        headers = {"Content-Type": "application/json"}
        logger.info("Posting /predict_proba to container %s (id=%s)", getattr(model, "container_name", "?"), getattr(model, "container_id", None))
        response = requests.post(f"http://{api_host}:{model.host_port}/predict_proba", json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("probabilities", [])
    except Exception as e:
        logs = get_container_logs(model)
        raise DockerContainerError(
            f"Predict_proba API request failed: {e}",
            container_id=getattr(model, "container_id", None),
            image_name=model.image_name,
            logs=logs,
            operation="predict_proba",
        ) from e
    finally:
        if not getattr(model, "keep_container_alive", False):
            stop_container(model)


def run_transform(model, payload):
    """
    Call the /transform endpoint for transformers/resamplers.
    """
    import requests
    from AutoImblearn.components.exceptions import DockerContainerError

    ensure_container_running(model)
    _wait_for_api(model)

    try:
        api_host = _detect_api_host()
        headers = {"Content-Type": "application/json"}
        logger.info("Posting /transform to container %s (id=%s)", getattr(model, "container_name", "?"), getattr(model, "container_id", None))
        response = requests.post(f"http://{api_host}:{model.host_port}/transform", json=payload, headers=headers)
        response.raise_for_status()
        return response
    except Exception as e:
        logs = get_container_logs(model)
        raise DockerContainerError(
            f"Transform API request failed: {e}",
            container_id=getattr(model, "container_id", None),
            image_name=model.image_name,
            logs=logs,
            operation="transform",
        ) from e
    finally:
        if not getattr(model, "keep_container_alive", False):
            stop_container(model)


def run_predict(model, payload, result_key="balanced_data"):
    """
    Call the /predict endpoint for estimators that expose it.
    """
    import requests
    from AutoImblearn.components.exceptions import DockerContainerError

    ensure_container_running(model)
    _wait_for_api(model)

    try:
        api_host = _detect_api_host()
        headers = {"Content-Type": "application/json"}
        logger.info("Posting /predict to container %s (id=%s)", getattr(model, "container_name", "?"), getattr(model, "container_id", None))
        response = requests.post(f"http://{api_host}:{model.host_port}/predict", json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get(result_key, [])
    except Exception as e:
        logs = get_container_logs(model)
        raise DockerContainerError(
            f"Predict API request failed: {e}",
            container_id=getattr(model, "container_id", None),
            image_name=model.image_name,
            logs=logs,
            operation="predict",
        ) from e
    finally:
        if not getattr(model, "keep_container_alive", False):
            stop_container(model)


def stop_container(model):
    """
    Stop and remove the running container.
    """
    client = docker.from_env()
    try:
        container = client.containers.get(model.container_name)
        logger.info("Stopping and removing container %s (id=%s)", container.name, container.id)
        container.stop()
        container.remove(force=True)
    except docker.errors.NotFound:
        return
    except Exception as e:
        logging.warning(f"Failed to stop/remove container {model.container_name}: {e}")


def get_container_logs(model):
    """Fetch recent logs for a model container."""
    client = docker.from_env()
    try:
        container = client.containers.get(model.container_name)
        raw = container.logs(tail=200) or b""
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return None


def _wait_for_api(model, timeout=60, path="/health"):
    import requests
    start_time = time.time()
    port = getattr(model, "host_port", None)
    api_host = _detect_api_host()
    url = f"http://{api_host}:{port}{path}"
    while time.time() - start_time < timeout:
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                return
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    raise TimeoutError(f"API failed to become ready within timeout period at {url}")
