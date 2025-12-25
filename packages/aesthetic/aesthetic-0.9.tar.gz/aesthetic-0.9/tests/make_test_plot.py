from aesthetic.plot import set_style

import numpy as np, matplotlib.pyplot as plt, matplotlib as mpl

def make_plot(style):
    x = np.linspace(0,10,1000)
    y = (x/100)**3 + 5*np.sin(x)
    _x, _y = np.arange(2, 8, 0.5), np.arange(2, 8, 0.5)

    fig, ax = plt.subplots(figsize=(3,2.5))
    cs = [None]*3 if '_wob' not in style else ['cyan','lime','yellow']
    ax.plot(x, y, label=f'style: {style}', color=cs[0])
    ax.plot(x, y+3, color=cs[1])
    ax.plot(x, y+6, color=cs[2])
    _yerr = np.abs(np.random.normal(2, 1, _x.size))
    c = 'k' if '_wob' not in style else 'w'
    ax.errorbar(_x, _y, yerr=_yerr, marker='o', elinewidth=0.5, lw=0, c=c, markersize=2)
    ax.update({ 'xlabel': r'x [units]', 'ylabel': r'y [units]' })
    ax.legend(fontsize='small')
    return fig

if __name__ == '__main__':
    styles = ['clean', 'science', 'clean_wob', 'science_wob']
    for style in styles:
        set_style(style)
        fig = make_plot(style)
        fig.savefig(f'../results/plot_{style}.png', bbox_inches='tight', dpi=400)
        mpl.rc_file_defaults()
