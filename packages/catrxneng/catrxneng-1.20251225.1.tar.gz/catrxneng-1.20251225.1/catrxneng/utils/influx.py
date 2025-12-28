import pandas as pd
import sys
from influxdb_client import InfluxDBClient, Point  # type: ignore
from influxdb_client.client.exceptions import InfluxDBError
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Time


class Influx:

    def __init__(self, url: str, org: str, bucket: str, measurement: str):
        self.url: str = url
        self.org: str = org
        self.bucket: str = bucket
        self.measurement: str = measurement
        self.raw_dataframes: list[pd.DataFrame]

    def write_data(
        self, data: pd.DataFrame | list[Point], token, data_descrip=None
    ) -> dict[str, bool | str]:
        with InfluxDBClient(url=self.url, token=token, org=self.org) as client:
            with client.write_api() as write_api:
                try:
                    write_api.write(bucket=self.bucket, org=self.org, record=data)
                    return {
                        "success": True,
                        "message": "Data successfully written to Influx.",
                    }
                except InfluxDBError as e:
                    status_code = (
                        e.response.status
                        if hasattr(e.response, "status")
                        else "Unknown"
                    )
                    sys.stdout.flush()
                    sys.stderr.flush()
                    return {
                        "success": False,
                        "message": f"Failed to write '{data_descrip}' to Influx (HTTP {status_code}): {e.message}",
                    }
                except Exception as e:
                    sys.stdout.flush()
                    sys.stderr.flush()
                    return {
                        "success": False,
                        "message": f"Failed to write '{data_descrip}' to Influx: {e}",
                    }

    def upload_dataframe(self, dataframe: pd.DataFrame, token: str):
        dataframe = dataframe.copy()
        dataframe.set_index("timestamp", inplace=True)
        return self.write_data(data=dataframe, token=token)

    def upload_points(
        self, points: list[Point], token: str, timestamp: str | int | None = None
    ) -> dict[str, bool | str]:
        return self.write_data(data=points, token=token, data_descrip=timestamp)

    def generate_query(
        self,
        tags: dict[str, dict[str, str | int | float]],
        start: "Time",
        end: "Time",
        dt_sec: int = 1,
    ):
        self.tags = tags
        tag_string = ""
        for value in tags.values():
            tag_string = tag_string + 'r["_field"] == "' + value["tag"] + '" or '  # type: ignore
        tag_string = tag_string[:-4]
        tag_string = tag_string + ")"

        query_start = (
            start.UTC.strftime("%Y-%m-%d") + "T" + start.UTC.strftime("%H:%M:%S") + "Z"
        )
        query_end = (
            end.UTC.strftime("%Y-%m-%d") + "T" + end.UTC.strftime("%H:%M:%S") + "Z"
        )

        self.query = """
        from(bucket: "BUCKET")
        |> range(start: START, stop: END)
        |> filter(fn: (r) => r["_measurement"] == "MEASUREMENT")
        |> filter(fn: (r) => TAGS
        |> aggregateWindow(every: SECONDSs, fn: last, createEmpty: false)
        |> map(fn: (r) => ({ r with _time: int(v: r._time) / 1000000000}))
        |> keep(columns: ["_time", "_field", "_value"])
        |> yield(name: "last")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        """

        self.query = self.query.replace("BUCKET", self.bucket)
        self.query = self.query.replace("MEASUREMENT", self.measurement)
        self.query = self.query.replace("START", query_start)
        self.query = self.query.replace("END", query_end)
        self.query = self.query.replace("TAGS", tag_string)
        self.query = self.query.replace("SECONDS", str(dt_sec))

    def request_data(self, token: str):
        timeout_min = 0.5
        max_retries = 3  # Maximum number of retries
        retry_count = 0

        while retry_count < max_retries:
            with InfluxDBClient(
                url=self.url,
                token=token,
                org=self.org,
                timeout=timeout_min * 60 * 1000,
            ) as client:
                try:
                    self.raw_dataframes = client.query_api().query_data_frame(
                        query=self.query
                    )
                    return  # Exit the method if the query is successful
                except ValueError:
                    # Handle the case where the query fails and needs adjustment
                    self.query = self.query.split("|> pivot")[0]
                    # retry_count += 1
                except Exception as e:
                    # Handle timeout or other exceptions
                    print(
                        f"Query failed with error: {e}. Retrying... ({retry_count + 1}/{max_retries})"
                    )
                    retry_count += 1

        raise TimeoutError("Failed to retrieve data after multiple retries.")

    def format_data(self):
        self.data = pd.concat(self.raw_dataframes, ignore_index=True)
        self.data = self.data[["_time", "_field", "_value"]]
        self.data.rename(
            columns={"_time": "timestamp", "_value": "value"}, inplace=True
        )
        self.data_dict = {
            key: self.data[self.data["_field"] == value["tag"]][["timestamp", "value"]]
            for key, value in self.tags.items()
        }
        for key, dataset in self.data_dict.items():
            try:
                config = self.tags[key]
                dataset.loc[:, "value"] = dataset["value"] * config.get("multiplier", 1)
                dataset.loc[:, "value"] = dataset["value"] + config.get("add", 0)
            except TypeError:
                pass
