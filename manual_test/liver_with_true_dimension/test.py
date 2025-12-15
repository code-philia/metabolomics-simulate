"""
run_metabolism.py

Stiff, physically-scaled metabolic network simulator.

Units:
 - concentration: mM
 - time: minutes
 - reaction rate: mM/min
 - Vmax (k_max in JSON): mM/min
 - Km, Ki in JSON: mM

Features:
 - Michaelis-Menten product form for multi-substrate reactions
 - External meal input (mM/min)
 - First-order clearance (1/min)
 - ODE solver: scipy.solve_ivp(method='BDF') for stiffness
 - Per-metabolite PNGs + combined grid PNG; optional CSV export
"""

import json
import math
import os
from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Callable, Any

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
from PIL import Image
import csv

# -------------------------
# Reaction dataclass
# -------------------------
@dataclass
class Reaction:
    id: str
    name: str
    inputs: Dict[str, float]
    outputs: Dict[str, float]
    k_max: float                   # Vmax in mM/min
    Km: Dict[str, float]           # Km per substrate (mM)
    Hill: Dict[str, float]         # Hill coefficients (dimensionless)
    Ki: Dict[str, float]           # inhibition constants (mM)
    Ki_Hill: Dict[str, float]      # Hill for inhibitors
    pH_opt: float = 7.4
    sigma_pH: float = 1.0
    Q10: float = 2.0
    transport_Vmax: float = 0.0
    transport_Km: float = 1.0
    hormone_factors: Dict[str, float] = field(default_factory=dict)
    feedback_params: Dict[str, Tuple[float, float]] = field(default_factory=dict)

    def rate(self, conc: Dict[str, float], hormones: Dict[str, float], env: Dict[str, float]) -> float:
        """
        Compute reaction rate v (mM/min).
        v = Vmax * prod_i ([S_i]^n / (Km_i^n + [S_i]^n)) * inhibition * env * hormone * feedback
        """
        # substrate saturation product
        S_term = 1.0
        if len(self.inputs) == 0:
            S_term = 1.0
        else:
            for s, sto in self.inputs.items():
                S = max(conc.get(s, 0.0), 0.0)
                Km = float(self.Km.get(s, 1e-6))  # avoid zero
                n = float(self.Hill.get(s, 1.0))
                # Hill-like saturation
                denom = Km**n + S**n
                sat = (S**n) / (denom + 1e-12)
                S_term *= sat

        # product inhibition (multiplicative)
        I_term = 1.0
        for p, Ki in self.Ki.items():
            P = max(conc.get(p, 0.0), 0.0)
            m = float(self.Ki_Hill.get(p, 1.0))
            denom = (Ki**m + P**m)
            inh = (Ki**m) / (denom + 1e-12)
            I_term *= inh

        # environment modifiers (rough)
        T = env.get("T", 37.0)
        Q10_term = self.Q10 ** ((T - 37.0) / 10.0)
        pH = env.get("pH", 7.4)
        pH_term = math.exp(-((pH - self.pH_opt)**2) / (2.0 * self.sigma_pH**2))

        # transport effect (convert to dimensionless saturation factor if provided)
        transport_factor = 1.0
        if self.transport_Vmax > 0 and len(self.inputs) > 0:
            first_s = next(iter(self.inputs.keys()))
            S = max(conc.get(first_s, 0.0), 0.0)
            transport_factor = S / (self.transport_Km + S + 1e-12)

        # hormone multiplicative factor (simple linear mapping)
        hormone_factor = 1.0
        for h, coef in self.hormone_factors.items():
            hormone_level = hormones.get(h, 0.0)
            hormone_factor *= (1.0 + float(coef) * hormone_level)

        # feedback inhibition (multiplicative)
        fb = 1.0
        for x, (Ki_val, m) in self.feedback_params.items():
            X = max(conc.get(x, 0.0), 0.0)
            Ki_val = float(Ki_val)
            m = float(m)
            fb *= (Ki_val**m) / (Ki_val**m + X**m + 1e-12)

        # Vmax in mM/min
        v = float(self.k_max) * S_term * I_term * Q10_term * pH_term * transport_factor * hormone_factor * fb

        # numerical safety: cap to a large value, ensure non-neg
        if not np.isfinite(v):
            v = 0.0
        v = max(v, 0.0)
        # optional global cap to prevent extreme instantaneous flux (tunable)
        max_allowed = 100.0  # mM/min, extremely high, but prevents blow-ups
        if v > max_allowed:
            v = max_allowed
        return v


