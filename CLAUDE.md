# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A QGIS processing plugin ("SciPy Filters") that exposes `scipy.ndimage` (and some custom NumPy/SciPy)
raster algorithms through the QGIS Processing Toolbox. It lives directly inside a QGIS profile's
`python/plugins/` directory (this repo *is* the installed plugin), so QGIS's own Python environment
is used — there is no separate virtualenv/build step. Package import root is `scipy_filters` (see
`sys.path` insertion in `scipy_filters.py`), so intra-package imports use `from scipy_filters.xxx import ...`.

## Running tests

Tests live in `test/` and use QGIS's Python bindings, so they must run inside (or against) a QGIS
Python environment, not a bare venv.

```bash
python -m pytest test/                  # from within a shell that has qgis/PyQt/gdal/scipy on PYTHONPATH
```

`.vscode/settings.json` configures both pytest and unittest discovery against `./test` — use whichever
runner is wired to a Python interpreter that has the `qgis` package importable (e.g. QGIS's bundled
Python, or `python-qgis-ltr`/OSGeo4W shell on Windows). There is no CI config in this repo.

Note: as of the current state of `main`, `test/` only contains a `__pycache__` directory — the actual
test sources were removed in commit "Remove broken tests" pending a rewrite. Check `git log -- test/`
before assuming test files exist.

## Architecture

### Provider registration flow

`__init__.py` → `classFactory()` → `SciPyFiltersPlugin` (`scipy_filters.py`). On `initGui()`, it tries
to import `SciPyFiltersProvider`; if SciPy isn't installed, `import scipy_filters_provider` raises
`ModuleNotFoundError` at module load time (caught in `scipy_filters.py`), and the plugin offers to
install it for the QGIS Python interpreter before registering the provider.
`SciPyFiltersProvider.loadAlgorithms()` (`scipy_filters_provider.py`) is the single place where every
algorithm class gets instantiated and added — new algorithms must be imported and added there. The
provider also registers the two global settings `WINDOWSIZE` and `MAXSIZE` (found under QGIS Settings →
Processing) via `ProcessingConfig`.

