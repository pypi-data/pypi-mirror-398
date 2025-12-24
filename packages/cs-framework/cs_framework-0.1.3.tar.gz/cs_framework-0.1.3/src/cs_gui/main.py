import argparse
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from nicegui import ui, app
try:
    from .graph_loader import load_graph_data
except ImportError:
    from graph_loader import load_graph_data

def run_gui(log_file="execution.ttl"):
    @ui.page('/')
    def index():
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('C-S Framework Execution Graph').classes('text-2xl font-bold')
            with ui.dialog() as help_dialog, ui.card().classes('w-2/3'):
                ui.label('About C-S Architecture').classes('text-xl font-bold mb-2')
                ui.markdown('''
                **C-S (Concept-Synchronization)** is an architecture that decouples systems into:
                
                *   **Concepts (Blue)**
                    <br>Independent units of state and logic (e.g., *TetrisEngine*). They do not know about each other.
                *   **Actions (Green)**
                    <br>Commands sent TO a Concept (e.g., *move_left*).
                *   **Events (Yellow/Red)**
                    <br>Signals emitted BY a Concept when something happens (e.g., *PieceMoved*).
                *   **Synchronizations**
                    <br>The invisible glue that listens to Events and triggers Actions.
                
                ---
                
                **How to read the graph:**
                
                1.  An **Action** (Green) is triggered on a Concept.
                2.  The Concept processes it and emits an **Event** (Yellow).
                3.  A Synchronization catches that Event and triggers a new **Action** (Green) on another Concept.
                ''')
                ui.button('Close', on_click=help_dialog.close)
            
            ui.button('What is C-S?', on_click=help_dialog.open).classes('bg-blue-500 text-white')

        # Legend
        with ui.row().classes('gap-4 mb-2'):
            ui.html('<span title="Concept: A self-contained module" style="cursor: help; display: inline-block; width: 12px; height: 12px; background-color: #5470c6; border-radius: 50%; margin-right: 5px;"></span> Concept', sanitize=False)
            ui.html('<span title="Action: A command executed by a Concept" style="cursor: help; display: inline-block; width: 12px; height: 12px; background-color: #91cc75; border-radius: 50%; margin-right: 5px;"></span> Action', sanitize=False)
            ui.html('<span title="Event: A signal emitted by a Concept" style="cursor: help; display: inline-block; width: 12px; height: 12px; background-color: #fac858; border-radius: 50%; margin-right: 5px;"></span> Event (Success)', sanitize=False)
            ui.html('<span title="Failure: An error occurred during processing" style="cursor: help; display: inline-block; width: 12px; height: 12px; background-color: #ee6666; border-radius: 50%; margin-right: 5px;"></span> Event (Failure)', sanitize=False)

        # ECharts container
        chart = ui.echart({
            'title': {'text': 'Execution Trace'},
            'tooltip': {},
            'legend': [{'data': ['Concept', 'Action', 'Event']}],
            'series': [
                {
                    'type': 'graph',
                    'layout': 'force',
                    'animation': False,
                    'label': {'show': True, 'position': 'right', 'formatter': '{b}'},
                    'draggable': True,
                    'data': [],
                    'links': [],
                    'categories': [{'name': 'Concept'}, {'name': 'Action'}, {'name': 'Event'}],
                    'roam': True,
                    'force': {
                        'repulsion': 100,
                        'edgeLength': 50
                    }
                }
            ]
        }).classes('w-full h-screen')

        last_mtime = 0

        def update_graph():
            nonlocal last_mtime
            try:
                mtime = os.path.getmtime(log_file)
            except FileNotFoundError:
                return

            if mtime > last_mtime:
                data = load_graph_data(log_file)
                if data["nodes"]:
                    chart.options['series'][0]['data'] = data["nodes"]
                    chart.options['series'][0]['links'] = data["links"]
                    chart.update()
                last_mtime = mtime

        ui.timer(0.5, update_graph)

    ui.run(title='C-S Framework GUI', port=8080, reload=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="execution.ttl", help="Path to the RDF log file")
    args = parser.parse_args()

    run_gui(args.log)

if __name__ in {"__main__", "__mp_main__"}:
    main()
