import json
import importlib.util
from pathlib import Path
from typing import Optional

import numpy as np
from ..components.automls import RunH2O, RunTPOT, RunAutoSklearn
from AutoImblearn.components.model_client.image_spec import DockerImageProvider


# AutoML systems - using lazy initialization pattern (lambdas)
# to avoid instantiation errors before host_data_root is set
automls = {
    "h2o": lambda host_data_root: RunH2O(host_data_root=host_data_root),
    "tpot": lambda host_data_root: RunTPOT(host_data_root=host_data_root),
    "autosklearn": lambda host_data_root: RunAutoSklearn(host_data_root=host_data_root),
}
_BUILTIN_AUTOMLS = set(automls.keys())


def load_custom_components():
    """Load custom AutoML clients registered via data/models/registry/automls.json."""
    registry_path = Path(__file__).resolve().parents[4] / "data" / "models" / "registry" / "automls.json"
    if not registry_path.exists():
        registry = []
    else:
        try:
            registry = json.loads(registry_path.read_text())
        except Exception:
            registry = []

    components_root = Path(__file__).resolve().parents[1] / "components"
    for entry in registry:
        model_id = entry.get("id")
        if not model_id or model_id in automls:
            continue

        target = components_root / "automls" / model_id / "run.py"
        if not target.exists():
            target = target.parent / "__init__.py"
        if not target.exists():
            continue

        spec = importlib.util.spec_from_file_location(f"AutoImblearn.components.automls.{model_id}", target)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore

        def factory(mod=module, mid=model_id, **kw):
            if hasattr(mod, "build_model"):
                return mod.build_model(**kw)
            if hasattr(mod, "get_model"):
                return mod.get_model(**kw)
            raise RuntimeError(f"Custom AutoML {mid} missing build_model/get_model")

        def wrapper(host_data_root, _factory=factory):
            try:
                return _factory(host_data_root=host_data_root)
            except TypeError:
                return _factory()

        automls[model_id] = wrapper


def reload_custom_components():
    """Reload custom AutoML clients, clearing previous custom entries first."""
    for key in [k for k in list(automls.keys()) if k not in _BUILTIN_AUTOMLS]:
        automls.pop(key, None)
    load_custom_components()


load_custom_components()


class CustomAutoML:
    def __init__(self, args, automl):
        self.args = args
        if automl not in automls:
            raise ValueError(f"Model {automl} not defined in model.py")

        factory = automls[automl]
        self.automl = None
        for builder in (
            lambda: factory(host_data_root=self.args.host_data_root),
            lambda: factory(),
        ):
            try:
                self.automl = builder()
                break
            except TypeError:
                continue
        if self.automl is None:
            raise ValueError(f"Could not initialize AutoML client for {automl}")
        if not hasattr(self.automl, "fit") or not hasattr(self.automl, "predict"):
            raise ValueError(f"AutoML client for {automl} must implement fit/predict")
        self.result = None

    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        # Train classifier
        try:
            self.automl.fit(X_train, y_train, args=self.args)
        except TypeError:
            self.automl.fit(X_train, y_train)

    def predict(self):
        try:
            return self.automl.predict(args=self.args)
        except TypeError:
            return self.automl.predict()


if __name__ == "__main__":
    class Arguments:
        def __init__(self):
            self.dataset = "nhanes.csv"
            self.metric = "auroc"

            self.device = "cpu"
            self.cuda = "0"

            self.val_ratio=0.1,
            self.test_raito=0.1,
    args = Arguments()

    tmp = CustomAutoML(args, 'autosklearn')
    tmp.train(None, None)
    print(tmp.predict(None, None))


def get_automl_provider(method: str) -> Optional[DockerImageProvider]:
    if method == "h2o":
        return RunH2O
    if method == "tpot":
        return RunTPOT
    if method == "autosklearn":
        return RunAutoSklearn
    return None
