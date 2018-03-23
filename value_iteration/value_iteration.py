from cliffwalker import *
from util.constants import *
from util import cvar_computation
import numpy as np
import copy

# use LP when computing CVaRs
# TAMAR_LP = True
TAMAR_LP = False

WASSERSTEIN = False
# WASSERSTEIN = True


class ValueFunction:

    def __init__(self, world):
        self.world = world

        self.V = np.empty((world.height, world.width), dtype=object)
        for ix in np.ndindex(self.V.shape):
            self.V[ix] = MarkovState()

    def update(self, y, x, deep=True):

        yc_a = []
        v_a = []

        for a in self.world.ACTIONS:
            t = list(self.transitions(y, x, a))

            if TAMAR_LP:
                v, yc = self.V[y, x].compute_cvar_by_lp([t_.prob for t_ in t], self.transition_ycs(y, x, a))
            elif WASSERSTEIN:
                v, yc = self.V[y, x].compute_wasserstein([t_.prob for t_ in t], self.transition_vars(y, x, a))
            else:
                v, yc = self.V[y, x].compute_cvar_by_sort([t_.prob for t_ in t], self.transition_vars(y, x, a),
                                                          [self.V[tr.state.y, tr.state.x].atoms for tr in t])
            yc_a.append(yc)
            v_a.append(v)

        yc_a = np.array(yc_a)
        v_a = np.array(v_a)

        best_args = np.argmax(yc_a, axis=0)

        self.V[y, x].yC = np.array([yc_a[best_args[i], i] for i in range(len(self.V[y, x].yC))])

        self.V[y, x].c_0 = max([cvar_computation.v_0_from_transitions(self.V, list(self.transitions(y, x, a)), gamma)
                                for a in self.world.ACTIONS])

        # check for error bound
        eps = 1.
        c_0 = v_a[best_args[0], 0]
        if c_0 - self.V[y, x].c_0 > eps:
            # if deep and self.V[y, x].nb_atoms < 100:
            if deep:
                self.V[y, x].increase_precision(eps)
                print('PRECISION:', self.V[y, x].nb_atoms, (y, x))
                self.update(y, x, False)

    def next_action(self, y, x, alpha):
        assert alpha != 0

        best = (-1e6, 0, 0)
        for a in self.world.ACTIONS:

            if TAMAR_LP:
                cv, xis = self.single_yc_xis_lp(y, x, a, alpha)
            else:
                _, cv, xis = self.single_var_yc_xis(y, x, a, alpha)

            if cv > best[0]:
                best = (cv, xis, a)

        _, xis, a = best
        print(xis)
        return a, xis

    def single_yc_xis_lp(self, y, x, a, alpha):
        transition_p = [t.prob for t in self.transitions(y, x, a)]
        atom_values = [self.V[t.state.y, t.state.x].atoms for t in self.transitions(y, x, a)]
        yc = self.transition_ycs(y, x, a)
        return cvar_computation.single_yc_lp_from_t(transition_p, atom_values, yc, alpha, xis=True)

    def single_var_yc_xis(self, y, x, a, alpha):
        """
        Compute VaR, CVaR and xi values in O(nlogn)
        """

        transitions = list(self.transitions(y, x, a))
        var_values = self.transition_vars(y, x, a)
        transition_p = [t.prob for t in transitions]
        t_atoms = [self.V[t.state.y, t.state.x].atoms for t in transitions]
        return cvar_computation.single_var_yc_xis_from_t(transition_p, t_atoms, var_values, alpha)

    def y_var(self, y, x, a, var):
        """ E[(Z-var)^-] + yvar"""

        transitions = list(self.transitions(y, x, a))
        var_values = self.transition_vars(y, x, a)

        info = extract_distribution(transitions, var_values, [self.V[tr.state.y, tr.state.x].atom_p for tr in transitions])

        yv = 0.
        p = 0
        for p_, _, v_ in info:
            if v_ >= var:  # TODO: solve for discrete distributions
                break
            else:
                yv += p_ * v_
            p += p_

        return p, yv

    def transitions(self, y, x, a):
        for t in self.world.transitions(State(y, x))[a]:
            yield t

    def transition_vars(self, y, x, a):
        return np.array([t.reward + gamma * self.V[t.state.y, t.state.x].var for t in self.transitions(y, x, a)])

    def transition_ycs(self, y, x, a):
        return np.array([t.reward*self.V[t.state.y, t.state.x].atoms[1:] + gamma * self.V[t.state.y, t.state.x].yC for t in self.transitions(y, x, a)])

    def optimal_path(self, alpha):
        """ Optimal deterministic path. """
        from policy_improvement.policies import TamarPolicy, TamarVarBasedPolicy
        policy = TamarPolicy(self, alpha)
        # policy = TamarVarBasedPolicy(self, alpha)
        s = self.world.initial_state
        states = [s]
        t = Transition(s, 0, 0)
        while s not in world.goal_states:
            a = policy.next_action(t)
            t = max(self.world.transitions(s)[a], key=lambda t: t.prob)
            s = t.state
            if s in states:
                print(s, world.ACTION_NAMES[a], end='')
                raise ZeroDivisionError()
            states.append(s)
            print(s, world.ACTION_NAMES[a])
        return states