# -------------------------
# Utilities: load reactions, build metabolite list
# -------------------------
def load_reactions(path: str) -> List[Reaction]:
    with open(path, "r") as f:
        params = json.load(f)
    reactions = []
    for rid, p in params.items():
        reactions.append(
            Reaction(
                id=rid,
                name=p.get("name", rid),
                inputs=p.get("inputs", {}),
                outputs=p.get("outputs", {}),
                k_max=float(p.get("k_max", 0.0)),
                Km={k: float(v) for k, v in p.get("Km", {}).items()},
                Hill={k: float(v) for k, v in p.get("Hill", {}).items()},
                Ki={k: float(v) for k, v in p.get("Ki", {}).items()},
                Ki_Hill={k: float(v) for k, v in p.get("Ki_Hill", {}).items()},
                pH_opt=float(p.get("pH_opt", 7.4)),
                sigma_pH=float(p.get("sigma_pH", 1.0)),
                Q10=float(p.get("Q10", 2.0)),
                transport_Vmax=float(p.get("transport_Vmax", 0.0)),
                transport_Km=float(p.get("transport_Km", 1.0)),
                hormone_factors=p.get("hormone_factors", {}),
                feedback_params=p.get("feedback_params", {}),
            )
        )
    return reactions


def collect_metabolites(reactions: List[Reaction]) -> List[str]:
    mets = set()
    for r in reactions:
        mets.update(r.inputs.keys())
        mets.update(r.outputs.keys())
    return sorted(list(mets))


def build_initial_pool(reactions: List[Reaction], user_initial: Dict[str, float], default_value: float = 0.0) -> Dict[str, float]:
    mets = collect_metabolites(reactions)
    init = {m: float(default_value) for m in mets}
    if user_initial:
        for k, v in user_initial.items():
            if k in init:
                init[k] = float(v)
            else:
                # if user provided a metabolite not present in reactions, still include it
                init[k] = float(v)
    return init


# -------------------------
# Meal input and clearance
# -------------------------
def meal_input_gaussian(t_min: float) -> Dict[str, float]:
    """
    Single meal absorption centered around 30 min.
    Returns fluxes in mM/min into the corresponding pools.
    Peak flux values chosen to be physiologically plausible magnitudes.
    """
    peak = 30.0  # minutes
    width = 30.0
    gauss = math.exp(-((t_min - peak)**2) / (2.0 * width**2))
    # scale so area ~ total bolus in mM*min not exact real grams->mM conversion
    return {
        "Dietary_TAG": 0.2 * gauss,       # mM/min peak ~0.2
        "Glucose": 1.0 * gauss,           # mM/min
        "CholesterylEster": 0.02 * gauss, # mM/min
    }



def meal_input_three_meals(t_min: float) -> Dict[str, float]:
    """
    Three-meal daily dietary absorption model.
    Time unit: minutes from simulation start.
    Meals:
        Breakfast 08:00  -> t= 480 min
        Lunch     13:00  -> t= 780 min
        Dinner    19:00  -> t=1140 min
    Each meal produces nutrient absorption approximated by a Gaussian curve.
    Output: fluxes in mM/min
    """

    # ---- Meal schedule (min) ----
    meals = {
        "breakfast": 480.0,   # 8:00
        "lunch":     780.0,   # 13:00
        "dinner":    1140.0,  # 19:00
    }

    # ---- Relative meal sizes (dimensionless scaling) ----
    meal_sizes = {
        "breakfast": 0.6,   # light breakfast
        "lunch":     1.2,   # largest meal
        "dinner":    1.0,
    }

    width = 90.0    # absorption spread (~1.5 hours)

    # output flux accumulator
    flux = {
        "Dietary_TAG": 0.0,
        "Dietary_Cholesterol": 0.0,
        "Glucose": 0.0,
        "CholesterylEster": 0.0,
    }

    # -------------------------
    # Sum contributions from each meal
    # -------------------------
    for meal, center in meals.items():
        size = meal_sizes[meal]

        gauss = math.exp(-((t_min - center)**2) / (2 * width**2))

        # scaled flux contribution
        flux["Dietary_TAG"]     += size * 0.20 * gauss   # mM/min
        flux["Dietary_Cholesterol"] += size * 0.10 * gauss
        flux["Glucose"]         += size * 1.00 * gauss
        flux["CholesterylEster"]+= size * 0.02 * gauss

    return flux



