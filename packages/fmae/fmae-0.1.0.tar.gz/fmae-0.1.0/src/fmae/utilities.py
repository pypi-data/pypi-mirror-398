import numpy as np
from sklearn.linear_model import Ridge
import copy
from sklearn.metrics import mean_squared_error
from sklearn.utils import check_random_state
from functools import partial
from sklearn import model_selection
from sklearn.metrics.pairwise import pairwise_distances
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

"""
Library of the functions used in FMAE

Please refer to the paper for more details:
"Hierarchical Fuzzy Model-Agnostic Explanation: Framework, Algorithms and Interface for XAI"
https://ieeexplore.ieee.org/document/10731553
Authors: Faliang Yin, Hak-Keung Lam, David Watson
"""


def get_weights(scaled_data, scaler, kernel_width=0.5, flag=True):
    # get weights for each sample with the value inversely proportional to the distance from the original instance
    # this function derives from LIME [3]
    def kernel(d, kernel_width):
        return np.sqrt(np.exp(-(d ** 2) / kernel_width ** 2))
    if flag is True:
        scaled_data = (scaled_data - scaler.mean_) / scaler.scale_
        kernel_fn = partial(kernel, kernel_width=kernel_width)
        distances = pairwise_distances(
            scaled_data,
            scaled_data[0].reshape(1, -1),
            metric='euclidean'
        ).ravel()
        return kernel_fn(distances)
    else:
        return None


def get_samples(instance, num_samples, scaler, sample_around_instance=True, zoomer=1, standardization=False):
    # sampling around the instance to train the explainer
    num_cols = instance.shape[0]
    instance_sample = instance
    scale = scaler.scale_
    mean = scaler.mean_
    random_state = check_random_state(None)
    data = random_state.normal(
        0, 1, num_samples * num_cols).reshape(
        num_samples, num_cols)
    if sample_around_instance:
        data = data * scale * zoomer + instance_sample
    else:
        data = data * scale * zoomer + mean
    data[0] = instance.copy()
    if not standardization:
        return data
    else:
        return (data - scaler.mean_) / scaler.scale_


def calculate_error(samples, responses, explainer, weight=None):
    # calculate mse error of explainer
    prediction, fir_str_bar, membership_value = explainer.forward(samples)
    loss = mean_squared_error(responses, prediction, sample_weight=weight)
    return loss, fir_str_bar, membership_value


def fast_update_error(rem_rule_output, rem_fir_str_bar, responses, prediction, weight=None):
    # a fast update of the error when removing a rule
    removements = np.einsum('NC,N->NC', rem_rule_output, rem_fir_str_bar)
    prediction = prediction - removements
    loss = mean_squared_error(responses, prediction, sample_weight=weight)
    return loss


def tune_model(explainer, sam_train, sam_labels_train, sample_weight=None):
    # fine-tune the consequent parameters of FLS
    explainer.lse_con_param(sam_train, sam_labels_train, sample_weight)
    tra_loss, fir_str_bar, membership_value = calculate_error(sam_train, sam_labels_train, explainer, sample_weight)
    return explainer, tra_loss, fir_str_bar


