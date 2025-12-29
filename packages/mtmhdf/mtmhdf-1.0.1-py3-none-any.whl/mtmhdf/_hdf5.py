from netCDF4 import Dataset, Variable

class HDF5(Dataset):
    @staticmethod
    def open(file_path:str, mode='r', *args, **kwargs):
        return Dataset(file_path, mode=mode, *args, **kwargs)

    @staticmethod
    def read(fp:Dataset, name:str) -> Variable:
        return HDF5._jump(fp, name)

    @staticmethod
    def keys(fp:Dataset) -> list[str]:
        return list(HDF5._walk(fp))
    
    @staticmethod
    def dpinfo(dp: Variable) -> dict:
        info_dict = dp.__dict__
        info_dict.update({
            "dataset_name": (dp.group().path + "/" + dp.name).replace("//", "/"),
            "dataset_dims": dp.shape,
            "dataset_type": dp.datatype.name
        })
        return info_dict

    @staticmethod
    def infos(fp:Dataset) -> dict:
        return {name: HDF5.dpinfo(HDF5.read(fp, name)) for name in HDF5.keys(fp)}

    @staticmethod
    def _walk(fp: Dataset, path=""):
        if not len(path) or path[-1] != "/":
            path += "/"
        current_variables = list(fp.variables.keys())
        for variable in current_variables:
            yield path + variable
        current_groups = list(fp.groups.keys())
        for group in current_groups:
            yield from HDF5._walk(fp.groups[group], path + group)

    @staticmethod
    def _jump(fp: Dataset, path="/"):
        path_list = path.lstrip("/").split("/")
        if not len(path_list):
            return fp
        subnode_fp = fp.__getitem__(path_list[0])
        subnode_path = "/" + "/".join(path_list[1:])
        if len(path_list) == 1:
            return subnode_fp
        else:
            return HDF5._jump(subnode_fp, subnode_path)
        
