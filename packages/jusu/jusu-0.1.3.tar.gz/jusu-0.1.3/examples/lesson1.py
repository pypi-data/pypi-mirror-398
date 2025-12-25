from JUSU import Div, H1, P, Button, Img, StyleSheet

page = Div(
    H1("Welcome to JUSU"),
    P("A tiny HTML builder."),
    Button("Click me", onclick="alert('Hello')", cls="btn"),
    Img(src="https://via.placeholder.com/150", alt="demo"),
    cls="container"
)

# Add a simple stylesheet
styles = StyleSheet()
styles.add_class("container", {"max-width": "800px", "margin": "0 auto", "padding": "1rem"})
styles.add_class("btn", {"background": "#007bff", "color": "white", "padding": "0.5rem 1rem", "border-radius": "4px"})

page.register_css(styles)
page.render_to_file("examples/jusu_demo.html", styles=styles)
print('Wrote examples/jusu_demo.html')
