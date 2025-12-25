from ChatGPTprompt import PromptEngineering
import os
from pathlib import Path
from ...processing.utils import DataLoader

model_abbreviation = {
    "lr" : "Logistic Regression",
    "mlp": "Multi-layer Perceptron",
    "ada": "Adaboost",
    "svm": "Support Vector Machine",
    "median": "Median Value Imputation",
    "knn": "kNN Imputation",
    "ii": "Iterative Imputation",
    "gain": "GAIN Imputation",
    "MIRACLE": "MIRACLE Imputation",
    "MIWAE": "MIWAE Imputation",
    'rus': "Random Under Sampler",
    'ros': "Random Over Sampler",
    'smote': "SMOTE",
    'mwmote': "MWMOTE",
}

_project_data_root = Path(__file__).resolve().parents[5] / "data"
data_loader = DataLoader(
    dataset="nhanes.csv",
    host_data_root=str(_project_data_root),
    container_data_root=str(os.getenv("CONTAINER_DATA_ROOT", _project_data_root)),
)
origin_folder = data_loader.get_models_dp_origins_folder()
api_key_path = os.path.join(data_loader.get_raw_data_folder(), "openai_key.txt")
with open(api_key_path, 'r') as f:
    api_key = f.read()[:-1]

# chat_prompt = PromptEngineering(api_key=api_key)
