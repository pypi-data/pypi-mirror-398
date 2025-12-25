from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import json
import contextlib

import pandas as pd
import xlwings as xw

from fractal_model_api.logger_config import get_logger
from fractal_model_api.const import FM_RANGE_CONFIG

logger = get_logger(__name__)


class FMReader:
    """FMReader class to read inputs from a Fractal Model Excel file (.xlsx or .xlsb)
    
    Features:
      - Resolves worksheet-scoped names first, then workbook-scoped.
      - Reads scalars, 1D lists, 2D tables (coerced to DataFrames), and discontiguous named ranges.
      - Provides utility methods to read all configured names or fetch a single name.
    """

    def __init__(self, file_path: str, *, coerce_tabular_to_dataframe: bool = True, visible: bool = False):
        self.file_path = file_path
        self.file_dir = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)
        self.file_ext = os.path.splitext(self.file_name)[1].lower()

        self.fm_range_config = FM_RANGE_CONFIG
        self.coerce_tabular_to_dataframe = coerce_tabular_to_dataframe
        self.visible = visible

        # Validate extension
        if self.file_ext in ('.xlsx', '.xlsb'):
            logger.info(f"Reading Fractal Model file {self.file_name}")
        else:
            msg = f"Incorrect file extension for {self.file_name}. Expected .xlsx or .xlsb. Got {self.file_ext}"
            logger.error(msg)
            raise ValueError(msg)

        # Validate config
        if not self.fm_range_config:
            logger.error("FM_RANGE_CONFIG is empty")
            raise ValueError("FM_RANGE_CONFIG is empty")

        if 'version' not in self.fm_range_config:
            logger.error("FM_RANGE_CONFIG does not have a version")
            raise ValueError("FM_RANGE_CONFIG does not have a version")

        if 'ranges' not in self.fm_range_config:
            logger.error("FM_RANGE_CONFIG does not have a ranges key")
            raise ValueError("FM_RANGE_CONFIG does not have a ranges key")

        if not isinstance(self.fm_range_config['ranges'], dict):
            logger.error("FM_RANGE_CONFIG['ranges'] must be a dict of sheet_name -> list[named_range]")
            raise ValueError("FM_RANGE_CONFIG['ranges'] must be a dict")

    # ------------------------------
    # Public API
    # ------------------------------

    def log_named_ranges(self) -> None:
        """Log the configured named ranges."""
        logger.info(f"Named Ranges in {self.file_name}:")
        for sheet_name, ranges in self.fm_range_config['ranges'].items():
            logger.info("--------------------------------")
            logger.info(f"Sheet: {sheet_name} has the following named ranges:")
            for range_name in ranges:
                logger.info(f"  - {range_name}")
        logger.info("--------------------------------")

    def read_all(self) -> Dict[str, Dict[str, Any]]:
        """Read all configured named ranges and return a nested dict:
           result[sheet][name] -> value (scalar | list | DataFrame | list-of-areas)
        """
        logger.info("Reading all FM named ranges...")
        with self._open_workbook() as (app, wb):
            out: Dict[str, Dict[str, Any]] = {}
            for sheet_name, names in self.fm_range_config['ranges'].items():
                sheet_dict: Dict[str, Any] = {}
                for nm in names:
                    try:
                        rng = self._resolve_named_range(wb, sheet_name, nm)
                        val = self._read_range_value(rng)
                        val = self._maybe_coerce(val)
                        sheet_dict[nm] = val
                        logger.debug(f"Read {sheet_name}!{nm} OK")
                    except Exception as e:
                        logger.exception(f"Failed reading named range {sheet_name}!{nm}: {e}")
                        sheet_dict[nm] = None
                out[sheet_name] = sheet_dict
            logger.info("Completed reading all FM named ranges.")
            return out

    def read_sheet(self, sheet_name: str) -> Dict[str, Any]:
        """Read all configured names for a single sheet."""
        if sheet_name not in self.fm_range_config['ranges']:
            raise KeyError(f"Sheet '{sheet_name}' not found in FM_RANGE_CONFIG['ranges']")
        logger.info(f"Reading sheet '{sheet_name}' named ranges...")
        with self._open_workbook() as (app, wb):
            sheet_dict: Dict[str, Any] = {}
            for nm in self.fm_range_config['ranges'][sheet_name]:
                try:
                    rng = self._resolve_named_range(wb, sheet_name, nm)
                    val = self._read_range_value(rng)
                    val = self._maybe_coerce(val)
                    sheet_dict[nm] = val
                except Exception as e:
                    logger.exception(f"Failed reading named range {sheet_name}!{nm}: {e}")
                    sheet_dict[nm] = None
            return sheet_dict

    def get_value(self, sheet_name: str, name: str) -> Any:
        """Read a single configured named range."""
        if sheet_name not in self.fm_range_config['ranges'] or name not in self.fm_range_config['ranges'][sheet_name]:
            raise KeyError(f"{sheet_name}!{name} not in FM_RANGE_CONFIG")
        logger.info(f"Reading single named range {sheet_name}!{name}")
        with self._open_workbook() as (app, wb):
            rng = self._resolve_named_range(wb, sheet_name, name)
            val = self._read_range_value(rng)
            return self._maybe_coerce(val)

    def get_addresses(self, sheet_name: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """Return addresses (A1) for configured names. Useful for debugging."""
        with self._open_workbook() as (app, wb):
            if sheet_name is None:
                targets = self.fm_range_config['ranges'].items()
            else:
                if sheet_name not in self.fm_range_config['ranges']:
                    raise KeyError(f"Sheet '{sheet_name}' not in FM_RANGE_CONFIG['ranges']")
                targets = [(sheet_name, self.fm_range_config['ranges'][sheet_name])]

            out: Dict[str, Dict[str, str]] = {}
            for sht, names in targets:
                d: Dict[str, str] = {}
                for nm in names:
                    try:
                        rng = self._resolve_named_range(wb, sht, nm)
                        d[nm] = f"{rng.sheet.name}!{rng.address}"
                    except Exception as e:
                        d[nm] = f"<unresolved: {e}>"
                out[sht] = d
            return out

    def to_json(self, data: Dict[str, Dict[str, Any]]) -> str:
        """Serialize nested dict to JSON, handling DataFrames."""
        def _default(o: Any):
            if isinstance(o, pd.DataFrame):
                return {
                    "__type__": "dataframe",
                    "columns": list(o.columns),
                    "data": o.where(pd.notna(o), None).values.tolist(),
                }
            return str(o)
        return json.dumps(data, default=_default)

    # ------------------------------
    # Internals
    # ------------------------------

    @contextlib.contextmanager
    def _open_workbook(self):
        """Context manager: open Excel app+workbook and clean up reliably."""
        app = xw.App(visible=self.visible, add_book=False)
        app.display_alerts = False
        app.screen_updating = False
        wb = None
        try:
            wb = app.books.open(self.file_path)
            yield app, wb
        finally:
            with contextlib.suppress(Exception):
                if wb is not None:
                    wb.close()
            # kill ensures no ghost process on Windows/macOS
            with contextlib.suppress(Exception):
                app.kill()

    @staticmethod
    def _read_range_value(rng: xw.main.Range) -> Any:
        """Return scalar, list/2D list, or list-of-areas for discontiguous ranges."""
        # Discontiguous?
        try:
            areas = rng.api.Areas
            if areas.Count > 1:
                out = []
                for i in range(1, areas.Count + 1):
                    area = xw.Range(areas.Item(i))
                    out.append(area.value)
                return out
        except Exception:
            pass
        return rng.value

    def _maybe_coerce(self, val: Any) -> Any:
        """Coerce 2D lists to DataFrame if enabled. If discontiguous (list of areas), coerce each area."""
        if not self.coerce_tabular_to_dataframe:
            return val

        def _to_df(v: Any) -> Any:
            if not isinstance(v, list):
                return v
            if not any(isinstance(r, list) for r in v):  # 1D
                return v
            # Normalize jagged rows
            rows: List[List[Any]] = []
            max_len = max(len(r) if isinstance(r, list) else 1 for r in v)
            for r in v:
                if isinstance(r, list):
                    rows.append(r + [None] * (max_len - len(r)))
                else:
                    rows.append([r] + [None] * (max_len - 1))
            first = rows[0]
            looks_header = all((isinstance(c, str) or c is None) for c in first) and len(set(first)) == len(first)
            return pd.DataFrame(rows[1:], columns=first) if looks_header else pd.DataFrame(rows)

        # Discontiguous: list of areas
        if isinstance(val, list) and any(isinstance(v, list) and any(isinstance(x, list) for x in (v if isinstance(v, list) else [])) for v in val):
            return [_to_df(v) for v in val]
        return _to_df(val)

    @staticmethod
    def _resolve_named_range(book: xw.Book, sheet_name: str, range_name: str) -> xw.main.Range:
        """Resolve a named range, preferring sheet scope then workbook scope."""
        # Try sheet-scoped first
        with contextlib.suppress(Exception):
            sht = book.sheets[sheet_name]
            with contextlib.suppress(Exception):
                return sht.names[range_name].refers_to_range
        # Fallback to workbook scope
        with contextlib.suppress(Exception):
            return book.names[range_name].refers_to_range
        raise KeyError(f"Named range not found: {sheet_name}!{range_name}")

    # Optional: diagnostic helper to list all names Excel sees
    def list_all_excel_names(self) -> List[str]:
        """Return all workbook-level name strings (useful for debugging mismatches)."""
        with self._open_workbook() as (app, wb):
            names = []
            for nm in wb.names:
                with contextlib.suppress(Exception):
                    names.append(nm.name)
            # Also include sheet-scoped names
            for sht in wb.sheets:
                with contextlib.suppress(Exception):
                    for nm in sht.names:
                        names.append(f"{sht.name}!{nm.name}")
            return names


class FMPrep:
    '''FMPrep class to prepare data for Fractal Model lambda
    
    Features:
      - Prepares read by FMReader to be sent to Fractal Model lambda
     '''

    def __init__(self, fm_data: dict):
        self.fm_data = fm_data

    #--------------------------------
    # Public Methods
    #--------------------------------

    def get_full_input_for_lambda(self) -> dict:
        '''Get full input for Fractal Model lambda for all the years'''
        logger.info("Preparing full input for Fractal Model lambda...")

        full_input_dict = {}
        
        # Project Info
        project_config = self._build_project_info_dict(self.fm_data)
        start_year = int(project_config['Year start'])
        end_year = int(project_config['Year end'])
        
        # Get annual input for all the years
        for year in range(start_year, end_year + 1):
            annual_input_dict = self.get_annual_input_for_lambda(year)
            full_input_dict[year] = annual_input_dict
        
        return full_input_dict
  

    def get_annual_input_for_lambda(self, year_index: int, multi_year_data: bool = False) -> dict:
        '''Get annual inputs for Fractal Model lambda
        year_index: int, year index
        multi_year_data: bool, if True, return multi-year data, otherwise return single year data
        '''
        fm_reader_data = self.fm_data
        annual_dict = {}

        #--------------------------------
        # Project Info
        annual_dict['project_config'] = self._build_project_info_dict(fm_reader_data)
        annual_dict['year_tuple'] = [1, 1]
        annual_dict['day_tuple'] = [annual_dict['project_config']['Day start'], annual_dict['project_config']['Day end']]
        annual_dict['starting_SOC'] = annual_dict['project_config']['Starting SOC']
        annual_dict['tolerance'] = annual_dict['project_config']['Tolerance']

        #--------------------------------
        # POI Limits
        annual_dict['poi_limits_discharge'] = self._convert_list_to_model_list(fm_reader_data['POI Limits']['poi_limit_discharge'])
        annual_dict['poi_limits_charge'] = self._convert_list_to_model_list(fm_reader_data['POI Limits']['poi_limit_charge'])
        
        annual_dict['clipped_energy'] = self._convert_list_to_model_list(fm_reader_data['POI Limits']['clipped_energy'])

        #--------------------------------
        # Ancillary Services
        ancillary_names = ['FRU', 'FRD', 'Spin', 'Non-spin']
        
        annual_dict['ancillary_limits'] = self._get_setting_by_yr_and_key(fm_reader_data['Schedule']['ancillary_limits'], year_index, ancillary_names)
        
        annual_dict['ancillary_throughput'] = {}
        annual_dict['ancillary_throughput']['FRU'] = self._convert_list_to_model_list(fm_reader_data['Applications']['throughput_fru'])
        annual_dict['ancillary_throughput']['FRD'] = self._convert_list_to_model_list(fm_reader_data['Applications']['throughput_frd'])
        annual_dict['ancillary_throughput']['Spin'] = self._convert_list_to_model_list(fm_reader_data['Applications']['throughput_spin'])
        annual_dict['ancillary_throughput']['Non-spin'] = self._convert_list_to_model_list(fm_reader_data['Applications']['throughput_nspin'])

        annual_dict['as_min_SOC_capacity'] = {}
        for index, service_name in enumerate(ancillary_names):
            annual_dict['as_min_SOC_capacity'][service_name] = self._convert_list_to_model_list(fm_reader_data['Applications']['as_min_duration'])[index]

        annual_dict['capacity_prices'] = {}
        annual_dict['capacity_prices']['FRU'] = self._get_yr_from_multi_col_2D_list(data=fm_reader_data['Market Prices']['price_cap_fru'], col_index=year_index, row_index=None)
        annual_dict['capacity_prices']['FRD'] = self._get_yr_from_multi_col_2D_list(data=fm_reader_data['Market Prices']['price_cap_frd'], col_index=year_index, row_index=None)
        annual_dict['capacity_prices']['Spin'] = self._get_yr_from_multi_col_2D_list(data=fm_reader_data['Market Prices']['price_cap_spin'], col_index=year_index, row_index=None)
        annual_dict['capacity_prices']['Non-spin'] = self._get_yr_from_multi_col_2D_list(data=fm_reader_data['Market Prices']['price_cap_nspin'], col_index=year_index, row_index=None)

        #--------------------------------
        # Energy Services
        annual_dict['energy_prices'] = {}
        annual_dict['energy_prices']['DA'] = self._get_yr_from_multi_col_2D_list(data=fm_reader_data['Market Prices']['price_ene_da_discharge'], col_index=year_index, row_index=None)
        annual_dict['energy_prices']['RT'] = self._get_yr_from_multi_col_2D_list(data=fm_reader_data['Market Prices']['price_ene_rt_discharge'], col_index=year_index, row_index=None)

        #--------------------------------
        # Dispatch Settings
        annual_dict['annual_rte'] = {}
        annual_dict['annual_rte']['Annual RTE'] = self._convert_list_to_model_list(fm_reader_data['Schedule']['annual_rte'])[year_index]

        annual_dict['annual_vom'] = {}
        annual_dict['annual_vom']['Annual VOM']= self._convert_list_to_model_list(fm_reader_data['Schedule']['annual_vom'])[year_index]

        annual_dict['usable_energy_capacity'] = {}
        annual_dict['usable_energy_capacity']['Usable energy capacity'] = self._convert_list_to_model_list(fm_reader_data['Battery']['usable_energy_capacity'])[year_index]

        annual_dict['ene_participation_share'] = {}
        annual_dict['ene_participation_share']['DA'] = self._convert_list_to_model_list(fm_reader_data['Schedule']['da_split_ratio'])[year_index]

        annual_dict['da_rt_split_enabled'] = {}
        annual_dict['da_rt_split_enabled']['DA-RT split'] = self._convert_list_to_model_list(fm_reader_data['Schedule']['da_rt_split_enabled'])[year_index]

        monthly_cycles = [monthly_cycle[0] for monthly_cycle in self._get_yr_from_multi_col_2D_list(data=fm_reader_data['Schedule']['max_cycles_day_monthly'], col_index=year_index, row_index=None)]
        annual_dict['max_discharge_kWh'] = self._get_daily_max_energy_discharge(annual_dict['usable_energy_capacity']['Usable energy capacity'][0], monthly_cycles)
        
        return annual_dict

    
    #--------------------------------
    # Internal Methods
    #--------------------------------

    def _convert_to_params_dict(self, data: pd.DataFrame) -> dict:
        data = data.dropna()
        data_dict = dict(zip(data[0], data[1]))
        return data_dict

    def _convert_1D_data_to_df(self, data: list, header_row: bool = False) -> pd.DataFrame:
        
        if not data:
            return pd.DataFrame()
        
        if len(data) == 0:
            return pd.DataFrame()
        
        if header_row:
            data = data[1:]
            df = pd.DataFrame(data)
            df.columns = data[0]
        
        else:
            df = pd.DataFrame(data)
        
        return df

    def _get_yr_from_multi_col_2D_list(self, data: list, col_index: int, row_index: int) -> list:
        '''Get a list of single year values from a multi-year 2D list
        For col_index: Use year for yearly data and service index for combined service data with 1 year only
        For row_index: Use hour for hourly data, month for monthly data, service index for combined service data
        When row_index is None, return all rows in a single list'''

        if not data:
            return []
        
        if len(data) == 0:
            return []

        if len(data[0]) == 0:
            return []
        
        if row_index is None:
            # since xlwings might read as Decimal from xls, we enforce float (API/json is not adopted to Decimal)
            return [[float(data[i][col_index])] for i in range(len(data))]
        
        return [float(data[row_index][col_index])]
            
        return to_ret

    def _get_setting_by_yr_and_key(self, data: list, year_index: int, key_list: list) -> dict:
        '''Get a list of values from a multi-year 2D list by year and key
        key_list is a list of keys to be extracted from the 2D list'''
        
        data_dict = {}

        if not data:
            return data_dict
        
        if len(data) == 0:
            return data_dict
        
        if len(data[0]) == 0:
            return data_dict

        if key_list is None:
            return data_dict
        
        if len(key_list) == 0:
            return data_dict
        
        if year_index is None:
            return data_dict

        for index, key in enumerate(key_list):
            data_dict[key] = self._get_yr_from_multi_col_2D_list(data=data, col_index=year_index, row_index=index)
        
        return data_dict

    def _convert_list_to_model_list(self, data: list) -> list:
        '''Convert a list to a model list'''
        return [[float(data[i])] for i in range(len(data))]

    def _build_project_info_dict(self, data: dict) -> dict:
        '''Build a dictionary of project info'''
        df_project_info = self._convert_1D_data_to_df(data['Settings']['project_info'])
        dict_project_info = self._convert_to_params_dict(df_project_info)
        
        return dict_project_info

    def _get_daily_max_energy_discharge(self, usable_energy_capacity: float, max_cycles_by_month: list) -> list:
        '''Get a 365x1 list of daily max energy discharge, where each element is the max energy discharge X cycles for the month'''
        num_days_by_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        daily_max_energy_discharge = []
        for month, num_days in enumerate(num_days_by_month):
            for day in range(num_days):
                daily_max_energy_discharge.append(usable_energy_capacity * max_cycles_by_month[month])
        return daily_max_energy_discharge

