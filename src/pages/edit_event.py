import dash
from dash import html, dcc, callback, Input, Output, State
import db
import pandas as pd
import dash_mantine_components as dmc
from typing import Any, cast, TypedDict

dash.register_page(__name__, path="/edit_event", name="Edit Event")

def layout():
    events = db.get_events()
    # --- type-annotation silences Pylance -----------------------------------
    event_options = [
        {"label": f'{ev["name"]} ({ev["tag"]})', "value": ev["id"]}
        for ev in events
    ]
    return html.Div([
        html.H2("Edit / Delete Existing Event"),
        dcc.Dropdown(id="event-picker", options=cast(Any, event_options),
                     placeholder="Select an event to edit", className="full-width"),
        html.Br(),
        html.Div(id="edit-form-container"),      # populated once an event is chosen
        dcc.Location(id="go-back", href="", refresh=False),
        html.Div(id="edit-msg", className="message")
    ], className="page-container")

# --- populate the form when an event is picked ------------------------------
@callback(Output("edit-form-container", "children"),
          Input("event-picker", "value"))
def load_event_form(selected_id):
    if not selected_id:
        return ""
    ev = next(e for e in db.get_events() if e["id"] == selected_id)
    events_all = db.get_events()
    events_all_df = pd.DataFrame(db.get_events())
    categories = events_all_df["category"].unique().tolist()
    topics = events_all_df["topic"].unique().tolist()
    countries = events_all_df["country"].unique().tolist()
    return html.Div([
        html.Label("Name:"),  dcc.Input(id="e-name", value=ev["name"], className="full-width"),
        html.Br(),
        html.Label("Description:"),
        dcc.Textarea(id="e-desc", value=ev["description"] or "",
                     className="textarea"),
        html.Br(),
        html.Label("Start Date:"), dcc.DatePickerSingle(id="e-start", date=ev["date_start"]),
        html.Label("End Date:"),  dcc.DatePickerSingle(id="e-end",   date=ev["date_end"]),
        html.Br(),
        html.Br(),
        html.Div(
            [
                html.Div([
                    html.Label("Category:"),
                    dmc.TagsInput(
                        id="e-category",
                        data=categories,
                        value=[ev["category"]] if ev.get("category") else [],
                        placeholder="Pick existing or type a new one",
                        clearable=True,
                        maxTags=1,
                    ),
                ], className="flex-1"),

                html.Div([
                    html.Label("Topic:"),
                    dmc.TagsInput(
                        id="e-topic", 
                        data = topics,
                        value=[ev["topic"]] if ev.get("topic") else [], 
                        placeholder ="Pick existing or type a new one",
                        clearable=True,
                        maxTags=1,
                        ),
                ], className="flex-1"),

                html.Div([
                    html.Label("Country:"),
                    dmc.TagsInput(
                        id="e-country", 
                        data = countries,
                        value=[ev["country"]] if ev.get("country") else [], 
                        placeholder = "Pick existing or type a new one",
                        clearable=True,
                        maxTags=1,
                        ),
                ], className="flex-1"),
            ],
            className="flex-row",
        ),
        html.Div(
            [
                html.Div([
                    html.Label("Affected By:"),
                    dcc.Dropdown(
                        id="e-affected-by",
                        options=[{"label": f'{e["name"]} ({e["tag"]})', "value": e["id"]} for e in events_all],
                        value=ev["affected_by"],
                        multi=True,
                        placeholder="Select events that caused this event",
                        className="full-width",
                    ),
                ], className="flex-1"),

                html.Div([
                    html.Label("Affects:"),
                    dcc.Dropdown(
                        id="e-affects",
                        options=[{"label": f'{e["name"]} ({e["tag"]})', "value": e["id"]} for e in events_all],
                        value=ev["affects"],
                        multi=True,
                        placeholder="Select events that this event caused",
                        className="full-width",
                    ),
                ], className="flex-1"),
            ],
            className="flex-row",
        ),
        html.Br(), html.Br(),
        html.Button("Save Changes", id="save-btn", n_clicks=0),
        html.Button("Delete", id="del-btn", n_clicks=0, className="delete ml-20"),
    ])

# --- handle save / delete ----------------------------------------------------
@callback(
    Output("go-back", "href"),
    Output("edit-msg", "children"),
    Input("save-btn", "n_clicks"),
    Input("del-btn", "n_clicks"),
    State("event-picker", "value"),
    State("e-name", "value"),
    State("e-desc", "value"),
    State("e-start", "date"),
    State("e-end", "date"),
    State("e-category", "value"),
    State("e-topic", "value"),
    State("e-country", "value"),
    prevent_initial_call=True
)
def commit_change(n_save, n_del, ev_id, name, desc, start, end, category, topic, country):
    ctx = dash.callback_context
    if not ctx.triggered or not ev_id:
        return dash.no_update, dash.no_update
    btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if btn_id == "del-btn":
        db.delete_event(ev_id)
        return "/", ""          # return to timeline
    # else save
    if not name or not start:
        return dash.no_update, "Name and Start Date are required."
    db.update_event(ev_id, name=name.strip(),
                    description=(desc or "").strip(),
                    date_start=start, date_end=end,category = category[0].strip(), topic = topic[0].strip(), country=country[0].strip())
    return "/", ""