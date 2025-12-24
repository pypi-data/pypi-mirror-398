'''
Omnivariant generalized least-square regression
'''

__author__    = 'Mathieu Daëron'
__contact__   = 'daeron@lsce.ipsl.fr'
__copyright__ = 'Copyright (c) 2023 Mathieu Daëron'
__license__   = 'MIT License - https://opensource.org/licenses/MIT'
__docformat__ = "restructuredtext"
__date__      = '2025-12-20'
__version__   = '1.0.1'

import numpy as np
from scipy.stats import chi2, kstest
from scipy.linalg import cholesky, eigh
from matplotlib import pyplot as ppl
from matplotlib.patches import Ellipse
from lmfit import Minimizer, Parameters, fit_report
import sys
from loguru import logger

logger.remove()
# logger.add(sys.stderr, format="{time} {level} {message}", level='DEBUG')

def sigma(C):
	'''
	Extract SE values from covariance matrix
	'''
	return np.diag(C)**.5

def cov_ellipse(CM, p = .95):
	"""
	Parameters
	----------
	CM : (2, 2) array
		Covariance matrix.
	p : float
		Confidence level, should be in (0, 1)

	Returns
	-------
	width, height, rotation :
		 The lengths of two axes and the rotation angle in degree
	for the ellipse.
	"""

	r2 = chi2.ppf(p, 2)
	val, vec = eigh(CM)
	width, height = 2 * np.sqrt(val[:, None] * r2)
	rotation = np.degrees(np.arctan2(*vec[::-1, 0]))

	return width, height, rotation

