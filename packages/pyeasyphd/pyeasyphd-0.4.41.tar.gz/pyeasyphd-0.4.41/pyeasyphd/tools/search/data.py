from typing import Any


def obtain_search_keywords() -> dict[str, Any]:
    """Obtain search keywords dictionary.

    Returns:
        dict[str, Any]: dictionary containing categorized search keywords.
    """
    _h_ = "(?:| |-)"  # hyphen

    evol = "evol(?:ution|utionary)"  # 'evol(?:ution|utionary|ve|ved|ving)'
    computation = "computation(?:|al)"
    strateg = "strateg(?:y|ies)"
    program = "program(?:|ming)"
    algorithm = "algorithm(?:|s)"
    automat = "automat(?:ed|ion)"
    keywords_ec = [  # evolution computation
        ["simulated annealing"],
        ["taboo search"],
        [f"{evol} {strateg}"],
        ["CMA-ES"],  #
        [f"{evol} {program}"],
        [f"differential {evol}"],
        [f"{evol} {algorithm}"],
        [[evol], [strateg, program, "differential", algorithm]],
        [f"genetic {algorithm}"],
        [f"genetic {program}"],
        [["genetic"], [algorithm, program]],
        ["particle swarm"],
        [["swarm"], ["particle"]],
        ["ant colony"],
        ["bee colony"],
        [["colony"], ["ant", "bee"]],
        [f"memetic {algorithm}"],
        [f"population{_h_}based"],
        ["quality diversity"],
        [evol, algorithm, automat],
        [evol, computation],
    ]

    keywords_ss = [  # search strategy
        ["local search"],
        [["local", "search"], ["local search"]],
        ["local optimization"],
        [["local", "optimization"], ["local optimization"]],
        ["random search"],
        [["random", "search"], ["random search"]],
        ["random optimization"],
        [["random", "optimization"], ["random optimization"]],
        ["global search"],
        [["global", "search"], ["global search"]],
        ["global optimization"],
        [["global", "optimization"], ["global optimization"]],
        ["heuristic search"],
        [["heuristic", "search"], ["heuristic search"]],
        ["heuristic optimization"],
        [["heuristic", "optimization"], ["heuristic optimization"]],
    ]

    nsga = "NSGA(?:|II|-II|III|-III)"
    moea_d = "MOEA/D"
    network = "network(?:|s)"
    uncertain = "uncertain(?:|ty)"
    keywords_multi = [  # multi objective
        [moea_d],
        [nsga],
        [f"multi{_h_}objective optimization"],
        [[f"multi{_h_}objective", "optimization"], [f"multi{_h_}objective optimization"]],
        [[f"multi{_h_}objective"], ["optimization"]],
        [f"multi{_h_}model optimization"],
        [[f"multi{_h_}model", "optimization"], [f"multi{_h_}model optimization"]],
        [[f"multi{_h_}model"], ["optimization"]],
        [f"many{_h_}objective optimization"],
        [[f"many{_h_}objective", "optimization"], [f"many{_h_}objective optimization"]],
        [[f"many{_h_}objective"], ["optimization"]],
        [f"dynamic multi{_h_}objective"],
        [f"dynamic {evol} multi{_h_}objective"],
        [["dynamic", f"multi{_h_}objective"], [f"dynamic multi{_h_}objective", f"dynamic {evol} multi{_h_}objective"]],
        [f"dynamic multi{_h_}model"],
        [["dynamic", f"multi{_h_}model"], [f"dynamic multi{_h_}model"]],
        [f"dynamic many{_h_}objective"],
        [f"dynamic {evol} many{_h_}objective"],
        [["dynamic", f"many{_h_}objective"], [f"dynamic many{_h_}objective", f"dynamic {evol} many{_h_}objective"]],
        ["dynamic", "optimization"],
        ["dynamic", network],
        [["dynamic"], [f"multi{_h_}objective", f"multi{_h_}model", f"many{_h_}objective", "optimization", network]],
        [f"{uncertain} optimization"],
        [[uncertain, "optimization"], [f"{uncertain} optimization"]],
        [[uncertain], ["optimization"]],
        ["pareto optimization"],
        [["pareto", "optimization"], ["pareto optimization"]],
        [["pareto"], ["optimization"]],
    ]

    dimension = "dimension(?:|al)"
    distribut = "distribut(?:ion|ed)"
    keywords_parallel = [  # parallel
        [f"large{_h_}scale"],
        [f"high{_h_}{dimension}"],
        [f"high{_h_}performance"],
        ["parallel", evol],
        ["parallel", algorithm],
        [["parallel"], [evol, algorithm]],
        [distribut, evol],
        [distribut, algorithm],
        [[distribut], [evol, algorithm]],
    ]

    keywords_mo = [  # math optimization
        [f"zero{_h_}orde", "optimization"],
        ["coordinate", "descent"],
        ["gradient", "descent"],
        ["gradient", "stochastic"],
        [["gradient"], ["descent", "stochastic"]],
        ["convex", "optimization"],
        [f"non{_h_}convex", "optimization"],
        [["convex"], [f"non{_h_}convex", "optimization"]],
        [[f"non{_h_}convex"], ["convex", "optimization"]],
        ["stochastic", "optimization"],
        [["stochastic"], ["optimization"]],
        ["gaussian", "distribution"],
    ]

    multi_task = "multi(?:|-)task"
    federa = "federa(?:l|ted)"
    weakly_ = f"weakly{_h_}"
    generat = "generat(?:ive|ion)"
    keywords_ml = [  # machine learning
        ["automated", "machine", "learning"],
        [["machine", "learning"], [automat]],
        ["deep", "learning"],
        [f"semi{_h_}supervised", "learning"],
        [f"self{_h_}supervised", "learning"],
        [f"{weakly_}supervised", "learning"],
        ["unsupervised", "learning"],
        [f"multi{_h_}instance", "learning"],
        ["active", "learning"],
        [
            ["supervised", "learning"],
            [f"semi{_h_}supervised", f"self{_h_}supervised", f"weakly{_h_}supervised", "unsupervised"],
        ],
        ["reinforcement", "learning", f"on{_h_}policy"],
        ["reinforcement", "learning", f"off{_h_}policy"],
        ["reinforcement", "learning", "offline"],
        ["reinforcement", "learning", f"model{_h_}based"],
        ["reinforcement", "learning", "continual"],
        ["reinforcement", "learning", "deep"],
        ["reinforcement", "learning", evol],
        [
            ["reinforcement", "learning"],
            ["offline", f"on{_h_}policy", f"off{_h_}policy", f"model{_h_}based", "deep", "continual", evol],
        ],
        ["policy", "search"],
        [["policy"], ["policy", "search"]],
        [f"q{_h_}learning"],
        ["manifold", "learning"],
        [["manifold"], ["Learning"]],
        [multi_task, "learning"],
        [[multi_task], ["learning"]],
        ["transfe", "learning"],
        [["transfe"], ["Learning"]],
        ["domain", "adaptation"],
        ["domain", "generalization"],
        [f"meta{_h_}learning"],
        [[f"meta{_h_}learning"], ["learning"]],
        [federa, "learning"],
        [[federa], ["learning"]],
        ["ensemble", "learning"],
        [["ensemble"], ["learning"]],
        ["online", "learning"],
        [f"few{_h_}shot", "learning"],
        [[f"few{_h_}shot"], ["learning"]],
        [f"one{_h_}shot", "learning"],
        [[f"one{_h_}shot"], ["learning"]],
        [f"zero{_h_}shot", "learning"],
        [[f"zero{_h_}shot"], ["learning"]],
        ["representation", "learning"],
        [["representation"], ["learning"]],
        ["induction"],
        ["deduction"],
        ["transduction"],
        ["neural", network],
        ["graph", network],
        [[network], ["graph", "neural"]],
        [["graph"], [network, "neural"]],
        ["kernel"],
        ["embedding"],
        ["transformer"],
        ["diffusion", "model"],
        [["diffusion"], ["model"]],
        [generat, "model"],
        [[generat], ["model"]],
        ["large language model"],
        [["large", "language", "model"], ["large language model"]],
    ]

    cluster = "cluster(?:|s|ing)"
    data_driven = "date(?:| |-)driven"
    prove = "prov(?:able|e)"
    predict = "predict(?:|ed|ion)"
    recommend = "recommend(?:ed|ation)"
    markov = "markov(?:|ian)"
    keywords_ec_ml = [  # evolution computation and machine learning
        ["neuro(?:| |-)evolution"],
        ["adaptation"],
        ["bayesian", "optimization"],
        ["bi-level", "optimization"],
        ["bayesian", "inference"],
        ["bayesian", "learning"],
        [["bayesian"], ["optimization", "inference", "learning"]],
        [markov, "decision"],
        [markov, "chain"],
        [[markov], ["decision", "chain"]],
        [prove],
        ["time", "series"],
        [cluster],
        [f"co{_h_}evolution", f"co{_h_}operation"],
        [[f"co{_h_}evolution"], [f"co{_h_}operation"]],
        [[f"co{_h_}operation"], [f"co{_h_}evolution"]],
        [data_driven],
        [predict],
        [recommend, "system"],
        [distribut, "shift"],
    ]

    converg = "converg(?:e|ence|ent|ed|ing)"
    theor = "theor(?:y|etic|etical|etically)"
    analy = "analy(?:ze|sis|zed|zing)"
    bound = "bound(?:|s)"
    run = "run(?:|ning)"
    keywords_theory = [  # theory
        ["drift", "analysis"],
        ["hitting", "time"],
        [evol, converg],
        [evol, "time"],
        [evol, theor],
        [evol, bound],
        [evol, "complexity"],
        ["swarm", converg],
        ["swarm", "time"],
        ["swarm", theor],
        ["swarm", bound],
        ["swarm", "complexity"],
        ["colony", converg],
        ["colony", "time"],
        ["colony", theor],
        ["colony", bound],
        ["colony", "complexity"],
        ["genetic", converg],
        ["genetic", "time"],
        ["genetic", theor],
        ["genetic", bound],
        ["genetic", "complexity"],
        [analy, converg],
        [analy, "time"],
        [analy, theor],
        [analy, bound],
        [analy, "complexity"],
        [computation, "time"],
        [f"{run} time"],
        ["upper", bound],
        ["lower", bound],
        [[converg], [evol, "swarm", "colony", "genetic", analy]],
        [["time"], [evol, "swarm", "colony", "genetic", analy, "hitting", computation, run]],
        [[theor], [evol, "swarm", "colony", "genetic", analy]],
        [[bound], [evol, "swarm", "colony", "genetic", analy, "upper", "lower"]],
        [["complexity"], [evol, "swarm", "colony", "genetic", analy]],
        [[analy], [converg, "time", theor, bound, "complexity"]],
    ]

    keywords_dict = {
        "EC": keywords_ec,
        "SS": keywords_ss,
        "Multi": keywords_multi,
        "Parallel": keywords_parallel,
        "MO": keywords_mo,
        "ML": keywords_ml,
        "ECML": keywords_ec_ml,
        "Theory": keywords_theory,
    }
    return keywords_dict
