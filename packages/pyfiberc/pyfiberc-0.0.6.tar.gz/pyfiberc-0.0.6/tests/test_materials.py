from pydantic import ValidationError

import pytest
from pathlib import Path

from pycivil.EXAStructural.codes import Code, CodeEnum
from pycivil.EXAStructural.materials import Concrete


from pyfiberc.materials import FiberConcrete, TpAnalysis, LawCode, TpValutation, DuctilityClass
from pyfiberc.tools.models import (
    FiberConcrete as FiberConcreteModel,
    fromModel,
    toModel,
    build_resources
)

def test_instance_001(tmp_path: Path):
    frc = FiberConcrete()

    # description for material
    #
    assert frc.get_description() == ''
    frc.set_description('default material')
    assert frc.get_description() == 'default material'

    assert not frc.is_valid_material()

    # concrete is base of fibred material
    code_obj = Code(CodeEnum.NTC2018)
    concrete = Concrete()
    concrete.setByCode(code_obj, "C40/50")
    frc.set_concrete(concrete)

    assert not frc.is_valid_material()

    # set delle resistenze residue e deformazione ultima in trazione FRC
    frc.set_fR1k(4.0)
    frc.set_fR3k(3.60)
    frc.set_efu(0.01)

    assert not frc.is_valid_material()


    assert not frc.is_valid_material()

    frc.set_normativa(LawCode.CODE_ND)
    frc.print_concrete_properties()

    # set normativa FRC
    frc.set_normativa(LawCode.CODE_MODEL_CODE_10)
    frc.print_concrete_properties()
    with pytest.raises(ValueError):
        frc.set_k0(11)
    with pytest.raises(ValueError):
        frc.set_kg(11)

    frc.set_valutazione_precisa(TpValutation.TP_ND)
    assert not frc.is_valid_material()

    frc.set_valutazione_precisa(TpValutation.TP_ACTIVE)
    assert not frc.is_valid_material()

    frc.set_normativa(LawCode.CODE_ITA_LG2022)
    frc.print_concrete_properties()

    with pytest.raises(ValueError):
        frc.set_k0(11)
    frc.set_k0(1)
    assert not frc.is_valid_material()

    with pytest.raises(ValueError):
        frc.set_kg(11)
    frc.set_kg(1)
    assert not frc.is_valid_material()

    with pytest.raises(ValueError):
        frc.set_valutazione_precisa(TpValutation.TP_ACTIVE)

    frc.set_normativa(LawCode.CODE_ND)
    with pytest.raises(ValueError):
        frc.set_valutazione_precisa(TpValutation.TP_ACTIVE)

    # valori di default sono entrambe le analisi
    frc.set_lcs(400)

    with pytest.raises(ValueError):
        frc.set_tipo_analisi(None)

    # set tipo di analisi e lunghezza caratteristca o dimensione mesh
    frc.set_tipo_analisi([TpAnalysis.TP_FEM])
    with pytest.raises(ValueError):
        frc.set_lcs(400)

    assert not frc.is_valid_material()

    frc.set_d1(1)
    frc.set_d2(1)
    frc.set_d3(1)

    frc.set_tipo_analisi([TpAnalysis.TP_SECTIONAL])
    with pytest.raises(ValueError):
        frc.set_d1(1)
    with pytest.raises(ValueError):
        frc.set_d2(1)
    with pytest.raises(ValueError):
        frc.set_d3(1)

    assert not frc.is_valid_material()
    frc.set_lcs(400)
    assert frc.is_valid_material()


    # Visualizza tutti i parametri
    frc.print_concrete_properties()

    # Visualizza riassunto dei parametri
    frc.print_settings_summary()

    # Test __str__()
    print(frc)

    assert frc.get_strength_class() == ""

    assert frc.get_ductility_class() is None

    assert frc.get_no_crack_sls() == False
    frc.set_no_crack_sls(True)
    assert frc.get_no_crack_sls() == True


