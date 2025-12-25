import json
import re
import os
import pandas as pd
import numpy as np
from typing import List
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor

from basedir import basedir
from athenah_ai.logger import logger


def nginx_log_df_parser(request_string):
    matches = re.match(
        r"(\S+) - - \[(\S+ \S+)\] \"(\S+) (\S+) (\S+)\" (\S+) (\S+) \"(\S+)\" \"(.+)\"",
        request_string,
    )
    request_dict = {
        "ip_address": matches.group(1),
        "timestamp": matches.group(2),
        "method": matches.group(3),
        "url": matches.group(4),
        "protocol": matches.group(5),
        "status_code": matches.group(6),
        "response_length": matches.group(7),
        "referer": matches.group(8),
        "user_agent": matches.group(9),
    }
    return request_dict


class MLClient(object):

    model: RandomForestRegressor
    features: RandomForestRegressor
    storage_type: str = "local"  # local or gcs
    id: str = ""
    dir: str = ""
    name: str = ""
    version: str = ""

    def __init__(
        cls,
        storage_type: str,
        id: str,
        dir: str,
        name: str,
        version: str = "v1",
        features: List[str] = [],
    ) -> None:
        cls.label_encoder = LabelEncoder()
        cls.features = features
        cls.storage_type = storage_type
        cls.id = id
        cls.dir = dir
        cls.name = name
        cls.version = version
        cls.dist_path: str = os.path.join(basedir, "dist")
        cls.base_path: str = os.path.join(basedir, dir)
        cls.name_path: str = os.path.join(cls.base_path, f"{cls.name}-ml")
        os.makedirs(cls.base_path, exist_ok=True)
        os.makedirs(cls.name_path, exist_ok=True)
        # with open(os.path.join(cls.name_path, "data.json"), "w") as f:
        #     f.write("[]")
        pass

    def load_data(cls):
        path = os.path.join(cls.name_path, "data.txt")
        with open(path, "r") as f:
            json_array = []
            with open(path, "r") as f:
                for line in f:
                    json_array.append(nginx_log_df_parser(line))
            json_data_str = json.dumps(json_array)
            from io import StringIO

            logger.debug(json_data_str)
            return pd.read_json(StringIO(json_data_str), orient="records")

    def prepare_training(cls, df: pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy()

        # Add a column to calculate number of API calls within a 5 minute period
        # df["api_calls"] = df.apply(
        #     lambda row: get_num_api_calls(df, row["timestamp"], row["ip_address"]),
        #     axis=1,
        # )

        df["label"] = df["ip_address"].apply(lambda x: 1 if x == "172.70.54.90" else 0)
        # df["label"] = df["user_agent"].apply(
        #     lambda x: 1 if x == "Python/3.10 websockets/10.3" else 0
        # )
        return df

    def prepare_invoke(cls, test_data: pd.DataFrame) -> pd.DataFrame:
        # test_data["api_calls"] = test_data.apply(
        #     lambda row: get_num_api_calls(df_copy, row["timestamp"], row["ip_address"]),
        #     axis=1,
        # )

        for feature in cls.features:
            test_data[feature] = np.searchsorted(
                cls.label_encoder_values[feature], test_data[feature]
            )

        return test_data

    def build(cls, data_df: pd.DataFrame):
        df = cls.prepare_training(data_df)
        cls.label_encoder_values = {}
        for feature in cls.features:
            df[feature] = cls.label_encoder.fit_transform(df[feature])
            cls.label_encoder_values[feature] = cls.label_encoder.classes_

        # print(df.head())
        X_train, X_test, y_train, y_test = train_test_split(
            df.drop("label", axis=1), df["label"], test_size=0.2, random_state=42
        )
        logger.debug(f"X_train: {X_train}")
        logger.debug(f"X_test: {X_test}")
        logger.debug(f"y_train: {y_train}")
        logger.debug(f"y_test: {y_test}")

        cls.model = RandomForestRegressor(n_estimators=10, random_state=42)
        cls.model.fit(X_train, y_train)

    def invoke(cls, query: pd.DataFrame):
        query = cls.prepare_invoke(query)
        prediction = cls.model.predict(query)
        print(prediction)
        return prediction[0]
