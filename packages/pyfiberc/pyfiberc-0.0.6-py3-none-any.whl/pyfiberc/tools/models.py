from typing_extensions import Self, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from typing import Optional, List
from pycivil.EXAStructural.materials import ConcreteModel

from pyfiberc.materials import (
    TpAnalysis,
    TpValutation,
    LawCode,
    FiberConcrete as FiberConcreteMaterial,
    DuctilityClass
)

class Rows(BaseModel):
    value: List[float | str]

class LawParamsRules(BaseModel):
    name: str
    value: Union[str, float, List[Any]]

class FiberConcreteByLaw(BaseModel):
    lawParams: List[LawParamsRules] | None = None

class LawFiberConcrete(BaseModel):
    law: LawCode
    material: FiberConcreteByLaw

class FiberConcrete(BaseModel):
    """Modello Pydantic per gli attributi privati di FiberConcrete"""
    description: str = Field(default="", description="Descrizione del materiale")
    concrete: ConcreteModel = Field(default=ConcreteModel(), description="Calcestruzzo della matrice base")

    # Coefficienti parziali di sicurezza
    ycf_uls: float = Field(default=1.5, description="Coefficiente parziale calcestruzzo in trazione ULS")
    ycf_sls: float = Field(default=1.0, description="Coefficiente parziale calcestruzzo in trazione SLS")
    ycc_uls: float = Field(default=1.5, description="Coefficiente parziale calcestruzzo in compressione")
    yce: float = Field(default=1.2, description="Coefficiente parziale calcestruzzo Modulo elastico")

    strength_class: str = Field(default="", description="Classe di resistenza")
    ductility_class: Optional[DuctilityClass] = Field(default=None, description="Duttilità")
    no_crack_els: bool = Field(default=True, description="Duttilità")

    # Resistenze a trazione residue FRC
    fR1k: Optional[float] = Field(default=None, description="Resistenza residua FRC a CMOD=0.5mm [MPa]")
    fR3k: Optional[float] = Field(default=None, description="Resistenza residua FRC a CMOD=2.5mm [MPa]")

    # Deformazione ultima in trazione FRC
    efu: Optional[float] = Field(default=None, description="Deformazione ultima in trazione FRC [-]")

    # Tipo di Analisi
    tipo_analisi: List[TpAnalysis] = Field(default=[TpAnalysis.TP_SECTIONAL, TpAnalysis.TP_FEM], description="Tipo di analisi (sezionale o FEM)")

    # Parametri per analisi sezionale
    lcs: Optional[float] = Field(default=None, description="Lunghezza critica sezionale [mm]")

    # Parametri per analisi FEM
    d1: Optional[float] = Field(default=None, description="Parametro d1 per analisi FEM [mm]")
    d2: Optional[float] = Field(default=None, description="Parametro d2 per analisi FEM [mm]")
    d3: Optional[float] = Field(default=None, description="Parametro d3 per analisi FEM [mm]")

    # Normativa
    normativa: Optional[LawCode] = Field(default=None, description="Normativa di riferimento")

    # Parametri per LG C.S.LL.PP (2022)
    k0: Optional[float] = Field(default=None, description="Parametro k0 per LG C.S.LL.PP [-]")
    kg: Optional[float] = Field(default=None, description="Parametro kg per LG C.S.LL.PP [-]")

    # Parametri per Model Code - fib Bulletin83
    valutazione_precisa: TpValutation = Field(default=TpValutation.TP_ND, description="Tipo di valutazione per Model Code")
    k: Optional[float] = Field(default=None, description="Parametro k per Model Code [-]")

    model_config = ConfigDict(arbitrary_types_allowed = True, validate_assignment = True)

    @field_validator(
        'fR1k',
        'fR3k',
        'efu',
        'ycf_uls',
        'ycf_sls',
        'ycc_uls',
        'yce',
        'k',
        'k0',
        'kg',
        mode='before')
    @classmethod
    def validate_positive_values(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Resistenze, deformazioni e coefficienti di sicurezza devono essere positivi")
        return v

    @field_validator('lcs', 'd1', 'd2', 'd3', mode='before')
    @classmethod
    def validate_lengths(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Le lunghezze devono essere valori positivi")
        return v

    @model_validator(mode='after')
    def validate_tp_analisi(self) -> Self:
        if TpAnalysis.TP_SECTIONAL in self.tipo_analisi:
            if self.lcs is None:
                raise ValueError("lcs must be set")

        if TpAnalysis.TP_FEM in self.tipo_analisi:
            if self.d1 is None or self.d2 is None or self.d3 is None:
                raise ValueError("d1, d2 and d3 must be set with TP_FEM")

        if self.ductility_class is not None and self.strength_class == "":
            raise ValueError("ductility_class and strength_class must be both either assigne or not !!!")

        if self.ductility_class is None and self.strength_class != "":
            raise ValueError("ductility_class and strength_class must be both either assigne or not !!!")

        return self


def fromModel(model: FiberConcrete) -> FiberConcreteMaterial:
    """
    Crea un'istanza di FiberConcrete a partire dal modello Pydantic

    Args:
        model: Il modello Pydantic contenente i dati

    Returns:
        Istanza di FiberConcrete configurata con i parametri del modello
    """
    fiber_conc = FiberConcreteMaterial()
    fiber_conc.set_description(model.description)

    concrete = model.concrete.toMaterial()
    fiber_conc.set_concrete(concrete)

    if model.normativa is not None:
        fiber_conc.set_normativa(model.normativa)

    if model.ductility_class is not None and model.strength_class is not None:
        fiber_conc.set_by_law(model.strength_class, model.ductility_class)
    else:
        # Imposta le resistenze FRC
        fiber_conc.set_fR1k(model.fR1k)
        fiber_conc.set_fR3k(model.fR3k)

        # Imposta i parametri specifici per LG C.S.LL.PP (2022)
        if model.normativa == LawCode.CODE_ITA_LG2022 or model.normativa == LawCode.CODE_EC2_11_2023:
            fiber_conc.set_k0(model.k0)
            fiber_conc.set_kg(model.kg)

        # Imposta i parametri specifici per Model Code
        if model.normativa == LawCode.CODE_MODEL_CODE_10:
            fiber_conc.set_valutazione_precisa(model.valutazione_precisa)
            fiber_conc.set_k(model.k)

    fiber_conc.set_efu(model.efu)

    fiber_conc.set_no_crack_sls(model.no_crack_els)

    # Imposta i coefficienti di sicurezza
    fiber_conc.set_ycf_uls(model.ycf_uls)
    fiber_conc.set_ycf_sls(model.ycf_sls)
    fiber_conc.set_yc(model.ycc_uls)
    fiber_conc.set_yce(model.yce)

    # Imposta il tipo di analisi
    fiber_conc.set_tipo_analisi(model.tipo_analisi)

    # Imposta i parametri per analisi sezionale
    if TpAnalysis.TP_SECTIONAL in model.tipo_analisi:
        fiber_conc.set_lcs(model.lcs)

    # Imposta i parametri per analisi FEM
    if TpAnalysis.TP_FEM in model.tipo_analisi:
        fiber_conc.set_d1(model.d1)
        fiber_conc.set_d2(model.d2)
        fiber_conc.set_d3(model.d3)

    assert fiber_conc.is_valid_material()
    return fiber_conc


def toModel(fiber_conc: FiberConcreteMaterial) -> FiberConcrete:
    """
    Crea un modello Pydantic a partire da un'istanza di FiberConcrete

    Args:
        fiber_conc: Istanza di FiberConcrete

    Returns:
        Modello Pydantic popolato con i dati di FiberConcrete
    """
    # Estrai tutti i valori usando i getter
    concrete_model = ConcreteModel()
    concrete_model.fromMaterial(fiber_conc.get_concrete())
    model_data = {
        "description": fiber_conc.get_description(),
        "concrete": concrete_model,
        "ycf_uls": fiber_conc.get_ycf_uls(),
        "ycf_sls": fiber_conc.get_ycf_sls(),
        "yc": fiber_conc.get_yc(),
        "yce": fiber_conc.get_yce(),
        "fR1k": fiber_conc.get_fR1k(),
        "fR3k": fiber_conc.get_fR3k(),
        "efu": fiber_conc.get_efu(),
        "tipo_analisi": fiber_conc.get_tipo_analisi(),
        "lcs": fiber_conc.get_lcs(),
        "d1": fiber_conc.get_d1(),
        "d2": fiber_conc.get_d2(),
        "d3": fiber_conc.get_d3(),
        "normativa": fiber_conc.get_normativa(),
        "k0": fiber_conc.get_k0(),
        "kg": fiber_conc.get_kg(),
        "k": fiber_conc.get_k(),
        "valutazione_precisa": fiber_conc.get_valutazione_precisa(),
        "strength_class": fiber_conc.get_strength_class(),
        "ductility_class": fiber_conc.get_ductility_class(),
        "no_crack_els": fiber_conc.get_no_crack_sls()
    }

    # Crea il modello
    model = FiberConcrete(**model_data)

    return model

class FiberConcreteResources(BaseModel):
    lawMaterialsAndRules: List[LawFiberConcrete]
    fiberedConcreteDefault: FiberConcrete

def build_resources() -> FiberConcreteResources:
    res_data: dict = {"lawMaterialsAndRules": []}
    for law_key, props_vals in FiberConcreteMaterial.rules_table.items():
        props_data = []
        for props_key, props_val in props_vals.items():
            props_data.append({"name": props_key, "value": props_val})
        res_data["lawMaterialsAndRules"].append({"law": law_key, "material": {"lawParams": props_data}})

    frc_material = FiberConcreteMaterial()
    frc_material.set_normativa(LawCode.CODE_ITA_LG2022)
    frc_material.set_by_law("2.0", DuctilityClass.c)
    frc_material.set_lcs(300)
    frc_material.set_d1(300)
    frc_material.set_d2(300)
    frc_material.set_d3(300)
    res_data["fiberedConcreteDefault"] = toModel(frc_material)

    res = FiberConcreteResources(**res_data)
    return res