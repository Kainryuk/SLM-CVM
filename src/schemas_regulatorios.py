"""
UC01 Sem02 — Kelvin (Trilha B: IA & Ontologia) — CVM
Contrato oficial de entidades e metadados regulatórios da CVM com Pydantic v2 + Enum.
"""

from enum import Enum

from pydantic import BaseModel, Field


class StatusVigencia(str, Enum):
    VIGENTE = "VIGENTE"
    REVOGADA = "REVOGADA"
    ALTERADA = "ALTERADA"


class TipoNormaCVM(str, Enum):
    RESOLUCAO = "Resolucao_CVM"
    INSTRUCAO = "Instrucao_CVM"
    OFICIO_CIRCULAR = "Oficio_Circular"
    DELIBERACAO = "Deliberacao"


class MetadadosExtraidosNorma(BaseModel):
    orgao: str = Field(default="CVM", description="Sigla da agência reguladora (CVM)")
    tipo_norma: TipoNormaCVM = Field(description="Tipo do ato normativo da CVM")
    tipo_e_numero: str = Field(
        description="Tipo, número e ano da norma. Ex: Resolução CVM 175/2022"
    )
    status_vigencia: StatusVigencia = Field(description="Status de vigência da norma")
    entidades_citadas: list[str] = Field(
        description=(
            "Lista de participantes do mercado de capitais citados "
            "(ex: Fundos de Investimento, Companhias Abertas, Administradores Fiduciários)"
        )
    )
    normas_revogadas_ou_alteradas: list[str] = Field(
        default_factory=list,
        description="Lista de normas antigas que este texto revoga ou altera",
    )
    resumo_tecnico: str = Field(
        description="Resumo objetivo de até 2 frases sobre a regra"
    )
