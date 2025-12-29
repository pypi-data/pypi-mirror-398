from pyhdf.SD import SD, SDC, SDS
import numpy as np





class HDF4:
    DATATYPES = {
        4: "char",
        3: "uchar",
        20: "int8",
        21: "uint8",
        22: "int16",
        23: "uint16",
        24: "int32",
        25: "uint32",
        5: "float32",
        6: "float64",
    }
    OPENMODES = {"r": SDC.READ, "w": SDC.WRITE}

    @staticmethod
    def open(file_path:str, mode='r', *args, **kwargs):
        return SD(file_path, mode=HDF4.OPENMODES[mode], *args, **kwargs)

    @staticmethod
    def read(fp:SD, dataset_name:str):
        return fp.select(dataset_name)
    
    @staticmethod
    def keys(fp:SD) -> list[str]:
        return list(fp.datasets().keys())

    @staticmethod
    def infos(fp:SD) -> dict:
        return {name: HDF4.dpinfo(HDF4.read(fp, name)) for name in HDF4.keys(fp)}

    @staticmethod
    def dpinfo(dp:SDS) -> dict:
        attrs = dp.attributes()
        _info_list = dp.info()
        _info_dict = {
            "dataset_name": _info_list[0], 
            "dataset_rank": _info_list[1], 
            "dataset_dims": _info_list[2], 
            "dataset_type": HDF4.DATATYPES[_info_list[3]]
        }
        _info_dict.update(attrs)
        return _info_dict
     
    

