from dataclasses import dataclass

@dataclass
class DeviceDataPowerSensor:
	meter_status: float = 0.0
	meter_u: float = 0.0
	meter_i: float = 0.0
	
	active_power: float = 0.0
	"""Instant Kwh given to (+) or taken from (-) grid"""
	
	reactive_power: float = 0.0
	power_factor: float = 0.0
	grid_frequency: float = 0.0
	active_cap: float = 0.0
	reverse_active_cap: float = 0.0
	run_state: int = 0
	ab_u: float = 0.0
	bc_u: float = 0.0
	ca_u: float = 0.0
	b_u: float = 0.0
	c_u: float = 0.0
	b_i: float = 0.0
	c_i: float = 0.0
	forward_reactive_cap: float = 0.0
	reverse_reactive_cap: float = 0.0
	active_power_a: float = 0.0
	active_power_b: float = 0.0
	active_power_c: float = 0.0
	reactive_power_a: float = 0.0
	reactive_power_b: float = 0.0
	reactive_power_c: float = 0.0
	total_apparent_power: float = 0.0
	reverse_active_peak: float = 0.0
	reverse_active_power: float = 0.0
	reverse_active_valley: float = 0.0
	reverse_active_top: float = 0.0
	positive_active_peak: float = 0.0
	positive_active_power: float = 0.0
	positive_active_valley: float = 0.0
	positive_active_top: float = 0.0
	reverse_reactive_peak: float = 0.0
	reverse_reactive_power: float = 0.0
	reverse_reactive_valley: float = 0.0
	reverse_reactive_top: float = 0.0
	positive_reactive_peak: float = 0.0
	positive_reactive_power: float = 0.0
	positive_reactive_valley: float = 0.0
	positive_reactive_top: float = 0.0
