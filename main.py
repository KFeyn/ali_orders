import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import time
from concurrent.futures import ThreadPoolExecutor

import web_parsing as web
import drawing as draw

my_login = ''
my_password = ''


def get_new_order_names_every(period=43200):
    while True:
        try:
            web.get_orders_names(my_login, my_password)
            print("Order names information updated")
        except:
            pass
            print("Mistake in order names")

        time.sleep(period)


def get_new_orders_days_every(period=1800):
    global df
    while True:
        df = web.get_orders_days()
        print("Customs information updated")
        time.sleep(period)


df = web.get_orders_days()

max_days = (df['China'] + df['Russia']).max()

app = dash.Dash(__name__)
server = app.server
app.layout = html.Div([dcc.Interval(id='graph-update', interval=3600000, n_intervals=0),
                       dcc.RangeSlider(id='range_l',
                                       min=0,
                                       max=max_days,
                                       step=None,
                                       marks={0: '0 дней', 7: 'неделя', 14: '2 недели', 21: '3 недели', 30: 'месяц', 60: '2 месяца', max_days: 'максимум'},
                                       value=[0, max_days]),

                       dcc.Checklist(id='checklist',
                                     options=[{'label': i, 'value': i} for i in df['custom']],
                                     value=[i for i in df['custom']],
                                     labelStyle={'display': 'block'}
                                     ),
                       dcc.Graph('shot-dist-graph', config={'displayModeBar': False})])


@app.callback(
    Output('shot-dist-graph', 'figure'),
    [Input('checklist', 'value'),
     Input('range_l', 'value'),
     Input('graph-update', 'n_intervals')]
)
def update_graph(checklist, range_l, n):
    return draw.drawing(df, checklist, range_l)


executor = ThreadPoolExecutor(max_workers=3)
executor.submit(get_new_order_names_every)
executor.submit(get_new_orders_days_every)


if __name__ == '__main__':
    app.run_server(debug=False, host='192.168.1.2')
