# soil_profile_collection.py
"""
# A Python module replicating some core functionality of the aqp R package's
# SoilProfileCollection object.
"""

import pandas as pd
import numpy as np
from typing import List, Union, Optional, Tuple, Dict, Any, Callable

# --- Helper Functions ---


def _select_hz_by_iloc(df_group, j_sel, top_col):
    """Selects horizons using iloc after sorting by top_col."""
    df_sorted = df_group.sort_values(by=top_col)
    try:
        return df_sorted.iloc[j_sel]
    except IndexError:
        return pd.DataFrame(columns=df_group.columns).astype(df_group.dtypes)
    except Exception as e:
        print(f"Warning: Error applying j selector within group: {e}")
        return pd.DataFrame(columns=df_group.columns).astype(df_group.dtypes)


def _validate_depths(
    horizons_df: pd.DataFrame, idname: str, topcol: str, bottomcol: str
) -> List[str]:
    """Checks for depth logic errors within profiles."""
    errors = []
    if not pd.api.types.is_numeric_dtype(horizons_df[topcol]):
        errors.append(f"Top depth column '{topcol}' is not numeric.")
    if not pd.api.types.is_numeric_dtype(horizons_df[bottomcol]):
        errors.append(f"Bottom depth column '{bottomcol}' is not numeric.")
    if errors:
        return errors

    # Check top <= bottom
    invalid_thickness = horizons_df[horizons_df[topcol] > horizons_df[bottomcol]]
    if not invalid_thickness.empty:
        errors.append(f"Found {len(invalid_thickness)} horizons where top depth > bottom depth.")

    # Check for gaps and overlaps within profiles
    for profile_id, horizons in horizons_df.groupby(idname):
        if horizons.empty:
            continue  # Should not happen if validation is correct, but safe

        horizons_sorted = horizons.sort_values(by=topcol)

        # Check for overlaps (bottom of horizon i > top of horizon i+1)
        overlaps = horizons_sorted[bottomcol] > horizons_sorted[topcol].shift(-1)

        # Check for gaps (bottom of horizon i < top of horizon i+1)
        gaps = horizons_sorted[bottomcol] < horizons_sorted[topcol].shift(-1)

        # Ignore the last horizon comparison (will be NaN)
        if overlaps.iloc[:-1].any():
            overlap_hzids = horizons_sorted.iloc[:-1][overlaps.iloc[:-1]].index
            errors.append(
                f"Profile ID '{profile_id}' has overlapping horizons (e.g., around horizon ID(s) {list(overlap_hzids)})."
            )
        # Check for gaps, ignoring the last horizon which has no 'next' horizon to compare to
        if gaps.iloc[:-1].any():
            valid_gaps = gaps.iloc[:-1]
            gap_indices = valid_gaps[valid_gaps].index
            gap_diffs = (
                horizons_sorted[topcol].shift(-1).loc[gap_indices]
                - horizons_sorted.loc[gap_indices, bottomcol]
            )
            # If ANY gap is found that is NOT close to zero, it's a real gap.
            if np.any(~np.isclose(gap_diffs, 0, atol=1e-9)):
                first_gap_hzid = gap_indices[0]
                errors.append(
                    f"Profile ID '{profile_id}' has depth gaps between horizons (e.g., after horizon ID '{first_gap_hzid}')."
                )

        # Check for duplicated depths within a profile (e.g., two horizons 0-10)
        depth_pairs = horizons[[topcol, bottomcol]].apply(tuple, axis=1)
        if depth_pairs.duplicated().any():
            errors.append(f"Profile ID '{profile_id}' has horizons with identical depth ranges.")

    return errors


def _glom_single_profile(
    profile_horizons: pd.DataFrame,
    id_col: str,
    top_col: str,
    bottom_col: str,
    slice_intervals: List[Tuple[float, float]],
    vars_to_agg: List[str],
    agg_fun: str,
) -> pd.DataFrame:
    """
    Calculates aggregated values for one profile over defined slices
    using the specified aggregation function.

    Internal helper function for glom(). Supports 'weighted.mean', 'sum',
    'min', 'max', and 'dominant'.
    """
    if profile_horizons.empty:
        return pd.DataFrame()

    profile_id = profile_horizons[id_col].iloc[0]
    results = []
    profile_horizons = profile_horizons.sort_values(by=top_col)

    for z_top, z_bottom in slice_intervals:
        # --- Initialize accumulators for the slice ---
        weighted_sums = {var: 0.0 for var in vars_to_agg}
        valid_weights = {var: 0.0 for var in vars_to_agg}
        current_mins = {var: np.inf for var in vars_to_agg}
        current_maxs = {var: -np.inf for var in vars_to_agg}
        seen_valid = {var: False for var in vars_to_agg}
        # For dominant: store list of (thickness, value) tuples for valid contributors
        dominant_contributors: Dict[str, List[tuple]] = {var: [] for var in vars_to_agg}

        # --- Iterate through horizons of this profile ---
        for _, hz_row in profile_horizons.iterrows():
            h_top = hz_row[top_col]
            h_bottom = hz_row[bottom_col]

            if pd.isna(h_top) or pd.isna(h_bottom) or h_top >= h_bottom:
                continue

            overlap_start = max(h_top, z_top)
            overlap_end = min(h_bottom, z_bottom)
            overlap_thickness = overlap_end - overlap_start

            # --- Process only if there's positive overlap ---
            if overlap_thickness > 1e-9:
                # total_overlap_thickness_in_slice += overlap_thickness

                for var in vars_to_agg:
                    value = hz_row[var]
                    # Only process non-missing values from horizons
                    if pd.notna(value):
                        # Accumulate for relevant functions
                        if agg_fun in ["weighted.mean", "sum"]:
                            weighted_sums[var] += value * overlap_thickness
                            valid_weights[var] += overlap_thickness
                        if agg_fun in ["min", "max"]:
                            # Update min/max (already handles first value correctly)
                            current_mins[var] = min(current_mins[var], value)
                            current_maxs[var] = max(current_maxs[var], value)
                            seen_valid[var] = True  # Mark that we saw at least one value
                        if agg_fun == "dominant":
                            # Store contribution: (thickness, value)
                            dominant_contributors[var].append((overlap_thickness, value))
                            seen_valid[var] = True  # Mark seen for dominant context too

        # --- Finalize calculation for the slice based on agg_fun ---
        slice_result = {id_col: profile_id, "top": z_top, "bottom": z_bottom}

        for var in vars_to_agg:
            final_value = np.nan  # Default to NaN
            if agg_fun == "weighted.mean":
                if valid_weights[var] > 1e-9:
                    final_value = weighted_sums[var] / valid_weights[var]
            elif agg_fun == "sum":
                if valid_weights[var] > 1e-9:
                    final_value = weighted_sums[var]
            elif agg_fun == "min":
                if seen_valid[var]:
                    final_value = current_mins[var]
            elif agg_fun == "max":
                if seen_valid[var]:
                    final_value = current_maxs[var]
            elif agg_fun == "dominant":
                # Find the contribution with the maximum thickness
                if dominant_contributors[var]:
                    dominant_contribution = max(
                        dominant_contributors[var], key=lambda item: item[0]
                    )
                    final_value = dominant_contribution[1]

            slice_result[var] = final_value

        results.append(slice_result)

    return pd.DataFrame(results) if results else pd.DataFrame()


