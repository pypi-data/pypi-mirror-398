"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
from scipy import stats
from scipy.optimize import root_scalar, minimize
from autograd import jacobian
import matplotlib.pyplot as plt

"""
Refs :
    - Mixture Model in Python:
        - http://www.awebb.info/probability/2017/05/12/quantiles-of-mixture-distributions.html
    - Expectation-Maximization :
        - https://fr.wikipedia.org/wiki/Algorithme_esp%C3%A9rance-maximisation
        - https://wildart.github.io/post/mle-mm/
        - https://wjchen.net/post/en/gmm-em-en.html#3em-algorithm-for-univariate-gmm
        - https://medium.com/@prateek.shubham.94/expectation-maximization-algorithm-7a4d1b65ca55
        - https://towardsdatascience.com/implement-expectation-maximization-em-algorithm-in-python-from-scratch-f1278d1b9137
"""

class MixtureModel():
    """
    Modèle de mélange
    """
    def __init__(self,component_distributions, ps) -> None:
        """
        Liste des distributions à mélanger et liste de coefficients (dont la somme vaut 1.)
        """
        self._components = component_distributions
        self.pond = ps

        # Return the function that is the pdf of the mixture distribution
        self.pdf = lambda x: sum(component_dist.pdf(x) * p for component_dist, p in zip(component_distributions, ps))
        # Internal function that is the cdf of the mixture distribution
        self.cdf = lambda x: sum(component_dist.cdf(x) * p for component_dist, p in zip(component_distributions, ps))
        # Return the function that is the nnlf of the mixture distribution
        self.nnlf = lambda x: -np.log(self.pdf(x))

    def ppf(self,p):
        """
        Return the pth quantile of the mixture distribution given by the component distributions and their probabilities

        Defined like function enabling overloading (ex.: SeasonMixtureModel)
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

        res = root_scalar(lambda x,p,f: p-f(x), args=(p,self.cdf), method='brenth', bracket=[lo,hi], xtol=1e-5)
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

        ax.plot(q,p, label='mixture model')
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
        ax.plot(q_all,p, label='mixture model')
        ax.legend()
        ax.set_title('Density probability function')
        ax.set_xlabel('Quantile')
        ax.set_ylabel('Probability')

        fig.tight_layout()
        if show:
            fig.show()

        return fig,axes

class SeasonMixtureModel(MixtureModel):
    """
    Extension d'un MixtureModel pour tenir compte directement
    de l'adaptation de la probabilité sur base de
    2 saisons sur une année

    Les variables et résultats des fonctions cdf et ppf s'expriment en probabilité annuelle

    Liaison entre période de retour annuelle (T) et probabilité cumulée/de non-dépassement (F)

        $ T = 1/(1-F^2) $
    """

    def __init__(self, component_distributions, ps) -> None:
        super().__init__(component_distributions, ps)

        self.power = 2. # Nombre d'événements sélectionnés par année

        # Return the function that is the pdf of the mixture distribution
        self._pdf = lambda x: sum(component_dist.pdf(x) * p for component_dist, p in zip(component_distributions, ps))
        self.pdf = lambda x: pow(sum(component_dist.pdf(x) * p for component_dist, p in zip(component_distributions, ps)),self.power)
        # Return the function that is the cdf of the mixture distribution
        self.cdf = lambda x: pow(sum(component_dist.cdf(x) * p for component_dist, p in zip(component_distributions, ps)),self.power)
        # Return the function that is the nnlf of the mixture distribution
        self.nnlf = lambda x: -np.log(self.pdf(x))

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

        ax.plot(q,p, label='mixture model')
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
        ax.plot(q_all,p, label='mixture model w expon')

        p = [self._pdf(curq) for curq in q_all]
        ax.plot(q_all,p, label='mixture model wo expon')

        ax.legend()
        ax.set_title('Density probability function')
        ax.set_xlabel('Quantile')
        ax.set_ylabel('Probability')

        fig.tight_layout()
        if show:
            fig.show()

        return fig,axes

def _nnlf_wgen(x0, data, weights):

    shape,loc,scale=x0
    # pdf  = stats.genextreme.pdf(data,shape, loc=loc, scale=scale)
    # func = np.inner(weights[pdf>0.],-np.log(pdf[pdf>0.]))

    lpdf  = stats.genextreme.logpdf(data,shape, loc=loc, scale=scale)
    func = np.inner(weights,-lpdf)

    return func

def _nnlf_wgum(x0, data, weights):

    loc,scale=x0
    lpdf  = stats.gumbel_r.logpdf(data, loc=loc, scale=scale)
    func = np.inner(weights,-lpdf)

    return func


def _nnlf_gen(x0, data):

    shape,loc,scale=x0

    func = -np.sum(np.log(stats.genextreme.pdf(data,shape, loc=loc, scale=scale)))

    return func

def fit_wgev(data, weights, shape = None, loc = None, scale= None):
    """Fit d'une loi GEV avec des poids attachés aux données"""
    if shape is None:
        shape=0.
        loc, scale = stats.gumbel_r.fit(data)

    res = minimize(_nnlf_wgum, (loc,scale), args=(data, weights))
    loc, scale = res.x
    if loc<0:
        res = minimize(_nnlf_wgum, (1.,1.), args=(data, weights))
        loc, scale = res.x

    res = minimize(_nnlf_wgen, (shape,loc,scale), args=(data, weights)) #, method='BFGS')

    newshape, newloc, newscale = res.x
    if abs(newshape)<1 and newloc>0.:
        return newshape, newloc, newscale
    else:
        return shape, loc, scale


