from dataclasses import dataclass

@dataclass
class DeviceDataBattery:
	battery_status: float = 0.0
	max_charge_power: float = 0.0
	max_discharge_power: float = 0.0
	
	ch_discharge_power: float = 0.0
	"""Instant Kwh given to (+) or taken from (-) battery"""
	
	busbar_u: float = 0.0
	
	battery_soc: float = 0.0
	"""Percentage of battery charge remaining"""
	
	battery_soh: float = 0.0
	ch_discharge_model: float = 0.0
	charge_cap: float = 0.0
	discharge_cap: float = 0.0
	rated_capacity: float = 0.0
	run_state: int = 0
