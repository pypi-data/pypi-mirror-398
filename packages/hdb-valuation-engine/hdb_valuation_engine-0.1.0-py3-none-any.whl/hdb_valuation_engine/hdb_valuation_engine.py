"""
HDB Valuation Engine CLI

A robust, object-oriented Python CLI tool for ingesting Singapore HDB resale transaction
CSV data and identifying undervalued properties using a composite valuation score.

Classes
-------
- HDBLoader: Handles CSV ingestion and schema normalization.
- FeatureEngineer: Parses remaining lease strings and computes engineered features.
- ValuationEngine: Computes group-wise Z-Scores and final valuation scores.
- ReportGenerator: Applies user filters and renders a clean top-N buy list to console.

Usage
-----
hdb-valuation-engine --input resale.csv --town "PUNGGOL" --budget 600000

Notes
-----
- Strict OOP: All logic is encapsulated within classes; only the CLI bootstrap lives
  under the `if __name__ == "__main__"` guard.
- Robustness: PEP 8 style, type hints, logging, try/except for I/O and parsing.
- Libraries: pandas, numpy, argparse, logging, sys
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
import json
import os
import hashlib
import pickle
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from sklearn.neighbors import KDTree  # type: ignore
except Exception:  # noqa: BLE001
    KDTree = None  # type: ignore[misc,assignment]

# ---------------------------------------------------------------------------
# Package version
# ---------------------------------------------------------------------------
__version__: str = "1.3.0"


# ---------------------------------------------------------------------------
# Logging configuration helper
# ---------------------------------------------------------------------------

def configure_logging(verbosity: int) -> None:
    """Configure root logger formatting and level.

    Parameters
    ----------
    verbosity : int
        Verbosity level from CLI:
        - 0: WARNING
        - 1: INFO
        - 2+: DEBUG
    """
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ---------------------------------------------------------------------------
# Data classes and helper utilities
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Schema:
    """Canonical column names expected by the pipeline.

    This class centralizes schema expectations while allowing flexible mapping
    from real-world datasets where names may vary slightly in case or spacing.
    """

    town: str = "town"
    flat_type: str = "flat_type"
    resale_price: str = "resale_price"
    floor_area: str = "floor_area_sqm"
    remaining_lease_raw: str = "remaining_lease"

    # Engineered fields
    remaining_lease_years: str = "remaining_lease_years"
    price_efficiency: str = "price_efficiency"
    z_price_efficiency: str = "z_price_efficiency"
    valuation_score: str = "valuation_score"


# ---------------------------------------------------------------------------
# Core pipeline classes
# ---------------------------------------------------------------------------

class HDBLoader:
    """Load and normalize HDB resale CSV data.

    The loader focuses on robust file I/O and schema normalization. It lowercases
    and strips column names to mitigate schema drift and attempts to coerce core
    numeric columns into numeric dtype with proper NA handling.
    """

    def __init__(self, schema: Schema | None = None) -> None:
        self.schema = schema or Schema()
        self.logger = logging.getLogger(self.__class__.__name__)

    def load(self, path: str) -> pd.DataFrame:
        """Load CSV into a pandas DataFrame with normalized column names.

        Parameters
        ----------
        path : str
            Path to the CSV file.

        Returns
        -------
        pd.DataFrame
            DataFrame with normalized columns and raw types preserved where possible.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the CSV cannot be parsed.
        """
        self.logger.info("Loading CSV file: %s", path)
        try:
            df = pd.read_csv(path)
        except FileNotFoundError as exc:
            self.logger.error("File not found: %s", path)
            raise
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("Failed to read CSV: %s", path)
            raise ValueError(f"Failed to read CSV: {path}") from exc

        # Normalize column names: lowercase, strip, replace spaces with underscore
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        self.logger.debug("Normalized columns: %s", df.columns.tolist())

        # Coerce common numeric fields when present
        for col in [self.schema.resale_price, self.schema.floor_area]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df


class FeatureEngineer:
    """Engineer features required for valuation.

    Responsibilities
    ---------------
    - Parse remaining lease strings of the form "85 years 3 months" into a float
      in units of years (e.g., 85.25) with robust handling of edge cases.
    - Compute price efficiency as: resale_price / (floor_area_sqm * remaining_lease_years)

    Mathematical Notes
    ------------------
    Price efficiency penalizes larger prices per effective area-year. By dividing
    price by both floor area (sqm) and remaining lease (years), the metric
    naturally adjusts for lease decay: two flats with identical area but different
    remaining leases will differ proportionally in price efficiency.
    """

    _LEASE_YEARS_RE = re.compile(r"(?P<years>\d+)\s*year")
    _LEASE_MONTHS_RE = re.compile(r"(?P<months>\d+)\s*month")

    def __init__(self, schema: Schema | None = None) -> None:
        self.schema = schema or Schema()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _parse_lease_text(self, text: str | float | int | None) -> Optional[float]:
        """Parse a remaining lease string into float years.

        Examples
        --------
        - "85 years 3 months" -> 85.25
        - "99 years" -> 99.0
        - "8 months" -> 0.666...
        - "less than 1 year" -> 0.5 (conservative placeholder)

        Parameters
        ----------
        text : str | float | int | None
            Raw value from the dataset.

        Returns
        -------
        Optional[float]
            Parsed years as float, or None if parsing fails.
        """
        if text is None or (isinstance(text, float) and np.isnan(text)):
            return None

        # If already numeric (rare), accept positive values
        if isinstance(text, (int, float)):
            try:
                val = float(text)
                return val if val >= 0 else None
            except Exception:  # noqa: BLE001
                return None

        s = str(text).strip().lower()
        if s in {"na", "n/a", "nan", "", "none"}:
            return None

        if "less than 1 year" in s:
            # Conservative assumption when qualitative
            return 0.5

        years = 0.0
        months = 0.0

        try:
            y_match = self._LEASE_YEARS_RE.search(s)
            m_match = self._LEASE_MONTHS_RE.search(s)
            if y_match:
                years = float(y_match.group("years"))
            if m_match:
                months = float(m_match.group("months"))
            if years == 0.0 and months == 0.0:
                # Try a pure-number fallback (e.g., "85")
                try:
                    return float(s)
                except Exception:  # noqa: BLE001
                    return None
            return years + months / 12.0
        except Exception:  # noqa: BLE001
            return None

    def _infer_remaining_lease_from_commence(
        self, df: pd.DataFrame, assumed_lease_years: float = 99.0
    ) -> pd.Series:
        """Infer remaining lease (years) from `lease_commence_date` and `month` columns.

        Mathematics
        -----------
        remaining_years = assumed_lease_years - ((year + month/12) - lease_commence_year)
        where (year, month) come from the transaction month string "YYYY-MM".

        Values are clipped to [0, assumed_lease_years]. Non-parsable rows yield NaN.
        """
        year_month = df.get("month")
        commence = df.get("lease_commence_date")
        out = pd.Series(np.nan, index=df.index, dtype="float64")
        if year_month is None or commence is None:
            return out

        # Coerce commence to numeric year
        commence_year = pd.to_numeric(commence, errors="coerce")

        # Parse year and month from YYYY-MM
        ym = year_month.astype(str).str.strip()
        year = pd.to_numeric(ym.str.slice(0, 4), errors="coerce")
        mon = pd.to_numeric(ym.str.slice(5, 7), errors="coerce")
        frac_year = year + (mon.fillna(1) - 1) / 12.0

        rem = assumed_lease_years - (frac_year - commence_year)
        rem = rem.where(np.isfinite(rem))
        rem = rem.clip(lower=0.0, upper=assumed_lease_years)
        return rem

    def parse_remaining_lease(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add a `remaining_lease_years` float column to the DataFrame.

        The method attempts to parse the canonical `remaining_lease` column if
        present. If a numeric-looking `remaining_lease_years` already exists,
        it is respected. If missing, it falls back to inferring from
        (`lease_commence_date`, `month`) assuming a 99-year lease.
        All parsing errors coerce to NaN.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe.

        Returns
        -------
        pd.DataFrame
            DataFrame with an added/updated `remaining_lease_years` column.
        """
        col_raw = self.schema.remaining_lease_raw
        col_years = self.schema.remaining_lease_years

        self.logger.info("Parsing remaining lease into years")
        if col_years in df.columns:
            df[col_years] = pd.to_numeric(df[col_years], errors="coerce")
            return df

        parsed: Optional[pd.Series] = None
        if col_raw in df.columns:
            parsed_list: List[Optional[float]] = []
            for val in df[col_raw].tolist():
                try:
                    parsed_list.append(self._parse_lease_text(val))
                except Exception:  # noqa: BLE001
                    parsed_list.append(None)
            parsed = pd.Series(parsed_list, index=df.index, dtype="float64")

        # Fallback inference when parsed is missing or largely NaN
        if parsed is None or parsed.isna().mean() > 0.5:
            self.logger.info(
                "Inferring remaining lease from lease_commence_date and month (99-year assumption)"
            )
            inferred = self._infer_remaining_lease_from_commence(df, assumed_lease_years=99.0)
            if parsed is None:
                parsed = inferred
            else:
                parsed = parsed.fillna(inferred)

        if parsed is None:
            self.logger.warning(
                "No remaining lease information available; creating NaN column"
            )
            df[col_years] = np.nan
        else:
            df[col_years] = pd.to_numeric(parsed, errors="coerce")
        return df

    def compute_price_efficiency(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute price efficiency metric.

        Formula
        -------
        price_efficiency = resale_price / (floor_area_sqm * remaining_lease_years)

        Interpretation
        --------------
        Lower values indicate better cost per area-year. Because the denominator
        includes remaining lease years, this metric adjusts for lease decay: a
        shorter remaining lease increases the denominator less, making price per
        effective area-year higher, and vice versa.
        """
        s = self.schema
        missing = [c for c in [s.resale_price, s.floor_area, s.remaining_lease_years] if c not in df.columns]
        if missing:
            self.logger.error("Missing required columns for price efficiency: %s", missing)
            df[s.price_efficiency] = np.nan
            return df

        self.logger.info("Computing price efficiency")
        denom = df[s.floor_area] * df[s.remaining_lease_years]
        with np.errstate(divide="ignore", invalid="ignore"):
            df[s.price_efficiency] = df[s.resale_price] / denom
        df.loc[~np.isfinite(df[s.price_efficiency]), s.price_efficiency] = np.nan
        return df


class ValuationEngine:
    """Compute group-wise Z-Scores and a final valuation score.

    Methodology
    -----------
    1) Compute Z-Score of `price_efficiency` within groups defined by configurable
       grouping keys (default: (town, flat_type)). The Z-Score is defined as:

           z = (x - mu) / sigma

       where x is the observation's price_efficiency, mu is the group mean,
       and sigma is the group standard deviation. If sigma == 0 or NaN, z is set to 0.

    2) Define Valuation_Score = -Z_Price_Efficiency so that higher scores indicate
       better (cheaper-than-peers) properties.
    """

    def __init__(self, schema: Schema | None = None) -> None:
        self.schema = schema or Schema()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _groupwise_zscore(self, series: pd.Series, groups: pd.Series) -> pd.Series:
        """Compute group-wise Z-Score with robust handling of zero std.

        Parameters
        ----------
        series : pd.Series
            Numeric series to standardize.
        groups : pd.Series
            Group labels of same length as series.

        Returns
        -------
        pd.Series
            Group-wise z-scores with NaN-safe handling; zeros where std is 0 or NaN.
        """
        df = pd.DataFrame({"x": series, "g": groups})
        # Compute mean and std per group using transform for alignment
        means = df.groupby("g")["x"].transform("mean")
        stds = df.groupby("g")["x"].transform("std")

        z = (series - means) / stds
        z = z.mask(~np.isfinite(z), 0.0)
        return z

    def score(self, df: pd.DataFrame, group_by: Optional[List[str]] = None) -> pd.DataFrame:
        """Add Z-Score and Valuation Score columns to the DataFrame.

        Adds the following columns:
        - z_price_efficiency: group-wise Z-Score of price_efficiency within selected groups
        - valuation_score: -z_price_efficiency, so higher is more undervalued

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame containing required columns.
        group_by : Optional[List[str]]
            Column names to define peer groups. Defaults to [town, flat_type].

        Returns
        -------
        pd.DataFrame
            DataFrame with added score columns.
        """
        s = self.schema
        default_groups = [s.town, s.flat_type]
        group_cols = (group_by or default_groups)

        required = group_cols + [s.price_efficiency]
        missing = [c for c in required if c not in df.columns]
        if missing:
            self.logger.error("Missing columns for valuation: %s", missing)
            df[s.z_price_efficiency] = np.nan
            df[s.valuation_score] = np.nan
            return df

        self.logger.info("Computing group-wise z-scores over groups: %s", group_cols)
        # Create tuple keys for groups to allow multiple columns grouping
        groups = list(zip(*[df[c] for c in group_cols])) if group_cols else [()] * len(df)
        group_keys = pd.Series(groups, index=df.index, dtype="object")

        z = self._groupwise_zscore(df[s.price_efficiency], group_keys)
        df[s.z_price_efficiency] = z
        df[s.valuation_score] = -z
        return df


class TransportScorer:
    """Compute MRT accessibility scores using spatial nearest-neighbor queries.

    This scorer loads a catalog of MRT station coordinates, strictly excluding
    all LRT stations using a regex filter '^(BP|S[WE]|P[WE])'. The pattern
    matches the line codes for Bukit Panjang (BP), Sengkang (SW/SE), and Punggol
    (PW/PE) LRT loops, ensuring that only heavy rail stations are retained.

    A KDTree (from scikit-learn) is used for vectorized nearest-neighbor
    computation across thousands of records instantly, avoiding Python loops.

    Accessibility score definition
    ------------------------------
    score = max(0, 10 - (dist_km * 2))
    where dist_km is the Euclidean distance in kilometers from the HDB listing
    coordinate to the nearest MRT station in the filtered catalog.
    """

    def __init__(self, stations_df: Optional[pd.DataFrame] = None, cache_dir: Optional[str] = None) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self._stations: Optional[pd.DataFrame] = None
        self._tree: Optional[KDTree] = None
        self._cache_dir = cache_dir or os.path.join(os.getcwd(), ".cache_transport")
        os.makedirs(self._cache_dir, exist_ok=True)
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("TransportScorer initialized with cache_dir=%s", self._cache_dir)
        if stations_df is not None:
            self.load_stations(stations_df)

    @staticmethod
    def _exclude_lrt(df: pd.DataFrame) -> pd.DataFrame:
        """Exclude LRT stations using strict regex on line codes.

        Excludes station rows whose `line_code` matches '^(BP|S[WE]|P[WE])'.
        Column expectations:
        - name: station name (str)
        - line_code: string line code such as 'NS', 'EW', 'DT', 'CC', 'BP', 'SW'
        - lat, lon: numeric coordinates in degrees
        """
        if "line_code" not in df.columns:
            return df
        mask = ~df["line_code"].astype(str).str.match(r"^(BP|S[WE]|P[WE])", na=False)
        return df.loc[mask].copy()

    def _cache_paths(self, tag: str) -> Tuple[str, str]:
        key = hashlib.sha256(tag.encode("utf-8")).hexdigest()[:16]
        return (
            os.path.join(self._cache_dir, f"stations_{key}.pkl"),
            os.path.join(self._cache_dir, f"kdtree_{key}.pkl"),
        )

    def clear_cache(self) -> None:
        """Delete cached stations and KDTree files in the cache directory."""
        try:
            import glob
            for p in glob.glob(os.path.join(self._cache_dir, "*.pkl")):
                try:
                    os.remove(p)
                except Exception:
                    pass
            if self.logger.isEnabledFor(logging.INFO):
                self.logger.info("Cleared transport cache at %s", self._cache_dir)
        except Exception:
            pass

    def _try_load_cache(self, tag: str) -> bool:
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("Transport cache lookup tag=%s dir=%s", tag, self._cache_dir)
        stations_pkl, tree_pkl = self._cache_paths(tag)
        try:
            with open(stations_pkl, "rb") as f:
                self._stations = pickle.load(f)
            with open(tree_pkl, "rb") as f:
                self._tree = pickle.load(f)
            self.logger.info("Transport cache HIT: %s", tag)
            return True
        except Exception:
            self.logger.info("Transport cache MISS: %s", tag)
            return False

    def _save_cache(self, tag: str) -> None:
        if self._stations is None or self._tree is None:
            return
        stations_pkl, tree_pkl = self._cache_paths(tag)
        try:
            with open(stations_pkl, "wb") as f:
                pickle.dump(self._stations, f)
            with open(tree_pkl, "wb") as f:
                pickle.dump(self._tree, f)
            self.logger.info("Saved transport cache for %s", tag)
        except Exception:
            pass

    def load_stations(self, stations_df: pd.DataFrame) -> None:
        """Load station catalog, exclude LRT, and build KDTree index.

        Parameters
        ----------
        stations_df : pd.DataFrame
            DataFrame with columns: ['name', 'line_code', 'lat', 'lon'].
        """
        if KDTree is None:
            raise ImportError(
                "scikit-learn not available. Install scikit-learn to use TransportScorer."
            )
        required = ["name", "lat", "lon"]
        missing = [c for c in required if c not in stations_df.columns]
        if missing:
            raise ValueError(f"Stations catalog missing columns: {missing}")

        df = stations_df.copy()
        # Normalize columns
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        # Try cache based on a stable tag (hash of station rows)
        tag = "csv:" + hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values.tobytes()).hexdigest()[:16]
        if self._try_load_cache(tag):
            return
        if "line_code" in df.columns:
            df["line_code"] = df["line_code"].astype(str).str.upper()
        # Fallback: if line_code missing, try to infer non-LRT by name not containing 'LRT'
        df = self._exclude_lrt(df)
        if "line_code" not in df.columns:
            df = df[~df.get("name", pd.Series("")).astype(str).str.contains("LRT", case=False, na=False)]

        df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)

        if df.empty:
            raise ValueError("No MRT stations available after LRT exclusion.")

        coords = np.deg2rad(df[["lat", "lon"]].to_numpy(dtype=float))
        # Use haversine-compatible KDTree by projecting to radians and custom metric
        self._tree = KDTree(coords, metric="euclidean")
        self._stations = df
        self._save_cache(tag)
        self.logger.info("Loaded %d MRT stations (LRT excluded)", len(df))

    def load_stations_geojson(self, path: str) -> None:
        """Load MRT stations from an LTA Exit GeoJSON file and build KDTree.

        The GeoJSON is expected to be a FeatureCollection where each feature is
        a station exit with properties containing station information. This
        loader will:
        - Extract station name and line code from common property keys.
        - Strictly exclude LRT using the regex '^(BP|S[WE]|P[WE])' on line codes
          when available, and additionally filter out any stations with 'LRT' in
          the name as a safety fallback.
        - Build a KDTree over exit coordinates (lon, lat). Using exits provides
          accurate pedestrian access points for distance calculations.

        Parameters
        ----------
        path : str
            Path to the GeoJSON file.
        """
        if KDTree is None:
            raise ImportError(
                "scikit-learn not available. Install scikit-learn to use TransportScorer."
            )
        # Cache by file mtime and size for stability
        try:
            stat = os.stat(path)
            tag = f"geojson:{os.path.basename(path)}:{int(stat.st_mtime)}:{stat.st_size}"
            if self._try_load_cache(tag):
                return
        except Exception:
            tag = f"geojson:{os.path.basename(path)}"
        try:
            with open(path, "r", encoding="utf-8") as f:
                gj = json.load(f)
        except FileNotFoundError as exc:
            raise
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("Failed to read GeoJSON: %s", path)
            raise ValueError(f"Failed to read GeoJSON: {path}") from exc

        features = gj.get("features", []) if isinstance(gj, dict) else []
        rows: List[Tuple[str, Optional[str], float, float]] = []
        for feat in features:
            try:
                geom = feat.get("geometry", {})
                if not geom or geom.get("type") != "Point":
                    continue
                coords = geom.get("coordinates")
                if not coords or len(coords) < 2:
                    continue
                lon, lat = float(coords[0]), float(coords[1])
                props = feat.get("properties", {}) or {}
                # Candidate keys for station name and line
                name = (
                    props.get("STN_NAME")
                    or props.get("STN_NAM")
                    or props.get("NAME")
                    or props.get("StationName")
                    or props.get("stn_name")
                    or props.get("station")
                )
                line_code = (
                    props.get("LINE")
                    or props.get("LINE_CODE")
                    or props.get("LINE_N")
                    or props.get("MRT_LINE")
                    or props.get("railLine")
                    or props.get("line")
                )
                if name is None:
                    # Some datasets store station at 'STN_NAM' with exit codes separate
                    continue
                name_str = str(name).strip()
                lc_str = str(line_code).strip().upper() if line_code is not None else None
                rows.append((name_str, lc_str, lat, lon))
            except Exception:  # noqa: BLE001
                continue

        if not rows:
            raise ValueError("No station exits parsed from GeoJSON.")

        df = pd.DataFrame(rows, columns=["name", "line_code", "lat", "lon"])
        # Exclude LRT by line_code regex when available; also filter names containing 'LRT'
        df = self._exclude_lrt(df)
        df = df[~df["name"].astype(str).str.contains("LRT", case=False, na=False)]
        df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)
        if df.empty:
            raise ValueError("No MRT stations available after parsing/exclusion.")

        coords = np.deg2rad(df[["lat", "lon"]].to_numpy(dtype=float))
        self._tree = KDTree(coords, metric="euclidean")
        self._stations = df
        self._save_cache(tag)
        self.logger.info("Loaded %d MRT exits from GeoJSON (LRT excluded)", len(df))

    @staticmethod
    def _haversine_meters(latlon1: np.ndarray, latlon2: np.ndarray) -> np.ndarray:
        """Compute haversine distance in meters between arrays of points.

        Parameters
        ----------
        latlon1 : np.ndarray
            Array of shape (n, 2) with columns [lat_rad, lon_rad] in radians.
        latlon2 : np.ndarray
            Array of shape (n, 2) with columns [lat_rad, lon_rad] in radians.
        """
        R = 6371000.0  # meters
        dlat = latlon2[:, 0] - latlon1[:, 0]
        dlon = latlon2[:, 1] - latlon1[:, 1]
        a = np.sin(dlat / 2.0) ** 2 + np.cos(latlon1[:, 0]) * np.cos(latlon2[:, 0]) * np.sin(dlon / 2.0) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return R * c

    def calculate_accessibility_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Annotate DataFrame with nearest MRT and accessibility score.

        Adds columns:
        - Nearest_MRT: name of nearest heavy-rail MRT station
        - Dist_m: distance to nearest station in meters
        - Accessibility_Score: score = max(0, 10 - (dist_km * 2))

        Expectations: Input `df` must have 'lat' and 'lon' columns (degrees).
        """
        if self._tree is None or self._stations is None:
            raise RuntimeError("TransportScorer not initialized. Call load_stations first.")

        if not {"lat", "lon"}.issubset(set(df.columns)):
            # No-op if coords not present; add NaNs
            out = df.copy()
            out["Nearest_MRT"] = np.nan
            out["Dist_m"] = np.nan
            out["Accessibility_Score"] = np.nan
            return out

        pts = np.deg2rad(df[["lat", "lon"]].to_numpy(dtype=float))
        # KDTree query (k=1)
        dist_rad, ind = self._tree.query(pts, k=1)
        # Convert chord distance in radian-space to meters using haversine to nearest
        nearest_rad = self._stations[["lat", "lon"]].to_numpy(dtype=float)
        nearest_rad = np.deg2rad(nearest_rad[ind.flatten()])
        dist_m = self._haversine_meters(pts, nearest_rad)

        # Score: max(0, 10 - 2 * km)
        dist_km = dist_m / 1000.0
        score = np.maximum(0.0, 10.0 - (dist_km * 2.0))

        out = df.copy()
        out["Nearest_MRT"] = self._stations.loc[ind.flatten(), "name"].to_numpy()
        out["Dist_m"] = dist_m
        out["Accessibility_Score"] = score
        return out


