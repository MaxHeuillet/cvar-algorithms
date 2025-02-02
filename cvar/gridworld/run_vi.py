from cvar.gridworld.core.constants import gamma
from cvar.gridworld.cliffwalker import *
from cvar.gridworld.core import cvar_computation
from cvar.gridworld.core.constants import gamma
from cvar.gridworld.core.runs import epoch
from cvar.gridworld.algorithms.value_iteration import value_iteration


def several_epochs(arg):
    np.random.seed()
    world, policy, nb_epochs = arg
    rewards = np.zeros(nb_epochs)

    for i in range(nb_epochs):
        S, A, R = epoch(world, policy)
        policy.reset()
        rewards[i] = np.sum(R)
        rewards[i] = np.dot(R, np.array([gamma ** i for i in range(len(R))]))

    return rewards


def policy_stats(world, policy, alpha, nb_epochs, verbose=True):
    import copy
    import multiprocessing as mp
    threads = 4

    with mp.Pool(threads) as p:
        rewards = p.map(several_epochs, [(world, copy.deepcopy(policy), int(nb_epochs/threads)) for _ in range(threads)])

    rewards = np.array(rewards).flatten()

    var, cvar = cvar_computation.var_cvar_from_samples(rewards, alpha)
    if verbose:
        print('----------------')
        print(policy.__name__)
        print('expected value=', np.mean(rewards))
        print('cvar_{}={}'.format(alpha, cvar))
        # print('var_{}={}'.format(alpha, var))

    return cvar, rewards


def exhaustive_stats(world, epochs, *args):
    V = value_iteration(world)

    alphas = np.array([1.0, 0.5, 0.25, 0.1, 0.05, 0.025, 0.01, 0.005, 0.001])

    cvars = np.zeros((len(args), len(alphas)))
    names = []

    for i, policy in enumerate(args):
        names.append(policy.__name__)
        for j, alpha in enumerate(alphas):
            pol = policy(V, alpha)

            cvars[i, j], _ = policy_stats(world, pol, alpha=alpha, nb_epochs=int(epochs), verbose=False)

            print('{}_{} done...'.format(pol.__name__, alpha))

    import pickle
    pickle.dump({'cvars': cvars, 'alphas': alphas, 'names': names}, open('data/stats.pkl', 'wb'))
    print(cvars)

    from cvar.gridworld.plots.other import plot_cvars
    plot_cvars()


if __name__ == '__main__':
    import pickle
    from cvar.gridworld.plots.grid import InteractivePlotMachine

    # np.random.seed(2)
    # # ============================= new config
    stoch = 0.1
    world = GridWorld(7, 10, random_action_p=stoch)
    V = value_iteration(world, max_iters=1000, eps_convergence=1e-5)
    pickle.dump((world, V), open('./results/vi_{}.pkl'.format(stoch), mode='wb'))

    # ============================= load
    world, V = pickle.load(open('./results/vi_{}.pkl'.format(stoch), 'rb'))

    for alpha in [1,0.04, 0.01]:
        # ============================= RUN
        img = np.array([V.V[ix].cvar_alpha(alpha) for ix in np.ndindex(V.V.shape)]).reshape(V.V.shape)
        pickle.dump(img, open('./results/map_{}_{}.pkl'.format(alpha, stoch), 'wb'))

        #Optimal path
        path = V.optimal_path(alpha)
        opt_path = [  [s[1] for s in path], [s[0] for s in path] ]
        pickle.dump(opt_path, open('./results/path_{}_{}.pkl'.format(alpha, stoch), 'wb'))

    
    # pm = InteractivePlotMachine(world, V, alpha=0.01, stochasticity = stoch)
    # # pm.show()

    # pm = InteractivePlotMachine(world, V, alpha=0.1, stochasticity = stoch)
    # # pm.show()

    # pm = InteractivePlotMachine(world, V, alpha=1, stochasticity = stoch)
    # # pm.show()