def fit_mixture_gev(data, fig, ax, sols):
    """
    Fit d'une loi de mélange sur base d'un algo "simple" d'Espérance-Maximisation
    """
    A_shape=0.
    B_shape=0.

    A_loc, A_scale = stats.gumbel_r.fit(data[:int(len(data)/2)])
    B_loc, B_scale = stats.gumbel_r.fit(data[int(len(data)/2):])

    diff = 1.
    i=1
    while diff>1.e-4:

        old = np.asarray([A_shape, A_loc, A_scale, B_shape, B_loc, B_scale])

        # Pour chaque valeur de X, calculer la probabilité
        # sous l'hypothèse A et B
        p_A = stats.genextreme(A_shape, loc=A_loc, scale=A_scale).pdf(data)
        p_B = stats.genextreme(B_shape, loc=B_loc, scale=B_scale).pdf(data)

        # Calculer pour chaque valeur de X, un poids correspondant
        # à son degrès d'appartenance à la loi A ou B.

        p_total  = p_A + p_B
        weight_A = p_A / p_total
        weight_B = p_B / p_total
        # weight_B = 1. - weight_A

        ax[1].clear()
        ax[1].plot(data, weight_A)
        ax[1].plot(data, weight_B)

        #Ajustement des paramètres

        A_shape, A_loc, A_scale = fit_wgev(data, weight_A, A_shape, A_loc, A_scale)
        B_shape, B_loc, B_scale = fit_wgev(data, weight_B, B_shape, B_loc, B_scale)

        ax[0].clear()
        ax[0].hist(data, bins=200, density=True)
        ax[0].plot(data, stats.genextreme(sols[0][0], loc = sols[0][1], scale = sols[0][2]).pdf(data), 'r--')
        ax[0].plot(data, stats.genextreme(sols[1][0], loc = sols[1][1], scale = sols[1][2]).pdf(data), 'b--')

        ax[0].plot(data,stats.genextreme(A_shape,loc=A_loc,scale=A_scale).pdf(data), 'r')
        ax[0].plot(data,stats.genextreme(B_shape,loc=B_loc,scale=B_scale).pdf(data), 'b')
        fig.canvas.draw()
        fig.canvas.flush_events()

        diff = np.sum(np.abs(old - np.asarray([A_shape, A_loc, A_scale, B_shape, B_loc, B_scale])))
        old = [A_shape, A_loc, A_scale, B_shape, B_loc, B_scale]

        print(i, diff)
        i+=1

    return (A_shape, A_loc, A_scale), (B_shape, B_loc, B_scale), (weight_A, weight_B)

def example_em():
    """
    voir https://dridk.me/expectation-maximisation.html
    """
    import seaborn as sns

    hommes = np.random.normal(190, 10, 1000)
    # hommes = [171,171,173,180,190,159 ...]
    femmes = np.random.normal(160,5, 1000)
    # femmes = [145,170,145,161,139,150 ...]

    # sns.distplot(femmes, label="Femmes")
    # sns.distplot(hommes, label="Hommes")

    X  = np.sort(np.concatenate((femmes,hommes)))

    # sns.distplot(X, label="mixture", color="green",)
    # plt.legend()
    # Distribution des tailles X.. (voir plus haut )
    # X      = [159,158, 159, 179, 189 ....]

    # Générer un modèle aléatoire A
    A_mean = np.random.randint(100,300)
    A_sd   = np.random.randint(10,30)

    # Générer un modèle aléatoire B
    B_mean = np.random.randint(100,300)
    B_sd   = np.random.randint(10,30)

    fig, ax = plt.subplots(1,1)

    # Faite 50 itérations... ( ca suffira)
    for i in range(50):

        # Pour chaque valeur de X, calculer la probabilité
        # sous l'hypothèse A et B
        p_A = stats.norm(loc=A_mean, scale=A_sd).pdf(X)
        p_B = stats.norm(loc=B_mean, scale=B_sd).pdf(X)

        # Calculer pour chaque valeur de X, un poids correspondant
        # à son degrès d'appartenance à la loi A ou B.

        p_total  = p_A + p_B
        weight_A = p_A / p_total
        weight_B = p_B / p_total

        # Exemple : Si la taille de 189cm appartient à la lois B
        # alors weight_B(189) sera grand et weight_A(189) sera petit.

        #Ajustement des paramètres (μA,σA) et (μB,σB) en fonction du poids.

        A_mean = np.sum(X * weight_A )/ np.sum(weight_A)
        B_mean = np.sum(X * weight_B )/ np.sum(weight_B)

        A_sd   = np.sqrt(np.sum(weight_A * (X - A_mean)**2) / np.sum(weight_A))
        B_sd   = np.sqrt(np.sum(weight_B * (X - B_mean)**2) / np.sum(weight_B))

        ax.clear()
        ax.step(X,weight_A)
        ax.step(X,weight_B)

        # On recommence jusqu'à convergence. Non testé ici, je m'arrête à 50 iterations.

    res = stats.genlogistic.fit(weight_A)
    ax.plot(X,stats.genlogistic(res[0],loc=res[1],scale=res[2]).cdf(X))
    pass


