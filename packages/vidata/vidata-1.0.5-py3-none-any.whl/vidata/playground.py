from omegaconf import OmegaConf
from vidata import ConfigManager
from napari.utils.colormaps import CyclicLabelColormap, DirectLabelColormap, label_colormap
from vidata.file_manager import FileManager
import numpy as np
import nrrd


# def load_nrrd__(file):
#     array, header = nrrd.read(str(file))
#     array = np.transpose(array, (2, 1, 0))  # (Z, Y, X)
#     print(header.keys())
#     print(header)
#     ndims = array.ndim
#     print(header.get("space", "").lower())
#     # Extract spacing
#     if "space directions" in header:
#         dirs = np.array(header["space directions"])
#         spacing = np.linalg.norm(dirs, axis=1)[::-1]  # SITK convention (z, y, x)
#     else:
#         spacing = np.ones(ndims)
#
#         # Extract origin
#     if "space origin" in header:
#         origin = np.array(header["space origin"])[::-1]
#     else:
#         origin = np.zeros(ndims)
#
#         # Extract direction matrix
#     if "space directions" in header:
#         dirs = np.array(header["space directions"])
#         dir_mat = dirs / (np.linalg.norm(dirs, axis=1, keepdims=True) + 1e-9)
#         direction = dir_mat  # [::-1, :]  # SITK convention
#     else:
#         direction = np.eye(ndims)
#
#     metadata = {
#         "spacing": spacing,
#         "origin": origin,
#         "direction": direction,
#     }
#     return array, metadata
#
#
# def load_nrrd(file):
#     """
#     Load a NRRD file using pynrrd but return all metadata in SimpleITK conventions.
#
#     Returns:
#         array:     np.ndarray, shape (Z, Y, X)
#         metadata: {
#             "spacing": (Zspacing, Yspacing, Xspacing),
#             "origin":  (Zorigin, Yorigin, Xorigin),
#             "direction": 3x3 direction matrix in SITK axis order,
#             "affine": 4x4 affine matrix
#         }
#     """
#     # Step 1: read using pynrrd
#     array_xyz, header = nrrd.read(str(file))
#     print(header)
#     # NRRD array is in (X, Y, Z) axis order
#     # SITK expects (Z, Y, X)
#     array_zyx = np.transpose(array_xyz, (2, 1, 0))
#     # print(header.get("space", "").lower())
#     ndims = array_zyx.ndim
#
#     # ----------------------------
#     # Step 2: Extract SPACING
#     # ----------------------------
#     if "space directions" in header:
#         dirs_xyz = np.array(header["space directions"])  # shape (3, 3)
#         # Spacing = vector length per axis
#         spacing_xyz = np.linalg.norm(dirs_xyz, axis=1)
#         spacing_zyx = spacing_xyz[::-1]  # reverse to Z,Y,X
#     else:
#         spacing_zyx = np.ones(ndims)
#
#     # ----------------------------
#     # Step 3: Extract ORIGIN
#     # ----------------------------
#     if "space origin" in header:
#         origin_xyz = np.array(header["space origin"])
#         origin_zyx = origin_xyz[::-1]
#     else:
#         origin_zyx = np.zeros(ndims)
#
#     # ----------------------------
#     # Step 4: Extract DIRECTION
#     # ----------------------------
#     if "space directions" in header:
#         dirs_xyz = np.array(header["space directions"])
#         # Normalize each axis vector
#         norms = np.linalg.norm(dirs_xyz, axis=1, keepdims=True)
#         direction = dirs_xyz / (norms + 1e-12)
#
#         # reorder axes: (X,Y,Z) → (Z,Y,X) for SITK
#         direction = direction  # [::-1, :]  # .T
#         # direction = direction.T
#         # direction_zyx = (direction_xyz @ orient_to_ras).T
#     else:
#         direction = np.eye(ndims)
#
#     metadata = {
#         "spacing": spacing_zyx,
#         "origin": origin_zyx,
#         "direction": direction,
#     }
#     return array_zyx, metadata
#
#
# def load_nrrd_v2(file):
#     array, header = nrrd.read(str(file))
#     orientation = header.get("space", "").lower()
#
#     # Select transformation matrix from NRRD orientation to RAS
#     if orientation == "left-posterior-superior":
#         orient_to_ras = np.diag([-1, -1, 1])
#     elif orientation == "right-anterior-superior":
#         orient_to_ras = np.eye(3)
#     else:
#         raise ValueError(f"Unsupported orientation: {orientation}. Only LPS and RAS are supported.")
#
#     # Read direction and origin from NRRD header
#     directions = np.array(header["space directions"])
#     origin = np.array(header["space origin"])
#
#     # Apply orientation transform to directions and transpose for NIfTI convention
#     directions_ras = (directions @ orient_to_ras).T
#
#     # Build 4x4 affine: rotation+scaling in upper 3x3
#     affine = np.eye(4)
#     affine[:3, :3] = directions_ras
#     affine[:3, 3] = origin @ orient_to_ras
#
#     # Extract voxel spacing (norm of each direction vector) and rotation
#     spacing = np.linalg.norm(directions_ras, axis=0)
#     rotation = affine[:3, :3]
#     return array, {"spacing": spacing, "origin": origin, "direction": directions, "affine": affine}
#
#
# def load_nrdd(file):
#     array, header = nrrd.read(str(file))
#     ndims = array.ndim
#     if ndims == 3:
#         array = array.transpose(2, 1, 0)  # (X,Y,Z) → (Z,Y,X)
#     elif ndims == 2:
#         array = array.transpose(1, 0)  # (X,Y) → (Y,X)
#
#     origin = np.array(header["space origin"]) if "space origin" in header else np.zeros(ndims)
#     spacing = (
#         np.linalg.norm(np.array(header["space directions"]), axis=1)
#         if "space directions" in header
#         else np.ones(ndims)
#     )
#
#     if "space directions" in header:
#         norms = np.linalg.norm(header["space directions"], axis=1, keepdims=True)
#         direction = header["space directions"] / (norms + 1e-12)
#     else:
#         direction = np.eye(ndims)
#     direction = direction.flatten()  # sitk style
#     # Convert (X,Y,Z) → (Z,Y,X)
#     spacing = spacing[::-1]
#     spacing = origin[::-1]
#     direction = np.array(direction[::-1]).reshape(ndims, ndims)


