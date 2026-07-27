# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the standalone binary shipped via Homebrew.

Why a binary at all: `skillspector` is not on PyPI, and the runtime tree is 48 packages, six
of them Rust/C extensions. A Homebrew Python formula would need ~47 hand-maintained resource
blocks plus a Rust toolchain. Freezing sidesteps dependency resolution completely — the
formula just downloads one file. See docs/adr/0008-homebrew-distribution.md.

Build:
    pyinstaller packaging/pyinstaller/skillspector-quality.spec --clean --noconfirm
"""

from PyInstaller.utils.hooks import collect_all, copy_metadata

# LangChain and LangGraph resolve nodes and providers through dynamic imports and entry-point
# metadata, so static analysis alone misses them. collect_all pulls submodules, data files and
# binaries; copy_metadata keeps importlib.metadata lookups working inside the bundle.
_COLLECT = (
    "skillspector",
    "skillspector_quality",
    "langchain_core",
    "langgraph",
    "langgraph_checkpoint",
    "langgraph_prebuilt",
    "langgraph_sdk",
    "langsmith",
    "typer",
    "rich",
    "radon",
)

# Distributions whose version metadata is read at runtime. skillspector's __version__ is
# surfaced in the report header, and langchain refuses to import without its own metadata.
_METADATA = (
    "skillspector",
    "skillspector-quality",
    "langchain-core",
    "langgraph",
    "langsmith",
    "rich",
    "typer",
    "pyyaml",
    "radon",
    "pydantic",
    "packaging",
)

datas: list = []
binaries: list = []
hiddenimports: list = []

for _pkg in _COLLECT:
    _d, _b, _h = collect_all(_pkg)
    datas += _d
    binaries += _b
    hiddenimports += _h

for _dist in _METADATA:
    # A missing optional distribution must not fail the whole build.
    try:
        datas += copy_metadata(_dist)
    except Exception:  # noqa: BLE001 - PyInstaller raises a bare Exception subclass here
        pass

a = Analysis(  # noqa: F821 - injected by PyInstaller
    ["entry.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Trimmed: pulled in transitively but never used by the CLI, and they add tens of MB.
    excludes=["tkinter", "matplotlib", "numpy", "pandas", "IPython", "pytest", "mypy"],
    noarchive=False,
)

pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="skillspector-quality",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX corrupts codesigned macOS binaries
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # native arch; cross-compiling is not supported, so CI uses one runner per arch
    codesign_identity=None,  # ad-hoc signature only — required for macOS arm64 to execute at all
    entitlements_file=None,
)
