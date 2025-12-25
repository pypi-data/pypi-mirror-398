from .core import KIMVVTestDriver, override_call_method
from .EquilibriumCrystalStructure.test_driver.test_driver import TestDriver as __EquilibriumCrystalStructure
from .ElasticConstantsCrystal.test_driver.test_driver import TestDriver as __ElasticConstantsCrystal
from .CrystalStructureAndEnergyVsPressure.test_driver.test_driver import TestDriver as __CrystalStructureAndEnergyVsPressure
from .GroundStateCrystalStructure.test_driver.test_driver import TestDriver as __GroundStateCrystalStructure
from .VacancyFormationEnergyRelaxationVolumeCrystal.test_driver.test_driver import TestDriver as __VacancyFormationEnergyRelaxationVolumeCrystal


@override_call_method
class EquilibriumCrystalStructure(__EquilibriumCrystalStructure, KIMVVTestDriver):
    pass


@override_call_method
class ElasticConstantsCrystal(__ElasticConstantsCrystal, KIMVVTestDriver):
    pass


@override_call_method
class CrystalStructureAndEnergyVsPressure(__CrystalStructureAndEnergyVsPressure, KIMVVTestDriver):
    pass


@override_call_method
class GroundStateCrystalStructure(__GroundStateCrystalStructure, KIMVVTestDriver):
    pass


@override_call_method
class VacancyFormationEnergyRelaxationVolumeCrystal(__VacancyFormationEnergyRelaxationVolumeCrystal, KIMVVTestDriver):
    pass


__all__ = [
    "EquilibriumCrystalStructure",
    "ElasticConstantsCrystal",
    "CrystalStructureAndEnergyVsPressure",
    "GroundStateCrystalStructure",
    "VacancyFormationEnergyRelaxationVolumeCrystal",
]
