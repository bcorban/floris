from pathlib import Path

import numpy as np
import pytest

from floris import FlorisModel
from floris.floris_model import ACOUSTIC_REFERENCE_DISTANCE


TEST_DATA = Path(__file__).resolve().parent / "data"
YAML_INPUT = TEST_DATA / "input_full.yaml"


def single_turbine_model(wind_speed=8.0):
    fmodel = FlorisModel(configuration=YAML_INPUT)
    fmodel.set(
        layout_x=[0.0],
        layout_y=[0.0],
        wind_speeds=[wind_speed],
        wind_directions=[270.0],
        turbulence_intensities=[0.06],
        wind_shear=0.0,
    )
    return fmodel


def test_acoustic_results_single_turbine():
    # Below rated, the tip speed is TSR * U
    fmodel = single_turbine_model(wind_speed=8.0)
    fmodel.run()
    D = fmodel.core.farm.rotor_diameters[0, 0]
    thrust_coefficient = fmodel.get_turbine_thrust_coefficients()[0, 0]

    tip_speed = 8.0 * 8.0  # TSR of the NREL 5MW times the wind speed
    blade_area_ratio = 3 * 3.0 / (np.pi * D / 2)
    expected = (
        63.3 * np.log10(tip_speed)
        + 11.5 * np.log10(blade_area_ratio)
        + 2.5 * np.log10(thrust_coefficient)
        + 20.0 * np.log10(D / ACOUSTIC_REFERENCE_DISTANCE)
        - 10.0 * np.log10(D)
        - 27.5
    )
    assert fmodel.acoustic_results.shape == (1, 1)
    np.testing.assert_allclose(fmodel.acoustic_results[0, 0], expected)

    # Above rated, the rotor speed is the rated rotor speed
    fmodel = single_turbine_model(wind_speed=15.0)
    fmodel.run()
    D = fmodel.core.farm.rotor_diameters[0, 0]
    thrust_coefficient = fmodel.get_turbine_thrust_coefficients()[0, 0]
    tip_speed = 12.1 * 2 * np.pi / 60 * D / 2
    expected = (
        63.3 * np.log10(tip_speed)
        + 11.5 * np.log10(blade_area_ratio)
        + 2.5 * np.log10(thrust_coefficient)
        + 20.0 * np.log10(D / ACOUSTIC_REFERENCE_DISTANCE)
        - 10.0 * np.log10(D)
        - 27.5
    )
    np.testing.assert_allclose(fmodel.acoustic_results[0, 0], expected)


def test_acoustic_results_need_run():
    fmodel = single_turbine_model()
    with pytest.raises(RuntimeError):
        fmodel.acoustic_results

    fmodel.run()
    level = fmodel.acoustic_results[0, 0]

    # Results of a previous run are not returned once the model has been changed
    fmodel.set(wind_speeds=[10.0])
    with pytest.raises(RuntimeError):
        fmodel.acoustic_results

    fmodel.run()
    assert fmodel.acoustic_results[0, 0] > level


def test_acoustic_results_yaw_and_derating():
    fmodel = FlorisModel(configuration=YAML_INPUT)
    fmodel.set_operation_model("mixed")
    fmodel.set(
        layout_x=[0.0, 0.0, 0.0, 0.0],
        layout_y=[0.0, 1000.0, 2000.0, 3000.0],
        wind_speeds=[15.0],
        wind_directions=[270.0],
        turbulence_intensities=[0.06],
        yaw_angles=np.array([[0.0, 20.0, 0.0, 20.0]]),
        power_setpoints=np.array([[1e12, 1e12, 2.0e6, 2.0e6]]),
    )
    fmodel.run()
    levels = fmodel.acoustic_results[0]

    # Yawing or derating a turbine reduces its noise, combining both reduces it further
    assert levels[1] < levels[0]
    assert levels[2] < levels[0]
    assert levels[3] < levels[2]


def test_acoustic_results_disabled_turbine():
    fmodel = FlorisModel(configuration=YAML_INPUT)
    fmodel.set(
        layout_x=[0.0, 0.0],
        layout_y=[0.0, 1000.0],
        wind_speeds=[8.0],
        wind_directions=[270.0],
        turbulence_intensities=[0.06],
        disable_turbines=np.array([[False, True]]),
    )
    fmodel.run()
    levels = fmodel.acoustic_results[0]
    assert np.isfinite(levels[0])
    assert levels[1] < levels[0] - 100.0


def test_acoustic_results_missing_parameters():
    fmodel = FlorisModel(configuration=YAML_INPUT)
    fmodel.set(turbine_type=["iea_15MW"], reference_wind_height=150.0)
    fmodel.run()
    with pytest.raises(ValueError, match="acoustics"):
        fmodel.acoustic_results


def test_calculate_acoustic_plane():
    fmodel = single_turbine_model()
    fmodel.run()
    level = fmodel.acoustic_results[0, 0]
    hub_height = fmodel.core.farm.hub_heights[0, 0]

    # 3 x 3 grid at hub height, with points at the reference distance from the hub
    plane = fmodel.calculate_acoustic_plane(
        height=hub_height,
        x_resolution=3,
        y_resolution=3,
        x_bounds=(-ACOUSTIC_REFERENCE_DISTANCE, ACOUSTIC_REFERENCE_DISTANCE),
        y_bounds=(-ACOUSTIC_REFERENCE_DISTANCE, ACOUSTIC_REFERENCE_DISTANCE),
    )
    df = plane.df
    assert len(df) == 9
    assert (df.v == 0).all() and (df.w == 0).all()

    def level_at(x, y):
        return df.u[(df.x1 == x) & (df.x2 == y)].item()

    # Upstream and downstream on the rotor axis: no spreading and no directivity loss
    np.testing.assert_allclose(level_at(-ACOUSTIC_REFERENCE_DISTANCE, 0.0), level)
    np.testing.assert_allclose(level_at(ACOUSTIC_REFERENCE_DISTANCE, 0.0), level)
    # In the rotor plane the dipole directivity removes the noise
    assert level_at(0.0, ACOUSTIC_REFERENCE_DISTANCE) < level - 100.0

    # Two identical turbines placed symmetrically give a symmetric noise map
    fmodel.set(layout_x=[0.0, 0.0], layout_y=[-1000.0, 1000.0])
    fmodel.run()
    plane = fmodel.calculate_acoustic_plane(
        height=0.0, x_resolution=3, y_resolution=3, x_bounds=(-500.0, 500.0),
        y_bounds=(-500.0, 500.0),
    )
    df = plane.df
    np.testing.assert_allclose(
        df.u[(df.x1 == -500.0) & (df.x2 == -500.0)].item(),
        df.u[(df.x1 == -500.0) & (df.x2 == 500.0)].item(),
    )
