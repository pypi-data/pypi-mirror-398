import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.text import Text
from matplotlib.lines import Line2D
from typing import List, Optional, Tuple, Union, Dict, Any

def richtext(
    x: float,
    y: float,
    strings: List[str],
    colors: Optional[Union[str, List[Any], Dict[Any, Any]]] = None,
    ax: Optional[Axes] = None,
    **kwargs
) -> List[Text]:
    """
    Display text with different colors and properties for each string, supporting word wrapping and alignment.

    Parameters
    ----------
    x, y : float
        Starting position of the text block.
    strings : List[str]
        List of text strings to display.
    colors : Union[str, List[str], Dict[int, str]]
        Color for the text. Can be:
        - A single string: Applied to all strings.
        - A list of colors: Corresponding to each string (dynamic extension supported).
        - A dictionary: Mapping indices to colors (e.g., {1: 'red'}). Unspecified indices use default/black.
    ax : matplotlib.axes.Axes, optional
        The axes to draw on. If None, uses the current axes.
    **kwargs : dict
        Additional arguments passed to `ax.text`.
        
        Global arguments (applied to the whole block):
        - box_width (float): Maximum width of the text block for wrapping. If None, no wrapping occurs.
        - linespacing (float): Line spacing multiplier (default: 1.5).
        - ha (str): Horizontal alignment ('left', 'center', 'right').
        - va (str): Vertical alignment ('top', 'center', 'bottom').
        - zorder (int): Z-order for the text.
        - transform: Transform for the text.

        Per-segment arguments:
        - Any other text property (e.g., fontsize, fontweight, fontproperties) can be:
          - A single value: Applied to all strings.
          - A list of values: Corresponding to each string (dynamic extension supported).
          - A dictionary: Mapping indices to values (e.g., {1: 20}).
          - underline (bool): If True, draws a line below the text.

    Returns
    -------
    List[matplotlib.text.Text]
        A list of the created Text objects.

    Raises
    ------
    ValueError
        If inputs are invalid.
    """
    if ax is None:
        ax = plt.gca()

    # Extract global special kwargs
    box_width: Optional[float] = kwargs.pop('box_width', None)
    linespacing: float = kwargs.pop('linespacing', 1.5)
    if 'spacing' in kwargs:
        linespacing = kwargs.pop('spacing')
    
    ha = kwargs.pop('ha', kwargs.pop('horizontalalignment', 'left'))
    va = kwargs.pop('va', kwargs.pop('verticalalignment', 'center'))
    transform = kwargs.pop('transform', ax.transData)
    zorder = kwargs.pop('zorder', 1)
    
    # Normalize properties for each string segment
    segment_properties = _normalize_properties(strings, colors, **kwargs)

    # Get renderer for measuring text
    fig = ax.get_figure()
    if fig == None:
         raise ValueError("The axes must be associated with a figure.")
         
    try:
        renderer = fig.canvas.get_renderer()
    except Exception:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()

    # Logic separation: Wrapping vs Non-Wrapping
    if box_width is not None:
        # 1. Tokenize into words with properties
        words = _tokenize_strings(strings, segment_properties)
        # 2. Build lines with wrapping
        lines = _build_lines_wrapped(words, ax, renderer, box_width)
    else:
        # 1. Treat strings as segments
        # 2. Build a single line
        lines = [_build_line_seamless(strings, segment_properties, ax, renderer)]

    # 3. Draw lines
    text_objects = _draw_lines(
        lines, x, y, ax, renderer, 
        linespacing=linespacing, ha=ha, va=va, 
        transform=transform, zorder=zorder
    )

    return text_objects


