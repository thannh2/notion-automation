import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
from notion_automation import NotionApi


app = dash.Dash(__name__)

notion_api = NotionApi()
data = notion_api.summarize_data_work_checking()

df = pd.DataFrame(data)

fig_tasks = px.bar(df, x="Assignee", y="Task", 
                   title="Task", color="Assignee", text_auto=True)

fig_time = px.line(df, x="Assignee", y="Average time", 
                   title="Average time", markers=True)

app.layout = html.Div(children=[
    html.H1("Dashboard Hiệu Quả Công Việc"),
    
    dcc.Dropdown(
        id="time_range",
        options=[
            {"label": "Tuần", "value": "weekly"},
            {"label": "Tháng", "value": "monthly"},
            {"label": "Quý", "value": "quarterly"},
        ],
        value="monthly",
        style={"width": "50%"}
    ),
    
    dcc.Graph(figure=fig_tasks),
    dcc.Graph(figure=fig_time),
])

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
