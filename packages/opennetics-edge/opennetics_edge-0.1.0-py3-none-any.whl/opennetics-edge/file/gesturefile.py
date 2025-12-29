
# file/gesturefile.py

#- Imports -----------------------------------------------------------------------------------------

import h5py
from typing import Optional

import numpy as np
from sklearn.mixture import GaussianMixture

from .version_reads import version_readers, GESTURE_VERSION
from ..utils.debug import alert
from ..typing import (
    GestureMatch, SensorData,
    data_dict_t, numeric_t,
)


#- GestureFile Class -------------------------------------------------------------------------------

class GestureFile:

    # Initialise the instance with default values
    def __init__(self, filename: str):
        self._filename: str = filename          # .ges file path
        self._batchsize: int = 0                # raw data array length for the gesture
        self._gesture_data: data_dict_t = {}    # GM models and model params


    #- Getter/Setter -------------------------------------------------------------------------------

    @property
    def gesture_data(self) -> data_dict_t: return self._gesture_data

    @property
    def batchsize(self) -> int: return self._batchsize


    # Get saved parameters in ModelParameters type
    def parameters(self, label: str) -> dict[str, numeric_t]:
        return {
            "n_components": self._gesture_data[label].n_components,
            "random_state": self._gesture_data[label].random_state,
            "threshold": self._gesture_data[label].threshold
        }


    # Get names of all sensors in the record
    def keys(self) -> list[str]: return list(self._gesture_data.keys())


    # Set parameters, either override individual, or override all with ModelParameters arg
    def set_parameters(self,
            label: str,
            n_components: Optional[int] = None,
            random_state: Optional[int] = None,
            threshold:Optional[float] = None
        ) -> None:
        if n_components is not None:
            assert n_components > 0, "n_components should be above 0"
            self._gesture_data[label].n_components = n_components

        if random_state is not None:
            assert random_state > 1, "random_state should be above 1"
            self._gesture_data[label].random_state = random_state

        if threshold is not None:
            self._gesture_data[label].threshold = threshold


    #- Public Methods ------------------------------------------------------------------------------

    # Create mew gesture file
    def create(self) -> bool:
        try:
            with h5py.File(self._filename, 'w') as f:
                f.create_dataset('version', data=GESTURE_VERSION)

        except Exception as e:
            alert(f"Unable to create file: {e}")
            return False

        return True


    # Append to the record
    def append_reading(self, label: str, model: list[GaussianMixture]) -> bool:
        try:
            #========================================
            # batch_size update
            #========================================
            # update _batchsize to be the biggest model size
            # _batchsize is used to create window of sensor data to see if it got this gesture
            if len(model) > self._batchsize: self._batchsize = len(model)

            #========================================
            # append data
            #========================================
            # create new dict key if label isn't existing key
            if label not in self._gesture_data.keys():
                self._gesture_data[label] = SensorData()

            # add data to model.key's value
            self._gesture_data[label].models += model

        except Exception as e:
            alert(f"Unable to append readings: {e}")
            return False

        return True


    # Add models for a sensor to the file
    def write(self, override: bool = False) -> bool:
        #========================================
        # file selection
        #========================================
        # don't bother if no data is there to save
        if self._gesture_data == {}:
            return False

        # create new file if override, else open to append
        if override: self.create()

        #========================================
        # add data
        #========================================
        try:
            with h5py.File(self._filename, 'a') as f:
                f.create_dataset('batchsize', data=self._batchsize)

                for group in self._gesture_data.keys():
                    #========================================
                    # group selection
                    #========================================
                    if group in f:
                        # use existing group and add new data to it
                        gmm_group = f[group]
                        model_start_index = len(gmm_group) # number of GM models already saved
                    else:
                        # create a new group for each sensor
                        gmm_group = f.create_group(group)
                        model_start_index = 0

                    #========================================
                    # global model parameters save
                    #========================================
                    # reduce repetition of same code syntax
                    def _user_variables(label: str, value: numeric_t):
                        if label in gmm_group.keys():
                            # update value
                            gmm_group[label][...] = value
                        else:
                            # create new tag with the value
                            gmm_group.create_dataset(label, data=value)

                    _user_variables('n_components', self._gesture_data[group].n_components)
                    _user_variables('random_state', self._gesture_data[group].random_state)
                    _user_variables('threshold', self._gesture_data[group].threshold)

                    #========================================
                    # save GM internal parameter as a group
                    #========================================
                    for i, data in enumerate(self._gesture_data[group].models):
                        model = gmm_group.create_group(f'model_{model_start_index + i}')
                        model.create_dataset('weights', data=data.weights_)
                        model.create_dataset('means', data=data.means_)
                        model.create_dataset('covariances', data=data.covariances_)
                        model.create_dataset('precisions_cholesky', data=data.precisions_cholesky_)
                        model.create_dataset('n_components', data=data.n_components)

        except Exception as e:
            alert(f"Unable to write readings: {e}")
            return False

        return True


    # Read the gesture file; deserialise it
    def read(self) -> bool:
        try:
            with h5py.File(self._filename, 'r') as f:
                #========================================
                # batchsize
                #========================================
                saved_batchsize = f['batchsize'][()].decode('utf-8')
                # save bigger value as _batchsize
                if saved_batchsize > self._batchsize: self._batchsize = saved_batchsize

                #========================================
                # file_version
                #========================================
                file_version = f['version'][()].decode('utf-8')
                print(f"file version = {file_version}")

                if file_version in version_readers:
                    self._gesture_data = version_readers[file_version](f)

                else:
                    raise ValueError(f"Unsupported file version: {file_version}")

        #========================================
        # exception case
        #========================================
        except Exception as e:
            alert(f"Invalid Gesture File. {e}")
            return False

        return True


    # Check if the readings trigger the gesture
    def has_gesture(self,
        timestamps: list[float], readings: dict[str, list[float]]
    ) -> tuple[bool, dict[str, GestureMatch]]:
        Result: dict[str, GestureMatch] = {}

        if self._gesture_data == {}:
            # print line where .is_gesture() was called, backtrack=2
            alert("Models aren't generated. Read a file.", backtrack=2)
            return False, Result

        for sensor in readings.keys():
            if len(timestamps) != len(readings[sensor]):
                alert("timestamps and readings should be of the same size.", backtrack=2)
                return False, Result

            if sensor not in self._gesture_data.keys():
                alert(f"\"{sensor}\" is not a valid key in the read record.", backtrack=2)
                return False, Result

            values2d = np.array([[x, y] for x, y in zip(timestamps, readings[sensor])])

            # Compute average log‑likelihood for each model
            # .score = mean log‑likelihood
            scores = [float(model.score(values2d)) for model in self._gesture_data[sensor].models]

            Result[sensor] = GestureMatch(
                value = max(scores), # would help with finding more appropriate threshold
                status = max(scores) > self._gesture_data[sensor].threshold # best‑matching orientation
            )

        return all(r.status for r in Result.values()), Result

