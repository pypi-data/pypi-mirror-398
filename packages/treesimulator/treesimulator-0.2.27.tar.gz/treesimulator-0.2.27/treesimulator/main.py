from treesimulator import save_forest
from treesimulator.generator import generate
from treesimulator.mtbd_models import Model, BirthDeathModel, BirthDeathExposedInfectiousModel, \
    BirthDeathWithSuperSpreadingModel, BirthDeathExposedInfectiousWithSuperSpreadingModel, CTModel

# 1. BD, BD-CT(1) and BD-CT(1)-Skyline
## BD model
bd_model = BirthDeathModel(p=0.5, la=0.5, psi=0.25)
bd_tree = generate([bd_model], min_tips=200, max_tips=500).sampled_forest[0]
save_forest([bd_tree], 'BD_tree.nwk')
## Adding -CT to the model above
bdct_model = CTModel(model=bd_model, upsilon=0.2, X_C=10, X_p=1)
bdct_tree = generate([bdct_model], min_tips=200, max_tips=500, max_notified_contacts=1).sampled_forest[0]
save_forest([bdct_tree], 'BDCT_tree.nwk')
## BD-CT(1)-Skyline models
bdct_model_1 = CTModel(BirthDeathModel(p=0.5, la=0.5, psi=0.25),
                       upsilon=0, X_C=10, X_p=1)
bdct_model_2 = CTModel(BirthDeathModel(p=0.75, la=1, psi=0.25),
                       upsilon=0.2, X_C=10, X_p=1)
bdct_skyline_tree = generate([bdct_model_1, bdct_model_2], skyline_times=[3],
                             min_tips=200, max_tips=500, max_notified_contacts=1).sampled_forest[0]
save_forest([bdct_skyline_tree], 'BDCTSkyline_tree.nwk')

# BDEI, BDEI-CT(2) and BDEI-CT(2)-Skyline
## BDEI model
bdei_model = BirthDeathExposedInfectiousModel(p=0.5, mu=1, la=0.5, psi=0.25)
print(bdei_model.get_epidemiological_parameters())
bdei_tree = generate([bdei_model], min_tips=200, max_tips=500).sampled_forest[0]
save_forest([bdei_tree], 'BDEI_tree.nwk')
## Adding -CT to the model above
bdeict_model = CTModel(model=bdei_model, upsilon=0.2, X_C=10, X_p=1)
bdeict_tree = generate([bdeict_model], min_tips=200, max_tips=500, max_notified_contacts=2).sampled_forest[0]
save_forest([bdeict_tree], 'BDEICT_tree.nwk')
## BDEI-CT(2)-Skyline with three time intervals
bdeict_model_1 = CTModel(model=BirthDeathExposedInfectiousModel(p=0.2, mu=1, la=0.5, psi=0.25),
                         upsilon=0.2, X_C=10, X_p=1)
bdeict_model_2 = CTModel(model=BirthDeathExposedInfectiousModel(p=0.3, mu=1, la=0.5, psi=0.3),
                         upsilon=0.3, X_C=10, X_p=1)
bdeict_model_3 = CTModel(model=BirthDeathExposedInfectiousModel(p=0.5, mu=1, la=0.5, psi=0.5),
                         upsilon=0.3, X_C=20, X_p=1)
bdeict_skyline_tree = generate([bdeict_model_1, bdeict_model_2, bdeict_model_3], skyline_times=[2, 3],
                               min_tips=200, max_tips=500, max_notified_contacts=2).sampled_forest[0]
save_forest([bdeict_skyline_tree], 'BDEICTSkyline_tree.nwk')

# BDSS, BDSS-CT(3) and BDSS-CT(3)-Skyline
## BDSS model
bdss_model = BirthDeathWithSuperSpreadingModel(p=0.5, la_nn=0.1, la_ns=0.3, la_sn=0.5, la_ss=1.5, psi=0.25)
print(bdss_model.get_epidemiological_parameters())
bdss_tree = generate([bdss_model], min_tips=200, max_tips=500).sampled_forest[0]
save_forest([bdss_tree], 'BDSS_tree.nwk')
## Adding -CT to the model above
bdssct_model = CTModel(model=bdss_model, upsilon=0.2, X_C=10, X_p=1)
bdssct_tree = generate([bdssct_model], min_tips=200, max_tips=500, max_notified_contacts=3).sampled_forest[0]
save_forest([bdssct_tree], 'BDSSCT_tree.nwk')
## BDSS-CT(3)-Skyline with two time intervals, using the model above for the first interval
bdssct_model_2 = CTModel(
    model=BirthDeathWithSuperSpreadingModel(p=0.5, la_nn=0.1, la_ns=0.3, la_sn=1, la_ss=3, psi=0.25),
    upsilon=0.5, X_C=20, X_p=1)
