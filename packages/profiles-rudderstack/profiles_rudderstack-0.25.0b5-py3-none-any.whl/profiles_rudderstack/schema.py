ContractBuildSpecSchema = {
    "properties": {
        "contract": {
            "type": "object",
            "properties": {
                "is_optional": {"type": "boolean"},
                "is_event_stream": {"type": "boolean"},
                "with_entity_ids": {"type": "array", "items": {"type": "string"}},
                "with_columns": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "datatype": {"type": "string"},
                            "type": {"type": "string"},
                            "is_optional": {"type": "boolean", "default": False},
                        },
                        "required": ["name"],
                        "additionalProperties": False,
                    },
                },
            },
            "additionalProperties": False,
        }
    },
    "required": [],
}

EntityKeyBuildSpecSchema = {
    "properties": {"entity_key": {"type": "string"}},
    "required": ["entity_key"],
}

EntityCohortBuildSpecSchema = {
    "properties": {"entity_cohort": {"type": "string"}},
}

TimeGrainBuildSpecSchema = {
    "properties": {
        "time_grain": {
            "type": "string",
            "enum": ["tick", "10minutes", "hour", "day", "week", "month", "year"],
        }
    },
    "required": ["time_grain"],
}

MaterializationBuildSpecSchema = {
    "properties": {
        "materialization": {
            "type": "object",
            "properties": {
                "output_type": {"type": "string"},
                "run_type": {"type": "string"},
                "requested_enable_status": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    "required": [],
}

EntityIdsBuildSpecSchema = {
    "properties": {
        "ids": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "select": {"type": "string"},
                    "type": {"type": "string"},
                    "entity": {"type": "string"},
                    "as_col": {"type": "string"},
                    "to_default_stitcher": {"type": "boolean"},
                },
                "required": ["select", "type", "entity"],
                "additionalProperties": False,
            },
        }
    },
    "required": [],
}

FeatureDetailsBuildSpecSchema = {
    "properties": {
        "features": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
    },
    "required": [],
}
