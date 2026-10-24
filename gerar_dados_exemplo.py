"""Gera uma planilha de vendas fictícia para testar o relatório."""

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

PRODUTOS = {
    "Camiseta básica": 49.90,
    "Calça jeans": 139.90,
    "Tênis casual": 229.90,
    "Moletom": 159.90,
    "Boné": 39.90,
    "Jaqueta corta-vento": 189.90,
}
VENDEDORES = ["Ana", "Bruno", "Carla", "Diego"]
CANAIS = ["Loja física", "Instagram", "WhatsApp", "Site"]


def gerar(linhas: int = 600, semente: int = 42) -> pd.DataFrame:
    rng = random.Random(semente)
    inicio = date(2026, 1, 1)
    registros = []
    for _ in range(linhas):
        produto = rng.choice(list(PRODUTOS))
        registros.append(
            {
                "data": inicio + timedelta(days=rng.randint(0, 272)),
                "produto": produto,
                "vendedor": rng.choice(VENDEDORES),
                "canal": rng.choice(CANAIS),
                "quantidade": rng.randint(1, 4),
                "preco_unitario": PRODUTOS[produto],
            }
        )
    return pd.DataFrame(registros).sort_values("data").reset_index(drop=True)


if __name__ == "__main__":
    destino = Path(__file__).parent / "dados" / "vendas_exemplo.xlsx"
    destino.parent.mkdir(exist_ok=True)
    gerar().to_excel(destino, index=False)
    print(f"Planilha criada em {destino}")