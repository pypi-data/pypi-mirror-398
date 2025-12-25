from typing import Any, SupportsFloat

type KonicStepStateObservation = tuple[Any, SupportsFloat, bool, bool, dict[str, Any]]

type KonicResetStateObservation = tuple[Any, dict[str, Any]]
