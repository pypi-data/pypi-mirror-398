'''
This module contains the classes functions to construct the graph from the
queried individual and similar individuals
'''

import pandas as pd


class Argument:
    '''
    Class for arguments in our graph
    '''
    def __init__(self, attr_name, attr_value):
        self.attr_name = attr_name
        self.attr_value = attr_value
        self.id = attr_name + str(attr_value)
        self.current_w = 1 # current weight is initial weight of argument at the start

    def get_id(self):
        return self.id

    def get_attr_name(self):
        return self.attr_name

    def get_attr_value(self):
        return self.attr_value

    def get_current_w(self):
        return self.current_w

    def set_current_w(self, new_w):
        self.current_w = new_w

    def __str__(self):
        """
        @return: string representation of argument
        """
        return self.attr_name + "=" + str(self.attr_value)

    def __repr__(self):
        return self.attr_name + "=" + str(self.attr_value)


class Graph:
    '''
    Class for our constructed argumentation graph used to identify the reasons for bias
    '''
    def __init__(self):
        # dictionary of arguments -> weight of argument
        self.args = []
        # dictionary of (attacker, attacked) -> strength of attack
        self.attacks = dict()
        # initial weight of arguments
        self.initial_weight = 1

    def get_initial_weight(self):
        return self.initial_weight

    def add_arg(self, name, value):
        arg = Argument(name, value)
        self.args.append(arg)

    def get_arg(self, id):
        for a in self.args:
            if a.get_id() == id:
                return a

    def get_args(self):
        return self.args

    def add_att(self, attacker, attacked):
        if (attacker, attacked) not in self.attacks:
            self.attacks[(attacker, attacked)] = 1
        else:
            self.attacks[(attacker, attacked)] += 1

    def get_attacks(self):
        return self.attacks

    def set_attacks(self, attacks):
        self.attacks = attacks

    def get_attackers(self):
        """
        @return: a list of all arguments and a list of corresponding attackers of those arguments
        """
        args = self.get_args()
        attacks = self.get_attacks()
        arguments = []
        attackers = []

        for arg in args:
            temp = []
            for att in attacks.keys():
                if att[1] == arg:
                    temp.append(att[0])
            attackers.append(temp)
            arguments.append(arg)

        return arguments, attackers

    def update_arg_strength(self, arg, weight):
        arg.set_current_w(weight)

    def print_args(self):
        for a in self.args:
            print(a, "with weight: ", a.get_current_w())
        print()

    def print_attacks(self):
        for a in self.attacks.keys():
            print(str(a[0]), "attacks", str(a[1]), " with strength ", self.attacks[a])


def get_attr_values(data, attr_name):
    """
    Get all the values of an attribute
    @param data: similar individual and queried individuals
    @param attr_name: attribute to find values of
    @return: list of all unique values of attribute
    """
    return data[attr_name].unique()


def create_arguments(data):
    """
    Create arguments for each attribute value in the global graph object
    """
    data = data.iloc[:, :-1]
    for d in data:
        attr_values = get_attr_values(data, d)
        for v in attr_values:
            graph.add_arg(d, v)


def add_attacks(data):
    """
    Add attacks to the global graph object based on the similar individuals and queried individual
    @param data: similar individual and queried individuals
    """
    individual = data.iloc[0, :]
    neighbours = data.iloc[1:, :]
    data = data.iloc[:, :-1]

    for i in range(len(neighbours)):
        n = neighbours.iloc[i, :]
        if n[-1:].values != individual[-1:].values:
            for d in data:
                n_data = n[:-1]
                ind_data = individual[:-1]
                if n_data[d] != ind_data[d]:
                    for column in n_data.index:
                        value = n_data[column]
                        attacker = graph.get_arg(column + str(value))
                        attacked = graph.get_arg(d + str(ind_data[d]))
                        graph.add_att(attacker, attacked)


def attack_strengths(k):
    """
    Calculates the attack strengths of the global graph object
    @param k: number of similar individuals
    """
    attacks = graph.get_attacks()
    norm_attacks = dict()
    for a in attacks.keys():
        norm_attacks[a] = attacks.get(a) / k
    graph.set_attacks(norm_attacks)


