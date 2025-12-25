import numpy as np

from treesimulator.generator import generate
from treesimulator.mtbd_models import Model
from treesimulator import STATE

p_p = 0.2 + np.random.random() * (0.75 - 0.2) # sampling prob in Paris between 0.2 and 0.75
p_c = np.random.random() * p_p # sampling prob in the Giverny between 0 and p_p

psi = 0.1
la = 0.2
mu = 0.05
model = Model(states=['Paris', 'Giverny'],
              transition_rates=[[0, mu], [5 * mu, 0]],
              transmission_rates=[[la, 0], [0, la]],
              removal_rates=[psi, psi], ps=[p_p, p_c])

for k, v in model.get_epidemiological_parameters().items():
    print(f'{k}: {v:g}')

print('\n Equillibrium frequencies: ')
frequencies = model.state_frequencies
print('pi_Paris: {:g}, pi_Giveny: {:g}'.format(*frequencies))

epidemic = generate([model], min_tips=200, max_tips=200, return_sampled_forest=True, return_stats=True)
n = len(epidemic.sampled_forest[0])
n_p = sum(1 for l in epidemic.sampled_forest[0] if getattr(l, STATE) == 'Paris')
print('pi_Paris_observed: {:g}, pi_Giveny_observed: {:g}'.format(n_p / n, (n - n_p) / n))

print('R_observed:', epidemic.R_e, 'd_observed:', epidemic.d, 'p_observed:', epidemic.p)

print('p_theoretical: {:g} vs p_observed: {:g}'.format(frequencies.dot(model.ps), p_p * n_p / n + p_c * (n - n_p) / n))

from bdct.bd_model import infer
from bdct.tree_manager import annotate_forest_with_time
annotate_forest_with_time(epidemic.sampled_forest)
vs, _ = infer(epidemic.sampled_forest, psi=psi, T=epidemic.T)