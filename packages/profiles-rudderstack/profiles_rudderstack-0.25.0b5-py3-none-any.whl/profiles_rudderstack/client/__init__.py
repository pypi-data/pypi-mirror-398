from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import importlib
from google.protobuf import json_format
from profiles_rudderstack.go_client import get_gorpc
import profiles_rudderstack.tunnel.tunnel_pb2 as tunnel
from profiles_rudderstack.logger import Logger

from profiles_rudderstack.client.client_base import BaseClient
from profiles_rudderstack.client.snowpark import SnowparkClient
from profiles_rudderstack.client.warehouse import WarehouseClient


def WhClient(project_id: int, common_props_material_ref: int) -> BaseClient:
    """Returns a warehouse client based on the type of warehouse configured in siteconfig

    Returns:
        IClient: Warehouse client object
    """
    gorpc = get_gorpc()
    logger = Logger("WhtWarehouseClient")
    # Warning: the common_props_material_ref should not be used to refer to a material only to access fields common to all materials
    creds_response: tunnel.GetWarehouseCredentialsResponse = gorpc.GetWarehouseCredentials(
        tunnel.GetWarehouseCredentialsRequest(project_id=project_id, material_ref=common_props_material_ref))

    creds = json_format.MessageToDict(creds_response.credentials)
    db = creds.get("dbname", "")
    schema = creds["schema"]
    wh_type = creds["type"]
    snowpark_enabled = False

    if wh_type == "snowflake":
        creds = populate_private_key_bytes(creds)
        try:
            importlib.import_module('snowflake.snowpark.session')
            snowpark_enabled = True
        except ImportError:
            logger.warn(
                "snowpark not installed, using warehouse connector instead")
    elif wh_type == "bigquery":
        db = creds.get("project_id", "")
    elif wh_type == "databricks":
        db = creds.get("catalog", "")

    if snowpark_enabled:
        return SnowparkClient(creds, db, wh_type, schema, project_id, common_props_material_ref)

    return WarehouseClient(creds, db, wh_type, schema, project_id, common_props_material_ref)


def populate_private_key_bytes(creds: dict) -> dict:
    new_creds = creds.copy()
    if creds.get('useKeyPairAuth', False):
        private_key = normalise_pem(creds["privateKey"])
        passphrase = creds.get("privateKeyPassphrase", None)
        p_key = serialization.load_pem_private_key(
            private_key.encode(), 
            password=(
                passphrase.encode() 
                if passphrase 
                else None
            ),
            backend=default_backend()
        )
        pkb = p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        new_creds['private_key'] = pkb

    return new_creds


def normalise_pem(content: str) -> str:
    """
    Normalises the PEM content by formatting it according to specific rules.

    Args:
        content (str): PEM content

    Returns:
        str: Formatted PEM content
    """
    # Remove all existing newline characters and replace them with a space
    formatted_content = content.replace("\n", " ")

    # Add a newline after specific BEGIN markers
    formatted_content = formatted_content.replace(
        "-----BEGIN CERTIFICATE-----", "-----BEGIN CERTIFICATE-----\n", 1)
    formatted_content = formatted_content.replace(
        "-----BEGIN RSA PRIVATE KEY-----", "-----BEGIN RSA PRIVATE KEY-----\n", 1)
    formatted_content = formatted_content.replace(
        "-----BEGIN ENCRYPTED PRIVATE KEY-----", "-----BEGIN ENCRYPTED PRIVATE KEY-----\n", 1)
    formatted_content = formatted_content.replace(
        "-----BEGIN PRIVATE KEY-----", "-----BEGIN PRIVATE KEY-----\n", 1)

    # Add a newline before and after specific END markers
    formatted_content = formatted_content.replace(
        "-----END CERTIFICATE-----", "\n-----END CERTIFICATE-----\n", 1)
    formatted_content = formatted_content.replace(
        "-----END RSA PRIVATE KEY-----", "\n-----END RSA PRIVATE KEY-----\n", 1)
    formatted_content = formatted_content.replace(
        "-----END ENCRYPTED PRIVATE KEY-----", "\n-----END ENCRYPTED PRIVATE KEY-----\n", 1)
    formatted_content = formatted_content.replace(
        "-----END PRIVATE KEY-----", "\n-----END PRIVATE KEY-----\n", 1)

    return formatted_content
