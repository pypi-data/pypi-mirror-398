import ctypes
import sys
from ctypes import wintypes
from pathlib import Path


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]

    @classmethod
    def from_str(cls, guid: str):
        guid = guid.strip("{}").replace("-", "")

        return cls.from_int(int(guid, 16))

    @classmethod
    def from_int(cls, guid: int):
        data1 = (guid >> 96) & 0xFFFFFFFF
        data2 = (guid >> 80) & 0xFFFF
        data3 = (guid >> 64) & 0xFFFF
        data4 = tuple((guid & 0xFFFFFFFFFFFFFFFF).to_bytes(8, byteorder="big"))

        return cls(data1, data2, data3, data4)


if sys.platform == "win32":
    _CoTaskMemFree = ctypes.windll.ole32.CoTaskMemFree
    _SHGetKnownFolderPath = ctypes.windll.shell32.SHGetKnownFolderPath

    _CoTaskMemFree.restype = None
    _CoTaskMemFree.argtypes = [wintypes.LPVOID]

    _SHGetKnownFolderPath.restype = wintypes.LONG
    _SHGetKnownFolderPath.argtypes = [
        ctypes.POINTER(GUID),
        wintypes.DWORD,
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.LPWSTR),
    ]


def known_folder(guid: GUID) -> Path:
    ptr = wintypes.LPWSTR()
    hresult = _SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(ptr))

    try:
        if hresult == 0:
            return Path(ptr.value)  # type: ignore
        else:
            raise ctypes.WinError(hresult)
    finally:
        _CoTaskMemFree(ptr)


def home_dir() -> Path:
    return known_folder(GUID.from_int(0x5E6C858F_0E22_4760_9AFE_EA3317B67173))


def app_data_local_dir() -> Path:
    return known_folder(GUID.from_int(0xF1B32785_6FBA_4FCF_9D55_7B8E7F157091))


def app_data_roaming_dir() -> Path:
    return known_folder(GUID.from_int(0x3EB685DB_65F9_4CF6_A03A_E3EF65729F3D))


def desktop_dir() -> Path:
    return known_folder(GUID.from_int(0xB4BFCC3A_DB2C_424C_B029_7FE99A87C641))


def documents_dir() -> Path:
    return known_folder(GUID.from_int(0xFDD39AD0_238F_46AF_ADB4_6C85480369C7))


def downloads_dir() -> Path:
    return known_folder(GUID.from_int(0x374DE290_123F_4565_9164_39C4925E467B))


def music_dir() -> Path:
    return known_folder(GUID.from_int(0x4BD8D571_6D19_48D3_BE97_422220080E43))


def pictures_dir() -> Path:
    return known_folder(GUID.from_int(0x33E28130_4E1E_4676_835A_98395C3BC3BB))


def public_dir() -> Path:
    return known_folder(GUID.from_int(0xDFDF76A2_C82A_4D63_906A_5644AC457385))


def videos_dir() -> Path:
    return known_folder(GUID.from_int(0x18989B1D_99B5_455B_841C_AB7C74E4DDFC))
