import logging

import numpy as np

from generator import generate
from mtbd_models import BirthDeathExposedInfectiousWithSuperSpreadingModel, CTModel

# logging.getLogger().handlers = []
# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

models = []
la = 2
X_S = 2
f_S = 0.3
mu = 1.5
model = BirthDeathExposedInfectiousWithSuperSpreadingModel(p=0.25,
                                                           mu_n=mu * (1 - f_S), mu_s=mu * f_S,
                                                           la_n=la, la_s=X_S * la,
                                                           psi=1,
                                                           n_recipients=[1, 1, 1])
model = CTModel(model=model, upsilon=0.2, X_C=50, X_p=1)
models.append(model)

R_e, p, d = 8/3, 0.25, 1/1.5 + 1
epidemic = generate(models,
                    min_tips=10000, max_tips=10000,
                    max_notified_contacts=1000, notify_at_removal=True,
                    return_stats=True)
R_e, p, d = epidemic.R_e, epidemic.p, epidemic.d

R_es, ds, ps = [], [], []
for _ in range(100):
    epidemic = generate(models,
                        min_tips=250, max_tips=250,
                        max_notified_contacts=1000, notify_at_removal=True,
                        return_stats=True)
    R_es.append(epidemic.R_e)
    ds.append(epidemic.R_e / la / (1 + (X_S - 1) * f_S) + 1 / mu)
    ps.append(epidemic.p)

print(R_e, 'vs', np.mean(R_es), np.quantile(R_es, [0.025, 0.5, 0.975]))
print(d, 'vs', np.mean(ds), np.quantile(ds, [0.025, 0.5, 0.975]))
print(p, 'vs', np.mean(ps), np.quantile(ps, [0.025, 0.5, 0.975]))