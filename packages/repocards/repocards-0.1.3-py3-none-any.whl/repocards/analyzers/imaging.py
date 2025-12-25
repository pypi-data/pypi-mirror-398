# src/repocards/analyzers/imaging.py
from __future__ import annotations
import re
from typing import Dict, List, Tuple
from ..schemas import FetchedFile

IMAGING_IMPORTS = {"pydicom","nibabel","SimpleITK","itk","vtk","cv2","skimage","monai","napari","torchio"}
FILE_EXTS = (".dcm",".dicom",".nii",".nii.gz",".mha",".mhd",".tif",".tiff",".svs",".czi",".ome.tif",".ome.tiff")
TASKS = {
    "segmentation": ["segmentation","segment","mask"],
    "registration": ["registration","register","warp","deformable"],
    "classification": ["classification","classify"],
    "detection": ["detection","detect","bounding box","bbox"],
    "denoising": ["denoise","denoising"],
    "reconstruction": ["reconstruction","tomography","ct reconstruction"],
}
MODALITIES = {
    "MRI": ["mri","nifti","bids","t1","t2","flair"],
    "CT": ["ct","hounsfield","hu","dicom"],
    "PET": ["pet","suv"],
    "X-ray": ["x-ray","radiography","dr","cr"],
    "ultrasound": ["ultrasound","us"],
    "microscopy": ["microscopy","histopathology","wsi","oct","ome","h&e"],
}

def analyze_imaging(files: List[FetchedFile]) -> Dict[str, object]:
    text = "\n".join(f.content.lower() for f in files)[:600_000]
    imports = set()
    for f in files:
        if f.path.endswith(".py"):
            for m in re.finditer(r"(?m)^\s*(?:from|import)\s+([A-Za-z_]\w*)", f.content):
                mod = m.group(1)
                if mod in IMAGING_IMPORTS:
                    imports.add(mod)

    file_types = sorted({ext for ext in FILE_EXTS if any(ext in f.path.lower() for f in files)})

    # Gate: if no hard signals, return empty
    if not imports and not file_types:
        return {"imaging_score": 0.0, "python_libs": [], "file_types": [], "tasks": [], "modalities": []}

    def freq(word: str) -> int:
        return len(re.findall(rf"\b{re.escape(word)}\b", text))

    tasks, modalities = [], []
    # tasks
    for k, ws in TASKS.items():
        # stricter for registration/reconstruction
        if k in {"registration","reconstruction"}:
            if (imports & {"SimpleITK","itk","monai","nibabel"} or any(ft in (".nii",".nii.gz",".mha",".mhd",".dcm",".dicom") for ft in file_types)) and any(freq(w) >= 1 for w in ws):
                tasks.append(k)
        else:
            if any(freq(w) >= 1 for w in ws):
                tasks.append(k)
    # modalities
    for k, ws in MODALITIES.items():
        hits = sum(freq(w) for w in ws)
        if hits >= 2 or file_types:  # require repetition or known medical file types
            if any(freq(w) >= 1 for w in ws):
                modalities.append(k)

    score = 0.0
    if imports: score += 0.4
    if file_types: score += 0.25
    if tasks: score += 0.25
    if modalities: score += 0.10
    score = min(1.0, round(score, 3))

    return {
        "imaging_score": score,
        "python_libs": sorted(list(imports)),
        "file_types": file_types,
        "tasks": sorted(tasks),
        "modalities": sorted(modalities),
    }
