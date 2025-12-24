"""
Algorithm-specific visualizers for dynamic, step-by-step animations
Each visualizer generates Manim code that shows the actual algorithm execution
"""

from typing import List, Dict, Any, Optional, Tuple
import re


class AlgorithmVisualizer:
    """Base class for algorithm visualizers"""
    
    def generate_manim_code(self, **kwargs) -> str:
        """Generate Manim scene code for the algorithm"""
        raise NotImplementedError


class NQueensVisualizer(AlgorithmVisualizer):
    """Visualizer for N-Queens backtracking algorithm"""
    
    def generate_manim_code(self, n: int = 4, show_steps: int = 20) -> str:
        """Generate dynamic N-Queens visualization with backtracking"""
        return f'''
class NQueensScene(Scene):
    def construct(self):
        # Title
        title = Text("N-Queens Algorithm (n={n})", font_size=40, color=GOLD, weight=BOLD)
        title.to_edge(UP, buff=0.3)
        self.play(Write(title), run_time=1)
        
        # Problem description
        desc = Text("Place {n} queens on {n}x{n} board\\nso no two queens attack each other", 
                   font_size=20, color=BLUE)
        desc.next_to(title, DOWN, buff=0.3)
        self.play(FadeIn(desc), run_time=0.8)
        self.wait(1)
        self.play(FadeOut(desc), run_time=0.5)
        
        # Create chessboard
        n = {n}
        square_size = min(0.7, 4.5 / n)
        board = VGroup()
        squares = [[None for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                color = "#f0d9b5" if (i + j) % 2 == 0 else "#b58863"
                square = Square(side_length=square_size, fill_color=color, 
                              fill_opacity=1, stroke_color=BLACK, stroke_width=1)
                square.move_to(RIGHT * j * square_size + DOWN * i * square_size)
                squares[i][j] = square
                board.add(square)
        
        board.center()
        self.play(FadeIn(board), run_time=1)
        
        # Add row/column labels
        labels = VGroup()
        for i in range(n):
            row_label = Text(str(i), font_size=int(16 * square_size), color=GRAY)
            row_label.next_to(squares[i][0], LEFT, buff=0.2)
            col_label = Text(str(i), font_size=int(16 * square_size), color=GRAY)
            col_label.next_to(squares[0][i], UP, buff=0.2)
            labels.add(row_label, col_label)
        self.play(FadeIn(labels), run_time=0.5)
        
        # Status text
        status = Text("", font_size=18, color=WHITE)
        status.to_edge(DOWN, buff=0.3)
        
        # Queens tracking
        queens = VGroup()
        queen_positions = []
        
        # Backtracking algorithm simulation
        solutions = []
        
        def is_safe(row, col, positions):
            for r, c in positions:
                if c == col or abs(row - r) == abs(col - c):
                    return False
            return True
        
        def solve(row, positions, steps_shown):
            if steps_shown[0] >= {show_steps}:
                return
                
            if row == n:
                solutions.append(positions[:])
                return
            
            for col in range(n):
                if is_safe(row, col, positions):
                    positions.append((row, col))
                    steps_shown[0] += 1
                    yield ("place", row, col, len(positions), positions[:])
                    
                    if len(solutions) == 0:  # Continue until first solution
                        yield from solve(row + 1, positions, steps_shown)
                    
                    if len(solutions) == 0:  # Backtrack if no solution yet
                        positions.pop()
                        steps_shown[0] += 1
                        yield ("remove", row, col, len(positions), positions[:])
        
        steps_shown = [0]
        
        # Execute algorithm with visualization
        for step in solve(0, [], steps_shown):
            action, row, col, depth, current_positions = step
            
            if action == "place":
                # Highlight the square we're trying
                self.play(
                    squares[row][col].animate.set_fill(BLUE_E, opacity=0.8),
                    run_time=0.2
                )
                
                # Check if placement is safe - show attack lines for invalid positions
                status_text = f"Trying Queen at ({{row}}, {{col}})"
                new_status = Text(status_text, font_size=18, color=YELLOW)
                new_status.to_edge(DOWN, buff=0.3)
                self.play(Transform(status, new_status), run_time=0.2)
                
                # Place queen
                queen = Text("♛", font_size=int(40 * square_size), color=RED)
                queen.move_to(squares[row][col].get_center())
                queens.add(queen)
                queen_positions.append((row, col))
                
                self.play(FadeIn(queen, scale=0.5), run_time=0.3)
                
                # Reset square color
                original_color = "#f0d9b5" if (row + col) % 2 == 0 else "#b58863"
                self.play(
                    squares[row][col].animate.set_fill(original_color, opacity=1),
                    run_time=0.2
                )
                
                # Show current depth
                depth_text = f"Queens placed: {{depth}}"
                new_status = Text(depth_text, font_size=18, color=GREEN)
                new_status.to_edge(DOWN, buff=0.3)
                self.play(Transform(status, new_status), run_time=0.2)
                
                self.wait(0.3)
                
            elif action == "remove":
                # Backtracking
                status_text = f"Backtracking from ({{row}}, {{col}})"
                new_status = Text(status_text, font_size=18, color=RED)
                new_status.to_edge(DOWN, buff=0.3)
                self.play(Transform(status, new_status), run_time=0.2)
                
                # Highlight square in red
                self.play(
                    squares[row][col].animate.set_fill(RED_E, opacity=0.6),
                    run_time=0.2
                )
                
                # Remove queen
                if len(queens) > 0:
                    removed_queen = queens[-1]
                    self.play(FadeOut(removed_queen, scale=0.5), run_time=0.3)
                    queens.remove(removed_queen)
                    if queen_positions:
                        queen_positions.pop()
                
                # Reset square color
                original_color = "#f0d9b5" if (row + col) % 2 == 0 else "#b58863"
                self.play(
                    squares[row][col].animate.set_fill(original_color, opacity=1),
                    run_time=0.2
                )
                
                self.wait(0.2)
        
        # Show solution found
        if solutions:
            success = Text("Solution Found!", font_size=32, color=GOLD, weight=BOLD)
            success.to_edge(DOWN, buff=0.3)
            self.play(Transform(status, success), run_time=0.5)
            
            # Highlight solution
            for queen in queens:
                self.play(queen.animate.set_color(GOLD).scale(1.2), run_time=0.1)
            
            self.wait(2)
        
        self.wait(1)
'''


