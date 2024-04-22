#!/usr/bin/python
# encoding: utf-8
def plt_rc(plt):
    plt.rc('axes', titlesize=16, linewidth=1.25)
    tick_conf = {
        'direction': 'in',
        'minor.visible': True,
        'major.size': 6,
        'major.width': 1.25,
        'minor.size': 3,
        'minor.width': 1.25,
        'labelsize': 16
         }
    font_conf = {
        "family": 'serif',
        "size": 16,
        "serif": 'Times New Roman'
    }
    # text_conf = {
    #     'usetex' : True,
    #     'latex.preamble' : r"\usepackage{amsmath} \usepackage{amssymb} \usepackage{sfmath}"
    # }
    plt.rc('xtick', **tick_conf)
    plt.rc('ytick', **tick_conf)
    plt.rc('font', **font_conf)
    # plt.rc('text', **text_conf)
    plt.rc('mathtext', fontset='stix')
    plt.rc('lines', linewidth=2)
    plt.rc('grid', linewidth=2)
    # plt.rc('figure',figsize=( 6, 12))

# def main():
    # plt_rc(plt)