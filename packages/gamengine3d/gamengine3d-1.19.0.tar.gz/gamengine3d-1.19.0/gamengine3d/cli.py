import re
import argparse
import runpy
from pathlib import Path
from .engine import Engine

def get_size(s: str):
    pattern = re.compile(r'^\s*(\d+)\s*[xX]\s*(\d+)\s*$')
    m = pattern.fullmatch(s)
    if not m:
        raise RuntimeError(f"Invalid size format: '{s}'. Expected '<number>x<number>'")
    return int(m.group(1)), int(m.group(2))

def main():
    parser = argparse.ArgumentParser(prog="gamengine3d")
    sub = parser.add_subparsers(dest="command", required=True)

    # Get the list of available demos from the examples folder
    examples_dir = Path(__file__).parent / "examples"
    available_demos = [
        f.stem for f in examples_dir.glob("*.py") if f.is_file() and f.name != "__init__.py"
    ]

    demo_cmd = sub.add_parser("demo", help="Run a built-in example")
    demo_cmd.add_argument(
        "demo_name",
        nargs="?",
        default="basics",
        choices=available_demos,  # restrict to available demos
        help=f"The name of the example to run. Available: {', '.join(available_demos)}"
    )

    load_scene_cmd = sub.add_parser("load", help="Load a scene from a JSON file")
    load_scene_cmd.add_argument(
        "filename",
        nargs="?",
        help=f"The file path to load the scene from"
    )
    load_scene_cmd.add_argument(
        "window_size",
        nargs="?",
        default="500x500",
        help=f"The size of the window to create in WIDTHxHEIGHT format (default: 500x500)"
    )
    load_scene_cmd.add_argument(
        "fps",
        nargs="?",
        default=60,
        help=f"FPS to run the engine at (default: 60)",
        type=int
    )
    load_scene_cmd.add_argument(
        "--dynamic-view",
        action="store_true",
        help="Enable dynamic view"
    )

    args = parser.parse_args()

    if args.command == "demo":
        module = f"gamengine3d.examples.{args.demo_name}"
        print(f"Running example: {args.demo_name}")
        print(f"Path: {module}")
        runpy.run_module(module, run_name="__main__")

    elif args.command == "load":
        if not args.filename:
            print("Error: Please provide a filename to load the scene from.")
            return

        if not args.filename.endswith(".json"):
            print("The filename must be a JSON file.")
            return

        size = get_size(args.window_size)
        print(f"Running scene loader for file: {args.filename}")

        engine = Engine(width=size[0], height=size[1])
        engine.load_scene(args.filename)
        engine.run(fps=args.fps, dynamic_view=args.dynamic_view)

if __name__ == "__main__":
    main()
