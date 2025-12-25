# Version: Fractal Model 25.09
# Named Sheets and Ranges

FM_RANGE_CONFIG = {
    'version': '25.09',
    'ranges': {
        'Settings': ['project_info'],
        'POI Limits': ['poi_limit_discharge', 'poi_limit_charge', 'clipped_energy', 'clipped_energy_8760_40', 'poi_limit_discharge_8760_40', 'poi_limit_charge_8760_40'],
        'Applications': ['throughput_fru', 'throughput_frd', 'throughput_spin', 'throughput_nspin', 'as_min_duration'],
        'Schedule': ['max_cycles_day', 'max_cycles_day_monthly', 'last_runtime', 'ancillary_limits', 'da_rt_split_enabled', 'da_split_ratio', 'starting_soc', 'annual_vom', 'annual_rte'],
        'Market Prices': ['price_ene_da_discharge', 'price_ene_da_charge', 'price_ene_rt_discharge', 'price_ene_rt_charge', 'price_cap_fru', 'price_cap_frd', 'price_cap_spin', 'price_cap_nspin'],
        'Battery': ['usable_energy_capacity'],
        'Dashboard': ['cod'],
    }
}


