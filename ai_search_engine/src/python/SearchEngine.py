from fetch_teams.oef_core_protocol import query_pb2
from utils.src.python.Logging import has_logger
import gensim.downloader
from nltk.tokenize import word_tokenize
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
import numpy as np
import scipy.spatial.distance as distance
from dap_api.src.python.DapInterface import DapInterface, DapBadUpdateRow
from dap_api.src.protos.dap_update_pb2 import DapUpdate
from dap_api.src.python.DapQuery import DapQuery


class SearchEngine(DapInterface):
    @has_logger
    def __init__(self, name="SearchEngineStorage", structure={"dm_store": {"data_model": "dm", "embedding": "embedding"}}):
        self._storage = {}
        nltk.download('stopwords')
        nltk.download('punkt')
        nltk.download('wordnet')
        self._stop_words = set(stopwords.words('english'))
        self._w2v = gensim.downloader.load("glove-wiki-gigaword-50") #"word2vec-google-news-300")
        self._porter = PorterStemmer()
        self._wnl = WordNetLemmatizer()
        self._encoding_dim = 50

        self.store = {}
        self.name = name
        self.structure_pb = structure

        self.tablenames = []
        self.structure = {}

        for table_name, fields in self.structure_pb.items():
            self.tablenames.append(table_name)
            for field_name, field_type in fields.items():
                self.structure.setdefault(table_name, {}).setdefault(field_name, {})['type'] = field_type

    def _string_to_vec(self, description: str):
        #print("Encode desc: ", description)
        if description.find("_") > -1:
            description = description.replace("_", " ")
        tokens = word_tokenize(description)
        words = [word.lower() for word in tokens if word.isalpha()]
        #print("Words: ", words)
        no_stops = [word for word in words if word not in self._stop_words]
        final = []
        for w in no_stops:
            w1 = self._wnl.lemmatize(w)
            if w1.endswith('e'):
                final.append(w1)
            else:
                final.append(self._porter.stem(w))
        #print("Final: ", final)
        feature_vec = np.zeros((self._encoding_dim,))
        counter = 0
        for w in final:
            try:
                feature_vec = np.add(self._w2v[w], feature_vec)
                counter += 1
            except KeyError as e:
                self.log.warning("Failed to embed word: %s" % w)
        if counter > 0:
            feature_vec = np.divide(feature_vec, float(counter))
        return feature_vec

    def _dm_to_vec(self, data: query_pb2.Query.DataModel):
        avg_feature = np.zeros((self._encoding_dim,))
        for attr in data.attributes:
            avg_feature = np.add(avg_feature, self._string_to_vec(attr.description))
            avg_feature = np.add(avg_feature, self._string_to_vec(attr.name))
        avg_feature = np.add(avg_feature, self._string_to_vec(data.name))
        avg_feature = np.add(avg_feature, self._string_to_vec(data.description))
        return avg_feature

    def add(self, data: query_pb2.Query.DataModel):
        avg_feature = self._dm_to_vec(data)
        self._storage[avg_feature.tobytes()] = data

    def search(self, query: str) -> str:
        encoded = self._string_to_vec(query)
        response = ""
        for key in self._storage:
            data = self._storage[key]
            score = distance.cosine(np.frombuffer(key), encoded)
            response += str(score) + " -> " + data.name
        return response

    def describe(self):
        result = dap_description_pb2.DapDescription()
        result.name = self.name

        for table_name, fields in self.structure_pb.items():
            result_table = result.table.add()
            result_table.name = table_name
            for field_name, field_type in fields.items():
                result_field = result_table.field.add()
                result_field.name = field_name
                result_field.type = field_type
        return result

    # (TODO): introduce service ID, right now only one service / agent is supported
    def update(self, update_data: DapUpdate):
        for upd in update_data.update:
            k, v = "dm", udp.value.dm
            if upd.tablename not in self.structure:
                raise DapBadUpdateRow("No such table", upd.tablename, upd.key.agent_name, upd.key.core_uri,
                                      upd.fieldname, k)

            if upd.fieldname not in self.structure[upd.tablename]:
                raise DapBadUpdateRow("No such field", upd.tablename, upd.key.agent_name, upd.key.core_uri,
                                      upd.fieldname, k)

            if self.structure[upd.tablename][upd.fieldname]['type'] != k:
                raise DapBadUpdateRow("Bad type", upd.tablename, upd.key.agent_name, upd.key.core_uri, upd.fieldname, k)

            vec = self._dm_to_vec(v)
            for core_uri in upd.key.core_uri:
                row = self.store.setdefault(upd.tablename, {}).setdefault(
                    (upd.key.agent_name, core_uri), {}
                )
                row[upd.fieldname] = v
                row["embedding"] = vec

    def query(self, query: DapQuery, agents=None):
        enc_query = np.zeros((self._encoding_dim,))
        if query.data_model:
            enc_query = np.add(enc_query, self._dm_to_vec(query.data_model))
        if query.description:
            enc_query = np.add(enc_query, self._string_to_vec(query.description))
        if not np.any(enc_query):
            return
        table = "dm_store"
        score_threshold = 0.2
        result = []
        for key, data in self.store[table].items():
            dist = distance.cosine(data["embedding"], enc_query)
            if dist < score_threshold:
                result.append((key, dist))
        ordered = sorted(result, key=lambda x: x[1], reverse=True)
        return ordered
