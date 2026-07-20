import numpy as np
from scipy.signal import find_peaks

def find_peak_boundaries(intensity, peak_idx, left_limit, right_limit,
                         flat_thresh, flat_count):

    start_idx = peak_idx
    flat_counter = 0
    last_val = intensity[peak_idx]

    while start_idx > left_limit:
        curr_val = intensity[start_idx - 1]
        delta = abs(curr_val - last_val)

        if delta < flat_thresh:
            flat_counter += 1
        else:
            flat_counter = 0

        if flat_counter >= flat_count or curr_val > last_val:
            start_idx = start_idx + flat_counter - 1
            break

        last_val = curr_val
        start_idx -= 1

    end_idx = peak_idx
    flat_counter = 0
    last_val = intensity[peak_idx]

    while end_idx < right_limit:
        curr_val = intensity[end_idx + 1]
        delta = abs(curr_val - last_val)

        if delta < flat_thresh:
            flat_counter += 1
        else:
            flat_counter = 0

        if flat_counter >= flat_count or curr_val > last_val:
            end_idx = end_idx - flat_counter + 1
            break

        last_val = curr_val
        end_idx += 1

    return start_idx, end_idx


def find_real_peak_index(wavelength, intensity, center, search_range=20):
    center_idx = np.argmin(np.abs(wavelength - center))

    left = max(center_idx - search_range, 0)
    right = min(center_idx + search_range, len(wavelength) - 1)

    local_int = intensity[left:right + 1]
    local_wl = wavelength[left:right + 1]

    peaks, _ = find_peaks(local_int, height=500)

    if len(peaks) == 0:
        return center_idx, left, right

    peak_wls = local_wl[peaks]
    best = peaks[np.argmin(np.abs(peak_wls - center))]

    return left + best, left, right
