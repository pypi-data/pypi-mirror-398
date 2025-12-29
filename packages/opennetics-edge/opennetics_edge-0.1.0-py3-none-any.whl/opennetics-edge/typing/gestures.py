
# typing/gesturefile.py

#- Imports -----------------------------------------------------------------------------------------

from dataclasses import dataclass

from sklearn.mixture import GaussianMixture

from ..utils import defaults


#- Data Classes ------------------------------------------------------------------------------------

# Mutable container for model configuration and inputs used when creating gestures.
class SensorData:
    models: list[GaussianMixture] = []
    threshold:  float = defaults.MODEL_THRESHOLD
    random_state: int = defaults.MODEL_RANDOM_STATE
    n_components: int = defaults.MODEL_N_COMPONENTS


# Immutable container for gesture checker
@dataclass(frozen=True)
class GestureMatch:
    value: float
    status: bool


#- Aliases -----------------------------------------------------------------------------------------

data_dict_t = dict[str, SensorData]

