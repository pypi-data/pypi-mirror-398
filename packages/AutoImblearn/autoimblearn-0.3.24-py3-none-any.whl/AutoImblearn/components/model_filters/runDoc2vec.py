import os
from typing import Dict

import gensim
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from sklearn.metrics.pairwise import cosine_similarity
from sys import exit

from .filter_utils import read_txt_files_to_corpus, count_top_models, get_query, find_best_pipes, get_accuracy


# query = "This dataset is provided by the National Institute of Diabetes and Digestive and Kidney Diseases and focuses on predicting the onset of diabetes in a population of Pima Indian women. It contains 768 instances, each with 8 attributes, including factors such as plasma glucose concentration, diastolic blood pressure, and body mass index. The dataset's class distribution is imbalanced, with 268 positive cases and 500 negative cases. The missing ratio is 10%."

# data = "Resamplers"

class RunDoc2Vec:
    def __init__(self, documents, topn=3):
        self.documents = documents
        self.topn = topn

        # Tagging the documents (Each document must have a unique tag)
        self.tagged_data = [TaggedDocument(words=self.preprocess(doc), tags=[str(i)]) for i, doc in enumerate(documents)]
        self.model = Doc2Vec(vector_size=100, window=5, min_count=2, workers=4, epochs=40)

    def preprocess(self, doc):
        return gensim.utils.simple_preprocess(doc)

    def train(self, corpus, query):
        self.model.build_vocab(self.tagged_data)
        self.model.train(self.tagged_data, total_examples=self.model.corpus_count, epochs=self.model.epochs)
        # Function to infer a vector for a new document
        def get_doc_vector(doc):
            preprocessed_doc = self.preprocess(doc)
            return self.model.infer_vector(preprocessed_doc)

        # Compare similarity between two documents
        def compare_documents(doc1, doc2):
            vec1 = get_doc_vector(doc1)
            vec2 = get_doc_vector(doc2)

            # Calculate cosine similarity
            similarity = cosine_similarity([vec1], [vec2])
            return similarity[0][0]

        # Example: Comparing document similarity
        doc_names = list(corpus.keys())
        final_score = []
        for i, doc in enumerate(self.documents):
            similarity_score = compare_documents(doc, query)
            final_score.append([doc_names[i], similarity_score])

        final_score = sorted(final_score, key=lambda x: x[1], reverse=True)

        return [row[0] for row in final_score][:self.topn]

# model_folder_path = os.path.join("..", 'data', 'models', data)
#
# corpus = read_txt_files_to_corpus(model_folder_path)
#
# # Example training data
# documents = corpus.values()
#
# # Preprocess the documents (optional, depending on the use case)
# def preprocess(doc):
#     return gensim.utils.simple_preprocess(doc)
#
# # Tagging the documents (Each document must have a unique tag)
# tagged_data = [TaggedDocument(words=preprocess(doc), tags=[str(i)]) for i, doc in enumerate(documents)]
#
# # Initialize the Doc2Vec model
# model = Doc2Vec(vector_size=100, window=5, min_count=2, workers=4, epochs=40)
#
# # Build vocabulary from the corpus
# model.build_vocab(tagged_data)
#
# # Train the model
# model.train(tagged_data, total_examples=model.corpus_count, epochs=model.epochs)
#
#
# # Function to infer a vector for a new document
# def get_doc_vector(doc):
#     preprocessed_doc = preprocess(doc)
#     return model.infer_vector(preprocessed_doc)
#
#
# # Compare similarity between two documents
# def compare_documents(doc1, doc2):
#     vec1 = get_doc_vector(doc1)
#     vec2 = get_doc_vector(doc2)
#
#     # Calculate cosine similarity
#     similarity = cosine_similarity([vec1], [vec2])
#     return similarity[0][0]
#
#
# # Example: Comparing document similarity
# doc_names = list(corpus.keys())
# final_score = []
# for i, doc in enumerate(documents):
#     similarity_score = compare_documents(doc, query)
#     final_score.append([doc_names[i], similarity_score])
#
# final_score = sorted(final_score, key=lambda x: x[1], reverse=True)
# for key, value in final_score:
#     print(key, value)


def get_ranking(datasets, topn=3):
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
                results = {}
                ranker = RunDoc2Vec(corpus.values())
                model_result = ranker.train(corpus, query)
                method_result[model_type] = model_result
            dataset_result[strategy] = method_result

    return LLM_result


if __name__ == "__main__":
    # methods = ["combined", "sequential", "interactive"]
    # strategies = ["combined", "sequential"]
    # strategies = ["combined"]
    strategies = ["sequential"]

    datasets = ["Pima", "Ljubljana", "Wisconsin", "NHANES"]
    # datasets = ["NHANES"]

    # query = "This dataset is provided by the National Institute of Diabetes and Digestive and Kidney Diseases and focuses on predicting the onset of diabetes in a population of Pima Indian women. It contains 768 instances, each with 8 attributes, including factors such as plasma glucose concentration, diastolic blood pressure, and body mass index. The dataset's class distribution is imbalanced, with 268 positive cases and 500 negative cases. The missing value ratio is 10\% across all features."
    # query = "This dataset is provided by the National Institute of Diabetes and Digestive and Kidney Diseases and focuses on predicting the onset of diabetes in a population of Pima Indian women. It contains 768 instances, each with 8 attributes, including factors such as plasma glucose concentration, diastolic blood pressure, and body mass index. The dataset's class distribution is imbalanced, with 268 positive cases and 500 negative cases. The missing ratio is 10%."

    model_types = ["imputer", "resampler", "classifier"]
    metrics = ["auroc", "macro_f1"]
    # metrics = ["auroc"]

    # ground_truth Structure: {metric: {dataset: {model_type: top count}}}
    ground_truth = find_best_pipes(datasets, metrics)

    # formatted_data = json.dumps(ground_truth, indent=4)
    # pprint(formatted_data)

    # LLM_result Structure: {dataset: {strategy: {model_type: model ranking}}}
    LLM_result = get_ranking(datasets)

    LLM_accuracy = {strategy:
                        {dataset:
                             {metric: {} for metric in metrics} for dataset in datasets} for strategy in strategies}

    for metric in metrics:
        for strategy in strategies:
            for dataset in ground_truth[metric]:
                LLM_accuracy[strategy][dataset][metric] = get_accuracy(ground_truth[metric][dataset], LLM_result[dataset][strategy])

    print(LLM_accuracy)