class ReportGenerator:
    """Filter, rank, and render a clean buy list table to console.

    Filtering
    ---------
    - Optional exact/partial `town` filter.
    - Optional `budget` filter for maximum resale price.
    - Extended filters: flat_model, flat_type (exact or partial), storey_min/max,
      area_min/max, lease_min/max.

    Ranking
    -------
    - Sort by `valuation_score` descending (highest implies most undervalued),
      with ties broken by lowest price_efficiency and then lowest resale_price.
    - Display the top N results (default: 10).

    Rendering
    ---------
    - Human-friendly table using pandas' built-in formatting.
    """

    def __init__(self, schema: Schema | None = None) -> None:
        self.schema = schema or Schema()
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def _parse_storey_range(sr: str) -> Tuple[Optional[int], Optional[int]]:
        """Parse HDB storey range strings like "07 TO 09" into (min, max).

        Non-parsable inputs return (None, None).
        """
        try:
            s = str(sr).strip()
            parts = s.split("TO") if "TO" in s else s.split("-")
            parts = [p.strip() for p in parts]
            if len(parts) == 2:
                return int(parts[0]), int(parts[1])
            # Sometimes raw single like "10" or "01"
            v = int(s)
            return v, v
        except Exception:  # noqa: BLE001
            return None, None

    def _apply_filters(
        self,
        df: pd.DataFrame,
        town: Optional[str] = None,
        town_like: Optional[str] = None,
        budget: Optional[float] = None,
        flat_type: Optional[str] = None,
        flat_type_like: Optional[str] = None,
        flat_model: Optional[str] = None,
        flat_model_like: Optional[str] = None,
        storey_min: Optional[int] = None,
        storey_max: Optional[int] = None,
        area_min: Optional[float] = None,
        area_max: Optional[float] = None,
        lease_min: Optional[float] = None,
        lease_max: Optional[float] = None,
    ) -> pd.DataFrame:
        """Apply user-specified filters to DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            The scored dataset.
        town : Optional[str]
            Town name for exact case-insensitive filtering.
        town_like : Optional[str]
            Substring case-insensitive match for town.
        budget : Optional[float]
            Maximum resale price.
        flat_type : Optional[str]
            Exact match filter for flat_type (case-insensitive).
        flat_type_like : Optional[str]
            Substring match for flat_type.
        flat_model : Optional[str]
            Exact match filter for flat_model.
        flat_model_like : Optional[str]
            Substring match for flat_model.
        storey_min, storey_max : Optional[int]
            Min/max storey number filter (overlap with storey_range).
        area_min, area_max : Optional[float]
            Floor area filters.
        lease_min, lease_max : Optional[float]
            Remaining lease (years) filters.
        """
        s = self.schema
        out = df.copy()

        # Town filters
        if town:
            if s.town not in out.columns:
                self.logger.warning("Town column '%s' not found; skipping town filter", s.town)
            else:
                out = out[out[s.town].astype(str).str.lower() == town.strip().lower()]
        if town_like:
            if s.town not in out.columns:
                self.logger.warning("Town column '%s' not found; skipping town_like filter", s.town)
            else:
                out = out[out[s.town].astype(str).str.contains(town_like, case=False, na=False)]

        # Budget filter
        if budget is not None:
            if s.resale_price not in out.columns:
                self.logger.warning(
                    "Resale price column '%s' not found; skipping budget filter", s.resale_price
                )
            else:
                out = out[pd.to_numeric(out[s.resale_price], errors="coerce") <= float(budget)]

        # Flat type filters
        if flat_type and s.flat_type in out.columns:
            out = out[out[s.flat_type].astype(str).str.lower() == flat_type.strip().lower()]
        if flat_type_like and s.flat_type in out.columns:
            out = out[out[s.flat_type].astype(str).str.contains(flat_type_like, case=False, na=False)]

        # Flat model filters
        if flat_model and "flat_model" in out.columns:
            out = out[out["flat_model"].astype(str).str.lower() == flat_model.strip().lower()]
        if flat_model_like and "flat_model" in out.columns:
            out = out[out["flat_model"].astype(str).str.contains(flat_model_like, case=False, na=False)]

        # Area filters
        if area_min is not None and s.floor_area in out.columns:
            out = out[pd.to_numeric(out[s.floor_area], errors="coerce") >= float(area_min)]
        if area_max is not None and s.floor_area in out.columns:
            out = out[pd.to_numeric(out[s.floor_area], errors="coerce") <= float(area_max)]

        # Lease filters
        if lease_min is not None and s.remaining_lease_years in out.columns:
            out = out[pd.to_numeric(out[s.remaining_lease_years], errors="coerce") >= float(lease_min)]
        if lease_max is not None and s.remaining_lease_years in out.columns:
            out = out[pd.to_numeric(out[s.remaining_lease_years], errors="coerce") <= float(lease_max)]

        # Storey overlap filters via storey_range string
        if (storey_min is not None or storey_max is not None) and "storey_range" in out.columns:
            mins, maxs = [], []
            for v in out["storey_range"].tolist():
                mn, mx = self._parse_storey_range(v)
                mins.append(mn)
                maxs.append(mx)
            out = out.assign(__sr_min=mins, __sr_max=maxs)
            if storey_min is not None:
                out = out[(out["__sr_max"].fillna(-np.inf) >= int(storey_min))]
            if storey_max is not None:
                out = out[(out["__sr_min"].fillna(np.inf) <= int(storey_max))]
            out = out.drop(columns=["__sr_min", "__sr_max"])

        return out

    def generate_dataframe(
        self,
        df: pd.DataFrame,
        town: Optional[str] = None,
        town_like: Optional[str] = None,
        budget: Optional[float] = None,
        flat_type: Optional[str] = None,
        flat_type_like: Optional[str] = None,
        flat_model: Optional[str] = None,
        flat_model_like: Optional[str] = None,
        storey_min: Optional[int] = None,
        storey_max: Optional[int] = None,
        area_min: Optional[float] = None,
        area_max: Optional[float] = None,
        lease_min: Optional[float] = None,
        lease_max: Optional[float] = None,
        top_n: int = 10,
        full: bool = False,
    ) -> pd.DataFrame:
        """Produce the filtered, sorted DataFrame for display/export.

        If full is True, returns all rows after sorting; otherwise, returns the top_n rows.
        """
        s = self.schema
        filtered = self._apply_filters(
            df,
            town=town,
            town_like=town_like,
            budget=budget,
            flat_type=flat_type,
            flat_type_like=flat_type_like,
            flat_model=flat_model,
            flat_model_like=flat_model_like,
            storey_min=storey_min,
            storey_max=storey_max,
            area_min=area_min,
            area_max=area_max,
            lease_min=lease_min,
            lease_max=lease_max,
        )

        cols_pref = [
            s.town,
            s.flat_type,
            "flat_model" if "flat_model" in filtered.columns else None,
            "storey_range" if "storey_range" in filtered.columns else None,
            s.resale_price,
            s.floor_area,
            s.remaining_lease_years,
            s.price_efficiency,
            s.z_price_efficiency,
            s.valuation_score,
            "Nearest_MRT" if "Nearest_MRT" in filtered.columns else None,
            "Dist_m" if "Dist_m" in filtered.columns else None,
            "Accessibility_Score" if "Accessibility_Score" in filtered.columns else None,
        ]
        cols_exist = [c for c in cols_pref if c is not None and c in filtered.columns]

        display = filtered[cols_exist].copy()
        if s.valuation_score in display.columns:
            display = display.dropna(subset=[s.valuation_score])

        sort_cols: List[str] = []
        ascending: List[bool] = []
        if s.valuation_score in display.columns:
            sort_cols.append(s.valuation_score)
            ascending.append(False)
        if s.price_efficiency in display.columns:
            sort_cols.append(s.price_efficiency)
            ascending.append(True)
        if s.resale_price in display.columns:
            sort_cols.append(s.resale_price)
            ascending.append(True)
        if sort_cols:
            display = display.sort_values(by=sort_cols, ascending=ascending)

        # Round for presentation but keep raw dtype for export (we'll round a copy for printing)
        return display.head(top_n)

    def render(
        self,
        df: pd.DataFrame,
        town: Optional[str] = None,
        town_like: Optional[str] = None,
        budget: Optional[float] = None,
        flat_type: Optional[str] = None,
        flat_type_like: Optional[str] = None,
        flat_model: Optional[str] = None,
        flat_model_like: Optional[str] = None,
        storey_min: Optional[int] = None,
        storey_max: Optional[int] = None,
        area_min: Optional[float] = None,
        area_max: Optional[float] = None,
        lease_min: Optional[float] = None,
        lease_max: Optional[float] = None,
        top_n: int = 10,
    ) -> str:
        """Generate the formatted table for the buy list.

        The table prioritizes the most undervalued units by sorting on
        `valuation_score` desc, breaking ties by `price_efficiency` asc and
        `resale_price` asc.
        """
        s = self.schema
        self.logger.info(
            "Preparing report (filters: town=%s town_like=%s budget=%s)", town, town_like, budget
        )

        display = self.generate_dataframe(
            df,
            town=town,
            town_like=town_like,
            budget=budget,
            flat_type=flat_type,
            flat_type_like=flat_type_like,
            flat_model=flat_model,
            flat_model_like=flat_model_like,
            storey_min=storey_min,
            storey_max=storey_max,
            area_min=area_min,
            area_max=area_max,
            lease_min=lease_min,
            lease_max=lease_max,
            top_n=top_n,
        ).copy()

        # Round numeric columns for presentation
        for col, nd in [
            (s.resale_price, 0),
            (s.floor_area, 2),
            (s.remaining_lease_years, 2),
            (s.price_efficiency, 6),
            (s.z_price_efficiency, 3),
            (s.valuation_score, 3),
        ]:
            if col in display.columns:
                display[col] = pd.to_numeric(display[col], errors="coerce").round(nd)

        if display.empty:
            return "No results match the given filters or insufficient data to score."

        return display.to_string(index=False)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class HDBValuationEngineApp:
    """Application orchestrator wiring the pipeline and the CLI."""

    def __init__(self) -> None:
        self.schema = Schema()
        self.loader = HDBLoader(self.schema)
        self.fe = FeatureEngineer(self.schema)
        self.engine = ValuationEngine(self.schema)
        # Transport scorer with optional cache dir
        cache_dir = None
        self.transport = TransportScorer(cache_dir=cache_dir)
        self.reporter = ReportGenerator(self.schema)
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self, args: argparse.Namespace) -> int:
        """Execute the end-to-end pipeline and render the report.

        Parameters
        ----------
        args : argparse.Namespace
            Parsed CLI arguments.

        Returns
        -------
        int
            Exit code: 0 on success, non-zero on error.
        """
        try:
            df = self.loader.load(args.input)
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Aborting due to load error: %s", exc)
            return 2

        try:
            df = self.fe.parse_remaining_lease(df)
            df = self.fe.compute_price_efficiency(df)

            # Optionally load MRT stations for transport scoring
            if getattr(args, "mrt_catalog", None):
                try:
                    # Configure optional cache dir and clearing
                    if getattr(args, "transport_cache_dir", None):
                        self.transport._cache_dir = args.transport_cache_dir  # safe internal override
                        os.makedirs(self.transport._cache_dir, exist_ok=True)
                    if getattr(args, "clear_transport_cache", False):
                        self.transport.clear_cache()
                    # First try GeoJSON, else fall back to CSV
                    if str(args.mrt_catalog).lower().endswith(".geojson"):
                        self.transport.load_stations_geojson(args.mrt_catalog)
                    else:
                        stations_df = pd.read_csv(args.mrt_catalog)
                        self.transport.load_stations(stations_df)
                    df = self.transport.calculate_accessibility_score(df)
                except Exception as exc:  # noqa: BLE001
                    self.logger.warning("Transport scoring skipped due to error: %s", exc)

            # Apply configurable grouping keys for z-scores (with accessibility integration)
            group_by: Optional[List[str]] = None
            if hasattr(args, "group_by") and args.group_by:
                group_by = [g.strip().lower().replace(" ", "_") for g in args.group_by]

            # Integrate Accessibility_Score into valuation by adjusting price_efficiency
            # We reduce price_efficiency proportionally to accessibility (better accessibility lowers PE)
            # new_price_efficiency = price_efficiency / (1 + Accessibility_Score/10)
            do_adjust = ("Accessibility_Score" in df.columns) and (not getattr(args, "no_accessibility_adjust", False))
            if do_adjust:
                adj = 1.0 + (pd.to_numeric(df["Accessibility_Score"], errors="coerce") / 10.0)
                with np.errstate(divide="ignore", invalid="ignore"):
                    df[self.schema.price_efficiency] = df[self.schema.price_efficiency] / adj

            df = self.engine.score(df, group_by=group_by)
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("Processing failed: %s", exc)
            return 3

        try:
            # Build display DataFrame (Top-N for console)
            display_df = self.reporter.generate_dataframe(
                df,
                town=args.town,
                town_like=getattr(args, "town_like", None),
                budget=args.budget,
                flat_type=getattr(args, "flat_type", None),
                flat_type_like=getattr(args, "flat_type_like", None),
                flat_model=getattr(args, "flat_model", None),
                flat_model_like=getattr(args, "flat_model_like", None),
                storey_min=getattr(args, "storey_min", None),
                storey_max=getattr(args, "storey_max", None),
                area_min=getattr(args, "area_min", None),
                area_max=getattr(args, "area_max", None),
                lease_min=getattr(args, "lease_min", None),
                lease_max=getattr(args, "lease_max", None),
                top_n=args.top,
                full=False,
            )

            # Build export DataFrame (full or top-n)
            export_df = display_df
            if getattr(args, "export_full", False):
                export_df = self.reporter.generate_dataframe(
                    df,
                    town=args.town,
                    town_like=getattr(args, "town_like", None),
                    budget=args.budget,
                    flat_type=getattr(args, "flat_type", None),
                    flat_type_like=getattr(args, "flat_type_like", None),
                    flat_model=getattr(args, "flat_model", None),
                    flat_model_like=getattr(args, "flat_model_like", None),
                    storey_min=getattr(args, "storey_min", None),
                    storey_max=getattr(args, "storey_max", None),
                    area_min=getattr(args, "area_min", None),
                    area_max=getattr(args, "area_max", None),
                    lease_min=getattr(args, "lease_min", None),
                    lease_max=getattr(args, "lease_max", None),
                    top_n=args.top,
                    full=True,
                )

            # Render to console
            table = self.reporter.render(
                df,
                town=args.town,
                town_like=getattr(args, "town_like", None),
                budget=args.budget,
                flat_type=getattr(args, "flat_type", None),
                flat_type_like=getattr(args, "flat_type_like", None),
                flat_model=getattr(args, "flat_model", None),
                flat_model_like=getattr(args, "flat_model_like", None),
                storey_min=getattr(args, "storey_min", None),
                storey_max=getattr(args, "storey_max", None),
                area_min=getattr(args, "area_min", None),
                area_max=getattr(args, "area_max", None),
                lease_min=getattr(args, "lease_min", None),
                lease_max=getattr(args, "lease_max", None),
                top_n=args.top,
            )
            print(table)  # noqa: T201 - intentional CLI output

            # Export if requested
            if getattr(args, "output", None):
                try:
                    fmt = getattr(args, "output_format", "csv") or "csv"
                    if fmt == "csv":
                        export_df.to_csv(args.output, index=False)
                    elif fmt == "json":
                        export_df.to_json(args.output, orient="records", lines=False)
                    elif fmt == "parquet":
                        try:
                            export_df.to_parquet(args.output, index=False)
                        except Exception as parq_exc:  # noqa: BLE001
                            self.logger.warning(
                                "Parquet export failed (missing engine?). Falling back to CSV: %s",
                                parq_exc,
                            )
                            export_df.to_csv(args.output, index=False)
                    self.logger.info(
                        "Exported %s (%s) to %s", "full" if getattr(args, "export_full", False) else f"Top-{args.top}", fmt, args.output
                    )
                except Exception as exc:  # noqa: BLE001
                    self.logger.exception("Failed to export to %s: %s", args.output, exc)
                    return 5
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("Failed to render report: %s", exc)
            return 4

        return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build an argument parser for the CLI.

    Returns
    -------
    argparse.ArgumentParser
        Configured CLI parser.
    """
    parser = argparse.ArgumentParser(
        prog="hdb_valuation_engine",
        description=(
            f"HDB Valuation Engine v{__version__} — Identify undervalued HDB resale properties using a "
            + "lease-adjusted price efficiency metric and group-wise z-scores."
        ),
    )

    subparsers = parser.add_subparsers(dest="command")

    # Cache management subcommand
    cache_parser = subparsers.add_parser("cache", help="Manage transport cache")
    cache_parser.add_argument("--clear", action="store_true", help="Clear transport cache and exit")
    cache_parser.add_argument(
        "--transport-cache-dir",
        required=False,
        help=("Directory of transport cache (default: .cache_transport in CWD)."),
    )
    cache_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (use -v or -vv).",
    )

    # Data fetch subcommand (resale CSV)
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch a sample HDB resale dataset (or generate synthetic) into ResaleFlatPrices/",
        description=(
            "Fetch a CSV for optional smoke tests. Attempts public APIs; falls back to synthetic data if needed."
        ),
    )
    fetch_parser.add_argument("--limit", type=int, default=5000, help="Max rows to write (0 = all, default: 5000)")
    fetch_parser.add_argument(
        "--out-dir", default="ResaleFlatPrices", help="Output directory for HDB resale CSV (default: ResaleFlatPrices)"
    )
    fetch_parser.add_argument(
        "--filename",
        default="Resale flat prices based on registration date from Jan-2017 onwards.csv",
        help="HDB resale output filename (default: Resale flat prices based on registration date from Jan-2017 onwards.csv)",
    )
    fetch_parser.add_argument(
        "--mrt-out",
        default=os.path.join(".data", "LTAMRTStationExitGEOJSON.geojson"),
        help="Output path for MRT station exits GeoJSON (default: .data/LTAMRTStationExitGEOJSON.geojson)",
    )
    fetch_parser.add_argument(
        "--datasets",
        default="all",
        choices=["all", "resale", "mrt"],
        help="Datasets to fetch (default: all)",
    )
    fetch_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (use -v or -vv).",
    )

    parser.add_argument(
        "--input",
        required=False,
        help="Path to HDB resale CSV data.",
    )
    parser.add_argument(
        "--mrt-catalog",
        required=False,
        help=(
            "Optional path to MRT stations GEOJSON (LTA exits) or CSV [name,line_code,lat,lon]. "
            "LRT lines (BP, SW/SE, PW/PE) are auto-excluded. Enables accessibility scoring."
        ),
    )
    parser.add_argument(
        "--transport-cache-dir",
        required=False,
        help=(
            "Directory to store transport KDTree cache (default: .cache_transport in CWD)."
        ),
    )
    parser.add_argument(
        "--clear-transport-cache",
        action="store_true",
        help="Clear transport KDTree/stations cache before building.",
    )
    # Filtering options
    parser.add_argument("--town", required=False, help="Exact town filter (case-insensitive)")
    parser.add_argument("--town-like", dest="town_like", required=False, help="Partial town match (case-insensitive substring)")
    parser.add_argument("--flat-type", dest="flat_type", required=False, help="Exact flat_type filter")
    parser.add_argument("--flat-type-like", dest="flat_type_like", required=False, help="Partial flat_type match")
    parser.add_argument("--flat-model", dest="flat_model", required=False, help="Exact flat_model filter")
    parser.add_argument("--flat-model-like", dest="flat_model_like", required=False, help="Partial flat_model match")
    parser.add_argument("--storey-min", dest="storey_min", type=int, required=False, help="Minimum storey (overlaps any storey_range)")
    parser.add_argument("--storey-max", dest="storey_max", type=int, required=False, help="Maximum storey (overlaps any storey_range)")
    parser.add_argument("--area-min", dest="area_min", type=float, required=False, help="Minimum floor area (sqm)")
    parser.add_argument("--area-max", dest="area_max", type=float, required=False, help="Maximum floor area (sqm)")
    parser.add_argument("--lease-min", dest="lease_min", type=float, required=False, help="Minimum remaining lease (years)")
    parser.add_argument("--lease-max", dest="lease_max", type=float, required=False, help="Maximum remaining lease (years)")

    parser.add_argument(
        "--budget",
        type=float,
        required=False,
        help="Optional maximum budget for resale_price.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of results to display (default: 10).",
    )
    parser.add_argument(
        "--group-by",
        nargs="+",
        required=False,
        help=(
            "Columns to group by for peer comparison z-scores (default: town flat_type). "
            "Use dataset column names (case/space insensitive)."
        ),
    )
    parser.add_argument(
        "--output",
        required=False,
        help="Optional output path to export the filtered table (format controlled by --output-format).",
    )
    parser.add_argument(
        "--export-full",
        action="store_true",
        help="Export full filtered dataset (ignores --top for the file; console still shows Top-N).",
    )
    parser.add_argument(
        "--output-format",
        choices=["csv", "json", "parquet"],
        default="csv",
        help="Output file format when --output is provided (default: csv).",
    )
    parser.add_argument(
        "--no-accessibility-adjust",
        action="store_true",
        help=(
            "Compute and display accessibility metrics but do NOT adjust price_efficiency. "
            "Useful for analysis-only runs."
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (use -v or -vv).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"hdb_valuation_engine {__version__}",
        help="Show program version and exit.",
    )
    return parser


def _cli_fetch(limit: int, out_dir: str, filename: str, verbose: int = 0) -> int:
    import csv, time
    from typing import Iterable
    import requests

    log = logging.getLogger("fetch")

    def _dump_body(resp, max_len: int = 300):
        try:
            text = resp.text if hasattr(resp, 'text') else ''
            return (text[:max_len] + ("..." if len(text) > max_len else "")) if text else "<no body>"
        except Exception:
            return "<unavailable>"

    def _get(url: str, **kwargs):
        for attempt in range(3):
            try:
                if verbose:
                    log.debug("GET %s (attempt %d)", url, attempt + 1)
                r = requests.get(url, timeout=60, **kwargs)
                if verbose:
                    log.debug("%s -> %s", url, getattr(r, 'status_code', '?'))
                r.raise_for_status()
                return r
            except requests.HTTPError as e:
                if verbose and hasattr(e, 'response') and e.response is not None:
                    log.debug("HTTPError for %s: %s; body: %s", url, e, _dump_body(e.response))
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)
            except Exception as e:
                if verbose:
                    log.debug("Error fetching %s: %s", url, e)
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)
        raise RuntimeError("unreachable")

    # Preferred: use data.gov.sg initiate-download for a dataset id
    def _initiate_download(dataset_id: str) -> Optional[str]:
        try:
            resp = _get(f"https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/initiate-download")
            j = resp.json()
            # Expect something like { data: { url: 'https://...' } }
            url = (j.get('data') or {}).get('url') if isinstance(j, dict) else None
            return url
        except Exception:
            return None

    csv_url = None
    try:
        meta = _get("https://api-production.data.gov.sg/v2/public/api/collections/189/metadata").json()
        cm = (meta.get("data") or {}).get("collectionMetadata") or {}
        cds = cm.get("childDatasets") or []
        # childDatasets may be list of ids (str) or dicts with datasetId/id
        candidates: list[str] = []
        for item in cds:
            if isinstance(item, str):
                candidates.append(item)
            elif isinstance(item, dict):
                did = item.get("datasetId") or item.get("id") or item.get("datasetID")
                if isinstance(did, str):
                    candidates.append(did)
        # Try initiate-download for each dataset id until one works
        for did in candidates:
            url = _initiate_download(did)
            if url and url.lower().endswith(('.csv', '.zip')):
                csv_url = url
                break
    except Exception:
        csv_url = None

    # Last-resort fallback to a known public CSV URL pattern (may change)
    if not csv_url:
        csv_url = (
            "https://raw.githubusercontent.com/isomerpages/mnd/main/data/"
            "Resale%20flat%20prices%20based%20on%20registration%20date%20from%20Jan-2017%20onwards.csv"
        )

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)

    # Attempt to stream rows; on any error, generate synthetic
    try:
        r = _get(csv_url, stream=True)
        r.encoding = "utf-8"
        lines = (line.decode("utf-8") if isinstance(line, (bytes, bytearray)) else line for line in r.iter_lines())
        reader = csv.reader(lines)
        header = next(reader)
        # Write rows; respect limit if > 0, else write all
        written = 0
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            for row in reader:
                w.writerow(row)
                written += 1
                if limit and written >= limit:
                    break
        logging.getLogger("fetch").info("Wrote %d rows to %s", written, out_path)
        return 0
    except Exception as e:
        logging.getLogger("fetch").warning("Fetch failed (%s). Generating synthetic dataset...", e)
        # Synthetic generator
        import random
        cols = [
            "month",
            "town",
            "flat_type",
            "block",
            "street_name",
            "storey_range",
            "floor_area_sqm",
            "flat_model",
            "lease_commence_date",
            "remaining_lease",
            "resale_price",
        ]
        towns = [
            "ANG MO KIO","BEDOK","BISHAN","BUKIT BATOK","BUKIT MERAH","BUKIT PANJANG",
            "BUKIT TIMAH","CENTRAL AREA","CHOA CHU KANG","CLEMENTI","GEYLANG","HOUGANG",
            "JURONG EAST","JURONG WEST","KALLANG/WHAMPOA","MARINE PARADE","PASIR RIS",
            "PUNGGOL","QUEENSTOWN","SEMBAWANG","SENGKANG","SERANGOON","TAMPINES",
            "TOA PAYOH","WOODLANDS","YISHUN"
        ]
        types = ["2 ROOM","3 ROOM","4 ROOM","5 ROOM","EXECUTIVE"]
        models = ["Improved","New Generation","Model A","Standard","Simplified","Premium Apartment","Apartment","Maisonette"]
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for i in range(min(limit, 10000)):
                year = 2017 + random.randint(0, 3)
                month = f"{year}-{random.randint(1,12):02d}"
                town = random.choice(towns)
                ft = random.choice(types)
                block = str(random.randint(1, 999))
                street = f"STREET {chr(65 + random.randint(0,25))}"
                sm = 1 + 3 * random.randint(0, 13)
                sr = f"{sm:02d} TO {sm+2:02d}"
                area = random.choice({"2 ROOM":[35,45],"3 ROOM":[60,65,70],"4 ROOM":[80,90,95],"5 ROOM":[105,110,120],"EXECUTIVE":[120,130,140]}.get(ft,[60,90,110]))
                model = random.choice(models)
                lcy = random.randint(1970, 2015)
                years_elapsed = max(0, year - lcy)
                remy = max(1, 99 - years_elapsed)
                rem = f"{remy} years {random.randint(0,11):02d} months"
                base_psm = 4000 + random.randint(-300, 600)
                lease_factor = 0.6 + 0.4 * (remy/99)
                town_factor = 0.9 + 0.2 * (town in {"QUEENSTOWN","BISHAN","BUKIT TIMAH","MARINE PARADE"})
                price = int(area * base_psm * lease_factor * town_factor * (0.9 + 0.2 * random.random()))
                w.writerow({
                    "month": month,
                    "town": town,
                    "flat_type": ft,
                    "block": block,
                    "street_name": street,
                    "storey_range": sr,
                    "floor_area_sqm": area,
                    "flat_model": model,
                    "lease_commence_date": lcy,
                    "remaining_lease": rem,
                    "resale_price": price,
                })
        logging.getLogger("fetch").info("Wrote synthetic dataset to %s", out_path)
        return 0



def main(argv: Optional[List[str]] = None) -> int:
    """Program entrypoint.

    Parameters
    ----------
    argv : Optional[List[str]]
        Optional override for sys.argv[1:]. Useful for testing.

    Returns
    -------
    int
        Process exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(getattr(args, "verbose", 0))

    # Handle cache subcommand
    if getattr(args, "command", None) == "cache":
        # create a scorer with provided or default cache dir
        cache_dir = getattr(args, "transport_cache_dir", None)
        scorer = TransportScorer(cache_dir=cache_dir)
        if getattr(args, "clear", False):
            scorer.clear_cache()
            return 0
        # if no explicit action, print cache dir and exit
        logging.getLogger("Cache").info("Transport cache dir: %s", scorer._cache_dir)
        return 0

    # Handle fetch subcommand
    if getattr(args, "command", None) == "fetch":
        limit = getattr(args, "limit", 5000)
        out_dir = getattr(args, "out_dir", "ResaleFlatPrices")
        filename = getattr(args, "filename", "Resale flat prices based on registration date from Jan-2017 onwards.csv")
        datasets = getattr(args, "datasets", "all")
        mrt_out = getattr(args, "mrt_out", os.path.join(".data", "LTAMRTStationExitGEOJSON.geojson"))
        rc = 0
        if datasets in ("all", "resale"):
            rc |= _cli_fetch(limit=limit, out_dir=out_dir, filename=filename, verbose=getattr(args, 'verbose', 0))
        if datasets in ("all", "mrt"):
            # inline minimal MRT fetch with synthetic fallback
            try:
                import requests, time
                def _get(url: str, **kwargs):
                    for attempt in range(3):
                        try:
                            r = requests.get(url, timeout=60, **kwargs)
                            r.raise_for_status()
                            return r
                        except Exception:
                            if attempt == 2:
                                raise
                            time.sleep(1 + attempt)
                    raise RuntimeError("unreachable")

                os.makedirs(os.path.dirname(mrt_out) or ".", exist_ok=True)
                meta = _get("https://api-production.data.gov.sg/v2/public/api/collections/367/metadata").json()
                data = meta.get("data", {})
                cm = data.get("collectionMetadata", {})
                gj_url = None
                # probe assets and child datasets
                def _assets(d: dict):
                    acc = []
                    for key in ("assets", "releases"):
                        v = d.get(key)
                        if isinstance(v, list):
                            for item in v:
                                if isinstance(item, dict) and "assets" in item:
                                    acc.extend(item.get("assets") or [])
                                elif isinstance(item, dict):
                                    acc.append(item)
                        elif isinstance(v, dict):
                            acc.extend(v.get("assets") or [])
                    return acc
                assets = _assets(cm)
                if not assets:
                    cds = cm.get("childDatasets") or []
                    for did in cds:
                        dm = _get(f"https://api-production.data.gov.sg/v2/public/api/datasets/{did}/metadata").json()
                        dmd = dm.get("data", {}).get("datasetMetadata", {})
                        assets = _assets(dmd)
                        if assets:
                            break
                for a in assets:
                    if not isinstance(a, dict):
                        continue
                    fmt = (a.get("fileFormat") or a.get("format") or "").lower()
                    url = a.get("downloadUrl") or a.get("url") or a.get("href")
                    name = (a.get("name") or a.get("title") or "").lower()
                    if url and (fmt in {"geojson", "json"} or str(url).lower().endswith(".geojson")) and (
                        "mrt" in name or "station" in name or "exit" in name
                    ):
                        gj_url = url
                        break
                if not gj_url:
                    raise RuntimeError("no geojson url")
                r = _get(gj_url)
                with open(mrt_out, "wb") as f:
                    f.write(r.content)
                logging.getLogger("fetch").info("Wrote MRT GeoJSON to %s", mrt_out)
            except Exception as e:
                import json
                logging.getLogger("fetch").warning("Fetch MRT failed (%s). Writing synthetic...", e)
                sample = {
                    "type": "FeatureCollection",
                    "features": [
                        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [103.851959, 1.290270]}, "properties": {"STN_NAME": "RAFFLES PLACE", "LINE": "NS"}},
                        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [103.845, 1.3008]}, "properties": {"STN_NAME": "BUGIS", "LINE": "DT"}},
                    ],
                }
                with open(mrt_out, "w", encoding="utf-8") as f:
                    json.dump(sample, f)
                logging.getLogger("fetch").info("Wrote synthetic MRT GeoJSON to %s", mrt_out)
        return rc

    app = HDBValuationEngineApp()
    return app.run(args)


if __name__ == "__main__":
    sys.exit(main())
