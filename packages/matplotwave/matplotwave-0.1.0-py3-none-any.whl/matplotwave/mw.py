#!/usr/bin/env python
from matplotlib import rcParams
import matplotlib.pyplot as plt
import cycler
import matplotlib
from matplotlib.colors import LinearSegmentedColormap

#for export
__all__ = [
"available", "cmap", "despine", "font_size", "reverse", "set_palette", "set_dark_theme", "set_light_theme", "view_palette"
]
#ordered palette is used for colormaps and for available as well as for keychecks
palettes_ordered = {
    "vaporwave": ["#94D0FF", "#8795E8", "#966bff", "#AD8CFF", "#C774E8", "#c774a9", "#FF6AD5", "#ff6a8b", "#ff8b8b", "#ffa58b", "#ffde8b", "#cdde8b", "#8bde8b", "#20de8b"],
    "cool": ["#FF6AD5", "#C774E8", "#AD8CFF", "#8795E8", "#94D0FF"],
    "crystal_pepsi": ["#FFCCFF", "#F1DAFF", "#E3E8FF", "#CCFFFF"],
    "mallsoft": ["#fbcff3", "#f7c0bb", "#acd0f4", "#8690ff", "#30bfdd", "#7fd4c1"],
    "jazzcup": ["#392682", "#7a3a9a", "#3f86bc", "#28ada8", "#83dde0"],
    "sunset": ["#661246", "#ae1357", "#f9247e", "#d7509f", "#f9897b"],
    "macplus": ["#1b4247", "#09979b", "#75d8d5", "#ffc0cb", "#fe7f9d", "#65323e"],
    "seapunk": ["#532e57", "#a997ab", "#7ec488", "#569874", "#296656"],
    "avanti": ["#FB4142", "#94376C", "#CE75AD", "#76BDCF", "#9DCFF0"],
    "neon_crystal_pepsi": ["#CD8BCD", "#B693D9", "#9BA9DB", "#82CACA"],  # darker variant
    "windows95" : ["#008080", "#0827f5", "#ff0081","#dfe300", "#6c6c6c",],
    "y2k": ["#7fff00","#ffa500","#ff1493", "#8a2be2","#1493ff"]
}
#randomized version which will be used for plotting lines
#maybe todo: automatize the generation of this palette?
palettes_randomized = {
    "vaporwave": [
        "#94D0FF",
        "#ff6a8b", "#20de8b", "#966bff", "#ffde8b",
        "#8795E8", "#ff8b8b", "#8bde8b", "#C774E8",
        "#ffa58b", "#cdde8b", "#AD8CFF", "#c774a9", "#FF6AD5"
    ],

    "cool": [
        "#FF6AD5",
        "#94D0FF", "#8795E8", "#AD8CFF", "#C774E8"
    ],

    "crystal_pepsi": [
        "#FFCCFF",
        "#CCFFFF", "#E3E8FF", "#F1DAFF"
    ],

    "mallsoft": [
        "#fbcff3",
        "#30bfdd", "#f7c0bb", "#8690ff", "#7fd4c1", "#acd0f4"
    ],

    "jazzcup": [
        "#392682",
        "#83dde0", "#7a3a9a", "#28ada8", "#3f86bc"
    ],

    "sunset": [
        "#661246",
        "#f9897b", "#ae1357", "#f9247e", "#d7509f"
    ],

    "macplus": [
        "#1b4247",
        "#ffc0cb", "#09979b", "#fe7f9d", "#75d8d5", "#65323e"
    ],

    "seapunk": [
        "#532e57",
        "#7ec488", "#a997ab", "#296656", "#569874"
    ],

    "avanti": [
        "#FB4142",
        "#9DCFF0", "#94376C", "#76BDCF", "#CE75AD"
    ],

    "neon_crystal_pepsi": [
        "#CD8BCD",
        "#82CACA", "#9BA9DB", "#B693D9"
    ],

    "windows95": [
        "#008080",
        "#ff0081", "#6c6c6c", "#dfe300", "#0827f5"
    ],

    "y2k": [
        "#7fff00",
        "#8a2be2", "#ffa500", "#1493ff", "#ff1493"
    ]
}


#For colormaps, we create smooth versions using LinearSegmentedColormap for better gradients
cmap_dict = {}
for name, colors in palettes_ordered.items():
    if len(colors) >= 2:
        cmap_dict[name] = LinearSegmentedColormap.from_list(name, colors, N=256)


def available(show=True):
    if not show:
        return palettes_ordered.keys()
    else:
        f, ax = plt.subplots(4, 3, figsize=(5, 8))
        for i, name in enumerate(palettes_ordered.keys()):
            x, y = i // 3, i % 3
            cycle = palettes_ordered[name]
            for j, c in enumerate(cycle):
                ax[x, y].hlines(j, 0, 1, colors=c, linewidth=15)
            ax[x, y].set_ylim(-1, len(cycle))
            ax[x, y].set_title(name)
            despine(ax[x, y], True)
        plt.show()

def check_key(palname):
    try:
        palettes_ordered[palname]
    except KeyError:
        raise KeyError("{} not an accepted palette name. Check matplotwave.available() for available palettes".format(palname))

def cmap(palname):
    check_key(palname)
    return cmap_dict[palname]

def despine(ax, all=False):
    if all is True:
        for sp in ax.spines:
            ax.spines[sp].set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
    else:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()

def font_size(s):
    matplotlib.rcParams.update({'font.size': s})

def palette(palname=None):
    if palname is None:
        return palettes_ordered
    else:
        check_key(palname)
        return palettes_ordered[palname]

def reverse(palname):
    check_key(palname)
    return list(reversed(palette(palname)))

def set_palette(palname):
        check_key(palname)
        rcParams['axes.prop_cycle'] = cycler.cycler(color=palettes_randomized[palname])

def set_dark_theme():
    dark_bg = '#1a1a1a'
    light_text = '#e0e0e0'
    rcParams['figure.facecolor'] = dark_bg
    rcParams['axes.facecolor'] = dark_bg
    rcParams['axes.edgecolor'] = light_text
    rcParams['axes.labelcolor'] = light_text
    rcParams['xtick.color'] = light_text
    rcParams['ytick.color'] = light_text
    rcParams['grid.color'] = '#444444'
    rcParams['text.color'] = light_text
def set_light_theme():
    light_bg = '#ffffff'
    dark_text = '#000000'
    rcParams.update({
        'figure.facecolor': light_bg,
        'axes.facecolor': light_bg,
        'axes.edgecolor': dark_text,
        'axes.labelcolor': dark_text,
        'xtick.color': dark_text,
        'ytick.color': dark_text,
        'grid.color': '#eaeaf2',
        'text.color': dark_text,
    })
def view_palette(*args):
    if len(args) > 1:
        f, ax = plt.subplots(1, len(args), figsize=(3 * len(args), 3))
        for i, name in enumerate(args):
            check_key(name)
            cycle = palettes_ordered[name]
            for j, c in enumerate(cycle):
                ax[i].hlines(j, 0, 1, colors=c, linewidth=15)
            ax[i].set_title(name)
            despine(ax[i], True)
        plt.show()
    elif len(args) == 1:
        f = plt.figure(figsize=(3, 3))
        check_key(args[0])
        cycle = palettes_ordered[args[0]]
        for j, c in enumerate(cycle):
            plt.hlines(j, 0, 1, colors=c, linewidth=15)
        plt.title(args[0])
        despine(plt.axes(), True)
        f.tight_layout()
        plt.show()
    else:
        raise NotImplementedError("ERROR: supply a palette to plot. check matplotwave.available() for available palettes")
