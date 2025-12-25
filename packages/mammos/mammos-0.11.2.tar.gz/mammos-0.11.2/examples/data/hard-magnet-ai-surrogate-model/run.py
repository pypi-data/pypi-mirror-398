"""Python file to run a mammos-mumag simulation."""

import json
import pathlib

import mammos_analysis
import mammos_entity as me
import mammos_mumag
import mammos_units as u
import pandas as pd

HERE = pathlib.Path(__file__).parent.resolve()
u.set_enabled_equivalencies(u.magnetic_flux_field())

with open(HERE / "inp_parameters.json") as f:
    parameters = json.load(f)

H_max = (5 * u.T).to("A/m")

results_hysteresis = mammos_mumag.hysteresis.run(
    mesh="mesh.fly",
    Ms=me.Ms(parameters["Ms"]),
    A=me.A(parameters["A"]),
    K1=me.Ku(parameters["K1"]),
    theta=0,
    phi=0,
    h_start=H_max,
    h_final=-H_max,
    h_n_steps=300,
)

hyst_data = pd.DataFrame(
    {
        "H (A/m)": results_hysteresis.H.q,
        "M (A/m)": results_hysteresis.M.q,
    }
)
hyst_data.to_csv("hystloop.dat", index=False, sep="\t")

# compute extrinsic parameters here and write to disk for convenience. Can also be done
# by `post-processing.ipynb` notebook later.

extrinsic_properties = mammos_analysis.hysteresis.extrinsic_properties(
    results_hysteresis.H,
    results_hysteresis.M,
    demagnetization_coefficient=1 / 3,
)

# Export inputs and outputs to JSON
parameters["Hc"] = extrinsic_properties.Hc.q.to(u.A / u.m).value
parameters["Mr"] = extrinsic_properties.Mr.q.to(u.A / u.m).value
parameters["BHmax"] = extrinsic_properties.BHmax.q.to(u.J / u.m**3).value
with open("parameters.json", "w") as f:
    json.dump(parameters, f, indent=4)
