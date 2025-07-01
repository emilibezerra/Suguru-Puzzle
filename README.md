# Puzzle-Suguru
Este projeto resolve puzzles Suguru (também conhecidos como "Number Blocks") utilizando Programação Linear Inteira (PLI) com a biblioteca pulp. Além disso, ele inclui:

- Uma interface gráfica (GUI) interativa.

- Análise estatística do desempenho do solver (tempo, memória, complexidade).

- Resolução progressiva com diferentes quantidades de dicas.

# Como Usar
Pré-requisitos
- Python 3.x
- Bibliotecas: pulp, tkinter, matplotlib, numpy, psutil
  

```bash
pip install pulp matplotlib numpy psutil
```
Executando o Solver:
1. Clone o repositorio
```bash
git clone https://github.com/emilibezerra/Suguru-Puzzle.git
cd Suguru-Puzzle
```

2. Execute o arquivo principal:
```bash
python suguru_PLI_estatistica.py
```

# Interface Gráfica (GUI)
Carregar Puzzle: Clique em Arquivo > Abrir Puzzle e selecione um arquivo no formato .in (exemplo abaixo).

Controles:
- Slider de Dicas: Ajuste a quantidade de dicas (valores pré-preenchidos) usadas pelo solver.

- Botões: Aplicar: Define o número de dicas selecionadas. Resolver: Inicia a resolução progressiva. Análise: Mostra gráficos de desempenho (tempo, memória, complexidade).

# Formato do Arquivo de Puzzle
O arquivo de entrada (.in) deve seguir esta estrutura:

```md
5 5                          # Linhas e colunas do grid
0 0 0 0 0                    # Grid (0 = célula vazia)
0 2 0 0 0
0 0 0 0 0
0 0 0 3 0
0 0 0 0 0
1 1 2 2 2                    # Mapa de áreas (cada número define uma região)
1 1 2 2 2
3 3 4 4 2
3 3 4 4 5
3 3 5 5 5
```
O dataset utilizado nesse projeto é encontrado em: https://github.com/abcqwq/suguru-backtrack.git