def _slice_single_profile(
    profile_horizons: pd.DataFrame,
    id_col: str,
    top_col: str,
    bottom_col: str,
    slice_intervals: List[Tuple[float, float]],
    original_hzid_col: str,
    truncate: bool,
    first_interval_top: float,
    last_interval_bottom: float,
) -> pd.DataFrame:
    """
    Creates new horizon segments representing the intersection of original
    horizons with specified depth intervals, respecting the truncate flag.

    Internal helper function for glom(..., agg_fun=None).
    """
    sliced_segments = []
    profile_horizons_sorted = profile_horizons.sort_values(by=top_col)

    for _, hz_row in profile_horizons_sorted.iterrows():
        h_top = hz_row[top_col]
        h_bottom = hz_row[bottom_col]

        if pd.isna(h_top) or pd.isna(h_bottom) or h_top >= h_bottom:
            continue

        for z_top, z_bottom in slice_intervals:
            overlap_start = max(h_top, z_top)
            overlap_end = min(h_bottom, z_bottom)
            overlap_thickness = overlap_end - overlap_start

            if overlap_thickness > 1e-9:
                # Start with truncated boundaries
                segment_top = overlap_start
                segment_bottom = overlap_end

                # Adjust boundaries if truncate is False and it's an edge interval
                if not truncate:
                    # Check if this segment overlaps the very first interval
                    if z_top == first_interval_top and h_top < z_top:
                        segment_top = h_top  # Extend top to original horizon top

                    # Check if this segment overlaps the very last interval
                    if z_bottom == last_interval_bottom and h_bottom > z_bottom:
                        segment_bottom = h_bottom  # Extend bottom to original horizon bottom

                # Create the segment record
                new_segment_data = hz_row.to_dict()
                new_segment_data[top_col] = segment_top
                new_segment_data[bottom_col] = segment_bottom
                sliced_segments.append(new_segment_data)

    return pd.DataFrame(sliced_segments)


# --- SoilProfileCollection class ---


