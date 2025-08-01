import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from flags import get_flag
import dash_mantine_components as dmc
import db
# 4) add one scatter trace per category for instant events
from collections import defaultdict

dash.register_page(__name__, path="/", name="Timeline")

CATEGORY_PATTERN = {
    "Politics": "-", # dots
    "Science": "+", # plus
    "Culture": "x", # cross
    "War": "\\",
    # Other options:
    # "-" (horizontal lines)
    # "|" (vertical lines) 
    # "/" (diagonal lines)
    # "\\" (diagonal lines)
    # "*" (asterisk)
}
# Helper function to filter events based on selected criteria
def filter_events(events, categories=None, countries=None, start_date=None, end_date=None):
    filtered = []
    # If an empty list is provided for categories or countries, interpret as "no events"
    if categories is not None and len(categories) == 0:
        return []
    if countries is not None and len(countries) == 0:
        return []
    for ev in events:
        if categories and ev["category"] not in categories:
            continue
        if countries and ev["country"] not in countries:
            continue
        # Check date range overlap:
        # Convert dates from string to datetime for comparison
        ev_start = datetime.fromisoformat(ev["date_start"])
        ev_end = datetime.fromisoformat(ev["date_end"]) if ev["date_end"] else ev_start
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            if ev_end < start_dt:
                continue  # event ends before filter window start
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            if ev_start > end_dt:
                continue  # event starts after filter window end
        filtered.append(ev)
    return filtered

def assign_rows(events):
    """Assign each event a row identifier so that events within the same
    ``(category, country, topic)`` group that do not overlap in time share a row.

    Returns two lists: the ordered row identifiers and the labels for display."""

    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for ev in events:
        key = (ev["category"], ev["country"])
        grouped[key].append(ev)

    row_order: list[str] = []
    row_labels: list[str] = []

    for key in sorted(grouped):
        label = "<br>".join(key)
        evs = sorted(grouped[key], key=lambda e: e["date_start"])

        # ``slots`` holds the end time of the last event occupying each slot
        slots: list[datetime] = []

        for ev in evs:
            start_dt = datetime.fromisoformat(ev["date_start"])
            end_dt = (
                datetime.fromisoformat(ev["date_end"])
                if ev["date_end"] else start_dt
            )

            slot_index: int | None = None
            for idx, last_end in enumerate(slots):
                if start_dt >= last_end:
                    slot_index = idx
                    slots[idx] = end_dt
                    break

            if slot_index is None:
                slot_index = len(slots)
                slots.append(end_dt)

            row_id = f"{key[0]}|{key[1]}_{slot_index}"
            ev["row_id"] = row_id

            if row_id not in row_order:
                row_order.append(row_id)
                row_labels.append(label)

    return row_order, row_labels

# Helper function to create a Plotly timeline figure (adds arrows if show_arrows=True)
def make_timeline_figure(events, show_arrows=False):
    if not events:
        # Return an empty figure with a message if no events to display
        fig = go.Figure()
        fig.add_annotation(text="No events to display", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(size=16))
        return fig
    # Sort events by category and start date for logical grouping
    row_order, row_labels = assign_rows(events)
    events_sorted = sorted(events, key=lambda e: (row_order.index(e["row_id"]), e["date_start"]))    

    fig = px.timeline(
        events_sorted,
        x_start="date_start", x_end="date_end", y="row_id", color="category",
        hover_name="name",
        hover_data={"category": True, "topic": True, "country": True,
                    "date_start": True, "date_end": True, "description": True},
        custom_data=["tag"]
    )
    # Style bars differently for each category
    line_styles = {"Politics": "solid", "Science": "dot", "Culture": "dash"}
    for tr in fig.data:
        pattern = CATEGORY_PATTERN.get(tr.name, "")
        if pattern:
            tr.marker.pattern.shape = pattern


    # Add small flag annotations centered on each event bar
    def mid_point(start: str, end: str | None) -> datetime:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end) if end else start_dt
        return start_dt + (end_dt - start_dt) / 2

    # Add small flag annotations based on country
    flag_emojis = {"USA": "🇺🇸", "Germany": "🇩🇪", "Global": "🌐", "Israel": ""}
    for ev in events_sorted:
        flag = get_flag(ev["country"])
        if flag:
            fig.add_annotation(
                x=mid_point(ev["date_start"], ev["date_end"]),
                y=ev["row_id"],
                text=flag,
                showarrow=False,
                xanchor="center",
                yanchor="middle",
            )
    points = [e for e in events if not e["date_end"]]
    # 3) grab the colour that Plotly just used for every category
    cat_colour = {tr.name: tr.marker.color for tr in fig.data}


    bucket = defaultdict(list)
    for ev in points:
        bucket[ev["category"]].append(ev)

    for cat, ev_list in bucket.items():
        fig.add_scatter(
            x=[e["date_start"] for e in ev_list],
            y=[e["row_id"]        for e in ev_list],
            mode="markers",
            marker_symbol="diamond",
            marker_size=10,
            marker_color=cat_colour.get(cat, "black"),  # fallback just in case
            name=f"{cat} (instant)",                     # legend merges under same colour
            showlegend=False                             # or True if you want a toggle
        )

    # Set custom y-axis order (to keep categories grouped and in sorted order)
    ordered_tags = row_order
    tick_text = [ev["name"] for ev in events_sorted]
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=row_order,
        autorange="reversed",
        tickmode="array",
        tickvals=row_order,
        ticktext=row_labels,
    )
    fig.update_layout(yaxis_title="", margin=dict(l=100, r=20, t=40, b=40))
    # Add a range slider for easy horizontal panning/zooming
    fig.update_xaxes(rangeslider_visible=True)
    # Add arrows for causal links if toggled on
    if show_arrows:
        tag_to_row = {e["tag"]: e["row_id"] for e in events}
        for ev in events:
            src_row = tag_to_row.get(ev["tag"])
            if ev["affects"]:
                # For each target tag that this event affects
                targets = [t.strip() for t in ev["affects"].split(",") if t.strip()]
                for tgt_tag in targets:
                    target_event = next((e for e in events if e["tag"] == tgt_tag), None)
                    if not target_event:
                        continue  # target event not in current filtered list
                    # Define arrow endpoints
                    source_end_date = ev["date_end"] if ev["date_end"] else ev["date_start"]
                    target_start_date = target_event["date_start"]
                    # Determine horizontal arrow segment start point
                    x_tail = source_end_date
                    if source_end_date > target_start_date:
                        # If source extends beyond target start, align at target start to avoid backward arrow
                        x_tail = target_start_date
                    # Draw horizontal segment (no arrowhead) if there's a gap between source end and target start
                    if x_tail < target_start_date and src_row is not None:
                        fig.add_annotation(x=target_start_date, y=src_row,
                                           ax=x_tail, ay=src_row,
                                           xref="x", yref="y", axref="x", ayref="y",
                                           showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor="black", text="")
                    # Draw vertical arrow segment from source to target at the target start time
                    fig.add_annotation(x=target_start_date, y=tag_to_row.get(tgt_tag),
                                       ax=target_start_date, ay=src_row,
                                       xref="x", yref="y", axref="x", ayref="y",
                                       showarrow=True, arrowhead=3, arrowwidth=1, arrowcolor="black", text="")
    return fig

