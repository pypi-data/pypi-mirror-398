import os
import time
from datetime import datetime
from typing import cast

import logfire
import requests
from dotenv import load_dotenv
from typesense.client import Client as TypesenseClient
from typesense.collection import Collection

load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_MODEL_EXPENSIVE = "text-embedding-3-large"
EMBEDDING_CONTEXT_MAX_LENGTH = 8191
EMBEDDING_ENCODING = "cl100k_base"
# For the model name to typesense's namming convention
EMBEDDING_MODEL_TYPESENSE_NAME = f"openai/{EMBEDDING_MODEL}"
EXPENSIVE_EMBEDDING_MODEL_TYPESENSE_NAME = f"openai/{EMBEDDING_MODEL_EXPENSIVE}"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class TypesenseManager:
    """
    This class is a client to interact with the Typesense search engine server (deployed in InfraV2).
    You can then is the client outside of the class to interact with the Typesense server.

    It also take care of creating the collections if they don't exist.
    ! Please maintain the schemas in the same file as the TypesenseManager class. !

    :attribute typesense_url: The typesense server URL.
    :attribute client: The typesense client object to interact with the typesense server.
    :attribute collection_nace_codes: The nace_codes collection object.
    :attribute collection_companies_names: The companies_names collection object.
    :attribute collection_descriptions: The descriptions collection object. (embedded desc for all websites & NACEs)
    """

    def __init__(
        self,
        host: str = os.getenv("TYPESENSE_HOST", ""),
        port: int = int(os.getenv("TYPESENSE_PORT", 443)),  # Default port is 443 for HTTPS
        api_key: str = os.getenv("TYPESENSE_API_KEY", ""),
        protocol: str = "https",
        pretty_logging: bool = False,
    ):
        """
        :param host: Typesense's server host
        :param port: Typesense's server port
        :param api_key: Typesense's API key
        :param protocol: Typesense's server protocol (http or https)
        """
        self.typesense_url = f"https://{host}"
        self.client: TypesenseClient = TypesenseClient(
            {
                "api_key": api_key,
                "nodes": [{"host": host, "port": port, "protocol": protocol}],
                "connection_timeout_seconds": 60 * 20,  # 20 minutes max
            }
        )

        # 1. Check the API's health
        self._check_server_heatlh()
        # 2. Create collections if they don't exist
        self._create_collections()

        # Expose collections
        self.collection_nace_codes: Collection = cast(Collection, self.client.collections["nace_codes"])
        self.collection_companies_names: Collection = cast(Collection, self.client.collections["companies_names"])
        self.collection_descriptions: Collection = cast(Collection, self.client.collections["descriptions"])
        logfire.debug("Typesense Manager ready!")

    def _check_server_heatlh(self) -> None:
        """Check if typesense server is up and running."""
        response = requests.get(f"{self.typesense_url}/health")
        response.raise_for_status()
        if not response.json()["ok"]:
            raise Exception("Typesense is not running!")
        logfire.info("Typesense server is up and running!")

    def _create_collections(self) -> None:
        """Create a Typesense schema so MongoDB's collection can be interpreted."""
        collections = self.client.collections.retrieve()
        existing_collections_name = set([col["name"] for col in collections])
        for collection in [naces_collection_schema, companies_names_collection_schema, descriptions_schema]:
            if collection["name"] not in existing_collections_name:
                self.client.collections.create(collection)  # type: ignore
                logfire.warning(f"Typesense collection {collection['name']} created!")
                continue
            logfire.debug(f"Typesense collection {collection['name']} already exists!")


def datetime_to_unix_timestamp(date: datetime) -> int:
    """
    Convert datetime to unix timestamp as int.

    This is the format that Typesense is expecting for datetime data.
    See: https://typesense.org/docs/guide/tips-for-searching-common-types-of-data.html#searching-for-null-or-empty-values
    """
    return int(time.mktime(date.timetuple()))


def unix_timestamp_to_datetime(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp)


# Define the schemas for each collection

