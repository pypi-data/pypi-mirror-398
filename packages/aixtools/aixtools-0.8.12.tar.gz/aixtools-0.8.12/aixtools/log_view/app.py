"""
Main application module for the Agent Log Viewer.
"""

import argparse
import os
import subprocess
from pathlib import Path

import streamlit as st

from aixtools.log_view.display import display_node
from aixtools.log_view.export import export_nodes_to_json
from aixtools.log_view.filters import filter_nodes
from aixtools.log_view.log_utils import format_timestamp_from_filename, get_log_files
from aixtools.log_view.node_summary import NodeTitle, extract_node_types

# Now we can import our modules
from aixtools.logging.log_objects import load_from_log
from aixtools.utils.config import LOGS_DIR


def main(log_dir: Path | None = None):  # noqa: PLR0915, pylint: disable=too-many-locals,too-many-statements
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="Agent Log Viewer",
        layout="wide",
    )

    st.title("Agent Log Viewer")

    # Use provided log directory or default
    if log_dir is None:
        log_dir = LOGS_DIR

    # Create the logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    st.sidebar.header("Settings")

    # Allow user to select a different log directory
    custom_log_dir = st.sidebar.text_input("Log Directory", value=str(log_dir))
    if custom_log_dir and custom_log_dir != str(log_dir):
        log_dir = Path(custom_log_dir)
        # Create the custom directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

    # Get log files
    log_files = get_log_files(log_dir)

    if not log_files:
        st.warning(f"No log files found in {log_dir}")
        st.info("Run an agent with logging enabled to create log files.")
        return

    # Create a dictionary of log files with formatted timestamps as display names
    log_file_options = {f"{format_timestamp_from_filename(f.name)} - {f.name}": f for f in log_files}

    # Select log file (default to most recent)
    selected_log_file_name = st.sidebar.selectbox(
        "Select Log File",
        options=list(log_file_options.keys()),
        index=0,
    )

    selected_log_file = log_file_options[selected_log_file_name]

    st.sidebar.info(f"Selected: {selected_log_file.name}")

    # Load nodes
    try:
        with st.spinner("Loading log file..."):
            nodes = load_from_log(selected_log_file)

        st.success(f"Loaded {len(nodes)} nodes from {selected_log_file.name}")

        # Create filter section in sidebar
        st.sidebar.header("Filters")

        # Text filter
        filter_text = st.sidebar.text_input("Text Search", help="Filter nodes containing this text")

        # Extract node types for filtering
        node_types = extract_node_types(nodes)

        # Type filter
        selected_types = st.sidebar.multiselect(
            "Node Types", options=sorted(node_types), default=[], help="Select node types to display"
        )

        # Attribute filter
        filter_attribute = st.sidebar.text_input("Has Attribute", help="Filter nodes that have this attribute")

        # Regex filter
        filter_regex = st.sidebar.text_input("Regex Pattern", help="Filter nodes matching this regex pattern")

        # Combine all filters
        filters = {"text": filter_text, "types": selected_types, "attribute": filter_attribute, "regex": filter_regex}

        # Apply filters
        filtered_nodes = filter_nodes(nodes, filters)

        # Show filter results
        if len(filtered_nodes) != len(nodes):
            st.info(f"Filtered to {len(filtered_nodes)} of {len(nodes)} nodes")

        # Display options
        st.sidebar.header("Display Options")

        # Option to expand all nodes by default
        expand_all = st.sidebar.checkbox("Expand All Nodes", value=False)

        # Option to select output format
        display_format = st.sidebar.radio(
            "Display Format",
            options=["Markdown", "Rich", "JSON"],
            index=0,
            help="Select the format for displaying node content",
        )

        # Export options
        st.sidebar.header("Export")

        # Export to JSON
        if st.sidebar.button("Export to JSON"):
            json_str = export_nodes_to_json(filtered_nodes)
            st.sidebar.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"agent_nodes_{selected_log_file.stem}.json",
                mime="application/json",
            )

        # Main content area - display nodes
        if filtered_nodes:
            node_title = NodeTitle()
            # Display nodes with proper formatting
            for i, node in enumerate(filtered_nodes):
                # Create a header for each node
                node_header = f"{i}: {node_title.summary(node)}"

                # Display the node with proper formatting
                with st.expander(node_header, expanded=expand_all):
                    try:
                        display_node(node, display_format=display_format)
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        st.error(f"Error displaying node: {e}")
                        st.exception(e)
        else:
            st.warning("No nodes match the current filters")

    except Exception as e:  # pylint: disable=broad-exception-caught
        st.error(f"Error loading or processing log file: {e}")
        st.exception(e)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Agent Log Viewer")
    parser.add_argument("log_dir", nargs="?", type=Path, help="Directory containing log files (default: DATA_DIR/logs)")
    return parser.parse_args()


def main_cli():
    """Entry point for the command-line tool."""
    cmd_args = parse_args()

    # Print a message to indicate the app is starting
    print("Starting Agent Log Viewer...")
    print(f"Log directory: {cmd_args.log_dir or LOGS_DIR}")

    # Launch the Streamlit app

    # Get the path to this script
    script_path = Path(__file__).resolve()

    # Use streamlit run to start the app
    cmd = ["streamlit", "run", str(script_path)]

    # Add log_dir argument if provided
    if cmd_args.log_dir:
        cmd.extend(["--", str(cmd_args.log_dir)])

    # Run the command
    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\nShutting down Agent Log Viewer...")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error running Streamlit app: {e}")


if __name__ == "__main__":
    args = parse_args()
    main(args.log_dir)
