def create_matplotlib_capture_function():
    return """
    # Capture matplotlib figures if they're created
    def capture_matplotlib_figures(*, exclude_ids=None):
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            import io
            import base64
            import traceback

            # Force matplotlib to use the Agg backend to ensure figure capture works
            matplotlib.use('Agg', force=True)

            figures = {}
            figure_ids = set()

            # Ensure exclude_ids is a set for quick lookups
            exclude_ids = set(exclude_ids or [])

            # Check if any figures exist
            if plt.get_fignums():
                for fig_num in plt.get_fignums():
                    if fig_num in exclude_ids:
                        continue
                    fig = plt.figure(fig_num)

                    # Convert figure to PNG data
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                    buf.seek(0)

                    # Encode to base64 for transmission
                    img_data = base64.b64encode(buf.read()).decode('utf-8')
                    figures[f"figure_{fig_num}"] = {
                        "mimetype": "image/png",
                        "data": img_data
                    }
                    figure_ids.add(fig_num)

                # Important: Need to close all figures to prevent memory leaks
                plt.close('all')

            return figures, figure_ids
        except ImportError:
            # Matplotlib not available
            print("Matplotlib not available for figure capture")
            return {}, set()
        except Exception as e:
            print(f"Error capturing matplotlib figures: {e}")
            traceback.print_exc()
            return {}, set()
    """
