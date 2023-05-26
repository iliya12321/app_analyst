from dash import html, Output, Input, State, dcc
from dash_extensions.enrich import (DashProxy,
                                    ServersideOutputTransform,
                                    MultiplexerTransform)
import dash_mantine_components as dmc
from dash.exceptions import PreventUpdate

import sqlite3
import pandas as pd
import plotly.express as px


connection = sqlite3.connect('тз/testDB.db')
df = pd.read_sql_query('SELECT * FROM sources', con=connection)

df_sum = df.groupby('reason').sum()

df['state_end'] = pd.to_datetime(df.state_end)
df['state_begin']= pd.to_datetime(df.state_begin)
df['duration'] = (df.state_end - df.state_begin).apply(lambda x: f"{int(x.total_seconds() // 60)}.{int(x.total_seconds() % 60):02d} мин")

circle = px.pie(df_sum, values='duration_hour', names=df_sum.index)
circle.update_layout(margin=dict(t=0, b=0, l=0, r=0))

def get_timeline(data_frame):
    timeline = px.timeline(data_frame, x_start='state_begin', x_end='state_end', y='endpoint_name', template="plotly_white", color='color',
                        hover_data=['state', 'reason', 'shift_day', 'period_name', 'operator', 'duration'])
    timeline.update_yaxes(title_text='')
    timeline.update_layout(showlegend=False, xaxis_tickformat='%H', title='График состояний',  title_x=0.5)
    timeline.update_traces(hovertemplate=f"<br>Состояние - %{{customdata[0]}}<extra></extra>"
                                        f"<br>Причина - %{{customdata[1]}}"
                                        f"<br>Начало -  %{{base|%H:%M:%S (%d.%m)}}"
                                        f"<br>Длительность - %{{customdata[5]}}<br>"
                                        f"<br>Сменный день - %{{customdata[2]}}"
                                        f"<br>Смена - %{{customdata[3]}}"
                                        f"<br>Оператор - %{{customdata[4]}}<br>")
    return timeline

CARD_STYLE = dict(withBorder=True,
                  shadow="sm",
                  radius="md",
                  style={'height': '400px'})

CARD_LOWER_STYLE = dict(withBorder=True,
            shadow="sm",
            radius="md",
            style={'height': '250px'})


class EncostDash(DashProxy):
    def __init__(self, **kwargs):
        self.app_container = None
        super().__init__(transforms=[ServersideOutputTransform(),
                                     MultiplexerTransform()], **kwargs)


app = EncostDash(name=__name__)


def get_layout():
    return html.Div([
        dmc.Paper([
            dmc.Grid([
                dmc.Col([
                    dmc.Card([
                        html.Div([
                            html.H1('Клиент: Кирпичный завод'),
                            html.P('Сменный день: 2023-05-12'),
                            html.P('Клиент: Бетономешалка'),
                            html.P('Начало периода: 08:00:00 (12.05)'),
                            html.P('Конец периода: 08:00:00 (05.05)'),
                        ]),
                        html.Div([
                            dcc.Dropdown(df['reason'].unique(),
                                        id='reason_colomn', multi=True)
                        ]),
                        dmc.Button(
                            children='Фильтровать',
                            id='button1')],
                        **CARD_STYLE)
                ], span=6),
                dmc.Col([
                    dmc.Card([
                        html.Div(dcc.Graph(figure=circle, style={'height': '350px'}))],
                        **CARD_STYLE)
                ], span=6),
                dmc.Col([
                    dmc.Card([
                        html.Div([
                            dcc.Graph(id='graphic_timeline', figure=get_timeline(df), style={'height': '250px'})
                        ])],
                        **CARD_LOWER_STYLE)
                ], span=12),
            ], gutter="xl",)
        ])
    ])


app.layout = get_layout()


@app.callback(
    Output('graphic_timeline', 'figure'),
    Input('button1', 'n_clicks'),
    State('reason_colomn', 'value'),
    prevent_initial_call=True,
)
def update_div1(
    click,
    reasons
):
    if click is None:
        raise PreventUpdate
    
    if not reasons:
        return get_timeline(df)

    filtered_df = df[df['reason'].isin(reasons)]
    
    return get_timeline(filtered_df)


if __name__ == '__main__':
    app.run_server(debug=True)
