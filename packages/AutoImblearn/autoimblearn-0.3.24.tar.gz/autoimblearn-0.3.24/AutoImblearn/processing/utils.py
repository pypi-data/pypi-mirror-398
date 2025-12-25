import os
import re
import pickle
import json
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

import pandas as pd
import numpy as np
# from imblearn.datasets import fetch_datasets
from sklearn.model_selection import StratifiedKFold
from sklearn.cluster import KMeans
from sklearn.preprocessing import KBinsDiscretizer
from scipy.stats import norm, gaussian_kde


# The path for the data folder
DATA_VOLUME_PATH = "../../data"
# DATA_VOLUME_PATH = os.path.join(__file__, '..', '..', 'data')

SHARED_HOST_DIR = os.path.abspath('DATA_VOLUME_PATH')
# SHARED_HOST_DIR = DATA_VOLUME_PATH
# Absolute path on the host to be shared
# os.makedirs(SHARED_HOST_DIR, exist_ok=True)    # ensure the directory exists

class ArgsNamespace(BaseModel):
    dataset: str = Field(default="nhanes.csv")
    target_name: str = Field(default="Status")  # Prediction target
    event_column: Optional[str] = Field(default=None)  # Survival event/status column
    time_column: Optional[str] = Field(default=None)  # Survival time-to-event column
    pipeline_type: Optional[str] = Field(default=None)  # Pipeline type selection from UI

    # Model parameters
    T_model: Literal["SVM", "LSVM", "lr", "rf", "mlp", "s2sl", "s2sLR", "ensemble", "ada", "bst"] = "lr"
    repeat: int = Field(default=0)

    # Pre-Processing
    aggregation: Literal["categorical", "binary"] = "binary"
    missing: Literal['median', 'mean', 'dropna', 'knn', 'ii', 'gain', 'MIRACLE', 'MIWAE'] = "median"

    # K-Fold
    n_splits: int = Field(default=10)

    # Resample related
    infor_method: Literal["normal", "nothing"] = "normal"
    resampling: bool = Field(default=False)
    resample_method: Literal["under", "over", "combined", "herding", "s2sl_mwmote", "MWMOTE", "smote"] = "under"
    samratio: float = Field(default=0.4)

    # Feature Importance
    feature_importance: Literal["NA", "lime", "shap"] = "NA"

    # GridSearchCV
    grid: bool = Field(default=False)

    # Top k feature
    top_k: int = Field(default=-1)

    # Auto-Imblearn related
    train_ratio: float = Field(default=1.0)
    metric: str = "auroc"
    rerun: bool = Field(default=False)
    exhaustive: bool = Field(default=False)
    host_data_root: Optional[str] = Field(default=None)
    container_data_root: Optional[str] = Field(default=None)

    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def _sync_fields(self):
        if self.host_data_root is None:
            raise ValueError("host_data_root is required and cannot be None")
        if self.container_data_root is None:
            raise ValueError("container_data_root is required and cannot be None")
        return self