# Esempio di utilizzo completo
def test_validation_model_001(tmp_path: Path):
    """Esempio completo di conversione bidirezionale"""

    # Crea un modello Pydantic di esempio
    model_data = {"ycf_uls": 1.5, "ycf_sls": 1.0, "yc": 1.5, "yce": 1.2, "fR1k": 4.5, "fR3k": 3.8, "efu": 25.0,
                  "normativa": LawCode.CODE_ITA_LG2022, "k0": 0.8, "kg": 1.2, "tipo_analisi": [TpAnalysis.TP_FEM],
                  "lcs": None, "d1": None, "d2": None, "d3": None}

    with pytest.raises(ValidationError):
        FiberConcreteModel(**model_data)

    model_data = {"ycf_uls": 1.5, "ycf_sls": 1.0, "yc": 1.5, "yce": 1.2, "fR1k": 4.5, "fR3k": 3.8, "efu": 25.0,
                  "normativa": LawCode.CODE_ITA_LG2022, "k0": 0.8, "kg": 1.2, "tipo_analisi": [TpAnalysis.TP_SECTIONAL],
                  "lcs": None, "d1": None, "d2": None, "d3": None}

    with pytest.raises(ValidationError):
        FiberConcreteModel(**model_data)

    # Test negative values
    model_data = {"ycf_uls": 1.5, "ycf_sls": 1.0, "yc": 1.5, "yce": 1.2, "fR1k": -4.5, "fR3k": 3.8, "efu": 25.0,
                  "normativa": LawCode.CODE_ITA_LG2022, "k0": 0.8, "kg": 1.2, "tipo_analisi": [TpAnalysis.TP_FEM],
                  "lcs": None, "d1": 1, "d2": 1, "d3": 1}

    with pytest.raises(ValidationError):
        FiberConcreteModel(**model_data)

    model_data = {"ycf_uls": 1.5, "ycf_sls": 1.0, "yc": 1.5, "yce": 1.2, "fR1k": 4.5, "fR3k": 3.8, "efu": 25.0,
                  "normativa": LawCode.CODE_ITA_LG2022, "k0": 0.8, "kg": 1.2, "tipo_analisi": [TpAnalysis.TP_FEM],
                  "lcs": None, "d1": 1, "d2": -1, "d3": 1}

    with pytest.raises(ValidationError):
        FiberConcreteModel(**model_data)

    model_data = {"ycf_uls": 1.5, "ycf_sls": 1.0, "yc": 1.5, "yce": 1.2, "fR1k": 4.5, "fR3k": 3.8, "efu": 25.0,
                  "normativa": LawCode.CODE_ITA_LG2022, "k0": 0.8, "kg": 1.2, "tipo_analisi": [TpAnalysis.TP_FEM],
                  "lcs": None, "d1": 1, "d2": 1, "d3": 1}

    FiberConcreteModel(**model_data)

    model_data = {"ycf_uls": 1.5, "ycf_sls": 1.0, "yc": 1.5, "yce": 1.2, "fR1k": 4.5, "fR3k": 3.8, "efu": 25.0,
                  "normativa": LawCode.CODE_ITA_LG2022, "k0": 0.8, "kg": 1.2, "tipo_analisi": [TpAnalysis.TP_FEM],
                  "lcs": None, "d1": 1, "d2": 1, "d3": 1, "strength_class": "4.0"}

    with pytest.raises(ValidationError):
        FiberConcreteModel(**model_data)

    model_data = {"ycf_uls": 1.5, "ycf_sls": 1.0, "yc": 1.5, "yce": 1.2, "fR1k": 4.5, "fR3k": 3.8, "efu": 25.0,
                  "normativa": LawCode.CODE_ITA_LG2022, "k0": 0.8, "kg": 1.2, "tipo_analisi": [TpAnalysis.TP_FEM],
                  "lcs": None, "d1": 1, "d2": 1, "d3": 1, "ductility_class": "e"}

    with pytest.raises(ValidationError):
        FiberConcreteModel(**model_data)

    model_data = {"ycf_uls": 1.5, "ycf_sls": 1.0, "yc": 1.5, "yce": 1.2, "fR1k": 4.5, "fR3k": 3.8, "efu": 25.0,
                  "normativa": LawCode.CODE_ITA_LG2022, "k0": 0.8, "kg": 1.2, "tipo_analisi": [TpAnalysis.TP_FEM],
                  "lcs": None, "d1": 1, "d2": 1, "d3": 1, "strength_class": "4.0", "ductility_class": "e"}

    FiberConcreteModel(**model_data)

    # "ductility_class": fiber_conc.get_ductility_class(),
    # "no_crack_els": fiber_conc.get_no_crack_sls()