def incoming_weight(attacker_weight: float, attack_strength: float) -> float:
    """
    Calculates the incoming weight of a single attacker to an argument
    @param attacker_weight: weight of a single incoming attacker (in interval [0,1])
    @param attack_strength: strength of the attack (in interval [0,1])
    @return: the weight of the attacker multiplied by the strength of the attack (in interval [0,1])
    """
    return attacker_weight * attack_strength


def aggregate(arg: object) -> float:
    """
    Calculates the aggregation of the incoming weights of attackers to an argument
    @param arg: the argument to calculate the aggregation of
    @return: the sum of all incoming weights to the argument multiplied by their respective attack strengths
    """
    arguments, attackers = graph.get_attackers()
    attack_strengths = graph.get_attacks()
    total = 0
    arg_index = arguments.index(arg)
    for a in attackers[arg_index]:
        total = total + incoming_weight(a.get_current_w(), attack_strengths.get((a, arg)))
    return total


def influence(arg: object) -> float:
    """
    Calculates the influence on an argument at a point in time, using the
    Weighted h-categorizer semantics (Hbs), Amgoud et al. 2022
    @param arg: the argument to update the weight of
    @return: the change in weight of the argument at a point in time
    """
    w = graph.get_initial_weight()
    update = w / (1 + (aggregate(arg)))
    return update


def weight_diffs(new_weights, current_weights):
    """
    Checks if the difference in weights between the current and new weights is greater than epsilon
    @param new_weights: weights calculated for the next iteration
    @param current_weights: weights calculated for the current iteration
    @return: True if the difference in an argument weight is greater than epsilon (not converged),
    False otherwise (converged)
    """
    epsilon = 0.01
    for i in range(len(new_weights)):
        if abs(new_weights[i] - current_weights[i]) > epsilon:
            return True
    return False


def calculate_final_weights():
    """
    Calculates the final weights of the arguments in the global graph object
    by iterating through the influence function until convergence
    """
    args = graph.get_args()
    current_weights = []
    for arg in args:
        arg.set_current_w(graph.get_initial_weight())
        current_weights.append(arg.get_current_w())

    not_converged = True
    # while the difference in changes is greater than epsilon (have not reached convergence threshold)
    while not_converged:
        diff_changes = []
        new_weights = []
        # for each argument, calculate the new weight and store
        for arg in args:
            new_weight = influence(arg)
            new_weights.append(new_weight)
        for i in range(len(new_weights)):
            graph.update_arg_strength(args[i], new_weights[i])

        # if any difference in weight changes is greater than epsilon, all arguments not converged
        not_converged = weight_diffs(new_weights, current_weights)

        # set current weights to new weights
        current_weights = new_weights


def display():
    """
    Prints the arguments and their weights in the global graph object
    Used for testing purposes
    """
    graph.print_args()
    print()
    graph.print_attacks()
    print()
    graph.print_args()
    print()


def get_final_weights():
    """
    Returns the final weights of the arguments in the global graph object
    @return: dictionary of arguments and their final weights
    """
    final_weights = {}
    args = graph.get_args()
    for a in args:
        # add argument and its weight to dictionary
        final_weights[str(a)] = round(a.get_current_w(), 2)
    return final_weights


def get_weakest_args(final_weights):
    """
    Returns the weakest arguments in the global graph object, or consistent
    if all arguments have a final strength of 1
    @param final_weights:
    @return: weakest arguments, or consistent
    """
    weakest_args = []
    # find the weakest arguments
    min_weight = min(final_weights.values())
    if min_weight != 1:
        for arg in final_weights.keys():
            if final_weights[arg] == min_weight:
                weakest_args.append(arg)
        return weakest_args
    else:
        return ["consistent"]


def construct_graph(df):
    """
    Constructs the graph using following the steps in the submitted paper
    @param filename: df containing the individuals (top row is queried individual, rest are similar individuals)
    @return: final weights of all arguments, the weakest arguments
    """
    inds = df

    # initialise graph
    global graph
    graph = Graph()

    # create arguments using Definition 2
    create_arguments(inds)

    # add attacks using Definition 4
    add_attacks(inds)

    # set attack strengths using Definition 4
    attack_strengths(len(inds) - 1)

    # calculate the final weights using Hbs semantics defined in Equation 1 and 2
    calculate_final_weights()

    # display the graph details (optional for testing)
    # display()

    # get final weights of arguments to 2dp
    final_weights = get_final_weights()

    # get the weakest arguments of the graph
    weakest_args = get_weakest_args(final_weights)

    return final_weights, weakest_args