def rule_reduction(explainer, fir_str_bar, sam_train, sam_labels_train, tra_loss, tra_loss0, tau_R,
                        log=False, weight=None):
    # simplify the rule base by removing redundant rules, please see Algorithm 2 in paper for more details
    # get the rule removing order list
    sort_id = np.argsort(np.mean(fir_str_bar, axis=0), axis=0)[::-1]  # from high to low
    explainer.con_param = explainer.con_param[:, sort_id, :]
    explainer.rule_base = explainer.rule_base[sort_id, :]
    fir_str_bar = fir_str_bar[:, sort_id]

    i_max = explainer.num_rule-1
    MR_his = [tra_loss]
    # calculate the initial prediction
    rule_output = explainer.consequent(sam_train)
    prediction = np.einsum('NRC,NR->NC', rule_output, fir_str_bar)
    avg_tra_loss, i = tra_loss, 0
    explainer_copy = copy.deepcopy(explainer)
    while i <= i_max:
        if i == i_max:
            # last rule is removed
            explainer_copy.reduce_to_linear()
            tra_loss, _, _ = calculate_error(sam_train, sam_labels_train, explainer_copy, weight)
        else:
            # remove the rule with less significance
            explainer_copy.remove_rule()
            rem_rule_output, rem_fir_str_bar = rule_output[:, -(i + 1), :], fir_str_bar[:, -(i + 1)]
            tra_loss = fast_update_error(rem_rule_output, rem_fir_str_bar, sam_labels_train, prediction, weight)
        MR_his.append(copy.deepcopy(tra_loss))
        avg_tra_loss = avg_win(MR_his, 10)
        if avg_tra_loss > tra_loss0 * tau_R:
            break
        else:
            explainer = copy.deepcopy(explainer_copy)
            i += 1
    if explainer.is_linear:
        print('all rules are removed')
    if log is True:
        return explainer, i
    else:
        return explainer


def premise_condensation(explainer, membership_value, sam_train, sam_labels_train, tra_loss, tra_loss0, tau_P,
                            log=False, weight=None):
    # Simplify the rules by removing redundant premises, please see Algorithm 2 in paper for more details
    MF_rem = np.mean(membership_value, axis=0)[0:-1, :]
    avg_tra_loss, MR_his, i = tra_loss, [tra_loss], 0
    explainer_copy = copy.deepcopy(explainer)
    i_max = explainer.num_fea * explainer.num_fuzzy_set - 1
    while i <= i_max:
        if i == i_max:
            # last premise is removed
            explainer_copy.reduce_to_linear()
        else:
            # remove the premise with less significance
            explainer_copy.remove_premise(MF_rem)
        tra_loss, _, _ = calculate_error(sam_train, sam_labels_train, explainer_copy, weight)
        MR_his.append(tra_loss)
        avg_tra_loss = avg_win(MR_his, 10)
        if avg_tra_loss > tra_loss0 * tau_P:
            break
        else:
            explainer = copy.deepcopy(explainer_copy)
            i += 1
    if explainer.is_linear:
        print('all premises are removed')
    if log is True:
        return explainer, i
    else:
        return explainer


def avg_win(MR_his, win_size):
    # calculate the average error of the last 'win_size' errors
    if len(MR_his) < win_size:
        avg_tra_acc = sum(MR_his) / len(MR_his)
    else:
        avg_tra_acc = sum(MR_his[-win_size:]) / win_size
    return avg_tra_acc


def load_dataset(name, mode='regression', num_features=5, fetch_index=-1, random_state=1, require_fea_idx=False):
    # an example function for data loading and feature selection
    if mode == 'classification':
        dataset = np.loadtxt('cla_data/{}.csv'.format(name), delimiter=",", skiprows=0)
    else:
        dataset = np.loadtxt('reg_data/{}.csv'.format(name), delimiter=",", skiprows=0)
    sam, label = dataset[:, :-1], dataset[:, -1].reshape(-1, 1)
    fea_idx = []
    if sam.shape[1] > num_features:
        fea_idx = forward_selection(sam, label, weights=None, num_features=5, random_state=random_state)
        sam = sam[:, fea_idx]
    train, test, labels_train, _ = \
        model_selection.train_test_split(sam, label, train_size=0.80, random_state=random_state)
    if require_fea_idx:
        return train, test, labels_train, fea_idx
    if fetch_index < 0:
        return train, test, labels_train
    else:
        return train, test, labels_train, sam[fetch_index]


def forward_selection(data, labels, weights, num_features, random_state):
    # iteratively adds features to the model to select the most important features
    # this function derives from LIME [3]
    clf = Ridge(alpha=0, fit_intercept=True, random_state=random_state)
    used_features = []
    for _ in range(min(num_features, data.shape[1])):
        max_ = -100000000
        best = 0
        for feature in range(data.shape[1]):
            if feature in used_features:
                continue
            clf.fit(data[:, used_features + [feature]], labels,
                    sample_weight=weights)
            score = clf.score(data[:, used_features + [feature]],
                              labels,
                              sample_weight=weights)
            if score > max_:
                best = feature
                max_ = score
        used_features.append(best)
    return np.array(used_features)


