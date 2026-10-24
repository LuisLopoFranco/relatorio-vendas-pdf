"""
Transforma uma planilha de vendas (Excel ou CSV) em um relatório PDF.
"""
import argparse
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import pymupdf
from fpdf import FPDF

COLUNAS_OBRIGATORIAS = {"data", "produto", "vendedor", "quantidade", "preco_unitario"}
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
COR_PRINCIPAL = (37, 99, 235)


def moeda(valor: float) -> str:
    """Formata no padrão brasileiro: R$ 1.234,56."""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def carregar_planilha(caminho: Path) -> pd.DataFrame:
    if caminho.suffix.lower() == ".csv":
        df = pd.read_csv(caminho)
    else:
        df = pd.read_excel(caminho)

    df.columns = [c.strip().lower() for c in df.columns]
    faltando = COLUNAS_OBRIGATORIAS - set(df.columns)
    if faltando:
        raise ValueError(f"A planilha não tem as colunas: {', '.join(sorted(faltando))}")

    df["data"] = pd.to_datetime(df["data"], dayfirst=True)
    df["total"] = df["quantidade"] * df["preco_unitario"]
    return df


@dataclass
class Resumo:
    faturamento: float
    pedidos: int
    ticket_medio: float
    itens: int
    por_mes: pd.Series
    top_produtos: pd.DataFrame
    por_vendedor: pd.DataFrame


def resumir(df: pd.DataFrame) -> Resumo:
    por_mes = df.groupby(df["data"].dt.to_period("M"))["total"].sum()
    top_produtos = (
        df.groupby("produto")
        .agg(quantidade=("quantidade", "sum"), total=("total", "sum"))
        .sort_values("total", ascending=False)
        .head(5)
    )
    por_vendedor = (
        df.groupby("vendedor")
        .agg(pedidos=("total", "size"), total=("total", "sum"))
        .sort_values("total", ascending=False)
    )
    faturamento = float(df["total"].sum())
    return Resumo(
        faturamento=faturamento,
        pedidos=len(df),
        ticket_medio=faturamento / len(df) if len(df) else 0.0,
        itens=int(df["quantidade"].sum()),
        por_mes=por_mes,
        top_produtos=top_produtos,
        por_vendedor=por_vendedor,
    )


def grafico_mensal(por_mes: pd.Series, destino: Path) -> None:
    rotulos = [f"{MESES[p.month - 1]}/{str(p.year)[2:]}" for p in por_mes.index]
    fig, ax = plt.subplots(figsize=(8, 3.2), dpi=150)
    ax.bar(rotulos, por_mes.values / 1000, color="#2563eb")
    ax.set_ylabel("Faturamento (mil R$)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


class RelatorioPDF(FPDF):
    def __init__(self, empresa: str):
        super().__init__()
        self.empresa = empresa

    def header(self):
        self.set_fill_color(*COR_PRINCIPAL)
        self.rect(0, 0, self.w, 18, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 13)
        self.set_xy(10, 5)
        self.cell(0, 8, f"Relatório de vendas - {self.empresa}")
        self.set_text_color(0, 0, 0)
        self.ln(18)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"Gerado em {date.today():%d/%m/%Y} - página {self.page_no()}", align="C")

    def titulo(self, texto: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, texto, new_x="LMARGIN", new_y="NEXT")

    def cartoes(self, itens: list[tuple[str, str]]):
        largura = (self.w - 20 - 3 * 4) / 4
        y = self.get_y()
        for i, (rotulo, valor) in enumerate(itens):
            x = 10 + i * (largura + 4)
            self.set_fill_color(239, 244, 255)
            self.rect(x, y, largura, 20, "F")
            self.set_xy(x + 3, y + 3)
            self.set_font("Helvetica", "", 8)
            self.cell(largura - 6, 4, rotulo)
            self.set_xy(x + 3, y + 9)
            self.set_font("Helvetica", "B", 11)
            self.cell(largura - 6, 7, valor)
        self.set_y(y + 24)

    def tabela(self, cabecalho: list[str], linhas: list[list[str]], larguras: list[int]):
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(*COR_PRINCIPAL)
        self.set_text_color(255, 255, 255)
        for texto, largura in zip(cabecalho, larguras):
            self.cell(largura, 7, texto, fill=True)
        self.ln()
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "", 9)
        for n, linha in enumerate(linhas):
            self.set_fill_color(*((248, 250, 252) if n % 2 else (255, 255, 255)))
            for texto, largura in zip(linha, larguras):
                self.cell(largura, 6.5, texto, fill=True)
            self.ln()


def gerar_pdf(df: pd.DataFrame, destino: Path, empresa: str) -> Resumo:
    resumo = resumir(df)
    pdf = RelatorioPDF(empresa)
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()

    inicio, fim = df["data"].min(), df["data"].max()
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Período: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.cartoes(
        [
            ("Faturamento", moeda(resumo.faturamento)),
            ("Pedidos", f"{resumo.pedidos:,}".replace(",", ".")),
            ("Ticket médio", moeda(resumo.ticket_medio)),
            ("Itens vendidos", f"{resumo.itens:,}".replace(",", ".")),
        ]
    )

    pdf.titulo("Faturamento por mês")
    with tempfile.TemporaryDirectory() as tmp:
        imagem = Path(tmp) / "mensal.png"
        grafico_mensal(resumo.por_mes, imagem)
        pdf.image(str(imagem), w=pdf.w - 20)

    pdf.titulo("Produtos que mais faturaram")
    pdf.tabela(
        ["Produto", "Quantidade", "Faturamento", "% do total"],
        [
            [
                produto,
                str(int(linha.quantidade)),
                moeda(linha.total),
                f"{linha.total / resumo.faturamento:.1%}".replace(".", ","),
            ]
            for produto, linha in resumo.top_produtos.iterrows()
        ],
        [80, 30, 45, 35],
    )

    pdf.titulo("Desempenho por vendedor")
    pdf.tabela(
        ["Vendedor", "Pedidos", "Faturamento", "Ticket médio"],
        [
            [vendedor, str(int(linha.pedidos)), moeda(linha.total), moeda(linha.total / linha.pedidos)]
            for vendedor, linha in resumo.por_vendedor.iterrows()
        ],
        [80, 30, 45, 35],
    )

    destino.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(destino))
    return resumo


def gerar_previa(pdf: Path, destino: Path, dpi: int = 100) -> None:
    """Salva a primeira página do PDF como imagem PNG, boa para mandar por WhatsApp ou pôr no README."""
    with pymupdf.open(pdf) as documento:
        documento[0].get_pixmap(dpi=dpi).save(destino)


def main():
    parser = argparse.ArgumentParser(description="Gera um relatório PDF a partir de uma planilha de vendas.")
    parser.add_argument("planilha", type=Path, help="Arquivo .xlsx ou .csv")
    parser.add_argument("-o", "--saida", type=Path, default=Path("saida") / "relatorio.pdf")
    parser.add_argument("--empresa", default="Minha Empresa")
    parser.add_argument("--previa", action="store_true", help="Também salva a primeira página como PNG, ao lado do PDF")
    args = parser.parse_args()

    df = carregar_planilha(args.planilha)
    resumo = gerar_pdf(df, args.saida, args.empresa)
    print(f"Relatório salvo em {args.saida} ({resumo.pedidos} pedidos, {moeda(resumo.faturamento)})")
    if args.previa:
        imagem = args.saida.with_suffix(".png")
        gerar_previa(args.saida, imagem)
        print(f"Prévia salva em {imagem}")


if __name__ == "__main__":
    main()