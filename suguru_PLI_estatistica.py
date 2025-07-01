import pulp
import os
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import time
from threading import Thread
import random
import colorsys
import matplotlib.pyplot as plt
import psutil
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SuguruSolver:
    def __init__(self, gui_callback=None):
        self.grid = None
        self.areas = None
        self.rows = 0
        self.cols = 0
        self.area_map = None
        self.cell_to_area = None
        self.given_numbers = None
        self.gui_callback = gui_callback
        self.stop_solving = False
        self.performance_data = []
        self.all_hints = []

    def load_puzzle(self, input_file):
        with open(input_file, 'r') as f:
            lines = f.readlines()
            
        self.rows, self.cols = map(int, lines[0].strip().split())
        self.grid = []
        for line in lines[1:self.rows+1]:
            self.grid.append(list(map(int, line.strip().split())))
            
        self.area_map = defaultdict(list)
        for i, line in enumerate(lines[self.rows+1:]):
            area_numbers = list(map(int, line.strip().split()))
            for j, num in enumerate(area_numbers):
                self.area_map[num].append((i, j))
                
        self.cell_to_area = {}
        for area_num, cells in self.area_map.items():
            for (i, j) in cells:
                self.cell_to_area[(i, j)] = area_num
                
        self.all_hints = []
        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i][j] != 0:
                    self.all_hints.append((i, j, self.grid[i][j]))
        
        self.given_numbers = []

    def set_hints(self, num_hints):
        if num_hints == 0:
            self.given_numbers = []
        else:
            self.given_numbers = random.sample(self.all_hints, min(num_hints, len(self.all_hints)))

    def solve_progressively(self, target_hints, visualize=False):
        self.performance_data = []
        
        for num_hints in range(0, target_hints + 1):
            if self.stop_solving:
                break
                
            self.set_hints(num_hints)
            solution = self.solve_with_hints(visualize=visualize and (num_hints == target_hints))
            
            if solution is None and num_hints > 0:
                break
                
        return solution

    def solve_with_hints(self, visualize=False):
        if self.stop_solving:
            return None
            
        start_time = time.time()
        process = psutil.Process(os.getpid())
        start_mem = process.memory_info().rss / (1024 * 1024)

        prob = pulp.LpProblem("Suguru_Solver", pulp.LpMinimize)
        
        x = pulp.LpVariable.dicts(
            "cell_value",
            ((i, j, k) for i in range(self.rows) 
                       for j in range(self.cols) 
                       for k in range(1, len(self.area_map[self.cell_to_area[(i,j)]]) + 1)),
            cat='Binary'
        )
        
        prob += 0, "Função Objetivo"

        for i in range(self.rows):
            for j in range(self.cols):
                area_size = len(self.area_map[self.cell_to_area[(i,j)]])
                prob += pulp.lpSum([x[(i, j, k)] for k in range(1, area_size + 1)]) == 1
        
        for area_num, cells in self.area_map.items():
            area_size = len(cells)
            for k in range(1, area_size + 1):
                prob += pulp.lpSum([x[(i, j, k)] for (i, j) in cells]) == 1
        
        for (i, j, val) in self.given_numbers:
            prob += x[(i, j, val)] == 1
        
        adjacent_pairs = set()
        for i in range(self.rows):
            for j in range(self.cols):
                for di in [-1, 0, 1]:
                    for dj in [-1, 0, 1]:
                        if di == 0 and dj == 0:
                            continue
                        ni, nj = i + di, j + dj
                        if 0 <= ni < self.rows and 0 <= nj < self.cols:
                            if (ni, nj) < (i, j):
                                adjacent_pairs.add(((ni, nj), (i, j)))
                            else:
                                adjacent_pairs.add(((i, j), (ni, nj)))
        
        for (i1, j1), (i2, j2) in adjacent_pairs:
            area1_size = len(self.area_map[self.cell_to_area[(i1, j1)]])
            area2_size = len(self.area_map[self.cell_to_area[(i2, j2)]])
            max_k = min(area1_size, area2_size)
            
            for k in range(1, max_k + 1):
                prob += x[(i1, j1, k)] + x[(i2, j2, k)] <= 1

        solver = pulp.PULP_CBC_CMD(msg=False)
        prob.solve(solver)
        
        end_time = time.time()
        solve_time = end_time - start_time
        mem_usage = (process.memory_info().rss / (1024 * 1024)) - start_mem
        
        self.performance_data.append({
            'num_hints': len(self.given_numbers),
            'time': solve_time,
            'memory': mem_usage,
            'variables': len(prob.variables()),
            'constraints': len(prob.constraints),
            'status': pulp.LpStatus[prob.status]
        })
        
        if pulp.LpStatus[prob.status] != 'Optimal':
            return None
        
        solution = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for area_num, cells in self.area_map.items():
            for (i, j) in cells:
                area_size = len(self.area_map[self.cell_to_area[(i,j)]])
                for k in range(1, area_size + 1):
                    if pulp.value(x[(i, j, k)]) == 1:
                        solution[i][j] = k
                        if visualize and self.gui_callback:
                            self.gui_callback(i, j, k)
                            time.sleep(0.05)
            if visualize:
                time.sleep(0.3)
                        
        return solution

class SuguruGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Suguru Solver - Análise Progressiva")
        self.current_puzzle = None
        self.cells = []
        self.area_colors = {}
        
        # Primeiro definimos todos os métodos necessários
        self.setup_ui()
        # Agora podemos passar a referência do callback
        self.solver = SuguruSolver(self.update_cell)
    
    def setup_ui(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Abrir Puzzle", command=self.load_puzzle)
        filemenu.add_command(label="Sair", command=self.root.quit)
        menubar.add_cascade(label="Arquivo", menu=filemenu)
        self.root.config(menu=menubar)
        
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=10)
        
        self.puzzle_frame = tk.Frame(self.main_frame)
        self.puzzle_frame.pack()
        
        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(pady=10)
        
        self.hint_control = tk.Frame(self.control_frame)
        self.hint_control.pack(side=tk.LEFT, padx=10)
        
        tk.Label(self.hint_control, text="Dicas:").pack(side=tk.LEFT)
        
        self.hint_slider = tk.Scale(
            self.hint_control,
            from_=0,
            to=20,
            orient=tk.HORIZONTAL,
            command=self.update_hint_display
        )
        self.hint_slider.pack(side=tk.LEFT)
        
        self.apply_hints_button = tk.Button(
            self.hint_control,
            text="Aplicar",
            command=self.apply_hints
        )
        self.apply_hints_button.pack(side=tk.LEFT, padx=5)
        
        self.solve_button = tk.Button(
            self.control_frame,
            text="Resolver",
            command=self.start_solving
        )
        self.solve_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(
            self.control_frame,
            text="Parar",
            command=self.stop_solving
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.analyze_button = tk.Button(
            self.control_frame,
            text="Análise",
            command=self.display_performance
        )
        self.analyze_button.pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(self.main_frame, text="Carregue um puzzle para começar")
        self.status_label.pack()
        
        self.plot_frame = tk.Frame(self.main_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)
    
    def update_cell(self, i, j, value):
        if 0 <= i < len(self.cells) and 0 <= j < len(self.cells[0]):
            self.cells[i][j].config(text=str(value))
            self.root.update()
    
    def update_hint_display(self, value):
        self.status_label.config(text=f"Dicas selecionadas: {value}")

    def apply_hints(self):
        num_hints = self.hint_slider.get()
        
        if not self.current_puzzle:
            messagebox.showwarning("Aviso", "Carregue um puzzle primeiro")
            return
            
        if num_hints > len(self.solver.all_hints):
            messagebox.showwarning("Aviso", f"O puzzle só tem {len(self.solver.all_hints)} dicas")
            return
            
        self.solver.set_hints(num_hints)
        self.display_puzzle()
        self.status_label.config(text=f"Puzzle com {num_hints} dicas aplicadas")

    def load_puzzle(self):
        file_path = filedialog.askopenfilename(filetypes=[("Arquivos Suguru", "*.in")])
        if file_path:
            try:
                self.solver.load_puzzle(file_path)
                self.current_puzzle = file_path
                self.hint_slider.config(to=len(self.solver.all_hints))
                self.solver.set_hints(0)  # Começa sem dicas
                self.display_puzzle()
                self.status_label.config(text=f"Carregado: {os.path.basename(file_path)}")
                self.solver.performance_data = []
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao carregar: {str(e)}")

    def display_puzzle(self):
        for widget in self.puzzle_frame.winfo_children():
            widget.destroy()
        self.cells = []
        self.area_colors = {}
        
        for i in range(self.solver.rows):
            row = []
            for j in range(self.solver.cols):
                area_num = self.solver.cell_to_area[(i, j)]
                if area_num not in self.area_colors:
                    self.area_colors[area_num] = self.generate_pastel_color(area_num)
                
                cell_value = ""
                for (x, y, val) in self.solver.given_numbers:
                    if x == i and y == j:
                        cell_value = str(val)
                        break
                
                cell = tk.Label(
                    self.puzzle_frame,
                    text=cell_value,
                    width=3,
                    height=1,
                    relief=tk.RIDGE,
                    bg=self.area_colors[area_num],
                    font=('Arial', 12, 'bold')
                )
                cell.grid(row=i, column=j, padx=1, pady=1)
                row.append(cell)
            self.cells.append(row)
    
    def generate_pastel_color(self, seed):
        random.seed(seed)
        h = random.random()
        s = 0.3 + random.random() * 0.2
        v = 0.9 + random.random() * 0.1
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def start_solving(self):
        if not self.current_puzzle:
            messagebox.showwarning("Aviso", "Carregue um puzzle primeiro")
            return
            
        target_hints = self.hint_slider.get()
        
        self.solver.stop_solving = False
        self.solve_button.config(state=tk.DISABLED)
        self.status_label.config(text=f"Resolvendo progressivamente até {target_hints} dicas...")
        
        solving_thread = Thread(target=self.solve_progressively, args=(target_hints,))
        solving_thread.start()

    def solve_progressively(self, target_hints):
        solution = self.solver.solve_progressively(target_hints, visualize=True)
        self.root.after(0, self.solving_complete, solution)

    def solving_complete(self, solution):
        self.solve_button.config(state=tk.NORMAL)
        if solution:
            self.status_label.config(text=f"Resolução completa! Visualizando com {self.hint_slider.get()} dicas")
            self.display_performance()
        else:
            self.status_label.config(text="Falha na resolução")

    def stop_solving(self):
        self.solver.stop_solving = True
        self.status_label.config(text="Resolução interrompida")

    def display_performance(self):
        if not self.solver.performance_data:
            messagebox.showinfo("Info", "Resolva o puzzle primeiro para gerar estatísticas")
            return
            
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        
        performance = sorted(self.solver.performance_data, key=lambda x: x['num_hints'])
        num_hints = [p['num_hints'] for p in performance]
        times = [p['time'] for p in performance]
        memory = [p['memory'] for p in performance]
        variables = [p['variables'] for p in performance]
        constraints = [p['constraints'] for p in performance]
        
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 12))
        fig.tight_layout(pad=3.0)
        
        ax1.plot(num_hints, times, 'bo-')
        ax1.set_title('Tempo de Resolução vs Número de Dicas', fontsize=8)
        ax1.set_xlabel('Número de Dicas', fontsize=10)
        ax1.set_ylabel('Tempo (segundos)', fontsize=10)
        ax1.grid(True)
        
        ax2.plot(num_hints, memory, 'go-')
        ax2.set_title('Uso de Memória vs Número de Dicas',fontsize=8)
        ax2.set_xlabel('Número de Dicas', fontsize=10)
        ax2.set_ylabel('Memória (MB)', fontsize=10)
        ax2.grid(True)
        
        ax3.plot(num_hints, variables, 'ro-', label='Variáveis')
        ax3.plot(num_hints, constraints, 'mo-', label='Restrições')
        ax3.set_title('Complexidade do Problema', fontsize=8)
        ax3.set_xlabel('Número de Dicas', fontsize=10)
        ax3.set_ylabel('Quantidade', fontsize=10)
        ax3.legend()
        ax3.grid(True)
        
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = SuguruGUI(root)
    root.mainloop()