# Contains description for all companies with a website or a NACE code
descriptions_schema = {
    "name": "descriptions",
    "enable_nested_fields": True,
    "fields": [
        # ---- Imported data ----
        {"optional": False, "name": "id", "type": "string"},
        {"optional": False, "name": "description_short", "type": "string"},
        {"optional": False, "name": "description_long", "type": "string"},
        {"optional": False, "name": "source", "type": "string"},
        {"optional": False, "name": "source_value", "type": "string"},
        # ---- Embeddings ----
        {
            "optional": True,
            "name": "description_short_embedding",
            "type": "float[]",
            "embed": {
                "from": ["description_short"],
                "model_config": {"model_name": EXPENSIVE_EMBEDDING_MODEL_TYPESENSE_NAME, "api_key": OPENAI_API_KEY},
            },
        },
        {
            "optional": True,
            "name": "description_long_embedding",
            "type": "float[]",
            "embed": {
                "from": ["description_long"],
                "model_config": {"model_name": EXPENSIVE_EMBEDDING_MODEL_TYPESENSE_NAME, "api_key": OPENAI_API_KEY},
            },
        },
    ],
}

# Contains all the naces codes, their labels and translations
naces_collection_schema = {
    "name": "nace_codes",
    "enable_nested_fields": True,
    "fields": [
        # ---- Imported data ----
        {"optional": False, "name": "country", "type": "string"},
        {"optional": False, "name": "level", "type": "int32"},
        {"optional": False, "name": "code", "type": "string"},
        {"optional": False, "name": "section_label", "type": "string"},
        {"optional": False, "name": "section_code", "type": "string"},
        {"optional": False, "name": "label_en", "type": "string"},
        {"optional": False, "name": "label_en_extended", "type": "string"},
        {"optional": True, "name": "label_fr", "type": "string"},
        {"optional": True, "name": "label_fr_extended", "type": "string"},
        {"optional": True, "name": "label_nl", "type": "string"},
        {"optional": True, "name": "label_nl_extended", "type": "string"},
        # ---- Embeddings ----
        {
            "optional": True,
            "name": "label_en_embedding",
            "type": "float[]",
            "embed": {
                "from": ["label_en"],
                "model_config": {"model_name": EMBEDDING_MODEL_TYPESENSE_NAME, "api_key": OPENAI_API_KEY},
            },
        },
        {
            "optional": True,
            "name": "label_en_extended_embedding",
            "type": "float[]",
            "embed": {
                "from": ["label_en_extended"],
                "model_config": {"model_name": EMBEDDING_MODEL_TYPESENSE_NAME, "api_key": OPENAI_API_KEY},
            },
        },
        {
            "optional": True,
            "name": "label_fr_embedding",
            "type": "float[]",
            "embed": {
                "from": ["label_fr"],
                "model_config": {"model_name": EMBEDDING_MODEL_TYPESENSE_NAME, "api_key": OPENAI_API_KEY},
            },
        },
        {
            "optional": True,
            "name": "label_fr_extended_embedding",
            "type": "float[]",
            "embed": {
                "from": ["label_fr_extended"],
                "model_config": {"model_name": EMBEDDING_MODEL_TYPESENSE_NAME, "api_key": OPENAI_API_KEY},
            },
        },
        {
            "optional": True,
            "name": "label_nl_embedding",
            "type": "float[]",
            "embed": {
                "from": ["label_nl"],
                "model_config": {"model_name": EMBEDDING_MODEL_TYPESENSE_NAME, "api_key": OPENAI_API_KEY},
            },
        },
        {
            "optional": True,
            "name": "label_nl_extended_embedding",
            "type": "float[]",
            "embed": {
                "from": ["label_nl_extended"],
                "model_config": {"model_name": EMBEDDING_MODEL_TYPESENSE_NAME, "api_key": OPENAI_API_KEY},
            },
        },
    ],
}

# Contains all the companies and establishment names for name matching puprose
companies_names_collection_schema = {
    "name": "companies_names",
    "enable_nested_fields": True,
    "fields": [
        {"optional": False, "name": "_id", "type": "string"},
        {"optional": True, "name": "name", "type": "string"},
        {"optional": True, "name": "name_fr", "type": "string"},
        {"optional": True, "name": "name_nl", "type": "string"},
        {"optional": True, "name": "name_de", "type": "string"},
        {"optional": True, "name": "website", "type": "string"},
        {"optional": True, "name": "establishments.name", "type": "string[]"},
        {"optional": True, "name": "establishments.name_fr", "type": "string[]"},
        {"optional": True, "name": "establishments.name_nl", "type": "string[]"},
        {"optional": True, "name": "establishments.name_de", "type": "string[]"},
    ],
}


if __name__ == "__main__":
    typesense_manager = TypesenseManager()
    print("OK!")