def find_categorical_columns(X: pd.DataFrame) -> dict:
    """ Predict which columns are categorical """
    category_columns = {}
    # TODO make this one a feature
    categorical_threshold = 0.5             # Set a threshold to determine if a column is categorical
    for feature_name in X.columns.values:
        is_categorical = True
        # Calculate the derivatives in the Probability Density Function (PDF)
        feature = X[feature_name]

        # Check if the column has mixed data types (numeric and string). Remove string cells if it's mixed type
        is_mixed = feature.apply(lambda x: pd.to_numeric(x, errors='coerce')).notna().any() and \
                   feature.apply(lambda x: isinstance(x, str)).any()
        if is_mixed:
            feature = pd.to_numeric(feature, errors='coerce')   # Convert mixed type column to numeric, coercing errors to NaN

        unique_values = np.unique(feature)
        # Treat non-numeric columns as categorical directly
        try:
            unique_values = unique_values.astype(float)
        except (TypeError, ValueError):
            category_columns[feature_name] = "non_numeric"
            continue

        unique_count = len(unique_values)

        # Delete empty value from unique_count
        if np.isnan(unique_values).any():
            unique_count -= 1

        # skip binary features
        if unique_count == 2:
            continue

        total_count = feature.shape[0]          # Get the total number of values in the column

        # TODO make the second condition a parameter
        # When there is limited amount of values in the column
        if unique_count / total_count < 0.05 and unique_count < 20:
            unique_values.sort()
            edges = [(unique_values[i] + unique_values[i + 1]) / 2 for i in range(unique_count - 1)]        # Calculate the edges between unique values
            category_columns[feature_name] = edges
            continue

        # Find unique value count
        feature = feature[~np.isnan(feature)]       # Remove NaN values from the feature
        kde = gaussian_kde(feature)                 # Generate a Gaussian Kernel Density Estimate (KDE) for the feature

        # Calculate the derivative of the KDE values for feature
        x_values = np.linspace(feature.min(), feature.max(), 1000)
        kde_values = kde(x_values)

        df = pd.DataFrame(np.transpose(np.vstack((x_values, kde_values))), columns=['X', 'y'])
        df = df.assign(derivative=df.diff().eval('y/X'))

        max_density = df['y'].max()

        # Find where the local minimal is in the PDF
        trough_points = []  # trough_points stores the 'major' trough points of PDF
        crest_points = []  # crest_points stores the all crest points of PDF

        derivative = df['derivative']
        for i in range(len(derivative) - 1):
            previous_state = derivative[i]
            current_state = derivative[i + 1]
            if current_state * previous_state <= 0 and previous_state < 0:
                # if df['y'].iat[i] - feature_min < categorical_threshold * (feature_max - feature_min):
                if max_density - df['y'].iat[i] > categorical_threshold * max_density:
                    trough_points.append(i)
            elif current_state * previous_state <= 0 and previous_state > 0:
                crest_points.append(i)

        if not trough_points or not is_categorical:
            continue


        # shrink the size of the major trough points
        index = 0
        back = None
        front = 0
        edges = []
        for i in range(len(trough_points) - 1):
            trough = df['y'].iat[trough_points[i]]
            # find the largest crest before point 'i'
            end = trough_points[i]
            if back is None:
                back = 0
                while crest_points[index] < end:
                    tmp = df['y'].iat[crest_points[index]]
                    if tmp > back:
                        back = tmp
                    index += 1

            # find the largest crest after point 'i'
            if i == len(trough_points) - 1:
                end = len(x_values)
            else:
                end = trough_points[i + 1]

            while index < len(crest_points) and crest_points[index] < end:
                tmp = df['y'].iat[crest_points[index]]
                if tmp > front:
                    front = tmp
                index += 1

            # TODO determine if treat the 0.3 threshold as parameter
            if abs(front - trough) > 0.3 * max_density or abs(back - trough) > 0.3 * max_density:
                edges.append(df['X'].iat[trough_points[i]])

            back = front
            front = 0

        edges.sort()

        if len(edges) < 1:
            continue

        # TODO make this one a selection feature
        # TODO don't change X[feature_name]
        use_KBinsDiscretizer = False
        if use_KBinsDiscretizer:
            discretizer = KBinsDiscretizer(n_bins=len(edges) + 1, encode='ordinal', strategy='kmeans')
            enc = discretizer.fit_transform(feature.to_numpy().reshape(-1, 1)).reshape(1, -1)[0]
            X[feature_name] = pd.Series(enc)
        else:
            def convert2cal(x, edges):
                result = 0
                while result < len(edges):
                    if x <= edges[result]:
                        break
                    result += 1
                return result

            X[feature_name] = X[feature_name].map(lambda x: convert2cal(x, edges))

        # calcuate the edges of the category
        if use_KBinsDiscretizer:
            edges = discretizer.bin_edges_[0].tolist()[1:-1]
            category_columns[feature_name] = edges
        else:
            category_columns[feature_name] = edges

        # print(edges)
        # from sys import exit
        # exit()
        ### Plot the Probability Density Function (PDF)
        # plt.fill_between(x_values, kde_values, alpha=0.5)
        # plt.plot(feature, np.full_like(feature, -0.1), '|k', markeredgewidth=1)
        # plt.show()
    return category_columns


