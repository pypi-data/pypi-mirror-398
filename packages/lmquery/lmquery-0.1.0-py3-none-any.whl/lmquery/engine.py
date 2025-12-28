import pandas as pd
import plotly.express as px
import re

def plot(df, query_str):
    """
    Executes a SQL-like visualization query on a pandas DataFrame.
    
    Syntax: SELECT [x_col], [y_col], [color_col], [size_col] FROM df WHERE [condition] PLOT [chart_type]
    
    Supported Chart Types: 'scatter', 'bar', 'line', 'histogram', 'box', 'pie'
    """
    
    # Input validation
    if not query_str or not isinstance(query_str, str):
        raise ValueError("Query string must be a non-empty string")
    
    if df is None or df.empty:
        raise ValueError("DataFrame must not be None or empty")
    
    # Normalize string
    q = query_str.strip().upper()
    
    # 1. Extract Chart Type
    plot_match = re.search(r"PLOT (\w+)", q)
    if not plot_match:
        raise ValueError("Query must end with 'PLOT [chart_type]' (e.g., PLOT SCATTER)")
    
    chart_type = plot_match.group(1).lower()
    
    # 2. Extract Columns (SELECT ...)
    select_match = re.search(r"SELECT (.*?) FROM", q)
    if not select_match:
        raise ValueError("Query must specify columns to SELECT")
    
    columns_str = select_match.group(1)
    # Split by comma, strip whitespace, filter empty strings, and lowercase to match dataframe
    cols = [c.strip().lower() for c in columns_str.split(',') if c.strip()]
    
    if not cols:
        raise ValueError("At least one column must be specified in SELECT clause")
    
    # 4. Validate columns exist in dataframe (moved before WHERE filtering)
    # Create case-insensitive column mapping
    df_cols_lower = {col.lower(): col for col in df.columns}
    valid_cols = list(df_cols_lower.keys())
    
    for c in cols:
        if c not in valid_cols:
            # Try to suggest similar column names
            suggestions = [col for col in valid_cols if c in col or col in c]
            suggestion_text = f" Did you mean one of these? {suggestions}" if suggestions else ""
            raise ValueError(f"Column '{c}' not found in data.{suggestion_text}")
    
    # Map SQL columns to actual DataFrame column names (preserving original case)
    actual_cols = []
    for c in cols:
        actual_cols.append(df_cols_lower[c])
    
    # 3. Filter Data (WHERE ...)
    # Use more robust WHERE clause parsing
    filtered_df = df.copy()
    where_match = re.search(r"WHERE (.+?)(?: PLOT|$)", q)  # More robust: capture until PLOT or end
    if where_match:
        where_clause = where_match.group(1)
        try:
            # Use the actual column names (preserving case) for the query
            # Create a mapping for case-insensitive WHERE clause evaluation
            where_clause_mapped = where_clause
            for orig_col, actual_col in zip(cols, actual_cols):
                where_clause_mapped = re.sub(r'\b' + re.escape(orig_col) + r'\b', actual_col, where_clause_mapped, flags=re.IGNORECASE)
            
            filtered_df = filtered_df.query(where_clause_mapped)
        except Exception as e:
            raise ValueError(f"Error in WHERE clause '{where_clause}': {str(e)}")

    # Update column references for plotting (use actual column names)
    # Map SQL columns to Plotly arguments
    # Logic: 1st col = x, 2nd col = y, 3rd col = color, 4th col = size
    kwargs = {}
    if len(actual_cols) > 0: kwargs['x'] = actual_cols[0]
    if len(actual_cols) > 1: kwargs['y'] = actual_cols[1]
    if len(actual_cols) > 2: kwargs['color'] = actual_cols[2]
    if len(actual_cols) > 3: kwargs['size'] = actual_cols[3]
    
    # Special handling for Pie charts (Pie needs names and values, not x/y)
    if chart_type == 'pie':
        if len(actual_cols) < 2:
            raise ValueError("Pie chart requires 2 columns: Names and Values")
        kwargs['names'] = actual_cols[0]
        kwargs['values'] = actual_cols[1]
        # Remove x/y as plotly express pie doesn't use them the same way
        kwargs.pop('x', None)
        kwargs.pop('y', None)

    # 5. Generate Plot
    if chart_type == 'scatter':
        fig = px.scatter(filtered_df, **kwargs, title="Interactive Scatter Plot")
    elif chart_type == 'line':
        fig = px.line(filtered_df, **kwargs, title="Interactive Line Plot")
    elif chart_type == 'bar':
        fig = px.bar(filtered_df, **kwargs, title="Interactive Bar Plot")
    elif chart_type == 'histogram':
        # Histogram usually only takes x
        fig = px.histogram(filtered_df, x=kwargs.get('x'), color=kwargs.get('color'), title="Histogram")
    elif chart_type == 'box':
        fig = px.box(filtered_df, **kwargs, title="Box Plot")
    elif chart_type == 'pie':
        fig = px.pie(filtered_df, **kwargs, title="Pie Chart")
    else:
        raise ValueError(f"Unsupported plot type: '{chart_type}'. Supported types: scatter, bar, line, histogram, box, pie")

    # Apply a beautiful default template
    fig.update_layout(template="plotly_dark")
    
    return fig
