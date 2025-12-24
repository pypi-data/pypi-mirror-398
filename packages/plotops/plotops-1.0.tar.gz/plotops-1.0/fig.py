#%%

import numpy as np
import matplotlib.pyplot as plt

#%%

def subplots(nh, nw,
                  gap=0.05,
                  marg_h=0.1,
                  marg_w=0.05,
                  weight_h=None,
                  weight_w=None,
                  fig=None,
                  skipaxes=False):
    """
    MATLAB-equivalent tight_subplot using absolute normalized gaps and margins.

    Parameters
    ----------
    nh, nw : int
        Number of rows and columns.
    gap : float or (float, float)
        Absolute gap size in normalized figure units (gap_h, gap_w).
    marg_h : float or (float, float)
        Absolute margins (bottom, top) in normalized units.
    marg_w : float or (float, float)
        Absolute margins (left, right) in normalized units.
    weight_h : array-like, optional
        Relative row heights (length nh).
    weight_w : array-like, optional
        Relative column widths (length nw).
    fig : matplotlib.figure.Figure, optional
        Figure to use (created if None).
    skipaxes : bool
        If True, only return positions.

    Returns
    -------
    axes : list of Axes
        Axes handles (row-wise, top-left first).
    pos : list of list
        [left, bottom, width, height] for each axes.
    """

    # --- normalize inputs ---
    if fig is None:
        fig = plt.figure()

    if np.isscalar(gap):
        gap = (gap, gap)
    if np.isscalar(marg_h):
        marg_h = (marg_h, marg_h)
    if np.isscalar(marg_w):
        marg_w = (marg_w, marg_w)

    if weight_h is None:
        weight_h = np.ones(nh)
    if weight_w is None:
        weight_w = np.ones(nw)

    weight_h = np.asarray(weight_h, dtype=float)
    weight_w = np.asarray(weight_w, dtype=float)

    if len(weight_h) != nh:
        raise ValueError('weight_h must have length nh')
    if len(weight_w) != nw:
        raise ValueError('weight_w must have length nw')

    weight_h /= weight_h.sum()
    weight_w /= weight_w.sum()

    # --- available space ---
    H = 1.0 - sum(marg_h) - gap[0] * (nh - 1)
    W = 1.0 - sum(marg_w) - gap[1] * (nw - 1)

    if H <= 0 or W <= 0:
        raise ValueError('Margins and gaps leave no space for axes')

    axh = H * weight_h
    axw = W * weight_w

    axes = []
    pos = []

    # --- build axes (top-left first) ---
    y = 1.0 - marg_h[1]
    for ih in range(nh):
        y -= axh[ih]
        x = marg_w[0]

        for iw in range(nw):
            p = [x, y, axw[iw], axh[ih]]
            pos.append(p)

            if not skipaxes:
                axes.append(fig.add_axes(p))

            x += axw[iw] + gap[1]

        y -= gap[0]

    return axes, fig, pos 

#%%

def syncx(axes):
    """
    Link x-axes of a list of matplotlib Axes objects.
    Zooming/panning one axis updates all others.
    """
    if not axes:
        return

    base = axes[0]
    for ax in axes[1:]:
        ax.sharex(base)
        
#%%
        
def _expand_limits(lim, frac, side='both', log=False, keep_zero=False):
    """
    Expand axis limits by a fraction of the data range.

    Parameters
    ----------
    lim : (low, high)
    frac : float
        Relative padding (e.g. 0.05)
    side : {'both', 'positive', 'negative'}
    log : bool
        Operate in log10 space
    keep_zero : bool
        Force lower limit to zero
    """
    lo, hi = lim

    if log:
        lo, hi = np.log10([lo, hi])

    rng = hi - lo
    if rng <= 0:
        return lim

    dlo = frac * rng if side in ('both', 'negative') else 0.0
    dhi = frac * rng if side in ('both', 'positive') else 0.0

    lo -= dlo
    hi += dhi

    if log:
        lo, hi = 10**lo, 10**hi

    if keep_zero:
        lo = 0.0

    return lo, hi


#%%

