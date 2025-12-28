def interpolate_rts(combined, batch_num):
    # todo make sure this thing actually works
    rt_col = "RT"
    rt_new_col = f"RT_{batch_num}"
    rt_last_col = f"RT_Last_{batch_num}"

    combined = combined.copy()
    combined.sort_values(rt_col, inplace=True)
    combined.reset_index(inplace=True)  # We'll fix this later

    # Identify known and missing
    known = combined[combined[rt_new_col].notnull() & combined[rt_last_col].notnull()]
    missing = combined[combined[rt_new_col].isnull()]

    # For quick lookup
    known_rts = known[rt_col].to_numpy()
    known_diffs = (known[rt_new_col] - known[rt_last_col]).to_numpy()

    result_rt = combined[rt_new_col].to_numpy()
    result_last = combined[rt_last_col].to_numpy()

    for idx in missing.index:
        rt_val = combined.at[idx, rt_col]

        # Binary search range start and end (could optimize further)
        low = known_rts.searchsorted(rt_val - 0.2, side="right")
        high = known_rts.searchsorted(rt_val + 0.2, side="left")

        if low < high:
            nearby_diffs = known_diffs[low:high]
            avg_diff = np.nanmean(nearby_diffs)

            if not np.isnan(avg_diff):
                result_rt[idx] = rt_val
                result_last[idx] = rt_val - avg_diff

    # Write back updated values
    combined[rt_new_col] = result_rt
    combined[rt_last_col] = result_last

    still_null = pd.isnull(combined[rt_new_col])
    combined.loc[still_null, rt_new_col] = combined[rt_col]
    combined.loc[still_null, rt_last_col] = combined[rt_col]

    combined.set_index("index", inplace=True)  # restore original index

    return combined


