import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gerar_dados_exemplo import gerar
from gerar_relatorio import carregar_planilha, gerar_pdf, gerar_previa, moeda, resumir


def test_moeda_formato_brasileiro():
    assert moeda(1234.5) == "R$ 1.234,50"
    assert moeda(0) == "R$ 0,00"


def test_resumo_calcula_totais(tmp_path):
    caminho = tmp_path / "vendas.csv"
    pd.DataFrame(
        {
            "Data": ["01/02/2026", "15/02/2026", "03/03/2026"],
            "Produto": ["A", "B", "A"],
            "Vendedor": ["Ana", "Ana", "Bruno"],
            "Quantidade": [2, 1, 1],
            "Preco_unitario": [10.0, 50.0, 10.0],
        }
    ).to_csv(caminho, index=False)

    resumo = resumir(carregar_planilha(caminho))

    assert resumo.faturamento == 80.0
    assert resumo.pedidos == 3
    assert resumo.itens == 4
    assert list(resumo.por_mes.values) == [70.0, 10.0]
    assert resumo.top_produtos.index[0] == "B"


def test_coluna_faltando(tmp_path):
    caminho = tmp_path / "ruim.csv"
    pd.DataFrame({"data": ["01/01/2026"], "produto": ["A"]}).to_csv(caminho, index=False)
    with pytest.raises(ValueError, match="preco_unitario"):
        carregar_planilha(caminho)


def test_gera_pdf_e_previa(tmp_path):
    planilha = tmp_path / "vendas.xlsx"
    gerar(linhas=100).to_excel(planilha, index=False)
    destino = tmp_path / "saida" / "relatorio.pdf"  # a pasta ainda não existe

    gerar_pdf(carregar_planilha(planilha), destino, "Loja Teste")
    assert destino.read_bytes().startswith(b"%PDF")

    imagem = destino.with_suffix(".png")
    gerar_previa(destino, imagem)
    assert imagem.read_bytes().startswith(b"\x89PNG")