def plot_feature_salience(values, absolute_mode=False, title_note='', feature_names=None, save_path=None):
    # Draw a horizontal bar chart of feature salience
    values = np.asarray(values)
    n = values.shape[0]
    if feature_names is None:
        feature_names = np.array([f"x{i + 1}" for i in range(n)])

    if absolute_mode:  # Sort based on absolute value
        sort_key = np.abs(values)
    else:
        sort_key = values

    idx_sorted = np.argsort(sort_key)[::-1]
    values_sorted = values[idx_sorted]
    features_sorted = feature_names[idx_sorted]
    bar_lengths = np.abs(values_sorted) if absolute_mode else values_sorted

    COLOR_POS = "#6BAED6"  # light blue
    COLOR_NEG = "#FDAE6B"  # light orange
    colors = [COLOR_POS if v >= 0 else COLOR_NEG for v in values_sorted]

    plt.figure(figsize=(8, max(3, n * 0.4)))
    plt.barh(features_sorted, bar_lengths, color=colors)
    plt.grid(axis='x', linestyle='--', alpha=0.6)
    plt.xlabel("Salience Value" + (" (Absolute)" if absolute_mode else ""))
    plt.ylabel("Features")
    plt.title("Feature Salience (Sorted) " + title_note)
    plt.gca().invert_yaxis()

    pos_patch = mpatches.Patch(color=COLOR_POS, label='Positive Influence')
    neg_patch = mpatches.Patch(color=COLOR_NEG, label='Negative Influence')
    plt.legend(handles=[pos_patch, neg_patch], loc='lower right')

    plt.tight_layout()
    if save_path is not None:
        plt.savefig(save_path, dpi=300)
    else:
        plt.show()


def get_dscore(explainer, model_input):
    # decision scores: simplify the consequent to the average output weighted by firing strength
    model_output, fir_str_bar, _ = explainer.explainer.forward(model_input)
    fir_str_bar_bar = fir_str_bar / np.expand_dims(np.sum(fir_str_bar, 0), 0)
    d_score = np.einsum('MC,MR->CR', model_output, fir_str_bar_bar)
    return d_score


def print_rules(rule_base, num_fuzzy_set, d_score, save_path=None,
                feature_list=None, class_list=None, fuzzy_set_list=None,
                std=None, is_print=False):
    # format and save the IF-THEN rules
    if len(rule_base) == 0:
        print('No rules to show.')
        return
    rule_base = np.array(rule_base)
    if fuzzy_set_list is None:
        if num_fuzzy_set == 3:
            fuzzy_set_list = ['low', 'medium', 'high']
        elif num_fuzzy_set == 2:
            fuzzy_set_list = ['low', 'high']
        else:
            fuzzy_set_list = ['Level {}'.format(i) for i in range(1, num_fuzzy_set + 1)]
    if class_list is None:
        feature_list = ['S{}'.format(i) for i in range(1, rule_base.shape[1] + 1)]
    if class_list is None:
        class_list = ['C{}'.format(i) for i in range(1, d_score.shape[0] + 1)]

    rules = []

    for i in range(rule_base.shape[0]):
        rule = f'r{i + 1}: IF '

        for j, feature in enumerate(feature_list):
            if rule_base[i, j] != num_fuzzy_set:
                rule += f'{feature} is {fuzzy_set_list[rule_base[i, j]]}, '

        rule += 'THEN predicted as '

        for j, cls in enumerate(class_list):
            rule += f'{cls} with {d_score[j, i]:.3f}'
            if std is not None:
                rule += f'\u00B1{std[j, i]:.3f}'
            rule += ';' if j == len(class_list) - 1 else ', '

        rules.append(rule)

    # save to file if path is given
    if save_path is not None:
        with open(save_path, 'w') as f:
            for rule in rules:
                f.write(rule + '\n')

    # print to screen if required
    if is_print or save_path is None:
        for rule in rules:
            print(rule)