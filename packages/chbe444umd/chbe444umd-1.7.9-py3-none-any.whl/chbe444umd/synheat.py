# Heat Integration: Heat Exchanger Network Synthesis
# Translated from GAMS for CHBE444: Design I, University of Maryland
# (C) Ganesh Sriram, 2025, originally written in MATLAB in 2017
# Licensed under GNU Public License 3.0
# Author contact info: gsriram@umd.edu

# This model designs a heat exchanger network operating at minimal
# annual cost and satisfying specified heating and cooling requirements.
# The superstructure consists of k stages and up to 10 possible exchangers.
# The original model was written based on this article:
#     Yee, T F, and Grossmann, I E, Simultaneous Optimization of Models for
#     Heat Integration: Heat Exchanger Network Synthesis. Computers and
#     Chemical Engineering 14, 10 (1990), 1151-1184.
# The GAMS version of this model is available in the GAMS model library:
#     https://www.gams.com/47/gamslib_ml/libhtml/gamslib_synheat.html

# Keywords
#    heat exchanger network
#    mixed integer nonlinear programming
#    optimization
#    chemical engineering design

import pandas as pd
import gamspy as gams


def synheat(streams, DT_min=10, n_stages=3, stages=None,
            T_hot_util_in=450, T_hot_util_out=450,
            T_cold_util_in=20, T_cold_util_out=20,
            hot_util_cost=100, cold_util_cost=100,
            exchanger_fixed_charge=5500, area_cost_coeff_exchanger=150,
            area_cost_coeff_heater=150, area_cost_coeff_cooler=150,
            cost_exponent_exchanger=0,
            hot_util_film_coeff=1, cold_util_film_coeff=1,
            decimals=2, disp=True):
    """
    Perform heat exchanger network (HEN) synthesis by Yee and Grossmann's
        transshipment method.

    Notes:
        This model designs a heat exchanger network operating at minimal
            annual cost and satisfying specified heating and cooling
            requirements. The superstructure consists of k stages and up
            to 10 possible exchangers.

        The original model was written based on this article:
            Yee, T F, and Grossmann, I E, Simultaneous Optimization of
            Models for Heat Integration: Heat Exchanger Network Synthesis.
            Computers and Chemical Engineering 14, 10 (1990), 1151-1184.

        The GAMS version of this model is available in the GAMS model
            library:
            https://www.gams.com/47/gamslib_ml/libhtml/gamslib_synheat.html

    Example:
        synheat([H1, H2, C1, C2], DT_min=20, decimals=2)

    Args:
        streams: A list of previously created Stream objects.
        DT_min: Minimum approach temperature. Defaults to 10 °C.
        n_stages: Number of stages ``k`` in the superstructure.
        stages: Same as ``n_stages``.
        T_hot_util_in: Hot utility inlet temperature. Defaults to 450 °C.
        T_hot_util_out: Hot utility outlet temperature. Defaults to 450 °C.
        T_cold_util_in: Cold utility inlet temperature Defaults to 20 °C.
        T_cold_util_out Cold utility outlet temperature. Defaults to 20 °C.
        hot_util_cost: Relative cost of hot utility. Defaults to 100 units.
        cold_util_cost: Relative cost of cold utility. Defaults to 100 units.
        exchanger_fixed_charge: Relative fixed price of exchanger. Defaults
            to 5500 units, but could be different in practice.
        area_cost_coeff_exchanger: Area cost coefficient for exchangers.
            Defaults to 150 units.
        area_cost_coeff_heater: Area cost coefficient for heaters.
            Defaults to 150 units.
        area_cost_coeff_cooler: Area cost coefficient for coolers.
            Defaults to 150 units.
        cost_exponent_exchanger: Cost exponent for exchangers.
            Defaults to 0, but could be different in practice.
        hot_util_film_coeff: Individual film heat transfer coefficient
            for hot utility. Defaults to 1.0 J/(s m^2 °C)
        cold_util_film_coeff=1: Individual film heat transfer coefficient
            for cold utility. Defaults to 1.0 J/(s m^2 °C).
        decimals: Number of decimals in output. Defaults to 2.

    Returns:
        A HENDesign instance containing number of stages, streams, hot and
            cold stream temperatures, and heat exchanged between streams.
    """

    if n_stages is not None and stages is not None:
        print(
            f"Both n_stages (= {n_stages}) and stages (= {stages}) " +
            "are specified; using n_stages"
        )
    elif n_stages is None:
        n_stages = stages
    elif n_stages is None and stages is None:
        print('At least one of n_stages or stages must be specified')
    else:
        pass

    hot_streams = [stream for stream in streams if stream.kind == 'hot']
    cold_streams = [stream for stream in streams if stream.kind == 'cold']
    hot_range = [n for n in range(1, len(hot_streams) + 1)]
    cold_range = [n for n in range(1, len(cold_streams) + 1)]

    m = gams.Container()

    # Sets for streams
    i = gams.Set(m, name='i', records=hot_range, description='hot streams')
    j = gams.Set(m, name='j', records=cold_range, description='cold streams')

    # Sets for stages
    k = gams.Set(
        m, name='k', records=range(1, n_stages + 1),
        description='Temperature locations')
    st = gams.Set(m, 'st', domain=k)  # up to second-last
    firstK = gams.Set(
        m, name='firstK', domain=k, is_singleton=True,
        description='First temperature location'
    )
    lastK = gams.Set(
        m, name='lastK', domain=k, is_singleton=True,
        description='Last temperature location',
    )
    st[k].where[~k.last] = True
    firstK[k].where[k.first] = True
    lastK[k].where[k.last] = True

    # Parameters
    fh = gams.Parameter(
        m, name='fh', domain=i,
        description='Hot stream heat capacity'
    )
    fc = gams.Parameter(
        m, name='fc', domain=j,
        description='Cold stream heat capacity'
    )
    thin = gams.Parameter(
        m, name='thin', domain=i,
        description='Hot stream source temperature')
    thout = gams.Parameter(
        m, name='thout', domain=i,
        description='Hot stream target temperature'
    )
    tcin = gams.Parameter(
        m, name='tcin', domain=j,
        description='Cold stream source temperature'
    )
    tcout = gams.Parameter(
        m, name='tcout', domain=j,
        description='Cold stream target temperature'
    )
    ech = gams.Parameter(
        m, name='ech', domain=i,
        description='Enthalpy content of hot stream i'
    )
    ecc = gams.Parameter(
        m, name='ecc', domain=j,
        description='Enthalpy content of cold stream j'
    )
    hh = gams.Parameter(
        m, name='hh', domain=i,
        description='Individual film coefficient of hot stream i'
    )
    hc = gams.Parameter(
        m, name='hc', domain=j,
        description='Individual film coefficient of cold stream j'
    )
    hucost = gams.Parameter(
        m, name='hucost', domain=[],
        description='Cost of hot utility'
    )
    cucost = gams.Parameter(
        m, name='cucost', domain=[],
        description='Cost of cold utility'
    )
    unitc = gams.Parameter(
        m, name='unitc', domain=[],
        description='Fixed charge for exchanger'
    )
    acoeff = gams.Parameter(
        m, name='acoeff', domain=[],
        description='Area cost coefficient for exchangers'
    )
    hucoeff = gams.Parameter(
        m, name='hucoeff', domain=[],
        description='Area cost coefficient for heaters'
    )
    cucoeff = gams.Parameter(
        m, name='cucoeff', domain=[],
        description='Area cost coefficient for coolers'
    )
    aexp = gams.Parameter(
        m, name='aexp', domain=[],
        description='Cost exponent for exchangers'
    )
    hhu = gams.Parameter(
        m, name='hhu', domain=[],
        description='Individual film coefficient of hot utility'
    )
    hcu = gams.Parameter(
        m, name='ccu', domain=[],
        description='Individual film coefficient of cold utility'
    )
    thuin = gams.Parameter(
        m, name='thuin', domain=[],
        description='Inlet temperature of hot utility'
    )
    thuout = gams.Parameter(
        m, name='thuout', domain=[],
        description='Outlet temperature of cold utility'
    )
    tcuin = gams.Parameter(
        m, name='tcuin', domain=[],
        description='Inlet temperature of hot utility'
    )
    tcuout = gams.Parameter(
        m, name='tcuout', domain=[],
        description='Outlet temperature of cold utility'
    )
    gamma = gams.Parameter(
        m, name='gamma', domain=[i, j],
        description='Upper bound of driving force'
    )
    a = gams.Parameter(
        m, name='a', domain=[i, j, k],
        description='Area for exchanger for match ij in interval k'
    )
    al = gams.Parameter(
        m, name='al', domain=[i, j, k],
        description='Area calculated with log mean'
    )
    acu = gams.Parameter(
        m, name='acu', domain=i,
        description='Area coolers'
    )
    ahu = gams.Parameter(
        m, name='ahu', domain=j,
        description='Area heaters')
    tmapp = gams.Parameter(
        m, name='tmapp', domain=[],
        description='Minimum approach temperature'
    )
    costheat = gams.Parameter(
        m, name='costheat', domain=[],
        description='Cost of heating'
    )
    costcool = gams.Parameter(
        m, name='costcool', domain=[],
        description='Cost of cooling'
    )
    invcost = gams.Parameter(
        m, name='invcost', domain=[],
        description='Investment cost'
    )

    # Variables
    z = gams.Variable(m, name='z', domain=[i, j, k], type='binary')
    zcu = gams.Variable(m, name='zcu', domain=[i], type='binary')
    zhu = gams.Variable(m, name='zhu', domain=[j], type='binary')
    th = gams.Variable(
        m, name='th', domain=[i, k], type='positive',
        description='Temperature of hot stream i as it enters stage k'
    )
    tc = gams.Variable(
        m, name='tc', domain=[j, k], type='positive',
        description='Temperature of cold stream j as it leaves stage k'
    )
    q = gams.Variable(
        m, name='q', domain=[i, j, k], type='positive',
        description=(
            'Energy exchanged between hot stream i ' +
            'and cold stream j in stage k'
        )
    )
    qc = gams.Variable(
        m, name='qc', domain=[i], type='positive',
        description=(
            'Energy exchanged between hot stream i and the cold utility'
        )
    )
    qh = gams.Variable(
        m, name='qh', domain=[j], type='positive',
        description=(
            'Energy exchanged between cold stream j and the hot utility'
        )
    )
    dt = gams.Variable(
        m, name='dt', domain=[i, j, k], type='positive',
        description=(
            'Approach between hot stream i and cold stream j at location k'
        )
    )
    dtcu = gams.Variable(
        m, name='dtcu', domain=[i], type='positive',
        description='Approach between hot stream i and the cold utility'
    )
    dthu = gams.Variable(
        m, name='dthu', domain=[j], type='positive',
        description='Approach between hot stream j and the hot utility'
    )
    cost = gams.Variable(
        m, name='cost',
        description='HEN and utility cost'
    )

    # Equations
    eh = gams.Equation(
        m, name='eh', domain=[i, k],
        description='Energy exchanged by hot stream i in stage k'
    )
    eqc = gams.Equation(
        m, name='eqc', domain=[i],
        description='Energy exchanged by hot stream i with the cold utility'
    )
    teh = gams.Equation(
        m, name='teh', domain=[i],
        description='Total energy exchanged by hot stream i'
    )
    ec = gams.Equation(
        m, name='ec', domain=[j, k],
        description='Energy exchanged by cold stream j in stage k'
    )
    eqh = gams.Equation(
        m, name='eqh', domain=[j],
        description='Energy exchanged by cold stream j with the hot utility'
    )
    tec = gams.Equation(
        m, name='tec', domain=[j],
        description='Total energy exchanged by cold stream j'
    )
    month = gams.Equation(
        m, name='month', domain=[i, k],
        description='Monotonicity of th'
    )
    montc = gams.Equation(
        m, name='montc', domain=[j, k],
        description='Monotonicity of tc'
    )
    monthl = gams.Equation(
        m, name='monthl', domain=[i],
        description='Monotonicity of th k = last'
    )
    montcf = gams.Equation(
        m, name='montcf', domain=[j],
        description='Monotonicity of tc for k = 1'
    )
    tinh = gams.Equation(
        m, name='tinh', domain=[i],
        description='Supply temperature of hot streams'
    )
    tinc = gams.Equation(
        m, name='tinc', domain=[j],
        description='Supply temperature of cold streams'
    )
    logq = gams.Equation(
        m, name='logq', domain=[i, j, k],
        description='Logical constraints on q'
    )
    logqh = gams.Equation(
        m, name='logqh', domain=[j],
        description='Logical constraints on qh(j)'
    )
    logqc = gams.Equation(
        m, name='logqc', domain=[i],
        description='Logical constraints on qc(i)'
    )
    logdth = gams.Equation(
        m, name='logdth', domain=[i, j, k],
        description='Logical constraints on dt at the hot end'
    )
    logdtc = gams.Equation(
        m, name='logdtc', domain=[i, j, k],
        description='Logical constraints on dt at the cold end'
    )
    logdtcu = gams.Equation(
        m, name='logdtcu', domain=[i],
        description='Logical constraints on dtcu'
    )
    logdthu = gams.Equation(
        m, name='logdthu', domain=[j],
        description='Logical constraints on dthu'
    )
    obj = gams.Equation(
        m, name='obj',
        description='Objective function'
    )

    # Equation listing
    teh[i] = (
        (thin[i] - thout[i]) * fh[i]
        == gams.Sum((j, st), q[i, j, st]) + qc[i]
    )
    tec[j] = (
        (tcout[j] - tcin[j]) * fc[j]
        == gams.Sum((i, st), q[i, j, st]) + qh[j]
    )
    eh[i, k].where[st[k]] = (
        fh[i] * (th[i, k] - th[i, k + 1])
        == gams.Sum(j, q[i, j, k])
    )
    ec[j, k].where[st[k]] = (
        fc[j] * (tc[j, k] - tc[j, k + 1])
        == gams.Sum(i, q[i, j, k])
    )
    eqc[i] = (
        fh[i] * (th[i, lastK] - thout[i]) == qc[i]
    )
    eqh[j] = (
        fc[j] * (tcout[j] - tc[j, firstK]) == qh[j]
    )
    tinh[i] = (
        thin[i] == th[i, firstK]
    )
    tinc[j] = (
        tcin[j] == tc[j, lastK]
    )
    month[i, k].where[st[k]] = (
        th[i, k] >= th[i, k + 1]
    )
    montc[j, k].where[st[k]] = (
        tc[j, k] >= tc[j, k + 1]
    )
    monthl[i] = (
        th[i, lastK] >= thout[i]
    )
    montcf[j] = (
        tcout[j] >= tc[j, firstK]
    )
    logq[i, j, k].where[st[k]] = (
        q[i, j, k] - gams.math.Min(ech[i], ecc[j]) * z[i, j, k] <= 0
    )
    logqc[i] = (
        qc[i] - ech[i] * zcu[i] <= 0
    )
    logqh[j] = (
        qh[j] - ecc[j] * zhu[j] <= 0
    )
    logdth[i, j, k].where[st[k]] = (
        dt[i, j, k]
        <= th[i, k] - tc[j, k] + gamma[i, j] * (1 - z[i, j, k])
    )
    logdtc[i, j, k].where[st[k]] = (
        dt[i, j, k + 1]
        <= th[i, k + 1] - tc[j, k + 1] + gamma[i, j] * (1 - z[i, j, k])
    )
    logdthu[j] = (
        dthu[j] <= (thuout - tc[j, firstK])
    )
    logdtcu[i] = (
        dtcu[i] <= th[i, lastK] - tcuout
    )
    obj[...] = cost == (
        # unit capital cost term
        unitc * (
            gams.Sum((i, j, st), z[i, j, st])
            + gams.Sum(i, zcu[i])
            + gams.Sum(j, zhu[j])
        )
        # exchanger area cost (Chen-type) for process stream exchangers
        + acoeff * gams.Sum(
            (i, j, k),
            (
                q[i, j, k] * ((1 / hh[i]) + (1 / hc[j]))
                / (
                    (
                        dt[i, j, k]
                        * dt[i, j, k + 1]
                        * (dt[i, j, k] + dt[i, j, k + 1]) / 2
                        + 1e-6
                    ) ** 0.33333
                    + 1e-6
                )
                + 1e-6
            ) ** aexp,
        )
        # area cost for heaters
        + hucoeff * gams.Sum(
            j,
            (
                qh[j] * ((1 / hc[j]) + 1 / hhu)
                / (
                    (
                        (thuin - tcout[j])
                        * dthu[j]
                        * ((thuin - tcout[j] + dthu[j]) / 2)
                        + 1e-6
                    ) ** 0.33333
                )
                + 1e-6
            ) ** aexp,
        )
        # area cost for coolers
        + cucoeff * gams.Sum(
            i,
            (
                qc[i] * ((1 / hh[i]) + 1 / hcu)
                / (
                    (
                        (thout[i] - tcuin)
                        * dtcu[i]
                        * ((thout[i] - tcuin + dtcu[i]) / 2)
                        + 1e-6
                    ) ** 0.33333
                )
                + 1e-6
            ) ** aexp,
        )
        # utility operating costs
        + gams.Sum(j, qh[j] * hucost)
        + gams.Sum(i, qc[i] * cucost)
    )

    # Process stream data
    ii = 0
    for stream in hot_streams:
        thin[ii + 1] = hot_streams[ii].T_source
        thout[ii + 1] = hot_streams[ii].T_target
        fh[ii + 1] = hot_streams[ii].C
        hh[ii + 1] = hot_streams[ii].h
        ii += 1

    jj = 0
    for stream in cold_streams:
        tcin[jj + 1] = cold_streams[jj].T_source
        tcout[jj + 1] = cold_streams[jj].T_target
        fc[jj + 1] = cold_streams[jj].C
        hc[jj + 1] = cold_streams[jj].h
        jj += 1

    thuin[...] = T_hot_util_in
    thuout[...] = T_hot_util_out
    tcuin[...] = T_cold_util_in
    tcuout[...] = T_cold_util_out
    hucost[...] = hot_util_cost
    cucost[...] = cold_util_cost
    unitc[...] = exchanger_fixed_charge
    acoeff[...] = area_cost_coeff_exchanger
    hucoeff[...] = area_cost_coeff_heater
    cucoeff[...] = area_cost_coeff_cooler
    aexp[...] = cost_exponent_exchanger
    hhu[...] = hot_util_film_coeff
    hcu[...] = cold_util_film_coeff
    tmapp[...] = DT_min

    # Bounds
    dt.lo[i, j, k] = tmapp
    dthu.lo[j] = tmapp
    dtcu.lo[i] = tmapp

    th.up[i, k] = thin[i]
    th.lo[i, k] = thout[i]

    tc.up[j, k] = tcout[j]
    tc.lo[j, k] = tcin[j]

    # Initialization
    th.l[i, k] = thin[i]
    tc.l[j, k] = tcin[j]

    dthu.l[j] = thuout - tcin[j]
    dtcu.l[i] = thin[i] - tcuout

    ech[i] = fh[i] * (thin[i] - thout[i])
    ecc[j] = fc[j] * (tcout[j] - tcin[j])

    gamma[i, j] = gams.math.Max(
        0,
        tcin[j] - thin[i],
        tcin[j] - thout[i],
        tcout[j] - thin[i],
        tcout[j] - thout[i],
    )

    dt.l[i, j, k] = thin[i] - tcin[j]

    # Note: using subset st in the domain instead of a $ condition
    q.l[i, j, st] = gams.math.Min(ech[i], ecc[j])

    # Model and solution
    super_model = gams.Model(
        m,
        name='super',
        equations=m.getEquations(),
        problem=gams.Problem.MINLP,
        sense=gams.Sense.MIN,
        objective=cost,
    )

    solve_options = gams.Options.fromGams(
        {
            'optcr': 0,
            'limrow': 0,
            'limcol': 0,
            'solprint': 0,
            'sysout': 'off',
        }
    )

    super_model.solve(options=solve_options)

    # Post-processing: areas by Chen approximation
    a[i, j, k].where[st[k]] = (
        q.l[i, j, k] * ((1 / hh[i]) + (1 / hc[j]))
        / (
            2 / 3 * (dt.l[i, j, k] * dt.l[i, j, k + 1]) ** 0.5
            + 1 / 6 * (1e-8 + dt.l[i, j, k] + dt.l[i, j, k + 1])
        )
    )

    al[i, j, k].where[st[k]] = (
        q.l[i, j, k] * ((1 / hh[i]) + (1 / hc[j]))
        / (
            dt.l[i, j, k]
            * dt.l[i, j, k + 1]
            * (dt.l[i, j, k] + dt.l[i, j, k + 1]) / 2
        ) ** 0.33333
    )

    # Areas of heaters and coolers
    ahu[j] = (
        qh.l[j]
        * ((1 / hc[j]) + 1 / hhu)
        / (
            (
                (thuin - tcout[j])
                * dthu.l[j]
                * ((thuin - tcout[j] + dthu.l[j]) / 2)
            )
            + 1e-6
        ) ** 0.33333
    )

    acu[i] = (
        qc.l[i]
        * ((1 / hh[i]) + 1 / hcu)
        / (
            (
                (thout[i] - tcuin)
                * dtcu.l[i]
                * ((thout[i] - tcuin + dtcu.l[i]) / 2)
            )
            + 1e-6
        ) ** 0.33333
    )

    # Utility costs
    costheat[...] = gams.Sum(j, qh.l[j] * hucost)
    costcool[...] = gams.Sum(i, qc.l[i] * cucost)

    # Investment cost
    invcost[...] = cost.l - costheat - costcool

    if q is not None:
        Q_exchange=q.l.records.sort_values(by=["k"])
    else:
        Q_exchange=None

    hen = HENDesign(
        streams=streams,
        n_stages=n_stages,
        Q_exchange=Q_exchange,
        T_hot_streams=th,
        T_cold_streams=tc,
    )

    # Print with GAMS-like DISPLAY behavior:
    if disp is True:
        with pd.option_context('display.precision', decimals):
            for var in (th, tc):
                print(f'{var.description}:')
                var_records_round = var.l.records.round(decimals)
                print(f'{var_records_round.to_string(index=False)}\n')

            print(f'{q.description}:')
            q_sorted_by_k = q.l.records.sort_values(by=["k"])
            q_sorted_by_k_round = q_sorted_by_k.round(decimals)
            print(f'{q_sorted_by_k_round.to_string(index=False)}\n')

            for var in (qc, qh, teh, tec):
                print(f'{var.description}:')
                var_records_round = var.l.records.round(decimals)
                print(f'{var_records_round.to_string(index=False)}\n')

            for var in (costheat, costcool, invcost):
                print(f'{var.description}: {var.toValue():.{decimals}f}')

    return hen


syn_heat = synheat
heat_integrate = synheat
synthesize_hen = hen_synthesize = synheat
design_hen = hen_design = synheat
grossmann = yee_grossmann = yee_and_grossmann = synheat
