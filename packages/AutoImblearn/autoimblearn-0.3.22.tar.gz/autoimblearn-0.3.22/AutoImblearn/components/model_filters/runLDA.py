from typing import Dict
from pprint import pprint
import json
# import re
import os
from sys import exit

from LDAword2vec import LDAword2vec

from .filter_utils import read_txt_files_to_corpus, count_top_models, get_query, find_best_pipes, get_accuracy
from ...processing.utils import Result


def get_ranking(datasets, model_types, topn=3):
    """ Get the ranking from model description and dataset description """
    LLM_result = {}
    for dataset in datasets:
        dataset_result = {}
        LLM_result[dataset] = dataset_result
        query = get_query(dataset)
        for strategy in strategies:
            method_result = {}
            for model_type in model_types:
                model_folder_path = os.path.join("../../../..", 'data', 'models', 'dps', strategy, model_type)
                index_folder_path = os.path.join("../../../..", 'data', 'processed', 'dps', strategy, model_type)
                corpus = read_txt_files_to_corpus(model_folder_path)

                ranker = LDAword2vec(index_folder_path, rerun=True)
                model_result = ranker.search(corpus=corpus, query=query, request_doc_num=3)
                method_result[model_type] = model_result
            dataset_result[strategy] = method_result

    return LLM_result

if __name__ == "__main__":
    # methods = ["combined", "sequential", "interactive"]
    # strategies = ["combined", "sequential"]
    strategies = ["combined"]
    # strategies = ["sequential"]

    datasets = ["Pima", "Ljubljana", "Wisconsin", "NHANES"]
    # datasets = ["NHANES"]

    model_types = ["imputer", "resampler", "classifier"]
    metrics = ["auroc", "macro_f1"]
    # metrics = ["auroc"]

    # ground_truth Structure: {dataset: {metric: {model_type: top count}}}
    ground_truth = find_best_pipes(datasets, metrics)

    # formatted_data = json.dumps(ground_truth, indent=4)
    # pprint(formatted_data)

    # LLM_result Structure: {dataset: {strategy: {model_type: model ranking}}}
    LLM_result = get_ranking(datasets, model_types)
    pprint(LLM_result)

    # Initiate LLM_accuracy structure
    LLM_accuracy = {
        strategy:
            {dataset:
                 {metric: {} for metric in metrics}
             for dataset in datasets}
        for strategy in strategies
    }

    for dataset in ground_truth:
        for metric in ground_truth[dataset]:
            for strategy in strategies:
                LLM_accuracy[strategy][dataset][metric] = get_accuracy(ground_truth[dataset][metric], LLM_result[dataset][strategy])

    pprint(LLM_accuracy)