if __name__ == "__main__":
    path = "/home/l727r/Documents/network_drives/mic_rocket/data/data_storage/accelerated_happy_baboon_8314301652/chunk_0/adorable_analytic_adder_0800009608.nrrd"
    # path = "/home/l727r/Desktop/MITK/Hands-On Tutorial/3D image/Pic3D.nrrd"
    from vidata.io import load_sitk, load_nrrd, save_sitk, save_nrrd
    from vidata.io.sitk_io import load_sitkT
    from medvol import MedVol

    import SimpleITK as sitk

    # a = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]])
    # data, meta = load_sitk(path)
    # print(meta["direction"])
    # meta["direction"] = a
    # meta["origin"] = [0, 0, 0]
    # meta["spacing"] = [1, 1, 1]
    # save_sitk(data, "/home/l727r/Desktop/MITK/Hands-On Tutorial/3D image/test.nii.gz", meta)
    data, meta = load_sitk("/home/l727r/Desktop/MITK/Hands-On Tutorial/3D image/test.nii.gz")
    print(meta["direction"])
    data, meta = load_sitkT("/home/l727r/Desktop/MITK/Hands-On Tutorial/3D image/test.nii.gz")
    print(meta["direction"])
    quit()

    mat = np.array(
        [
            [0.0183876, 0.037722, 0.999119],
            [0.999695, -0.0171618, -0.0177503],
            [-0.0164771, -0.999141, 0.038026],
        ]
    )
    # rot = np.array(
    #     [
    #         [0.038026, -0.99914089, -0.01647709],
    #         [-0.0177503, -0.01716179, 0.99969515],
    #         [0.99911909, 0.03772201, 0.01838764],
    #     ]
    # )
    # rot2 = np.array(
    #     [
    #         [0.01838764, 0.03772201, 0.99911909],
    #         [0.99969515, -0.0171617, -0.0177503],
    #         [-0.01647709, -0.99914089, 0.038026],
    #     ]
    # )
    #
    # rot2 = [
    #     [0.01838764, 0.99969515, -0.01647709],
    #     [0.03772201, -0.01716179, -0.99914089],
    #     [0.99911909, -0.0177503, 0.038026],
    # ]
    #
    # rot = np.array(
    #     [
    #         [0.01838764, 0, 0],
    #         [0, -0.01716179, 0],
    #         [0, 0, 0.038026],
    #     ]
    # )
    #
    # rot3 = [
    #     [0.038026, -0.99914089, -0.01647709],
    #     [-0.0177503, -0.01716179, 0.99969515],
    #     [0.99911909, 0.03772201, 0.01838764],
    # ]
    # rot3 = np.array(
    #     [
    #         [0.01838764, 0.99969515, 0.99911909],
    #         [0.03772201, -0.01716179, -0.99914089],
    #         [-0.01647709, -0.0177503, 0.038026],
    #     ]
    # )

    data, meta = load_sitk(path)
    print("Shape", data.shape)
    print("Affine", meta["affine"])
    print("Spacing", meta["spacing"])
    print("Direction", meta["direction"])
    print("Origin", meta["origin"])
    data, meta = load_sitkT(path)
    print("Shape", data.shape)
    print("Affine", meta["affine"])
    print("Spacing", meta["spacing"])
    print("Direction", meta["direction"])
    print("Origin", meta["origin"])
    # data, meta = load_nrrd(path)
    # print(data.shape, meta["affine"])
    # print(data.shape, meta["spacing"])
    # print(data.shape, meta["direction"])
    # print(data.shape, meta["origin"])

    # image = MedVol(path)
    # print(image.array.shape, image.affine)
    # print(image.direction)

    # print(meta)
    # nrrd_header = meta["header"]
    # space_dirs = np.array(nrrd_header["space directions"], dtype=float)
    #
    # # spacing = length of each direction vector
    # spacing = np.linalg.norm(space_dirs, axis=1)
    #
    # # direction matrix = normalized vectors (SITK expects unit directions)
    # direction = space_dirs / spacing[:, None]
    #
    # # SITK stores direction flattened row-major
    # direction_flat = direction.flatten().tolist()
    # print(direction_flat)
    #
    # image = sitk.ReadImage(path)
    # print(image.GetDirection())
    quit()

    from vidata.registry import TASK_REGISTRY
    from vidata import LOADER_REGISTRY

    cfg_file = "/home/l727r/Desktop/Project_Utils/ViData/dataset_cfg/Cityscapes.yaml"
    cm = ConfigManager(cfg_file)
    print(cm)
    print(cm.layers)
    layer = cm.layer("Images")
    tm = layer.task_manager()
    print(tm)
    layer = cm.layer("Labels")
    tm = layer.task_manager()
    print(tm)
    # print(LOADER_REGISTRY)
    # print(TASK_REGISTRY["semseg"])
    quit()

    file = "/home/l727r/Documents/cluster-data-all/k539i/test001.nrrd"
    # file = "/home/l727r/Desktop/MITK/Hands-On Tutorial/3D image/Pic3D.nrrd"
    file_2 = "/home/l727r/Desktop/MITK/Hands-On Tutorial/3D image/test001.nrrd"
    file_nii = "/home/l727r/Desktop/MITK/Hands-On Tutorial/3D image/Pic3D.nii.gz"

    # SITK - Array : Z,Y,X
    # SITK - Meta : X,Y,Z
    # NRRD - [x, y, z]

    from vidata.io import load_sitk, save_sitk
    from vidata.io.nrrd_io import load_nrrd, save_nrrd
    import SimpleITK as sitk

    # data, meta = load_sitk(file)
    # print(data.shape, meta["origin"], meta["spacing"], meta["direction"], meta["affine"])
    data, meta = load_nrrd(file)
    # print(data.shape, meta["origin"], meta["spacing"], meta["direction"], meta["affine"])
    save_nrrd(data, file_2, meta)
    _, _ = load_nrrd(file_2)

    # print(meta["header"])
    # image = sitk.ReadImage(file)
    # array = sitk.GetArrayFromImage(image)
    # ndims = len(array.shape)
    #
    # spacing = np.array(image.GetSpacing())  # [::-1])
    # origin = np.array(image.GetOrigin())  # [::-1])
    # direction = np.array(image.GetDirection())  # [::-1]).reshape(ndims, ndims)
    #
    # print(array.shape, spacing, origin, direction)
    #
    # array, header = nrrd.read(str(file))
    # array = array.transpose(2, 1, 0)
    # ndims = array.ndim
    # origin = np.array(header["space origin"]) if "space origin" in header else np.zeros(ndims)
    # spacing = (
    #     np.linalg.norm(np.array(header["space directions"]), axis=1)
    #     if "space directions" in header
    #     else np.zeros(ndims)
    # )
    #
    # norms = np.linalg.norm(header["space directions"], axis=1, keepdims=True)
    # direction = header["space directions"] / (norms + 1e-12)
    # direction = direction.flatten()
    #
    # # direction = None
    # print(array.shape, header)
    # print(array.shape, spacing, origin, direction.flatten())

    # data, meta = load_sitk(file)
    # del meta["affine"]
    # print(data.shape, meta)
    # save_sitk(data, file_2, metadata=meta)
    # data, meta = load_sitk(file_2)
    # del meta["affine"]
    # print(data.shape, meta)
    # # data, meta = load_sitk(file_nii)
    # # del meta["affine"]
    # # print(data.shape, meta)
    # #
    # data, meta = load_nrrd(file_2)
    # data, meta = load_nrrd(file)
    #
    # print(data.shape, meta)
    # data, meta = load_nrrd_v2(file)
    # print(data.shape, meta)
    # print(data.shape, meta)

    # array, header = nrrd.read(str(file))
    # print(array.shape, header)
    #
    # dirs = np.array(header["space directions"])
    # spacing = np.linalg.norm(dirs, axis=1)[::-1]
    # print("S", spacing)

    # cfg = OmegaConf.load(file)
    # cm = ConfigManager(cfg)

    quit()

    fm = FileManager("list.json", ".png")
    print(len(fm))
    print(fm[0])

    dirs = np.array(header["space directions"])
    spacing = np.linalg.norm(dirs, axis=1)[::-1]
    print("S", spacing)
    quit()
    # cfg_file="/home/l727r/Desktop/Project_Utils/ViData/dataset_cfg/Cityscapes.yaml"
    # cm = ConfigManager(cfg_file)
    # print(cm)
    # print(cm.layers)
    # layer = cm.layer("Images")
    cm = label_colormap(num_colors=49, seed=0.5, background_value=0)
    print(cm.colors[0:5])
    print("\n")
    cm = label_colormap(num_colors=120, seed=0.5, background_value=0)
    print(cm.colors[0:5])
