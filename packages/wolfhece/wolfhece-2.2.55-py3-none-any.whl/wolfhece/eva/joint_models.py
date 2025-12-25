"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
from scipy import stats
from scipy.optimize import root_scalar
from math import prod

import matplotlib.pyplot as plt

"""
Joint model of independant variables
"""

class JointModel():
    """
    Modèle statistique conjoint de variables indépendantes

    L'indépendance permet de simplifier significativement les calculs en se résumant au produit des fonctions de base
    """
    def __init__(self,component_distributions) -> None:
        """
        component_distributions : Liste des distributions à joindre
        """
        self._components = component_distributions

        # Return the function that is the pdf of the joint distribution
        self.pdf = lambda x: prod(component_dist.pdf(x) for component_dist in component_distributions)
        # Return the function that is the cdf of the joint distribution
        self.cdf = lambda x: prod(component_dist.cdf(x) for component_dist in component_distributions)
        # Return the function that is the nnlf of the joint distribution
        self.nnlf = lambda x: -np.log(self.pdf(x))

    def ppf(self,p):
        """
        Return the pth quantile of the joint distribution given by the component distributions
        Recherche du quantile sur base de la résolution d'une fonction non linéaire
        """
        # We can probably be a bit smarter about how we pick the limits
        lo = np.min([dist.ppf(.00001) for dist in self._components])
        hi = np.max([dist.ppf(.99999) for dist in self._components])

        # root_scalar must have opposite sign for function to bounds
        while np.sign(p-self.cdf(lo)) * np.sign(p-self.cdf(hi))>0:
            lo/=2
            hi*=2

        if lo is np.nan:
            lo = -10000.
        if hi is np.nan:
            hi = 10000.

        # find root "x" of the lambda function defined as "p-cdf(x)""
        res = root_scalar(lambda x,p,f: p-f(x), args=(p,self.cdf), method='brenth', bracket=[lo,hi])
        if res.converged:
            return res.root
        else:
            print(res)
            raise ValueError('Bad convergence of the root scalar function - Please debug !')

    def plots(self,fig=None, axes=None, show=True):
        """
        Graphique de la cdf et de la pdf
        """
        if axes is None:
            fig, axes = plt.subplots(2,1)

        p = np.arange(.1, 1.,.001)
        q_all = []
        ax=axes[0]
        for k, curdist in enumerate(self._components):
            q = curdist.ppf(p)
            q_all+=list(q)
            ax.plot(q,p, label='component {}'.format(k+1))

        q = [self.ppf(curp) for curp in p]
        q_all+=q

        ax.plot(q,p, label='joint model')
        ax.legend()
        ax.set_title('Cumulative probability function')
        ax.set_xlabel('Quantile')
        ax.set_ylabel('Cumulative probability')

        q_all = np.asarray(sorted(q_all))

        ax=axes[1]
        for k, curdist in enumerate(self._components):
            p = curdist.pdf(q_all)
            ax.plot(q_all,p, label='component {}'.format(k+1))

        p = [self.pdf(curq) for curq in q_all]
        ax.plot(q_all,p, label='joint model')
        ax.legend()
        ax.set_title('Density probability function')
        ax.set_xlabel('Quantile')
        ax.set_ylabel('Probability')

        fig.tight_layout()
        if show:
            fig.show()

        return fig,axes


def test_joint_gev():
    # The two component distributions: 2 gev
    component_dists = [stats.genextreme(c=0., loc=0., scale=1.), stats.genextreme(c=0.1, loc=1., scale=1.)]
    # We want the 90th percentile of the mixture
    p = 0.9
    myjoint = JointModel(component_dists)
    quantile = myjoint.ppf(p)

    myjoint.plots()

    if abs(quantile - 3.337033672304296) > 1e-13:
        raise Exception('Bad result -- Verify')
    print("Computed quantile for p = 0.9: {}".format(quantile))

def test_joint_mixture():
    """
    Comparaison d'une approche de jointure et de mélange
    """
    try:
        from mixture_models import SeasonMixtureModel

        # The two component distributions: 2 gev
        component_dists = [stats.genextreme(c=0., loc=0., scale=1.), stats.genextreme(c=0.1, loc=1., scale=1.)]
        # We want the 90th percentile of the mixture
        p = 0.9

        myjoint = JointModel(component_dists)
        mymixt  = SeasonMixtureModel(component_dists, [0.5,0.5])

        quantile_j = myjoint.ppf(p)
        quantile_m = mymixt.ppf(p)
        quantile_m2 = mymixt.ppf(np.power(p,2.))

        p_j = myjoint.cdf(quantile_j)
        p_m = mymixt.cdf(quantile_m)

        fig,ax = myjoint.plots(show=False)
        mymixt.plots(fig,ax)

        if abs(quantile_j - 3.337033672304296) > 1e-13:
            raise Exception('Bad result -- Verify')

        if abs(quantile_m - 3.901156543126872) > 1e-13:
            raise Exception('Bad result -- Verify')

        if abs(p_j-p) > 1e-13:
            raise Exception('Bad result -- Verify')
        if abs(p_m-p) > 1e-13:
            raise Exception('Bad result -- Verify')

        print("Computed quantile for p = 0.9 - joint model: {}".format(quantile_j))
        print("Computed quantile for p = 0.9 - mixture model: {}".format(quantile_m))
    except :
        raise Exception('Test de comparaison joint/mixture non calculé -- Verify')
        pass

if __name__ == '__main__':
    test_joint_gev()
    test_joint_mixture()
    pass
