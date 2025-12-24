from elasticsearch import Elasticsearch

from nlbone.config.settings import get_settings

setting = get_settings()


def get_es_client():
    es = Elasticsearch(
        setting.ELASTIC_PERCOLATE_URL,
        basic_auth=(setting.ELASTIC_PERCOLATE_USER, setting.ELASTIC_PERCOLATE_PASS.get_secret_value().strip()),
        http_compress=True,
        max_retries=2,
        retry_on_timeout=True,
    )
    return es
