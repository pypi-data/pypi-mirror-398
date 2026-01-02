from enum import IntEnum
from enum import unique


@unique
class BrowserProxyTypeEnum(IntEnum):
	MANUAL=1
	SYSTEM=5
