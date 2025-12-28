from typing import Optional
import requests

from ..utils import Time


class Unit:
    tags: dict[str, dict[str, str | int | float]]
    bucket: str
    org: str
    measurement: str

    def __init__(self, unit_class_name: str):
        self.unit_class_name = unit_class_name

    def populate_attributes_from_emp(self, host: str):
        url = f"{host}/api/get_unit_data"
        params = {"unit_class_name": self.unit_class_name}
        response = requests.get(url, json=params).json()
        for key, value in response.items():
            setattr(self, key, value)

    def last_expt_number(self, host: str) -> int:
        url = f"{host}/api/get_last_expt_number_on_unit"
        params = {"unit_class_name": self.unit_class_name}
        response = requests.get(url, json=params).json()
        return response["last_expt_number_on_unit"]

    def last_expt_end(self, host: str) -> Optional[Time]:
        url = f"{host}/api/last_expt_end"
        params = {"unit_class_name": self.unit_class_name}
        try:
            response = requests.get(url, json=params)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            last_expt_end_UET = response.json()["last_expt_end_UET"]
            if last_expt_end_UET is None:
                return None
            return Time(UET=last_expt_end_UET)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch last experiment end time: {e}")
