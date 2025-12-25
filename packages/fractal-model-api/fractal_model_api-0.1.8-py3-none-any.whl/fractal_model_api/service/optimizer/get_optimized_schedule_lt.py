import base64
import gzip
from dataclasses import dataclass
from typing import TypeAlias

from .base import OptimizerRequest
from ..base import RequestConfig
from ...json_utils import robust_json_dumps

GetOptimizedScheduleLTResponse: TypeAlias = dict


@dataclass
class GetOptimizedScheduleLTRequest(OptimizerRequest[GetOptimizedScheduleLTResponse]):
    request_config = RequestConfig(
        action="get_optimized_schedule_lt",
    )

    year_tuple: tuple[int, int]
    day_tuple: tuple[int, int]
    tolerance: float
    project_config: dict
    starting_soc: float
    energy_prices: dict
    capacity_prices: dict
    ancillary_throughput: dict
    poi_limits_discharge: list
    poi_limits_charge: list
    ancillary_limits: dict
    max_discharge_kWh: dict
    ene_participation_share: dict
    usable_energy_capacity: dict
    da_rt_split_enabled: dict
    as_min_SOC_capacity: dict
    clipped_energy: list
    annual_vom: dict
    annual_rte: dict

    def normalize(self):
        # some xls might return e.g. 3.0 here, but backend requires int for indexing
        # check it is integral first
        if float(self.project_config['Lookback period']).is_integer():
            self.project_config['Lookback period'] = int(self.project_config['Lookback period'])
        else:
            raise ValueError(f"Lookback period must be an integer value, got {self.project_config['Lookback period']}")

    def serialize(self):
        payload = self.as_json()
        raw_payload = robust_json_dumps(payload).encode()  # some decimals might be casted to float here
        gzip_payload = gzip.compress(raw_payload)
        data = base64.b64encode(gzip_payload).decode()
        return data
    
    def as_json(self):
        self.normalize()
        payload = super().serialize()
        return payload