class DataLoader:
    """ DataLoader object to load train, valid and test data from dataset.
        Args:
            dataset (str): Name os the dataset
    """

    def __init__(self,
                 dataset: str='nhanes.csv', # The dataset name for training
                 is_notebook=False,         # If running the code in jupyter notebook
                 host_data_root=None,       # Host path for model containers
                 container_data_root=None,   # In-container path for celery/web
                 ) -> None:
        if host_data_root is None:
            raise ValueError("host_data_root is required for DataLoader")
        if container_data_root is None:
            raise ValueError("container_data_root is required for DataLoader")
        self.host_data_root = host_data_root
        self.container_data_root = container_data_root
        self.path = os.path.join(self.container_data_root, 'raw', dataset)

        self.name = os.path.basename(self.path)


        if is_notebook:
            self.path = os.path.join("../../../..", self.path)
        self.header = []

    def get_host_data_root(self):
        return self.host_data_root

    def get_interim_data_folder(self):
        return os.path.join(self.container_data_root, 'interim')

    def get_processed_data_folder(self):
        return os.path.join(self.container_data_root, 'processed')

    def get_raw_data_folder(self):
        return os.path.join(self.container_data_root, 'raw')

    def get_models_data_folder(self):
        return os.path.join(self.container_data_root, 'models')

    def get_models_dp_folder(self):
        return os.path.join(self.get_models_data_folder(), 'dps')

    def get_models_dp_origins_folder(self):
        return os.path.join(self.get_models_data_folder(), 'origins')

    def get_dataset_dp_folder(self):
        return os.path.join(self.container_data_root, 'datasets')

    def get_data_description(self, data_name):
        dp_folder = self.get_dataset_dp_folder()
        dp_path = os.path.join(dp_folder, 'dps.json')

        with open(dp_path) as f:
            dps = json.load(f)
        return dps[data_name]

    def train_loader(self, has_header=True) -> pd.DataFrame:
        """ Load training data
        :returns:
            df: whole data
        """
        if os.path.isfile(self.path):

            null_values = ['', ' ']

            # filetype = re.search("[^\.]*$", self.path).group()
            filetype = re.search(r"[^.]*$", self.path).group()

            if has_header:
                if filetype == "csv":
                    df = pd.read_csv(self.path, na_values=null_values)
                elif filetype == "xlsx":
                    df = pd.read_excel(self.path, na_values=null_values)
            else:
                if filetype == "csv":
                    df = pd.read_csv(self.path, na_values=null_values, header=None)
                elif filetype == "xlsx":
                    df = pd.read_excel(self.path, na_values=null_values, header=None)
            self.header = list(df.columns.values)
            return df
        # datasets = fetch_datasets()
        # if self.name in datasets.keys():
        #     df = datasets[self.name]
        #     # TODO set up dataset to accept target column value
        #     data = pd.DataFrame(data=df.data)
        #     data.columns = data.columns.astype(str)
        #     target = pd.DataFrame(data=df.target)
        #     target = target.rename(columns={0:"Status"})
        #     df = pd.concat([data, target], axis=1).copy()
        #     return df
        else:
            raise ValueError("There is no corresponding dataset of: {}".format(self.name))


class Samplar:
    """ Samplar oject to split data
        Args:
            X (np.ndarray):
            Y (np.ndarray):
    """
    def __init__(self, X: np.ndarray, Y: np.ndarray):

        self.X = X
        self.Y = Y


    def apply_kfold(self, split_num):
        """Apply stratified cross validation to dataset"""
        skf = StratifiedKFold(n_splits=split_num, shuffle=True, random_state=42)
        for train_index, test_index in skf.split(self.X, self.Y):
            X_train, X_test = self.X[train_index], self.X[test_index]
            Y_train, Y_test = self.Y[train_index], self.Y[test_index]
            yield (X_train, Y_train, X_test, Y_test)


class SurvivalSamplar:
    """
    Stratified sampler for survival data. Stratifies on the event indicator.

    Y can be a DataFrame with columns ["time","event"] or a structured array with
    fields ("Status","Survival_in_days").
    """

    def __init__(self, X: pd.DataFrame, Y: pd.DataFrame):
        self.X = X
        self.Y = Y

        # Extract event indicator
        if hasattr(Y, "dtype") and getattr(Y.dtype, "names", None):
            # Structured array
            events = Y["Status"]
        elif hasattr(Y, "columns"):
            # DataFrame
            if "event" in Y.columns:
                events = Y["event"].values
            elif "Status" in Y.columns:
                events = Y["Status"].values
            else:
                raise ValueError("Survival target must include an event or Status column")
        else:
            raise ValueError("Unsupported survival target format")

        # Validate at least two classes
        unique_events = set(np.asarray(events).astype(int).tolist())
        if len(unique_events) < 2:
            raise ValueError("survival stratification requires both events and censored samples")

        self.events = events

    def apply_kfold(self, split_num):
        """Apply stratified cross validation on event indicator."""
        skf = StratifiedKFold(n_splits=split_num, shuffle=True, random_state=42)
        for train_index, test_index in skf.split(self.X, self.events):
            X_train, X_test = self.X.iloc[train_index], self.X.iloc[test_index]
            Y_train, Y_test = self.Y.iloc[train_index], self.Y.iloc[test_index]
            yield (X_train, Y_train, X_test, Y_test)


