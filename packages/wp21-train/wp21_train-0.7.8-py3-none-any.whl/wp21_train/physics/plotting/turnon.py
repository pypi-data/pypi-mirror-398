import os
#import atlas_mpl_style as ampl
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np

class DashAxis:
    def __init__(self, axis, show=True):
        self._show = show
        self._axis = axis
        self._data = None

    def set_title(self, *args, **kwargs):
        if self._axis is not None and self._show:
            self._axis.set_title(*args, **kwargs)

    def set_xlabel(self, *args, **kwargs):
        if self._axis is not None and self._show:
            self._axis.set_xlabel(*args, **kwargs)

    def set_ylabel(self, *args, **kwargs):
        if self._axis is not None and self._show:
            self._axis.set_ylabel(*args, **kwargs)

    def set_xlim(self, *args, **kwargs):
        if self._axis is not None and self._show:
            self._axis.set_xlim(*args, **kwargs)

    def set_ylim(self, *args, **kwargs):
        if self._axis is not None and self._show:
            self._axis.set_ylim(*args, **kwargs)

    def legend(self, *args, **kwargs):
        if self._axis is not None and self._show:
            self._axis.legend(*args, **kwargs)

    def axvline(self, *args, **kwargs):
        if self._axis is not None and self._show:
            self._axis.axvline(*args, **kwargs)

    def scatter(self, *args, **kwargs):
        if self._axis is not None and self._show:
            self._axis.scatter(*args, **kwargs)

    def errorbar(self, *args, **kwargs):
        if self._axis is not None and self._show:
            self._axis.errorbar(*args, **kwargs)

    def plot(self, *args, **kwargs):
        if self._axis is not None and self._show:
            self._axis.plot(*args, **kwargs)
        self._data= {"x": args[0].to_list(), "y": args[1].to_list()}

    @property
    def _get_lines(self):
        if self._axis is not None:
            return self._axis._get_lines
        return None

    @property
    def data(self):
        return self._data

