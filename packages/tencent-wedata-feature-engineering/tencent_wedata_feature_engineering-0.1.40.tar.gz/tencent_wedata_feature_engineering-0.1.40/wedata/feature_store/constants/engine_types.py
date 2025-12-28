from enum import Enum
import os


class EngineTypes(Enum):
    HIVE_ENGINE = "hive"
    ICEBERG_ENGINE = "iceberg"

    @classmethod
    def get_engine(cls, engine_name: str) -> 'EngineTypes':
        try:
            return cls(engine_name.lower())
        except ValueError:
            raise ValueError(f"Invalid engine type: {engine_name}. Supported engine types: {list(cls)}")


class CalculateEngineTypes(Enum):
    DLC = "dlc"
    EMR = "emr"

    @classmethod
    def get_calculate_engine(cls, engine_name: str) -> 'CalculateEngineTypes':
        try:
            return cls(engine_name.lower())
        except ValueError:
            raise ValueError(f"Invalid engine type: {engine_name}. Supported engine types: {list(cls)}")


def judge_engine_type() -> 'CalculateEngineTypes':
    if os.environ.get("DLC_REGION", ""):
        return CalculateEngineTypes.DLC
    else:
        return CalculateEngineTypes.EMR

