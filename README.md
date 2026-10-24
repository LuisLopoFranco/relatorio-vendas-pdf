# Relatório de vendas em PDF a partir de planilha

Transforma uma planilha de vendas (Excel ou CSV) em um relatório PDF pronto para enviar ao dono do negócio: faturamento, ticket médio, gráfico mensal, produtos que mais vendem e desempenho por vendedor.

![Prévia do relatório](exemplo/preview.png)

**Problema que resolve:** muita loja ainda monta relatório na mão, copiando dados do Excel todo fim de mês. Este script faz isso em segundos e pode rodar automaticamente.

## Como usar

Requer Python 3.10 ou mais novo.

```bash
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt

python gerar_dados_exemplo.py    # cria dados/vendas_exemplo.xlsx
python gerar_relatorio.py dados/vendas_exemplo.xlsx -o relatorio.pdf --empresa "Loja Exemplo"
```

Veja um resultado em [exemplo/relatorio_exemplo.pdf](exemplo/relatorio_exemplo.pdf).

## Formato da planilha

| data | produto | vendedor | quantidade | preco_unitario |
|---|---|---|---|---|
| 05/01/2026 | Camiseta básica | Ana | 2 | 49.90 |

Outras colunas são ignoradas. Os nomes das colunas não diferenciam maiúsculas de minúsculas.

## Estrutura

| Arquivo | O que faz |
|---|---|
| `gerar_relatorio.py` | Lê a planilha, calcula os indicadores, desenha o gráfico e monta o PDF |
| `gerar_dados_exemplo.py` | Cria uma planilha fictícia com 600 vendas para testar |
| `exemplo/` | Um relatório já gerado e a imagem de prévia |
| `tests/` | Testes com pytest |

## Testes

```bash
pytest
```

## Tecnologias

Python, pandas, matplotlib, fpdf2.

## Ideias de evolução

- Enviar o PDF por e-mail ou WhatsApp automaticamente todo dia 1º.
- Ler direto do Google Sheets ou do banco de dados do sistema da loja.
- Comparar com o mês anterior e destacar quedas.

## Autor

Feito por **Luis Gabriel Lopo**, desenvolvedor Python, Java e TypeScript. Faço automações, relatórios e chatbots sob medida para pequenos negócios. Veja os outros projetos no meu perfil do GitHub.