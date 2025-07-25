import os
import argparse
import dash
from dash import Dash, html, dcc
import db

# Initialize Dash app with support for pages
app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

# Define the layout with a navigation header and page container
app.layout = html.Div([
    html.H1("Multi-Page Timeline Application"),
    html.Div([
        # Navigation links for each page in the app
        dcc.Link(page["name"], href=page["relative_path"], style={"margin": "10px"})
        for page in dash.page_registry.values()
    ]),
    # Container where the page content will be displayed
    dash.page_container
])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Dash application")
    parser.add_argument("--db", help="Path to the database file")
    args = parser.parse_args()
    if args.db:
        os.environ["EVENTS_DB_FILE"] = args.db
    db.init_db()
    app.run(debug=True)