class OGLS_Regression():
	'''
	Define `(x,y)` data, their covariance matrix, and a model function `y = f(x)`.
	'''

	def __init__(self,
		X, Y,
		model_fun,
		model_fun_J,
		sX = None,
		sY = None,
		sYX = None,
		bfp  = None,
		bfp_CM = None,
		chisq = None,
		cholesky_residuals = None,
		aic = None,
		bic = None,
		ks_pvalue = None,
		method = 'least_squares',
		):

		self.method = method                               # lmfit method to use for minimization
		self.bfp = bfp                                     # bst-fit parameters
		self.bfp_CM = np.asarray(bfp_CM, dtype = 'float')  # (co)variance matrix of bfp
		self.chisq = chisq                                 # best-fit chi-square value
		self.cholesky_residuals = cholesky_residuals
		self.aic = aic
		self.bic = bic
		self.ks_pvalue = ks_pvalue

		self.X = np.asarray(X, dtype = 'float')            # X observations
		self.Y = np.asarray(Y, dtype = 'float')            # Y observations

		self.N = self.X.size                                    # N of observations

		self.fit_params = Parameters()
		for k in model_fun_J:
			if k != 'X':
				self.fit_params.add(k, value = 0)

		self.Nf = self.N - len(self.fit_params)            # degrees of freedom

		try:
			self.red_chisq = chisq / self.Nf
		except:
			self.red_chisq = None
		try:
			self.chisq_pvalue = chi2.cdf(chisq, self.Nf)
		except:
			self.chisq_pvalue = None
		
		# assign X (co)variance:
		if sX is None:
			self.sX = np.zeros((self.N, self.N))
		else:
			self.sX = np.asarray(sX)
			if len(self.sX.shape) == 1:
				self.sX = np.diag(self.sX**2)
			elif len(self.sX.shape) == 0:
				self.sX = np.eye(self.X.size) * self.sX**2

		# assign Y (co)variance:
		if sY is None:
			self.sY = np.zeros((self.N, self.N))
		else:
			self.sY = np.asarray(sY)
			if len(self.sY.shape) == 1:
				self.sY = np.diag(self.sY**2)
			elif len(self.sY.shape) == 0:
				self.sY = np.eye(self.Y.size) * self.sY**2
		
		# assign XY (co)variance:
		if sYX is None:
			self.sYX = np.zeros((self.N, self.N))
		else:
			self.sYX = np.asarray(sYX)


		self.model_fun = model_fun
		self.model_fun_J = model_fun_J
		self.model_fun_deriv = self.model_fun_J['X']
		self.J = np.block([[np.eye(self.N)], [np.zeros((self.N, self.N))]])
		
		self.V = np.block([[self.sY, self.sYX], [self.sYX.T, self.sX]])

	def cost_fun(self, p):
		self.R = (self.Y - self.model_fun(p, self.X)).reshape(self.N, 1)
		self.J[-self.N:,:] = -np.diag(self.model_fun_deriv(p, self.X))
		invS = np.linalg.solve(self.J.T @ self.V @ self.J, np.eye(self.N))
		L = cholesky(invS)

		logger.debug(f'R.T =\n{self.R.T}')
		logger.debug(f'J =\n{self.J}')
		logger.debug(f'V =\n{self.V}')
		logger.debug(f'self.J.T @ self.V @ self.J =\n{self.J.T @ self.V @ self.J}')
		logger.debug(f'invS =\n{invS}')
		logger.debug(f'L =\n{L}')
		logger.debug(f'L @ self.R =\n{L @ self.R}')
		if self.N > len(p):
			logger.debug(f'Reduced chi-squared = {((L @ self.R).T @ (L @ self.R)).item() / (self.N - len(p))}')

		return L @ self.R

	def regress(self, verbose = False, params = None, overdispersion_scaling = False, underdispersion_scaling = False):
		'''
		Perform regression
		'''

		if isinstance(params, dict):
			for k in params:
				if isinstance(params[k], dict):
					self.fit_params[k].set(**{
						j: params[k][j] for j in params[k]
						if j in ['value', 'vary', 'min', 'max', 'expr', 'brute_step']
						})
				else:
					self.fit_params[k].set(value = params[k])

		model = Minimizer(self.cost_fun, self.fit_params, scale_covar = False)
		minresult = model.minimize(method = self.method)
		if not minresult.success:
			print(f'CONVERGENCE ERROR: {minresult.message}')
		if not minresult.errorbars:
			print(f'WARNING: error bars were not computed')
		if verbose:
			print(fit_report(minresult))
		
		self.cholesky_residuals = minresult.residual
		self.chisq = float(self.cholesky_residuals.T @ self.cholesky_residuals)
		self.Nf = self.N - len(self.fit_params)
		self.aic = minresult.aic
		self.bic = minresult.bic
		self.ks_pvalue = kstest(self.cholesky_residuals, 'norm', (0, 1)).pvalue
		if self.Nf:
			self.chisq_pvalue = 1 - chi2.cdf(self.chisq, self.Nf)
		else:
			self.chisq_pvalue = None
		
		self.bfp = {k: minresult.params.valuesdict()[k] for k in self.fit_params}
		self.bfp_CM = np.zeros((len(self.fit_params), len(self.fit_params)))
		for j,a in enumerate(self.fit_params):
			for k,b in enumerate(self.fit_params):
				if a in minresult.var_names and b in minresult.var_names:
					self.bfp_CM[j,k] = minresult.covar[minresult.var_names.index(a), minresult.var_names.index(b)]

		if self.Nf:
			self.red_chisq = self.chisq / self.Nf
			self.chisq_pvalue = chi2.cdf(self.chisq, self.Nf)
			if (
				(self.red_chisq > 1 and overdispersion_scaling)
				or
				(self.red_chisq < 1 and underdispersion_scaling)
				):
				self.bfp_CM *= self.red_chisq
		else:
			self.red_chisq = None
		
		self.bfp_se = {k: self.bfp_CM[i,i]**.5 for i,k in enumerate(self.fit_params)}


	def bff(self, x):
		'''
		Best-fit function
		'''
		return self.model_fun(self.bfp, x)

	def bff_covar(self, x):
		'''
		Covariance matrix of best-fit function over vector of x values
		'''
		J = np.array([self.model_fun_J[k](self.bfp, x) for k in self.fit_params])
		return J.T @ self.bfp_CM @ J

	def bff_se(self, x):
		'''
		SE of best-fit function
		'''
		var = self.bff_covar(x)
		if len(var.shape):
			return np.diag(var)**.5
		return var**.5

	def plot_data(self, **kw):
		kw_defaults = dict(
			ls = 'None',
			marker = 'o',
			ms = 5,
			mew = 1,
			mec = 'b',
			mfc = 'w',
			)
		return ppl.plot(self.X, self.Y, **{**kw_defaults, **kw})

	def plot_error_bars(self, p = 0.95, **kw):
		pfactor = chi2.ppf(p, 1)**.5 # this applies to the confidence intervals on X and Y
		kw_defaults = dict(
			ls = 'None',
			marker = 'None',
			ecolor = 'b',
			elinewidth = 1,
			capthick = 1,
			capsize = 2,
			)
		return ppl.errorbar(self.X, self.Y, pfactor * sigma(self.sY), 1.96 * sigma(self.sX), **{**kw_defaults, **kw})

	def plot_error_ellipses(self, p = 0.95, **kw):
		out = []
		kw_defaults = dict(
			ls = '-',
			lw = 1,
			fc = 'None',
			ec = 'b',
			)
		for k in range(self.X.size):
			w,h,r = cov_ellipse(np.array([[self.sX[k,k], self.sYX[k,k]], [self.sYX[k,k], self.sY[k,k]]]), p )
			out.append(
				ppl.gca().add_patch(
					Ellipse(
						xy = (self.X[k], self.Y[k]),
						width = w,
						height = h,
						angle = r, **{**kw_defaults, **kw}),
						)
				)
		ppl.gca().autoscale_view()
		return out
	
	def plot_bff(self, xi = None, Nxi = 1001, **kw):
		if xi is None:
			Xspan = self.X.max() - self.X.min()
			xi = np.linspace(self.X.min() - Xspan/20, self.X.max() + Xspan/20, Nxi)
		kw_defaults = dict(
			marker = None,
			ls = '-',
			color = 'r',
			lw = 1,
			)
		return ppl.plot(xi, self.bff(xi), **{**kw_defaults, **kw})

	def plot_bff_ci(self, xi = None, Nxi = 1001, p = 0.95, fill = True, **kw):
		pfactor = chi2.ppf(p, 1)**.5 # this applies to the confidence intervals on Y
		if xi is None:
			Xspan = self.X.max() - self.X.min()
			xi = np.linspace(self.X.min() - Xspan/20, self.X.max() + Xspan/20, Nxi)
		kw_defaults = dict(
			lw = 0,
			alpha = .2,
			color = 'r',
			)
		if fill:
			return ppl.fill_between(
				xi,
				self.bff(xi) + pfactor * self.bff_se(xi),
				self.bff(xi) - pfactor * self.bff_se(xi),
				**{**kw_defaults, **kw})
		else:
			return ppl.plot(
				np.array([xi, xi]).T,
				np.array([
					self.bff(xi) + pfactor * self.bff_se(xi),
					self.bff(xi) - pfactor * self.bff_se(xi)
					]).T,
				**{**kw_defaults, **kw})