def _normalize_properties(
    strings: List[str], 
    colors: Union[str, List[Any], Dict[Any, Any]], 
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Normalize colors and kwargs into a list of property dictionaries, one for each string.
    Supports:
    - Scalar values (applied globally).
    - Lists of values (dynamic extension).
    - Dictionaries with int/tuple keys (targeted overrides).
    - Lists of pairs [(indices, value)] (targeted overrides).
    - Plural arguments (e.g., fontsizes) overriding singular ones (e.g., fontsize).
    """
    n = len(strings)
    props_list = []
    
    # Helper to extend list to length n
    def extend_list(lst: List[Any], target_len: int) -> List[Any]:
        if not lst:
            return [None] * target_len 
        if len(lst) >= target_len:
            return lst[:target_len]
        last_val = lst[-1]
        extension = [last_val] * (target_len - len(lst))
        return lst + extension

    # Helper to parse mapping from dict or list-of-pairs
    def parse_mapping(val: Any) -> Optional[Dict[int, Any]]:
        flat_d = {}
        
        if isinstance(val, dict):
            for k, v in val.items():
                if isinstance(k, tuple):
                    for idx in k:
                        flat_d[idx] = v
                else:
                    flat_d[k] = v
            return flat_d
            
        if isinstance(val, list):
            if not val:
                return None
            first = val[0]
            if isinstance(first, (list, tuple)) and len(first) == 2:
                k, v = first
                if isinstance(k, int) or (isinstance(k, (list, tuple)) and all(isinstance(x, int) for x in k)):
                    for item in val:
                        if not (isinstance(item, (list, tuple)) and len(item) == 2):
                            return None 
                        k, v = item
                        if isinstance(k, (list, tuple)):
                            for idx in k:
                                flat_d[idx] = v
                        else:
                            flat_d[k] = v
                    return flat_d
            return None
        return None
    
    # Handle colors
    color_mapping = parse_mapping(colors)
    color_list = [None] * n
    
    if color_mapping is not None:
        pass 
    elif isinstance(colors, str):
        color_list = [colors] * n
    elif isinstance(colors, list):
        color_list = extend_list(colors, n)
    else:
        if colors is not None:
             raise ValueError("colors must be a string, a list, or a mapping.")
        
    # Handle other kwargs
    list_kwargs = {}
    mapping_kwargs = {}
    scalar_kwargs = {}
    
    # Map plural keys to singular keys
    plural_map = {
        'fontsizes': 'fontsize',
        'fontweights': 'fontweight',
        'fontfamilies': 'fontfamily',
        'fontstyles': 'fontstyle',
        'alphas': 'alpha',
        'backgroundcolors': 'backgroundcolor',
        'colors': 'color', # Special case if passed in kwargs
        'underlines': 'underline'
    }
    
    # Separate kwargs into types
    for k, v in kwargs.items():
        # Check for plural override first
        if k in plural_map:
            singular_k = plural_map[k]
            mapping = parse_mapping(v)
            if mapping is not None:
                if singular_k not in mapping_kwargs:
                    mapping_kwargs[singular_k] = {}
                mapping_kwargs[singular_k].update(mapping)
            elif isinstance(v, list):
                # If plural is a list, treat as list_kwargs for the singular key
                list_kwargs[singular_k] = extend_list(v, n)
            continue
            
        mapping = parse_mapping(v)
        if mapping is not None:
            mapping_kwargs[k] = mapping
        elif isinstance(v, list):
            list_kwargs[k] = extend_list(v, n)
        else:
            scalar_kwargs[k] = v
            
    for i in range(n):
        # 1. Start with scalar (global) properties
        props = scalar_kwargs.copy()
        
        # 2. Apply list-based properties (if any)
        for k, v_list in list_kwargs.items():
            props[k] = v_list[i]
            
        # 3. Apply color (specific overrides global)
        if color_list[i] is not None:
             props['color'] = color_list[i]
        
        if color_mapping and i in color_mapping:
            props['color'] = color_mapping[i]
        
        # 4. Apply mapping-based properties (specific overrides global & list)
        for k, v_map in mapping_kwargs.items():
            if i in v_map:
                props[k] = v_map[i]
                
        props_list.append(props)
        
    return props_list


def _tokenize_strings(
    strings: List[str], 
    properties: List[Dict[str, Any]]
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Split strings into words while preserving spaces and associating properties.
    Used ONLY when wrapping is enabled.
    """
    words: List[Tuple[str, Dict[str, Any]]] = []
    for string, props in zip(strings, properties):
        parts = string.split(' ')
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                words.append((part + ' ', props))
            else:
                if part:
                    words.append((part, props))
                elif not part and i > 0:
                     pass
    return words


def _get_text_width(text: str, ax: Axes, renderer, **text_kwargs) -> float:
    """Measure the width of a text string."""
    # Remove custom properties that ax.text doesn't understand
    kwargs = text_kwargs.copy()
    kwargs.pop('underline', None)
    
    t = ax.text(0, 0, text, **kwargs)
    bbox = t.get_window_extent(renderer=renderer)
    bbox_data = bbox.transformed(ax.transData.inverted())
    w = bbox_data.width
    t.remove()
    return w


def _get_text_height(text: str, ax: Axes, renderer, **text_kwargs) -> float:
    """Measure the height of a text string."""
    # Remove custom properties that ax.text doesn't understand
    kwargs = text_kwargs.copy()
    kwargs.pop('underline', None)

    # Use a representative character for height if text is empty or space
    # But we need the height of THIS specific font configuration.
    measure_text = text if text.strip() else "Hg"
    t = ax.text(0, 0, measure_text, **kwargs)
    bbox = t.get_window_extent(renderer=renderer)
    bbox_data = bbox.transformed(ax.transData.inverted())
    h = bbox_data.height
    t.remove()
    return h


def _build_lines_wrapped(
    words: List[Tuple[str, Dict[str, Any]]], 
    ax: Axes, 
    renderer, 
    box_width: float
) -> List[List[Tuple[str, Dict[str, Any], float]]]:
    """
    Group words into lines based on box_width.
    """
    lines: List[List[Tuple[str, Dict[str, Any], float]]] = []
    current_line: List[Tuple[str, Dict[str, Any], float]] = []
    current_line_width = 0.0

    for word, props in words:
        w = _get_text_width(word, ax, renderer, **props)
        
        if current_line_width + w > box_width and current_line:
            # Wrap to new line
            lines.append(current_line)
            current_line = [(word, props, w)]
            current_line_width = w
        else:
            current_line.append((word, props, w))
            current_line_width += w
            
    if current_line:
        lines.append(current_line)
        
    return lines


def _build_line_seamless(
    strings: List[str],
    properties: List[Dict[str, Any]],
    ax: Axes,
    renderer
) -> List[Tuple[str, Dict[str, Any], float]]:
    """
    Build a single line from strings without splitting by spaces.
    """
    line: List[Tuple[str, Dict[str, Any], float]] = []
    for string, props in zip(strings, properties):
        w = _get_text_width(string, ax, renderer, **props)
        line.append((string, props, w))
    return line


def _draw_lines(
    lines: List[List[Tuple[str, Dict[str, Any], float]]],
    x: float,
    y: float,
    ax: Axes,
    renderer,
    linespacing: float,
    ha: str,
    va: str,
    transform,
    zorder: int
) -> List[Text]:
    """
    Draw the lines of text onto the axes.
    """
    text_objects: List[Text] = []
    
    # Calculate height for each line
    line_heights = []
    for line in lines:
        # Find max height in this line
        max_h = 0.0
        for word, props, _ in line:
            h = _get_text_height(word, ax, renderer, **props)
            if h > max_h:
                max_h = h
        line_heights.append(max_h * linespacing)
        
    total_block_height = sum(line_heights)
    
    # Calculate top Y position based on vertical alignment
    if va == 'center':
        top_y = y + (total_block_height / 2)
    elif va == 'top':
        top_y = y
    elif va == 'bottom':
        top_y = y + total_block_height
    else: 
        top_y = y + (total_block_height / 2)

    current_y = top_y
    
    for i, line in enumerate(lines):
        line_height = line_heights[i]
        
        # Position line center
        line_center_y = current_y - (line_height / 2)
        
        # Calculate line width for horizontal alignment
        line_width = sum(item[2] for item in line)
        
        if ha == 'center':
            line_start_x = x - (line_width / 2)
        elif ha == 'right':
            line_start_x = x - line_width
        else: # left
            line_start_x = x
            
        current_x = line_start_x
        
        for word, props, w in line:
            text_kwargs = props.copy()
            
            # Extract underline property
            underline = text_kwargs.pop('underline', False)
            
            text_kwargs.update({
                'va': 'center', 
                'ha': 'left',
                'transform': transform,
                'zorder': zorder
            })
            
            t = ax.text(current_x, line_center_y, word, **text_kwargs)
            text_objects.append(t)
            
            # Draw underline if requested
            if underline:
                # Get the bounding box of the text we just drew
                # We can use the width w we already calculated
                # But for Y position, we want it slightly below the text
                
                # A simple approximation is to draw it at the bottom of the line band?
                # Or relative to the text baseline?
                # Since we used va='center', the text is centered at line_center_y.
                # The height is roughly line_height / linespacing.
                # Let's put the underline at line_center_y - (h/2) - padding?
                
                # Let's use the bbox of the text object to find the bottom
                bbox = t.get_window_extent(renderer=renderer)
                bbox_data = bbox.transformed(ax.transData.inverted())
                
                # y0 is the bottom of the text bbox
                y_bottom = bbox_data.y0
                
                # Draw line from current_x to current_x + w
                # Use the same color as the text
                color = t.get_color()
                
                line = Line2D(
                    [current_x, current_x + w], 
                    [y_bottom, y_bottom], 
                    color=color, 
                    linewidth=1, # Maybe configurable?
                    transform=transform,
                    zorder=zorder
                )
                ax.add_line(line)
            
            current_x += w
            
        current_y -= line_height
        
    return text_objects
