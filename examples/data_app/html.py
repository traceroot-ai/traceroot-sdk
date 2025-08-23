from dash import dcc, html


def create_layout(response_fig, accuracy_fig, styles):
    """Create the HTML layout for the dashboard"""
    return html.Div(
        [
            html.H1("AI Agent Dashboard",
                    style={
                        'text-align': 'center',
                        'color': 'white',
                        'margin': '10px 0 30px 0',
                        'text-shadow': styles['title_shadow'],
                        'font-weight': 'bold'
                    }),
            html.Div(
                [
                    html.Div(
                        [
                            html.H4("Response Times",
                                    style={
                                        'text-align': 'center',
                                        'margin': '5px 0',
                                        'color': '#2c3e50',
                                        'background': 'rgba(255,255,255,0.9)',
                                        'padding': '8px',
                                        'border-radius': '8px',
                                        'box-shadow':
                                        '0 2px 10px rgba(0,0,0,0.1)'
                                    }),
                            dcc.Graph(figure=response_fig,
                                      style={'height': styles['chart_height']})
                        ],
                        style={
                            'flex': f'0 0 {styles["card_width"]}',
                            'background': 'rgba(255,255,255,0.95)',
                            'border-radius': styles['border_radius'],
                            'padding': styles['card_padding'],
                            'box-shadow': styles['shadow'],
                            'margin-right': styles['gap']
                        }),
                    html.Div(
                        [
                            html.H4("Model Accuracy",
                                    style={
                                        'text-align': 'center',
                                        'margin': '5px 0',
                                        'color': '#2c3e50',
                                        'background': 'rgba(255,255,255,0.9)',
                                        'padding': '8px',
                                        'border-radius': '8px',
                                        'box-shadow':
                                        '0 2px 10px rgba(0,0,0,0.1)'
                                    }),
                            dcc.Graph(figure=accuracy_fig,
                                      style={'height': styles['chart_height']})
                        ],
                        style={
                            'flex': f'0 0 {styles["card_width"]}',
                            'background': 'rgba(255,255,255,0.95)',
                            'border-radius': styles['border_radius'],
                            'padding': styles['card_padding'],
                            'box-shadow': styles['shadow']
                        })
                ],
                style={
                    'display': 'flex',
                    'flex-direction': 'row',
                    'justify-content': 'center',
                    'align-items': 'flex-start',
                    'gap': styles['gap'],
                    'width': '100%'
                })
        ],
        style={
            'padding': styles['padding'],
            'font-family': 'Arial, sans-serif',
            'min-height': styles['viewport_height'],
            'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'background-attachment': 'fixed'
        })