def test_validation_model_002(tmp_path: Path):
    model_data = {"ycf_uls": 1.5, "ycf_sls": 1.0, "yc": 1.5, "yce": 1.2, "fR1k": 4.5, "fR3k": 3.8, "efu": 25.0,
                  "normativa": LawCode.CODE_ITA_LG2022, "k0": 0.8, "kg": 1.2, "tipo_analisi": [TpAnalysis.TP_FEM],
                  "lcs": None, "d1": 1, "d2": 1, "d3": 1}

    model = FiberConcreteModel(**model_data)

    # Conversione da modello a FiberConcrete
    fiber_conc = fromModel(model)

    # Conversione da FiberConcrete a modello
    converted_model = toModel(fiber_conc)

    fiber_conc2 = fromModel(converted_model)
    converted_model2 = toModel(fiber_conc2)
    assert converted_model.fR1k == converted_model2.fR1k

def test_validation_model_003(tmp_path: Path):
    model_data = {"ycf_uls": 1.5, "ycf_sls": 1.0, "yc": 1.5, "yce": 1.2, "fR1k": 4.5, "fR3k": 3.8, "efu": 25.0,
                  "normativa": LawCode.CODE_ITA_LG2022, "k0": 0.8, "kg": 1.2, "tipo_analisi": [TpAnalysis.TP_SECTIONAL],
                  "lcs": 1, "d1": None, "d2": None, "d3": None}

    model = FiberConcreteModel(**model_data)

    # Conversione da modello a FiberConcrete
    fiber_conc = fromModel(model)

    # Conversione da FiberConcrete a modello
    converted_model = toModel(fiber_conc)

    fiber_conc2 = fromModel(converted_model)
    converted_model2 = toModel(fiber_conc2)
    assert converted_model.fR1k == converted_model2.fR1k

def test_validation_model_004(tmp_path: Path):
    model_data = {"ycf_uls": 1.5, "ycf_sls": 1.0, "yc": 1.5, "yce": 1.2, "fR1k": 4.5, "fR3k": 3.8, "efu": 25.0,
                  "normativa": LawCode.CODE_MODEL_CODE_10, "k0": 0.8, "kg": 1.2, "tipo_analisi": [TpAnalysis.TP_SECTIONAL],
                  "lcs": 1, "d1": None, "d2": None, "d3": None, "k": 1.0, "valutazione_precisa": TpValutation.TP_INACTIVE}

    model = FiberConcreteModel(**model_data)

    # Conversione da modello a FiberConcrete
    fiber_conc = fromModel(model)

    # Conversione da FiberConcrete a modello
    converted_model = toModel(fiber_conc)

    fiber_conc2 = fromModel(converted_model)
    converted_model2 = toModel(fiber_conc2)
    assert converted_model.fR1k == converted_model2.fR1k

