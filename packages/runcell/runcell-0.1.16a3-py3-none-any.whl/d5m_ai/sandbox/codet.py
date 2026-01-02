def create_custom_json_serializer():
    return """
    # Enhanced function to handle custom JSON serialization with rich formats
    def custom_json_serializer(obj):
        import numpy as np
        import pandas as pd
        import io
        import base64
        from IPython.display import display, HTML
        
        # Handle pandas DataFrame
        if isinstance(obj, pd.DataFrame):
            # Convert DataFrame to both data and HTML representation
            html_repr = obj.to_html(max_rows=20, index=True, notebook=True)
            # Handle various special values that can break JSON
            df_clean = obj.replace({
                np.nan: None,
                np.inf: None,
                -np.inf: None,
                pd.NaT: None,  # Not a Time
                pd.NA: None,   # Pandas NA
                pd.NaT: None,  # Not a Time
                'nan': None,
                'NaN': None,
                'None': None,
                'none': None,
                'NULL': None,
                'null': None
            })
            return {
                "__dataframe__": True,
                "data": df_clean.to_dict(orient='records'),
                "columns": obj.columns.tolist(),
                "index": obj.index.tolist(),
                "html": html_repr,
                "mimetype": "text/html"
            }
        
        # Handle numpy arrays
        elif isinstance(obj, np.ndarray):
            return {"__ndarray__": True, "data": obj.tolist()}
        
        # Handle numpy data types - Updated for NumPy 2.0 compatibility
        elif isinstance(obj, (np.integer, np.int8, np.int16, np.int32, np.int64, 
                            np.uint8, np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        
        # Handle objects with _repr_html_ method (like many Jupyter-compatible objects)
        elif hasattr(obj, '_repr_html_') and callable(obj._repr_html_):
            html_repr = obj._repr_html_()
            if html_repr is not None:
                return {
                    "__html_repr__": True,
                    "html": html_repr,
                    "mimetype": "text/html",
                }
        
        # Handle objects with _repr_markdown_ method
        elif hasattr(obj, '_repr_markdown_') and callable(obj._repr_markdown_):
            md_repr = obj._repr_markdown_()
            if md_repr is not None:
                return {
                    "__markdown_repr__": True,
                    "markdown": md_repr,
                    "mimetype": "text/markdown",
                }
        
        # Handle objects with _repr_latex_ method
        elif hasattr(obj, '_repr_latex_') and callable(obj._repr_latex_):
            latex_repr = obj._repr_latex_()
            if latex_repr is not None:
                return {
                    "__latex_repr__": True,
                    "latex": latex_repr,
                    "mimetype": "text/latex",
                }
        
        # Try to handle other special objects with string representation
        try:
            return str(obj)
        except:
            return "Unserializable object"
"""