import os
import pickle

class PickleProcess():

    @staticmethod
    def create_path(path):
        os.makedirs(path, exist_ok=True)

    @classmethod
    def save(cls, name, data, path='.\\'):
        if not path:
            path = '.\\'
        cls.create_path(path)
        with open(os.path.join(path, name + '.pickle'), 'wb') as f:
            pickle.dump(obj=data, file=f)

    @classmethod
    def save_by_folder(cls, folder_name, name, data, path=r'./'):
        folder_path = os.path.join(path, folder_name)
        cls.create_path(folder_path)
        with open(os.path.join(folder_path, name + '.pickle'), 'wb') as f:
            pickle.dump(obj=data, file=f)

    @staticmethod
    def read(name, path=r'./'):
        with open(os.path.join(path, name + '.pickle'), 'rb') as f:
            obj = pickle.load(f)
        return obj

