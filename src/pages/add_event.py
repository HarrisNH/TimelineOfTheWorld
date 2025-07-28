import dash
from dash import html, dcc, callback, Input, Output, State
import db
import pandas as pd
from typing import Any, cast, TypedDict
import dash_mantine_components as dmc

dash.register_page(__name__, name="Add Event", path="/add_event")

def layout():
    # Fetch current events to populate the related-event dropdown options
    events = db.get_events()
    events_all_df: pd.DataFrame = pd.DataFrame(events)   # <- this is a DataFrame
    categories = events_all_df["category"].unique().tolist()
    topics = events_all_df["topic"].unique().tolist()
    countries = events_all_df["country"].unique().tolist()
    event_options = [{"label": f'{ev["name"]} ({ev["tag"]})', "value": ev["tag"]} for ev in events]
    
    return html.Div([
        html.H2("Add New Event"),
        html.Div([
                    html.Label("Category:"),
                    dmc.TagsInput(
                        id="input-category",
                        data=categories,
                        placeholder="Pick existing or type a new one",
                        clearable=True,
                        maxTags=1,
                    ),
        ], className="form-group"),
        html.Div([
                    html.Label("Topic:"),
                    dmc.TagsInput(
                        id="input-topic",
                        data=topics,
                        placeholder="Pick existing or type a new one",
                        clearable=True,
                        maxTags=1,
                    ),
        ], className="form-group"),
        html.Div([
            html.Label("Name:*"),
            dcc.Input(id="input-name", type="text", placeholder="e.g. World War III", className="full-width")
        ], className="form-group"),
        html.Div([
                    html.Label("Country:"),
                    dmc.TagsInput(
                        id="input-country",
                        data=countries,
                        placeholder="Pick existing or type a new one",
                        clearable=True,
                        maxTags=1,
                    ),
        ], className="form-group"),
        html.Div([
            html.Label("Start Date:*"),
            dcc.DatePickerSingle(id="input-date-start", display_format="YYYY-MM-DD")
        ], className="form-group"),
        html.Div([
            html.Label("End Date:"),
            dcc.DatePickerSingle(id="input-date-end", display_format="YYYY-MM-DD")
        ], className="form-group"),
        html.Div([
            html.Label("Description:"),
            html.Br(),
            dcc.Textarea(
                id="input-description",
                placeholder="Event description (optional)",
                className="textarea",
            ),
        ], className="form-group"),
        html.Div([
            html.Label("Affected By (select events that cause this event):"),
            dcc.Dropdown(id="input-affected-by", options=cast(Any, event_options),multi=True,
                         placeholder="Select preceding related events")
        ], className="form-group"),
        html.Div([
            html.Label("Affects (select events that this event will cause):"),
            dcc.Dropdown(id="input-affects", options=cast(Any, event_options), multi=True,
                         placeholder="Select subsequent related events")
        ], className="form-group"),
        # Submit button
        html.Button("Add Event", id="submit-event", n_clicks=0),
        # Hidden location component for redirecting after submission
        dcc.Location(id="redirect-page", href="", refresh=False),
        # Message area for errors or confirmations
        html.Div(id="form-message", className="message")
    ], className="page-container")

@callback(
    Output("redirect-page", "href"),
    Output("form-message", "children"),
    Input("submit-event", "n_clicks"),
    State("input-category", "value"),
    State("input-topic", "value"),
    State("input-name", "value"),
    State("input-country", "value"),
    State("input-date-start", "date"),
    State("input-date-end", "date"),
    State("input-description", "value"),
    State("input-affected-by", "value"),
    State("input-affects", "value"),
    prevent_initial_call=True
)
def submit_new_event(n_clicks, category, topic, name, country, date_start, date_end, description, affected_by, affects):
    if n_clicks is None or n_clicks < 1:
        return dash.no_update, dash.no_update
    # Validate required fields
    missing = []
    category = category[0] if isinstance(category, list) else category
    topic = topic[0] if isinstance(topic, list) else topic
    country = country[0] if isinstance(country, list) else country
    if not category or not category.strip():
        missing.append("Category")
    if not topic or not topic.strip():
        missing.append("Topic")
    if not name or not name.strip():
        missing.append("Name")
    if not date_start:
        missing.append("Start Date")
    if missing:
        return dash.no_update, "Please provide: " + ", ".join(missing)
    # Validate date range
    if date_end and date_end < date_start:
        return dash.no_update, "End date cannot be earlier than start date."
    # Generate the unique tag for the new event (Category_Topic_Name_Year)
    year = date_start[:4] if date_start else ""
    tag_cat = category.strip().replace(" ", "_").replace(",", "_")
    tag_topic = topic.strip().replace(" ", "_").replace(",", "_")
    tag_name = name.strip().replace(" ", "_").replace(",", "_")
    new_tag = f"{tag_cat}_{tag_topic}_{tag_name}_{year}"
    # Prepare related tags strings for storage
    affected_by_tags = affected_by if affected_by else []
    affects_tags = affects if affects else []
    # Insert the new event into the database
    try:
        db.insert_event(
            category.strip(),
            topic.strip(),
            name.strip(),
            (country.strip() if country else ""),
            date_start,
            date_end,
            (description if description else ""),
            new_tag,
            ",".join(affected_by_tags),
            ",".join(affects_tags),
        )
    except ValueError as exc:
        return dash.no_update, str(exc)
    # Update related events in the database to maintain two-way relationships
    for tag in affected_by_tags:
        db.add_relation_tag(tag, "affects", new_tag)
    for tag in affects_tags:
        db.add_relation_tag(tag, "affected_by", new_tag)
    # Redirect to the timeline page upon successful submission

    return "/", "Insertion successful! You can now view the new event in the timeline."