def extract_distribution(transitions, var_values, atom_ps):
    """

    :param transitions:
    :param var_values:
    :param atom_p:
    :return: sorted list of tuples (probability, index, var)
    """
    info = []
    for i_t, t in enumerate(transitions):
        for i_v, v, p_ in zip(range(len(var_values[i_t])), var_values[i_t], atom_ps[i_t]):
            info.append((p_ * t.prob, i_t, v))

    info.sort(key=lambda x: x[-1])
    return info


class MarkovState:

    def __init__(self):
        self.nb_atoms = NB_ATOMS  # TODO: make property
        self.yC = np.zeros(NB_ATOMS)
        self.atoms = spaced_atoms(self.nb_atoms, SPACING, LOG)    # e.g. [0, 0.25, 0.5, 1]
        self.atom_p = self.atoms[1:] - self.atoms[:-1]  # [0.25, 0.25, 0.5]

        self.c_0 = 0  # separate estimate for CVaR_0

    def plot(self, show=True, figax=None):
        import matplotlib.pyplot as plt
        if figax is None:
            fig, ax = plt.subplots(1, 2)
        else:
            fig, ax = figax

        # var
        ax[0].step(self.atoms, list(self.var) + [self.var[-1]], 'o-', where='post')

        # yV
        ax[1].plot(self.atoms, np.insert(self.yC, 0, 0), 'o-')
        if show:
            plt.show()

    @property
    def var(self):
        return cvar_computation.yc_to_var(self.atoms, self.yC)

    def increase_precision(self, eps):
        """ Bound error by adding atoms. Follows the adaptive procedure from RSRDM. """
        new_atoms = []
        v_0 = self.yC[0]
        y = (eps*self.atom_p[0])/(np.abs(v_0-self.c_0))
        if y < 1e-15:
            print('SMALL')

        while y < self.atom_p[0]:
            new_atoms.append(y)
            y *= SPACING

        self.atoms = np.hstack((np.array([0]), new_atoms, self.atoms[1:]))
        self.atom_p = self.atoms[1:] - self.atoms[:-1]

        self.yC = np.hstack((v_0*np.array(new_atoms), self.yC))

        self.nb_atoms = len(self.yC)

    def cvar_alpha(self, alpha):
        return cvar_computation.single_alpha_to_cvar(self.atom_p, self.var, alpha)

    def expected_value(self):
        return np.dot(self.atom_p, self.var)

    def compute_cvar_by_sort(self, transition_p, var_values, t_atoms):
        return cvar_computation.v_yc_from_t(self.atoms, transition_p, var_values, t_atoms)

    def compute_wasserstein(self, transition_p, var_values):
        raise NotImplementedError("Waiting for transfer from lp_compare and fix.")

    def compute_cvar_by_lp(self, transition_p, var_values):
        return cvar_computation.v_yc_from_t_lp(self.atoms, transition_p, var_values)


def value_update(world, V, id=0, figax=None):

    V_ = copy.deepcopy(V)
    for s in world.states():
        V_.update(s.y, s.x)
        # if id >=28 and s.y == 2 and s.x == 0:
        #     import matplotlib.pyplot as plt
        #     plt.ion()
        #     V.V[2, 0].plot(show=False, figax=figax)
        #     if id > 43:
        #         plt.pause(100)

    return V_


def converged(V, V_, world):
    eps = 1e-6
    max_val = eps
    max_state = None
    for s in world.states():
        # dist = np.max(np.abs(V.V[s.y, s.x].var-V_.V[s.y, s.x].var))
        cvars = np.array([V.V[s.y, s.x].cvar_alpha(alpha) for alpha in V.V[s.y, s.x].atoms[1:]])
        cvars_ = np.array([V_.V[s.y, s.x].cvar_alpha(alpha) for alpha in V_.V[s.y, s.x].atoms[1:]])
        if cvars.shape != cvars_.shape:
            return False
        dist = np.max(np.abs(cvars - cvars_))
        if dist > max_val:
            max_state = s
            max_val = dist
    if max_val > eps:
        print(max_val, max_state)
        return False
    return True


def value_iteration(world, max_iters=1e3):
    V = ValueFunction(world)
    i = 0
    figax=None
    while True:
        if i == 28:
            import matplotlib.pyplot as plt
            figax = plt.subplots(1, 2)
        V_ = value_update(world, V, i, figax)
        # if i % 10 == 0:
        #     V_.V[2, 3].plot()
        if (converged(V, V_, world) and i != 0) or i > max_iters:
            print("value fully learned after %d iterations" % (i,))
            break
        V = V_
        i += 1

        print('Value iteration:', i)

    return V

if __name__ == '__main__':
    import pickle
    from plots.grid_plot_machine import InteractivePlotMachine
    # world = GridWorld(10, 15, random_action_p=0.05)
    world = GridWorld(50, 60, random_action_p=.05)  # Tamar

    print('ATOMS:', spaced_atoms(NB_ATOMS, SPACING, LOG))

    # =============== VI setup
    V = value_iteration(world, max_iters=1000)
    pickle.dump(V, open('../files/vi.pkl', mode='wb'))
    # V = pickle.load(open('../files/vi.pkl', 'rb'))

    for alpha in np.arange(0.05, 1, 0.05):
        print(alpha)
        pm = InteractivePlotMachine(world, V, alpha=alpha)
        pm.show()

