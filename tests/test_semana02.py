from src.schemas_regulatorios import (
    MetadadosExtraidosNorma,
    StatusVigencia,
    TipoNormaCVM,
)


def test_validacao_schema_pydantic():
    dados_simulados = {
        "orgao": "CVM",
        "tipo_norma": "Resolucao_CVM",
        "tipo_e_numero": "Resolução CVM 175/2022",
        "status_vigencia": "VIGENTE",
        "entidades_citadas": [
            "Fundos de Investimento",
            "Administradores Fiduciários",
        ],
        "normas_revogadas_ou_alteradas": ["Instrução CVM 555/2014"],
        "resumo_tecnico": (
            "Dispõe sobre a constituição, o funcionamento e a divulgação de "
            "informações dos fundos de investimento."
        ),
    }
    objeto = MetadadosExtraidosNorma(**dados_simulados)
    assert objeto.orgao == "CVM"
    assert objeto.tipo_norma == TipoNormaCVM.RESOLUCAO
    assert objeto.status_vigencia == StatusVigencia.VIGENTE
    assert len(objeto.entidades_citadas) == 2
    assert objeto.normas_revogadas_ou_alteradas == ["Instrução CVM 555/2014"]
