import os
import argparse
import dash
from dash import Dash, html, dcc
import dash_mantine_components as dmc
import db

# Initialize Dash app with support for pages
app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

app.layout = dmc.MantineProvider(
    children=[
        html.H1("Multi-Page Timeline Application"),
        html.Div([
            dcc.Link(page["name"], href=page["relative_path"], style={"margin": "10px"})
            for page in dash.page_registry.values()
        ]),
        dash.page_container
    ]
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Dash application")
    parser.add_argument("--db", help="Path to the database file")
    args = parser.parse_args()
    if args.db:
        os.environ["EVENTS_DB_FILE"] = args.db
    db.init_db()
    app.run(debug=True)