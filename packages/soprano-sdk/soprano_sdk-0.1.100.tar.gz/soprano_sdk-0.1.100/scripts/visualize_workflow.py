"""
Visualize workflow graph as an image
"""

from soprano_sdk import load_workflow
import sys


def visualize_workflow(yaml_path: str, output_path: str = None):
    """Generate a visual representation of the workflow graph"""
    print(f"Loading workflow from: {yaml_path}")
    graph, engine = load_workflow(yaml_path)

    # Get the graph drawable representation
    try:
        # Try PNG format first (requires graphviz)
        if output_path is None:
            output_path = yaml_path.replace('.yaml', '_graph.png')

        print("Generating graph visualization...")
        graph_image = graph.get_graph().draw_mermaid_png()

        with open(output_path, 'wb') as f:
            f.write(graph_image)

        print(f"✓ Graph saved to: {output_path}")

    except Exception as e:
        print(f"PNG generation failed: {e}")
        print("\nTrying Mermaid format instead...")

        # Fallback to mermaid text format
        output_path = yaml_path.replace('.yaml', '_graph.mmd')
        mermaid = graph.get_graph().draw_mermaid()

        with open(output_path, 'w') as f:
            f.write(mermaid)

        print(f"✓ Mermaid graph saved to: {output_path}")
        print("You can visualize this at: https://mermaid.live/")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python visualize_workflow.py <workflow.yaml> [output.png]")
        sys.exit(1)

    yaml_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        visualize_workflow(yaml_file, output_file)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