class Polynomial(OGLS_Regression):
	
	def __init__(self, X, Y,
		sX = None, sY = None, sYX = None,
		degrees = [0,1],
		**kw):
		self.degrees = degrees
		f = lambda p,x: np.array([p[f'a{k}'] * x**k for k in degrees]).sum(axis = 0)
		J = {
			'X': lambda p,x: np.array([k * p[f'a{k}'] * x**(max(1,k)-1) for k in degrees]).sum(axis = 0),
			**{
				f'a{k}': (lambda p,x,k=k: x**k)
				for k in degrees
				}}
		OGLS_Regression.__init__(self, X=X, Y=Y, sX=sX, sY=sY, sYX=sYX, model_fun=f, model_fun_J=J, **kw)

class InverseTPolynomial(Polynomial):

	def __init__(self, T, Y,
		sT = None, sY = None, sTY = None,
		degrees = [0,1], xpower = 1,
		**kw):
		
		self.T = np.asarray(T, dtype = 'float')
		X = 1/(self.T + 273.15)
		
		self.N = self.T.size

		if sT is None:
			self.sT = np.zeros((self.N, self.N))
		else:
			self.sT = np.asarray(sT)
			if len(self.sT.shape) == 1:
				self.sT = np.diag(self.sT**2)
			elif len(self.sT.shape) == 0:
				self.sT = np.eye(self.T.size) * self.sT**2

		if sTY is None:
			self.sTY = np.zeros((self.N, self.N))
		else:
			self.sTY = np.asarray(sTY)

		Jx = np.diag(-X**2)
		sX = Jx.T @ self.sT @ Jx
		sYX = self.sTY @ Jx
		
		Polynomial.__init__(self, X=X, Y=Y, sX=sX, sY=sY, sYX=sYX, degrees = degrees, **kw)

		self._set_xpower(xpower)

	def _set_xpower(self, xpower):
		self.xpower = xpower
		self.Xp = self.X ** self.xpower
		Jxp = self.xpower * np.diag(self.X ** (self.xpower-1))
		self.sXp = Jxp.T @ self.sX @ Jxp
		self.sXpY = self.sYX @ Jxp
	
	def invT_xaxis(self,
		xlabel = None,
		ylabel = None,
		Ti = [0,20,50,100,250,1000],
		):
		if xlabel is None:
			xlabel = f'1 / T$^{self.xpower}$' if self.xpower > 1 else '1/T'
		ppl.xlabel(xlabel)
		if ylabel is not None:
			ppl.ylabel(ylabel)
		ppl.xticks([(273.15 + t) ** -self.xpower for t in Ti])
		ax = ppl.gca()
		ax.set_xticklabels([f"${t}\\,$°C" for t in Ti])
		ax.tick_params(which="major")

		return ax
	
	
	def plot_data(self, label = False, **kw):
		kw_defaults = dict(
			ls = 'None',
			marker = 'o',
			ms = 5,
			mew = 1,
			mec = 'b',
			mfc = 'w',
			)
		if label is not False:
			kw['label'] = self.label if label is True else label
		return ppl.plot(self.Xp, self.Y, **{**kw_defaults, **kw})
		
		
	def plot_error_bars(self, p = 0.95, **kw):
		pfactor = chi2.ppf(p, 1)**.5 # this applies to the confidence intervals on X and Y
		kw_defaults = dict(
			ls = 'None',
			marker = 'None',
			ecolor = 'b',
			elinewidth = 1,
			capthick = 1,
			capsize = 2,
			)
		return ppl.errorbar(self.Xp, self.Y, pfactor * sigma(self.sY), pfactor * sigma(self.sXp), **{**kw_defaults, **kw})

	def plot_error_ellipses(self, p = 0.95, **kw):
		out = []
		kw_defaults = dict(
			ls = '-',
			lw = 1,
			fc = 'None',
			ec = 'b',
			)
		for k in range(self.X.size):
			w,h,r = cov_ellipse(np.array([[self.sXp[k,k], self.sXpY[k,k]], [self.sXpY[k,k], self.sY[k,k]]]), p )
			out.append(
				ppl.gca().add_patch(
					Ellipse(
						xy = (self.Xp[k], self.Y[k]),
						width = w,
						height = h,
						angle = r, **{**kw_defaults, **kw}),
						)
				)
		ppl.gca().autoscale_view()
		return out
	
	def _xlinspace(self, xi = None, Nxi = 1001, span = 1.1, xpmin = 0, xpmax = np.inf):
		'''
		Sample `X**xpower` uniformly over the range of observations and return the corresponding `X` and `X**xpower` values.
		
		### Parameters
		
		+ **xi**:
		If not `None`, simply return `(xi, xi**xpower)`.
		+ **Nxi**:
		Number of `X` values to sample.
		+ **span**:
		The total `X` width to sample, relative to the actual range of observations (i.e. `X.max() - X.min()`).

		### Returns
		
		+ **xi**: the (irregularly-incremented) sampled `X` values.
		+ **xpi**: the corresponding (regularly-incremented) `X**xpower` values.
		'''
		if xi is None:
			Xspan = self.Xp.max() - self.Xp.min()
			xpi = np.linspace(
				max(xpmin, self.Xp.min() - Xspan * (span-1)/2),
				min(xpmax, self.Xp.max() + Xspan * (span-1)/2),
				Nxi,
				)
			xi = xpi ** (1/self.xpower)
		else:
			xpi = xi**self.xpower
		return xi, xpi

	def plot_bff(self, xi = None, Nxi = 1001, span = 1.1, xpmin = 0, xpmax = np.inf, **kw):
		xi, xpi = self._xlinspace(xi, span = span, xpmin = xpmin, xpmax = xpmax)
		kw_defaults = dict(
			marker = None,
			ls = '-',
			color = 'r',
			lw = 1,
			)
		return ppl.plot(xpi, self.bff(xi), **{**kw_defaults, **kw})

	def plot_bff_ci(self, p = 0.95, xi = None, Nxi = 1001, span = 1.1, xpmin = 0, xpmax = np.inf, **kw):
		pfactor = chi2.ppf(p, 1)**.5 # this applies to the confidence intervals on Y
		xi, xpi = self._xlinspace(xi, span = span, xpmin = xpmin, xpmax = xpmax)
		kw_defaults = dict(
			lw = 0,
			color = 'r',
			alpha = .2,
			)
		
		return ppl.fill_between(
			xpi,
			self.bff(xi) + pfactor * self.bff_se(xi),
			self.bff(xi) - pfactor * self.bff_se(xi),
			**{**kw_defaults, **kw})


