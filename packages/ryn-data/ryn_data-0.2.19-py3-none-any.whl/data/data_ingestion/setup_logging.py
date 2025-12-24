import logging
import json
from elasticsearch import Elasticsearch
from ecs_logging import StdlibFormatter
import urllib3
import sys
LOG_LEVEL_MAP = {
    logging.CRITICAL: "CRITICAL",
    logging.ERROR: "ERROR",
    logging.WARNING: "WARNING",
    logging.INFO: "INFO",
    logging.DEBUG: "DEBUG",
}


# Suppress the InsecureRequestWarning from urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ElasticsearchHandler(logging.Handler):
    """
    Custom logging handler that sends logs to Elasticsearch.
    """
    def __init__(self, es_client, index_name):
        super().__init__()
        self.es_client = es_client
        self.index_name = index_name

    def emit(self, record):
        try:
            # self.format(record) uses the formatter attached to the handler
            log_entry_str = self.format(record)
            log_entry = json.loads(log_entry_str)
            
            self.es_client.index(index=self.index_name, document=log_entry)

        except Exception:
            sys.stderr.write(f"Failed to send log to Elasticsearch: {record.msg}\n")


def setup_logging(service_name: str, es_hosts: list, auth=None, verify_certs=False):
    """
    Configures dual logging:
      1. Console (human-readable)
      2. Elasticsearch (ECS JSON)
    """
    root_logger = logging.getLogger()
    # Ensure we don't add handlers multiple times
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.setLevel(logging.INFO)

    # 1. Console Handler (for simple, readable output)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    print("✅ Console logging configured.")

    # 2. Elasticsearch Handler (for structured, ECS-compliant JSON)
    try:
        es_client = Elasticsearch(
            hosts=es_hosts,
            basic_auth=auth,
            verify_certs=verify_certs,
        )
        
        # Check connection
        if not es_client.ping():
            raise ConnectionError("Could not connect to Elasticsearch.")

        es_handler = ElasticsearchHandler(
            es_client=es_client,
            index_name="ingestion-logs-main" # Or your desired index name
        )

        # Use the standard ECS formatter directly
        ecs_formatter = StdlibFormatter()
        
        # Attach the formatter to the handler
        es_handler.setFormatter(ecs_formatter)
        
        root_logger.addHandler(es_handler)
        print(f"✅ Elasticsearch logging configured for service '{service_name}'.")

    except Exception as e:
        print(f"⚠️ Could not configure Elasticsearch handler: {e}")

    # Prevent spammy logs from underlying libraries propagating to the root logger
    logging.getLogger("elasticsearch").propagate = False
    logging.getLogger("elastic_transport").propagate = False
    logging.getLogger("urllib3").propagate = False