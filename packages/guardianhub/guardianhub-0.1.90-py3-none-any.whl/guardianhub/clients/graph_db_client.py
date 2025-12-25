# services/clients/neo4j_client.py (New File/Class)
import datetime
import json
from typing import Dict, Any, Optional

import httpx
import yaml  # Must be imported for YAML output
# Import all model classes to make them available at the package level
from guardianhub.models.template.suggestion import TemplateSchemaSuggestion

from guardianhub.config.settings import settings
from guardianhub import get_logger
logger = get_logger(__name__)

# NOTE: The actual driver must be injected/managed by the calling service (doc-template service)
class GraphDBClient:
    def __init__(self, base_url: str, poll_interval: int = 5, poll_timeout: int = 300):
        """
        Initializes the Paperless client.
        """
        self.api_url = base_url.rstrip('/')
        self.api_token = settings.endpoints.GRAPH_DB_URL
        self.headers = {
            "Accept": "application/json",
        }
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout

        # Initialize the persistent httpx client here.
        # DO NOT use it in an 'async with' block in methods, or it will be closed.
        self.client = httpx.AsyncClient(headers=self.headers, base_url=self.api_url, timeout=self.poll_timeout + 60)
        logger.info("PaperlessClient initialized for URL: %s", self.api_url)

    async def save_document_template(self, template: TemplateSchemaSuggestion) -> bool:
        """
        Creates a new DocumentTemplate node and links it to the Doc-Template Service
        node by submitting a YAML payload to the ingestion endpoint.
        """

        # 1. Prepare Node Properties
        template_properties = {
            "template_id": template.template_id,
            "document_type": template.document_type,
            "template_name": template.template_name,
            "required_keywords": template.required_keywords,
            # The ingestion endpoint requires the schema to be stored as a property value.
            # We must serialize the JSON schema dictionary to a string/YAML-safe string.
            "json_schema_str": json.dumps(template.json_schema)
        }

        # 2. Construct the Graph Ingestion Dictionary (The YAML Payload Structure)
        ingestion_payload = {
            "nodes": [
                {
                    "type": "DocumentTemplate",
                    "properties": template_properties
                }
            ],
            "relationships": [
                {
                    "from": {
                        "type": "PlatformService",
                        "property": "name",
                        "value": "doc-template-service"  # Matching the service node created at startup
                    },
                    "to": {
                        "type": "DocumentTemplate",
                        "property": "template_id",
                        "value": template.template_id
                    },
                    "type": "MANAGES_TEMPLATE",
                    "properties": {
                        "link_date": datetime.datetime.now()
                    }
                }
            ]
        }

        # 3. Convert to YAML
        yaml_payload = yaml.dump(ingestion_payload, sort_keys=False)

        # 4. POST to the ingestion endpoint
        try:
            response = await self.client.post(
                "/ingest-yaml-schema",
                content=yaml_payload,
                headers={'Content-Type': 'application/x-yaml'},
                timeout=30.0
            )
            response.raise_for_status()

            response_json = response.json()
            if response_json.get("status") == "success":
                logger.info(f"✅ Template {template.template_id} successfully persisted via YAML ingestion.")
                return True
            else:
                logger.error(
                    f"Graph DB Service returned non-success status for template {template.template_id}: {response_json.get('message')}")
                return False

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error during YAML ingestion (Template {template.template_id}). Status: {e.response.status_code}. Detail: {e.response.text}",
                exc_info=True
            )
            return False
        except Exception as e:
            logger.error(f"Failed to ingest template YAML for {template.template_id}: {e}", exc_info=True)
            return False

        # services/clients/neo4j_client.py (Corrected get_template_by_id)

    async def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the properties of a DocumentTemplate node by its ID via the
        /query-cypher endpoint.
        """

        # 1. Define the Cypher query
        cypher_query = """
        MATCH (t:DocumentTemplate {template_id: $template_id})
        RETURN properties(t) as template
        """

        # 2. Prepare the JSON payload for the read endpoint
        payload = {
            "query": cypher_query,
            "parameters": {"template_id": template_id}
        }

        try:
            # 🛠️ FIX: Target the correct read endpoint and send JSON payload
            response = await self.client.post(
                "/query-cypher", # The correct read endpoint
                json=payload,    # Send as JSON
                timeout=30.0
            )
            response.raise_for_status()

            response_json = response.json()

            if response_json.get("status") == "success" and response_json.get("results"):
                # The result is typically a list of dicts from Cypher execution
                record = response_json["results"][0]
                template_data = record["template"]

                # Convert the stored JSON Schema string back to a dictionary
                template_data['json_schema'] = json.loads(template_data.pop('json_schema_str'))

                logger.info(f"✅ Template {template_id} successfully retrieved from GraphDB.")
                return template_data
            else:
                logger.info(f"Template {template_id} not found or query failed: {response_json.get('message')}")
                return None

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error retrieving template {template_id}. Status: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve template {template_id} from Neo4j: {e}", exc_info=True)
            return None