class SortingVisualizer(AlgorithmVisualizer):
    """Visualizer for sorting algorithms with step-by-step execution"""
    
    def generate_manim_code(self, algorithm: str = "quicksort", array: Optional[List[int]] = None) -> str:
        """Generate dynamic sorting visualization"""
        if array is None:
            array = [64, 34, 25, 12, 22, 11, 90, 88]
        
        array_str = str(array)
        
        if algorithm.lower() in ["quick", "quicksort"]:
            return self._generate_quicksort(array_str)
        elif algorithm.lower() in ["merge", "mergesort"]:
            return self._generate_mergesort(array_str)
        elif algorithm.lower() in ["bubble", "bubblesort"]:
            return self._generate_bubblesort(array_str)
        else:
            return self._generate_bubblesort(array_str)
    
    def _generate_bubblesort(self, array_str: str) -> str:
        return f'''
class BubbleSortScene(Scene):
    def construct(self):
        # Title
        title = Text("Bubble Sort Algorithm", font_size=36, color=BLUE, weight=BOLD)
        title.to_edge(UP, buff=0.3)
        self.play(Write(title), run_time=1)
        
        # Array
        arr = {array_str}
        n = len(arr)
        
        # Create bars
        max_val = max(arr)
        bars = VGroup()
        bar_labels = VGroup()
        
        bar_width = min(0.6, 8.0 / n)
        
        for i, val in enumerate(arr):
            height = (val / max_val) * 3 + 0.5
            bar = Rectangle(
                width=bar_width,
                height=height,
                fill_color=BLUE,
                fill_opacity=0.7,
                stroke_color=WHITE,
                stroke_width=2
            )
            bar.shift(RIGHT * i * (bar_width + 0.1) + DOWN * 0.5)
            bar.align_to(DOWN * 2, DOWN)
            
            label = Text(str(val), font_size=int(18 * bar_width), color=WHITE)
            label.next_to(bar, DOWN, buff=0.1)
            
            bars.add(bar)
            bar_labels.add(label)
        
        bars.center()
        bar_labels.center()
        
        self.play(FadeIn(bars), FadeIn(bar_labels), run_time=1)
        
        # Status
        status = Text("Starting Bubble Sort...", font_size=20, color=WHITE)
        status.to_edge(DOWN, buff=0.3)
        self.play(Write(status), run_time=0.5)
        
        # Bubble sort algorithm
        comparisons = 0
        swaps = 0
        
        for i in range(n):
            swapped = False
            for j in range(n - i - 1):
                # Highlight comparing elements
                self.play(
                    bars[j].animate.set_fill(YELLOW, opacity=0.9),
                    bars[j+1].animate.set_fill(YELLOW, opacity=0.9),
                    run_time=0.2
                )
                
                comparisons += 1
                comp_text = f"Comparing: {{arr[j]}} vs {{arr[j+1]}}"
                new_status = Text(comp_text, font_size=20, color=YELLOW)
                new_status.to_edge(DOWN, buff=0.3)
                self.play(Transform(status, new_status), run_time=0.2)
                
                if arr[j] > arr[j+1]:
                    # Swap
                    swaps += 1
                    arr[j], arr[j+1] = arr[j+1], arr[j]
                    
                    swap_text = f"Swapping {{arr[j+1]}} and {{arr[j]}}"
                    new_status = Text(swap_text, font_size=20, color=RED)
                    new_status.to_edge(DOWN, buff=0.3)
                    self.play(Transform(status, new_status), run_time=0.2)
                    
                    # Animate swap
                    self.play(
                        bars[j].animate.shift(RIGHT * (bar_width + 0.1)),
                        bars[j+1].animate.shift(LEFT * (bar_width + 0.1)),
                        bar_labels[j].animate.shift(RIGHT * (bar_width + 0.1)),
                        bar_labels[j+1].animate.shift(LEFT * (bar_width + 0.1)),
                        run_time=0.4
                    )
                    
                    # Swap in groups
                    bars[j], bars[j+1] = bars[j+1], bars[j]
                    bar_labels[j], bar_labels[j+1] = bar_labels[j+1], bar_labels[j]
                    
                    swapped = True
                
                # Reset colors
                self.play(
                    bars[j].animate.set_fill(BLUE, opacity=0.7),
                    bars[j+1].animate.set_fill(BLUE, opacity=0.7) if j+1 < n-i-1 else bars[j+1].animate.set_fill(GREEN, opacity=0.7),
                    run_time=0.2
                )
                
                self.wait(0.1)
            
            # Mark sorted element
            self.play(
                bars[n-i-1].animate.set_fill(GREEN, opacity=0.9),
                run_time=0.3
            )
            
            if not swapped:
                break
        
        # Mark all as sorted
        self.play(
            *[bars[i].animate.set_fill(GREEN, opacity=0.9) for i in range(n)],
            run_time=0.5
        )
        
        # Final status
        final_text = f"Sorted! Comparisons: {{comparisons}}, Swaps: {{swaps}}"
        new_status = Text(final_text, font_size=20, color=GOLD)
        new_status.to_edge(DOWN, buff=0.3)
        self.play(Transform(status, new_status), run_time=0.5)
        
        self.wait(2)
'''
    
    def _generate_quicksort(self, array_str: str) -> str:
        return f'''
class QuickSortScene(Scene):
    def construct(self):
        title = Text("Quick Sort Algorithm", font_size=36, color=PURPLE, weight=BOLD)
        title.to_edge(UP, buff=0.3)
        self.play(Write(title), run_time=1)
        
        arr = {array_str}
        n = len(arr)
        
        # Create bars
        max_val = max(arr)
        bars = VGroup()
        bar_labels = VGroup()
        bar_width = min(0.6, 8.0 / n)
        
        for i, val in enumerate(arr):
            height = (val / max_val) * 3 + 0.5
            bar = Rectangle(width=bar_width, height=height, fill_color=PURPLE,
                          fill_opacity=0.7, stroke_color=WHITE, stroke_width=2)
            bar.shift(RIGHT * i * (bar_width + 0.1) + DOWN * 0.5)
            bar.align_to(DOWN * 2, DOWN)
            
            label = Text(str(val), font_size=int(18 * bar_width), color=WHITE)
            label.next_to(bar, DOWN, buff=0.1)
            
            bars.add(bar)
            bar_labels.add(label)
        
        bars.center()
        bar_labels.center()
        self.play(FadeIn(bars), FadeIn(bar_labels), run_time=1)
        
        status = Text("Starting Quick Sort...", font_size=20, color=WHITE)
        status.to_edge(DOWN, buff=0.3)
        self.play(Write(status), run_time=0.5)
        
        # Quick sort with visualization
        def partition_viz(low, high):
            pivot_val = arr[high]
            
            # Highlight pivot
            self.play(bars[high].animate.set_fill(GOLD, opacity=0.9), run_time=0.3)
            pivot_text = f"Pivot: {{pivot_val}}"
            new_status = Text(pivot_text, font_size=20, color=GOLD)
            new_status.to_edge(DOWN, buff=0.3)
            self.play(Transform(status, new_status), run_time=0.3)
            
            i = low - 1
            
            for j in range(low, high):
                # Highlight current element
                self.play(bars[j].animate.set_fill(YELLOW, opacity=0.9), run_time=0.2)
                
                if arr[j] < pivot_val:
                    i += 1
                    if i != j:
                        # Swap
                        arr[i], arr[j] = arr[j], arr[i]
                        self.play(
                            bars[i].animate.shift(RIGHT * (j - i) * (bar_width + 0.1)),
                            bars[j].animate.shift(LEFT * (j - i) * (bar_width + 0.1)),
                            bar_labels[i].animate.shift(RIGHT * (j - i) * (bar_width + 0.1)),
                            bar_labels[j].animate.shift(LEFT * (j - i) * (bar_width + 0.1)),
                            run_time=0.4
                        )
                        bars[i], bars[j] = bars[j], bars[i]
                        bar_labels[i], bar_labels[j] = bar_labels[j], bar_labels[i]
                
                self.play(bars[j].animate.set_fill(PURPLE, opacity=0.7), run_time=0.2)
            
            # Place pivot in correct position
            i += 1
            if i != high:
                arr[i], arr[high] = arr[high], arr[i]
                self.play(
                    bars[i].animate.shift(RIGHT * (high - i) * (bar_width + 0.1)),
                    bars[high].animate.shift(LEFT * (high - i) * (bar_width + 0.1)),
                    bar_labels[i].animate.shift(RIGHT * (high - i) * (bar_width + 0.1)),
                    bar_labels[high].animate.shift(LEFT * (high - i) * (bar_width + 0.1)),
                    run_time=0.4
                )
                bars[i], bars[high] = bars[high], bars[i]
                bar_labels[i], bar_labels[high] = bar_labels[high], bar_labels[i]
            
            self.play(bars[i].animate.set_fill(GREEN, opacity=0.9), run_time=0.3)
            return i
        
        def quicksort_viz(low, high):
            if low < high:
                pi = partition_viz(low, high)
                quicksort_viz(low, pi - 1)
                quicksort_viz(pi + 1, high)
        
        quicksort_viz(0, n - 1)
        
        self.play(*[bars[i].animate.set_fill(GREEN, opacity=0.9) for i in range(n)], run_time=0.5)
        final_text = "Quick Sort Complete!"
        new_status = Text(final_text, font_size=24, color=GOLD, weight=BOLD)
        new_status.to_edge(DOWN, buff=0.3)
        self.play(Transform(status, new_status), run_time=0.5)
        self.wait(2)
'''
    
    def _generate_mergesort(self, array_str: str) -> str:
        return f'''
class MergeSortScene(Scene):
    def construct(self):
        title = Text("Merge Sort - Divide & Conquer", font_size=36, color=TEAL, weight=BOLD)
        title.to_edge(UP, buff=0.3)
        self.play(Write(title), run_time=1)
        
        # Simple merge sort visualization with recursive tree
        arr = {array_str}
        
        text = Text(f"Array: {{arr}}", font_size=24, color=WHITE)
        self.play(Write(text), run_time=1)
        self.wait(1)
        
        divide_text = Text("Dividing array recursively...", font_size=20, color=YELLOW)
        divide_text.shift(DOWN)
        self.play(Write(divide_text), run_time=0.5)
        self.wait(1)
        
        merge_text = Text("Merging sorted subarrays...", font_size=20, color=GREEN)
        merge_text.shift(DOWN * 1.5)
        self.play(Write(merge_text), run_time=0.5)
        self.wait(1)
        
        sorted_arr = sorted(arr)
        result = Text(f"Sorted: {{sorted_arr}}", font_size=24, color=GOLD, weight=BOLD)
        result.shift(DOWN * 2.5)
        self.play(Write(result), run_time=1)
        self.wait(2)
'''