bdssct_skyline_tree = generate([bdssct_model, bdssct_model_2], skyline_times=[2], min_tips=200, max_tips=500,
                               max_notified_contacts=3).sampled_forest[0]
save_forest([bdssct_skyline_tree], 'BDSSCTSkyline_tree.nwk')

# BDEISS, BDEISS-CT(1) and BDEISS-CT(1)-Skyline
## BDEISS model
bdeiss_model = BirthDeathExposedInfectiousWithSuperSpreadingModel(p=0.5, mu_n=0.1, mu_s=0.3, la_n=0.5, la_s=1.5,
                                                                  psi=0.25)
print(bdeiss_model.get_epidemiological_parameters())
bdeiss_tree = generate([bdeiss_model], min_tips=200, max_tips=500).sampled_forest[0]
save_forest([bdeiss_tree], 'BDEISS_tree.nwk')
## Adding -CT to the model above
bdeissct_model = CTModel(model=bdeiss_model, upsilon=0.2, X_C=10, X_p=1)
bdeissct_tree = generate([bdeissct_model], min_tips=200, max_tips=500, max_notified_contacts=1).sampled_forest[0]
save_forest([bdeissct_tree], 'BDEISSCT_tree.nwk')
## BDEISS-CT(1)-Skyline with two time intervals, using the model above for the first interval
bdeissct_model_2 = CTModel(
    model=BirthDeathExposedInfectiousWithSuperSpreadingModel(p=0.2, mu_n=0.1, mu_s=0.3, la_n=0.5, la_s=1.5, psi=0.25),
    upsilon=0.5, X_C=20, X_p=1)
bdeissct_skyline_tree = generate([bdeissct_model, bdeissct_model_2], skyline_times=[2], min_tips=200,
                                 max_tips=500, max_notified_contacts=1).sampled_forest[0]
save_forest([bdeissct_skyline_tree], 'BDEISSCTSkyline_tree.nwk')

# MTBD, MTBD-CT(1) and MTBD-CT(1)-Skyline
## MTBD model with two states: A and B
mtbd_model = Model(states=['A', 'B'], transition_rates=[[0, 0.6], [0.7, 0]],
                   transmission_rates=[[0.1, 0.2], [0.3, 0.4]],
                   removal_rates=[0.05, 0.08], ps=[0.15, 0.65])
mtbd_tree = generate([mtbd_model], min_tips=200, max_tips=500).sampled_forest[0]
save_forest([mtbd_tree], 'MTBD_tree.nwk')
## Adding -CT to the model above
mtbdct_model = CTModel(model=mtbd_model, upsilon=0.2, X_C=10, X_p=1)
mtbdct_tree = generate([mtbdct_model], min_tips=200, max_tips=500, max_notified_contacts=1).sampled_forest[0]
save_forest([mtbdct_tree], 'MTBDCT_tree.nwk')
## MTBD-CT(1)-Skyline with two time intervals, using the model above for the first interval
mtbdct_model_2 = CTModel(model=Model(states=['A', 'B'], transition_rates=[[0, 1.6], [1.7, 0]],
                                     transmission_rates=[[1.1, 1.2], [1.3, 1.4]],
                                     removal_rates=[1.05, 1.08], ps=[0.1, 0.6]),
                         upsilon=0.4, X_C=20, X_p=1)
mtbdct_skyline_tree = generate([mtbdct_model, mtbdct_model_2], skyline_times=[8],
                               min_tips=200, max_tips=500, max_notified_contacts=1).sampled_forest[0]
save_forest([mtbdct_skyline_tree], 'MTBDCTSkyline_tree.nwk')