def axistight(ax, p=0.05, axes=('y',)):
    """
    MATLAB-like axistight for matplotlib.

    Parameters
    ----------
    ax : matplotlib Axes or iterable of Axes
    p : float or sequence
        Relative padding per axis
    axes : iterable of str
        'x', 'y', '+x', '-y', 'x0', 'ylog', etc.
    """

    # --- allow ax to be a list/tuple ---
    if isinstance(ax, (list, tuple)):
        for a in ax:
            axistight(a, p=p, axes=axes)
        return

    # --- from here: ax is a single Axes ---
    ax.autoscale(enable=True, tight=True)

    if np.isscalar(p):
        p = [p] * len(axes)

    for frac, spec in zip(p, axes):
        log = spec.endswith('log')
        axis = spec[-1]

        side = 'both'
        keep_zero = False

        if spec.startswith('+'):
            side = 'positive'
        elif spec.startswith('-'):
            side = 'negative'
        elif spec.endswith('0'):
            keep_zero = True

        if axis == 'x':
            lim = ax.get_xlim()
            newlim = _expand_limits(lim, frac, side, log, keep_zero)
            ax.set_xlim(newlim)

        elif axis == 'y':
            lim = ax.get_ylim()
            newlim = _expand_limits(lim, frac, side, log, keep_zero)
            ax.set_ylim(newlim)

def tilefigs(nw, nh,side=None,gap_px=10,extra_vgap_px=50,edge_px=20,top_gap_px=60,bottom_gap_px=100):
    """
    Tile all open matplotlib figures on screen without overlap.
    """

    figs = [plt.figure(n) for n in plt.get_fignums()]
    if not figs:
        print('No open figures to tile.')
        return

    # --- get screen size ---
    root = tk.Tk()
    root.withdraw()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.destroy()

    # --- usable screen region ---
    x0 = edge_px
    y0 = top_gap_px
    usable_w = screen_w - 2 * edge_px
    usable_h = screen_h - top_gap_px - bottom_gap_px

    # --- left / right half ---
    if side == 'l':
        usable_w //= 2
    elif side == 'r':
        x0 += usable_w // 2
        usable_w //= 2

    # --- effective vertical gap ---
    vgap = gap_px + extra_vgap_px

    # --- window size ---
    win_w = (usable_w - (nw - 1) * gap_px) // nw
    win_h = (usable_h - (nh - 1) * vgap) // nh

    if win_w <= 0 or win_h <= 0:
        raise ValueError('Screen too small for requested layout.')

    backend = matplotlib.get_backend().lower()

    # --- tile figures ---
    for k, fig in enumerate(figs):
        row = k // nw
        col = k % nw
        if row >= nh:
            break

        x = x0 + col * (win_w + gap_px)
        y = y0 + row * (win_h + vgap)

        mgr = fig.canvas.manager
        fig.set_size_inches(win_w / fig.dpi, win_h / fig.dpi, forward=True)

        # --- TkAgg ---
        if 'tk' in backend:
            mgr.window.wm_geometry(f'{win_w}x{win_h}+{x}+{y}')

        # --- QtAgg ---
        elif 'qt' in backend:
            mgr.window.setGeometry(x, y, win_w, win_h)
            
            _bring_to_front(fig)
                        
        else:
            print(f'Backend {backend} does not support window tiling.')
            
        
def _bring_to_front(fig):
    mgr = fig.canvas.manager
    win = mgr.window

    try:
        # Make sure window is shown
        #win.show()

        # Temporarily toggle "always on top"
        win.setWindowState(
            win.windowState() & ~QtCore.Qt.WindowMinimized
        )
        win.raise_()
        win.activateWindow()

        win.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        win.show()
        win.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, False)
        win.show()

    except Exception as e:
        print('Could not raise window:', e)
  
        
  
def sizefig(
    fig,
    width_frac=0.5,
    height_frac=0.5,
    y_center_frac=2/3
):
    """
    Resize and place a matplotlib figure.

    y_center_frac is measured from the *bottom* of the screen.
    """
    
    root = tk.Tk()
    root.withdraw()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.destroy()

    win_w = int(screen_w * width_frac)
    win_h = int(screen_h * height_frac)

    x = int((screen_w - win_w) / 2)
    y = int(screen_h * (1 - y_center_frac) - win_h / 2)

    mgr = fig.canvas.manager
    fig.set_size_inches(win_w / fig.dpi, win_h / fig.dpi, forward=True)

    backend = matplotlib.get_backend().lower()

    if 'tk' in backend:
        mgr.window.wm_geometry(f'{win_w}x{win_h}+{x}+{y}')
    elif 'qt' in backend:
        mgr.window.setGeometry(x, y, win_w, win_h)
    
    _bring_to_front(fig)
    
#%%