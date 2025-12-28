import scipy.interpolate as inter
from pyroll.report import hookimpl
from pyroll.core import Unit, PassSequence, Transport, CoolingPipe, RollPass

import matplotlib.pyplot as plt

@hookimpl(specname="unit_plot")
def disked_unit_temperature_plot(unit: Unit):
    if isinstance(unit, RollPass):
        fig: plt.Figure = plt.figure(figsize=(6, 6))
        ax: plt.Axes
        axl: plt.Axes
        ax, axl = fig.subplots(nrows=2, height_ratios=[1, 0.3])
        ax.set_title("Karman Stress Distribution ")
        ax.grid(lw=0.5)


        vertical_stress_interpolation = inter.interp1d(unit.karman_solution.solution.index, unit.karman_solution.solution["vertical_stress"],
                                                            fill_value="extrapolate")

        normal_pressure_interpolation = inter.interp1d(unit.karman_solution.solution.index, unit.karman_solution.solution["normal_pressure"],
                                                            fill_value="extrapolate")

        shear_stress_interpolation = inter.interp1d(unit.karman_solution.solution.index, unit.karman_solution.solution["shear_stress"],
                                                            fill_value="extrapolate")

        vert_stress = ax.plot(unit.karman_solution.solution.index, vertical_stress_interpolation(unit.karman_solution.solution.index), label=r"Vertical Stress $\sigma_{y}$")
        normal_press = ax.plot(unit.karman_solution.solution.index, normal_pressure_interpolation(unit.karman_solution.solution.index),
                label=r"Normal Pressure $p_{N}$")
        shear_stress = ax.plot(unit.karman_solution.solution.index, shear_stress_interpolation(unit.karman_solution.solution.index),
                label=r"Shear Stress $\tau$")
        ax.set_xlabel("x")
        ax.set_ylabel("Stress")

        axl.axis("off")
        axl.legend(handles=vert_stress + normal_press + shear_stress, ncols=3, loc="lower center")

        return fig