class Plotter:
    def __init__(self, curves, baseline_curve_label=None):
        self._curves = curves
        self._baseline_curve_label = baseline_curve_label

    @staticmethod
    def _get_bin_centers(curve, x_key):
        x = curve[x_key].rolling(2).mean().dropna()
        diff = x.diff().dropna().median()
        x = x.to_list()
        x += [x[-1] + diff]
        return x
   
    @staticmethod
    def _get_bin_widths(curve, x_key):
        x = curve[x_key].diff().dropna()
        x = x.to_list()
        x += [x[-1]]
        return x
   
    @staticmethod
    def _get_plotting_data(curve, x_key):
        x_for_err = Plotter._get_bin_centers(curve, x_key)
        bin_widths = np.array(Plotter._get_bin_widths(curve, x_key))
        y_err = np.sqrt((curve['efficiency']*(1-curve['efficiency']))/curve['denominator']).fillna(0)
        eff=curve['efficiency'].iloc[:-1]
        x_for_err = np.array(x_for_err[:-1])
        y_err = y_err.iloc[:-1]
        bin_widths = bin_widths[1:]
        return x_for_err[eff>0], eff.loc[eff>0], y_err.loc[eff>0], bin_widths[eff>0]
   
    @staticmethod
    def _get_ratio(curve, baseline_curve):
        ratio = curve['efficiency'].copy()
        ratio /= baseline_curve['efficiency']
        ratio[(curve['efficiency'].values == 0) & (curve['efficiency'].values == 0)] = 1
        return ratio.values
    
    def plot_curves(self, plot_ratio=False, grid=True, s=20,alpha=0.5,alpha_steps=0.5, colors=[], draw_style='steps', ax=None, do_square = False, use_dash=False, show=True, \
            x_label="Offline $p_T$ (MeV)", save_path=None):
        """
        do_square - adjust the figsize and ratio to be more square
        """
        figsize = (12,8) if do_square else (12,7)
       
        curves = self._curves
        if not curves:
            return
        if not ax:
            if plot_ratio:
                assert self._baseline_curve_label in curves, f"baseline_curve_level set to {self._baseline_curve_label} but it's not in curves"
                fig = plt.figure(constrained_layout=True)
                # width_ratios[i] / sum(width_ratios)
                widths = [1]
                heights = [4,1] if do_square else [2,1]
                gs_kw = dict(width_ratios=widths, height_ratios=heights)
                fig, axes = plt.subplots(ncols=1, nrows=2, constrained_layout=True,
                                         gridspec_kw=gs_kw, figsize=figsize)
                #fig = plt.figure(figsize=(12, 7), dpi=80)
                ax = axes[0]
            else:
                fig = plt.figure(figsize=figsize, dpi=80)
                ax = fig.gca()
  
        if use_dash:
            ax=DashAxis(ax, show)

        x_key = 'pt'
        xmin = 0
        xlabel = x_label
        if 'pt' not in list(curves.values())[0]:
            x_key = 'eta'
            xmin=list(curves.values())[0][x_key].min()
            xlabel = "$\\eta$"

        _, _, _, bin_widths = Plotter._get_plotting_data(list(curves.values())[0], x_key)
        min_separation = min(bin_widths/len(curves)) # Used to separate between turnons for mlutiple turnons (then set to something other than 1
    
        xmax=list(curves.values())[0][x_key].max()
        cols=[]
        for i, (label, curve) in enumerate(curves.items()):
            if not colors:
                colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
            color = colors[i%len(colors)]
            cols.append(color)
            if len(curve) == 0:
                print(f"WARNING: empty turn-on curve for {label}")
                continue
            x_for_err, y_for_err, y_err, _ = Plotter._get_plotting_data(curve, x_key)
            if 'steps' in draw_style:
                if draw_style=='steps+points':
                    label_kwargs = {}
                else:
                    label_kwargs = {'label':label}#self.get_label(label, curve)}
                ax.plot(curve[x_key], curve['efficiency'],
                        lw=2, drawstyle='steps-post', color=color, alpha=alpha_steps, **label_kwargs)
            if 'points' in draw_style:
                x_for_err += min_separation*i - min_separation * (len(curves)/2-0.5)
                ax.scatter(x_for_err, y_for_err,
                        lw=2, label=label, color=color, alpha=alpha, s=s)
            ax.errorbar(x_for_err, y_for_err, yerr=y_err, fmt='', ls='', color=color, alpha=alpha)
    
        if grid:
            for xc in list(curves.values())[0][x_key]:
                ax.axvline(x=xc, c='grey', alpha=0.2)
    
        if plot_ratio:
            x = Plotter._get_bin_centers(list(curves.items())[0][1], x_key)
            for i, (label, c) in enumerate(curves.items()):
                if label == self._baseline_curve_label:
                    baseline_color = cols[i]
                    continue
                ratio = Plotter._get_ratio(c, curves[self._baseline_curve_label])
    
                color = cols[i]
                if (pd.Series(ratio).replace({np.inf: 0, -np.inf:0}).fillna(0) == 0).all():
                    print(f"WARNING: ratio is all either 0 or nan for {label}")
                    continue
                axes[1].scatter(x, ratio, lw=2, label=label, color=color, s=2)
    
            axes[1].hlines(y=1, xmin=0, xmax=xmax, linewidth=2, color=baseline_color)
            axes[1].set_xlabel("Offline $p_T$ (MeV)")
            axes[1].set_ylabel('Eff/Eff({})'.format(self._baseline_curve_label))
            ylim_max_ratio = 1.4 if do_square else 2
            ylim_min_ratio = 0.6 if do_square else 0
            axes[1].set_ylim(ylim_min_ratio, ylim_max_ratio)
            axes[1].set_xlim(0, xmax)
    
        if (not plot_ratio):
            ax.set_xlabel(xlabel)
        ax.set_ylabel('Efficiency')
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        #ax.set_title(title)
        ax.set_ylim(0, 1.1)
        ax.set_xlim(xmin, xmax)

        if save_path:
            ax.get_figure().savefig(save_path, dpi=300, bbox_inches="tight")

        return ax

    @staticmethod    
    def atlas_style():
        ampl.use_atlas_style()
    
