
import json
import sys
import irispie as ir

m = ir.Simultaneous.from_file(
    ["model-source/vanilla-rbc.model", "model-source/parameters.model"],
)

n = ir.Simultaneous.from_file(
    ["model-source/vanilla-rbc-stationarized.model", "model-source/parameters.model"],
    flat=True,
)

postprocessor = ir.Sequential.from_file(
    "model-source/vanilla-rbc-stationarized-postprocessor.model",
)

parameters = dict(
    alpha = 1.02**(1/4),
    beta = 0.95**(1/4),
    gamma = 0.40,
    delta = 0.05,
    rho = 0.8,
    std_shock_a = 0.9,
    std_shock_c = 0.9,
)

with open("parameters.json", "wt+", ) as fid:
    json.dump(parameters, fid, indent=4, )

m.assign(**parameters, )
n.assign(**parameters, )

m.assign(a = 1, k = 20, )
n.assign(kk = 20, )

info = m.steady(
    fix_levels=("a", ),
    flat=False,
)

chk, info = m.check_steady(when_fails="warning", )
info = m.solve()

n.steady()

chk, info = n.check_steady(when_fails="warning", )
info = n.solve()



start_sim = ir.qq(2020,1)
end_sim = ir.qq(2040,4)
sim_span = start_sim >> end_sim


dm = ir.Databox.steady(m, sim_span, deviation=True, )
dm0 = dm.copy()
dm0["shock_a"][start_sim] = 0.1
sm0, *_ = m.simulate(dm0, sim_span, deviation=True, )


dn = ir.Databox.steady(n, sim_span, deviation=True, )
dn0 = dn.copy()
dn0["shock_a"][start_sim] = 0.1
sn0, *_ = n.simulate(dn0, sim_span, deviation=True, )


dm = ir.Databox.steady(m, sim_span, )
dm1 = dm.copy()
dm1["shock_a"][start_sim] = 0.1
sm1, *_ = m.simulate(dm1, sim_span, )


dn = ir.Databox.steady(n, sim_span, )
dn1 = dn.copy()
dn1["shock_a"][start_sim] = 0.1
sn1, *_ = n.simulate(dn1, sim_span, )

sn1['a'] = ir.Series()
sn1['a'][start_sim-1] = sm1['a'][start_sim-1]


p = ir.PlanSimulate(postprocessor, start_sim-1>>end_sim, )
p.exogenize(start_sim-1, "a", when_data=True, )

sn1, *_ = postprocessor.simulate(
    sn1, start_sim-1>>end_sim,
    plan=p,
    when_nonfinite="silent",
    target_databox=sn1,
)


## Charts

ch = ir.Chartpack(
    span=start_sim-1 >> end_sim,
)

fig = ch.add_figure("Comparision of level and stationarized models", )

fig.add_charts((
    "Consumption: c",
    "Investment: i",
    "Interest rate: r",
    "Technology: a",
))

chart_db = sm1.copy()
chart_db.merge((sn1, ), action="hstack", )
ch.plot(chart_db, )


