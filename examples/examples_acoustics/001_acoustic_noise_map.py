"""Example: Acoustic noise map

This example computes the noise emitted by each turbine of a small farm with the empirical
acoustic model of FlorisModel, and maps the total A-weighted sound pressure level at ground
level. It compares normal operation with a case where the front turbine is yawed and derated.

The turbine parameters used by the acoustic model are given in the ``acoustics`` section of the
turbine definition (see floris/turbine_library/nrel_5MW.yaml).
"""

import matplotlib.pyplot as plt
import numpy as np

from floris import FlorisModel
from floris.flow_visualization import visualize_cut_plane
from floris.layout_visualization import plot_turbine_rotors


# Create a row of three turbines, with yaw and derating allowed on the same turbine
fmodel = FlorisModel("../inputs/gch.yaml")
fmodel.set_operation_model("mixed")
D = 125.88  # Rotor diameter of the NREL 5MW turbine [m]
fmodel.set(
    layout_x=[0.0, 5 * D, 10 * D],
    layout_y=[0.0, 0.0, 0.0],
    wind_speeds=[12.0, 12.0],
    wind_directions=[270.0, 270.0],
    turbulence_intensities=[0.06, 0.06],
)

# First condition: normal operation. Second condition: front turbine yawed by 20 degrees
# and derated to 3 MW.
fmodel.set(
    yaw_angles=np.array([[0.0, 0.0, 0.0], [20.0, 0.0, 0.0]]),
    power_setpoints=np.array([[1e12, 1e12, 1e12], [3.0e6, 1e12, 1e12]]),
)
fmodel.run()

# Sound pressure level of each turbine 100 m from its hub, with shape (n_findex, n_turbines)
print("Turbine sound pressure levels at 100 m [dB(A)]")
print(f"  Normal operation:     {np.round(fmodel.acoustic_results[0], 1)}")
print(f"  Front turbine curbed: {np.round(fmodel.acoustic_results[1], 1)}")
print("Farm power [MW]")
print(f"  Normal operation:     {fmodel.get_farm_power()[0] / 1e6:.2f}")
print(f"  Front turbine curbed: {fmodel.get_farm_power()[1] / 1e6:.2f}")

# Ground-level noise maps
fig, axarr = plt.subplots(2, 1, figsize=(10, 8))
titles = ["Normal operation", "Front turbine yawed and derated"]
for findex, (ax, title) in enumerate(zip(axarr, titles)):
    acoustic_plane = fmodel.calculate_acoustic_plane(
        height=0.0,
        findex_for_viz=findex,
        x_resolution=300,
        y_resolution=150,
        y_bounds=(-3 * D, 3 * D),
    )
    visualize_cut_plane(
        acoustic_plane,
        ax=ax,
        levels=np.arange(25.0, 62.5, 2.5),
        cmap="magma",
        color_bar=True,
        colorbar_label="SPL [dB(A)]",
        line_contour=False,
        title=title,
    )
    plot_turbine_rotors(fmodel, ax=ax, yaw_angles=fmodel.core.farm.yaw_angles[findex])

plt.tight_layout()
plt.show()
