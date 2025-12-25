import asyncio
import base64
import json
import os
from typing import Any
from typing import overload

import httpx

from fractal_model_api.const import FM_RANGE_CONFIG
from fractal_model_api.reader import FMPrep
from fractal_model_api.reader import FMReader
from fractal_model_api.service.optimizer.get_optimized_schedule_lt import GetOptimizedScheduleLTRequest


class FractalModelAPIClient:
    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,

        range_config: dict | None = None,

        client_args: dict | None = None,

        service_endpoint: str = "https://modelapi.fractal.energy/api",
    ):
        self.__api_key = api_key or os.environ.get("FM_API_KEY")
        self.__api_secret = api_secret or os.environ.get("FM_API_SECRET")
        self.__service_endpoint = service_endpoint.rstrip('/') + '/'

        if not self.__api_key:
            raise ValueError("API key must be provided either via argument or FM_API_KEY environment variable")
        if not self.__api_secret:
            raise ValueError("API secret must be provided either via argument or FM_API_SECRET environment variable")

        client_args = client_args or {}

        client_args["headers"] = client_args.get("headers") or {}
        client_args["headers"]["Authorization"] = (
            f"Basic {base64.b64encode(f'{self.__api_key}:{self.__api_secret}'.encode()).decode()}"
        )

        client_args["timeout"] = client_args.get("timeout") or 30
        client_args["base_url"] = self.__service_endpoint

        self.__client = httpx.AsyncClient(**client_args)

        self.range_config = range_config
        if self.range_config is None:
            self.range_config = FM_RANGE_CONFIG

    async def verify_auth(self) -> None:
        try:
            resp = await self.__client.post(
                url="optimizer",
                json={
                    "action": "check_auth",
                    "payload": {},
                },
                timeout=10,
            )

            if resp.status_code in (401, 403):
                error_detail = None
                try:
                    error_detail = resp.json().get("error")
                except Exception:
                    pass

                if error_detail is None:
                    error_detail = resp.text

                if "invalid access level" in (error_detail or ""):
                    raise Exception(
                        "Authentication failed due to invalid access level. "
                        "Please ensure your API Key and API Secret have the necessary permissions."
                    )
                else:
                    raise Exception(f"Authentication failed. Details: {error_detail}")

            resp.raise_for_status()
        except Exception as exc:
            msg = str(exc)
            # Common DNS/host issues
            if "Name or service not known" in msg or "getaddrinfo failed" in msg:
                raise Exception(
                    "Failed to resolve service endpoint host. "
                    "Please check your network connection and the service endpoint URL."
                )
            elif isinstance(exc, httpx.HTTPStatusError):
                raise Exception(
                    "An error occurred during authentication check. "
                    "Please check your API Key, API Secret, and service endpoint URL."
                    " Details: " + exc.response.text
                ) from exc
            else:
                raise
        print("✅ User Authentication Successful")

    async def __get_simulation_result(self, payload: dict[int, GetOptimizedScheduleLTRequest]) -> dict:

        if not payload:
            return {}

        # Launch all single-year simulations concurrently.
        items = list(payload.items())
        gathered = asyncio.gather(
            *(self.__get_simulation_result_single_year(req) for _, req in items)
        )

        # Centralized progress logging while the async jobs are running.
        elapsed_seconds = 0
        while not gathered.done():
            await asyncio.sleep(5)
            elapsed_seconds += 5
            print(f"⏱️ Waiting for optimizer result, {elapsed_seconds} seconds passed")

        # Await completion (will re-raise any exception from the tasks).
        results = await gathered

        # Merge all per-call year dictionaries into a single result.
        merged: dict[int, Any] = {}
        for (year_key, _), result in zip(items, results):
            merged[year_key] = list(result.values())[0]

        return merged

    async def __get_simulation_result_single_year(self, payload: GetOptimizedScheduleLTRequest) -> dict:
        """Run long-running LT optimization via async API flow.

        This mirrors the JS `callLTDispatch` logic:
        - start async job
        - stream yearly payload parts via `add`
        - trigger `run`
        - poll `check` until `status == 'done'`
        - fetch all yearly `data` chunks and assemble result dict
        """

        # Extract the underlying (already compressed+base64) payload once.
        base_payload = payload.serialize()

        # Determine year range from the request object.
        year_start, year_end = payload.year_tuple

        optimizer_url = "optimizer"

        # 1) Start async job
        start_body = {
            "action": "async",
            "payload": {
                "async_action": "start",
                "async_payload": {
                    "action": "get_optimized_schedule_lt",
                },
            },
        }

        start_response = await self.__client.post(
            url=optimizer_url,
            json=start_body,
        )

        if not start_response.is_success:
            print("Start response status:", start_response.status_code)
            print("Start response time (UTC):", __import__("datetime").datetime.utcnow().isoformat())
            print("Start response headers:")
            for key, value in start_response.headers.items():
                print(f"  {key}: {value}")
        start_response.raise_for_status()

        start_response_dict = start_response.json()
        if "error" in start_response_dict:
            raise RuntimeError(start_response_dict["error"])

        # Async optimizer responses are plain objects (no top-level "data")
        async_id = start_response_dict.get("id") if isinstance(start_response_dict, dict) else None
        if not async_id:
            raise RuntimeError(
                f"Async optimizer start did not return an id, it returned: {json.dumps(start_response_dict)}")

        # 2) Send payload chunks per year using `add`.
        #
        # The JS client sends one payload per year. Here we currently
        # have a single compressed payload. If the backend expects
        # multiple chunks, the caller should provide the already-sliced
        # base64 strings instead of a single blob. For now we mirror the
        # structure but reuse the same payload for each year.
        for _year in range(year_start, year_end + 1):
            add_body = {
                "action": "async",
                "payload": {
                    "async_action": "add",
                    "async_payload": {
                        "id": async_id,
                        "data": base_payload,
                    },
                },
            }

            add_response = await self.__client.post(
                url=optimizer_url,
                json=add_body,
                timeout=30,
            )
            add_response.raise_for_status()
            add_response_dict = add_response.json()
            if "error" in add_response_dict:
                raise RuntimeError(add_response_dict["error"])

        # 3) Trigger run
        run_body = {
            "action": "async",
            "payload": {
                "async_action": "run",
                "async_payload": {
                    "id": async_id,
                },
            },
        }

        run_response = await self.__client.post(
            url=optimizer_url,
            json=run_body,
        )
        run_response.raise_for_status()
        run_response_dict = run_response.json()
        if "error" in run_response_dict:
            raise RuntimeError(run_response_dict["error"])

        # 4) Poll for completion
        async def _check_status() -> None:
            while True:
                check_body = {
                    "action": "async",
                    "payload": {
                        "async_action": "check",
                        "async_payload": {
                            "id": async_id,
                        },
                    },
                }

                check_response = await self.__client.post(
                    url=optimizer_url,
                    json=check_body,
                )
                check_response.raise_for_status()
                check_response_dict = check_response.json()
                if "error" in check_response_dict:
                    raise RuntimeError(check_response_dict["error"])

                # Expect a flat object like {"status": "...", "error": ...}
                status = check_response_dict.get("status") if isinstance(check_response_dict, dict) else None

                if not status:
                    raise RuntimeError("Async optimizer check failed: no status in response")

                if status == "done":
                    return

                # sleep 5 seconds between checks
                await asyncio.sleep(3)

        await _check_status()

        # 5) Fetch all year data chunks
        result: dict[int, Any] = {}
        num_years = year_end - year_start + 1
        for index in range(num_years):
            data_body = {
                "action": "async",
                "payload": {
                    "async_action": "data",
                    "async_payload": {
                        "id": async_id,
                        "index": index,
                    },
                },
            }

            data_response = await self.__client.post(
                url=optimizer_url,
                json=data_body,
            )
            data_response.raise_for_status()
            data_response_dict = data_response.json()
            if "error" in data_response_dict:
                raise RuntimeError(data_response_dict["error"])

            # Data endpoint returns the result itself (possibly with __version)
            data = data_response_dict

            if isinstance(data, dict) and "__version" in data:
                data = {k: v for k, v in data.items() if k != "__version"}

            result[year_start + index] = data

        return result

    @overload
    async def get_optimized_schedule_lt(
        self, *,
        file_path: str,
    ) -> dict:
        ...

    @overload
    async def get_optimized_schedule_lt(
        self, *,
        payload: dict[int, GetOptimizedScheduleLTRequest],
    ) -> dict:
        ...

    async def get_optimized_schedule_lt(
        self,
        *,
        file_path: str | None = None,
        payload: dict[int, GetOptimizedScheduleLTRequest] | None = None,
    ) -> dict:
        if (file_path is None) == (payload is None):
            raise ValueError("Either file_path or payload must be provided")

        await self.verify_auth()

        simulation_input = {}
        if file_path is not None:
            reader = FMReader(
                file_path=file_path,
                coerce_tabular_to_dataframe=False,
            )
            prep = FMPrep(reader.read_all())
            lambda_input = prep.get_full_input_for_lambda()

            simulation_input = {
                year_number: GetOptimizedScheduleLTRequest(
                    year_tuple=tuple(src["year_tuple"]),
                    day_tuple=tuple(int(d) for d in src["day_tuple"]),  # ensure ints
                    tolerance=src["tolerance"],
                    project_config=src["project_config"],
                    starting_soc=src["starting_SOC"],  # rename only
                    energy_prices=src["energy_prices"],
                    capacity_prices=src["capacity_prices"],
                    ancillary_throughput=src["ancillary_throughput"],
                    poi_limits_discharge=src["poi_limits_discharge"],
                    poi_limits_charge=src["poi_limits_charge"],
                    ancillary_limits=src["ancillary_limits"],
                    max_discharge_kWh=src["max_discharge_kWh"],
                    ene_participation_share=src["ene_participation_share"],
                    usable_energy_capacity=src["usable_energy_capacity"],
                    da_rt_split_enabled=src["da_rt_split_enabled"],
                    as_min_SOC_capacity=src["as_min_SOC_capacity"],
                    clipped_energy=src["clipped_energy"],
                    annual_vom=src["annual_vom"],
                    annual_rte=src["annual_rte"],
                ) for year_number, src in lambda_input.items()
            }
        elif payload is not None:
            simulation_input = payload

        simulation_result = await self.__get_simulation_result(simulation_input)

        return simulation_result
