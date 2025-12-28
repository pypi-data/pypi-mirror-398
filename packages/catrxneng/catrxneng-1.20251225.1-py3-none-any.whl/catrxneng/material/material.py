from typing import Any


class Material:
    project_id: str
    common_name: str
    lab_notebook_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "material_class_name": type(self).__name__,
            "common_name": self.common_name,
            "project_id": self.project_id,
        }
