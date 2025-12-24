"""
Video Generator module using Manim for creating educational DSA explanation videos
with proper animations, visual data structures, and algorithm visualizations
"""

import os
import re
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from pragyan.models import Question, Solution, VideoConfig, AnimationScene
from pragyan.algorithm_visualizers import get_visualizer_for_problem


class VideoGenerator:
    """
    Generates educational videos explaining DSA problems and solutions using Manim
    with proper animations, visual data structures, and algorithm visualizations
    """
    
    def __init__(self, config: Optional[VideoConfig] = None):
        self.config = config or VideoConfig()
        self._temp_dir = None
        self._verify_manim_installation()
        self.llm_client = None  # Can be set later for LLM-powered animations
        self._scene_class_name = "DSAExplanation"  # Track which scene class to render
    
    def set_llm_client(self, llm_client):
        """Set LLM client for advanced animation generation"""
        self.llm_client = llm_client
    
    def _verify_manim_installation(self):
        """Verify that Manim is properly installed"""
        try:
            import manim
            self.manim_version = manim.__version__
        except ImportError:
            raise ImportError(
                "Manim is not installed. Please install it with: pip install manim\n"
                "You may also need to install additional dependencies. "
                "See: https://docs.manim.community/en/stable/installation.html"
            )
    
    def _get_temp_dir(self) -> Path:
        if self._temp_dir is None:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="pragyan_"))
        return self._temp_dir
    
    def _cleanup_temp_dir(self):
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None
    
    def generate_video(
        self,
        question: Question,
        solution: Solution,
        analysis: Dict[str, Any],
        video_script: Optional[List[Dict[str, Any]]] = None,
        output_filename: Optional[str] = None
    ) -> Path:
        temp_dir = self._get_temp_dir()
        
        # Always use LLM to generate dynamic, problem-specific animation code
        if self.llm_client:
            scene_code, self._scene_class_name = self._generate_dynamic_scene(
                question, solution, analysis
            )
        else:
            # Fallback to generic animated scene if no LLM
            scene_code = self._generate_animated_scene(question, solution, analysis)
            self._scene_class_name = "DSAExplanation"
        
        scene_file = temp_dir / "dsa_explanation.py"
        with open(scene_file, "w", encoding="utf-8") as f:
            f.write(scene_code)
        
        # Debug: save a copy of the generated code (silent)
        debug_file = Path.cwd() / "last_generated_scene.py"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(scene_code)
        
        output_path = self._render_video(scene_file, output_filename, self._scene_class_name)
        return output_path
    
    def _escape_for_python(self, s: str, max_len: int = 500) -> str:
        """Escape string for Python code embedding"""
        if not s:
            return ""
        s = s[:max_len]
        s = s.replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        s = s.replace("'", "\\'")
        s = s.replace('\n', ' ')
        s = s.replace('\r', '')
        s = s.replace('\t', ' ')
        s = ''.join(c for c in s if c.isprintable() or c == ' ')
        return s
    
    def _extract_example_array(self, question: Question) -> str:
        """Try to extract an example array from the question"""
        # Handle examples that might be dicts or strings
        examples_text = ""
        if question.examples:
            for ex in question.examples:
                if isinstance(ex, dict):
                    examples_text += " " + str(ex.get("input", "")) + " " + str(ex.get("output", ""))
                elif isinstance(ex, str):
                    examples_text += " " + ex
        
        text = question.description + " " + examples_text
        
        # Look for patterns like [1, 2, 3] or nums = [1, 2, 3]
        patterns = [
            r'\[[\d,\s-]+\]',
            r'nums\s*=\s*\[[\d,\s-]+\]',
            r'arr\s*=\s*\[[\d,\s-]+\]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Extract just the array part
                arr_match = re.search(r'\[([\d,\s-]+)\]', match.group())
                if arr_match:
                    try:
                        arr_str = "[" + arr_match.group(1) + "]"
                        # Validate it's a valid list
                        arr = eval(arr_str)
                        if isinstance(arr, list) and len(arr) >= 2 and len(arr) <= 10:
                            return str(arr)
                    except:
                        pass
        
        # Default example array
        return "[3, 1, 4, 1, 5, 9, 2, 6]"
    
    def _detect_algorithm_type(self, analysis: Dict[str, Any], solution: Solution) -> str:
        """Detect algorithm type for visualization"""
        concept = (solution.concept + " " + solution.approach).lower()
        topics = [t.lower() for t in analysis.get("topics", [])]
        
        if any(x in concept for x in ["two pointer", "two-pointer"]):
            return "two_pointer"
        elif any(x in concept for x in ["sliding window"]):
            return "sliding_window"
        elif any(x in concept for x in ["binary search"]):
            return "binary_search"
        elif any(x in concept for x in ["hash", "dictionary", "map"]):
            return "hash_map"
        elif any(x in concept for x in ["dynamic", "dp", "memoization"]):
            return "dp"
        elif any(x in concept for x in ["stack"]):
            return "stack"
        elif any(x in concept for x in ["queue", "bfs"]):
            return "queue"
        elif any(x in concept for x in ["tree", "dfs"]):
            return "tree"
        elif any(x in concept for x in ["linked list"]):
            return "linked_list"
        elif any(x in concept for x in ["sort"]):
            return "sorting"
        elif any(x in concept for x in ["graph"]):
            return "graph"
        elif any(x in concept for x in ["backtrack", "n-queen", "queen"]):
            return "backtracking"
        elif "array" in topics or "string" in topics:
            return "array"
        return "array"
    
    def _generate_dynamic_scene(
        self,
        question: Question,
        solution: Solution,
        analysis: Dict[str, Any]
    ) -> tuple:
        """
        Use LLM to generate complete, dynamic Manim scene code for the specific problem.
        This creates a unique visualization tailored to the exact algorithm and problem.
        
        Returns:
            tuple: (scene_code, scene_class_name)
        """
        # Detect algorithm type for better prompting
        algo_type = self._detect_algorithm_type(analysis, solution)
        
        # Get example from question
        example_input = ""
        if question.examples:
            ex = question.examples[0]
            if isinstance(ex, dict):
                example_input = str(ex.get("input", ""))
            else:
                example_input = str(ex)
        
        # Build comprehensive prompt for LLM
        prompt = f'''Generate a complete Manim Community Edition scene that creates an educational video explaining this algorithm.

PROBLEM: {question.title}
DESCRIPTION: {question.description[:800]}
EXAMPLE INPUT: {example_input}

SOLUTION APPROACH: {solution.concept}
ALGORITHM TYPE: {algo_type}
TIME COMPLEXITY: {solution.time_complexity}
SPACE COMPLEXITY: {solution.space_complexity}

SOLUTION CODE:
```
{solution.code[:1500] if solution.code else "# No code provided"}
```

CRITICAL: THE VIDEO MUST BE 60-120 SECONDS LONG. Use longer run_time values and more self.wait() calls.

REQUIREMENTS FOR THE VIDEO (60-120 seconds MINIMUM):
1. **INTRO (10-15 seconds)**: 
   - Animated title with problem name (run_time=2)
   - Brief problem statement explanation with Text animations (run_time=3)
   - Show the example input visually (run_time=3)
   - self.wait(2) after each section

2. **ALGORITHM EXPLANATION (15-20 seconds)**:
   - Explain the approach/strategy being used step by step
   - Show key insight or pattern with visual diagrams
   - List each step of the algorithm with bullet animations
   - Use run_time=2-3 for each animation
   - self.wait(1.5) between explanations

3. **STEP-BY-STEP VISUALIZATION (30-50 seconds)** - THIS IS THE MAIN PART:
   - Create appropriate visual representation for the data structures
   - Show EACH step of the algorithm executing with SLOW animations (run_time=1.5-2.5)
   - Use colors: BLUE for current, GREEN for done, RED for backtrack/invalid, YELLOW for comparing
   - Add status text showing what's happening at each step
   - Include counters (comparisons, iterations, etc.)
   - self.wait(1) after each major step
   - For loops/iterations, show at least 3-5 iterations with full animation

4. **RESULT & COMPLEXITY (10-15 seconds)**:
   - Show final answer/solution with celebration animation (run_time=2)
   - Display Time and Space complexity in nice boxes (run_time=2)
   - Key takeaways (3 bullet points, each with run_time=1.5)
   - self.wait(2) after result

5. **OUTRO (5-8 seconds)**:
   - "Generated by Pragyan" branding with fade animation
   - self.wait(3) at the end

ANIMATION TIMING REQUIREMENTS (CRITICAL):
- NEVER use run_time less than 1.0 for any animation
- Use run_time=2.0 to 3.0 for important animations (title, explanations)
- Use run_time=1.5 for step-by-step visualizations
- Add self.wait(1.0) to self.wait(2.0) between each major section
- Add self.wait(0.5) between small animations within a section
- Total animation time MUST exceed 60 seconds

MANIM CODE REQUIREMENTS:
- Use `from manim import *`
- Class must be named `AlgorithmScene` and extend `Scene`
- Use these colors: GOLD, BLUE, GREEN, RED, YELLOW, WHITE, GRAY, PURPLE
- Keep text readable: title 36-48px, body 18-24px
- Position elements clearly - use `.to_edge()`, `.shift()`, `.next_to()`
- Make it visually engaging with smooth transitions

CRITICAL - TEXT RENDERING:
- ONLY use `Text()` for ALL text - NEVER use `Tex()`, `MathTex()`, or any LaTeX
- For math symbols, write them as plain text: "O(n²)" not "$O(n^2)$"
- Use `Text("x * y")` not `MathTex("x \\times y")`
- This is required because LaTeX is not installed

Generate ONLY the Python code, no markdown, no explanation. Start with `from manim import *`'''

        system_prompt = """You are an expert Manim animator who creates beautiful, educational algorithm visualization videos.
You write clean, working Manim Community Edition code that produces engaging 45-90 second educational videos.
Always include proper intro, step-by-step algorithm visualization, and complexity analysis.
Make the visualizations dynamic and educational - show the algorithm actually running, not just static slides.
Your code must be syntactically correct and render without errors.
IMPORTANT: Never use Tex, MathTex, or any LaTeX - only use Text() for all text rendering."""

        try:
            # Generate code from LLM
            raw_response = self.llm_client.generate(prompt, system_prompt)
            
            # Clean the response - extract just the Python code
            scene_code = self._extract_manim_code(raw_response)
            
            # Add config header
            final_code = f'''"""
Dynamically generated Manim scene by Pragyan
Problem: {self._escape_for_python(question.title, 100)}
Generated using LLM-powered visualization
"""

from manim import *
import numpy as np

config.pixel_height = {self.config.pixel_height}
config.pixel_width = {self.config.pixel_width}
config.frame_rate = {self.config.fps}
config.background_color = "{self.config.background_color}"

'''
            # Add the generated scene code (removing duplicate imports if present)
            scene_code_cleaned = scene_code.replace("from manim import *", "").strip()
            scene_code_cleaned = scene_code_cleaned.replace("import numpy as np", "").strip()
            
            final_code += scene_code_cleaned
            
            return final_code, "AlgorithmScene"
            
        except Exception as e:
            # LLM scene generation failed, fall back silently
            return self._generate_animated_scene(question, solution, analysis), "DSAExplanation"
    
    def _extract_manim_code(self, response: str) -> str:
        """Extract clean Manim code from LLM response"""
        # Remove markdown code blocks
        code = response.strip()
        
        if "```python" in code:
            code = code.split("```python")[1]
            if "```" in code:
                code = code.split("```")[0]
        elif "```" in code:
            parts = code.split("```")
            if len(parts) >= 2:
                code = parts[1]
        
        code = code.strip()
        
        # Ensure it starts with from manim import * if not present
        if not code.startswith("from manim"):
            code = "from manim import *\n\n" + code
        
        # CRITICAL: Replace Tex/MathTex with Text to avoid LaTeX dependency
        # This handles cases where LLM ignores the instruction
        code = re.sub(r'\bTex\s*\(', 'Text(', code)
        code = re.sub(r'\bMathTex\s*\(', 'Text(', code)
        # Remove LaTeX-specific arguments that Text doesn't support
        code = re.sub(r',\s*tex_environment\s*=\s*["\'][^"\']*["\']', '', code)
        code = re.sub(r',\s*tex_template\s*=\s*[^,\)]+', '', code)
        # Clean up LaTeX syntax in strings (basic conversion)
        code = code.replace(r'\times', '×')
        code = code.replace(r'\cdot', '·')
        code = code.replace(r'\leq', '≤')
        code = code.replace(r'\geq', '≥')
        code = code.replace(r'\neq', '≠')
        code = code.replace(r'\rightarrow', '→')
        code = code.replace(r'\leftarrow', '←')
        
        return code

    def _generate_specialized_scene(
        self,
        question: Question,
        solution: Solution,
        analysis: Dict[str, Any],
        visualizer,
        kwargs: Dict[str, Any]
    ) -> tuple:
        """Generate a scene using specialized algorithm visualizer
        
        Returns:
            tuple: (scene_code, scene_class_name)
        """
        
        # Get the algorithm-specific animation code
        algorithm_scene_code = visualizer.generate_manim_code(**kwargs)
        
        # Extract the scene class name from the generated code
        import re
        class_match = re.search(r'class\s+(\w+Scene)\s*\(Scene\)', algorithm_scene_code)
        scene_class_name = class_match.group(1) if class_match else "DSAExplanation"
        
        # Build the complete scene file with just the algorithm scene
        # The algorithm scene already has all the visualization logic
        scene_code = f'''"""
Manim scene for DSA explanation video - Generated by Pragyan
Algorithm-specific visualization: {scene_class_name}
"""

from manim import *
import numpy as np
import textwrap

config.pixel_height = {self.config.pixel_height}
config.pixel_width = {self.config.pixel_width}
config.frame_rate = {self.config.fps}
config.background_color = "{self.config.background_color}"

'''
        
        # Combine header with the algorithm-specific scene code
        final_code = scene_code + algorithm_scene_code
        
        return final_code, scene_class_name
    
    def _generate_llm_powered_scene(
        self,
        question: Question,
        solution: Solution,
        analysis: Dict[str, Any]
    ) -> str:
        """Generate a scene using LLM to create custom animations"""
        if not self.llm_client:
            return self._generate_animated_scene(question, solution, analysis)
        
        try:
            # Get detailed animation steps from LLM
            animation_steps = self.llm_client.generate_algorithm_animation_steps(
                question, solution, analysis
            )
            
            # TODO: Convert animation steps to Manim code
            # For now, fallback to generic
            return self._generate_animated_scene(question, solution, analysis)
        except Exception:
            # Silent fallback
            return self._generate_animated_scene(question, solution, analysis)
    
    def _generate_animated_scene(
        self,
        question: Question,
        solution: Solution,
        analysis: Dict[str, Any]
    ) -> str:
        """Generate Manim scene with proper animations and visualizations"""
        
        title = self._escape_for_python(question.title, 100)
        concept = self._escape_for_python(solution.concept, 200)
        approach = self._escape_for_python(solution.approach, 300)
        time_comp = self._escape_for_python(solution.time_complexity, 50)
        space_comp = self._escape_for_python(solution.space_complexity, 50)
        
        # Get topics
        topics = analysis.get("topics", [])
        topics_str = ", ".join(str(t) for t in topics[:4])
        topics_str = self._escape_for_python(topics_str, 100)
        
        # Get example array
        example_arr = self._extract_example_array(question)
        
        # Detect algorithm type
        algo_type = self._detect_algorithm_type(analysis, solution)
        
        # Generate step-by-step as Python list
        steps = solution.step_by_step[:5] if solution.step_by_step else []
        steps_list = "[" + ", ".join(f'"{self._escape_for_python(str(s), 100)}"' for s in steps) + "]"
        
        # Prepare code lines (first 15 lines only)
        code_lines = solution.code.split('\n')[:15] if solution.code else ["# Solution code"]
        code_for_display = []
        for line in code_lines:
            clean_line = self._escape_for_python(line, 80)
            code_for_display.append(clean_line)
        code_list = "[" + ", ".join(f'"{line}"' for line in code_for_display) + "]"
        
        # Build scene code - use f-string ONLY for the header with variable substitution
        scene_header = f'''"""
Manim scene for DSA explanation video - Generated by Pragyan
"""

from manim import *
import numpy as np
import textwrap

config.pixel_height = {self.config.pixel_height}
config.pixel_width = {self.config.pixel_width}
config.frame_rate = {self.config.fps}
config.background_color = "{self.config.background_color}"


class DSAExplanation(Scene):
    def construct(self):
        # Data
        title = "{title}"
        concept = "{concept}"
        approach = "{approach}"
        time_complexity = "{time_comp}"
        space_complexity = "{space_comp}"
        topics = "{topics_str}"
        example_arr = {example_arr}
        algo_type = "{algo_type}"
        steps = {steps_list}
        code_lines = {code_list}
        
        # Run scenes
        self.intro_scene(title, topics)
        self.concept_scene(concept)
        self.data_structure_scene(example_arr)
        self.algorithm_scene(example_arr, algo_type)
        self.code_scene(code_lines)
        self.complexity_scene(time_complexity, space_complexity)
        self.outro_scene(title)
'''
        
        # The rest is a regular string with NO f-string formatting
        # This avoids the issue with loop variables like {i} being interpreted
        scene_body = '''
    def clear_all(self):
        if self.mobjects:
            self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)
    
    def intro_scene(self, title, topics):
        # Title
        title_text = Text(title[:50], font_size=42, color=WHITE, weight=BOLD)
        title_text.to_edge(UP, buff=1.2)
        
        underline = Line(
            title_text.get_left() + DOWN*0.3,
            title_text.get_right() + DOWN*0.3,
            color=BLUE
        )
        
        self.play(Write(title_text), run_time=1.5)
        self.play(Create(underline), run_time=0.5)
        
        # Topics as badges
        if topics:
            topic_list = [t.strip() for t in topics.split(",")][:4]
            badges = VGroup()
            for topic in topic_list:
                badge = VGroup(
                    RoundedRectangle(
                        width=len(topic)*0.15 + 0.6,
                        height=0.5,
                        corner_radius=0.2,
                        fill_color=BLUE_E,
                        fill_opacity=0.8,
                        stroke_color=BLUE
                    ),
                    Text(topic, font_size=18, color=WHITE)
                )
                badge[1].move_to(badge[0])
                badges.add(badge)
            
            badges.arrange(RIGHT, buff=0.3)
            badges.next_to(title_text, DOWN, buff=0.8)
            
            self.play(
                *[FadeIn(b, shift=UP*0.3) for b in badges],
                run_time=1
            )
        
        # DSA icon - tree structure
        root = Circle(radius=0.25, color=GOLD, fill_opacity=0.8)
        left = Circle(radius=0.2, color=BLUE, fill_opacity=0.8).shift(LEFT*0.8 + DOWN*0.7)
        right = Circle(radius=0.2, color=GREEN, fill_opacity=0.8).shift(RIGHT*0.8 + DOWN*0.7)
        edge1 = Line(root.get_center(), left.get_center(), color=WHITE)
        edge2 = Line(root.get_center(), right.get_center(), color=WHITE)
        dsa_icon = VGroup(edge1, edge2, root, left, right).scale(0.8).shift(DOWN*1.5)
        
        self.play(GrowFromCenter(dsa_icon), run_time=1)
        
        self.wait(1.5)
        self.clear_all()
    
    def concept_scene(self, concept):
        header = Text("Core Concept", font_size=36, color=ORANGE, weight=BOLD)
        header.to_edge(UP, buff=0.5)
        self.play(Write(header), run_time=0.5)
        
        concept_short = concept[:100] + "..." if len(concept) > 100 else concept
        wrapped = "\\n".join(textwrap.wrap(concept_short, 40))
        
        concept_box = VGroup(
            RoundedRectangle(
                width=9, height=2.5,
                corner_radius=0.3,
                fill_color="#1a1a2e",
                fill_opacity=0.9,
                stroke_color=ORANGE,
                stroke_width=2
            ),
            Text(wrapped, font_size=22, color=WHITE)
        )
        concept_box[1].move_to(concept_box[0])
        concept_box.next_to(header, DOWN, buff=0.6)
        
        self.play(FadeIn(concept_box[0], scale=0.9), Write(concept_box[1]), run_time=1.5)
        
        self.wait(2)
        self.clear_all()
    
    def data_structure_scene(self, arr):
        header = Text("Data Structure", font_size=32, color=GREEN, weight=BOLD)
        header.to_edge(UP, buff=0.5)
        self.play(Write(header), run_time=0.5)
        
        arr = arr[:8]  # Limit size
        n = len(arr)
        box_size = min(0.8, 6.0 / n)
        
        boxes = VGroup()
        values = VGroup()
        indices = VGroup()
        
        for idx, val in enumerate(arr):
            box = Square(
                side_length=box_size,
                color=BLUE,
                fill_opacity=0.2,
                stroke_width=2
            ).shift(RIGHT * idx * (box_size + 0.1))
            boxes.add(box)
            
            value = Text(str(val), font_size=int(20 * box_size), color=WHITE)
            value.move_to(box.get_center())
            values.add(value)
            
            idx_text = Text(str(idx), font_size=int(14 * box_size), color=GRAY)
            idx_text.next_to(box, DOWN, buff=0.15)
            indices.add(idx_text)
        
        array_viz = VGroup(boxes, values, indices)
        array_viz.center().next_to(header, DOWN, buff=1)
        
        self.play(*[GrowFromCenter(box) for box in boxes], run_time=1)
        self.play(*[Write(val) for val in values], run_time=0.8)
        self.play(*[FadeIn(idx) for idx in indices], run_time=0.5)
        
        # Properties
        props = VGroup(
            Text(f"Length: {n}", font_size=20, color=YELLOW),
            Text("Type: Integer Array", font_size=20, color=YELLOW),
        ).arrange(RIGHT, buff=1).shift(DOWN*2)
        
        self.play(FadeIn(props), run_time=0.5)
        
        self.wait(2)
        self.clear_all()
    
    def algorithm_scene(self, arr, algo_type):
        header = Text("Algorithm Walkthrough", font_size=32, color=PURPLE, weight=BOLD)
        header.to_edge(UP, buff=0.5)
        self.play(Write(header), run_time=0.5)
        
        arr = arr[:8]
        n = len(arr)
        box_size = min(0.8, 6.0 / n)
        
        boxes = VGroup()
        values = VGroup()
        
        for idx, val in enumerate(arr):
            box = Square(
                side_length=box_size,
                color=BLUE,
                fill_opacity=0.2,
                stroke_width=2
            ).shift(RIGHT * idx * (box_size + 0.1))
            boxes.add(box)
            
            value = Text(str(val), font_size=int(20 * box_size), color=WHITE)
            value.move_to(box.get_center())
            values.add(value)
        
        array_viz = VGroup(boxes, values)
        array_viz.center().next_to(header, DOWN, buff=0.8)
        
        self.play(FadeIn(array_viz), run_time=0.8)
        
        # Animate based on algorithm type
        if algo_type == "two_pointer" and n >= 2:
            left_ptr = Arrow(boxes[0].get_bottom() + DOWN*0.5, boxes[0].get_bottom(), color=BLUE, buff=0.05)
            right_ptr = Arrow(boxes[-1].get_bottom() + DOWN*0.5, boxes[-1].get_bottom(), color=RED, buff=0.05)
            left_label = Text("L", font_size=20, color=BLUE).next_to(left_ptr, DOWN, buff=0.1)
            right_label = Text("R", font_size=20, color=RED).next_to(right_ptr, DOWN, buff=0.1)
            
            self.play(GrowArrow(left_ptr), GrowArrow(right_ptr), Write(left_label), Write(right_label), run_time=0.8)
            
            left_idx, right_idx = 0, n - 1
            for _ in range(min(3, n//2)):
                if left_idx >= right_idx:
                    break
                self.play(
                    boxes[left_idx].animate.set_fill(BLUE, opacity=0.5),
                    boxes[right_idx].animate.set_fill(RED, opacity=0.5),
                    run_time=0.5
                )
                self.wait(0.3)
                left_idx += 1
                right_idx -= 1
            
            check = Text("Two Pointers!", font_size=28, color=GREEN).shift(DOWN*2.5)
            self.play(Write(check), run_time=0.5)
        
        elif algo_type == "sliding_window" and n >= 3:
            k = min(3, n - 1)
            window = SurroundingRectangle(VGroup(*boxes[:k]), color=YELLOW, buff=0.05, stroke_width=3)
            self.play(Create(window), run_time=0.8)
            
            for idx in range(min(n - k, 4)):
                if idx > 0:
                    new_window = SurroundingRectangle(VGroup(*boxes[idx:idx+k]), color=YELLOW, buff=0.05, stroke_width=3)
                    self.play(Transform(window, new_window), run_time=0.5)
                self.wait(0.3)
            
            check = Text("Sliding Window!", font_size=28, color=GREEN).shift(DOWN*2.5)
            self.play(Write(check), run_time=0.5)
        
        else:
            # Generic iteration
            pointer = Arrow(boxes[0].get_top() + UP*0.5, boxes[0].get_top(), color=GREEN, buff=0.05)
            self.play(GrowArrow(pointer), run_time=0.5)
            
            for idx in range(min(n, 5)):
                if idx > 0:
                    self.play(pointer.animate.next_to(boxes[idx], UP, buff=0.05).shift(UP*0.5), run_time=0.3)
                self.play(boxes[idx].animate.set_fill(GREEN, opacity=0.5), run_time=0.3)
                self.wait(0.2)
            
            check = Text("Iteration Complete!", font_size=28, color=GREEN).shift(DOWN*2.5)
            self.play(Write(check), run_time=0.5)
        
        self.wait(1)
        self.clear_all()
    
    def code_scene(self, code_lines):
        header = Text("Solution Code", font_size=32, color=GREEN, weight=BOLD)
        header.to_edge(UP, buff=0.5)
        self.play(Write(header), run_time=0.5)
        
        code_group = VGroup()
        for idx, line in enumerate(code_lines[:12]):
            line_num = Text(f"{idx+1:2d}", font_size=14, color=GRAY)
            line_num.align_to(LEFT*6, LEFT)
            line_num.shift(DOWN * idx * 0.35)
            
            code_text = Text(line[:60] if line else " ", font_size=14, color=WHITE, font="Monospace")
            code_text.next_to(line_num, RIGHT, buff=0.3)
            
            code_group.add(VGroup(line_num, code_text))
        
        code_group.center().shift(DOWN*0.5)
        
        code_bg = RoundedRectangle(
            width=12, height=len(code_lines[:12]) * 0.35 + 0.6,
            corner_radius=0.2,
            fill_color="#1e1e1e",
            fill_opacity=0.95,
            stroke_color=GREEN,
            stroke_width=1
        ).move_to(code_group.get_center())
        
        self.play(FadeIn(code_bg), run_time=0.3)
        
        for line_group in code_group:
            self.play(Write(line_group), run_time=0.15)
        
        self.wait(2)
        self.clear_all()
    
    def complexity_scene(self, time_comp, space_comp):
        header = Text("Complexity Analysis", font_size=32, color=RED, weight=BOLD)
        header.to_edge(UP, buff=0.5)
        self.play(Write(header), run_time=0.5)
        
        # Time complexity box
        time_box = VGroup(
            RoundedRectangle(width=4.5, height=2, corner_radius=0.2, fill_color="#1a1a2e", fill_opacity=0.9, stroke_color=BLUE, stroke_width=2),
            Text("Time", font_size=24, color=BLUE, weight=BOLD),
            Text(time_comp[:30], font_size=18, color=WHITE),
        )
        time_box[1].move_to(time_box[0].get_top() + DOWN*0.4)
        time_box[2].move_to(time_box[0].get_center() + DOWN*0.2)
        time_box.shift(LEFT*3)
        
        # Space complexity box
        space_box = VGroup(
            RoundedRectangle(width=4.5, height=2, corner_radius=0.2, fill_color="#1a1a2e", fill_opacity=0.9, stroke_color=GREEN, stroke_width=2),
            Text("Space", font_size=24, color=GREEN, weight=BOLD),
            Text(space_comp[:30], font_size=18, color=WHITE),
        )
        space_box[1].move_to(space_box[0].get_top() + DOWN*0.4)
        space_box[2].move_to(space_box[0].get_center() + DOWN*0.2)
        space_box.shift(RIGHT*3)
        
        self.play(FadeIn(time_box, shift=RIGHT), FadeIn(space_box, shift=LEFT), run_time=1)
        
        self.wait(2)
        self.clear_all()
    
    def outro_scene(self, title):
        success = Text("Solution Complete!", font_size=42, color=GOLD, weight=BOLD)
        success.shift(UP*0.5)
        self.play(Write(success), run_time=1)
        
        prob_title = Text(title[:40], font_size=24, color=WHITE)
        prob_title.next_to(success, DOWN, buff=0.5)
        self.play(FadeIn(prob_title), run_time=0.5)
        
        branding = Text("Generated by Pragyan", font_size=18, color=GRAY)
        branding.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(branding), run_time=0.3)
        
        self.wait(2)
        self.clear_all()
'''
        
        return scene_header + scene_body
    
    def _render_video(self, scene_file: Path, output_filename: Optional[str] = None, scene_class_name: str = "DSAExplanation") -> Path:
        """Render the Manim scene to video
        
        Args:
            scene_file: Path to the Python file containing the Manim scene
            output_filename: Optional custom output filename
            scene_class_name: Name of the Scene class to render (e.g., 'NQueensScene', 'BubbleSortScene')
        """
        quality_map = {
            "low_quality": "-ql",
            "medium_quality": "-qm",
            "high_quality": "-qh",
            "production_quality": "-qp",
        }
        quality_flag = quality_map.get(self.config.video_quality, "-qm")
        
        cmd = [
            "manim",
            quality_flag,
            str(scene_file),
            scene_class_name,  # Use the actual algorithm scene class name
            "--media_dir", str(self._get_temp_dir() / "media"),
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(scene_file.parent),
                timeout=300
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Manim rendering failed: {result.stderr}")
            
            # Find the output video
            media_dir = self._get_temp_dir() / "media" / "videos" / "dsa_explanation"
            
            for quality_dir in media_dir.iterdir() if media_dir.exists() else []:
                for video_file in quality_dir.glob("*.mp4"):
                    if output_filename:
                        output_path = Path.cwd() / output_filename
                    else:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_path = Path.cwd() / f"dsa_explanation_{timestamp}.mp4"
                    
                    shutil.copy(video_file, output_path)
                    return output_path
            
            raise FileNotFoundError("No video file was generated")
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Video rendering timed out after 5 minutes")
        except Exception as e:
            raise RuntimeError(f"Video generation failed: {str(e)}")


class SimpleVideoGenerator:
    """Fallback video generator using MoviePy"""
    
    def __init__(self, config: Optional[VideoConfig] = None):
        self.config = config or VideoConfig()
    
    def generate_slideshow(
        self,
        question: Question,
        solution: Solution,
        analysis: Dict[str, Any]
    ) -> Path:
        try:
            from moviepy.editor import TextClip, CompositeVideoClip, concatenate_videoclips, ColorClip
        except ImportError:
            raise ImportError("MoviePy not installed. Install with: pip install moviepy")
        
        clips = []
        duration = 5
        bg_color = tuple(int(self.config.background_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        
        for title, content in [
            (question.title, "DSA Problem Solution"),
            ("Concept", solution.concept),
            ("Approach", solution.approach[:300]),
            ("Complexity", f"Time: {solution.time_complexity}\nSpace: {solution.space_complexity}"),
        ]:
            bg = ColorClip(
                size=(self.config.pixel_width, self.config.pixel_height),
                color=bg_color, duration=duration
            )
            title_clip = TextClip(
                title, fontsize=60, color='white', font='Arial-Bold',
                method='caption', size=(self.config.pixel_width - 100, None)
            ).set_position(('center', 100)).set_duration(duration)
            content_clip = TextClip(
                content, fontsize=36, color='lightgray', font='Arial',
                method='caption', size=(self.config.pixel_width - 150, None)
            ).set_position(('center', 'center')).set_duration(duration)
            clips.append(CompositeVideoClip([bg, title_clip, content_clip]))
        
        final_video = concatenate_videoclips(clips, method="compose")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.config.output_dir / f"pragyan_solution_{timestamp}.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_video.write_videofile(str(output_path), fps=self.config.fps, codec="libx264", audio=False, verbose=False, logger=None)
        
        return output_path