def param_loader():
    # Load resampling strategy find manually
    param_file = os.path.join("../..", 'data', 'interim', "params.p")
    with open(param_file, "rb") as f:
        params = pickle.load(f)
    return params


class Result:
    """ The result saving class
    Parameters
    ----------
    train_ratio : the percentage of data used for training
        See main.py for more information.

    metric : The evaluation metric choosed for the training
        Mainly choose from "auroc" and "macro_f1"

    dataset : The name of the datased used for training

    Attributes
    ----------
    saved_file_path : The file path to save the results

    saved_result : The trained results
    """

    def __init__(self, train_ratio, metric, dataset, dataloader: DataLoader = None):
        saved_file_name = "{}_saved_pipe_{}_{}.json".format(dataset, metric, str(train_ratio))

        if dataloader is None:
            pass
        else:
            self.saved_file_path = os.path.join(dataloader.get_processed_data_folder(), saved_file_name)
        self.saved_result = {}

    def load_saved_result(self):
        # load data from file
        if os.path.isfile(self.saved_file_path):
            with open(self.saved_file_path, "r") as f:
                self.saved_result = json.load(f)
        else:
            self.saved_result = {}

    def is_in(self, pipe):
        # Check if pipe in result
        print(pipe)
        try:
            tmp = self.saved_result[pipe[0]]
            for i in range(1, len(pipe)):
                tmp = tmp[pipe[i]]
            return True
        except KeyError:
            return False

    def append(self, pipe, score):
        # append pipeline into result
        if len(pipe) == 1:
            automl = pipe[0]
            if automl not in self.saved_result:
                self.saved_result[automl] = score
        elif len(pipe) == 2:
            imp, hbd = pipe
            if imp not in self.saved_result:
                self.saved_result[imp] = {}
            if hbd not in self.saved_result[imp]:
                self.saved_result[imp][hbd] = score
        elif len(pipe) == 3:
            imp, rsp, clf = pipe
            if imp not in self.saved_result:
                self.saved_result[imp] = {}
            if rsp not in self.saved_result[imp]:
                self.saved_result[imp][rsp] = {}
            if clf not in self.saved_result[imp][rsp]:
                self.saved_result[imp][rsp][clf] = score
        else:
            raise ValueError("Length of pipe {} is not correct".format(pipe))
        self.save2file()


    def get(self, pipe: List):
        # get the result
        result = self.saved_result[pipe[0]]
        for i in range(1, len(pipe)):
            result = result[pipe[i]]
        return result
        # imp, rsp, clf = pipe
        # return self.saved_result[imp][rsp][clf]

    def save2file(self):
        # save result to json file
        if self.saved_result is None:
            raise ValueError("Please create saved_result first before save.")
        with open(self.saved_file_path, "w") as f:
            json.dump(self.saved_result, f, indent=4)


if __name__ == "__main__":
    fallback_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
    dataloader = DataLoader("nhanes.csv", host_data_root=fallback_root, container_data_root=fallback_root)
    _ = dataloader.train_loader()
    # print(a)

    # a = Result(1.0, "auroc", "test")
    # a.load_saved_result()
    # print(a.saved_result)
    # print(a.is_in(["automl"]))
    # print(a.is_in(["imp", "hbd"]))
    # print(a.is_in(["imp", "rsp", "clf"]))
    # print(a.get(["imp", "rsp", "clf"]))


    dataloader = DataLoader("nhanes.csv", host_data_root=fallback_root, container_data_root=fallback_root)
    data = dataloader.train_loader()
    find_categorical_columns(data)

    args = ArgsNamespace(
        dataset="my_data.csv",
        target="Outcome",
        T_model="rf",
        repeat=10,
        aggregation="categorical",
        missing="mean",
        n_splits=5,
        infor_method="nothing",
        resampling=True,
        resample_method="over",
        samratio=0.6,
        feature_importance="lime",
        grid=True,
        top_k=20,
        train_ratio=0.75,
        metric="macro_f1",
        rerun=True,
        exhaustive=True,
        host_data_root=fallback_root,
        container_data_root=fallback_root,
    )

    print(args.dataset)
