import json
import torch
import pyro
import pyro.distributions as dist
from pyro.distributions.util import log_sum_exp
from torch.distributions import constraints, transform_to
from pyro.infer import SVI, ADVIDiagonalNormal
import pyro.optim as optim
from pdb import set_trace as bb


def model(K, N, D, y, alpha0, alpha0_vec):
    theta = pyro.sample("theta", dist.Dirichlet(alpha0_vec))
    mu = pyro.sample("mu", dist.Normal(torch.zeros(K, D), 10. * torch.ones(K, D)))
    sigma = pyro.sample("sigma", dist.LogNormal(torch.ones(K, D), torch.ones(K, D)))
    # sigma = transform_to(dist.Normal.arg_constraints['scale'])(sigma)

    with pyro.iarange('data'):
        assign = pyro.sample('mixture', dist.Categorical(theta))
        pyro.sample('obs', dist.Normal(mu[assign], sigma[assign]), obs=data)


def get_data(fname, varnames):
    with open(fname, "r") as f:
        j = json.load(f)
    d = {}
    for i in range(len(j[0])):
        var_name = j[0][i]
        if isinstance(j[1][i], int):
            val = j[1][i]
        else:
            val = torch.tensor(j[1][i])
        d[var_name] = val
    return tuple([d[k] for k in varnames]), d


def transformed_data(K, N, D, y, alpha0):
    alpha0_vec = torch.ones(K) * alpha0
    return alpha0_vec


def main(args):
    advi = ADVIDiagonalNormal(model)
    adam = optim.Adam({'lr': 1e-3})
    svi = SVI(advi.model, advi.guide, adam, loss="ELBO")
    for i in range(100):
        loss = svi.step(*args)
        print('loss=', loss)
        if i % 5 == 0:
            d = advi.median()
#             print({k: d[k] for k in ["mu", "theta", "sigma"]})


if __name__ == "__main__":
    varnames = ["K", "N", "D", "y", "alpha0"]
    (K, N, D, y, alpha0), data = get_data("data/training.data.json", varnames)
    alpha0_vec = transformed_data(K, N, D, y, alpha0)
    args = (K, N, D, y, alpha0, alpha0_vec)
    main(args)