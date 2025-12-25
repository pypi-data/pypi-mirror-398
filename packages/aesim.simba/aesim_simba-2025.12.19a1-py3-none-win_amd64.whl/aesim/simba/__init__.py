__version__ = "2025.12.19a1"

# --- MUST BE THE FIRST LINES IN __init__.py ---
import os
import sys

# Allow opt-in/opt-out via environment variable (spawn/fork/forkserver)
# Default on Linux: switch to "spawn" BEFORE initializing the CLR.
_START_METHOD_ENV = os.environ.get("SIMBA_MP_START_METHOD", "").strip().lower()

if sys.platform.startswith("linux"):
    import multiprocessing as _mp

    try:
        _current = _mp.get_start_method(allow_none=True)
    except Exception:
        _current = None

    _target = _START_METHOD_ENV or "spawn"
    if _current is None or _current != _target:
        try:
            _mp.set_start_method(_target, force=True)
        except RuntimeError:
            # Start method was already set elsewhere: keep running, but warn.
            if _target != _current:
                sys.stderr.write(
                    f"[aesim.simba] Warning: multiprocessing start method is '{_current}', "
                    f"not '{_target}'. Running with '{_current}' may segfault if the CLR is "
                    f"already loaded before forking.\n"
                )
# --- END patch ---

# --------------------------------------------------------------------------- #
# Library initialization
# --------------------------------------------------------------------------- #


import clr_loader
import pythonnet
import json

# Resource paths
_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Resources")
_DOTNET_DIR = os.path.join(_RESOURCES_DIR, "dotnet")
_RUNTIME_CONFIG_PATH = os.path.join(_RESOURCES_DIR, "Simba.Data.runtimeconfig.json")


def _get_required_dotnet_runtime_version() -> tuple[str, str]:
    """Read required .NET runtime name and version from the runtimeconfig.json."""
    with open(_RUNTIME_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    name = data["runtimeOptions"]["framework"]["name"]
    version = data["runtimeOptions"]["framework"]["version"]
    return name, version


# If a private DOTNET runtime is bundled with the package, expose it.
if os.path.exists(_DOTNET_DIR):
    os.environ["DOTNET_ROOT"] = _DOTNET_DIR

# Initialize CoreCLR via pythonnet using the package's runtimeconfig.
try:
    pythonnet.set_runtime(clr_loader.get_coreclr(runtime_config=_RUNTIME_CONFIG_PATH))
except Exception as e:
    name, version = _get_required_dotnet_runtime_version()
    sys.stderr.write(
        f"[aesim.simba] Error: unable to load .NET runtime '{name}' version {version}.\n"
        f"[aesim.simba] DOTNET_ROOT set to '{_DOTNET_DIR}' "
        f"(exists: {os.path.exists(_DOTNET_DIR)}).\n"
    )
    raise

# Load the managed assembly and wire up conveniences
import clr  # noqa: E402  (import after set_runtime)
sys.path.append(_RESOURCES_DIR)
clr.AddReference("Simba.Data")

# Re-export common types/names for convenience
from Simba.Data.Repository import ProjectRepository, JsonProjectRepository  # noqa: E402,F401
from Simba.Data import (  # noqa: E402,F401
    License,
    Design,
    Circuit,
    DesignExamples,
    ACSweep,
    SweepType,
    Status,
    Subcircuit,
    CircuitBuilder,
    ThermalComputationMethodType,
    ThermalDataType,
    ThermalDataSemiconductorType,
)
from Simba.Data.Thermal import ThermalData, IV_T, EI_VT  # noqa: E402,F401
from Simba.Data.PsimImport import PsimImporter  # noqa: E402,F401
from System import Array  # noqa: E402,F401
import Simba.Data  # noqa: E402

# Ensure the assembly resolver is configured
Simba.Data.FunctionsAssemblyResolver.RedirectAssembly()

# Register pythonnet type conversions for relevant Simba types
import Python.Runtime  # noqa: E402

Python.Runtime.PyObjectConversions.RegisterEncoder(Simba.Data.DoubleArrayPythonEncoder.Instance)
Python.Runtime.PyObjectConversions.RegisterEncoder(Simba.Data.Double2DArrayPythonEncoder.Instance)
Python.Runtime.PyObjectConversions.RegisterEncoder(Simba.Data.ParameterToPythonEncoder.Instance)
Python.Runtime.PyObjectConversions.RegisterDecoder(Simba.Data.PythonToParameterDecoder.Instance)
Python.Runtime.PyObjectConversions.RegisterDecoder(Python.Runtime.Codecs.IterableDecoder.Instance)
Python.Runtime.PyObjectConversions.RegisterDecoder(Python.Runtime.Codecs.ListDecoder.Instance)

# Optional license activation from environment variable
if os.environ.get("SIMBA_DEPLOYMENT_KEY") is not None:
    License.Activate(os.environ["SIMBA_DEPLOYMENT_KEY"])


def create_analysis_progress(callback):
    """
    Create a Progress[AnalysisProgress] instance from a Python callback.

    Parameters
    ----------
    callback : callable
        A Python function or lambda that accepts either:
            - Two arguments: (progress_value, status), or
            - One argument: (analysis_progress) for the raw object.

    Returns
    -------
    Progress[AnalysisProgress]
        An instance that can be passed to NewJob(progress_instance).
    """
    from System import Action, Progress
    from Simba.Data.Analysis import AnalysisProgress

    def _handler(analysis_progress):
        # If you prefer the full object, call: callback(analysis_progress)
        callback(analysis_progress.Progress, analysis_progress.Status)

    action = Action[AnalysisProgress](_handler)
    return Progress[AnalysisProgress](action)


def import_psim_xml(file_path: str):
    """
    Import a PSIM XML file into a SIMBA repository.

    Parameters
    ----------
    file_path : str
        Path to the PSIM XML file.

    Returns
    -------
    Tuple[ProjectRepository, JsonProjectRepository, str]
        A tuple containing:
            - status: The status of the import operation
            - ProjectRepository: The project repository with the SIMBA design
            - str: Error message if any, otherwise an empty string
    """
    ret = PsimImporter.CreateSIMBARepositoryFromPSIMFile(file_path)
    return ret.Item1, ret.Item2, ret.Item3

import argparse

def project_repository():
    """Return the current project repository opened in SIMBA Desktop, if any.

    Returns:
        [ProjectRepository]: Current Repository or None if not found
    """
    
    def project_path_from_args():
        parser = argparse.ArgumentParser(description='SIMBA Python Script')
        parser.add_argument('--project-path', type=str, help='Path to SIMBA project file')
        args = parser.parse_args()
        project_path = args.project_path
        return project_path
    
    project_path = project_path_from_args()
    
    if project_path:
        repo = ProjectRepository(project_path)
        return repo
    else:
        return None