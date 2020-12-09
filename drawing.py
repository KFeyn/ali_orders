import plotly.graph_objects as go


def drawing(alpha, checklist, range_sl):

    if type(checklist) == str:
        checklist = [checklist]

    alpha = alpha[alpha.custom.isin(checklist)]

    alpha = alpha[(alpha['China'] + alpha['Russia'] >= range_sl[0]) & (alpha['China'] + alpha['Russia'] <= range_sl[1])]

    x = alpha['custom']

    plot = go.Figure(data=[go.Bar(
        name='В Китае',
        y=x,
        x=alpha['China'], orientation='h', text=alpha['China']
        , textposition='inside', textangle=0
        , marker_color='crimson', customdata=alpha['last_status']
        , hovertemplate="Последний статус: %{customdata}"
    ),
        go.Bar(
            name='В России',
            y=x,
            x=alpha['Russia'], orientation='h', text=alpha['Russia']
            , textposition='inside', textangle=0
            , marker_color='blue', customdata=alpha['last_status']
            , hovertemplate="Последний статус: %{customdata}"
        )
    ])

    plot.update_layout(barmode='stack', xaxis=dict(
        title='Дни',
        titlefont_size=16,
        tickfont_size=14,
    ))
    return plot