**The SciPy auto-installer (`install_scipy()`/`_install_scipy_safely()` in `scipy_filters.py`) is
NumPy-ABI-aware, fixed identically on both `main` and `qgis4`.** A naive `pip install scipy` is
dangerous here: GDAL's Python bindings are a compiled extension tied to whichever NumPy ABI they were
built against (could be NumPy 1.x *or* 2.x depending on the QGIS distribution — there's no metadata to
just read this off), and letting pip freely upgrade NumPy to satisfy SciPy's own declared minimum (the
latest SciPy on PyPI requires `numpy>=2.0.0`) can silently break GDAL's `ReadAsArray`/`WriteArray` with
a NumPy 1.x/2.x ABI mismatch — surfacing later, at unrelated call sites, as
`ImportError: A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x...` (confirmed
first-hand on QGIS 4.2.2/Flatpak, see below). The fix empirically preserves compatibility instead of
guessing a NumPy generation: it runs a tiny GDAL↔NumPy roundtrip self-test **in a fresh subprocess**
(critical — testing in-process would hit Python's module cache and miss any on-disk change a `pip
install` just made) before and after installing, and if a compatible NumPy was already working, pins
that *exact* version alongside `scipy` in the same `pip install` call so pip's resolver either finds a
compatible SciPy or fails cleanly. Failures now surface the actual captured pip stdout/stderr in the
QMessageBox — previously the dialog showed a generic message while the real reason (e.g. `No module
named pip` on Flatpak) only appeared in the console/log, invisible to most users. A successful install
still requires restarting QGIS to take effect (the provider import chain isn't retried in the same
process either way — pre-existing behavior, unchanged).

### Algorithm base class hierarchy (`scipy_algorithm_baseclasses.py`)

Nearly every filter is a `QgsProcessingAlgorithm` subclass built on top of `SciPyAlgorithm`, which
implements the entire read → tile → filter → write pipeline generically:

- `SciPyAlgorithm` — base: adds INPUT/OUTPUT/DIMENSION/DTYPE/BANDSTATS parameters, opens the raster
  with GDAL, chooses 2D-per-band vs 3D-datacube processing (`Dimensions` enum), iterates
  `helpers.window.get_windows()` tiles, fills no-data, calls `self.get_fct()` on each tile/window,
  re-masks no-data, writes output, and (optionally) computes band stats / renames the output layer.
- `SciPyAlgorithmWithMode(SciPyAlgorithm)` — adds border `mode` + `cval` (used by most `scipy.ndimage`
  filters that take these).
- `SciPyAlgorithmWithModeAxis(SciPyAlgorithmWithMode)` — adds an `axis` choice (horizontal/vertical/
  band-axis/magnitude), used by directional filters like Sobel/Prewitt.
- `SciPyStatisticalAlgorithm(SciPyAlgorithmWithMode)` — adds size/sizes/footprint/origin parameters
  for neighborhood-based filters (median, rank, uniform, etc.) and computes the required tile margin
  from the footprint/size/origin.

To add a new filter based on `scipy.ndimage`, subclass the most specific base class that already
provides the parameters you need, then override:
- class attrs `_name`, `_displayname`, `_groupid` (must be a key in the `groups` dict), `_default_dtype`
- `get_fct()` — returns the callable to run on each array (can be a bound method for custom logic)
- `insert_parameters(config)` and/or `get_parameters(parameters, context)` (always call `super()` first)
- `createInstance()` — must return a fresh instance of the same class
- the class **docstring** — it is parsed by `checkAndComplain`/`shortHelpString()` via
  `helpers/docstring_html.convert_docstring_to_html()` and rendered as the algorithm's help panel in
  QGIS. It understands a restricted subset of Sphinx/RST markup: `**bold**`, `*italic*`, `.. note::`,
  `.. versionadded::/.. versionchanged::`, and `` `text <url>`_ `` links — not full RST/Sphinx.

Algorithms are grouped in `algs/` roughly by SciPy submodule/theme (`scipy_edge_algorithms.py`,
`scipy_morphological_algorithm.py`, `scipy_fourier_algorithm.py`, `scipy_statistical_algorithms.py`,
`scipy_pixel_statistic_algorithms.py`, `scipy_nodata_algorithm.py`, etc.). `scipy_pca_algorithm.py`
and its helpers/biplot are the notable exception: PCA needs the whole raster in memory at once, so it
does **not** subclass `SciPyAlgorithm`/use the moving-window pipeline — it's a standalone
`QgsProcessingAlgorithm` bounded by the `MAXSIZE` (megapixels) setting instead of `WINDOWSIZE`.

### Moving-window processing (`helpers/window.py`)

Large rasters are processed tile-by-tile to avoid exhausting memory: `get_windows()` yields
`RasterWindow` objects describing a tile plus a margin (needed so neighborhood-based filters get
correct values near tile boundaries); `win.gdalin`/`win.gdalout` give GDAL `ReadAsArray`/`WriteArray`
offset tuples, and `win.getslice(ndim)` gives the NumPy slice to strip the margin back off before
writing. `wrap_margin()` special-cases border `mode="wrap"` so edge tiles wrap around to the *opposite
side of the whole raster*, not just the tile. When adding a new neighborhood filter, `self.margin`
must be set (in `get_parameters`) to at least half the largest kernel/footprint/structure dimension, or
results near tile boundaries will be wrong for large rasters.

### No-data handling

SciPy filters don't understand raster no-data values, so `SciPyAlgorithm.processAlgorithm()` builds a
no-data mask per tile/band, fills no-data cells (`fill_nodata()`, default: 0) before filtering so they
don't corrupt neighboring real pixels, runs the filter, and then re-stamps the original no-data mask
onto the output. `algs/scipy_nodata_algorithm.py` provides standalone filters (get mask / apply mask /
fill with 0, value, band mean, or dtype min/max/central) for users who need finer control, per the
"No data cells" section of `README.md`.

### UI layer (`ui/`)

`ui/scipy_processing_dialog.py` (`ScipyProcessingDialog`, wired up via `createCustomParametersWidget`
in `SciPyAlgorithm`) replaces QGIS's default algorithm dialog — this was necessary because Qt6 broke
the old `WidgetWrapper`-based approach (see README's "Note on QGIS 4 / Qt6"). `ui/structure_widget.py`
(`SciPyParameterStructure`) and `ui/origin_widget.py` (`SciPyParameterOrigin`) are custom
`QgsProcessingParameterDefinition` + widget pairs for entering kernels/structures/footprints and
origin offsets as strings (parsed via `helpers/structures.py`'s `str_to_array`/`check_structure`/
`str_to_int_or_list`). `.ui` files are Qt Designer sources for the corresponding `_widget.py` classes.

**History (pre-Qt6, tag `v1.9`, before the QGIS 4 port):** each cross-widget-dependent parameter
(`DIMENSION`, `SIZES`, `FOOTPRINT`, `ORIGIN`) used to have its own `processing.gui.wrappers.WidgetWrapper`
subclass (`DimsWidgetWrapper`/`SciPyParameterDims` in the now-deleted `ui/dim_widget.py`,
`SizesWidgetWrapper`, `StructureWidgetWrapper`, `OriginWidgetWrapper`), registered per-parameter via
`param.setMetadata({'widget_wrapper': {'class': ...}})` and wired to each other through
`postInitialize(wrappers)` + Qt signals (e.g. changing `DIMENSION` told the origin/structure widgets to
switch between 2D/3D). `WidgetWrapper`-based dialogs crash on Windows Qt6 builds, so this was replaced
wholesale: `ScipyProcessingDialog` now builds and owns every widget for the whole algorithm dialog
directly and wires them together itself (e.g. the old `DimsWidgetWrapper.parentLayerChanged` band-count
check, "3D only if input has >1 band", now lives in `ScipyProcessingDialog` instead). If you're
debugging odd interactions between the dimension/size/footprint/origin widgets, the logic to look at is
in `ScipyProcessingDialog` and the widgets' own `dimensionChanged()`/`setDim()`/`valueChanged` methods,
not a `WidgetWrapper`.

### QGIS 4.2 compatibility — two branches, and a planned rewrite

QGIS 4.2 (Sept. 2026) **removed `QgsProcessingAlgorithmDialogBase` entirely** (class + C++ header both
gone upstream, confirmed by reading QGIS's own `master` source tree) — this broke the plugin
(`ImportError: cannot import name 'QgsProcessingAlgorithmDialogBase'`, GitHub issue #10) because
`ScipyProcessingDialog` subclasses it. There is **no single fix that covers both QGIS 3.x and 4.x**
cleanly, because the replacement class, `QgsProcessingAlgorithmWidgetBase`, is **QGIS-4.x-only** — it
is *not* exposed in the Python bindings of any QGIS 3.x release, not even recent ones (confirmed absent
from `qgis.gui` in a locally installed QGIS 3.44.7). A C++ doc-comment `\since QGIS 3.24` on that class
refers only to a nested enum (`WidgetMode`), not to the class's availability — don't be misled by it.
Consequently this repo maintains **two branches**:

- **`main`** — unchanged, targets `qgisMinimumVersion=3.22`..`4.99` as before, keeps using
  `QgsProcessingAlgorithmDialogBase`. Stable for QGIS 3.x (and QGIS 4.0/4.1, which still had that class
  — unconfirmed exactly when it was removed, only that it's gone by 4.2.2).
- **`qgis4`** — QGIS-4.2+-only release line (`qgisMinimumVersion=4.2`, version bumped e.g. to `2.2` in
  `metadata.txt`/`README.md` changelog). `ui/scipy_processing_dialog.py` imports
  `QgsProcessingAlgorithmWidgetBase` directly (aliased to the old name so the rest of the file is
  untouched for now). `QgsProcessingAlgorithmWidgetBase` is a `QWidget` (not `QDialog`) subclass — it
  supports docking (new `WidgetFlag.NoDocking` to opt out, not currently used) — but exposes the same
  method names `ScipyProcessingDialog` already calls: `setAlgorithm`/`setMainWidget`, `buttonBox()`/
  `cancelButton()`/`messageBar()`, `createFeedback()`, `showLog()`, `setCurrentTask()`,
  `setResults()`/`setExecuted()`/`setExecutedAnyResult()`, `resetGui()`, `updateRunButtonVisibility()`,
  and the `algorithmAboutToRun`/`algorithmFinished` signals — so no other changes were needed to get it
  importing again. These two plugin versions would need to be uploaded as separate versions on the QGIS
  plugin repository (which serves the right one per QGIS's own min/max version matching).

**Planned follow-up rewrite (on `qgis4`, after the import fix is confirmed working in real QGIS 4.2):**
`ScipyProcessingDialog`'s entire hand-built dialog (widget-per-parameter loop, run/cancel/batch button
wiring, `QgsProcessingAlgRunnerTask` orchestration, history logging, etc.) exists *only* because the old
per-parameter `processing.gui.wrappers.WidgetWrapper` mechanism was unusable on Qt6. That old Python
`WidgetWrapper` class (and the whole `processing/gui/wrappers.py` file) **no longer exists in QGIS at
all** (confirmed missing from QGIS's current source tree) — but a modern successor does, and QGIS's own
`ParametersPanel.py` (which builds the standard algorithm dialog) still uses the same
`postInitialize(wrappers)` cross-wiring pattern as the old `WidgetWrapper`, just on new base classes.
This means the QGIS-4-only branch can likely drop `ScipyProcessingDialog` entirely and go back to
something much closer to the pre-Qt6 architecture:
  - Per-parameter custom widgets are now `QgsAbstractProcessingParameterWidgetWrapper` subclasses
    (from `qgis.gui`), not `WidgetWrapper` subclasses.
  - They are **not** attachable to an arbitrary parameter *instance* via
    `param.setMetadata({'widget_wrapper': {'class': ...}})` any more — that per-instance mechanism is
    gone. `QgsProcessingGuiRegistry::createParameterWidgetWrapper()` (confirmed by reading its C++
    source) looks up a wrapper factory **globally, by `parameter.type()` string**
    (`metadata()['widget_wrapper']['widget_type']` only lets you pick between multiple *registered*
    variants for the same type — it's not a hook for arbitrary Python classes).
  - So each parameter type needing a custom widget must: (1) have a distinct `type()` string (custom
    `QgsProcessingParameterDefinition` subclasses like `SciPyParameterStructure`/`SciPyParameterOrigin`
    already do this; `SIZES` currently doesn't — it's a plain `QgsProcessingParameterString` and would
    need to become its own subclass, e.g. `SciPyParameterSizes`, to get a custom widget under this
    model), and (2) have a matching `QgsProcessingParameterWidgetFactoryInterface` registered once at
    plugin startup via `QgsGui.processingGuiRegistry().addParameterWidgetFactory(...)`.
  - Cross-widget wiring (e.g. `DIMENSION` changing → `ORIGIN`/`STRUCTURE`/`SIZES` widgets switching
    between 2D/3D) still goes through `postInitialize(all_wrappers)`, called on every wrapper after all
    are created — same shape as the pre-Qt6 code, just via `QgsAbstractProcessingParameterWidgetWrapper`
    and its `widgetValueHasChanged` signal instead of the old `WidgetWrapper.valueChanged`.
  - The old `DimsWidgetWrapper` convenience (auto-disable the "3D" option when the input layer has only
    1 band, by watching the `INPUT` wrapper) has no obvious cheap equivalent yet — `DIMENSION` doesn't
    need a custom parameter type/wrapper otherwise, and `checkParameterValues` already rejects 3D on a
    1-band layer with an error message, so simply dropping that auto-disable convenience (relying on the
    existing error instead) is the pragmatic option unless it's specifically re-implemented.
  - Net effect: `SciPyAlgorithm.createCustomParametersWidget` override goes away, QGIS's own
    `AlgorithmWidget`/`ParametersPanel` builds the dialog again (batch mode, run/cancel, log, history,
    help panel all "for free"), and only the FOOTPRINT/ORIGIN/SIZES widget classes + their factories
    need to be maintained.

### Testing against real QGIS 4.x (Flatpak)

No QGIS 4.x is installed as a system package on this dev machine (only QGIS 3.44 native, which is what
this repo's own path — `.../QGIS3/profiles/default/python/plugins/scipy_filters` — belongs to). QGIS
4.2.2 is available via Flatpak (`org.qgis.qgis`) for testing the `qgis4` branch. Notes specific to that
setup:

- The Flatpak's **active** profile is `~/.var/app/org.qgis.qgis/data/QGIS/QGIS4/profiles/default/`, not
  the `QGIS3/profiles/default/` sibling that also exists there (that one's a stale leftover from an
  older QGIS Flatpak version — check directory mtimes if unsure which is live). To test this repo
  in-place instead of copying files, symlink it into that profile's plugin directory:
  `ln -s <repo> ~/.var/app/org.qgis.qgis/data/QGIS/QGIS4/profiles/default/python/plugins/scipy_filters`
  (the `python/plugins/` dir may not exist yet — `mkdir -p` it first). The Flatpak has
  `filesystems=host` permission (`flatpak info --show-permissions org.qgis.qgis`), so a symlink pointing
  anywhere on the host filesystem resolves fine inside the sandbox.
- You can introspect the Flatpak's embedded Python without launching the GUI:
  `flatpak run --command=python3 org.qgis.qgis -c "..."`.
- That embedded Python (3.13 in this install) has **no `pip` module** and lives partly under a
  **read-only** `/app`, so this plugin's own `install_scipy()` auto-installer
  (`sys.executable -m pip install scipy` in `scipy_filters.py`) **fails outright** on Flatpak QGIS with
  `No module named pip` — a real, separate, not-yet-fixed limitation, distinct from the QGIS 4.2 dialog
  bug. To manually get SciPy importable for testing: bootstrap pip into the writable user base first —
  `flatpak run --command=python3 org.qgis.qgis -m ensurepip --user`
  (this works because the Flatpak sets `PYTHONUSERBASE=/var/data/python`, which maps to
  `~/.var/app/org.qgis.qgis/data/python` on the host, and `site.ENABLE_USER_SITE=True`, i.e. `--user`
  installs land somewhere already on `sys.path` for the *current* bundled Python version — matching
  `python{X.Y}` subdirectories matter: a stale `data/python/lib/python3.12/...` from a prior Flatpak
  update with an older bundled Python is invisible to a newer 3.13 interpreter).
- **Do not just `pip install --user scipy`** — it pulls in a fresh NumPy 2.x, but the Flatpak's bundled
  GDAL Python bindings (`/app/lib/python3.13/site-packages/osgeo`, read-only) were compiled against
  **NumPy 1.26.4** (also bundled alongside it). User site-packages comes *before* `/app/lib/.../
  site-packages` on `sys.path`, so a fresh NumPy 2.x there silently shadows the compatible 1.26.4 and
  any GDAL call that touches a NumPy array (`ReadAsArray`/`WriteArray` — i.e. everywhere in this plugin)
  crashes with `ImportError: A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x...`,
  at whatever call site happens to touch an array first (so it can surface from many different places).
  There is no fix by pinning NumPy back to 1.x either — NumPy dropped the 1.x line before Python 3.13
  existed, so no NumPy 1.x wheel exists for cp313, and the sandbox has no C/Fortran compiler to build one
  from source. The working fix: **don't install any NumPy yourself** (let GDAL's bundled 1.26.4 keep
  resolving) and install a SciPy version old enough to still declare `numpy<2.3` compatibility but new
  enough to ship a cp313 wheel — confirmed working: SciPy **1.14.1** (requires `numpy<2.3,>=1.23.5`,
  which 1.26.4 satisfies):
  `flatpak run --command=python3 org.qgis.qgis -m pip uninstall -y numpy scipy` (if a bad combo is already installed)
  `flatpak run --command=python3 org.qgis.qgis -m pip install --user --no-deps scipy==1.14.1`
  (`--no-deps` is required — without it pip will still try to satisfy scipy's numpy constraint with a
  fresh 2.x wheel instead of recognizing the already-present 1.26.4). Verified end-to-end: `gdal
  ReadAsArray` → `scipy.ndimage.laplace` → `WriteArray` round-trips cleanly with this combination.

### `helpers/wizard.py` — `RasterWizard`

A convenience API for interactive/script use in the QGIS Python console (not used by the processing
algorithms themselves): load a `QgsRasterLayer` as a NumPy array, run arbitrary NumPy/SciPy/
scikit-image code on it, and write the result back as a new raster layer. See the "Tips for python
users" section of `README.md` for usage and gotchas (band axis order, no-data handling, dtype
parameters when calling algorithms from the console/scripts).

## Translation

User-facing strings are wrapped in `tr()` (`ui/i18n.py`, a thin wrapper over
`QCoreApplication.translate`). `i18n/scipy_filters.pro` + `.ts`/`.qm` files hold the German
translation; algorithm docstrings (help text) are *not* translated.

## Style

`pylintrc` at the repo root configures pylint (note: `max-line-length=80`, `disable=locally-disabled,C0103`)
if you run it, but there's no enforced formatter/linter step in this repo.
