import dash
from dash import html, dcc
import db


dash.register_page(__name__, path="/event_detail", name="Event Detail")


def layout(tag=None, **kwargs):
    if not tag:
        return html.Div("No event specified")
    event = db.get_event_by_tag(tag)
    if not event:
        return html.Div("Event not found")

    def make_links(value):
        tags = [t for t in (value or "").split(',') if t]
        if not tags:
            return "None"
        return [
            dcc.Link(t, href=f"/event_detail?tag={t}", style={"marginRight": "10px"})
            for t in tags
        ]

    return html.Div([
        html.H2(event.get("name", "")),
        html.Ul([
            html.Li(f"Category: {event.get('category', '')}"),
            html.Li(f"Topic: {event.get('topic', '')}"),
            html.Li(f"Country: {event.get('country', '')}"),
            html.Li(f"Start Date: {event.get('date_start', '')}"),
            html.Li(f"End Date: {event.get('date_end', '')}"),
            html.Li(f"Description: {event.get('description', '')}"),
        ]),
        html.Div([html.Strong("Affected by: "), *make_links(event.get('affected_by'))]),
        html.Div([html.Strong("Affects: "), *make_links(event.get('affects'))])
    ], style={"marginLeft": "40px", "marginRight": "40px", "maxWidth": "800px"})
