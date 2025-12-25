import os
import pickle
from collections import Counter
from typing import Dict

# from runDoc2vec import Doc2Vec
from ...processing.utils import DataLoader


def read_txt_files_to_corpus(model_folder_path):
    corpus = {}

    # Iterate over all files in the specified folder
    for filename in os.listdir(model_folder_path):
        # Check if the file has a .txt extension
        if filename.endswith('.txt'):
            # Get the file path
            file_path = os.path.join(model_folder_path, filename)

            # Open the file and read the content
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Remove the file extension (.txt) from the filename to use as the key
            file_key = os.path.splitext(filename)[0]

            # Add the content to the corpus with the filename as the key
            corpus[file_key] = content

    return corpus


def count_top_models(result_file):
    """ Find the top models from exhaustive search results """
    with open(result_file, 'rb') as f:
        data = pickle.load(f)

    # formatted_data = json.dumps(data, indent=4)
    # pprint(formatted_data)
    #
    #
    # try:
    #     data['MIRACLE'] = data['miracle']
    #     del data['miracle']
    #     data['MIWAE'] = data['miwae']
    #     del data['miwae']
    #     with open(result_file, "wb") as f:
    #         pickle.dump(data, f)
    # except KeyError:
    #     pass


    # Validate the value key pair
    # for imputer, resamplers in data.items():
    #     if not data[imputer]:
    #         del data[imputer]
    #         print("{} is deleted".format(imputer))
    #     for resampler, classifiers in resamplers.items():
    #         if not resamplers[resampler]:
    #             del resamplers[resampler]
    #             print("{} {} is deleted".format(imputer, resampler))
    #         for classifier, value in classifiers.items():
    #             if not classifiers[classifier]:
    #                 del classifiers[classifier]
    #                 print("{} {} {} is deleted".format(imputer, resampler, classifier))

    # Initialize counters
    classifier_counter = Counter()
    resampler_counter = Counter()
    imputer_counter = Counter()

    classifier_names = list(next(iter(next(iter(data.values())).values())).keys())

    # Fix imputer and resampler -> Find best classifier
    for imputer, resamplers in data.items():
        for resampler, classifiers in resamplers.items():
            best_classifier = max(classifiers, key=classifiers.get)
            classifier_counter[best_classifier] += 1

    # Fix imputer and classifier -> Find best resampler
    for imputer, resamplers in data.items():
        for classifier in classifier_names:
            best_resampler = max(resamplers, key=lambda r: resamplers[r][classifier])
            resampler_counter[best_resampler] += 1

    # Fix resampler and classifier -> Find best imputer
    for resampler in list(data.values())[0]:
        for classifier in classifier_names:
            best_imputer = max(data, key=lambda i: data[i][resampler][classifier])
            imputer_counter[best_imputer] += 1

    return {'imputer':imputer_counter, 'resampler': resampler_counter, 'classifier': classifier_counter}


def get_query(dataset_name):
    """get the dataset description based on dataset name"""
    dataset_dp_path = os.path.join("../../../..", "data", 'datasets', dataset_name + ".txt")
    if os.path.isfile(dataset_dp_path):
        with open(dataset_dp_path, "r") as f:
            query = f.read()
        return query
    else:
        raise ValueError(f"Description for dataset {dataset_name} doesn't exist in file path {dataset_dp_path}")


def find_best_pipes(dataset_names, metrics):
    # Find the best pipes for all datasets
    # result = {key: {dataset: {} for dataset in dataset_names} for key in metrics}
    result = {dataset: {key: {} for key in metrics} for dataset in dataset_names}

    for dataset in dataset_names:
        host_data_root_path = os.path.join("../../../..", 'data', 'processed', dataset)
        if not os.path.isdir(host_data_root_path):
            continue

        for file in os.listdir(host_data_root_path):
            if file.endswith(".p"):
                for metric in metrics:
                    if metric in file:
                        result_file = os.path.join(host_data_root_path, file)
                        result[dataset][metric] = count_top_models(result_file)
    return result


def get_accuracy(truth: Dict[str, Dict[str, int]], result: Dict):
    """ compare LLM result and ground truth

    : truth : [model type, top count]
    : result: [model type, model ranking]
     """
    accuracy = {}
    for model_type, counts in truth.items():
        total_count = 0
        hit_count = 0
        for model, count in counts.items():
            total_count += count
            if model in result[model_type]:
                hit_count += count
        accuracy[model_type] = hit_count/total_count

    return accuracy


if __name__ == "__main__":
    base_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "data"))
    container_root = os.getenv("CONTAINER_DATA_ROOT", base_root)
    data_loader = DataLoader(
        dataset="pima-indians-diabetes-missing.csv",
        host_data_root=base_root,
        container_data_root=container_root,
    )
    dp = data_loader.get_data_description("Pima")
    # model_filtering = ModelFiltering(dp)
    # print(model_filtering.get_topn("Imputers"))