class WeightedMean2D():

	def __init__(self, X, Y,
		sX = None, sY = None, sYX = None,
		bfp  = None, bfp_CM = None, chisq = None, Nf = None,
		method = 'least_squares',
		):

		self.method = method
		self.bfp = bfp
		self.bfp_CM = np.asarray(bfp_CM, dtype = 'float')
		self.chisq = chisq
		self.Nf = Nf
		self.red_chisq = chisq / Nf if Nf else None

		self.X = np.asarray(X, dtype = 'float')
		self.Y = np.asarray(Y, dtype = 'float')
		
		self.N = self.X.size
		
		if sX is None:
			self.sX = np.zeros((self.N, self.N))
		else:
			self.sX = np.asarray(sX)
			if len(self.sX.shape) == 1:
				self.sX = np.diag(self.sX**2)
			elif len(self.sX.shape) == 0:
				self.sX = np.eye(self.X.size) * self.sX**2

		if sY is None:
			self.sY = np.zeros((self.N, self.N))
		else:
			self.sY = np.asarray(sY)
			if len(self.sY.shape) == 1:
				self.sY = np.diag(self.sY**2)
			elif len(self.sY.shape) == 0:
				self.sY = np.eye(self.Y.size) * self.sY**2
		
		if sYX is None:
			self.sYX = np.zeros((self.N, self.N))
		else:
			self.sYX = np.asarray(sYX)

		self.fit_params = Parameters()
		self.fit_params.add('X', value = 0)
		self.fit_params.add('Y', value = 0)

		self.V = np.zeros((2*self.N, 2*self.N))
		self.V[:self.N,:self.N] = self.sY
		self.V[-self.N:,-self.N:] = self.sX
		self.V[:self.N,-self.N:] = self.sYX
		self.V[-self.N:,:self.N] = self.sYX.T

