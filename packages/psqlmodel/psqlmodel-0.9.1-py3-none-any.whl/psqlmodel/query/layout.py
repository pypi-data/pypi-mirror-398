
from typing import List, Any
from ..orm.column import Column, Alias

def calculate_layout(normalized_items: List[Any]) -> List[dict]:
    """
    Calculate the layout of the result set based on the selected items.
    
    Args:
        normalized_items: List of items (Models, Columns, Aliases, etc.)
        
    Returns:
        List of dictionaries describing the layout structure:
        - {"type": "model", "model": cls, "start": int, "end": int}
        - {"type": "scalar", "index": int, "key": str|None, "column": col|None}
    """
    layout = []
    current_idx = 0
    
    for item in normalized_items:
        item_expr = item.expr if isinstance(item, Alias) else item
        
        # CASE A: Full Model
        if hasattr(item_expr, "__tablename__") and hasattr(item_expr, "__columns__"):
            model_cls = item_expr
            cols_count = len(getattr(model_cls, "__columns__", {}))
            layout.append({
                "type": "model",
                "model": model_cls,
                "start": current_idx,
                "end": current_idx + cols_count
            })
            current_idx += cols_count
        
        # CASE B: Scalar (anything else)
        else:
            layout_item = {
                "type": "scalar",
                "index": current_idx,
                "key": None
            }
            
            # Determine key/name
            if getattr(item, "alias", None):
                layout_item["key"] = item.alias
            elif isinstance(item, Alias): # Just in case
                layout_item["key"] = item.alias
            elif hasattr(item_expr, "attr_name"): # Column
                layout_item["key"] = item_expr.attr_name
            elif isinstance(item_expr, Column) and hasattr(item_expr, "name"):
                    layout_item["key"] = item_expr.name
            
            # Capture Column definition specifically for JSON parsing
            if isinstance(item_expr, Column):
                layout_item["column"] = item_expr
            
            layout.append(layout_item)
            current_idx += 1
            
    return layout
