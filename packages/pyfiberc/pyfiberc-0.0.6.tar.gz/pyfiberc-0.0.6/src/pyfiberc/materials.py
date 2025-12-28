from typing import List
from pycivil.EXAStructural.materials import Concrete
from enum import Enum

class LawCode(str, Enum):
    CODE_ITA_LG2022 = "ITA_LG2022"
    CODE_MODEL_CODE_10 = "MODEL_CODE_10"
    CODE_EC2_11_2023 = "EC2_11_2023"
    CODE_ND = "CODE_ND"

class TpAnalysis(str, Enum):
    TP_SECTIONAL = "SECTIONAL"
    TP_FEM = "FEM"

class TpValutation(str, Enum):
    TP_ACTIVE = "ACTIVE"
    TP_INACTIVE = "INACTIVE"
    TP_ND = "NOT_DEFINED"

class DuctilityClass(str, Enum):
    a = "a"
    b = "b"
    c = "c"
    d = "d"
    e = "e"

class FiberConcrete:
    rules_table = {
        LawCode.CODE_ITA_LG2022: {
            "frc_tab_column_names": ["ductility class", "1.0", "1.5", "2.0", "2.5", "3.0", "4.0", "5.0", "6.0", "8.0", "10.0", "12.0", "14.0"],
            "frc_tab_column_names_rule": "Tabella 1 pg 6",
            "frc_tab_rows": [
                ["a", 0.5, 0.75, 1.00, 1.25, 1.50, 2.00, 2.50, 3.00, 4.00, 5.00, 6.00, 7.00],
                ["b", 0.70, 1.05, 1.40, 1.75, 2.10, 2.80, 3.50, 4.20, 5.60, 7.00, 8.40, 9.80],
                ["c", 0.90, 1.35, 1.80, 2.25, 2.70, 3.60, 4.50, 5.40, 7.20, 9.00, 10.80, 12.60],
                ["d", 1.10, 1.65, 2.20, 2.75, 3.30, 4.40, 5.50, 6.60, 8.80, 11.00, 13.20, 15.40],
                ["e", 1.30, 1.95, 2.60, 3.25, 3.90, 5.20, 6.50, 7.80, 10.40, 13.00, 15.60, 18.20],
            ],
            "frc_tab_rows_rule": "Tabella 1 pg 6",
            "k0_min": 0.27,
            "k0_min_rule": "Tabella A1.1 pg 37 per pareti verticali, zona centrale, Trasversale, alto",
            "k0_max": 1.70,
            "k0_max_rule": "Paragrafo 3.2 pg 9 per distribuzione omogenea e fibre dirette ortogonalmente alla sezione",
            "k0_proposed": 0.5,
            "k0_proposed_rule":
"""
Paragrafo 3.2 pg 9 per tener conto a fini cautelativi di possibili disomogeneità 
ed anisotropie del materiale, sulla base dei valori riscontrati nelle esperienze finora disponibili
""",
            "kg_min": 1.00,
            "kg_min_rule": "Paragrafo 3.2 pg 9",
            "kg_max": 1.25,
            "kg_max_rule": "Paragrafo 3.2 pg 9",
            "kg_proposed": 1.00,
            "kg_proposed_rule":" Paragrafo 3.2 pg 9",
        },
        LawCode.CODE_MODEL_CODE_10: {
            "frc_tab_column_names": ["ductility class", "1.0", "1.5", "2.0", "2.5", "3.0", "4.0", "5.0", "6.0", "7.0", "8.0"],
            "frc_tab_column_names_rule": "Paragraph 5.6.3",
            "frc_tab_rows": [
                ["a", 0.5, 0.75, 1.00, 1.25, 1.50, 2.00, 2.50, 3.00, 3.50, 4.00],
                ["b", 0.70, 1.05, 1.40, 1.75, 2.10, 2.80, 3.50, 4.20, 4.90, 5.60],
                ["c", 0.90, 1.35, 1.80, 2.25, 2.70, 3.60, 4.50, 5.40, 6.30, 7.20],
                ["d", 1.10, 1.65, 2.20, 2.75, 3.30, 4.40, 5.50, 6.60, 7.70, 8.80],
                ["e", 1.30, 1.95, 2.60, 3.25, 3.90, 5.20, 6.50, 7.80, 9.10, 10.40],
            ],
            "frc_tab_rows_rules": "Paragraph 5.6.3",
            "k_proposed": 1.00,
            "k_proposed_rule": "Section 5.6.7 pg 150",
            "k_min": 0,
            "k_min_rule":"Section 5.6.7 pg 150",
        },
        LawCode.CODE_EC2_11_2023: {
            "frc_tab_column_names": ["ductility class", "1.0", "1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "4.5", "5.0", "6.0", "7.0", "8.0"],
            "frc_tab_column_names_rule": "Table L.2",
            "frc_tab_rows": [
                ["a", 0.5, 0.75, 1.00, 1.25, 1.50, 1.80, 2.00, 2.30, 2.50, 3.00, 3.50, 4.00],
                ["b", 0.70, 1.05, 1.40, 1.75, 2.10, 2.50, 2.80, 3.20, 3.50, 4.20, 4.90, 5.60],
                ["c", 0.90, 1.35, 1.80, 2.25, 2.70, 3.20, 3.60, 4.10, 4.50, 5.40, 6.30, 7.20],
                ["d", 1.10, 1.65, 2.20, 2.75, 3.30, 3.90, 4.40, 5.00, 5.50, 6.60, 7.70, 8.80],
                ["e", 1.30, 1.95, 2.60, 3.25, 3.90, 4.60, 5.20, 5.90, 6.50, 7.80, 9.10, 10.40],
            ],
            "frc_tab_rows_rules": "Table L.2",
            "k0_max": 1.70,
            "k0_max_rule": "L.5.5.1(6)",
            "k0_proposed": 0.5,
            "k0_proposed_rule": "L.5.5.1(3)",
            "kg_min": 1.00,
            "kg_min_rule": "L.5.5.1(7)",
            "kg_max": 1.30,
            "kg_max_rule": "L.5.5.1(7)",
            "kg_proposed": 1.00,
        },
    }
    def __init__(self) -> None:
        self.__concrete: Concrete = Concrete()  # elemento privato
        self.__description: str = ""

        # Coefficienti parziali di sicurezza
        # TODO: manca accidentale come in EC2-1.1 Table L.1.
        self.__ycf_uls: float = 1.5  # Coefficiente parziale calcestruzzo in trazione ULS
        self.__ycf_sls: float  = 1.0  # Coefficiente parziale calcestruzzo in trazione SLS
        self.__ycc_uls: float  = 1.5  # Coefficiente parziale calcestruzzo in compressione ULS

        # TODO: valorizzarlo quando si sceglie la verifica NON SEZIONALE
        self.__yce: float  = 1.2  # Coefficiente parziale calcestruzzo Modulo elastico

        # Valorizzate quando si sceglie il materiale da normativa
        self.__strength_class: str = ""
        self.__ductility_class: DuctilityClass | None = None

        # Parametro di fessurazione nulla
        self.__no_crack_els: bool = False

        # Resistenze a trazione residue FRC
        self.__fR1k: float | None = None  # [MPa]
        self.__fR3k: float | None  = None  # [MPa]

        # Deformazione ultima in trazione FRC
        self.__efu: float | None = None  # [-]

        # Tipo di Analisi (sezionale o FEM)
        self.__tipo_analisi: List[TpAnalysis] = [TpAnalysis.TP_SECTIONAL, TpAnalysis.TP_FEM]

        # Parametri per analisi sezionale
        self.__lcs: float | None  = None  # [mm] - lunghezza critica sezionale

        # Parametri per analisi FEM
        self.__d1: float | None = None  # [mm]
        self.__d2: float | None = None  # [mm]
        self.__d3: float | None = None  # [mm]

        # Normativa
        self.__normativa: LawCode = LawCode.CODE_ITA_LG2022  # "LG C.S.LL.PP (2022)" o "Model Code - fib Bulletin83"

        # Parametri per LG C.S.LL.PP (2022)
        self.__k0: float | None = None  # [-]
        self.__kg: float | None = None  # [-]

        # Parametri per Model Code - fib Bulletin83
        self.__valutazione_precisa: TpValutation = TpValutation.TP_ND
        self.__k: float | None = None # [-]

    def get_description(self):
        return self.__description

    def set_description(self, description: str):
        self.__description = description

    def concrete_compression_def_parameters(self):
        """
        Calcola i parametri deformativi aggiuntivi 
        Compressione Uniassiale - Legame costitutivo non lineare del calcestruzzo EC2
        ec1: deformazione al raggiungimento della resistenza massima
        k: fattore che definisce il ramo discendente
        ecu1: deformazione ultima in compressione
        """
        if self.__concrete.get_fck() == 0 or self.__concrete.get_fcm() == 0 or self.__concrete.get_Ecm() == 0:
            return None, None, None

        # Calcolo di ec1 secondo EC2 - Eq. 3.17
        ec1 = 0.7 * (self.__concrete.get_fcm() ** 0.31) / 1000

        if ec1<=2.8/1000:
            ec1=ec1
        else:
            ec1=2.8/1000

        # Calcolo di ecu1 secondo EC2 - Eq. 3.19 e 3.20
        if self.__concrete.get_fck() <= 50:
            ecu1 = 3.5 / 1000
        else:
            ecu1 = (2.8 + 27 * ((98 - self.__concrete.get_fcm()) / 100) ** 4) / 1000

        # Calcolo di k secondo EC2 - Eq. 3.14
        # k = 1.05 * Ecm * |ec1| / fcm
        k = 1.05 * self.__concrete.get_Ecm() * abs(ec1) / self.__concrete.get_fcm()

        return ec1, k, ecu1


    # METODI PRINCIPALI PER IMPOSTARE TUTTI I PARAMETRI DEL CALCESTRUZZO
    def set_concrete(self, concrete: Concrete):
        self.__concrete = concrete

    def get_concrete(self):
        return self.__concrete

    # METODO PER OTTENERE TUTTI I PARAMETRI IN FORMATO DIZIONARIO
    def __get_all_concrete_properties(self) -> dict:
        """
        Restituisce tutti i parametri del calcestruzzo in un dizionario organizzato
        """
        # Calcola i parametri deformativi aggiuntivi usando la tua funzione
        ec1, k, ecu1 = self.concrete_compression_def_parameters()

        properties = {
            "Informazioni generali": {
                "Normativa calcestruzzo": self.__concrete.codeStr() if hasattr(self.__concrete,
                                                                               'codeStr') else "Non definita",
                "Classe calcestruzzo": self.__concrete.catStr() if hasattr(self.__concrete,
                                                                           'catStr') else "Non definita",
                "Tipo analisi": self.__tipo_analisi,
                "Valutazione precisa": self.__valutazione_precisa,
                "Normativa FRC": self.__normativa,
            },
            "Resistenze caratteristiche": {
                "fck": self.__concrete.get_fck(),
                "Rck": self.__concrete.get_Rck(),
                "fcm": self.__concrete.get_fcm(),
                "fctm": self.__concrete.get_fctm(),
                "fct_crack": self.__concrete.get_fct_crack(),
            },
            "Proprietà deformative": {
                "Ecm": self.__concrete.get_Ecm(),
                "ec2": self.__concrete.get_ec2(),
                "ecu": self.__concrete.get_ecu(),
                "ec1": ec1,  # Deformazione al picco [‰]
                "k": k,  # Fattore ramo discendente [-]
                "ecu1": ecu1,  # Deformazione ultima [‰]
            },
            "Parametri di calcolo": {
                "lambda": self.__concrete.get_lambda(),
                "eta": self.__concrete.get_eta(),
                "alphacc": self.__concrete.get_alphacc(),
                "k1": self.__concrete.get_k1(),
                "k2": self.__concrete.get_k2(),
            },
            "Coefficienti di sicurezza": {
                "gammac": self.__concrete.get_gammac(),
                "γc": self.__ycc_uls,
                "γce":self.__yce,
                "γcf_uls": self.__ycf_uls,
                "γcf_sls": self.__ycf_sls,
            },
            "Tensioni massime": {
                "sigmac_max_c": self.__concrete.get_sigmac_max_c(),
                "sigmac_max_q": self.__concrete.get_sigmac_max_q(),
            },
            "Parametri FRC": {
                "fR1k": self.__fR1k,
                "fR3k": self.__fR3k,
                "εfu": self.__efu,
            },
            "Parametri analisi sezionale": {
                "lcs": self.__lcs,
            } if self.__tipo_analisi == "Sezionale" else {},
            "Parametri analisi FEM": {
                "d1": self.__d1,
                "d2": self.__d2,
                "d3": self.__d3,
            } if self.__tipo_analisi == "FEM" else {},
            "Parametri normativa specifica": self.__get_normativa_specifica_params()
        }

        return properties

    def __get_normativa_specifica_params(self) -> dict:
        """Restituisce i parametri specifici in base alla normativa FRC selezionata"""
        if self.__normativa == LawCode.CODE_ITA_LG2022:
            return {
                "k0": self.__k0,
                "kg": self.__kg,
            }
        elif self.__normativa == LawCode.CODE_MODEL_CODE_10:
            return {
                "Valutazione precisa": self.__valutazione_precisa,
            }
        else:
            return {}

    def print_concrete_properties(self):
        """Stampa tutti i parametri del calcestruzzo in formato leggibile"""
        props = self.__get_all_concrete_properties()

        print("=" * 70)
        print("PARAMETRI CALCESTRUZZO FIBRORINFORZATO - Riepilogo COMPLETO")
        print("=" * 70)

        for category, parameters in props.items():
            if parameters:  # Mostra solo le categorie che hanno parametri
                print(f"\n{category}:")
                print("-" * 50)
                for key, value in parameters.items():
                    if value is not None:
                        unit = self.__get_unit(key)
                        if isinstance(value, (int, float)):
                            print(f"  {key:25} = {value:8.4f} {unit}")
                        else:
                            print(f"  {key:25} = {value} {unit}")

    @staticmethod
    def __get_unit(parameter: str) -> str:
        """Restituisce l'unità di misura per il parametro"""
        units = {
            # Informazioni generali
            'Normativa calcestruzzo': '', 'Classe calcestruzzo': '',
            'Tipo analisi': '', 'Valutazione precisa': '', 'Normativa FRC': '',

            # Resistenze
            'fck': 'MPa', 'Rck': 'MPa', 'fcm': 'MPa', 'fctm': 'MPa',
            'fct_crack': 'MPa',

            # Proprietà deformative
            'Ecm': 'MPa', 'ec2': '-', 'ecu': '-', 'ec1': '-',
            'ecu1': '-', 'k': '-',

            # Parametri di calcolo
            'lambda': '-', 'eta': '-', 'alphacc': '-', 'k1': '-', 'k2': '-',

            # Coefficienti di sicurezza
            'gammac': '-', 'γc': '-', 'γce': '-', 'γcf_uls': '-', 'γcf_sls': '-',

            # Tensioni massime
            'sigmac_max_c': 'MPa', 'sigmac_max_q': 'MPa',

            # Parametri FRC
            'fR1k': 'MPa', 'fR3k': 'MPa', 'εfu': '-',

            # Parametri analisi
            'lcs': 'mm', 'd1': 'mm', 'd2': 'mm', 'd3': 'mm',

            # Parametri normativa specifica
            'k0': '-', 'kg': '-',
        }
        return units.get(parameter, '')

    # Metodo per visualizzare il riepilogo delle impostazioni
    def print_settings_summary(self):
        """Stampa un riepilogo delle impostazioni principali"""
        print("=" * 70)
        print("RIEPILOGO IMPOSTAZIONI FIBERCONCRETE")
        print("=" * 70)

        concrete_code = self.__concrete.codeStr() if hasattr(self.__concrete, 'codeStr') else "Non definita"
        concrete_class = self.__concrete.catStr() if hasattr(self.__concrete, 'catStr') else "Non definita"

        summary = {
            "Normativa calcestruzzo": concrete_code,
            "Classe calcestruzzo": concrete_class,
            "Normativa FRC": self.__normativa,
            "Tipo analisi": self.__tipo_analisi,
            "Valutazione precisa": self.__valutazione_precisa,
            "fck": f"{self.__concrete.get_fck()} MPa" if self.__concrete.get_fck() else "Non definito",
            "fR1k": f"{self.__fR1k} MPa" if self.__fR1k else "Non definito",
            "fR3k": f"{self.__fR3k} MPa" if self.__fR3k else "Non definito",
        }

        for key, value in summary.items():
            print(f"  {key:25} : {value}")

    # GETTER e SETTER per tutte le variabili

    # Coefficienti di sicurezza
    def set_ycf_uls(self, value):
        self.__ycf_uls = value

    def get_ycf_uls(self):
        return self.__ycf_uls

    def set_ycf_sls(self, value):
        self.__ycf_sls = value

    def get_ycf_sls(self):
        return self.__ycf_sls

    def set_yc(self, value):
        self.__ycc_uls = value

    def get_yc(self):
        return self.__ycc_uls

    def set_yce(self, value):
        self.__yce = value

    def get_yce(self):
        return self.__yce

    # Resistenze FRC
    def set_fR1k(self, value):
        self.__fR1k = value

    def get_fR1k(self):
        return self.__fR1k

    def set_fR3k(self, value):
        self.__fR3k = value

    def get_fR3k(self):
        return self.__fR3k

    def get_strength_class(self):
        return self.__strength_class

    def get_ductility_class(self):
        return self.__ductility_class

    def get_no_crack_sls(self):
        return self.__no_crack_els

    def set_no_crack_sls(self, v: bool):
        self.__no_crack_els = v

    # Deformazione ultima
    def set_efu(self, value):
        self.__efu = value

    def get_efu(self):
        return self.__efu

    def cal_ec1(self):
        ec1, _, _ = self.concrete_compression_def_parameters()
        return ec1

    def cal_k(self):
        _, k, _ = self.concrete_compression_def_parameters()
        return k

    def cal_ecu1(self):
        _, _, ecu1 = self.concrete_compression_def_parameters()
        return ecu1

    # Tipo di Analisi
    def set_tipo_analisi(self, value: List[TpAnalysis]):
        if value is None:
            raise ValueError("Tipo analisi non valido")

        self.__tipo_analisi = value

        if TpAnalysis.TP_SECTIONAL not in self.__tipo_analisi:
            self.__lcs = None

        if TpAnalysis.TP_FEM not in self.__tipo_analisi:
            self.__d1 = None
            self.__d2 = None
            self.__d3 = None

    def get_tipo_analisi(self):
        return self.__tipo_analisi

    # Parametri analisi sezionale
    def set_lcs(self, value):
        if TpAnalysis.TP_SECTIONAL not in self.__tipo_analisi:
            raise ValueError("Only active with SECTIONAL analysis !!!")

        self.__lcs = value

    def get_lcs(self):
        return self.__lcs

    # Parametri analisi FEM
    def set_d1(self, value):
        if TpAnalysis.TP_FEM not in self.__tipo_analisi:
            raise ValueError("Only active with FEM analysis !!!")

        self.__d1 = value


    def get_d1(self):
        return self.__d1

    def set_d2(self, value):
        if TpAnalysis.TP_FEM not in self.__tipo_analisi:
            raise ValueError("Only active with FEM analysis !!!")

        self.__d2 = value

    def get_d2(self):
        return self.__d2

    def set_d3(self, value):
        if TpAnalysis.TP_FEM not in self.__tipo_analisi:
            raise ValueError("Only active with FEM analysis !!!")

        self.__d3 = value

    def get_d3(self):
        return self.__d3

    # Normativa
    def set_normativa(self, value: LawCode):
        if value == LawCode.CODE_MODEL_CODE_10:
            self.__valutazione_precisa = TpValutation.TP_INACTIVE
            self.__k0 = None
            self.__kg = None

        if value == LawCode.CODE_ITA_LG2022:
            self.__valutazione_precisa = TpValutation.TP_ND
            self.__k = None

        if value == LawCode.CODE_EC2_11_2023:
            self.__k = None

        self.__normativa = value

    def set_by_law(self,
                   strength_class: str,
                   ductility_class: DuctilityClass
                   ):

        rules_table = FiberConcrete.rules_table.get(self.__normativa)
        if rules_table is None:
            raise ValueError("Code not found")

        values = rules_table["frc_tab_column_names"]
        assert isinstance(values, list)
        if strength_class not in values:
            raise ValueError("Strength class not found")

        self.__strength_class = strength_class
        self.__ductility_class = ductility_class

        idx_column = values.index(strength_class)
        idx_row = ['a', 'b', 'c', 'd', 'e'].index(ductility_class)

        self.__fR1k = float(values[idx_column])

        value = rules_table.get("frc_tab_rows")
        assert isinstance(value,list)
        self.__fR3k = value[idx_row][idx_column]

        if self.__normativa == LawCode.CODE_MODEL_CODE_10:
            k_proposed = rules_table.get("k_proposed")
            assert isinstance(k_proposed,float)
            self.__k = k_proposed
            self.__k0 = None
            self.__kg = None
        elif self.__normativa == LawCode.CODE_ITA_LG2022:
            self.__k = None
            k0_proposed = rules_table.get("k0_proposed")
            assert isinstance(k0_proposed,float)
            self.__k0 = k0_proposed
            kg_proposed = rules_table.get("kg_proposed")
            assert isinstance(kg_proposed,float)
            self.__kg = kg_proposed
        else: # self.__normativa == LawCode.CODE_EC2_11_2023:
            self.__k = None
            k0_proposed = rules_table.get("k0_proposed")
            kg_proposed = rules_table.get("kg_proposed")
            assert isinstance(k0_proposed,float)
            assert isinstance(kg_proposed,float)
            self.__k0 = k0_proposed
            self.__kg = kg_proposed

    def get_normativa(self):
        return self.__normativa

    # Parametri LG C.S.LL.PP (2022)
    def set_k0(self, value):
        if self.__normativa == LawCode.CODE_ITA_LG2022 or self.__normativa == LawCode.CODE_EC2_11_2023:
            k0_min = FiberConcrete.rules_table.get(self.__normativa)["k0_min"]
            k0_max = FiberConcrete.rules_table.get(self.__normativa)["k0_max"]
            if k0_min <= value <= k0_max:
                self.__k0 = value
                return
            raise ValueError(f"k0 not in range [{k0_min}, {k0_max}] with value {value} and code {self.__normativa}")
        raise ValueError("Doesn't exist k0 without CODE_ITA_LG2022 or CODE_EC2_11_2023")

    def get_k0(self):
        return self.__k0

    # Parametri Model Code 2010
    def set_k(self, value):
        if self.__normativa == LawCode.CODE_MODEL_CODE_10:
            k_min = FiberConcrete.rules_table.get(self.__normativa)["k_min"]
            if k_min < value:
                self.__k = value
                return
            raise ValueError(f"k not in range ({k_min}, +inf) with value {value} and code {self.__normativa}")
        raise ValueError("Doesn't exist k0 without Model Code 2010 !!!")

    def get_k(self):
        return self.__k

    def set_kg(self, value):
        if self.__normativa == LawCode.CODE_ITA_LG2022 or self.__normativa == LawCode.CODE_EC2_11_2023:
            kg_min = FiberConcrete.rules_table.get(self.__normativa)["kg_min"]
            kg_max = FiberConcrete.rules_table.get(self.__normativa)["kg_max"]
            if kg_min <= value <= kg_max:
                self.__kg = value
                return
            raise ValueError(f"kg not in range [{kg_min}, {kg_max}] with value {value} and code {self.__normativa}")
        raise ValueError("Doesn't exist kg without CODE_ITA_LG2022 or CODE_EC2_11_2023")

    def get_kg(self):
        return self.__kg

    # Parametri Model Code - fib Bulletin83
    def set_valutazione_precisa(self, value: TpValutation):
        if self.__normativa == LawCode.CODE_ITA_LG2022:
            raise ValueError("Setting valido solo per Model Code")
        if self.__normativa == LawCode.CODE_MODEL_CODE_10:
            self.__valutazione_precisa = value
            return
        raise ValueError("Low code unknown !!!")

    def get_valutazione_precisa(self):
        return self.__valutazione_precisa

    def is_valid_material(self) -> bool:

        # 1. Ho assegnato almeno i tre parametri
        if self.__fR1k is None or self.__fR3k is None or self.__efu is None:
            return False

        # 3. Ho assegnato i valori legati alla normativa
        if self.__normativa == LawCode.CODE_ITA_LG2022 or self.__normativa == LawCode.CODE_EC2_11_2023:
            if self.__k0 is None or self.__kg is None:
                return False

        if self.__normativa == LawCode.CODE_MODEL_CODE_10:
            if self.__valutazione_precisa is TpValutation.TP_ND:
                return False
            if self.__k is None:
                return False

        # 4. Ho assegnato i valori legati al tipo di analisi
        if TpAnalysis.TP_SECTIONAL in self.__tipo_analisi and self.__lcs is None:
            return False

        if TpAnalysis.TP_FEM in self.__tipo_analisi and (
                self.__d1 is None or self.__d2 is None or self.__d3 is None
        ):
            return False

        return True

    def __str__(self):
        return (f"FiberConcrete\n"
                f"Normativa: {self.__normativa}\n"
    
                f"k0: {self.__k0} -, kg: {self.__kg} -\n"
                f"Valutazione Precisa da Model Code: {self.__valutazione_precisa} \n"
                
                f"Tipo Analisi: {self.__tipo_analisi}\n"
                f"d1: {self.__d1} mm, d2: {self.__d2} mm, d3: {self.__d3} mm \n"
                f"lcs: {self.__lcs} mm \n"
                
                f"fR1k: {self.__fR1k} MPa, fR3k: {self.__fR3k} MPa\n"
                f"fck: {self.__concrete.get_fck()} MPa, Rck: {self.__concrete.get_Rck()} MPa\n"
                f"Ecm: {self.__concrete.get_Ecm()} MPa\n"
                f"εfu: {self.__efu} \n"
                
                f"γcf_uls: {self.__ycf_uls}, γcf_sls: {self.__ycf_sls}")