# 		print(f'self.V =\n{self.V}')

		invS = np.linalg.solve(self.V, np.eye(self.N*2))
		self.L = cholesky(invS)
# 		print(f'L =\n{L}')

	def cost_fun(self, p):
		self.R = np.concatenate((self.Y - p['Y'], self.X - p['X'])).reshape(self.N*2, 1)
# 		print(p)
# 		print(f'R = {self.R.shape}\n{self.R}')
		return self.L @ self.R

	def regress(self, verbose = False, params = None, overdispersion_scaling = False, underdispersion_scaling = False):
		'''
		Perform regression
		'''

		if isinstance(params, dict):
			for k in params:
				if isinstance(params[k], dict):
					self.fit_params[k].set(**{
						j: params[k][j] for j in params[k]
						if j in ['value', 'vary', 'min', 'max', 'expr', 'brute_step']
						})
				else:
					self.fit_params[k].set(value = params[k])

		model = Minimizer(self.cost_fun, self.fit_params, scale_covar = False)
		minresult = model.minimize(method = self.method)
		if not minresult.success:
			print(f'CONVERGENCE ERROR: {minresult.message}')
		if not minresult.errorbars:
			print(f'WARNING: error bars were not computed')
		if verbose:
			print(fit_report(minresult))
		
		self.cholesky_residuals = minresult.residual
		self.chisq = float(self.cholesky_residuals.T @ self.cholesky_residuals)
		self.Nf = self.N - len(self.fit_params)
		self.aic = minresult.aic
		self.bic = minresult.bic
		
		self.bfp = {k: minresult.params.valuesdict()[k] for k in self.fit_params}
		self.bfp_CM = np.zeros((len(self.fit_params), len(self.fit_params)))
		for j,a in enumerate(self.fit_params):
			for k,b in enumerate(self.fit_params):
				if a in minresult.var_names and b in minresult.var_names:
					self.bfp_CM[j,k] = minresult.covar[minresult.var_names.index(a), minresult.var_names.index(b)]

		if self.Nf:
			self.red_chisq = self.chisq / self.Nf
			if (
				(self.red_chisq > 1 and overdispersion_scaling)
				or
				(self.red_chisq < 1 and underdispersion_scaling)
				):
				self.bfp_CM *= self.red_chisq
		else:
			self.red_chisq = None
		
		self.bfp_se = {k: self.bfp_CM[i,i]**.5 for i,k in enumerate(self.fit_params)}

	def plot_data(self, **kw):
		kw_defaults = dict(
			ls = 'None',
			marker = 'o',
			ms = 5,
			mew = 1,
			mec = 'b',
			mfc = 'w',
			)
		return ppl.plot(self.X, self.Y, **{**kw_defaults, **kw})

	def plot_error_bars(self, p = 0.95, **kw):
		pfactor = chi2.ppf(p, 1)**.5 # this applies to the confidence intervals on X and Y
		kw_defaults = dict(
			ls = 'None',
			marker = 'None',
			ecolor = 'b',
			elinewidth = 1,
			capthick = 1,
			capsize = 2,
			)
		return ppl.errorbar(self.X, self.Y, pfactor * sigma(self.sY), 1.96 * sigma(self.sX), **{**kw_defaults, **kw})

	def plot_error_ellipses(self, p = 0.95, **kw):
		out = []
		kw_defaults = dict(
			ls = '-',
			lw = 1,
			fc = 'None',
			ec = 'b',
			)
		for k in range(self.X.size):
			w,h,r = cov_ellipse(np.array([[self.sX[k,k], self.sYX[k,k]], [self.sYX[k,k], self.sY[k,k]]]), p )
			out.append(
				ppl.gca().add_patch(
					Ellipse(
						xy = (self.X[k], self.Y[k]),
						width = w,
						height = h,
						angle = r, **{**kw_defaults, **kw}),
						)
				)
		ppl.gca().autoscale_view()
		return out

