# src/repocards/core/detectors.py
from __future__ import annotations
import re
from typing import Dict, List, Tuple, Any
from ..schemas import FetchedFile
from .extractors import bucket_commands_by_os

# ---------- Ecosystem detection (simple, general) ----------

def detect_ecosystems(files: List[FetchedFile]) -> List[str]:
    paths = {f.path.lower() for f in files}
    ecos = []
    if any(p.endswith(("cmakelists.txt",".cmake","makefile")) for p in paths):
        ecos.append("cmake")
    if any(p in paths for p in ("pyproject.toml","setup.cfg","setup.py","requirements.txt","pipfile")):
        ecos.append("python")
    if "package.json" in paths:
        ecos.append("node")
    return ecos

# ---------- Entry points (console scripts only; ignore build-backend etc.) ----------

def detect_entrypoints(files: List[FetchedFile]) -> List[str]:
    """Only [project.scripts], [tool.poetry.scripts], and entry_points.console_scripts."""
    out: List[str] = []
    fmap = {f.path: f.content for f in files}

    # pyproject.toml
    pp = fmap.get("pyproject.toml")
    if pp:
        # [project.scripts]
        m = re.search(r"(?s)^\s*\[project\.scripts\]\s*(.*?)^\s*\[", pp, re.M)
        block = m.group(1) if m else None
        if block:
            for mm in re.finditer(r"(?m)^\s*([A-Za-z0-9_-]+)\s*=\s*['\"]([^'\"]+)['\"]", block):
                out.append(f"{mm.group(1)} = {mm.group(2)}")
        # [tool.poetry.scripts]
        m = re.search(r"(?s)^\s*\[tool\.poetry\.scripts\]\s*(.*?)^\s*\[", pp, re.M)
        block = m.group(1) if m else None
        if block:
            for mm in re.finditer(r"(?m)^\s*([A-Za-z0-9_-]+)\s*=\s*['\"]([^'\"]+)['\"]", block):
                out.append(f"{mm.group(1)} = {mm.group(2)}")

    # setup.cfg -> [options.entry_points] console_scripts
    scfg = fmap.get("setup.cfg")
    if scfg:
        m = re.search(r"(?s)^\s*\[options\.entry_points\]\s*(.*?)^\s*\[", scfg, re.M)
        sect = m.group(1) if m else ""
        m2 = re.search(r"(?s)^\s*console_scripts\s*=\s*(.+)", sect, re.M)
        if m2:
            body = m2.group(1)
            for mm in re.finditer(r"(?m)^\s*([A-Za-z0-9_-]+)\s*=\s*([A-Za-z0-9_.:]+)", body):
                out.append(f"{mm.group(1)} = {mm.group(2)}")

    # dedupe
    seen, ded = set(), []
    for s in out:
        if s not in seen:
            ded.append(s); seen.add(s)
    return ded[:20]

# ---------- Package names from pip installs (ignore -r, options) ----------

def detect_package_names(install_cmds: List[Tuple[str,str]]) -> List[str]:
    names: List[str] = []
    for cmd, _ in install_cmds:
        low = cmd.lower().strip()
        if not (low.startswith(("pip ","pip3 ","pipx ","uv ")) and " install " in low):
            continue
        tail = re.split(r"\s+", cmd.strip().split(" install ", 1)[1])
        for tok in tail:
            t = tok.strip()
            if not t or t.startswith("-"):  # skip -r, -U, etc.
                continue
            if any(x in t.lower() for x in ("git+","http://","https://","<var>")):
                continue
            if t.endswith((".txt",".in",".cfg",".toml",".whl")):
                continue
            if t.startswith("."):            # . or .[extras]
                continue
            # strip extras and version pins
            t = re.split(r"\[|\==|>=|<=|~=|!=|===|@", t, maxsplit=1)[0]
            if t:
                names.append(t)
    out, seen = [], set()
    for n in names:
        if n not in seen:
            out.append(n); seen.add(n)
    return out[:10]

# ---------- Links split into weights/datasets ----------

def split_weight_and_dataset_links(urls: List[Tuple[str,str]]) -> Dict[str, List[str]]:
    weights, datasets = [], []
    for u, _ in urls:
        ul = u.lower()
        if any(ul.endswith(ext) for ext in (".pt",".pth",".onnx",".ckpt",".safetensors")) or "huggingface.co" in ul:
            weights.append(u)
        if any(d in ul for d in ("zenodo.org","figshare.com","kaggle.com","drive.google.com")):
            datasets.append(u)
    # dedupe
    def ded(seq): 
        out, seen = [], set()
        for x in seq:
            if x not in seen: out.append(x); seen.add(x)
        return out
    return {"model_weight_links": ded(weights)[:12], "dataset_links": ded(datasets)[:12]}

