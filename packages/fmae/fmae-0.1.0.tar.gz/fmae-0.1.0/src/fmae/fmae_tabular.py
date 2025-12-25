from fmae.fmae_base import FmaeBasicFls, FmaeBasicExplainer
from fmae.utilities import get_samples, get_weights
import numpy as np
import sklearn

"""
FMAE for tabular explanation task with MULTIPLE instances
FmaeFls: corresponding to 'FMAE:Initial FLS' in TABLE I in paper 
    where rule reduction and premise condensation are not enabled
FmaeExplainer: corresponding to 'FMAE:Initial explainer' in TABLE I in paper
    where rule reduction and premise condensation can be enabled
    
Please refer to the paper for more details:
"Hierarchical Fuzzy Model-Agnostic Explanation: Framework, Algorithms and Interface for XAI"
https://ieeexplore.ieee.org/document/10731553
Authors: Faliang Yin, Hak-Keung Lam, David Watson
"""


class FmaeFls:
    """
    Explaining on the provided batch of instances by the FLS of FMAE
    Parameters
    ----------
    model: closed box (black box) model to be explained
    instances: instances of interest to be explained
    mode: regression or classification
    num_sam: number of samples
    num_fuzzy_set: number of fuzzy set for each feature
    """
    def __init__(self, model, instances, mode='regression', num_sam=5000, num_fuzzy_set=3):
        self.model = model  # closed box (black box) model to be explained
        if str(type(instances)).endswith("pandas.core.frame.DataFrame'>"):  # transform to np data if input is pd data
            instances = instances.values
        self.mode = mode  # regression or classification
        self.scaler = sklearn.preprocessing.StandardScaler(with_mean=False)
        self.scaler.fit(instances)  # learn the distribution of data for sampling
        self.num_sam = num_sam  # number of samples
        self.kernel_width = 0.5 * np.sqrt(instances.shape[-1])  # kernel width for sampling

        self.num_fea = instances.shape[1]  # number of input features
        self.num_class = 1  # number of output (classes)
        self.num_fuzzy_set = num_fuzzy_set  # number of fuzzy set for each feature
        self.explainer = None  # basic TSK FLS model of FMAE
        self.score = None  # performance score for approximation ability of the FLS
        self.d_scores = []  # decision scores: simplify the consequent to the average output weighted by firing strength
        self.rule_bases = []  # rule base of each explainer

    def explain(self, instances):
        if str(type(instances)).endswith("pandas.core.frame.DataFrame'>"):  # transform to np array if input is pd data
            instances = instances.values

        fs_all, score = [], []
        self.rule_bases, self.d_scores = [], []
        for instance in instances:
            # for each instance, generate samples, labels and weights to train an FLS as explainer
            samples = get_samples(instance, self.num_sam, self.scaler)
            labels = self.model(samples)
            weights = get_weights(samples, self.scaler, kernel_width=self.kernel_width)
            if self.mode == 'regression':
                labels = np.expand_dims(labels, axis=1)
            else:
                self.num_class = labels.shape[1]
            self.explainer = FmaeBasicFls(self.num_fea, self.num_class, self.num_fuzzy_set, self.mode)
            self.explainer.fit(samples, labels, sample_weight=weights)
            fs = self.explainer.coef_  # generate feature salience explanations
            score.append(self.explainer.score(samples, labels, sample_weight=weights))
            fs_all.append(fs)

            self.rule_bases.append(self.explainer.rule_base)
            self.d_scores.append(self.explainer.d_score)

        self.score = np.average(score)
        return np.array(fs_all)


class FmaeExplainer:
    """
    Explaining on the provided batch of instances by the explainer of FMAE
    Parameters
    ----------
    model: closed box (black box) model to be explained
    instances: instances of interest to be explained
    mode: regression or classification
    num_sam: number of samples
    num_fuzzy_set: number of fuzzy set for each feature
    """
    def __init__(self, model, instances, mode='regression', num_sam=5000, num_fuzzy_set=3):

        self.model = model  # closed box (black box) model to be explained
        if str(type(instances)).endswith("pandas.core.frame.DataFrame'>"):  # transform to np data if input is pd data
            instances = instances.values
        self.mode = mode  # regression or classification
        self.scaler = sklearn.preprocessing.StandardScaler(with_mean=False)
        self.scaler.fit(instances)  # learn the distribution of data for sampling
        self.num_sam = num_sam  # number of samples
        self.kernel_width = 0.5 * np.sqrt(instances.shape[-1])  # kernel width for sampling

        self.num_fea = instances.shape[1]  # number of input features
        self.num_class = 1  # number of output (classes)
        self.num_fuzzy_set = num_fuzzy_set  # number of fuzzy set for each feature
        self.explainer = None  # basic explainer of FMAE
        self.score = None  # performance score for approximation ability of the FLS
        self.num_rule = 0  # number of rules
        self.d_scores = []  # decision scores: simplify the consequent to the average output weighted by firing strength
        self.rule_bases = []  # rule base of each explainer

    def explain(self, instances):
        if str(type(instances)).endswith("pandas.core.frame.DataFrame'>"):  # transform to np array if input is pd data
            instances = instances.values

        fs_all, score, num_rule = [], [], []
        self.rule_bases, self.d_scores = [], []
        for instance in instances:
            # for each instance, generate samples, labels and weights to train an FLS as explainer
            samples = get_samples(instance, self.num_sam, self.scaler)
            labels = self.model(samples)
            if self.mode == 'regression':
                labels = np.expand_dims(labels, axis=1)
            else:
                self.num_class = labels.shape[1]
            self.explainer = FmaeBasicExplainer(self.num_fea, self.num_class, self.num_fuzzy_set, mode=self.mode)
            weights = get_weights(samples, self.scaler, kernel_width=self.kernel_width)
            self.explainer.fit(samples, labels, sample_weight=weights)
            fs = self.explainer.coef_  # generate feature salience explanations
            fs_all.append(fs)
            score.append(self.explainer.score(samples, labels, sample_weight=weights))
            num_rule.append(self.explainer.num_rule)

            self.rule_bases.append(self.explainer.explainer.rule_base)
            self.d_scores.append(self.explainer.explainer.d_score)

        self.score = np.average(score)
        self.num_rule = np.average(num_rule)
        return np.array(fs_all)  # [num_instance, num_fea, num_class]