class WeightedMean():

	def __init__(self, X, CM, method = 'least_squares'):
		'''
		X = (D, N) array of N observations in D dimensions,

		CM = (N*D, N*D) variance-covariance matrix, with
		     CM[i*N+j, k*N+l] = covariance(X[i,j], X[k,l])
		'''

		self.method = method

		self.X = np.asarray(X, dtype = 'float')
		self.CM = np.asarray(CM, dtype = 'float')
		
		self.D, self.N = self.X.shape		

		self.fit_params = Parameters()
		for i in range(self.D):
			self.fit_params.add(f'X{i}', value = 0)

		invS = np.linalg.solve(self.CM, np.eye(self.N * self.D))
		self.L = cholesky(invS)
# 		print(f'L =\n{L}')

	def cost_fun(self, p):
		self.R = (self.X - np.array([[p[k]] for k in self.fit_params])).reshape((self.N * self.D, 1))
# 		print(f'R = {self.R.shape}\n{self.R}')
		return self.L @ self.R

	def regress(self, verbose = False, params = None, overdispersion_scaling = False, underdispersion_scaling = False):
		'''
		Perform regression
		'''

		if isinstance(params, dict):
			for k in params:
				if isinstance(params[k], dict):
					self.fit_params[k].set(**{
						j: params[k][j] for j in params[k]
						if j in ['value', 'vary', 'min', 'max', 'expr', 'brute_step']
						})
				else:
					self.fit_params[k].set(value = params[k])

		model = Minimizer(self.cost_fun, self.fit_params, scale_covar = False)
		minresult = model.minimize(method = self.method)
		if not minresult.success:
			print(f'CONVERGENCE ERROR: {minresult.message}')
		if not minresult.errorbars:
			print(f'WARNING: error bars were not computed')
		if verbose:
			print(fit_report(minresult))
		
		self.cholesky_residuals = minresult.residual
		self.chisq = float(self.cholesky_residuals.T @ self.cholesky_residuals)
		self.Nf = self.N - len(self.fit_params)
		self.aic = minresult.aic
		self.bic = minresult.bic
		
		self.bfp = {k: minresult.params.valuesdict()[k] for k in self.fit_params}
		self.bfp_CM = np.zeros((len(self.fit_params), len(self.fit_params)))
		for j,a in enumerate(self.fit_params):
			for k,b in enumerate(self.fit_params):
				if a in minresult.var_names and b in minresult.var_names:
					self.bfp_CM[j,k] = minresult.covar[minresult.var_names.index(a), minresult.var_names.index(b)]

		if self.Nf:
			self.red_chisq = self.chisq / self.Nf
			if (
				(self.red_chisq > 1 and overdispersion_scaling)
				or
				(self.red_chisq < 1 and underdispersion_scaling)
				):
				self.bfp_CM *= self.red_chisq
		else:
			self.red_chisq = None
		
		self.bfp_se = {k: self.bfp_CM[i,i]**.5 for i,k in enumerate(self.fit_params)}

