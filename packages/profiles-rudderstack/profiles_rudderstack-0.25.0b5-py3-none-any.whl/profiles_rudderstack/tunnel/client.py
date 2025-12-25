"""
Tunnel client module for calling Go RPC services from Python.

This module provides convenience functions for Python models to call back to Go
during the parsing/sanitization phase.
"""

from google.protobuf import json_format
from profiles_rudderstack.go_client import get_gorpc
from profiles_rudderstack.tunnel import tunnel_pb2


def sanitize_base(project_id: int, buildspec_ref: int, model_type: str):
	"""
	Call [Py → Go] RPC: WhtServicer.SanitizeBase() to get base BSN messages.

	This is called during the sanitize_buildspec phase to get base messages from
	CVBS.Sanitize() (e.g., LinkCohortFeature messages).

	Args:
		project_id: The project ID
		buildspec_ref: Reference to the Go PyNativeModelBuildSpec object
		model_type: The model type name

	Returns:
		List of BSN message dicts with keys:
			- update_type: str
			- destination: dict or None
			- payload: dict or None
			- context_entity_key: str
			- for_parent_project: bool
	"""
	gorpc = get_gorpc()

	# Create the request
	request = tunnel_pb2.SanitizeBaseRequest(
		project_id=project_id,
		buildspec_ref=buildspec_ref,
		model_type=model_type,
	)

	# Call Go RPC
	response = gorpc.SanitizeBase(request)

	# Convert protobuf messages to Python dicts
	messages = []
	for msg in response.messages:
		message_dict = {
			"update_type": msg.update_type,
			"destination": json_format.MessageToDict(msg.destination) if msg.destination else None,
			"payload": json_format.MessageToDict(msg.payload) if msg.payload else None,
			"context_entity_key": msg.context_entity_key,
			"for_parent_project": msg.for_parent_project,
		}
		messages.append(message_dict)

	return messages