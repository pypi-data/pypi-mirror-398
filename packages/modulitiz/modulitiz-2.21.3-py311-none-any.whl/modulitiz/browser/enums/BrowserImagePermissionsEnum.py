from enum import IntEnum
from enum import auto
from enum import unique


@unique
class BrowserImagePermissionsEnum(IntEnum):
	"""
	Permessi immagini:
	1 - Allow all
	2 - Block all
	3 - Block only 3rd party
	"""
	ALLOW=auto()
	BLOCK=auto()
	BLOCK_ONLY_3RD_PARTY=auto()
