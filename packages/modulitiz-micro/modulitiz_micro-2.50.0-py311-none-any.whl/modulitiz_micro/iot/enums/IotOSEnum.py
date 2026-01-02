from enum import StrEnum
from enum import unique


@unique
class IotOSEnum(StrEnum):
	"""
	Supported operating systems for Iot devices
	"""
	ESPURNA="ESPURNA"
	TASMOTA="TASMOTA"
	TIZS="TIZS"
