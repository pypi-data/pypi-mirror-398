from JUSU.core import Div, P


def comp():
    return Div(P("Component example"), cls="example", css={"example": {"color": "#333", "padding": "8px"}})
