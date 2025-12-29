
# readfile/v1.py

#- Imports -----------------------------------------------------------------------------------------

import h5py

from sklearn.mixture import GaussianMixture

from ...utils.debug import alert
from ...typing import (
    data_dict_t, SensorData
)

IGNORE_ERROR: str = "Field names only allowed for compound types"

#- Read Method -------------------------------------------------------------------------------------

def read_file(f: h5py.File) -> data_dict_t:
    try:
        models_dict: data_dict_t = {}

        for name in f.keys():
            gmm_group = f[name]

            if isinstance(gmm_group, h5py.Group):
                models_dict[name] = SensorData()

                models_dict[name].threshold = float(gmm_group['threshold'][()])
                models_dict[name].n_components = int(gmm_group['n_components'][()])
                models_dict[name].random_state = int(gmm_group['random_state'][()])

                for model_name in gmm_group.keys():
                    model_group = gmm_group[model_name]
                    model_instance = GaussianMixture()

                    model_instance.n_components = model_group['n_components'][()]
                    model_instance.weights_ = model_group['weights'][()]
                    model_instance.means_ = model_group['means'][()]
                    model_instance.covariances_ = model_group['covariances'][()]
                    model_instance.precisions_cholesky_ = model_group['precisions_cholesky'][()]

                    models_dict[name].models.append(model_instance)

    except Exception as e:
        if str(e) != IGNORE_ERROR: alert(f"Unable to parse file. {e}")

    return models_dict