class WeightedMeansByCategory():

	def __init__(self, G, X, CM, method = 'least_squares'):
		'''
		X = (D, N) array of N observations in D dimensions,
		G = (N,) array with each element being the unique identifier/category of the corresponding observation,

		CM = (N*D, N*D) variance-covariance matrix, with
		     CM[i*N+j, k*N+l] = covariance(X[i,j], X[k,l])
		
		Regression computes a `bfp` attribute corresponding to an ordered dictionary of
		weighted mean values sorted first by identifier/category then by dimension, and
		a `bfp_CM` attribute corresponding to the variance-covariance matrix of these values.
		'''

		self.method = method

		self.G = np.asarray(G, dtype = 'str')
		self.IDs = sorted(set(self.G))
		self.X = np.asarray(X, dtype = 'float')
		self.CM = np.asarray(CM, dtype = 'float')
		
		self.D, self.N = self.X.shape		

		self.fit_params = Parameters()
		for g in self.IDs:
			for i in range(self.D):
				self.fit_params.add(f'ID{g}_X{i}', value = 0)

		invS = np.linalg.solve(self.CM, np.eye(self.N * self.D))
		self.L = cholesky(invS)
# 		print(f'L =\n{L}')

	def cost_fun(self, p):
# 		print(self.X - np.array([[p[f'ID{g}_X{d}'] for g in self.G] for d in range(self.D)]))
		self.R = (self.X - np.array([[p[f'ID{g}_X{d}'] for g in self.G] for d in range(self.D)])).reshape((self.N * self.D, 1))
# 		print(f'R = {self.R.shape}\n{self.R}')
# 		print(self.CM)
# 		print(self.L @ self.R)
# 		print(float((self.L @ self.R).T @ (self.L @ self.R)))
		return self.L @ self.R

	def regress(self, verbose = False, params = None, overdispersion_scaling = False, underdispersion_scaling = False):
		'''
		Perform regression
		'''

		if isinstance(params, dict):
			for k in params:
				if isinstance(params[k], dict):
					self.fit_params[k].set(**{
						j: params[k][j] for j in params[k]
						if j in ['value', 'vary', 'min', 'max', 'expr', 'brute_step']
						})
				else:
					self.fit_params[k].set(value = params[k])

		model = Minimizer(self.cost_fun, self.fit_params, scale_covar = False)
		minresult = model.minimize(method = self.method)
		if not minresult.success:
			print(f'CONVERGENCE ERROR: {minresult.message}')
		if not minresult.errorbars:
			print(f'WARNING: error bars were not computed')
		if verbose:
			print(fit_report(minresult))
		
		self.cholesky_residuals = minresult.residual
		self.chisq = float(self.cholesky_residuals.T @ self.cholesky_residuals)
		self.Nf = self.N - len(self.fit_params)
		self.aic = minresult.aic
		self.bic = minresult.bic
		
		self.bfp = {g: np.array([minresult.params.valuesdict()[f'ID{g}_X{d}'] for d in range(self.D)]) for g in self.IDs}
		self.bfp_CM = np.zeros((len(self.fit_params), len(self.fit_params)))
		for j,a in enumerate(self.fit_params):
			for k,b in enumerate(self.fit_params):
				if a in minresult.var_names and b in minresult.var_names:
					self.bfp_CM[j,k] = minresult.covar[minresult.var_names.index(a), minresult.var_names.index(b)]

		if self.Nf:
			self.red_chisq = self.chisq / self.Nf
			if (
				(self.red_chisq > 1 and overdispersion_scaling)
				or
				(self.red_chisq < 1 and underdispersion_scaling)
				):
				self.bfp_CM *= self.red_chisq
		else:
			self.red_chisq = None

		