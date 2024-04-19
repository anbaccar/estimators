from pathlib import Path
from scipy.special import xlogy
from scipy.stats import poisson
import sys
import json
import os
import time
import numpy as np
from mixed_ksg import Mixed_KSG
from dist_params import *

np.random.seed(0)


class sampleData:
    def __init__(self, params, N, numT, numS, x_A, fn):
        self.params = params  # the distribution params
        self.N = N
        self.x_A = (
            x_A  # vector of attacker inputs (fixed, but can be changed if needed )
        )
        self.x_T = np.asarray(self.sample(numT))
        self.x_S = np.asarray(self.sample(numS))
        self.fn = fn
        self.O = self.produceOutputs()

    def sample(self, numP):
        if self.params.t == "uniform_int":
            return np.reshape(
                np.random.randint(self.params.a, self.params.b, self.N * numP),
                (self.N, numP),
            )
        if self.params.t == "uniform_real":
            return np.reshape(
                np.random.uniform(self.params.a, self.params.b, self.N * numP),
                (self.N, numP),
            )
        if self.params.t == "normal":
            return np.reshape(
                np.random.normal(self.params.mu, self.params.sigma, self.N * numP),
                (self.N, numP),
            )
        if self.params.t == "lognormal":
            return np.reshape(
                np.random.lognormal(self.params.mu, self.params.sigma, self.N * numP),
                (self.N, numP),
            )
        if self.params.t == "poisson":
            return np.reshape(
                np.random.poisson(self.params.lam, self.N * numP), (self.N, numP)
            )
        print("unknown distribution encountered: %s" % (self.params.t))
        exit()

    def produceOutputs(self):
        return np.asarray(
            [
                (self.fn(np.concatenate((xts, self.x_A))))
                for (xts) in np.column_stack((self.x_T, self.x_S))
            ]
        )

    # updates x_A, then re-generateates O samples automatically
    def update_xA(self, x_A):
        self.x_A = x_A
        self.O = self.produceOutputs()


class func:

    def __init__(self, fn, fn_name):
        self.fn = fn
        self.fn_name = fn_name


def write_json(
    numIterations, params, N, numT, numA, target_init_entropy, MI_data, fn: func
):

    data = {
        "name": fn.fn_name,
        "dist": params.getJSON(),
        "num_samples": N,
        "num_T": numT,
        "num_A": numA,
        "num_iterations": numIterations,
        "target_init_entropy": target_init_entropy,
        "awae_data": MI_data,
    }

    dir_path = "../output/" + str(fn.fn_name) + "/" + str(params.t) + "/"

    Path(dir_path).mkdir(parents=True, exist_ok=True)
    pstr = params.getJSON()["param_str"]
    fname = dir_path + pstr + ".json"
    with open(fname, "w") as json_file:
        json.dump(data, json_file)


def calculateTargetInitEntropy(dist_params):
    if isinstance(dist_params, uniform_real_params):
        return np.log2(float(dist_params.b) - float(dist_params.a - 1))

    if isinstance(dist_params, uniform_int_params):
        return np.log2(float(dist_params.b) - float(dist_params.a - 1) + 1.0)

    if isinstance(dist_params, normal_params):
        return 0.5 * np.log2(2.0 * np.pi * np.e * dist_params.sigma)

    if isinstance(dist_params, poisson_params):
        if dist_params.lam > 10:
            return 0.5 * np.log2(2.0 * np.pi * np.e * dist_params.lam)
        else:
            res = 0.0
            for i in range(0, 10 * dist_params.lam):
                tmp = poisson.pmf(i, dist_params.lam)
                accum += xlogy(tmp, tmp)

    if isinstance(dist_params, lognormal_params):
        return (
            dist_params.mu + 0.5 * np.log(2.0 * np.pi * np.e * dist_params.sigma)
        ) / np.log(2.0)

    print("unknown distribution encountered: %s" % (dist_params.t))
    exit()


def batch_experiment_uniform_int(fn: func):
    numIterations = 10
    maxNumSpecs = 10
    numT = 1
    numA = 1
    N = 30
    k = 5
    N_vals = np.array([4, 8, 16])
    x_A_min = 0
    for n in N_vals:
        spec_to_xA_to_MI = {}
        params = uniform_real_params(0, n)  # generates data from 0, 3-1
        target_init_entropy = calculateTargetInitEntropy(params)
        x_A_max = n
        for numSpecs in range(1, maxNumSpecs):
            xA_to_MI = {}
            for xA in range(x_A_min, x_A_max):
                MI = 0.0
                for i in range(numIterations):
                    s = sampleData(params, N, numT, numSpecs, [xA], fn)
                    MI += Mixed_KSG(s.x_T, s.O, k)
                xA_to_MI[xA] = MI / float(numIterations)
            xA_to_MI[numSpecs] = xA_to_MI
        write_json(
            numIterations, params, N, numT, numA, target_init_entropy, xA_to_MI, fn
        )
    # return


def main():

    params = uniform_real_params(0, 3)  # generates data from 0, 3-1
    print("target init entropy : ", calculateTargetInitEntropy(params))

    def fn(x):
        # return np.asarray([sum(x), sum(x)])
        return np.asarray([sum(x)])

    s = sampleData(params, 10, 1, 1, [1], np.sum)
    
    # print("Mixed KSG: I(X:Y) = ", Mixed_KSG(s.x_T, s.O, k=5))
    return


if __name__ == "__main__":
    if len(sys.argv) == 1:
        start_time = time.time()
        main()
        print(
            "finished computation at %s\nelapsed time: %s seconds "
            % (time.ctime(), time.time() - start_time)
        )