class SoilProfileCollection:
    @classmethod
    def from_dataframe(
        cls,
        data: pd.DataFrame,
        schema_template: Dict[str, str],
        idname: Optional[str] = None,
        hzidname: Optional[str] = None,
        depthcols: Optional[Tuple[str, str]] = None,
        hzdesgncol: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        crs: Optional[Any] = None,
        validate: bool = True,
    ):
        """
        Creates a SoilProfileCollection object from a DataFrame based on a schema template.

        Args:
            data: DataFrame containing the soil profile data.
            schema_template: A dictionary mapping source column names in `data`
                             to the target column names required by SoilProfileCollection.
                             Example: {'profile_id': 'id', 'hz_id': 'hzid', 'top_depth': 'top',
                                       'bottom_depth': 'bottom', 'hz_name': 'hzname'}
            idname: Target column name for profile IDs. If None, inferred from schema_template.
            hzidname: Target column name for unique horizon IDs. If None, inferred from schema.
            depthcols: Tuple of (top, bottom) column names. If None, inferred from schema.
            hzdesgncol: Optional target column name for horizon designations. If None, inferred.
            metadata: Optional dictionary for metadata.
            crs: Optional Coordinate Reference System information.
            validate: If True (default), performs validation checks on initialization.

        Returns:
            A new SoilProfileCollection instance.

        Example:
            >>> schema = {
            ...     'profile_id': 'id',
            ...     'hz_id': 'hzid',
            ...     'top_depth': 'top',
            ...     'bottom_depth': 'bottom',
            ...     'hz_name': 'hzname'
            ... }
            >>> spc = SoilProfileCollection.from_dataframe(df, schema)
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("`data` must be a pandas DataFrame.")
        if not isinstance(schema_template, dict):
            raise TypeError("`schema_template` must be a dictionary.")

        # Infer standard column names from schema_template if not provided
        # The schema maps source_name -> target_name, so check if standard names are in values
        inferred_standard_names = set(schema_template.values())

        # Infer idname (look for mapping to 'id')
        if idname is None:
            idname = "id" if "id" in inferred_standard_names else "id"

        # Infer hzidname (look for mapping to 'hzid')
        if hzidname is None:
            hzidname = "hzid" if "hzid" in inferred_standard_names else "hzid"

        # Infer depthcols (look for mappings to 'top' and 'bottom')
        if depthcols is None:
            has_top = "top" in inferred_standard_names
            has_bottom = "bottom" in inferred_standard_names
            top_col = "top" if has_top else "top"
            bottom_col = "bottom" if has_bottom else "bottom"
            depthcols = (top_col, bottom_col)

        # Infer hzdesgncol (look for mapping to 'hzname')
        if hzdesgncol is None:
            hzdesgncol = "hzname" if "hzname" in inferred_standard_names else None

        # Make a copy to avoid modifying the original DataFrame
        processed_data = data.copy()

        # Rename columns based on the schema template
        processed_data.rename(columns=schema_template, inplace=True)

        # For now, assume all data is horizon data and derive site data.
        # A more advanced implementation will split site/horizon data based on the template.
        horizons_df = processed_data

        # A minimal site DataFrame will be created by the SPC constructor
        site_df = None

        return cls(
            horizons=horizons_df,
            site=site_df,
            idname=idname,
            hzidname=hzidname,
            depthcols=depthcols,
            hzdesgncol=hzdesgncol,
            metadata=metadata,
            crs=crs,
            validate=validate,
        )

    """
    Represents a collection of soil profiles, similar to aqp::SoilProfileCollection.

    Attributes:
        horizons (pd.DataFrame): DataFrame containing horizon-level data.
                                 Must contain columns specified by idname, hzidname,
                                 and depthcols. Indexed by hzidname.
        site (pd.DataFrame): DataFrame containing site/profile-level data.
                             Must contain the column specified by idname.
                             Indexed by idname.
        idname (str): Name of the column uniquely identifying profiles (in both site and horizons).
        hzidname (str): Name of the column uniquely identifying horizons (in horizons).
        depthcols (Tuple[str, str]): Tuple containing the names of the top and bottom depth columns.
        hzdesgncol (Optional[str]): Name of the horizon designation column (e.g., 'hzname').
        metadata (Dict[str, Any]): Dictionary for storing metadata about the collection.
        crs (Optional[Any]): Coordinate Reference System information (can be EPSG code, WKT string, etc.).
                               Not actively used in base functionality but stored.
    """

    def __init__(
        self,
        horizons: pd.DataFrame,
        site: Optional[pd.DataFrame] = None,
        idname: str = "id",
        hzidname: str = "hzid",
        depthcols: Tuple[str, str] = ("top", "bottom"),
        hzdesgncol: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        crs: Optional[Any] = None,
        validate: bool = True,
    ):
        """
        Initializes the SoilProfileCollection object.

        Args:
            horizons: DataFrame with horizon data.
            site: Optional DataFrame with site data. If None, site data is
                  derived from unique profile IDs in the horizons table.
            idname: Column name for profile IDs.
            hzidname: Column name for unique horizon IDs.
            depthcols: Tuple of (top_depth_column_name, bottom_depth_column_name).
            hzdesgncol: Optional column name for horizon designations.
            metadata: Optional dictionary for metadata.
            crs: Optional Coordinate Reference System information.
            validate: If True (default), performs validation checks on initialization.
        """
        if not isinstance(horizons, pd.DataFrame):
            raise TypeError("`horizons` must be a pandas DataFrame.")
        if site is not None and not isinstance(site, pd.DataFrame):
            raise TypeError("`site` must be a pandas DataFrame or None.")
        if not isinstance(idname, str):
            raise TypeError("`idname` must be a string.")
        if not isinstance(hzidname, str):
            raise TypeError("`hzidname` must be a string.")
        if not (
            isinstance(depthcols, (list, tuple))
            and len(depthcols) == 2
            and isinstance(depthcols[0], str)
            and isinstance(depthcols[1], str)
        ):
            raise TypeError("`depthcols` must be a list or tuple of two strings (top, bottom).")
        if hzdesgncol is not None and not isinstance(hzdesgncol, str):
            raise TypeError("`hzdesgncol` must be a string or None.")

        # --- Store core attributes ---
        self._idname = idname
        self._hzidname = hzidname
        self._depthcols: Tuple[str, str] = tuple(depthcols)  # type: ignore
        self._topcol, self._bottomcol = self._depthcols
        self._hzdesgncol = hzdesgncol
        self._metadata = metadata.copy() if metadata else {}
        self._crs = crs

        # --- Process and validate horizons ---
        h = horizons.copy()
        # Check required horizon columns
        required_hz_cols = [self._idname, self._hzidname, self._topcol, self._bottomcol]
        if self._hzdesgncol and self._hzdesgncol not in h.columns:
            print(
                f"Warning: Horizon designation column '{self._hzdesgncol}' not found in horizons."
            )
            self._hzdesgncol = None  # Reset if not found
        elif self._hzdesgncol:
            required_hz_cols.append(self._hzdesgncol)

        missing_hz_cols = [col for col in required_hz_cols if col not in h.columns]
        if missing_hz_cols:
            raise KeyError(f"Horizon data missing required columns: {missing_hz_cols}")

        # Check horizon ID uniqueness
        if not h[self._hzidname].is_unique:
            raise ValueError(f"Horizon ID column ('{self._hzidname}') contains duplicate values.")

        # Set horizon index
        try:
            h = h.set_index(self._hzidname, drop=False)  # Keep column for reference
        except KeyError:
            raise KeyError(f"Horizon ID column ('{self._hzidname}') not found in horizons data.")
        h.index.name = f"{self._hzidname}_idx"  # Avoid clash if hzidname is index name

        self._horizons = h

        # --- Process and validate site ---
        if site is None:
            # Create minimal site table from unique profile IDs in horizons
            site_ids = self._horizons[self._idname].unique()
            self._site = pd.DataFrame({self._idname: site_ids}).set_index(self._idname)
            self._site.index.name = f"{self._idname}_idx"
        else:
            s = site.copy()
            # Check required site column
            if self._idname not in s.columns:
                raise KeyError(f"Site data missing required profile ID column: '{self._idname}'")

            # Check site ID uniqueness
            if s[self._idname].duplicated().any():
                raise ValueError(
                    f"Profile ID column ('{self._idname}') in site data contains duplicate values."
                )

            # Set site index
            try:
                s = s.set_index(self._idname, drop=False)  # Keep column for potential joins
            except KeyError:
                raise KeyError(f"Profile ID column ('{self._idname}') not found in site data.")
            s.index.name = f"{self._idname}_idx"  # Avoid clash

            self._site = s

        # --- Final Cross-Validation ---
        # Check if all profile IDs in horizons exist in the site table
        hz_prof_ids = set(self._horizons[self._idname].unique())
        site_prof_ids = set(self._site.index)  # Index is profile ID

        if not hz_prof_ids.issubset(site_prof_ids):
            missing_in_site = hz_prof_ids - site_prof_ids
            raise ValueError(
                f"Profile IDs found in horizons but not in site data: {missing_in_site}"
            )

        orphaned_sites = site_prof_ids - hz_prof_ids
        if orphaned_sites:
            print(
                f"Warning: Site data contains profile IDs with no matching horizons: {orphaned_sites}"
            )

        # Perform depth validation if requested
        if validate:
            depth_errors = _validate_depths(
                self._horizons, self._idname, self._topcol, self._bottomcol
            )
            if depth_errors:
                raise ValueError("Depth validation failed:\n- " + "\n- ".join(depth_errors))

        # Store profile IDs for quick access
        self._profile_ids = self._site.index.tolist()

    # --- Properties for safe access ---
    @property
    def idname(self) -> str:
        """Name of the profile ID column."""
        return self._idname

    @property
    def hzidname(self) -> str:
        """Name of the horizon ID column."""
        return self._hzidname

    @property
    def depthcols(self) -> Tuple[str, str]:
        """Tuple of (top_depth_col, bottom_depth_col)."""
        return self._depthcols

    @property
    def hzdesgncol(self) -> Optional[str]:
        """Name of the horizon designation column, if set."""
        return self._hzdesgncol

    @property
    def metadata(self) -> Dict[str, Any]:
        """Metadata dictionary associated with the collection."""
        return self._metadata

    @property
    def crs(self) -> Any:
        """Coordinate Reference System information."""
        return self._crs

    @property
    def site(self) -> pd.DataFrame:
        """Returns a copy of the site data DataFrame."""
        return self._site.copy()

    @property
    def horizons(self) -> pd.DataFrame:
        """Returns a copy of the horizons data DataFrame."""
        return self._horizons.copy()

    @property
    def profile_ids(self) -> List[Any]:
        """Returns a list of unique profile IDs in the collection."""
        # return self._profile_ids # This is static after init
        return (
            self._site.index.tolist()
        )  # Recalculate in case site was modified externally (bad practice!)

    # --- Core Methods ---
    def __len__(self) -> int:
        """Returns the number of profiles in the collection."""
        return len(self._site)

    def __repr__(self) -> str:
        """String representation for console output."""
        n_prof = len(self)
        n_hz = len(self._horizons)
        repr_str = f"<SoilProfileCollection> ({n_prof} profiles, {n_hz} horizons)\n"
        repr_str += f"  Profile ID:   {self.idname}\n"
        repr_str += f"  Horizon ID:   {self.hzidname}\n"
        repr_str += f"  Depth Cols:   {self.depthcols[0]} (top), {self.depthcols[1]} (bottom)\n"

        # --- Updated Depth Range Calculation using self.depths() DataFrames ---
        min_depth_str = "Not computed"
        max_depth_str = "Not computed"
        calculation_possible = True

        # Preliminary check if horizons exist and depth cols appear numeric
        if (
            self._horizons.empty
            or not pd.api.types.is_numeric_dtype(self._horizons.get(self._topcol))
            or not pd.api.types.is_numeric_dtype(self._horizons.get(self._bottomcol))
        ):
            min_depth_str += " (check horizon data/depth columns)."
            max_depth_str += " (check horizon data/depth columns)."
            calculation_possible = False

        if calculation_possible:
            try:
                # 1. Get profile min depths DataFrame
                profile_mins_df = self.depths(how="min")  # DataFrame: idname, min_depth
                # Extract the 'min_depth' Series for summary stats, dropping NaNs
                valid_min_depths = profile_mins_df["min_depth"].dropna()

                # 2. Get profile max depths DataFrame
                profile_maxs_df = self.depths(how="max")  # DataFrame: idname, max_depth
                # Extract the 'max_depth' Series for summary stats, dropping NaNs
                valid_max_depths = profile_maxs_df["max_depth"].dropna()

                # 3. Summarize the minimum profile top depths
                if not valid_min_depths.empty:
                    min_of_mins = valid_min_depths.min()
                    mean_of_mins = valid_min_depths.mean()
                    max_of_mins = valid_min_depths.max()
                    if pd.notna([min_of_mins, mean_of_mins, max_of_mins]).all():
                        min_depth_str = f"[min: {min_of_mins:.1f}, mean: {mean_of_mins:.1f}, max: {max_of_mins:.1f}]"
                    else:
                        min_depth_str = "[NaN result]"
                else:
                    min_depth_str = "[no valid profiles]"

                # 4. Summarize the maximum profile bottom depths
                if not valid_max_depths.empty:
                    min_of_maxs = valid_max_depths.min()
                    mean_of_maxs = valid_max_depths.mean()
                    max_of_maxs = valid_max_depths.max()
                    if pd.notna([min_of_maxs, mean_of_maxs, max_of_maxs]).all():
                        max_depth_str = f"[min: {min_of_maxs:.1f}, mean: {mean_of_maxs:.1f}, max: {max_of_maxs:.1f}]"
                    else:
                        max_depth_str = "[NaN result]"
                else:
                    max_depth_str = "[no valid profiles]"

            except (TypeError, KeyError, Exception) as e:
                print(
                    f"\nWarning: Error calculating depth summary in __repr__: {type(e).__name__} - {e}"
                )
                min_depth_str = "[Error during calculation]"
                max_depth_str = "[Error during calculation]"

        # Add formatted strings to the main repr string
        repr_str += f"  Profile Top Depths:    {min_depth_str}\n"
        repr_str += f"  Profile Bottom Depths: {max_depth_str}\n"

        # --- Show variable lists (unchanged) ---
        if self.hzdesgncol:
            repr_str += f"  Hz Desgn Col: {self.hzdesgncol}\n"
        if self.crs:
            crs_str = str(self.crs)
            repr_str += f"  CRS:          {crs_str[:60]}{'...' if len(crs_str) > 60 else ''}\n"
        site_cols = list(self._site.columns)
        hz_cols = list(self._horizons.columns)
        site_cols_display = [c for c in site_cols if c != self._site.index.name]
        hz_cols_display = [c for c in hz_cols if c != self._horizons.index.name]
        repr_str += f"  Site Vars:    {', '.join(site_cols_display[:5])}{'...' if len(site_cols_display) > 5 else ''} ({len(site_cols_display)} total)\n"
        repr_str += f"  Horizon Vars: {', '.join(hz_cols_display[:5])}{'...' if len(hz_cols_display) > 5 else ''} ({len(hz_cols_display)} total)\n"

        return repr_str

    def __str__(self) -> str:
        """User-friendly string representation."""
        return self.__repr__()

    def __getitem__(
        self, key: Union[int, slice, list, tuple, pd.Series, np.ndarray]
    ) -> "SoilProfileCollection":
        """
        Subsetting the SoilProfileCollection by profile index/ID ('i') and
        optionally by within-profile horizon index ('j').

        Usage:
            spc[i]        -> Selects profiles based on 'i'.
            spc[i, j]     -> Selects profiles based on 'i', then selects horizons
                           within those profiles based on 'j'.

        Args:
            key:
                If not a tuple: interpreted as 'i' for profile selection.
                    - int: Select profile by integer position.
                    - slice: Select profiles by slice of positions.
                    - str: Select profile by ID (idname).
                    - list/array/Series: Select profiles by list of positions (int)
                      or list of IDs (str/object), or boolean mask.
                If a tuple `(i, j)`:
                    - `i`: Profile selector (as described above).
                    - `j`: Horizon selector (applied *within each selected profile*
                           after sorting horizons by top depth):
                        - int: Select horizon by 0-based index within profile.
                        - slice: Select horizons by slice of indices within profile.
                        - list/array: Select horizons by list of integers within profile.

        Returns:
            A new SoilProfileCollection instance containing the subsetted data.

        Raises:
            IndexError, KeyError, TypeError: For invalid keys or indices.
        """
        i_selector = key
        j_selector = None  # Default: select all horizons for selected profiles

        if isinstance(key, tuple):
            if len(key) == 2:
                i_selector, j_selector = key
            elif len(key) == 1:
                i_selector = key[0]
            else:
                raise TypeError("Subsetting key tuple must have 1 or 2 elements (i, [j]).")

        # --- 1. Process `i` selector (Profile Selection) ---
        selected_profile_ids: List[Any]
        n_profiles = len(self)
        if isinstance(i_selector, int):
            if i_selector < -n_profiles or i_selector >= n_profiles:
                raise IndexError(f"Profile index {i_selector} out of bounds.")
            selected_profile_ids = [self._site.index[i_selector % n_profiles]]
        elif isinstance(i_selector, slice):
            selected_profile_ids = self._site.index[i_selector].tolist()
        elif isinstance(i_selector, str):
            if i_selector not in self._site.index:
                raise KeyError(f"Profile ID '{i_selector}' not found.")
            selected_profile_ids = [i_selector]
        elif isinstance(i_selector, (list, tuple, np.ndarray, pd.Series)):
            i_array = np.asarray(i_selector)
            if i_array.size == 0:
                selected_profile_ids = []
            elif pd.api.types.is_integer_dtype(i_array):
                if np.any(i_array < -n_profiles) or np.any(i_array >= n_profiles):
                    raise IndexError("Profile index out of bounds.")
                selected_profile_ids = self._site.index[i_array].tolist()
            elif pd.api.types.is_bool_dtype(i_array):
                if len(i_array) != n_profiles:
                    raise IndexError(
                        f"Boolean mask length mismatch ({len(i_array)} vs {n_profiles})."
                    )
                selected_profile_ids = self._site.index[i_array].tolist()
            elif pd.api.types.is_string_dtype(i_array) or pd.api.types.is_object_dtype(i_array):
                selected_profile_ids = list(i_array)
                missing = [pid for pid in selected_profile_ids if pid not in self._site.index]
                if missing:
                    raise KeyError(f"Profile IDs not found: {missing}")
            else:
                raise TypeError(
                    f"Unsupported type for profile selector list/array: {i_array.dtype}"
                )
        else:
            raise TypeError(f"Unsupported profile selector type: {type(i_selector)}")

        new_site = self._site.loc[selected_profile_ids]
        intermediate_horizons = self._horizons[
            self._horizons[self.idname].isin(selected_profile_ids)
        ]

        # --- 2. Process `j` selector (Horizon Selection within Profiles) ---
        if j_selector is None or intermediate_horizons.empty:
            new_horizons = intermediate_horizons
        else:
            if not isinstance(j_selector, (int, slice, list, tuple, np.ndarray)):
                raise TypeError(
                    f"Horizon selector 'j' must be an int, slice, list, or array, not {type(j_selector)}."
                )
            if isinstance(j_selector, (list, tuple, np.ndarray)):
                j_array = np.asarray(j_selector)
                if not pd.api.types.is_integer_dtype(j_array):
                    raise TypeError("Horizon selector list/array 'j' must contain integers.")

            global _select_hz_by_iloc

            # Group by profile, apply the selection logic
            selected_hz_groups = intermediate_horizons.groupby(
                self.idname, sort=False, observed=True
            ).apply(
                _select_hz_by_iloc, j_sel=j_selector, top_col=self._topcol, include_groups=False
            )

            if isinstance(selected_hz_groups.index, pd.MultiIndex):
                new_horizons = selected_hz_groups.reset_index(level=0)
                
                if new_horizons.columns[0] == self.idname:
                    pass 
                else:
                    new_horizons = new_horizons.rename(columns={new_horizons.columns[0]: self.idname})
            else:
                new_horizons = selected_hz_groups

        # --- 3. Create and return new SoilProfileCollection ---
        return SoilProfileCollection(
            horizons=new_horizons,
            site=new_site,
            idname=self.idname,
            hzidname=self.hzidname,
            depthcols=self.depthcols,
            hzdesgncol=self.hzdesgncol,
            metadata=self.metadata.copy(),
            crs=self.crs,
            validate=False,  # Subsetting should not require re-validation
        )

    # Replace the depths() method within your SoilProfileCollection class with this:

    def depths(self, how: str = "hz") -> pd.DataFrame:  # Always returns DataFrame
        """
        Returns horizon depth information or profile depth summaries as a DataFrame,
        always including the profile ID column.

        Args:
            how (str): Method to determine output format and content.
                - 'hz' (default): Returns DataFrame with profile ID (idname),
                  horizon ID (hzidname), top depth (topcol), and bottom depth
                  (bottomcol) for all horizons.
                - 'min': Returns DataFrame with profile ID (idname) and 'min_depth'
                  (minimum top depth per profile). Includes all profiles.
                - 'max': Returns DataFrame with profile ID (idname) and 'max_depth'
                  (maximum bottom depth per profile). Includes all profiles.
                - 'minmax': Returns DataFrame with profile ID (idname), 'min_depth',
                  and 'max_depth'. Includes all profiles.

        Returns:
            pd.DataFrame: Horizon/profile depth information based on 'how'.

        Raises:
            ValueError: If 'how' is not supported.
            TypeError: If depth columns are not numeric (when needed for aggregation).
            KeyError: If required columns are missing.
        """
        supported_how = ["hz", "min", "max", "minmax"]
        if how not in supported_how:
            raise ValueError(f"`how` must be one of {supported_how}, not '{how}'")

        # Get attributes
        hz = self._horizons
        id_col = self.idname
        hzid_col = self.hzidname
        top_col, bottom_col = self._depthcols
        site_index = self._site.index  # Use site index for comprehensive results

        # --- Handle Empty Horizon Table ---
        if hz.empty:
            print("Warning: Horizon data is empty.")
            empty_df = pd.DataFrame({id_col: site_index}).set_index(id_col)
            if how == "hz":
                empty_df[[hzid_col, top_col, bottom_col]] = np.nan
            if how == "min" or how == "minmax":
                empty_df["min_depth"] = np.nan
            if how == "max" or how == "minmax":
                empty_df["max_depth"] = np.nan
            return empty_df.reset_index()

        # --- Default: Horizon-level details ('hz') ---
        if how == "hz":
            required_cols = [id_col, hzid_col, top_col, bottom_col]
            missing = [c for c in required_cols if c not in hz.columns]
            if missing:
                raise KeyError(f"Required columns for depths(how='hz') not found: {missing}")
            return hz[required_cols].copy()

        # --- Aggregation Modes ('min', 'max', 'minmax') ---
        if not pd.api.types.is_numeric_dtype(hz.get(top_col)):
            raise TypeError(
                f"Top depth column '{top_col}' is not numeric (required for how='{how}')."
            )
        if not pd.api.types.is_numeric_dtype(hz.get(bottom_col)):
            raise TypeError(
                f"Bottom depth column '{bottom_col}' is not numeric (required for how='{how}')."
            )

        # Calculate aggregations
        if how == "min":
            summary_df = hz.groupby(id_col, observed=True).agg(min_depth=(top_col, "min"))
        elif how == "max":
            summary_df = hz.groupby(id_col, observed=True).agg(max_depth=(bottom_col, "max"))
        elif how == "minmax":
            summary_df = hz.groupby(id_col, observed=True).agg(
                min_depth=(top_col, "min"), max_depth=(bottom_col, "max")
            )
        else:
            raise RuntimeError(f"Internal Error: Unhandled 'how' value: {how}")

        # Reindex to include all profiles from the site table (fills missing with NaN)
        summary_df = summary_df.reindex(site_index)

        # Reset index to turn the profile ID index into a column
        summary_df = summary_df.reset_index()

        # --- Simplified Renaming Logic ---
        # Check if the first column (created from index) needs renaming
        current_index_col_name = summary_df.columns[0]
        if current_index_col_name != id_col:
            # Rename the column created from the index to the expected id_col name
            summary_df.rename(columns={current_index_col_name: id_col}, inplace=True)

        # Ensure expected columns exist
        if how == "min" and "min_depth" not in summary_df.columns:
            summary_df["min_depth"] = np.nan
        if how == "max" and "max_depth" not in summary_df.columns:
            summary_df["max_depth"] = np.nan
        if how == "minmax":
            if "min_depth" not in summary_df.columns:
                summary_df["min_depth"] = np.nan
            if "max_depth" not in summary_df.columns:
                summary_df["max_depth"] = np.nan

        # Define expected final column order
        if how == "min":
            final_cols = [id_col, "min_depth"]
        elif how == "max":
            final_cols = [id_col, "max_depth"]
        elif how == "minmax":
            final_cols = [id_col, "min_depth", "max_depth"]
        else:
            final_cols = summary_df.columns

        return summary_df[final_cols]

    def thickness(self) -> pd.Series:
        """
        Calculates the thickness (bottom - top) for each horizon.

        Returns:
             A pandas Series containing the thickness for each horizon,
             indexed by the horizon ID (hzidname).
        """
        # Ensure depths are numeric before calculation
        if pd.api.types.is_numeric_dtype(
            self._horizons[self._topcol]
        ) and pd.api.types.is_numeric_dtype(self._horizons[self._bottomcol]):
            return self._horizons[self._bottomcol] - self._horizons[self._topcol]
        else:
            print("Warning: Cannot calculate thickness because depth columns are not numeric.")
            # Return a series of NaN with the correct index
            return pd.Series(np.nan, index=self._horizons.index)

    def get_profile(self, profile_id: Any) -> Optional[pd.DataFrame]:
        """
        Retrieves the horizon data for a single specified profile ID.

        Args:
            profile_id: The ID of the profile to retrieve.

        Returns:
            A DataFrame containing the horizon data for the requested profile,
            or None if the profile ID is not found. The DataFrame is sorted by top depth.
        """
        if profile_id not in self._site.index:
            # print(f"Warning: Profile ID '{profile_id}' not found in site data.")
            return None

        profile_horizons = self._horizons[self._horizons[self.idname] == profile_id]

        if profile_horizons.empty:
            # Profile ID exists in site, but has no horizons
            return pd.DataFrame(columns=self._horizons.columns).set_index(self.hzidname)

        return profile_horizons.sort_values(by=self._topcol)

    def get_hz_data(self, profile_id: Any) -> Optional[pd.DataFrame]:
        """Alias for get_profile()."""
        return self.get_profile(profile_id)

    def profile_apply(self, func: Callable, *args, **kwargs) -> pd.Series:
        """
        Applies a function to the horizon data of each profile.

        The function `func` should accept a pandas DataFrame (containing the
        horizons of a single profile) as its first argument, followed by
        any additional *args and **kwargs.

        Args:
            func: The function to apply to each profile's horizon data.
            *args: Positional arguments to pass to `func`.
            **kwargs: Keyword arguments to pass to `func`.

        Returns:
            A pandas Series where the index contains profile IDs and the values
            are the results returned by `func` for each profile. If the function
            returns multiple values (e.g., a Series or dict), the result might
            need further processing depending on the function's output structure.
            This basic version assumes a scalar return value.
        """
        results = {}
        # Group horizons by profile ID
        grouped_horizons = self._horizons.groupby(self.idname)

        for profile_id, horizon_data in grouped_horizons:
            # Apply the function to the DataFrame chunk for this profile
            try:
                result = func(horizon_data, *args, **kwargs)
                results[profile_id] = result
            except Exception as e:
                print(f"Warning: Error applying function to profile '{profile_id}': {e}")
                results[profile_id] = np.nan  # Or some other error indicator

        result_series = pd.Series(results).reindex(self._site.index)

        return result_series

    def plot(
        self,
        n: Optional[int] = None,
        max_depth: Optional[float] = None,
        width: float = 0.4,
        spacing: float = 0.2,
        color: Optional[str] = "grey",  # Default fixed color or column name
        cmap: Optional[str] = "viridis",  # Colormap for numeric data
        vmin: Optional[float] = None,  # Min value for color normalization
        vmax: Optional[float] = None,  # Max value for color normalization
        na_color: str = "lightgrey",  # Color for NaN values when mapping numeric
        label_hz: bool = True,
        label_offset: float = 0.05,
        figsize: Optional[Tuple[float, float]] = None,
        ax: Optional["Any"] = None,
        **kwargs,
    ) -> "Any":
        """
        Creates a simple sketch of the soil profiles.

        Note: This method requires matplotlib. Install with:
            pip install soilprofilecollection[plot]

        Args:
            n: Maximum number of profiles to plot. If None, plots all.
            max_depth: Maximum depth for the y-axis. If None, auto-calculates.
            width: Width of each profile rectangle.
            spacing: Horizontal spacing between profiles.
            color: - A column name in horizons data. If numeric, values are mapped
                     using `cmap`. If non-numeric, values are assumed to be valid
                     matplotlib colors (e.g., 'red', '#FF0000').
                   - A single fixed color string (e.g., 'sandybrown').
                   - None to use matplotlib's default color cycle per horizon.
            cmap: Colormap name (e.g., 'viridis', 'YlGnBu') to use when `color`
                  refers to a numeric column. Default: 'viridis'.
            vmin: Minimum value for color scale normalization (numeric `color` only).
                  If None, uses the minimum of the data in the `color` column.
            vmax: Maximum value for color scale normalization (numeric `color` only).
                  If None, uses the maximum of the data in the `color` column.
            na_color: Color to use for horizons where the value in the `color`
                      column is NaN (numeric `color` only). Default: 'lightgrey'.
            label_hz: If True and hzdesgncol is set, label horizons.
            label_offset: Horizontal offset for horizon labels.
            figsize: Tuple specifying figure size (width, height).
            ax: A matplotlib Axes object to plot on. If None, creates a new figure.
            **kwargs: Additional args passed to matplotlib.patches.Rectangle.

        Returns:
            The matplotlib Axes object containing the plot.
        """
        # Lazy import matplotlib (only when plot() is called)
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            import matplotlib.cm as cm
            import matplotlib.colors as colors
        except ImportError as e:
            raise ImportError(
                "The plot() method requires matplotlib. "
                "Install with: pip install soilprofilecollection[plot]"
            ) from e

        if ax is None:
            # Adjust default figsize calculation slightly
            num_profiles_to_plot = min(len(self), n) if n is not None else len(self)
            fig_width = figsize[0] if figsize else max(6, num_profiles_to_plot * (width + spacing))
            fig_height = figsize[1] if figsize else 6
            fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        else:
            fig = ax.figure

        profile_ids_to_plot = self.profile_ids
        if n is not None and n < len(self):
            profile_ids_to_plot = self.profile_ids[:n]

        if not profile_ids_to_plot:
            ax.text(
                0.5, 0.5, "No profiles to plot.", ha="center", va="center", transform=ax.transAxes
            )
            return ax

        plotted_max_depth = 0
        color_source_is_column = False
        is_numeric_color_col = False
        fixed_color = None
        hz_colors_series = None  # To store the pd.Series if color is a column
        norm = None  # Normalization object
        cmap_obj = None  # Colormap object

        # --- Determine Color Source and Setup ---
        if color is not None:
            if color in self._horizons.columns:
                color_source_is_column = True
                hz_colors_series = self._horizons[color]
                if pd.api.types.is_numeric_dtype(hz_colors_series):
                    is_numeric_color_col = True
                    # Get data range, handling potential NaNs
                    valid_data = hz_colors_series.dropna()
                    data_min = (
                        vmin
                        if vmin is not None
                        else (valid_data.min() if not valid_data.empty else 0)
                    )
                    data_max = (
                        vmax
                        if vmax is not None
                        else (valid_data.max() if not valid_data.empty else 1)
                    )
                    # Handle case where min == max
                    if data_min == data_max:
                        data_min -= 0.5  # Avoid division by zero in norm
                        data_max += 0.5
                        if data_min >= data_max:  # Still an issue if original was 0
                            data_min = 0
                            data_max = 1
                    norm = colors.Normalize(vmin=data_min, vmax=data_max)
                    try:
                        cmap_obj = cm.get_cmap(cmap)
                    except ValueError:
                        print(f"Warning: Invalid colormap name '{cmap}'. Using 'viridis'.")
                        cmap_obj = cm.get_cmap("viridis")
            else:
                fixed_color = color

        # --- Plotting Loop ---
        for i, profile_id in enumerate(profile_ids_to_plot):
            profile_horizons = self.get_profile(profile_id)  # Already sorted by get_profile

            if profile_horizons is None or profile_horizons.empty:
                continue

            x_pos = i * (width + spacing)
            current_max_depth = profile_horizons[self._bottomcol].max()
            if pd.notna(current_max_depth):
                plotted_max_depth = max(plotted_max_depth, current_max_depth)

            # Iterate through horizons of the current profile
            for hzid, hz in profile_horizons.iterrows():
                top = hz[self._topcol]
                bottom = hz[self._bottomcol]

                if pd.isna(top) or pd.isna(bottom):
                    continue
                height = bottom - top
                if height < 0:
                    height = 0

                # --- Determine Horizon Color ---
                horizon_color: Any = None  # Start with MPL default assumption

                if color_source_is_column and hz_colors_series is not None:
                    value = (
                        hz_colors_series.loc[hzid] if hzid in hz_colors_series.index else None
                    )  # Get value using original hzid index
                    if is_numeric_color_col:
                        if value is not None and norm is not None and cmap_obj is not None:
                            try:
                                # Normalize value and get color from cmap
                                horizon_color = cmap_obj(norm(float(value)))
                            except Exception as e:
                                print(
                                    f"Warning: Error getting color for value {value}: {e}. Using na_color."
                                )
                                horizon_color = na_color
                        else:
                            # Value is NaN or norm/cmap setup failed
                            horizon_color = na_color
                    else:
                        # Non-numeric column, use value directly (if not NaN)
                        horizon_color = (
                            value if pd.notna(value) else "grey"
                        )  # Use grey for missing categorical colors
                elif fixed_color is not None:
                    # Fixed color specified for all horizons
                    horizon_color = fixed_color
                # else: horizon_color remains None, matplotlib will cycle colors

                # --- Create Rectangle ---
                rect = patches.Rectangle(
                    (x_pos, top),
                    width,
                    height,
                    facecolor=horizon_color,  # Pass the determined color (can be None)
                    edgecolor="black",
                    linewidth=0.5,
                    **kwargs,
                )
                ax.add_patch(rect)

                # --- Add Label ---
                if label_hz and self.hzdesgncol and self.hzdesgncol in hz:
                    hz_label = str(hz[self.hzdesgncol])
                    if pd.notna(hz_label) and hz_label.lower() != "nan":
                        ax.text(
                            x_pos + width / 2 + label_offset,
                            top + height / 2,
                            hz_label,
                            ha="left",
                            va="center",
                            fontsize=8,
                        )

            # Add profile ID label
            ax.text(
                x_pos + width / 2,
                -plotted_max_depth * 0.05,
                str(profile_id),
                ha="center",
                va="top",
                fontsize=9,
            )

        # --- Configure Axes ---
        ax.set_xlim(-spacing, len(profile_ids_to_plot) * (width + spacing))
        final_max_depth = (
            max_depth
            if max_depth is not None
            else (plotted_max_depth * 1.1 if plotted_max_depth > 0 else 10)
        )
        ax.set_ylim(final_max_depth, 0)
        ax.set_ylabel("Depth")
        ax.set_xlabel("Profile Index / ID")
        ax.set_xticks([])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        # ax.set_title(f'Soil Profile Sketch ({len(profile_ids_to_plot)} profiles)')

        # Optional: Add colorbar if a numeric column was used
        if is_numeric_color_col and norm is not None and cmap_obj is not None:
            # Add a colorbar
            sm = cm.ScalarMappable(cmap=cmap_obj, norm=norm)
            # Set array just to make mappable happy, doesn't affect scale
            sm.set_array([])
            # Add colorbar to the figure, linked to the axes
            # Adjust fraction and pad as needed for layout
            cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.04)
            if color is not None:
                cbar.set_label(color)  # Label with the column name

        return ax

    def glom(
        self,
        intervals: Union[List[float], Tuple[float, ...]],
        agg_fun: Optional[str] = None,
        v: Optional[Union[str, List[str]]] = None,
        truncate: Optional[bool] = None,  # Default is None now!
        fill: bool = False,
        output: str = "spc",
        new_hzidname: str = "slice_hzid",
    ) -> Union["SoilProfileCollection", pd.DataFrame]:
        """
        Slices horizons by depth intervals or aggregates properties within slices.

        Default behavior (`agg_fun=None`): Returns a new SPC containing portions
        of original horizons falling within `intervals`. By default (`truncate=None`
        or `truncate=False`), segments overlapping the first/last interval are
        NOT truncated at the interval boundaries if the original horizon extends
        beyond them. Set `truncate=True` to force clipping at interval boundaries.

        Aggregation behavior (`agg_fun` is specified): Aggregates properties (`v`)
        within each slice. By default (`truncate=None` or `truncate=True`), horizon
        contributions are effectively truncated at slice boundaries by the overlap
        calculation. `truncate=False` currently has no effect on aggregation results.

        Args:
            intervals: List/tuple of depth boundaries (sorted, >= 2 values).
            agg_fun: Aggregation function ('weighted.mean', 'sum', 'min', 'max',
                     'dominant') or None (default) for slicing.
            v: Variable(s) to aggregate. Used only if `agg_fun` is specified.
            truncate: Control horizon boundary clipping.
                      - Slicing (`agg_fun=None`): Default `None` acts as `False` (no edge truncate).
                        `True` clips segments at interval boundaries.
                      - Aggregation (`agg_fun != None`): Default `None` acts as `True` (implicit truncation).
                        `False` currently has no effect on results.
            fill: Only applies when `agg_fun` is specified. If True, output
                  includes all profile/interval combinations. Default: False.
            output: Type of output ('spc' or 'dataframe'). Default: 'spc'.
            new_hzidname: Name for the unique horizon ID column in the output
                          SPC's horizon table. Default changes based on agg_fun.

        Returns:
            A new SoilProfileCollection or pandas DataFrame.
        """
        # --- Input Validation ---
        supported_agg_funs = ["weighted.mean", "sum", "min", "max", "dominant"]
        numeric_agg_funs = ["weighted.mean", "sum", "min", "max"]
        if agg_fun is not None and agg_fun not in supported_agg_funs:
            raise ValueError(
                f"Unsupported agg_fun '{agg_fun}'. Supported: {supported_agg_funs} or None."
            )
        if output not in ["spc", "dataframe"]:
            raise ValueError("`output` must be 'spc' or 'dataframe'.")
        if not isinstance(intervals, (list, tuple)) or len(intervals) < 2:
            raise TypeError("`intervals` must be list/tuple >= 2")
        if not all(isinstance(i, (int, float)) for i in intervals):
            raise TypeError("`intervals` values must be numeric.")
        if not np.all(np.diff(intervals) > 0):
            raise ValueError("`intervals` must be sorted increasing.")

        # --- Determine Effective Settings ---
        if truncate is None:  # User didn't specify
            effective_truncate = agg_fun is not None  # True for aggregation, False for slicing
        else:  # User specified True or False
            effective_truncate = truncate

        # Adjust default hzid name based on operation
        effective_new_hzidname = new_hzidname
        if new_hzidname == "slice_hzid":  # Check if default name was left unchanged
            effective_new_hzidname = "agg_hzid" if agg_fun is not None else "slice_hzid"
        if not isinstance(effective_new_hzidname, str) or not effective_new_hzidname:
            raise ValueError("`new_hzidname` must resolve to a non-empty string.")

        # --- Get core properties ---
        hz = self._horizons
        id_col = self.idname
        original_hzid_col = self.hzidname
        top_col, bottom_col = self.depthcols
        slice_intervals = list(zip(intervals[:-1], intervals[1:]))
        first_interval_top = intervals[0]
        last_interval_bottom = intervals[-1]

        # --- Main Logic Branch: Slice vs Aggregate ---
        final_data_df: pd.DataFrame
        vars_aggregated = []

        if agg_fun is None:
            mode = "slicing"
            if hz.empty:
                slice_cols = list(hz.columns)
                for core_col in [id_col, original_hzid_col, top_col, bottom_col]:
                    if core_col not in slice_cols:
                        slice_cols.append(core_col)
                final_data_df = pd.DataFrame(columns=slice_cols)
            else:
                slice_results_list = []
                global _slice_single_profile
                for pid, group_df in hz.groupby(id_col, sort=False, observed=True):
                    if not group_df.empty:
                        res = _slice_single_profile(
                            profile_horizons=group_df,
                            id_col=id_col,
                            top_col=top_col,
                            bottom_col=bottom_col,
                            slice_intervals=slice_intervals,
                            original_hzid_col=original_hzid_col,
                            truncate=effective_truncate,
                            first_interval_top=first_interval_top,
                            last_interval_bottom=last_interval_bottom,
                        )
                        if not res.empty:
                            slice_results_list.append(res)

                if not slice_results_list:
                    final_data_df = pd.DataFrame(columns=hz.columns)
                else:
                    final_data_df = pd.concat(slice_results_list, ignore_index=True)
                    try:
                        final_data_df = final_data_df[hz.columns]
                    except KeyError:
                        print("Warning: Columns in sliced data differ from original.")

        else:
            mode = "aggregation"
            if v is None:
                if agg_fun in numeric_agg_funs:
                    potential_vars = hz.select_dtypes(include=np.number).columns.tolist()
                    vars_to_agg = [
                        col
                        for col in potential_vars
                        if col not in [id_col, top_col, bottom_col, original_hzid_col]
                    ]
                    if not vars_to_agg:
                        raise ValueError(
                            f"No suitable numeric columns found for agg_fun='{agg_fun}'."
                        )
                elif agg_fun == "dominant":
                    potential_vars = hz.columns.tolist()
                    vars_to_agg = [
                        col
                        for col in potential_vars
                        if col not in [id_col, top_col, bottom_col, original_hzid_col]
                    ]
                    if not vars_to_agg:
                        raise ValueError("No suitable columns found for agg_fun='dominant'.")
                else:
                    raise ValueError(
                        "Cannot auto-detect variables for unknown agg_fun."
                    )  # Should not happen
            elif isinstance(v, str):
                vars_to_agg = [v]
            elif isinstance(v, (list, tuple)):
                vars_to_agg = list(v)
            else:
                raise TypeError("`v` must be a string, list/tuple of strings, or None.")

            missing_vars = [col for col in vars_to_agg if col not in hz.columns]
            if missing_vars:
                raise ValueError(f"Variable(s) not found in horizon data: {missing_vars}")
            if agg_fun in numeric_agg_funs:
                non_numeric_vars = [
                    col for col in vars_to_agg if not pd.api.types.is_numeric_dtype(hz[col])
                ]
                if non_numeric_vars:
                    raise ValueError(
                        f"Variable(s) selected for agg_fun='{agg_fun}' are not numeric: {non_numeric_vars}"
                    )
            vars_aggregated = vars_to_agg

            if hz.empty:
                agg_cols = [id_col, top_col, bottom_col] + vars_aggregated
                glommed_data = pd.DataFrame(columns=agg_cols)
            else:
                glommed_data_list = []
                global _glom_single_profile
                for pid, group_df in hz.groupby(id_col, sort=False, observed=True):
                    if not group_df.empty:
                        res = _glom_single_profile(
                            profile_horizons=group_df,
                            id_col=id_col,
                            top_col=top_col,
                            bottom_col=bottom_col,
                            slice_intervals=slice_intervals,
                            vars_to_agg=vars_aggregated,
                            agg_fun=agg_fun,
                        )
                        if not res.empty:
                            glommed_data_list.append(res)

                if not glommed_data_list:
                    print(f"Warning: No valid data for aggregation with '{agg_fun}'.")

                if glommed_data_list:
                    glommed_data = pd.concat(glommed_data_list, ignore_index=True)
                else:
                    glommed_data = pd.DataFrame(
                        columns=[id_col, top_col, bottom_col] + vars_aggregated
                    )

            if fill:
                all_profile_ids = self._site.index
                interval_df = pd.DataFrame(slice_intervals, columns=[top_col, bottom_col])
                multi_index = pd.MultiIndex.from_product(
                    [all_profile_ids, interval_df.index], names=[id_col, "_interval_idx"]
                )
                full_template = pd.DataFrame(index=multi_index)
                interval_df["_interval_idx"] = interval_df.index
                full_template_flat = full_template.reset_index()
                full_template_merged = pd.merge(
                    full_template_flat, interval_df, on="_interval_idx"
                ).drop(columns=["_interval_idx"])
                full_template_indexed = full_template_merged.set_index(
                    [id_col, top_col, bottom_col]
                )

                if not glommed_data.empty:
                    try:
                        glommed_data_indexed = glommed_data.set_index([id_col, top_col, bottom_col])
                    except KeyError as e:
                        raise RuntimeError(f"Aggregated data missing columns: {e}")
                    final_data_filled = glommed_data_indexed.reindex(full_template_indexed.index)
                else:
                    final_data_filled = pd.DataFrame(
                        np.nan, index=full_template_indexed.index, columns=vars_aggregated
                    )
                final_data_df = final_data_filled.reset_index()
            else:
                final_data_df = glommed_data

            agg_cols_ordered = [id_col, top_col, bottom_col] + vars_aggregated
            for col in agg_cols_ordered:
                if col not in final_data_df.columns:
                    final_data_df[col] = np.nan
            final_data_df = final_data_df[agg_cols_ordered]

        try:
            if id_col in final_data_df.columns:
                final_data_df[id_col] = final_data_df[id_col].astype(self._site.index.dtype)
            if top_col in final_data_df.columns:
                final_data_df[top_col] = pd.to_numeric(final_data_df[top_col], errors="coerce")
            if bottom_col in final_data_df.columns:
                final_data_df[bottom_col] = pd.to_numeric(
                    final_data_df[bottom_col], errors="coerce"
                )
            if agg_fun is not None:  # Only force numeric for aggregation results if needed
                for var in vars_aggregated:
                    if var not in final_data_df.columns:
                        continue
                    original_is_numeric = pd.api.types.is_numeric_dtype(hz.get(var))
                    target_is_numeric = pd.api.types.is_numeric_dtype(final_data_df[var])
                    if (
                        agg_fun in numeric_agg_funs or original_is_numeric
                    ) and not target_is_numeric:
                        if pd.api.types.is_object_dtype(final_data_df[var]):
                            final_data_df[var] = pd.to_numeric(final_data_df[var], errors="coerce")
        except Exception as e:
            print(f"Warning: Could not enforce final dtypes consistently: {e}")

        if output == "dataframe":
            return final_data_df
        else:
            if final_data_df.empty:
                empty_hz_cols = [id_col, effective_new_hzidname, top_col, bottom_col] + (
                    vars_aggregated if agg_fun else list(hz.columns)
                )
                empty_hz_cols = list(dict.fromkeys(empty_hz_cols))
                empty_hz = pd.DataFrame(columns=empty_hz_cols).astype(
                    {id_col: self._site.index.dtype, top_col: float, bottom_col: float}
                )
                empty_site = self._site.iloc[0:0].copy()
                return SoilProfileCollection(
                    horizons=empty_hz,
                    site=empty_site,
                    idname=id_col,
                    hzidname=effective_new_hzidname,
                    depthcols=(top_col, bottom_col),
                    hzdesgncol=self.hzdesgncol if agg_fun is None else None,
                    metadata=self.metadata.copy(),
                    crs=self.crs,
                    validate=False,
                )

            new_horizons_df = final_data_df.copy()

            if (
                effective_new_hzidname in new_horizons_df.columns
                and effective_new_hzidname != original_hzid_col
            ):
                raise ValueError(
                    f"Chosen `new_hzidname` ('{effective_new_hzidname}') conflicts with existing column."
                )

            if effective_new_hzidname not in new_horizons_df.columns or agg_fun is None:
                new_horizons_df[effective_new_hzidname] = range(len(new_horizons_df))
                new_horizons_df[effective_new_hzidname] = new_horizons_df[
                    effective_new_hzidname
                ].astype(str)

            profile_ids_in_result = new_horizons_df[id_col].unique()
            try:
                new_site_df = self._site.loc[profile_ids_in_result].copy()
            except KeyError:
                new_site_df = self._site[self._site.index.isin(profile_ids_in_result)].copy()
            except Exception as e:
                raise RuntimeError(f"Could not filter site data for resulting SPC: {e}")

            try:
                final_hzdesgncol = (
                    self.hzdesgncol
                    if agg_fun is None and self.hzdesgncol in new_horizons_df.columns
                    else None
                )

                return SoilProfileCollection(
                    horizons=new_horizons_df,
                    site=new_site_df,
                    idname=id_col,
                    hzidname=effective_new_hzidname,  # Use effective name
                    depthcols=(top_col, bottom_col),
                    hzdesgncol=final_hzdesgncol,
                    metadata=self.metadata.copy(),
                    crs=self.crs,
                    validate=False,  # Assume valid structure post-glom/slice
                )
            except Exception as e:
                print("\nError creating SPC:")
                print(
                    f"  Mode: {mode}, agg_fun: {agg_fun}, truncate: {effective_truncate}, fill: {fill if agg_fun else 'N/A'}"
                )
                print(
                    f"  Horizons ({new_horizons_df.shape}):\n{new_horizons_df.head().to_string()}"
                )
                print(f"  Site ({new_site_df.shape}):\n{new_site_df.head().to_string()}")
                print(
                    f"  idname='{id_col}', hzidname='{effective_new_hzidname}', depthcols=({top_col}, {bottom_col}), hzdesgncol='{final_hzdesgncol}'"
                )
                raise RuntimeError(f"Failed to create SPC from results: {e}")