def default_clearance(conc: Dict[str, float]) -> Dict[str, float]:
    """
    First-order clearance fluxes (mM/min) = k_clear * concentration
    k_clear values are per-minute fractional clearances.
    """
    out = {}
    kmap = {
        # "Chylomicron": 0.02,
        # "Chylomicron_Remnant": 0.05,
        # "VLDL": 0.01,
        # "LDL": 0.005,
        "Bile": 0.02,
        # "Bilirubin": 0.02,
        # # free metabolite clearances
        # "FFA_plasma": 0.1,
        # "FFA": 0.05,
    }
    for m, k in kmap.items():
        out[m] = k * conc.get(m, 0.0)
    return out


# -------------------------
# ODE RHS builder
# -------------------------
def make_rhs(reactions: List[Reaction],
             metabolites: List[str],
             food_fn: Callable[[float], Dict[str, float]],
             clearance_fn: Callable[[Dict[str, float]], Dict[str, float]],
             hormones_fn: Callable[[Dict[str, float], float], Dict[str, float]],
             env: Dict[str, float]) -> Callable[[float, np.ndarray], np.ndarray]:
    met_index = {m: i for i, m in enumerate(metabolites)}

    def rhs(t, y):
        """
        t in minutes (float)
        y is vector of concentrations (mM) in order metabolites
        returns dy/dt (mM/min)
        """
        conc = {m: float(y[met_index[m]]) for m in metabolites}
        hormones = hormones_fn(conc, t)
        # compute reaction rates
        rates = [r.rate(conc, hormones, env) for r in reactions]   # list length R

        # initialize dy/dt
        dydt = {m: 0.0 for m in metabolites}

        # contributions from reactions
        for r, v in zip(reactions, rates):
            # subtract substrates
            for s, sto in r.inputs.items():
                if s in dydt:
                    dydt[s] -= sto * v
                else:
                    # if substrate not part of global metabolites, ignore (or consider creating variable)
                    pass
            # add products
            for p, sto in r.outputs.items():
                if p in dydt:
                    dydt[p] += sto * v

        # add food inputs (flux mM/min)
        if food_fn is not None:
            food_flux = food_fn(t)
            for m, flux in food_flux.items():
                if m in dydt:
                    dydt[m] += float(flux)
                else:
                    # optionally extend dydt for new metabolite - ignored here
                    pass

        # subtract clearances
        if clearance_fn is not None:
            clear_flux = clearance_fn(conc)
            for m, flux in clear_flux.items():
                if m in dydt:
                    dydt[m] -= float(flux)

        # convert dict to array in correct order
        dy = np.zeros(len(metabolites))
        for m, i in met_index.items():
            dy[i] = dydt[m]

        return dy

    return rhs


# -------------------------
# Simple hormone model
# -------------------------
def simple_hormone_model(conc: Dict[str, float], t_min: float) -> Dict[str, float]:
    """
    Map glucose level to insulin/glucagon scale:
    insulin ~ sigmoid of glucose (basal 1.0)
    glucagon ~ inverse of insulin
    Returns dimensionless hormone levels (1.0 basal)
    """
    glucose = conc.get("Glucose", 5.0)
    # insulin: logistic centered at 5 mM
    ins = 1.0 + 2.0 / (1.0 + math.exp(- (glucose - 5.0)))   # ranges ~1..3
    glu = 1.0 + 1.0 / (1.0 + math.exp((glucose - 5.0)))     # glucagon decreases as glucose increases
    return {"insulin": ins, "glucagon": glu}


# -------------------------
# Visualization utilities
# -------------------------
def plot_and_save_per_metabolite(time_vec: np.ndarray, conc_hist: np.ndarray, metabolites: List[str],
                                 out_dir: str = "metabolite_plots", grid_fname: str = "metabolites_grid.png"):
    os.makedirs(out_dir, exist_ok=True)
    image_paths = []
    for i, m in enumerate(metabolites):
        plt.figure(figsize=(4, 3))
        plt.plot(time_vec/60, conc_hist[:, i])
        plt.title(f"{m}")
        plt.xlabel("Time (h)")
        plt.ylabel("Concentration (mM)")
        plt.grid(True)
        fname = os.path.join(out_dir, f"{i:03d}_{m}.png")
        plt.tight_layout()
        plt.savefig(fname, dpi=150)
        plt.close()
        image_paths.append(fname)

    imgs = [Image.open(p) for p in image_paths]
    N = len(imgs)
    cols = int(math.ceil(math.sqrt(N)))
    rows = int(math.ceil(N / cols))
    w, h = imgs[0].size
    grid = Image.new("RGB", (cols * w, rows * h), "white")
    for idx, im in enumerate(imgs):
        r = idx // cols
        c = idx % cols
        grid.paste(im, (c * w, r * h))
    grid.save(grid_fname)
    print("Saved combined grid to", grid_fname)