def test_validation_model_005(tmp_path: Path):
    model_data = {"ycf_uls": 1.5, "ycf_sls": 1.0, "yc": 1.5, "yce": 1.2, "fR1k": 4.5, "fR3k": 3.8, "efu": 25.0,
                  "normativa": LawCode.CODE_MODEL_CODE_10, "k0": 0.8, "kg": 1.2, "tipo_analisi": [TpAnalysis.TP_SECTIONAL],
                  "lcs": 1, "d1": None, "d2": None, "d3": None, "k": 1.0, "strength_class": "4.0", "ductility_class": "e"}

    model = FiberConcreteModel(**model_data)

    # Conversione da modello a FiberConcrete
    fiber_conc = fromModel(model)

    # Conversione da FiberConcrete a modello
    converted_model = toModel(fiber_conc)

    fiber_conc2 = fromModel(converted_model)
    converted_model2 = toModel(fiber_conc2)
    assert converted_model.fR1k == converted_model2.fR1k
    assert converted_model.fR3k == converted_model2.fR3k
    assert converted_model.fR1k == 4.0
    assert converted_model.fR3k == 5.2

def test_validation_model_006(tmp_path: Path):
    model_data = {"ycf_uls": 1.5, "ycf_sls": 1.0, "yc": 1.5, "yce": 1.2, "fR1k": 4.5, "fR3k": 3.8, "efu": 25.0,
                  "normativa": LawCode.CODE_MODEL_CODE_10, "k0": 0.8, "kg": 1.2, "tipo_analisi": [TpAnalysis.TP_SECTIONAL],
                  "lcs": 1, "d1": None, "d2": None, "d3": None, "k": 1.0, "strength_class": "4.4", "ductility_class": "e"}

    FiberConcreteModel(**model_data)

    model_data["strength_class"] = "4.0"
    model_data["ductility_class"] = "r"

    with pytest.raises(ValidationError):
        FiberConcreteModel(**model_data)



def test_concrete_compression_001(tmp_path: Path):
    frc = FiberConcrete()

    # set delle resistenze residue e deformazione ultima in trazione FRC
    frc.set_fR1k(4.0)
    frc.set_fR3k(3.60)
    frc.set_efu(0.01)

    code_obj = Code(CodeEnum.NTC2018)
    concrete = Concrete()

    # Default value are for Concrete class
    frc.set_concrete(concrete)
    frc.set_concrete(concrete)
    assert frc.cal_ecu1() is None
    assert frc.cal_ec1() is None
    assert frc.cal_k() is None

    # Test for low fck
    concrete.setByCode(code_obj, "C50/60")
    assert frc.cal_ecu1() == 3.5 / 1000
    assert frc.cal_ec1() != 0.0028

    # Test for hight fck
    concrete.setByCode(code_obj, "C70/85")
    assert frc.cal_ec1() != 0.0028
    concrete.setByCode(code_obj, "C80/95")
    assert frc.cal_ec1() == 0.0028
    concrete.setByCode(code_obj, "C90/105")
    assert frc.cal_ec1() == 0.0028

def test_code_EC2_MODEL_CODE_001():
    frc = FiberConcrete()
    frc.set_normativa(LawCode.CODE_EC2_11_2023)
    assert frc.get_k() is None

    with pytest.raises(ValueError):
        frc.set_k(1)

    frc.set_normativa(LawCode.CODE_MODEL_CODE_10)
    with pytest.raises(ValueError):
        frc.set_k(0)

    with pytest.raises(ValueError):
        frc.set_k(-1)

def test_law_specific_properties_001():
    frc = FiberConcrete()

    with pytest.raises(ValueError):
        frc.set_normativa(LawCode.CODE_ND)
        frc.set_by_law("-3.0", DuctilityClass.a)

    with pytest.raises(ValueError):
        frc.set_normativa(LawCode.CODE_ITA_LG2022)
        frc.set_by_law("-3.0", DuctilityClass.a)

    frc.set_normativa(LawCode.CODE_ITA_LG2022)
    frc.set_by_law( "3.0", DuctilityClass.a)

    frc.set_normativa(LawCode.CODE_MODEL_CODE_10)
    frc.set_by_law( "3.0", DuctilityClass.a)

    frc.set_normativa(LawCode.CODE_EC2_11_2023)
    frc.set_by_law( "3.0", DuctilityClass.a)

def test_build_resources_001():
    res = build_resources()
    #TODO: inspect more properties and not regression
    assert len(res.lawMaterialsAndRules) == 3


