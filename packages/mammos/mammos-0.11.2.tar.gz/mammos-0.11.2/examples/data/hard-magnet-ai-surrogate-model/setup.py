"""Python file to run all simulations."""

import json
import pathlib
import shutil
import subprocess

import mammos_analysis
import mammos_dft
import mammos_spindynamics
import mammos_units as u
import numpy as np
from mammos_mumag.mesh import Mesh

u.set_enabled_equivalencies(u.magnetic_flux_field())
HERE = pathlib.Path(__file__).parent.resolve()


def setup():
    """Setup hystloop simulation with mumag."""
    OUTDIR = HERE / "out"
    OUTDIR.mkdir(parents=True, exist_ok=True)

    material = "Co2Fe2H4"
    results_dft = mammos_dft.db.get_micromagnetic_properties(material)
    results_spindynamics = mammos_spindynamics.db.get_spontaneous_magnetization(material)
    results_kuzmin = mammos_analysis.kuzmin_properties(
        T=results_spindynamics.T,
        Ms=results_spindynamics.Ms,
        K1_0=results_dft.Ku_0,
    )

    # Download mesh if needed
    if not pathlib.Path("mesh.fly").exists():
        mesh = Mesh("cube50_singlegrain_msize2")
        mesh.write("mesh.fly")

    for T_full in np.linspace(0, 0.95 * results_kuzmin.Tc.value, 16):
        T = round(T_full, 3)  # avoid very large floating point numbers
        print(f"Working on {T=} K.")
        Ms = results_kuzmin.Ms(T)
        A = results_kuzmin.A(T)
        K1 = results_kuzmin.K1(T)

        outdir_i = OUTDIR / f"T_{T}"

        if outdir_i.is_dir():
            # if the output directory is already there, but no parameter file
            # is found, remove the directory and run simulation again
            if (outdir_i / "parameters.json").is_file():
                continue
            else:
                shutil.rmtree(outdir_i)

        outdir_i.mkdir(parents=True)  # raise err if the individual outdir exists
        with open(outdir_i / "inp_parameters.json", "w") as f:
            json.dump(
                {
                    "T": T,
                    "Ms": Ms.value,
                    "A": A.value,
                    "K1": K1.value,
                },
                f,
                indent=4,
            )

        shutil.copyfile(HERE / "submit.sh", outdir_i / "submit.sh")
        shutil.copyfile(HERE / "run.py", outdir_i / "run.py")
        shutil.copy(HERE / "mesh.fly", outdir_i / "mesh.fly")

        res = subprocess.run(
            ["sbatch", "submit.sh"],
            cwd=outdir_i,
            stderr=subprocess.PIPE,
        )

        return_code = res.returncode

        if return_code:
            raise RuntimeError(f"Submission has failed. Exit with error: \n{res.stderr.decode('utf-8')}")

    print("Submission complete.")


if __name__ == "__main__":
    setup()
