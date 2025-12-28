import h5py
import numpy as np


class OutputDataset:
    def __init__(self, path: str, frame_structure: dict):
        self.path = path
        self.frame_structure = frame_structure

    def add_frame(self, frame_data: dict):
        pass

    def save_episode(self):
        pass


class Hdf5Dataset(OutputDataset):
    def __init__(self, path: str, frame_structure: dict, config: dict):
        super().__init__(path, frame_structure)
        self.hdf5_file = h5py.File(path, 'w')
        self.datasets = {}

        for key, value in self.frame_structure.items():
            if value["type"] == "image":
                self.datasets[key] = self.hdf5_file.create_dataset(
                    key, (0,), maxshape=(None,), dtype=h5py.special_dtype(vlen=np.dtype('uint8')))
            elif value["type"] == "string":
                self.datasets[key] = self.hdf5_file.create_dataset(
                    key, (0,), maxshape=(None,), dtype=h5py.string_dtype(encoding='utf-8'))
            elif value["type"] == "float32":
                self.datasets[key] = self.hdf5_file.create_dataset(
                    key, (0, value["dof"]), maxshape=(None, value["dof"]), dtype='float32')
            else:
                raise ValueError(f"Unsupported frame structure type: {value['type']}")

        self.hdf5_file.create_dataset(
            "more_actions_expected_after_episode",
            (1,),
            dtype='bool',
            data=np.array([config.get("more_actions_expected_after_episode")])
        )

    def add_frame(self, frame_data: dict):
        for key in self.frame_structure.keys():
            self.datasets[key].resize(self.datasets[key].shape[0] + 1, axis=0)
            self.datasets[key][-1] = frame_data[key]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.hdf5_file.__exit__(exc_type, exc_value, traceback)


class LerobotDataset(OutputDataset):
    def __init__(self, path: str):
        super().__init__(path)

    def add_frame(self, frame_data: dict):
        pass

    def save_episode(self):
        pass