# ---------- Capabilities ----------

def compute_capabilities(
    files: List[FetchedFile],
    harvested_cmds: List[Tuple[str,str]],
    urls: List[Tuple[str,str]],
    api_snippets: List[Tuple[str,str]],
) -> Dict[str, Any]:
    entrypoints = detect_entrypoints(files)
    provides_api = bool(api_snippets)
    provides_cli = bool(entrypoints)
    dockerfile_present = any(f.path.endswith("Dockerfile") or "/docker/" in f.path.lower() or f.path.lower().startswith("docker/")
                             for f in files) or " docker " in (" " + " ".join(c for c,_ in harvested_cmds).lower() + " ")
    # bucketed commands -> OS support
    buckets_by_os = bucket_commands_by_os(harvested_cmds)
    os_support = [oskey for oskey in ("linux","macos","windows") if any(buckets_by_os[c][oskey] for c in buckets_by_os)]
    # install commands for package names
    install_cmds: List[Tuple[str,str]] = []
    for oskey in ("linux","macos","windows","generic"):
        install_cmds.extend(buckets_by_os.get("install", {}).get(oskey, []))
    package_names = detect_package_names(install_cmds)
    links = split_weight_and_dataset_links(urls)

    return {
        "entrypoints": entrypoints,
        "provides_api": provides_api,
        "provides_cli": provides_cli,
        "dockerfile_present": dockerfile_present,
        "package_names": package_names,
        "os_support": os_support,
        **links,
        "buckets_by_os": buckets_by_os,
    }

# ---------- Quickstart synthesis tuned to repo type ----------

def _is_cmake_repo(buckets_by_os: Dict[str, Dict[str, List[Tuple[str,str]]]]) -> bool:
    for cat in ("build","run","install"):
        for oskey, items in buckets_by_os.get(cat, {}).items():
            for cmd, _ in items:
                cl = cmd.lower()
                if cl.startswith(("cmake","ninja","make","xcodebuild","msbuild")):
                    return True
    return False

def synthesize_quickstart(buckets_by_os: Dict[str, Dict[str, List[Tuple[str,str]]]]) -> Dict[str, List[Dict[str,str]]]:
    is_cmake = _is_cmake_repo(buckets_by_os)
    out: Dict[str, List[Dict[str,str]]] = {}
    for oskey in ("linux","macos","windows","generic"):
        steps: List[Dict[str,str]] = []

        def _is_sys_pkg(c: str) -> bool:
            cl = c.lower()
            return cl.startswith(("apt","dnf","pacman","brew","choco","winget"))

        def _not_docs_build(c: str) -> bool:
            cl = c.lower()
            if " jupyter-book" in cl or " sphinx" in cl or ".[docs]" in cl:
                return False
            if " --upgrade pip" in cl:       # noise
                return False
            if re.search(r"\bpip(3|x)?\s+install\s+-r\b", cl):  # -r requirements
                return False
            return True

        # quotas
        n_total = 6

        if is_cmake:
            # system deps → cmake/ninja/make → run
            for cmd, src in buckets_by_os.get("install", {}).get(oskey, []):
                if _is_sys_pkg(cmd) and len(steps) < 2:
                    steps.append({"cmd": cmd, "source": src})
            for cmd, src in buckets_by_os.get("build", {}).get(oskey, []):
                if cmd.lower().startswith(("cmake","ninja","make")) and len(steps) < 5:
                    steps.append({"cmd": cmd, "source": src})
            for cmd, src in buckets_by_os.get("run", {}).get(oskey, []):
                if len(steps) < n_total:
                    steps.append({"cmd": cmd, "source": src})
        else:
            # python-first
            for cmd, src in buckets_by_os.get("install", {}).get(oskey, []):
                if _not_docs_build(cmd) and len(steps) < 2:
                    steps.append({"cmd": cmd, "source": src})
            for cmd, src in buckets_by_os.get("run", {}).get(oskey, []):
                if len(steps) < 5:
                    steps.append({"cmd": cmd, "source": src})
            for cmd, src in buckets_by_os.get("test", {}).get(oskey, []):
                if len(steps) < n_total:
                    steps.append({"cmd": cmd, "source": src})

        if not steps:
            for cmd, src in buckets_by_os.get("run", {}).get("generic", [])[:2]:
                steps.append({"cmd": cmd, "source": src})

        out[oskey] = steps[:n_total]
    return out