# 5
def combine_batches(batches, start=0, stop=None, to_csv=True):
    """
    stop is not inclusive
    """
    MSAligner.descriptors = {"RT": "linear", "MZ": "ppm"}
    if stop is None:
        stop = len(batches)
    batch_nums = slice(start, stop)
    combined_sparse = None
    # combined_conserved = None
    prev_batch = None
    print("starting...", start, stop)
    lengths = {}
    qc_columns = [
        "Base_Gaussian_Correlation",
        "Prominence_Gaussian_Correlation",
        "Signal_To_Noise",
        "Best_Correlation",
        "FW20%M",
    ]

    important_columns = [
        "Compound_ID",
        "RT",
        "RT_Last",
        "MZ",
    ] + qc_columns
    intensity_column = "Intensity_Triangle"  # must be separate to avoid renaming
    lengths_sparse = {}
    combined_is_limited = False
    current_is_limited = False
    for batch_num in range(start, stop):
        print(batch_num)
        batch_columns = [col + f"_{batch_num}" for col in important_columns]
        try:
            current_batch = pd.read_csv(PB_DIR + DD_SLUG % batch_num)
        except:
            continue
        current_batch = current_batch[important_columns + [intensity_column]]

        if prev_batch is None:
            prev_batch = current_batch
            combined = current_batch.copy()
            combined["RT"] = combined["RT_Last"]
            continue
        print("calculating scalers...")
        # align to current to previous (*not* combined) to get scalers and stdevs
        a = MSAligner(
            prev_batch, current_batch, names=[str(batch_num - 1), str(batch_num)]
        )
        a.default_cutoff = 10
        a.default_coarse_params["RT"] = {
            "upper": 0.2,
            "lower": -0.2,
        }  # wider coarse matching
        a.default_scaler_params = {
            "smoothing_method": "lowess",
            "smoothing_params": {"frac": 0.5},
        }
        a.gen_anchors()
        a.gen_coarse()
        a.gen_scalers()
        a.gen_scaled_values()
        a.gen_stds()
        scalers = a.scalers
        stds = a.stds

        print("aligning to combined robust")
        # align current to robust combined features
        intensity_cols = [
            col for col in combined.columns if col.startswith("Intensity_Triangle")
        ]
        non_empty = combined[intensity_cols].notnull().all(axis=1)
        a = MSAligner(
            combined[non_empty],
            current_batch,
            names=[str(batch_num - 1), str(batch_num)],
        )

        a.default_cutoff = 10
        a.scalers = scalers
        a.stds = stds
        a.gen_scaled_values()
        a.gen_matches()
        a.gen_graph()
        results = a.results()  # ,c_size_or_loss=1, g_size_or_loss=1, diameter=1)
        print("parsing robust...")
        lengths[batch_num] = len(results)
        combined_robust = pd.DataFrame(index=results.index)

        # copy over all descriptors
        combined_robust.loc[:, important_columns + batch_columns] = results[
            important_columns + batch_columns
        ]
        # and all intensities
        intensity_cols = results.columns[
            results.columns.str.startswith("Intensity_Triangle")
        ]
        combined_robust.loc[:, intensity_cols] = results[intensity_cols]

        # get the sparse features which were aligned
        combined_robust_found = pd.Index(results[str(batch_num - 1)]).astype(int)

        # combined_robust_notfound = combined.index - combined_robust_found
        print("aligning to sparse")
        current_robust_found = pd.Index(results[str(batch_num)])
        current_robust_notfound = current_batch.index.difference(current_robust_found)
        a = MSAligner(
            combined[~non_empty],
            current_batch.loc[current_robust_notfound, :],
            names=[str(batch_num - 1), str(batch_num)],
        )

        a.default_cutoff = 10
        a.scalers = scalers
        a.stds = stds
        a.gen_scaled_values()
        a.gen_matches()
        a.gen_graph()
        results = a.results()
        print("parsing sparse")
        combined_sparse = pd.DataFrame(index=results.index)

        # copy over all descriptors for sparse
        combined_sparse.loc[:, important_columns + batch_columns] = results[
            important_columns + batch_columns
        ]
        intensity_cols = results.columns[
            results.columns.str.startswith("Intensity_Triangle")
        ]
        combined_sparse.loc[:, intensity_cols] = results[intensity_cols]

        # build the notfound databases
        combined_sparse_found = pd.Index(results[str(batch_num - 1)]).astype(int)
        current_sparse_found = pd.Index(results[str(batch_num)])

        combined_not_found = combined.index.difference(
            combined_robust_found
        ).difference(combined_sparse_found)
        print(combined.index[:5])
        print(combined_robust_found[:5])
        print(combined_sparse_found[:5])
        print(
            len(combined.index),
            len(combined_robust_found),
            len(combined_sparse_found),
            len(combined_not_found),
        )
        print(current_batch.index[:5])
        print(current_robust_found[:5])
        print(current_sparse_found[:5])

        current_not_found = current_batch.index.difference(
            current_robust_found
        ).difference(current_sparse_found)

        print(
            len(current_batch.index),
            len(current_robust_found),
            len(current_sparse_found),
            len(current_not_found),
        )
        df_combined_not_found = combined.loc[combined_not_found, :]
        df_current_not_found = current_batch.loc[current_not_found, :]
        print("interpolating1")
        # rename the current to add batch num so we can combine it with the others
        df_current_not_found = df_current_not_found.rename(
            columns={
                col: col + f"_{batch_num}"
                for col in important_columns + [intensity_column]
            }
        )

        combined = pd.concat(
            [
                combined_robust,
                combined_sparse,
                df_current_not_found,
                df_combined_not_found,
            ],
            ignore_index=True,
        )
        lengths_sparse[batch_num] = len(combined)

        # fill in missing MZ, RT_Last, Compound_ID for the most recent batch
        missing_mask = pd.isnull(combined[f"Intensity_Triangle_{batch_num}"])
        combined.loc[missing_mask, f"MZ_{batch_num}"] = combined.loc[missing_mask, "MZ"]
        combined.loc[missing_mask, f"Compound_ID_{batch_num}"] = combined.loc[
            missing_mask, "Compound_ID"
        ]
        print("interpolating2")
        combined = interpolate_rts(combined, batch_num)

        print("finalizing")
        combined["RT"] = combined["RT_Last"]

        # reassign columns to the "latest"
        for qc_col in qc_columns:
            combined[qc_col + f"_{batch_num}"] = combined[
                [qc_col, qc_col + f"_{batch_num}"]
            ].max(axis=1)
        intensity_cols = results.columns[
            results.columns.str.startswith("Intensity_Triangle")
        ]
        combined = combined[batch_columns + list(intensity_cols)]
        combined = combined.rename(
            columns={col: bcol for col, bcol in zip(batch_columns, important_columns)}
        )

        combined["RT"] = combined["RT_Last"]

        prev_batch = current_batch

    for k in lengths:
        print(f"{k}\t{lengths[k]}\t{lengths_sparse[k]}")

    # pull intensity and save
    only_results = pd.DataFrame(index=combined.index)
    only_results["Compound_ID"] = combined["Compound_ID"]
    only_results["RT"] = combined["RT"]
    only_results["MZ"] = combined["MZ"]
    only_results[qc_columns] = combined[qc_columns]
    intensity_columns = combined.columns[
        combined.columns.str.startswith("Intensity_Triangle")
    ]
    all_samples = list(
        dict.fromkeys(sample for batch in batches[batch_nums] for sample in batch)
    )
    only_results.loc[:, all_samples] = pd.NA

    for batch, int_col in zip(batches[batch_nums], intensity_columns):
        print("Batch: ", batch)
        json_parsed = []
        empty = [pd.NA] * len(batch)
        for i, (row_id, row_values) in enumerate(combined.iterrows()):
            if isinstance(row_values[int_col], str):
                json_parsed.append(json.loads(row_values[int_col]))
            else:
                json_parsed.append(empty)
        only_results.loc[:, batch] = json_parsed

    if to_csv:
        if not os.path.exists(COMB_DIR):
            os.makedirs(COMB_DIR)
        only_results.to_csv(COMB_DIR + "triangle.csv")
        combined.to_csv(COMB_DIR + COMB_SLUG)
    return only_results


def process(fwhm_min, fwhm_max):
    print("Processing with ", fwhm_min, fwhm_max)
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    names, batches = get_batches(pd.read_csv(f"./injection_data.csv"))

    # get segments
    with multiprocessing.Pool(processes=os.cpu_count() - 2) as pool:
        pool.map(m_get_segments, names)
    #
    # identify single-file peaks
    partial_func = partial(m_segments_to_peaks, fwhm_min=fwhm_min, fwhm_max=fwhm_max)
    with multiprocessing.Pool(processes=os.cpu_count() - 2) as pool:
        pool.map(partial_func, names)

    # get combine peaks into a batch
    with multiprocessing.Pool(processes=10) as pool:
        args = [(batch, batch_id) for batch_id, batch in enumerate(batches)]
        pool.starmap(m_peaks_to_batches, args)

    # repick and integration batch peaks
    with multiprocessing.Pool(processes=10) as pool:
        args = [
            (batch, batch_id, fwhm_min, fwhm_max)
            for batch_id, batch in enumerate(batches)
        ]
        pool.starmap(m_pick_consensus, args)

    # combine batches
    return combine_batches(batches)