def save_timecourse_csv(time_vec: np.ndarray, conc_hist: np.ndarray, metabolites: List[str], csv_path: str):
    with open(csv_path, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["time_min"] + metabolites)
        for t, row in zip(time_vec, conc_hist):
            writer.writerow([t] + list(row))


# -------------------------
# Main driver
# -------------------------
def main(reaction_json_path: str = "reaction_parameters.json",
         realistic_initial: Dict[str, float] = None,
         t_max_min: float = 1440.0,
         dt_out_min: float = 1.0):
    # load reactions
    reactions = load_reactions(reaction_json_path)

    # collect metabolites and initial pool
    metabolites = collect_metabolites(reactions)

    # fallback realistic_initial if not given
    # if realistic_initial is None:
    #     realistic_initial = {
    #         "Dietary_TAG": 0.0, "Emulsified_TAG": 0.05, "MAG": 0.01, "FFA": 0.1, "FFA_plasma": 0.2,
    #         "FA": 0.1, "Acyl_CoA": 0.05, "Acetyl_CoA": 0.05, "ATP": 2.5, "NADH": 0.1,
    #         "Chylomicron": 0.01, "Chylomicron_Remnant": 0.0, "FreeCholesterol": 0.2, "CholesterylEster": 0.05,
    #         "Bile": 0.1, "Glucose": 5.0, "Bilirubin": 0.01, "G3P": 0.05, "TAG_Adipose": 1.0, "TAG_Liver": 0.2,
    #         "VLDL": 0.01, "HDL": 0.01, "LDL": 0.01
    #     }

    init_pool = build_initial_pool(reactions, realistic_initial, default_value=0.0)
    y0 = np.array([init_pool[m] for m in metabolites], dtype=float)

    # build RHS
    rhs = make_rhs(reactions,
                   metabolites,
                #    food_fn=meal_input_gaussian,
                   food_fn=meal_input_three_meals,
                   clearance_fn=default_clearance,
                   hormones_fn=simple_hormone_model,
                   env={"T": 37.0, "pH": 7.4})

    # time span
    t_span = (0.0, t_max_min)
    # output times (to store)
    t_eval = np.arange(0.0, t_max_min + dt_out_min, dt_out_min)

    # Solve stiff ODE with BDF (backward differentiation) method
    sol = solve_ivp(fun=rhs, t_span=t_span, y0=y0, method='BDF', t_eval=t_eval, atol=1e-6, rtol=1e-6)

    if not sol.success:
        print("WARNING: solver failed:", sol.message)

    conc_hist = sol.y.T   # shape (len(t_eval), n_mets)
    time_vec = sol.t

    # save CSV
    save_timecourse_csv(time_vec, conc_hist, metabolites, "metabolites_timecourse.csv")
    print("Saved metabolites_timecourse.csv")

    # plot per metabolite and grid
    plot_and_save_per_metabolite(time_vec, conc_hist, metabolites,
                                 out_dir="metabolite_plots", grid_fname="metabolites_grid.png")
    print("Plots saved in metabolite_plots/ and metabolites_grid.png")

    # plot some selected reaction rates optionally (compute rates over solution)
    # compute rates time series (expensive but useful)
    rate_time_series = []
    for idx, t in enumerate(time_vec):
        conc_at_t = {m: float(conc_hist[idx, i]) for i, m in enumerate(metabolites)}
        hormones = simple_hormone_model(conc_at_t, t)
        rates = [r.rate(conc_at_t, hormones, {"T": 37.0, "pH": 7.4}) for r in reactions]
        rate_time_series.append(rates)
    rate_time_series = np.array(rate_time_series)  # shape (len(t), n_reactions)

    # plot first 8 reaction rates for quick check
    plt.figure(figsize=(10,6))
    for i in range(min(8, rate_time_series.shape[1])):
        plt.plot(time_vec/60, rate_time_series[:, i], label=reactions[i].id)
    plt.legend()
    plt.xlabel("Time (h)")
    plt.ylabel("Rate (mM/min)")
    plt.title("Sample reaction rates")
    plt.savefig("sample_reaction_rates.png", dpi=150)
    plt.close()
    print("Saved sample_reaction_rates.png")


if __name__ == "__main__":
    main(reaction_json_path="reaction_parameters.json",
         realistic_initial=None,
         t_max_min=1440.0,
         dt_out_min=1.0)