class BacktrackingVisualizer(AlgorithmVisualizer):
    """Visualizer for backtracking algorithms"""
    
    def generate_manim_code(self, problem_type: str = "sudoku", **kwargs) -> str:
        """Generate backtracking visualization"""
        if problem_type.lower() == "nqueens":
            return NQueensVisualizer().generate_manim_code(**kwargs)
        # Add more backtracking problems here
        return NQueensVisualizer().generate_manim_code(**kwargs)


class GraphVisualizer(AlgorithmVisualizer):
    """Visualizer for graph algorithms (DFS, BFS, Dijkstra)"""
    
    def generate_manim_code(self, algorithm: str = "bfs", **kwargs) -> str:
        """Generate graph algorithm visualization"""
        if algorithm.lower() in ["bfs", "breadth-first"]:
            return self._generate_bfs()
        elif algorithm.lower() in ["dfs", "depth-first"]:
            return self._generate_dfs()
        else:
            return self._generate_bfs()
    
    def _generate_bfs(self) -> str:
        return '''
class BFSScene(Scene):
    def construct(self):
        title = Text("Breadth-First Search (BFS)", font_size=36, color=BLUE, weight=BOLD)
        title.to_edge(UP, buff=0.3)
        self.play(Write(title), run_time=1)
        
        # Create graph
        vertices = {
            "A": UP * 2,
            "B": LEFT * 2,
            "C": RIGHT * 2,
            "D": DOWN * 1 + LEFT * 2,
            "E": DOWN * 1 + RIGHT * 2,
            "F": DOWN * 2.5
        }
        
        edges = [
            ("A", "B"), ("A", "C"),
            ("B", "D"), ("C", "E"),
            ("D", "F"), ("E", "F")
        ]
        
        # Create nodes
        nodes = {}
        labels = {}
        for name, pos in vertices.items():
            node = Circle(radius=0.4, color=BLUE, fill_opacity=0.3, stroke_width=3)
            node.move_to(pos)
            label = Text(name, font_size=28, color=WHITE, weight=BOLD)
            label.move_to(pos)
            nodes[name] = node
            labels[name] = label
        
        # Create edges
        edge_lines = VGroup()
        for start, end in edges:
            line = Line(nodes[start].get_center(), nodes[end].get_center(), 
                       color=GRAY, stroke_width=2)
            edge_lines.add(line)
        
        # Draw graph
        self.play(Create(edge_lines), run_time=1)
        self.play(*[Create(n) for n in nodes.values()], 
                 *[Write(l) for l in labels.values()], run_time=1)
        
        # BFS traversal
        status = Text("Starting BFS from A", font_size=20, color=WHITE)
        status.to_edge(DOWN, buff=0.3)
        self.play(Write(status), run_time=0.5)
        
        # Queue visualization
        queue_text = Text("Queue: ", font_size=18, color=YELLOW)
        queue_text.to_corner(DR, buff=0.5).shift(UP * 0.5)
        queue_display = Text("[]", font_size=18, color=YELLOW)
        queue_display.next_to(queue_text, RIGHT, buff=0.2)
        self.play(Write(queue_text), Write(queue_display), run_time=0.3)
        
        visited = set()
        queue = ["A"]
        
        # Update queue display
        new_queue = Text("[A]", font_size=18, color=YELLOW)
        new_queue.next_to(queue_text, RIGHT, buff=0.2)
        self.play(Transform(queue_display, new_queue), run_time=0.3)
        
        # BFS execution
        visit_order = []
        adjacency = {
            "A": ["B", "C"],
            "B": ["A", "D"],
            "C": ["A", "E"],
            "D": ["B", "F"],
            "E": ["C", "F"],
            "F": ["D", "E"]
        }
        
        while queue:
            current = queue.pop(0)
            
            if current not in visited:
                visited.add(current)
                visit_order.append(current)
                
                # Highlight current node
                self.play(
                    nodes[current].animate.set_fill(GREEN, opacity=0.7),
                    nodes[current].animate.set_stroke(GREEN, width=5),
                    labels[current].animate.set_color(BLACK),
                    run_time=0.4
                )
                
                visit_text = f"Visiting: {{current}}"
                new_status = Text(visit_text, font_size=20, color=GREEN)
                new_status.to_edge(DOWN, buff=0.3)
                self.play(Transform(status, new_status), run_time=0.3)
                
                # Add neighbors to queue
                for neighbor in adjacency[current]:
                    if neighbor not in visited and neighbor not in queue:
                        queue.append(neighbor)
                
                # Update queue display
                queue_str = str(queue) if queue else "[]"
                new_queue = Text(queue_str, font_size=18, color=YELLOW)
                new_queue.next_to(queue_text, RIGHT, buff=0.2)
                self.play(Transform(queue_display, new_queue), run_time=0.3)
                
                self.wait(0.5)
        
        # Show traversal order
        order_text = f"Traversal Order: {{' → '.join(visit_order)}}"
        final = Text(order_text, font_size=20, color=GOLD, weight=BOLD)
        final.to_edge(DOWN, buff=0.3)
        self.play(Transform(status, final), run_time=0.5)
        
        self.wait(2)
'''
    
    def _generate_dfs(self) -> str:
        return '''
class DFSScene(Scene):
    def construct(self):
        title = Text("Depth-First Search (DFS)", font_size=36, color=RED, weight=BOLD)
        title.to_edge(UP, buff=0.3)
        self.play(Write(title), run_time=1)
        
        # Similar to BFS but with stack and different order
        # ... implementation similar to BFS but depth-first
        self.wait(2)
'''


