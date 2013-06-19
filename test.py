import unittest
import numpy as np
import crf
from scipy import misc
from collections import defaultdict
from numpy import empty, zeros, ones, log, exp, sqrt, add, int32, abs
def argmax(X):
	"""
	Find the most likely assignment to labels given parameters using the
	Viterbi algorithm.
	"""
	N,K,_ = X.shape
	g0 = X[0,0]
	g  = X[1:]

	B = ones((N,K), dtype=int32) * -1
	# compute max-marginals and backtrace matrix
	V = g0
	for t in xrange(1,N):
		U = empty(K)
		for y in xrange(K):
			w = V + g[t-1,:,y]
			B[t,y] = b = w.argmax()
			U[y] = w[b]
		V = U
	# extract the best path by brack-tracking
	y = V.argmax()
	trace = []
	for t in reversed(xrange(N)):
		trace.append(y)
		y = B[t, y]
	trace.reverse()
	return trace

def forward(g0, g, N, K):
	"""
	Calculate matrix of forward unnormalized log-probabilities.

	a[i,y] log of the sum of scores of all sequences from 0 to i where
	the label at position i is y.
	"""
	a = np.zeros((N,K))
	a[0,:] = g0
	for t in xrange(1,N):
		ayp = a[t-1,:]
		for y in xrange(K):
			a[t,y] = misc.logsumexp(ayp + g[t-1,:,y])
	return a

def backward(g, N, K):
	""" Calculate matrix of backward unnormalized log-probabilities. """
	b = np.zeros((N,K))
	for t in reversed(xrange(0,N-1)):
		by = b[t+1,:]
		for yp in xrange(K):
			b[t,yp] = misc.logsumexp(by + g[t,yp,:])
	return b



def expectation(N,K,log_M):
	"""
	Expectation of the sufficient statistics given ``x`` and current
	parameter settings.
	"""
	g0 = log_M[0,0]
	g  = log_M[1:]
	a = forward(g0,g,N,K)
	b = backward(g,N,K)
	print "Forward:"
	print a
	print "Backward:"
	print b
	# log-normalizing constant
	logZ = misc.logsumexp(a[N-1,:])

	E = defaultdict(float)

	# The first factor needs to be special case'd
	# E[ f( y_0 ) ] = p(y_0 | y_[1:N], x) * f(y_0)
	c = exp(g0 + b[0,:] - logZ).clip(0.0, 1.0)
	for y in xrange(K):
		p = c[y]
		if p < 1e-40: continue   # skip really small updates.
		for k in f[0, None, y]:
			E[k] += p

	for t in xrange(1,N):
		# vectorized computation of the marginal for this transition factor
		c = exp((add.outer(a[t-1,:], b[t,:]) + g[t-1,:,:] - logZ)).clip(0.0, 1.0)

		for yp in xrange(K):
			for y in xrange(K):
				# we can also use the following to compute ``p`` but its quite
				# a bit slower than the computation of vectorized quantity ``c``.
				#p = exp(a[t-1,yp] + g[t-1,yp,y] + b[t,y] - logZ).clip(0.0, 1.0)
				p = c[yp, y]
				if p < 1e-40: continue   # skip really small updates.
				# expectation of this factor is p*f(t, yp, y)
				for k in f[t, yp, y]:
					E[k] += p

	return E


class TestCRF(unittest.TestCase):

	def setUp(self):
		self.matrix = 0.001 + np.random.poisson(lam=1.5, size=(3,3)).astype(np.float)
		self.vector = 0.001 + np.random.poisson(lam=1.5, size=(3,)).astype(np.float)
		self.M = 0.001 + np.random.poisson(lam=1.5, size=(10,3,3)).astype(np.float)
		self.crf = crf.CRF([],[])

	def test_log_dot_mv(self):
		self.assertTrue(
				(np.around(np.exp(
					crf.log_dot_mv(
						np.log(self.matrix),
						np.log(self.vector)
						)
					),10) == np.around(np.dot(self.matrix,self.vector),10)).all()
		)

	def test_log_dot_vm(self):
		self.assertTrue(
				(np.around(np.exp(
					crf.log_dot_vm(
						np.log(self.vector),
						np.log(self.matrix)
						)
					),10) == np.around(np.dot(self.vector,self.matrix),10)).all()
		)

	def test_forward(self):
		M = self.M/self.M.sum(axis=2).reshape(self.M.shape[:-1]+(1,))
		res = np.around(np.exp(self.crf.forward(np.log(M))[0]).sum(axis=1),10)
		res_true = np.around(np.ones(M.shape[0]),10)
		self.assertTrue((res == res_true).all())

	def test_predict(self):
		label_pred = self.crf.log_predict(self.M,self.M.shape[0],self.M.shape[1])
		label_act  = argmax(self.M)
		print label_pred
		print label_act
		self.assertTrue(label_pred == label_act)


if __name__ == '__main__':
	for i in range(10):
		unittest.main()