def layout():
    """Render the timeline page with the latest data."""
    events = db.get_events()
    categories = sorted({ev["category"] for ev in events})
    countries = sorted({ev["country"] for ev in events})
    min_date = min(ev["date_start"] for ev in events)
    max_date = max((ev["date_end"] if ev["date_end"] else ev["date_start"]) for ev in events)
    initial_fig = make_timeline_figure(events, show_arrows=False)

    return html.Div([
        html.H2("Timeline View"),
        # Filter controls section
        html.Div([
            html.Label("Category:"),
            dcc.Dropdown(
            id="filter-category",
            options=[{"label": cat, "value": cat} for cat in categories],
            value=categories,  # default select all categories
            multi=True
        ),
        html.Label(" Country:", className="filter-spacing"),
        dcc.Dropdown(
            id="filter-country",
            options=[{"label": c, "value": c} for c in countries],
            value=countries,  # default select all countries
            multi=True
        ),
        dmc.Box([
            dmc.Button("Choose dates", id="collapse-btn", n_clicks=0),
            dmc.Collapse(
                dmc.Group([
                    dmc.Text("Date Range:"),
                    dmc.TextInput(id="filter-date-start", placeholder="YYYY-MM-DD", value=min_date),
                    dmc.TextInput(id="filter-date-end", placeholder="YYYY-MM-DD", value=max_date),
                    dmc.Button(
                            "Apply Filters",
                            id="apply-filters",
                            variant="filled",
                            color="blue",),
                ], align="center"),
                opened=False, id="collapse-simple",  transitionDuration=1000,
        transitionTimingFunction="linear",),
                
        ]),
        html.Label(" ", className="filter-spacing"),  # spacer
        dcc.Checklist(
            id="toggle-arrows",
            options=[{"label": "Show causal links", "value": "show"}],
            value=[],  # unchecked by default (no arrows)
            className="checklist"
        )
    ], className="filter-controls"),
    # Timeline graph component
    dcc.Graph(id="timeline-graph", figure=initial_fig),
    # hidden location for navigating to event detail when a point is clicked
    # use callback-nav refresh mode so the new page loads without a full refresh
    dcc.Location(id="event-detail-nav", href="", refresh="callback-nav"),
], className="page-container")

# Callback to update the timeline graph when filters or arrow toggle change
@callback(
    Output("timeline-graph", "figure"),
    Input("filter-category", "value"),
    Input("filter-country", "value"),
    Input("apply-filters", "n_clicks"),
    Input("toggle-arrows", "value"),
    State("filter-date-start", "value"),
    State("filter-date-end", "value"),
)
def update_timeline(selected_categories, selected_countries, apply_filters, arrows_toggle, start_date, end_date, ):
    # Load the latest events (including any newly added events)
    events = db.get_events()
    # Apply filters
    filtered_events = filter_events(events,
                                    categories=selected_categories,
                                    countries=selected_countries,
                                    start_date=start_date,
                                    end_date=end_date)
    # Determine whether to show arrows based on the toggle
    show_arrows = bool(arrows_toggle and "show" in arrows_toggle)
    # Generate updated figure
    fig = make_timeline_figure(filtered_events, show_arrows=show_arrows)
    return fig


@callback(
    Output("event-detail-nav", "href", allow_duplicate=True),
    Input("timeline-graph", "clickData"),
    prevent_initial_call=True,
)
def go_to_detail(click_data):
    """Navigate to the event detail page when a bar is clicked."""
    if not click_data or "points" not in click_data:
        return dash.no_update
    point = click_data["points"][0]
    custom = point.get("customdata")
    tag = custom[0] if custom else None
    if not tag:
        return dash.no_update
    # Returning an href triggers a client side navigation
    return f"/event_detail?tag={tag}"
