def create_seaborn_capture_function():
    return """
    def capture_seaborn_plots():
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            import io
            import base64
            import inspect
            
            # Since seaborn works on top of matplotlib,
            # we need to check if there are active plots first
            figures = {}
            figure_ids = set()
            
            # Get the current axis if it exists
            if plt.get_fignums():
                # Seaborn typically returns the matplotlib Axes object
                # Let's check for any variables in caller's frame that might be seaborn plots
                caller_frame = inspect.currentframe().f_back
                if caller_frame:
                    for var_name, var_val in caller_frame.f_locals.items():
                        # Check if this is a seaborn plot object
                        # This is a bit of a heuristic, as seaborn doesn't have a specific plot class
                        if str(type(var_val)).startswith("<class 'seaborn."):
                            # Handle seaborn plot - convert to figure
                            # Try to get the figure from the plot
                            if hasattr(var_val, 'figure'):
                                fig = var_val.figure
                            elif hasattr(var_val, 'fig'):
                                fig = var_val.fig
                            else:
                                # Skip if we can't get the figure
                                continue
                                
                            # Convert figure to PNG data
                            buf = io.BytesIO()
                            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                            buf.seek(0)
                            
                            # Encode to base64 for transmission
                            img_data = base64.b64encode(buf.read()).decode('utf-8')
                            figures[f"seaborn_plot_{var_name}"] = {
                                "mimetype": "image/png",
                                "data": img_data
                            }
                            if hasattr(fig, 'number'):
                                figure_ids.add(fig.number)
                
                # Also capture any current figures that might be seaborn plots
                # This is a fallback for when we can't identify specific seaborn objects
                for fig_num in plt.get_fignums():
                    fig = plt.figure(fig_num)
                    
                    # Skip if we already captured this figure
                    if any(f"figure_{fig_num}" in key for key in figures.keys()):
                        continue
                    
                    # Convert figure to PNG data
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                    buf.seek(0)
                    
                    # Encode to base64 for transmission
                    img_data = base64.b64encode(buf.read()).decode('utf-8')
                    figures[f"seaborn_figure_{fig_num}"] = {
                        "mimetype": "image/png",
                        "data": img_data
                    }
                    figure_ids.add(fig_num)
                
                # Don't close the figures here, as they might still be needed
                # Let the matplotlib capture function handle the closing
            
            return figures, figure_ids
        except ImportError:
            # Seaborn not available
            print("Seaborn not available for plot capture")
            return {}, set()
        except Exception as e:
            print(f"Error capturing seaborn plots: {e}")
            import traceback
            traceback.print_exc()
            return {}, set()
    """

