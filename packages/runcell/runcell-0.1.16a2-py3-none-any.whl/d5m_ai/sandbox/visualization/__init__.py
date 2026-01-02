from .matplotlib import create_matplotlib_capture_function
from .seaborn import create_seaborn_capture_function

def create_visualization_capture_functions():
    return f"""
    {create_seaborn_capture_function()}
    {create_matplotlib_capture_function()}

    def capture_all_visualizations():
        visualizations = {{}}
        captured_figure_ids = set()  # Track which figures have been captured
        
        # Check if seaborn is already imported
        seaborn_imported = 'seaborn' in sys.modules or 'sns' in sys.modules
        
        # Check if matplotlib is already imported
        matplotlib_imported = 'matplotlib' in sys.modules or 'matplotlib.pyplot' in sys.modules or 'plt' in sys.modules
        
        # First capture seaborn plots if it's imported
        # We do this first because seaborn uses matplotlib under the hood
        if seaborn_imported:
            seaborn_plots, seaborn_figure_ids = capture_seaborn_plots()
            visualizations.update(seaborn_plots)
            captured_figure_ids.update(seaborn_figure_ids)
        
        # Then capture any remaining matplotlib figures if it's imported
        if matplotlib_imported:
            matplotlib_figures, matplotlib_figure_ids = capture_matplotlib_figures(exclude_ids=captured_figure_ids)
            visualizations.update(matplotlib_figures)
            captured_figure_ids.update(matplotlib_figure_ids)
        
        return visualizations
"""