def example_one_gev():

    data = [9.4, 38.0, 12.5, 35.3, 17.6, 12.9, 12.4, 19.6, 15.0, 13.2, 12.3, 16.9, 16.9, 29.4, 13.6, 11.1, 8.0, 16.6, 12.0, 13.1, 9.1, 9.7, 21.0, 11.2, 14.4, 18.8, 14.0, 19.9, 12.4, 10.8, 21.6, 15.4, 17.4, 14.8, 22.7, 11.5, 10.5, 11.8, 12.4, 16.6, 11.7, 12.9, 17.8]

    shape, loc, scale = stats.genextreme.fit(data)

    # mle = -np.sum(stats.genextreme(shape, loc=loc, scale=scale).logpdf(data))
    # mle1 = stats.genextreme.nnlf((shape, loc, scale), data)
    # mle2 = _nnlf_gen((shape, loc, scale), data)
    # mle3 = _nnlf_gen((shape, loc, scale), data, np.ones(len(data)))

    if  not np.allclose([shape,loc,scale],[-0.21988720690114583, 12.749730029827154, 3.448963234019624]):
        raise Exception('Bad result -- Verify')

    shape, loc, scale = fit_wgev(data,np.ones(len(data)))

    if  not np.allclose([shape,loc,scale],[-0.21989445389551832, 12.74974586825777, 3.4490271528260927]):
        raise Exception('Bad result -- Verify')

def example_mixture_gev():

    A_sol = [-.15,1.,1.]
    B_sol = [-.2,2.,1.5]
    data1 = stats.genextreme.rvs(A_sol[0], loc = A_sol[1], scale = A_sol[2], size=100)
    data2 = stats.genextreme.rvs(B_sol[0], loc = B_sol[1], scale = B_sol[2], size=100)
    data1 = np.sort(data1)
    data2 = np.sort(data2)

    data_all = np.sort(np.hstack((data1, data2)))

    fig, ax = plt.subplots(2,1)

    ax[0].hist(data_all, bins=200, density=True)
    ax[0].hist(data1,bins=100, density=True)
    ax[0].hist(data2,bins=100, density=True)

    ax[0].plot(data1, stats.genextreme(A_sol[0], loc = A_sol[1], scale = A_sol[2]).pdf(data1))
    ax[0].plot(data2, stats.genextreme(B_sol[0], loc = B_sol[1], scale = B_sol[2]).pdf(data2))
    plt.show(block=False)

    res = fit_mixture_gev(data_all, fig, ax, [A_sol, B_sol])

    print('A : ',res[0])
    print('B : ',res[1])

    ax[0].plot(data_all,stats.genlogistic(res[0][0],loc=res[0][1],scale=res[0][2]).cdf(data_all))
    ax[0].plot(data_all,stats.genlogistic(res[1][0],loc=res[1][1],scale=res[1][2]).cdf(data_all))

    plt.show()

    pass


def test_mixture():
    # The two component distributions: a normal and an exponential distribution
    component_dists = [stats.norm(), stats.expon()]
    # Chosen by fair coin flip
    ps = [0.5, 0.5]
    # We want the 75th percentile of the mixture
    p = 0.75

    mymixt = MixtureModel(component_dists,ps)
    quantile = mymixt.ppf(p)
    test_p = mymixt.cdf(quantile)

    if abs(quantile - 1.044491028438254)>1e-13:
        raise Exception('Bad result -- Verify')
    if abs(test_p-p) > 1e-13:
        raise Exception('Bad result -- Verify')
    print("Computed quantile for p = 0.75: {}".format(quantile))

def test_season_mixture():
    # The two component distributions: a normal and an exponential distribution
    component_dists = [stats.norm(), stats.expon()]
    # Chosen by fair coin flip
    ps = [0.5, 0.5]
    # We want the 75th percentile of the mixture
    p = 0.75

    mymixt = SeasonMixtureModel(component_dists,ps)

    quantile = mymixt.ppf(p)
    test_p = mymixt.cdf(quantile)

    if abs(quantile - 2.1092509198855587) > 1e-13:
        raise Exception('Bad result -- Verify')

    if abs(test_p-p) > 1e-13:
        raise Exception('Bad result -- Verify')

    print("Computed quantile for p = 0.75: {}".format(quantile))

if __name__ == '__main__':
    test_mixture()
    test_season_mixture()

    # example_mixture_gev()
    # example_one_gev()
    # example_em()
