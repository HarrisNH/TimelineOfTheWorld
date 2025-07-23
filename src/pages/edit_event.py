import dash
from dash import html, dcc, callback, Input, Output, State
import db

dash.register_page(__name__, path="/edit_event", name="Edit Event")

def layout():
    events = db.get_events()
    # --- type-annotation silences Pylance -----------------------------------
    event_options: list[dict[str, str]] = [
        {"label": f'{ev["name"]} ({ev["tag"]})', "value": ev["id"]}
        for ev in events
    ]
    return html.Div([
        html.H2("Edit / Delete Existing Event"),
        dcc.Dropdown(id="event-picker", options=event_options,
                     placeholder="Select an event to edit"),
        html.Br(),
        html.Div(id="edit-form-container"),      # populated once an event is chosen
        dcc.Location(id="go-back", href="", refresh=False),
        html.Div(id="edit-msg", style={"marginTop": "10px", "color": "red"})
    ])

# --- populate the form when an event is picked ------------------------------
@callback(Output("edit-form-container", "children"),
          Input("event-picker", "value"))
def load_event_form(selected_id):
    if not selected_id:
        return ""
    ev = next(e for e in db.get_events() if e["id"] == selected_id)
    return html.Div([
        html.Label("Name:"),  dcc.Input(id="e-name", value=ev["name"], style={"width": "100%"}),
        html.Br(),
        html.Label("Description:"),
        dcc.Textarea(id="e-desc", value=ev["description"] or "",
                     style={"width": "100%", "height": "80px"}),
        html.Br(),
        html.Label("Start Date:"), dcc.DatePickerSingle(id="e-start", date=ev["date_start"]),
        html.Label(" End Date:"),  dcc.DatePickerSingle(id="e-end",   date=ev["date_end"]),
        html.Br(), html.Br(),
        html.Button("Save Changes", id="save-btn", n_clicks=0),
        html.Button("Delete", id="del-btn", n_clicks=0,
                    style={"marginLeft": "20px", "background": "#c23", "color": "white"}),
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
    prevent_initial_call=True
)
def commit_change(n_save, n_del, ev_id, name, desc, start, end):
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
                    date_start=start, date_end=end)
    return "/", ""