import numpy as np

from ._hdf4 import HDF4
from ._hdf5 import HDF5

from ._utils import int2binarystring, bitoffset, scale, mask


class TemplateData:
    def __init__(self) -> None:
        raise NotImplementedError("Subclass must implement this method")

    def infos(self) -> dict:
        raise NotImplementedError("Subclass must implement this method")

    def __getitem__(self, *item) -> np.ma.MaskedArray | np.ndarray:
        raise NotImplementedError("Subclass must implement this method")


class TemplateReader:
    LinkedDataClass = None

    def __init__(self, data_file:str, *args, **kwargs):
        raise NotImplementedError("Subclass must implement this method")

    def read(self, name:str, *args, **kwargs):
        raise NotImplementedError("Subclass must implement this method")

    def __getitem__(self, name:str):
        return self.rawread(name)

    def readraw(self, name:str):
        raise NotImplementedError("Subclass must implement this method")

    def readbit(self, name:str, bit_start_pos: int, bit_end_pos: int, *args, **kwargs) -> np.ma.MaskedArray | np.ndarray:
        # Bit fields within each byte are numbered from the left:
        # 7, 6, 5, 4, 3, 2, 1, 0.
        # The left-most bit (bit 7) is the most significant bit.
        # The right-most bit (bit 0) is the least significant bit.
        # 左开右闭区间，即从bit_start_pos开始，到bit_end_pos结束，不包含bit_end_pos
        dp = self.readraw(name)
        return bitoffset(np.array(dp[:]), bit_start_pos, bit_end_pos)

    def keys(self) -> list[str]:
        raise NotImplementedError("Subclass must implement this method")

    def infos(self) -> dict:
        raise NotImplementedError("Subclass must implement this method")

# ===================================================================================================


class HDF4Data(TemplateData):
    def __init__(self, dp:HDF4, mode="manual", isScaleAndOffset: bool = True, isMasked: bool = True, manual_options=None, **kwargs) -> None:
        self.dp = dp
        self.mode = mode
        self.isMasked = isMasked
        self.isScaleAndOffset = isScaleAndOffset

        default_manual_options = {
            "attr_scale_factor": "scale_factor",
            "attr_add_offset": "add_offset",
            "attr_fill_value": "_FillValue",
            "attr_decimal": 8,
        }
        if manual_options is None:
            self.manual_options = default_manual_options
        else:
            self.manual_options = manual_options.copy()
            self.manual_options.update(default_manual_options)

    def infos(self):
        return HDF4.dpinfo(self.dp)

    def manual_transform(self, data: np.ndarray) -> np.ma.MaskedArray|np.ndarray:
        infos: dict = self.infos()
        
        attr_scale_factor = self.manual_options["attr_scale_factor"]
        attr_add_offset = self.manual_options["attr_add_offset"]
        attr_fill_value = self.manual_options["attr_fill_value"]
        attr_decimal = self.manual_options["attr_decimal"]

        scale_factor = round(infos.get(attr_scale_factor, 1), attr_decimal)
        add_offset = round(infos.get(attr_add_offset, 0), attr_decimal)
        fill_value = infos.get(attr_fill_value)

        if self.isMasked:
            data = mask(data, fill_value)
        if self.isScaleAndOffset:
            data = scale(data, scale_factor, add_offset)
        return data  

    def __getitem__(self, *item) -> np.ma.MaskedArray | np.ndarray:
        data = self.dp.__getitem__(*item)
        if self.mode == "native":
            return data
        elif self.mode == "manual":
            return self.manual_transform(np.array(data))
        else:
            raise ValueError(f"Invalid mode: {self.mode}")


class HDF4Reader(TemplateReader):
    LinkedDataClass = HDF4Data

    def __init__(self, data_file:str, *args, **kwargs):
        self.fp = HDF4.open(data_file, *args, **kwargs)

    def readraw(self, name:str):
        return HDF4.read(self.fp, name)

    def read(self, name:str, isScaleAndOffset: bool = True, isMasked: bool = True, **kwargs):
        dp = HDF4.read(self.fp, name)
        DataClass = HDF4Reader.LinkedDataClass
        return DataClass(dp, mode="manual", isScaleAndOffset=isScaleAndOffset, isMasked=isMasked, **kwargs)

    def keys(self) -> list[str]:
        return HDF4.keys(self.fp)

    def infos(self) -> dict:
        return HDF4.infos(self.fp)

# ===================================================================================================


class HDF5Data(TemplateData):
    def __init__(self, dp, mode="manual", isScaleAndOffset: bool = False, isMasked: bool = True, manual_options=None, **kwargs) -> None:
        self.dp = dp
        self.mode = mode
        self.isScaleAndOffset = isScaleAndOffset
        self.isMasked = isMasked

        default_manual_options = {
            "attr_scale_factor": "scale_factor",
            "attr_add_offset": "add_offset",
            "attr_fill_value": "_FillValue",
            "attr_decimal": 8,
        }
        if manual_options is None:
            self.manual_options = default_manual_options
        else:
            self.manual_options = manual_options.copy()
            self.manual_options.update(default_manual_options)
            
        if mode == "manual":
            self.dp.set_auto_scale(False)
            self.dp.set_auto_mask(False)
        elif mode == "native":
            self.dp.set_auto_scale(isScaleAndOffset)
            self.dp.set_auto_mask(isMasked)
        else:
            raise ValueError(f"Invalid mode: {self.mode}")

    def infos(self):
        return HDF5.dpinfo(self.dp)

    def manual_transform(self, data: np.ndarray) -> np.ma.MaskedArray|np.ndarray:
        infos: dict = self.infos()
        
        attr_scale_factor = self.manual_options["attr_scale_factor"]
        attr_add_offset = self.manual_options["attr_add_offset"]
        attr_fill_value = self.manual_options["attr_fill_value"]
        attr_decimal = self.manual_options["attr_decimal"]
        scale_factor = round(infos.get(attr_scale_factor, 1), attr_decimal)
        add_offset = round(infos.get(attr_add_offset, 0), attr_decimal)
        fill_value = infos.get(attr_fill_value)

        if self.isMasked:
            data = mask(data, fill_value)
        if self.isScaleAndOffset:
            data = scale(data, scale_factor, add_offset)
        return data

    def __getitem__(self, *item) -> np.ma.MaskedArray | np.ndarray:
        data = self.dp.__getitem__(*item)
        if self.mode == "native":
            return data
        elif self.mode == "manual":
            return self.manual_transform(np.array(data))
        else:
            raise ValueError(f"Invalid mode: {self.mode}")

class HDF5Reader(TemplateReader):
    LinkedDataClass = HDF5Data

    def __init__(self, data_file:str, *args, **kwargs):
        self.fp = HDF5.open(data_file, *args, **kwargs)

    def readraw(self, name:str):
        return HDF5.read(self.fp, name)

    def read(self, name:str, isScaleAndOffset: bool = True, isMasked: bool = True, mode="native", **kwargs):
        dp = HDF5.read(self.fp, name)
        DataClass = HDF5Reader.LinkedDataClass
        return DataClass(dp, mode=mode, isScaleAndOffset=isScaleAndOffset, isMasked=isMasked, **kwargs)

    def keys(self) -> list[str]:
        return HDF5.keys(self.fp)

    def infos(self) -> dict:
        return HDF5.infos(self.fp)

