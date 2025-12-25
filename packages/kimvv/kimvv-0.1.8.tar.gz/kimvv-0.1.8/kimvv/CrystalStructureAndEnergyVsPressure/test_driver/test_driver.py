import os
from math import exp, floor, log
from typing import Dict, List, Optional, Tuple

import numpy as np
from ase.atoms import Atoms
from ase.data import atomic_masses
from ase.filters import FrechetCellFilter, UnitCellFilter
from ase.optimize.lbfgs import LBFGSLineSearch
from ase.optimize.optimize import Optimizer
from ase.units import GPa, kg, m
from kim_tools import AFLOW, SingleCrystalTestDriver
from kim_tools.symmetry_util.core import FixProvidedSymmetry
from matplotlib import pyplot as plt

CONFIG_TPL = "instance_{prop_idx}_{p_gpa}_GPa.poscar"


class StopScanError(Exception):
    pass


class VolumeMockConstraint:
    """
    "Constraint" that just raises an error if volume is exceeded.
    This is better than using a stopping criterion in an irun loop, because
    it allows stopping in the middle of a linesearch
    """

    def __init__(self, min_volume, max_volume):
        self.min_volume = min_volume
        self.max_volume = max_volume

    def adjust_positions(self, atoms, newpositions):
        pass

    def adjust_forces(self, atoms, forces):
        pass

    def adjust_cell(self, atoms, cell):
        if cell.volume > self.max_volume or cell.volume < self.min_volume:
            raise StopScanError(
                "Volume exceeded prescribed range, stopping pressure scan."
            )


