# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import json
import pathlib
import re
import urllib.request
from functools import lru_cache
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version
from typing import List
from typing import Optional
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import pooch
from packaging.version import Version
from uncertainties import UFloat
from uncertainties import ufloat
from uncertainties import ufloat_fromstr

from easydiffraction.display.tables import TableRenderer
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log

pooch.get_logger().setLevel('WARNING')  # Suppress pooch info messages


def _validate_url(url: str) -> None:
    """Validate that a URL uses only safe HTTP/HTTPS schemes.

    Args:
        url: The URL to validate.

    Raises:
        ValueError: If the URL scheme is not HTTP or HTTPS.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f"Unsafe URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are allowed.")


def _filename_for_id_from_url(data_id: int | str, url: str) -> str:
    """Return local filename like 'ed-12.xye' using extension from the
    URL.
    """
    suffix = pathlib.Path(urlparse(url).path).suffix  # includes leading dot ('.cif', '.xye', ...)
    # If URL has no suffix, fall back to no extension.
    return f'ed-{data_id}{suffix}'


def _normalize_known_hash(value: str | None) -> str | None:
    """Return pooch-compatible known_hash or None.

    Treat placeholder values like 'sha256:...' as unset.
    """
    if not value:
        return None
    value = value.strip()
    if value.lower() == 'sha256:...':
        return None
    return value


@lru_cache(maxsize=1)
def _fetch_data_index() -> dict:
    """Fetch & cache the diffraction data index.json and return it as
    dict.
    """
    index_url = 'https://raw.githubusercontent.com/easyscience/data/refs/heads/master/diffraction/index.json'
    _validate_url(index_url)

    # macOS: sha256sum index.json
    index_hash = 'sha256:e78f5dd2f229ea83bfeb606502da602fc0b07136889877d3ab601694625dd3d7'
    destination_dirname = 'easydiffraction'
    destination_fname = 'data-index.json'
    cache_dir = pooch.os_cache(destination_dirname)

    index_path = pooch.retrieve(
        url=index_url,
        known_hash=index_hash,
        fname=destination_fname,
        path=cache_dir,
        progressbar=False,
    )

    with pathlib.Path(index_path).open('r', encoding='utf-8') as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _fetch_tutorials_index() -> dict:
    """Fetch & cache the tutorials index.json from gh-pages and return
    it as dict.

    The index is fetched from:
    https://easyscience.github.io/diffraction-lib/{version}/tutorials/index.json

    For released versions, {version} is the public version string
    (e.g., '0.8.0.post1'). For development versions, 'dev' is used.

    Returns:
        dict: The tutorials index as a dictionary, or empty dict if
            fetch fails.
    """
    version = _get_version_for_url()
    index_url = f'https://easyscience.github.io/diffraction-lib/{version}/tutorials/index.json'

    try:
        _validate_url(index_url)
        with _safe_urlopen(index_url) as response:
            return json.load(response)
    except Exception as e:
        log.warning(
            f'Failed to fetch tutorials index from {index_url}: {e}',
            exc_type=UserWarning,
        )
        return {}


def download_data(
    id: int | str,
    destination: str = 'data',
    overwrite: bool = False,
) -> str:
    """Download a dataset by numeric ID using the remote diffraction
    index.

    Example:
        path = download_data(id=12, destination="data")

    Args:
        id: Numeric dataset id (e.g. 12).
        destination: Directory to save the file into (created if
            missing).
        overwrite: Whether to overwrite the file if it already exists.

    Returns:
        str: Full path to the downloaded file as string.

    Raises:
        KeyError: If the id is not found in the index.
        ValueError: If the resolved URL is not HTTP/HTTPS.
    """
    index = _fetch_data_index()
    key = str(id)

    if key not in index:
        # Provide a helpful message (and keep KeyError semantics)
        available = ', '.join(
            sorted(index.keys(), key=lambda s: int(s) if s.isdigit() else s)[:20]
        )
        raise KeyError(f'Unknown dataset id={id}. Example available ids: {available} ...')

    record = index[key]
    url = record['url']
    _validate_url(url)

    known_hash = _normalize_known_hash(record.get('hash'))
    fname = _filename_for_id_from_url(id, url)

    dest_path = pathlib.Path(destination)
    dest_path.mkdir(parents=True, exist_ok=True)
    file_path = dest_path / fname

    description = record.get('description', '')
    message = f'Data #{id}'
    if description:
        message += f': {description}'

    console.paragraph('Getting data...')
    console.print(f'{message}')

    if file_path.exists():
        if not overwrite:
            console.print(
                f"✅ Data #{id} already present at '{file_path}'. Keeping existing file."
            )
            return str(file_path)
        log.debug(f"Data #{id} already present at '{file_path}', but will be overwritten.")
        file_path.unlink()

    # Pooch downloads to destination with our controlled filename.
    pooch.retrieve(
        url=url,
        known_hash=known_hash,
        fname=fname,
        path=str(dest_path),
    )

    console.print(f"✅ Data #{id} downloaded to '{file_path}'")
    return str(file_path)


def package_version(package_name: str) -> str | None:
    """Get the installed version string of the specified package.

    Args:
        package_name (str): The name of the package to query.

    Returns:
        str | None: The raw version string (may include local part,
        e.g., '1.2.3+abc123'), or None if the package is not installed.
    """
    try:
        return version(package_name)
    except PackageNotFoundError:
        return None


def stripped_package_version(package_name: str) -> str | None:
    """Get the installed version of the specified package, stripped of
    any local version part.

    Returns only the public version segment (e.g., '1.2.3' or
    '1.2.3.post4'), omitting any local segment (e.g., '+d136').

    Args:
        package_name (str): The name of the package to query.

    Returns:
        str | None: The public version string, or None if the package
        is not installed.
    """
    v_str = package_version(package_name)
    if v_str is None:
        return None
    try:
        v = Version(v_str)
        return str(v.public)
    except Exception:
        return v_str


def _is_dev_version(package_name: str) -> bool:
    """Check if the installed package version is a development/local
    version.

    A version is considered "dev" if:
    - The raw version contains '+dev', '+dirty', or '+devdirty' (local
      suffixes from versioningit)
    - The public version is '999.0.0' (versioningit default-tag
      fallback)

    Args:
        package_name (str): The name of the package to query.

    Returns:
        bool: True if the version is a development version, False
            otherwise.
    """
    raw_version = package_version(package_name)
    if raw_version is None:
        return True  # No version found, assume dev

    # Check for local version suffixes from versioningit
    if any(marker in raw_version for marker in ('+dev', '+dirty', '+devdirty')):
        return True

    # Check for default-tag fallback (999.0.0)
    public_version = stripped_package_version(package_name)
    return bool(public_version and public_version.startswith('999.'))


def _get_version_for_url(package_name: str = 'easydiffraction') -> str:
    """Get the version string to use in URLs for fetching remote
    resources.

    Returns the public version for released versions, or 'dev' for
    development/local versions.

    Args:
        package_name (str): The name of the package to query.

    Returns:
        str: The version string to use in URLs ('dev' or a version like
            '0.8.0.post1').
    """
    if _is_dev_version(package_name):
        return 'dev'
    return stripped_package_version(package_name) or 'dev'


def _safe_urlopen(request_or_url):  # type: ignore[no-untyped-def]
    """Wrapper for urlopen with prior validation.

    Centralises lint suppression for validated HTTPS requests.
    """
    # Only allow https scheme.
    if isinstance(request_or_url, str):
        parsed = urllib.parse.urlparse(request_or_url)
        if parsed.scheme != 'https':  # pragma: no cover - sanity check
            raise ValueError('Only https URLs are permitted')
    elif isinstance(request_or_url, urllib.request.Request):  # noqa: S310 - request object inspected, not opened
        parsed = urllib.parse.urlparse(request_or_url.full_url)
        if parsed.scheme != 'https':  # pragma: no cover
            raise ValueError('Only https URLs are permitted')
    return urllib.request.urlopen(request_or_url)  # noqa: S310 - validated https only


def _resolve_tutorial_url(url_template: str) -> str:
    """Replace {version} placeholder in URL template with actual
    version.

    Args:
        url_template (str): URL template containing {version}
            placeholder.

    Returns:
        str: URL with {version} replaced by actual version string.
    """
    version = _get_version_for_url()
    return url_template.replace('{version}', version)


def list_tutorials() -> None:
    """Display a table of available tutorial notebooks.

    Shows tutorial ID, filename, title, and description for all
    tutorials available for the current version of easydiffraction.
    """
    index = _fetch_tutorials_index()
    if not index:
        console.print('❌ No tutorials available.')
        return

    version = _get_version_for_url()
    console.print(f'Tutorials available for easydiffraction v{version}:')
    console.print('')

    columns_headers = ['id', 'file', 'title', 'description']
    columns_alignment = ['right', 'left', 'left', 'left']
    columns_data = []

    for tutorial_id in sorted(index.keys(), key=lambda x: int(x) if x.isdigit() else x):
        record = index[tutorial_id]
        filename = f'ed-{tutorial_id}.ipynb'
        title = record.get('title', '')
        description = record.get('description', '')
        columns_data.append([tutorial_id, filename, title, description])

    render_table(
        columns_headers=columns_headers,
        columns_data=columns_data,
        columns_alignment=columns_alignment,
    )


def download_tutorial(
    id: int | str,
    destination: str = 'tutorials',
    overwrite: bool = False,
) -> str:
    """Download a tutorial notebook by numeric ID.

    Example:
        path = download_tutorial(id=1, destination="tutorials")

    Args:
        id: Numeric tutorial id (e.g. 1).
        destination: Directory to save the file into (created if
            missing).
        overwrite: Whether to overwrite the file if it already exists.

    Returns:
        str: Full path to the downloaded file as string.

    Raises:
        KeyError: If the id is not found in the index.
        ValueError: If the resolved URL is not HTTP/HTTPS.
    """
    index = _fetch_tutorials_index()
    key = str(id)

    if key not in index:
        available = ', '.join(
            sorted(index.keys(), key=lambda s: int(s) if s.isdigit() else s)[:20]
        )
        raise KeyError(f'Unknown tutorial id={id}. Available ids: {available}')

    record = index[key]
    url_template = record['url']
    url = _resolve_tutorial_url(url_template)
    _validate_url(url)

    fname = f'ed-{id}.ipynb'

    dest_path = pathlib.Path(destination)
    dest_path.mkdir(parents=True, exist_ok=True)
    file_path = dest_path / fname

    title = record.get('title', '')
    message = f'Tutorial #{id}'
    if title:
        message += f': {title}'

    console.paragraph('Getting tutorial...')
    console.print(f'{message}')

    if file_path.exists():
        if not overwrite:
            console.print(
                f"✅ Tutorial #{id} already present at '{file_path}'. Keeping existing file."
            )
            return str(file_path)
        log.debug(f"Tutorial #{id} already present at '{file_path}', but will be overwritten.")
        file_path.unlink()

    # Download the notebook
    with _safe_urlopen(url) as resp:
        file_path.write_bytes(resp.read())

    console.print(f"✅ Tutorial #{id} downloaded to '{file_path}'")
    return str(file_path)


def download_all_tutorials(
    destination: str = 'tutorials',
    overwrite: bool = False,
) -> list[str]:
    """Download all available tutorial notebooks.

    Example:
        paths = download_all_tutorials(destination="tutorials")

    Args:
        destination: Directory to save the files into (created if
            missing).
        overwrite: Whether to overwrite files if they already exist.

    Returns:
        list[str]: List of full paths to the downloaded files.
    """
    index = _fetch_tutorials_index()
    if not index:
        console.print('❌ No tutorials available to download.')
        return []

    version = _get_version_for_url()
    console.print(f'📥 Downloading all tutorials for easydiffraction v{version}...')

    downloaded_paths = []
    for tutorial_id in sorted(index.keys(), key=lambda x: int(x) if x.isdigit() else x):
        try:
            path = download_tutorial(
                id=tutorial_id,
                destination=destination,
                overwrite=overwrite,
            )
            downloaded_paths.append(path)
        except Exception as e:
            log.warning(f'Failed to download tutorial #{tutorial_id}: {e}')

    console.print(f'✅ Downloaded {len(downloaded_paths)} tutorials to "{destination}/"')
    return downloaded_paths


def show_version() -> None:
    """Print the installed version of the easydiffraction package.

    Args:
        None
    """
    current_ed_version = package_version('easydiffraction')
    console.print(f'Current easydiffraction v{current_ed_version}')


# TODO: This is a temporary utility function. Complete migration to
#  TableRenderer (as e.g. in show_all_params) and remove this.
def render_table(
    columns_data,
    columns_alignment,
    columns_headers=None,
    display_handle=None,
):
    headers = [
        (col, align) for col, align in zip(columns_headers, columns_alignment, strict=False)
    ]
    df = pd.DataFrame(columns_data, columns=pd.MultiIndex.from_tuples(headers))

    tabler = TableRenderer.get()
    tabler.render(df, display_handle=display_handle)


def render_cif(cif_text) -> None:
    """Display the CIF text as a formatted table in Jupyter Notebook or
    terminal.

    Args:
        cif_text: The CIF text to display.
    """
    # Split into lines
    lines: List[str] = [line for line in cif_text.splitlines()]

    # Convert each line into a single-column format for table rendering
    columns: List[List[str]] = [[line] for line in lines]

    # Render the table using left alignment and no headers
    render_table(
        columns_headers=['CIF'],
        columns_alignment=['left'],
        columns_data=columns,
    )


def tof_to_d(
    tof: np.ndarray,
    offset: float,
    linear: float,
    quad: float,
    quad_eps=1e-20,
) -> np.ndarray:
    """Convert time-of-flight (TOF) to d-spacing using a quadratic
    calibration.

    Model:
        TOF = offset + linear * d + quad * d²

    The function:
      - Uses a linear fallback when the quadratic term is effectively
        zero.
      - Solves the quadratic for d and selects the smallest positive,
        finite root.
      - Returns NaN where no valid solution exists.
      - Expects ``tof`` as a NumPy array; output matches its shape.

    Args:
        tof (np.ndarray): Time-of-flight values (µs). Must be a NumPy
            array.
        offset (float): Calibration offset (µs).
        linear (float): Linear calibration coefficient (µs/Å).
        quad (float): Quadratic calibration coefficient (µs/Å²).
        quad_eps (float, optional): Threshold to treat ``quad`` as zero.
            Defaults to 1e-20.

    Returns:
        np.ndarray: d-spacing values (Å), NaN where invalid.

    Raises:
        TypeError: If ``tof`` is not a NumPy array or coefficients are
            not real numbers.
    """
    # Type checks
    if not isinstance(tof, np.ndarray):
        raise TypeError(f"'tof' must be a NumPy array, got {type(tof).__name__}")
    for name, val in (
        ('offset', offset),
        ('linear', linear),
        ('quad', quad),
        ('quad_eps', quad_eps),
    ):
        if not isinstance(val, (int, float, np.integer, np.floating)):
            raise TypeError(f"'{name}' must be a real number, got {type(val).__name__}")

    # Output initialized to NaN
    d_out = np.full_like(tof, np.nan, dtype=float)

    # 1) If quadratic term is effectively zero, use linear formula:
    #    TOF ≈ offset + linear * d =>
    #    d ≈ (tof - offset) / linear
    if abs(quad) < quad_eps:
        if linear != 0.0:
            d = (tof - offset) / linear
            # Keep only positive, finite results
            valid = np.isfinite(d) & (d > 0)
            d_out[valid] = d[valid]
        # If B == 0 too, there's no solution; leave NaN
        return d_out

    # 2) If quadratic term is significant, solve the quadratic equation:
    #    TOF = offset + linear * d + quad * d² =>
    #    quad * d² + linear * d + (offset - tof) = 0
    discr = linear**2 - 4 * quad * (offset - tof)
    has_real_roots = discr >= 0

    if np.any(has_real_roots):
        sqrt_discr = np.sqrt(discr[has_real_roots])

        root_1 = (-linear + sqrt_discr) / (2 * quad)
        root_2 = (-linear - sqrt_discr) / (2 * quad)

        # Pick smallest positive, finite root per element
        # Stack roots for comparison
        roots = np.stack((root_1, root_2), axis=0)
        # Replace non-finite or negative roots with NaN
        roots = np.where(np.isfinite(roots) & (roots > 0), roots, np.nan)
        # Choose the smallest positive root or NaN if none are valid
        chosen = np.nanmin(roots, axis=0)

        d_out[has_real_roots] = chosen

    return d_out


def twotheta_to_d(twotheta, wavelength):
    """Convert 2-theta to d-spacing using Bragg's law.

    Parameters:
        twotheta (float or np.ndarray): 2-theta angle in degrees.
        wavelength (float): Wavelength in Å.

    Returns:
        d (float or np.ndarray): d-spacing in Å.
    """
    # Convert twotheta from degrees to radians
    theta_rad = np.radians(twotheta / 2)

    # Calculate d-spacing using Bragg's law
    d = wavelength / (2 * np.sin(theta_rad))

    return d


def get_value_from_xye_header(file_path, key):
    """Extracts a floating point value from the first line of the file,
    corresponding to the given key.

    Parameters:
        file_path (str): Path to the input file.
        key (str): The key to extract ('DIFC' or 'two_theta').

    Returns:
        float: The extracted value.

    Raises:
        ValueError: If the key is not found.
    """
    pattern = rf'{key}\s*=\s*([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)'

    with pathlib.Path(file_path).open('r') as f:
        first_line = f.readline()

    match = re.search(pattern, first_line)
    if match:
        return float(match.group(1))
    else:
        raise ValueError(f'{key} not found in the header.')


def str_to_ufloat(s: Optional[str], default: Optional[float] = None) -> UFloat:
    """Parse a CIF-style numeric string into a `ufloat` with an optional
    uncertainty.

    Examples of supported input:
    - "3.566"       → ufloat(3.566, nan)
    - "3.566(2)"    → ufloat(3.566, 0.002)
    - None          → ufloat(default, nan)

    Behavior:
    - If the input string contains a value with parentheses (e.g.
      "3.566(2)"), the number in parentheses is interpreted as an
      estimated standard deviation (esd) in the last digit(s).
    - If the input string has no parentheses, an uncertainty of NaN is
      assigned to indicate "no esd provided".
    - If parsing fails, the function falls back to the given `default`
      value with uncertainty NaN.

    Parameters
    ----------
    s : str or None
        Numeric string in CIF format (e.g. "3.566", "3.566(2)") or None.
    default : float or None, optional
        Default value to use if `s` is None or parsing fails.
        Defaults to None.

    Returns:
    -------
    UFloat
        An `uncertainties.UFloat` object with the parsed value and
        uncertainty. The uncertainty will be NaN if not specified or
        parsing failed.
    """
    if s is None:
        return ufloat(default, np.nan)

    if '(' not in s and ')' not in s:
        s = f'{s}(nan)'
    try:
        return ufloat_fromstr(s)
    except Exception:
        return ufloat(default, np.nan)