def get_visualizer_for_problem(problem_description: str, solution_approach: str) -> Optional[Tuple[AlgorithmVisualizer, Dict[str, Any]]]:
    """
    Detect the appropriate visualizer based on problem description
    
    Returns:
        Tuple of (visualizer instance, kwargs dict) or None
    """
    text = (problem_description + " " + solution_approach).lower()
    
    # N-Queens detection
    if "n-queen" in text or "n queen" in text or "nqueen" in text or "queens" in text:
        n = 4  # default
        # Try to extract n
        import re
        match = re.search(r'(\d+)[-\s]*queen', text)
        if match:
            n = int(match.group(1))
        return (NQueensVisualizer(), {"n": min(n, 8), "show_steps": 20})
    
    # Sorting algorithms
    if any(sort in text for sort in ["quick sort", "quicksort", "merge sort", "mergesort", 
                                      "bubble sort", "bubblesort", "sort"]):
        algo_type = "quicksort"
        if "bubble" in text:
            algo_type = "bubblesort"
        elif "merge" in text:
            algo_type = "mergesort"
        elif "quick" in text:
            algo_type = "quicksort"
        
        return (SortingVisualizer(), {"algorithm": algo_type})
    
    # Graph algorithms
    if any(graph in text for graph in ["bfs", "breadth-first", "breadth first", 
                                        "dfs", "depth-first", "depth first",
                                        "dijkstra", "graph traversal"]):
        algo_type = "bfs"
        if "dfs" in text or "depth" in text:
            algo_type = "dfs"
        elif "bfs" in text or "breadth" in text:
            algo_type = "bfs"
        
        return (GraphVisualizer(), {"algorithm": algo_type})
    
    # Backtracking
    if "backtrack" in text:
        return (BacktrackingVisualizer(), {"problem_type": "nqueens"})
    
    return None
