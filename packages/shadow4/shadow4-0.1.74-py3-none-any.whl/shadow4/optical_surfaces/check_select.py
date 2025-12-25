import numpy as np

def select_first_real_by_abs(t0, t1, t2, t3, tol=1e-10):
    """
    Select the first real root (sorted by absolute value) from 4 complex arrays.

    Parameters
    ----------
    t0, t1, t2, t3 : array_like of shape (n,)
        Arrays of complex numbers.
    tol : float
        Tolerance for considering a number as real.

    Returns
    -------
    t_selected : ndarray of shape (n,)
        The selected real root for each set, 0 if no real roots.
    i_res : ndarray of shape (n,)
        Mask: 1 if a real root exists, -1 if no real root.
    """
    # Stack inputs into (n,4)
    roots = np.stack([t0, t1, t2, t3], axis=1)

    # Mask real roots
    mask_real = np.abs(roots.imag) < tol
    roots_real = np.where(mask_real, roots.real, np.nan)

    # Sort each row by absolute value
    temp = np.where(np.isnan(roots_real), np.inf, np.abs(roots_real))
    sort_idx = np.argsort(temp, axis=1)
    roots_sorted = np.take_along_axis(roots_real, sort_idx, axis=1)

    # Select first real root
    t_selected = roots_sorted[:, 0].copy()

    # Create mask for no-solution positions
    no_solution_mask = np.isnan(t_selected)
    t_selected[no_solution_mask] = 0.0

    # i_res = 1 if solution exists, -1 if none
    i_res = np.ones_like(t_selected, dtype=int)
    i_res[no_solution_mask] = -1

    return t_selected, i_res


# Example usage
if __name__ == "__main__":
    n = 5
    t0 = np.array([1+0j, 1j, -3+0j, 0+0j, 1+2j])
    t1 = np.array([0+0j, 1j, 3+0j, -1+0j, 0+3j])
    t2 = np.array([2+0j, 1j, 0+0j, 4+8j, 1+3j])
    t3 = np.array([1j, 5+3j, 2+0j, -2+0j, -1+1j])

    t_selected, i_res = select_first_real_by_abs(t0, t1, t2, t3)
    print("Selected real roots:", t_selected)
    print("i_res mask:", i_res)