class TestDriver(SingleCrystalTestDriver):
    def _minimize_volume_limited(
        self,
        atoms: Atoms,
        scalar_pressure: float,
    ) -> bool:
        """
        Use LBFGSLineSearch (default) to Minimize cell energy with respect to cell
        shape and internal atom positions, with parameters inherited
        from the class instance.

        LBFGSLineSearch convergence behavior is as follows:

        - The solver returns True if it is able to converge within the optimizer
        iteration limits (which can be changed by the ``steps`` argument passed
        to ``run``), otherwise it returns False.
        - The solver raises an exception in situations where the line search cannot
        improve the solution, typically due to an incompatibility between the
        potential's values for energy, forces, and/or stress.

        This routine attempts to minimizes the energy until the force and stress
        reduce below specified tolerances given a provided limit on the number of
        allowed steps. The code returns when convergence is achieved or no
        further progress can be made, either due to reaching the iteration step
        limit, or a stalled minimization due to line search failures.

        Args:
            atoms:
                Atomic configuration to be minimized.
            scalar_pressure:
                The scalar pressure to apply

        Returns:
            Whether the minimization succeeded
        """
        atoms_wrapped = self.cell_filter(
            atoms, scalar_pressure=scalar_pressure, **self.min_flt_kwargs
        )
        opt = self.min_algorithm(atoms_wrapped, logfile="-", **self.min_opt_kwargs)
        try:
            converged = opt.run(fmax=self.min_fmax, steps=self.min_steps)
            iteration_limits_reached = not converged
            minimization_stalled = False
        except RuntimeError as e:
            if str(e) == "LineSearch failed!":
                minimization_stalled = True
                iteration_limits_reached = False
                print(
                    "LineSearch failed."
                    "Assuming it is non-fatal and accepting result with disclaimer."
                )
            else:
                raise e

        print(
            "Minimization "
            + (
                "stalled"
                if minimization_stalled
                else "stopped" if iteration_limits_reached else "converged"
            )
            + " after "
            + (
                ("hitting the maximum of " + str(self.min_steps))
                if iteration_limits_reached
                else str(opt.nsteps)
            )
            + " steps."
        )

        if minimization_stalled or iteration_limits_reached:
            print("Final forces:")
            print(atoms.get_forces())
            print("Final stress:")
            print(atoms.get_stress())
            return False
        else:
            return True

    def _do_scan(self, backward: bool) -> Tuple[
        List[float],
        List[float],
        List[float],
        List[float],
        List[float],
        List[float],
        List[float],
        List[List[float]],
    ]:
        """
        Backward: linear scan from 0 to -self.max_steps
        Forward: exp scan from 0 to max_steps, with the pressure being
        exp(i*self.exp_step) * self.pressure_step_gpa
        """
        binding_potential_energy_per_atom = []
        binding_potential_energy_per_formula = []
        volume_per_atom = []
        volume_per_formula = []
        density_kg_m3 = []
        pressure_gpa = []
        a = []
        parameter_values = []
        if backward:
            iterrange = reversed(range(-self.max_pressure_steps, 1))
        else:
            iterrange = range(self.max_pressure_steps)

        # Get original atoms
        # Could use self._get_atoms() but no reason
        # to call AFLOW every time
        atoms = self.original_atoms.copy()
        atoms.calc = self._calc
        sgnum = self.get_nominal_space_group_number()
        atoms.set_constraint(
            [
                FixProvidedSymmetry(atoms, sgnum),
                VolumeMockConstraint(self.min_volume, self.max_volume),
            ]
        )
        num_atoms = len(atoms)
        num_atoms_in_formula = sum(self.get_nominal_stoichiometry())
        prototype_label = self.get_nominal_prototype_label()
        aflow = AFLOW()
        for i in iterrange:
            if backward:
                current_pressure_gpa = i * self.pressure_step_gpa
            else:
                current_pressure_gpa = exp(i * self.exp_step) * self.pressure_step_gpa
            print(f"\nPressure: {current_pressure_gpa} GPa\n")
            current_pressure = current_pressure_gpa * GPa
            try:
                # Relax with fixed pressure
                if not self._minimize_volume_limited(atoms, current_pressure):
                    if self.disclaimer is None:
                        self.disclaimer = (
                            "Relaxation failed to reach force tolerance of "
                            f"{self.min_fmax} eV/angstrom at "
                            f"{current_pressure_gpa} GPa"
                        )
                    else:
                        self.disclaimer += f", {current_pressure_gpa} GPa"
                # redetect current crystal structure first, as if this fails we do not
                # report anything. We need this to write the file in the correct
                # orientation later
                curr_param_values = aflow.solve_for_params_of_known_prototype(
                    atoms=atoms,
                    prototype_label=prototype_label,
                    match_library_proto=False,
                )
                # get other quantities
                potential_energy = atoms.get_potential_energy()
                volume = atoms.get_volume()

                # write config
                # property instances are 1-based, but we have not initialized the
                # newest one yet
                prop_idx = len(self.property_instances) + 1
                filename = os.path.join(
                    "output",
                    CONFIG_TPL.format(p_gpa=current_pressure_gpa, prop_idx=prop_idx),
                )

                # Regenerate poscar from parameter values instead of
                # just self.write_atoms -- otherwise they won't be in
                # standard orientation
                aflow.write_poscar_from_prototype(
                    prototype_label=prototype_label,
                    species=self.get_nominal_stoichiometric_species(),
                    parameter_values=curr_param_values,
                    output_file=filename,
                )

                # report things
                current_volume_per_atom = volume / num_atoms
                current_binding_potential_energy_per_atom = potential_energy / num_atoms
                volume_per_atom.append(current_volume_per_atom)
                volume_per_formula.append(
                    current_volume_per_atom * num_atoms_in_formula
                )
                # compute density
                mass = 0.0
                for atomic_number in atoms.get_atomic_numbers():
                    mass += atomic_masses[atomic_number]
                mass_kg = mass / kg
                volume_m3 = volume / m**3
                density_kg_m3.append(mass_kg / volume_m3)
                binding_potential_energy_per_atom.append(
                    current_binding_potential_energy_per_atom
                )
                binding_potential_energy_per_formula.append(
                    current_binding_potential_energy_per_atom * num_atoms_in_formula
                )
                a.append(curr_param_values[0])
                parameter_values.append(curr_param_values[1:])
                pressure_gpa.append(current_pressure_gpa)
            except Exception as e:
                print(
                    "Failed to get energy or crystal structure "
                    f"at pressure {current_pressure_gpa} GPa. Exception:\n{repr(e)}"
                )
                # Don't keep trying larger pressures after one failure
                break
        return (
            binding_potential_energy_per_atom,
            binding_potential_energy_per_formula,
            volume_per_atom,
            volume_per_formula,
            density_kg_m3,
            pressure_gpa,
            a,
            parameter_values,
        )

    def _plot(
        self,
        ydata: List[float],
        title: str,
        ylabel: str,
        filename: str,
        keyname: str,
        y_logthresh: Optional[float] = None,
    ):
        min_press = min(self.pressure_gpa)
        max_press = max(self.pressure_gpa)
        min_press_range = min(abs(min_press), abs(max_press))
        fig, ax = plt.subplots()
        ax.plot(self.pressure_gpa, ydata, "-", color="k")
        fig.suptitle(title)
        # If pressure range is highly asymmetric, do symlog scale
        if max(abs(min_press), abs(max_press)) > min_press_range * 10:
            ax.set_xscale("symlog", linthresh=min_press_range)

            # Take care of major ticks
            ax.xaxis.get_major_locator().set_params(subs=[1, -1])
            major_ticks = list(ax.get_xticks())
            oldlabels = ax.get_xticklabels()
            newlabels = []
            closest_lin_decade = round(log(min_press_range, 10))
            del_label_locs = []
            if closest_lin_decade < 0:
                # just in case, delete 3 decades smaller. Won't hurt anything
                # Don't delete too many though, or you'll get np.allclose to zero
                irange = range(closest_lin_decade - 3, closest_lin_decade)
            else:
                irange = range(0, closest_lin_decade)
            for i in irange:
                del_label_locs += [-(10**i), 10**i]
            # Hide labels that are too crowded
            for tick, label in zip(major_ticks, oldlabels):
                if any([np.isclose(tick, del_loc) for del_loc in del_label_locs]):
                    newlabels.append("")
                else:
                    newlabels.append(label)
            ax.set_xticks(major_ticks, newlabels)

            # Take care of minor ticks
            ax.xaxis.get_minor_locator().set_params(
                subs=list(range(-9, 0)) + list(range(1, 10))
            )
            oldminorticks = list(ax.get_xticks(minor=True))
            newminorticks = []
            tickstep = 10 ** (closest_lin_decade - 1)
            for i in range(
                -floor(min_press_range / tickstep),
                floor(min_press_range / tickstep) + 1,
            ):
                if not any(
                    [np.isclose(i * tickstep, old_tick) for old_tick in oldminorticks]
                ):
                    newminorticks.append(i * tickstep)
            ax.set_xticks(oldminorticks + newminorticks, minor=True)
            ax.axvspan(min_press_range, max_press, color="b", alpha=0.18)
            pad_x = 20.0
            ax.text(
                0.95,
                -0.08,
                "(Log scale)",
                verticalalignment="top",
                horizontalalignment="right",
                transform=ax.transAxes,
                fontsize="small",
            )
            ax.text(
                0.05,
                -0.08,
                "(Linear scale)",
                verticalalignment="top",
                horizontalalignment="left",
                transform=ax.transAxes,
                fontsize="small",
            )
        else:
            pad_x = 4.0

        if y_logthresh is not None:
            # If somehow we get negative numbers that are bigger
            # than y_logthresh, we want to extend the linear region
            # to them so we don't leave the linear region at the
            # bottom of the graph
            y_logthresh = max(-min(ydata), y_logthresh)
            ax.set_yscale("symlog", linthresh=y_logthresh)

            # Take care of major ticks
            ax.yaxis.get_major_locator().set_params(subs=[1, -1])
            major_ticks = list(ax.get_yticks())
            oldlabels = ax.get_yticklabels()
            newlabels = []
            closest_lin_decade = round(log(y_logthresh, 10))
            del_label_locs = []
            if closest_lin_decade < 0:
                # just in case, delete 3 decades smaller. Won't hurt anything
                # Don't delete too many though, or you'll get np.allclose to zero
                irange = range(closest_lin_decade - 3, closest_lin_decade)
            else:
                irange = range(0, closest_lin_decade)
            for i in irange:
                del_label_locs += [-(10**i), 10**i]
            # Hide labels that are too crowded
            for tick, label in zip(major_ticks, oldlabels):
                if any([np.isclose(tick, del_loc) for del_loc in del_label_locs]):
                    newlabels.append("")
                else:
                    newlabels.append(label)
            ax.set_yticks(major_ticks, newlabels)

            # Take care of minor ticks
            ax.yaxis.get_minor_locator().set_params(
                subs=list(range(-9, 0)) + list(range(1, 10))
            )
            oldminorticks = list(ax.get_yticks(minor=True))
            newminorticks = []
            tickstep = 10 ** (closest_lin_decade - 1)
            for i in range(
                -floor(y_logthresh / tickstep),
                floor(y_logthresh / tickstep) + 1,
            ):
                if not any(
                    [np.isclose(i * tickstep, old_tick) for old_tick in oldminorticks]
                ):
                    newminorticks.append(i * tickstep)
            ax.set_yticks(oldminorticks + newminorticks, minor=True)
            ax.axhspan(min(ydata), y_logthresh, color="g", alpha=0.18)
            pad_y = 24.0
            ax.text(
                -0.1,
                0.95,
                "(Log scale)",
                verticalalignment="top",
                horizontalalignment="right",
                transform=ax.transAxes,
                fontsize="small",
                rotation="vertical",
            )
            ax.text(
                -0.1,
                0.05,
                "(Linear scale)",
                verticalalignment="bottom",
                horizontalalignment="right",
                transform=ax.transAxes,
                fontsize="small",
                rotation="vertical",
            )
            ax.set_ylim(min(ydata), max(ydata))
        else:
            # If we have an all-linear scale, and including
            # zero in the won't squish the data too much
            # (by less than half), then include zero
            if min(ydata) > 0 and min(ydata) < max(ydata) / 2:
                ax.set_ylim(0, max(ydata))
            else:
                ax.set_ylim(min(ydata), max(ydata))
            pad_y = 4.0
        ax.set_xlim(min_press, max_press)
        ax.set_xlabel("Pressure (GPa)", labelpad=pad_x)
        ax.set_ylabel(ylabel, labelpad=pad_y)
        plt.savefig(filename, bbox_inches="tight")
        self._add_file_to_current_property_instance(keyname, filename)

    def _calculate(
        self,
        pressure_step_gpa: float = 0.5,
        min_fractional_volume: float = 0.25,
        max_fractional_volume: float = 4,
        max_pressure_steps: int = 1000,
        exp_step: float = log(2) / 6,
        min_fmax: float = 1e-5,
        min_steps: int = 200,
        min_algorithm: type[Optimizer] = LBFGSLineSearch,
        cell_filter: type[UnitCellFilter] = FrechetCellFilter,
        min_opt_kwargs: Dict = {},
        min_flt_kwargs: Dict = {},
        **kwargs,
    ) -> None:
        """
        Computes the energy and (generally anisotropic) crystal structure as a function
        of applied hydrostatic pressure. Note that reaching either maximum or minimum
        requested fractional volume is not guaranteed, as the computation may fail
        before then (e.g. due to neighbor list overflow). All arguments are optional,
        and have reasonable defaults that should work for most materials.

        Args:
            pressure_step_gpa:
                pressure step
            min_fractional_volume:
                Stop the pressure scan if the system gets below this volume
            max_fractional_volume:
                Stop the pressure scan if the system gets above this volume
            max_pressure_steps:
                A hard limit on the maximum steps if the volume limits are
                not reached somehow
            exp_step:
                The compression scan grows exponentially,
                p=exp(i*exp_step)*pressure_step_gpa.
            min_fmax:
                The force tolerance used for minimization
            min_steps:
                The step limit for minimization
            min_algorithm:
                The ASE Optimizer class type to use for minimization
            cell_filter:
                The ASE UnitCellFilter class type to use for minimization
            min_opt_kwargs:
                A dictionary of keyword arguments to pass to the optimizer
            min_flt_kwargs:
                A dictionary of keyword arguments to pass to the filter
                in addition to the scalar_pressure argument
        """
        if min_fractional_volume > 1.0:
            raise RuntimeError(
                "Minimum fractional volume requested must be less than 1"
            )
        if max_fractional_volume < 1.0:
            raise RuntimeError(
                "Maximum fractional volume requested must be greater than 1"
            )
        self.pressure_step_gpa = pressure_step_gpa
        self.original_atoms = self._get_atoms()
        original_volume = self.original_atoms.get_volume()
        self.min_volume = original_volume * min_fractional_volume
        self.max_volume = original_volume * max_fractional_volume
        self.max_pressure_steps = max_pressure_steps
        self.exp_step = exp_step
        self.min_fmax = min_fmax
        self.min_steps = min_steps
        self.min_algorithm = min_algorithm
        self.cell_filter = cell_filter
        self.min_opt_kwargs = min_opt_kwargs
        self.min_flt_kwargs = min_flt_kwargs

        self.disclaimer = None

        print("\nPerforming energy scan...\n")

        # Forward scan
        (
            binding_potential_energy_per_atom,
            binding_potential_energy_per_formula,
            volume_per_atom,
            volume_per_formula,
            density_kg_m3,
            self.pressure_gpa,
            a,
            parameter_values,
        ) = self._do_scan(backward=False)

        max_pe_peratom_compr = max(binding_potential_energy_per_atom)

        # Backward scan
        (
            binding_potential_energy_per_atom_back,
            binding_potential_energy_per_formula_back,
            volume_per_atom_back,
            volume_per_formula_back,
            density_kg_m3_back,
            pressure_gpa_back,
            a_back,
            parameter_values_back,
        ) = self._do_scan(backward=True)

        max_pe_peratom_vacu = max(binding_potential_energy_per_atom_back)
        pe_peratom_eqbm = binding_potential_energy_per_atom_back[0]
        rel_max_pe_peratom_compr = max_pe_peratom_compr - pe_peratom_eqbm
        rel_max_pe_peratom_vacu = max_pe_peratom_vacu - pe_peratom_eqbm

        binding_potential_energy_per_atom = (
            list(reversed(binding_potential_energy_per_atom_back))
            + binding_potential_energy_per_atom
        )
        binding_potential_energy_per_formula = (
            list(reversed(binding_potential_energy_per_formula_back))
            + binding_potential_energy_per_formula
        )
        volume_per_atom = list(reversed(volume_per_atom_back)) + volume_per_atom
        volume_per_formula = (
            list(reversed(volume_per_formula_back)) + volume_per_formula
        )
        density_kg_m3 = list(reversed(density_kg_m3_back)) + density_kg_m3
        self.pressure_gpa = list(reversed(pressure_gpa_back)) + self.pressure_gpa
        a = list(reversed(a_back)) + a
        parameter_values = list(reversed(parameter_values_back)) + parameter_values

        assert len(binding_potential_energy_per_atom) == len(self.pressure_gpa)
        assert len(binding_potential_energy_per_formula) == len(self.pressure_gpa)
        assert len(volume_per_atom) == len(self.pressure_gpa)
        assert len(volume_per_formula) == len(self.pressure_gpa)
        assert len(density_kg_m3) == len(self.pressure_gpa)
        assert len(a) == len(self.pressure_gpa)
        assert len(parameter_values) == len(self.pressure_gpa)

        # Infer file names

        # Now it is time to write the output.
        parameter_names = self.get_nominal_parameter_names()
        if parameter_names is None:
            parameter_names = []

        self._add_property_instance_and_common_crystal_genome_keys(
            property_name=(
                "energy-and-crystal-structure-vs-hydrostatic-pressure-relation"
            ),
            write_stress=False,
            write_temp=False,
            disclaimer=self.disclaimer,
            omit_keys=[
                # Crystal structures are arrays due to the scan
                "a",
                "parameter-values",
                "coordinates-file",
                "coordinates-file-conventional",
            ],
        )
        self._add_key_to_current_property_instance(
            "volume-per-atom", volume_per_atom, unit="angstrom^3"
        )
        self._add_key_to_current_property_instance(
            "volume-per-formula", volume_per_formula, unit="angstrom^3"
        )
        self._add_key_to_current_property_instance(
            "mass-density", density_kg_m3, unit="kg/m^3"
        )
        self._add_key_to_current_property_instance(
            "binding-potential-energy-per-atom",
            binding_potential_energy_per_atom,
            unit="eV",
        )
        self._add_key_to_current_property_instance(
            "binding-potential-energy-per-formula",
            binding_potential_energy_per_formula,
            unit="eV",
        )
        self._add_key_to_current_property_instance("a", a, unit="angstrom")
        if len(parameter_names) != 0:
            self._add_key_to_current_property_instance(
                "parameter-values",
                parameter_values,
            )
        self._add_key_to_current_property_instance(
            "pressure", self.pressure_gpa, unit="GPa"
        )

        # 1-based, and we have already created the current prop instance
        prop_idx = len(self.property_instances)
        coordinates_file = []
        # Infer names of saved files
        for p_gpa in self.pressure_gpa:
            filename = CONFIG_TPL.format(p_gpa=p_gpa, prop_idx=prop_idx)
            assert os.path.isfile(os.path.join("output", filename))
            coordinates_file.append(filename)

        self._add_key_to_current_property_instance("coordinates-file", coordinates_file)
        # Plots

        # Energy
        # If one arm of the energy curve is much higher than the other, we should do
        # a symlog scale
        if rel_max_pe_peratom_compr > 10 * rel_max_pe_peratom_vacu:
            # Linear scale > 1 eV loses detail
            rel_pe_peratom_logthresh = min(rel_max_pe_peratom_vacu, 1)
        elif rel_max_pe_peratom_vacu > 10 * rel_max_pe_peratom_compr:
            # Linear scale > 1 eV loses detail
            rel_pe_peratom_logthresh = min(rel_max_pe_peratom_compr, 1)
        else:
            rel_pe_peratom_logthresh = None

        self._plot(
            ydata=np.asarray(binding_potential_energy_per_atom) - pe_peratom_eqbm,
            title=(
                "Binding potential energy per atom\n"
                "as a function of applied hydrostatic pressure"
            ),
            ylabel=f"Energy relative to {pe_peratom_eqbm:.3f} (eV/atom)",
            filename="eplot.svg",
            keyname="binding-potential-energy-per-atom-vs-pressure-curve",
            y_logthresh=rel_pe_peratom_logthresh,
        )

        # Volume
        self._plot(
            ydata=volume_per_atom,
            title="Volume per atom as a function of applied hydrostatic pressure",
            ylabel="Volume (angstrom\u00b3/atom)",
            filename="vplot.svg",
            keyname="volume-per-atom-vs-pressure-curve",
        )

        # Density
        self._plot(
            ydata=density_kg_m3,
            title="Mass density as a function of applied hydrostatic pressure",
            ylabel="Density (kg/m\u00b3)",
            filename="rhoplot.svg",
            keyname="density-vs-pressure-curve",
        )

        # a
        A_IT = r"$a$"
        self._plot(
            ydata=a,
            title=(
                f"Lattice parameter {A_IT} "
                "as a function of applied hydrostatic pressure"
            ),
            ylabel=f"{A_IT} (angstrom)",
            filename="aplot.svg",
            keyname="a-vs-pressure-curve",
        )
        # Other parameter_values
        # Convert parameter_values to numpy array so we can get slices
        parameter_values = np.asarray(parameter_values)

        B_IT = r"$b$"
        C_IT = r"$c$"

        tex_map = {
            "b/a": f"{B_IT}/{A_IT}",
            "c/a": f"{C_IT}/{A_IT}",
            "alpha": r"$\alpha$",
            "beta": r"$\beta$",
            "gamma": r"$\gamma$",
        }

        for i, param_name in enumerate(parameter_names):
            if (
                param_name.startswith("x")
                or param_name.startswith("y")
                or param_name.startswith("z")
            ):
                break  # not continue, if we are here, we are done
            param_valu_arr = parameter_values[:, i]
            nice_name = param_name.replace("/", "-over-")
            filename = f"{nice_name}plot.svg"
            keyname = f"{nice_name}-vs-pressure-curve"
            self._plot(
                ydata=param_valu_arr,
                title=(
                    f"Lattice parameter {tex_map[param_name]} as a function of "
                    "applied hydrostatic pressure"
                ),
                ylabel=tex_map[param_name],
                filename=filename,
                keyname=keyname,
            )
