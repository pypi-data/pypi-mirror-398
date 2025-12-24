#! /usr/bin/env python3
'''
Create OGLS logo
'''
from matplotlib import rcParams

rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = 'Helvetica'
rcParams['font.size'] = 10
rcParams['mathtext.fontset'] = 'custom'
rcParams['mathtext.rm'] = 'sans'
rcParams['mathtext.bf'] = 'sans:bold'
rcParams['mathtext.it'] = 'sans:italic'
rcParams['mathtext.cal'] = 'sans:italic'
rcParams['mathtext.default'] = 'rm'
rcParams['xtick.major.size'] = 4
rcParams['xtick.major.width'] = 1
rcParams['ytick.major.size'] = 4
rcParams['ytick.major.width'] = 1
rcParams['axes.grid'] = False
rcParams['axes.linewidth'] = 1
rcParams['grid.linewidth'] = .75
rcParams['grid.linestyle'] = '-'
rcParams['grid.alpha'] = .15
rcParams['savefig.dpi'] = 100

yello = (1,.8,.2)

from ogls import *

X = [1, 2, 3, 4, 5]
Y = [4, 0, 2, 3, 0]
sX = [.15, .2, .08, .1, .05]
sY = [.2, .2, .16, .5, .25]
sYX = np.diag(np.array([.75,0,-.75,0,-.5])*np.array(sX)*np.array(sY))

M = Polynomial(
	X=X,
	Y=Y,
	sX=sX,
	sY=sY,
	sYX=sYX,
	degrees = [0,1,2,3],
	)

M.regress(verbose = True, params = dict(a0 = 0, a1 = 0))
# 	params = dict(a0 = 13, a1 = -1, a3 = .5)

xmin, xmax = np.min(X)-.5, np.max(X)+.25
mycolor = yello
ppl.figure(figsize = (2, 1.5))
ppl.subplots_adjust(.02,.02,.98,.98)
M.plot_bff_ci(xi = np.linspace(xmin, xmax, 101), color = mycolor, zorder = -20, alpha = 1/3)
M.plot_bff(xi = np.linspace(xmin, xmax, 101), color = mycolor, lw = 2, zorder = -10)
# M.plot_error_bars()
M.plot_error_ellipses(ec = 'k')
# M.plot_data()
ppl.text(0.92, 0.9, 'OGLS', va = 'top', ha = 'right', size = 24, weight = 'bold', color = mycolor, transform = ppl.gca().transAxes)
ppl.xticks([])
ppl.yticks([])
ppl.axis([xmin, xmax, M.bff(xmax), M.bff(xmin)])
ppl.setp(ppl.gca().spines.values(), color=(.75,.75,.75))
ppl.savefig('ogls_logo.png')
