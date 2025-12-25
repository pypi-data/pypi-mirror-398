KIND_TEMPLATES = {
    "ids": ["default"],
    "protocol": ["default"],
    "task-script": ["default"],
    "tetraflow": ["spark"],
    "data-app": ["streamlit", "react"],
    "schema": ["default"],
}

KINDS = sorted(KIND_TEMPLATES.keys())

TEMPLATES = sorted(
    set([template for templates in KIND_TEMPLATES.values() for template in templates])
)

KIND_DEFAULTS = {kind: templates[0] for kind, templates in KIND_TEMPLATES.items()}
