"""
Example demonstrating the new dynamic, algorithm-specific animations
Shows how Pragyan now generates custom visualizations for different algorithms
"""

import os
import sys
from pathlib import Path

# Use local source code instead of installed package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pragyan import Pragyan
from pragyan.models import Question, ProgrammingLanguage

def example_nqueens():
    """
    Example: N-Queens problem with dynamic chess board and backtracking visualization
    """
    print("=" * 60)
    print("N-QUEENS ALGORITHM - Dynamic Chess Board Animation")
    print("=" * 60)
    
    # Initialize Pragyan
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Please set GEMINI_API_KEY or GROQ_API_KEY environment variable")
    provider = "gemini" if os.getenv("GEMINI_API_KEY") else "groq"
    
    pragyan = Pragyan(provider=provider, api_key=api_key)
    
    # Create N-Queens question
    question = Question(
        title="N-Queens Problem",
        description="""
        The n-queens puzzle is the problem of placing n queens on an n×n chessboard 
        such that no two queens attack each other.
        
        Given an integer n, return all distinct solutions to the n-queens puzzle. 
        You may return the answer in any order.
        
        Each solution contains a distinct board configuration of the n-queens' placement, 
        where 'Q' and '.' both indicate a queen and an empty space, respectively.
        """,
        examples=[
            {
                "input": "n = 4",
                "output": [[".Q..","...Q","Q...","..Q."],["..Q.","Q...","...Q",".Q.."]],
                "explanation": "There exist two distinct solutions to the 4-queens puzzle"
            }
        ],
        constraints=["1 <= n <= 9"],
        difficulty="Hard"
    )
    
    # Solve the problem
    print("\n📊 Analyzing N-Queens problem...")
    solution = pragyan.solve(question, ProgrammingLanguage.PYTHON)
    
    print(f"✓ Solution generated using: {solution.concept}")
    print(f"✓ Time Complexity: {solution.time_complexity}")
    print(f"✓ Space Complexity: {solution.space_complexity}")
    
    # Generate video with dynamic chess board animation
    print("\n🎬 Generating video with dynamic chess board animation...")
    print("   - Showing queen placements step-by-step")
    print("   - Visualizing backtracking when conflicts occur")
    print("   - Highlighting safe vs unsafe positions")
    
    video_path = pragyan.generate_video(question, solution)
    
    print(f"\n✅ Video generated: {video_path}")
    print("   The video will show:")
    print("   • Animated chess board")
    print("   • Queens being placed one by one")
    print("   • Backtracking visualization when placement fails")
    print("   • Step-by-step arrival at the solution")
    

def example_sorting():
    """
    Example: Sorting algorithm with dynamic bar chart visualization
    """
    print("\n" + "=" * 60)
    print("SORTING ALGORITHM - Dynamic Bar Chart Animation")
    print("=" * 60)
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Please set GEMINI_API_KEY or GROQ_API_KEY environment variable")
    provider = "gemini" if os.getenv("GEMINI_API_KEY") else "groq"
    
    pragyan = Pragyan(provider=provider, api_key=api_key)
    
    # Create sorting question
    question = Question(
        title="Quick Sort Implementation",
        description="""
        Implement the Quick Sort algorithm to sort an array of integers in ascending order.
        
        Quick Sort is a divide-and-conquer algorithm that works by selecting a 'pivot' element
        and partitioning the array around the pivot.
        
        Input: nums = [64, 34, 25, 12, 22, 11, 90, 88]
        Output: [11, 12, 22, 25, 34, 64, 88, 90]
        """,
        examples=[
            {
                "input": "[64, 34, 25, 12, 22, 11, 90, 88]",
                "output": "[11, 12, 22, 25, 34, 64, 88, 90]"
            }
        ],
        constraints=["1 <= nums.length <= 1000"],
        difficulty="Medium"
    )
    
    print("\n📊 Analyzing Quick Sort algorithm...")
    solution = pragyan.solve(question, ProgrammingLanguage.PYTHON)
    
    print(f"✓ Solution generated using: {solution.concept}")
    print(f"✓ Time Complexity: {solution.time_complexity}")
    
    print("\n🎬 Generating video with dynamic sorting animation...")
    print("   - Showing bars representing array elements")
    print("   - Highlighting pivot selection")
    print("   - Animating partition process")
    print("   - Showing every comparison and swap")
    
    video_path = pragyan.generate_video(question, solution)
    
    print(f"\n✅ Video generated: {video_path}")
    print("   The video will show:")
    print("   • Animated bar chart of array values")
    print("   • Pivot selection highlighted in gold")
    print("   • Elements being compared (yellow)")
    print("   • Swaps happening in real-time")
    print("   • Recursive partitioning visualization")


