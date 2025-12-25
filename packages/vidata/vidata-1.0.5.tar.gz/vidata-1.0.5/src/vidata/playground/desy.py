from vidata.file_manager import FileManager
from pathlib import Path
import numpy as np
from vidata.io import load_tif, save_sitk

if __name__ == "__main__":
    path = "/home/l727r/Documents/E130-Projekte/Photoacoustics/RawData/20251219_DESY_Daten/nano14369_21119_o.tif"
    path_out = path.replace(".tif", ".nii.gz")

    data, _ = load_tif(path)
    print(data.shape)
    save_sitk(data, path_out)
    quit()

    path = (
        Path("/home/l727r/Documents/E130-Projekte/Photoacoustics/RawData/20251219_DESY_Daten")
        / "nano14410_21119_z1200"
    )
    ftype = ".tiff"

    fm = FileManager(path, ftype)
    fm.files = fm.files[0:10]
    vol = []
    for file in fm:
        data, _ = load_tif(file)
        vol.append(data)
    vol = np.array(vol)
    print(vol.shape)

    print(len(fm))
