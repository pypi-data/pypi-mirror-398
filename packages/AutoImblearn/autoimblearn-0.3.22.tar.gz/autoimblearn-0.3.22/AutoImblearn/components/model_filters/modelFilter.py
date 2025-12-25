import os

from ...processing.utils import DataLoader
from .filter_utils import read_txt_files_to_corpus
from .runDoc2vec import RunDoc2Vec


class ModelFiltering:
    """Run model filtering before running in AutoML system"""
    def __init__(self,
                 data_description,
                 container_data_root,  # The root path of the data folder
                 method='lda',
                 strategy='combined',
                 ):
        self.data_description = data_description
        self.method = method
        self.strategy = strategy
        self.container_data_root=container_data_root

        # self.rankers = {"lda": }

    def get_topn(self, model_type, topn=3):
        """ Get the ranking from model description and dataset description """
        from LDAword2vec import LDAword2vec

        model_folder_path = os.path.join(self.container_data_root, 'models', 'dps', self.strategy, model_type)
        index_folder_path = os.path.join(self.container_data_root, 'processed', 'dps', self.strategy, model_type)
        corpus = read_txt_files_to_corpus(model_folder_path)

        ranker = LDAword2vec(index_folder_path, rerun=True)
        model_result = ranker.search(corpus=corpus, query=self.data_description, request_doc_num=topn)

        return model_result

    # def get_topn(self, model_type: str, request_doc_num=3):
    #     data_location = DataLoader()
    #     corpus = read_txt_files_to_corpus(os.path.join(data_location.get_models_dp_folder(), model_type))
    #     print(corpus)
    #
    #     ranker = LDAword2vec(data_location.get_interim_data_folder(), rerun=True)
    #     models = ranker.search(corpus=corpus, query=self.data_description, request_doc_num=request_doc_num)
    #     return models