def example_graph_bfs():
    """
    Example: BFS algorithm with dynamic graph traversal
    """
    print("\n" + "=" * 60)
    print("BFS ALGORITHM - Dynamic Graph Traversal Animation")
    print("=" * 60)
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Please set GEMINI_API_KEY or GROQ_API_KEY environment variable")
    provider = "gemini" if os.getenv("GEMINI_API_KEY") else "groq"
    
    pragyan = Pragyan(provider=provider, api_key=api_key)
    
    question = Question(
        title="Breadth-First Search in Graph",
        description="""
        Implement Breadth-First Search (BFS) to traverse a graph starting from a given node.
        
        BFS explores all vertices at the current depth before moving to vertices at the next depth.
        It uses a queue to keep track of vertices to visit.
        
        Given a graph and a starting vertex, return the order of vertices visited using BFS.
        """,
        examples=[
            {
                "input": "graph = {A: [B,C], B: [A,D], C: [A,E], D: [B,F], E: [C,F], F: [D,E]}, start = A",
                "output": "[A, B, C, D, E, F]"
            }
        ],
        constraints=["Graph may have cycles"],
        difficulty="Medium"
    )
    
    print("\n📊 Analyzing BFS algorithm...")
    solution = pragyan.solve(question, ProgrammingLanguage.PYTHON)
    
    print(f"✓ Solution generated using: {solution.concept}")
    
    print("\n🎬 Generating video with dynamic graph traversal...")
    print("   - Showing graph nodes and edges")
    print("   - Visualizing queue state at each step")
    print("   - Highlighting current node being visited")
    print("   - Showing BFS level-by-level exploration")
    
    video_path = pragyan.generate_video(question, solution)
    
    print(f"\n✅ Video generated: {video_path}")
    print("   The video will show:")
    print("   • Animated graph structure")
    print("   • Queue contents updating in real-time")
    print("   • Nodes changing color as they're visited")
    print("   • Complete traversal order")


def compare_old_vs_new():
    """
    Show the difference between old static animations and new dynamic ones
    """
    print("\n" + "=" * 60)
    print("COMPARISON: OLD vs NEW ANIMATION SYSTEM")
    print("=" * 60)
    
    print("\n❌ OLD SYSTEM (Static & Boring):")
    print("   • Same generic array visualization for all problems")
    print("   • Static text slides with code")
    print("   • No algorithm execution visualization")
    print("   • No step-by-step walkthrough")
    print("   • Just shows final result")
    
    print("\n✅ NEW SYSTEM (Dynamic & Engaging):")
    print("   • Algorithm-specific visualizations:")
    print("     - N-Queens: Animated chess board with backtracking")
    print("     - Sorting: Dynamic bar charts with swaps")
    print("     - Graph: Animated traversal with queue/stack states")
    print("     - DP: Table filling animation")
    print("   • Step-by-step execution showing how algorithm works")
    print("   • Visual cues for comparisons, swaps, backtracks")
    print("   • Arrival at solution through animation")
    print("   • Engaging and educational")
    
    print("\n📈 BENEFITS:")
    print("   • Actually see the algorithm run")
    print("   • Understand the logic through visualization")
    print("   • Remember concepts better")
    print("   • Videos are interesting to watch")
    print("   • Great for learning and teaching")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║                  PRAGYAN - DYNAMIC ANIMATIONS                ║
║          Transform your DSA learning with visualization      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Show comparison first
    compare_old_vs_new()
    
    print("\n" + "=" * 60)
    print("Choose an example to run:")
    print("=" * 60)
    print("1. N-Queens with chess board animation")
    print("2. Quick Sort with bar chart animation")
    print("3. BFS with graph traversal animation")
    print("4. Run all examples")
    print("=" * 60)
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        example_nqueens()
    elif choice == "2":
        example_sorting()
    elif choice == "3":
        example_graph_bfs()
    elif choice == "4":
        example_nqueens()
        example_sorting()
        example_graph_bfs()
    else:
        print("Invalid choice")
    
    print("\n" + "=" * 60)
    print("✨ The new dynamic animation system makes learning fun!")
    print("   No more boring static slides - see algorithms in action!")
    print("=" * 60)
