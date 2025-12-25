import os
from pathlib import Path
from textwrap import dedent


def generate_dockerfile(
        model_name: str,
        model_dir: str,
        base_image: str,
        entrypoint="app.py",):
    """
    generate the Dockerfile for the selected model

    :param model_name: The name of the model selected
    :param model_dir: The path that contains the model, flask API script, requirements
    :param base_image: The name of the base image
    :param entrypoint: The name of flask API script file
    :return: None
    """
    model_path = Path(model_dir) / model_name
    model_path.mkdir(parents=True, exist_ok=True)
    dockerfile_path = model_path / "Dockerfile"

    content = dedent(f"""\
        FROM {base_image}

        # Copy model files
        COPY . /app/
        WORKDIR /app

        # Set the entrypoint
        CMD ["python", "{entrypoint}"]
    """)

    with open(dockerfile_path, "w") as f:
        f.write(content)
    print(f"[✓] Dockerfile generated for '{model_name}' at {dockerfile_path}")


# Example usage
if __name__ == "__main__":
    models = [
        {"name": "autosmote", "entrypoint": "autosmote_api.py"},
        {"name": "mesa", "entrypoint": "mesa_api.py"},
        {"name": "autoresampler", "entrypoint": "resampler_api.py"},
    ]

    for m in models:
        generate_dockerfile(
            model_name=m["name"],
            entrypoint=m["entrypoint"],
            model_dir="AutImblearn/AutImblearn/models"
        )
