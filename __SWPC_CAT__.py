#
# Copyright © 2018 United States Government as represented by the Administrator of the 
# National Aeronautics and Space Administration. All Rights Reserved.
#

__author__ = "Juan A. Figueroa, Reid Gomillion"
__credits__ = ["Juan A. Figueroa, Reid Gomillion, Asher Pembroke, Richard Mullinix"]
__version__ = "1.0"
__maintainer__ = "Juan A. Figueroa"
__email__ = "Juan.a.figueroa@nasa.gov, Reid.j.gomillion@nasa.gov"
__status__ = "Prototype"

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash.dependencies as dcd
import numpy as np
from scipy import stats
import plotly.graph_objs as go
from datetime import datetime, timedelta, date
from astropy.utils.data import download_file
import astropy.units as u
import sunpy
import json
import pandas as pd
import re
import julian
import logging
import flask
import os
import io
import swpc_utils
import pytz
import time

DEVMODE = True

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# constant for domain and grid inits
GRID_HALF_WIDTH = 800

# constants of the lemniscate
# C1 = Radial Distance
# C2 = C1 * tan(Angular Width/2)
# C3 = 1

# bernoullis lemniscate
# X = C1 * np.cos(theta)
# Y = C2 * np.cos(theta) * np.sin(theta) * np.cos(phi)
# Z = C2 * np.cos(theta) * np.sin(theta) * np.sin(phi)
#
# v = (X, Y, Z)

external_js = [
    'https://dap.digitalgov.gov/Universal-Federated-Analytics-Min.js?agency=NASA&subagency=GSFC&yt=true&dclink=true',
    {'src': 'https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js',
     'integrity': 'sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q',
     'crossorigin': 'anonymous'},
    {'src': 'https://code.jquery.com/jquery-3.2.1.slim.min.js',
     'integrity': 'sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN',
     'crossorigin': 'anonymous'},
    {'src': 'https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js',
     'integrity': 'sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl',
     'crossorigin': 'anonymous'}
]

external_css = ['https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css',
                'https://use.fontawesome.com/releases/v5.9.0/css/all.css']



app = dash.Dash(__name__,
                external_scripts=external_js,
                external_stylesheets=external_css,
                requests_pathname_prefix='/swpc_cat_web/')

if DEVMODE:
    app = dash.Dash(__name__,
                external_scripts=external_js,
                external_stylesheets=external_css)



# app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/brPBPO.css'})

server = app.server

app.title = 'SWPC_CAT'




@server.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(server.root_path, 'assets'),
                                     'favicon.ico')




# app.config.suppress_callback_exceptions = True

# --------------------------------------------------------------<html section>----------------------------------
# layout for dash application

app.layout = html.Div([
    # -----------<Nav-Bar>----------
    html.Nav(className='navbar navbar-expand-lg navbar-dark bg-dark',
             children=[
                 html.Button(className='navbar-toggler', type='button',
                             **{'data-toggle': 'collapse', 'data-target': '#navbarTogglerSection',
                                'aria-controls': 'navbarTogglerSection', 'aria-expanded': 'false',
                                'aria-label': 'Toggle navigation'},
                             children=[html.Span(className='navbar-toggler-icon')]),
                 html.Span(className="navbar-brand",
                           children=[
                               html.Img(src='/assets/SWPC_CAT.png',
                                        width='50', height='50', className='d-inline', style={'margin-right': '10px'}),
                               'SWPC_CAT']),
                 html.Div(className='collapse navbar-collapse', id='navbarTogglerSection',
                          children=[
                              html.Ul(className='navbar-nav mr-auto mt-2 mt-lg-0',
                                      children=[
                                          html.Li(className='nav-item',
                                                  children=[
                                                      html.A(className='nav-link active', href='#',
                                                             children=[html.H5(children=['Home']),
                                                                       html.Span(className='sr-only',
                                                                                 children=['(current)'])])]),
                                          html.Li(className='nav-item',
                                                  children=[
                                                      html.A(className='nav-link',
                                                             href='https://ccmc.gsfc.nasa.gov/swpc_cat_web/',
                                                             children=[html.H5(children=['About'])])]),
                                          html.Li(className='nav-item',
                                                  children=[
                                                      html.A(className='nav-link', href='https://ccmc.gsfc.nasa.gov/',
                                                             children=[html.H5(children=['CCMC'])])]),
                                          html.Li(className='nav-item',
                                                  children=[
                                                      html.A(className='nav-link',
                                                             href='https://www.nasa.gov/centers/goddard/home/index.html',
                                                             children=[html.H5(children=['NASA'])])]),
                                      ]),
                              html.H5(className='navbar-text text-white  mr-sm-2',
                                      children=['Select Start Date and Time:']),
                              dcc.DatePickerSingle(
                                  placeholder='YYYY-MM-DD',
                                  date=datetime.now(tz=pytz.UTC).date(),
                                  min_date_allowed=datetime(2007, 1, 1),
                                  #max_date_allowed=datetime.now(tz=pytz.UTC).date(),
                                  display_format='YYYY-MM-DD',
                                  id='date-picker',
                                  className='mr-sm-2'),

                              html.Div(className='mr-sm-2',
                                       children=[
                                           dcc.Input(type='text',
                                                     placeholder="HH:MM",
                                                     style={'width': '80px'},
                                                     className='form-control',
                                                     value='00:00',
                                                     pattern=u"^(2[0-3]|[01]?[0-9]):([0-5]?[0-9])$",
                                                     id='date-time')
                                       ]),

                              dcc.RadioItems(
                                  id='end-time',
                                  inputStyle={"margin-left": "5px"},
                                  className='text-white',
                                  labelStyle={'display': 'inline-block'},
                                  options=[
                                      {'label': '+6 hrs ', 'value': 6},
                                      {'label': '+12 hrs ', 'value': 12},
                                      {'label': '+24 hrs ', 'value': 24}
                                  ],
                                  value=6
                              ),

                              html.Button(
                                  style={'margin-right': '5px',
                                         'margin-left': '5px'},
                                  **{'data-toggle': 'tooltip',
                                     'data-placement': 'bottom',
                                     'title': 'Loads two days of images, if available, starting from the selected date'},
                                  id='btn-load-images',
                                  type='button',
                                  className='btn btn-primary btn-md',
                                  n_clicks_timestamp=0,
                                  children=['Load Images'])

                          ])

             ]),
    # -----------</Nav-Bar>----------

    # -----------<Plot-Section>----------
    html.Div(className='container-fluid',
             children=[html.Div(className='row',
                                children=[
                                    html.Div(className='col card bg-dark text-center',
                                             id='STEREO-B',
                                             children=[
                                                 html.Div(className='card-header row',
                                                          children=[
                                                              html.Button(
                                                                  id='left_move_btn_l',
                                                                  style={'margin-left': '20px'},
                                                                  type='button',
                                                                  className='btn btn-primary col-sm-1',
                                                                  n_clicks_timestamp=0,
                                                                  children=[
                                                                      html.Span(className='fas fa-arrow-left')
                                                                  ]),
                                                              html.Div(className='col',
                                                                       children=[
                                                                           dcc.Dropdown(
                                                                               id='l-image-dropdown',
                                                                               options=[
                                                                                   {'label': 'STEREO B COR2 - Running difference',
                                                                                    'value': 'Norm'}
                                                                               ],
                                                                               value='Norm',
                                                                               searchable=False,
                                                                               clearable=False
                                                                           )]),
                                                              html.Button(
                                                                  id='right_move_btn_l',
                                                                  style={'margin-right': '20px'},
                                                                  type='button',
                                                                  className='btn btn-primary col-sm-1',
                                                                  n_clicks_timestamp=0,
                                                                  children=[
                                                                      html.Span(className='fas fa-arrow-right')
                                                                  ]),
                                                              html.Button(
                                                                  id='time_import_btn_l',
                                                                  className='btn btn-primary col-sm-1',
                                                                  type='button',
                                                                  title='Sync other spacecraft to this timestamp',
                                                                  n_clicks_timestamp=0,
                                                                  style={'margin-right': '20px'},
                                                                  children=[
                                                                      html.Img(src='assets/clock.png', height=24, width=24)
                                                                  ])]),

                                                 html.Div(id='l-image-text',
                                                          style={'color': 'white',
                                                                 'font-size': 'x-large'}),
                                                 html.Div(className='row',
                                                          children=[
                                                              dcc.Slider(
                                                                  className='col',
                                                                  id='l-image-slider',
                                                                  min=1,
                                                                  max=1,
                                                                  value=1,
                                                                  step=1,
                                                                  updatemode='mouseup'),
                                                              html.Div(className='text-center',
                                                                       children=[
                                                                           html.Div(
                                                                               className='btn-group btn-group-sm',
                                                                               role='group',
                                                                               **{
                                                                                   'aria-label': 'button-group-r'},
                                                                               children=[
                                                                                   html.Button(
                                                                                       style={'margin-right': '20px'},
                                                                                       id='l-btn-match',
                                                                                       type='button',
                                                                                       n_clicks_timestamp=0,
                                                                                       className='btn btn-primary btn-lg btn-block',
                                                                                       children=['Match Image']),
                                                                                   html.Button(
                                                                                       style={'margin-right': '20px'},
                                                                                       id='unmatch-btn-l',
                                                                                       n_clicks_timestamp=0,
                                                                                       type='button',
                                                                                       className='btn btn-primary btn-lg btn-block',
                                                                                       children=['Unmatch Image']),
                                                                               ])
                                                                       ]),


                                                          ]),
                                                 html.Div(
                                                     style={'margin': 'auto'},
                                                     children=[
                                                         dcc.Loading(type='circle',
                                                                     children=[
                                                                         dcc.Graph(id='2d-l-lemniscate',
                                                                                   config={
                                                                                       'modeBarButtonsToRemove': [
                                                                                           'sendDataToCloud',
                                                                                           'zoom2d', 'pan2d',
                                                                                           'select2d',
                                                                                           'lasso2d', 'zoomIn2d',
                                                                                           'zoomOut2d',
                                                                                           'hoverCompareCartesian',
                                                                                           'hoverClosestCartesian',
                                                                                           'toggleSpikelines'],
                                                                                       'displaylogo': False})]),
                                                     ]),


                                                 html.Br()
                                             ]),
                                    html.Div(className='col card bg-dark text-center',
                                             id='SOHO',
                                             children=[
                                                 html.Div(className='card-header row',
                                                          children=[
                                                              html.Button(
                                                                  id='left_move_btn_c',
                                                                  style={'margin-left': '20px'},
                                                                  type='button',
                                                                  className='btn btn-primary col-sm-1',
                                                                  n_clicks_timestamp=0,
                                                                  children=[
                                                                      html.Span(className='fas fa-arrow-left')
                                                                  ]),
                                                              html.Div(className='col',
                                                                       children=[
                                                                           dcc.Dropdown(
                                                                               id='c-image-dropdown',
                                                                               options=[
                                                                                   {
                                                                                       'label': 'SOHO LASCO C2 - Running difference',
                                                                                       'value': 'C2'},
                                                                                   {
                                                                                       'label': 'SOHO LASCO C3 - Running difference',
                                                                                       'value': 'C3'},
                                                                               ],
                                                                               value='C3',
                                                                               searchable=False,
                                                                               clearable=False
                                                                           )]),
                                                              html.Button(
                                                                  id='right_move_btn_c',
                                                                  style={'margin-right': '20px'},
                                                                  type='button',
                                                                  className='btn btn-primary col-sm-1',
                                                                  n_clicks_timestamp=0,
                                                                  children=[
                                                                      html.Span(className='fas fa-arrow-right')
                                                                  ]),
                                                              html.Button(
                                                                  id='time_import_btn_c',
                                                                  className='btn btn-primary col-sm-1',
                                                                  type='button',
                                                                  title='Sync other spacecraft to this timestamp',
                                                                  n_clicks_timestamp=0,
                                                                  style={'margin-right': '20px'},
                                                                  children=[
                                                                      html.Img(src='assets/clock.png', height=24,
                                                                               width=24)
                                                                  ]
                                                              )
                                                          ]),
                                                 html.Div(id='c-image-text',
                                                          style={'color': 'white',
                                                                 'font-size': 'x-large'}),
                                                 html.Div(className='row',
                                                          children=[
                                                              dcc.Slider(
                                                                  className='col',
                                                                  id='c-image-slider',
                                                                  min=1,
                                                                  max=1,
                                                                  value=1,
                                                                  step=1,
                                                                  updatemode='mouseup'),
                                                              html.Div(className='text-center',
                                                                       children=[
                                                                           html.Div(
                                                                               className='btn-group btn-group-sm',
                                                                               role='group',
                                                                               **{
                                                                                   'aria-label': 'button-group-r'},
                                                                               children=[
                                                                                   html.Button(
                                                                                       style={'margin-right': '20px'},
                                                                                       id='c-btn-match',
                                                                                       n_clicks_timestamp=0,
                                                                                       type='button',
                                                                                       className='btn btn-primary btn-lg btn-block',
                                                                                       children=['Match Image']),
                                                                                   html.Button(
                                                                                       style={'margin-right': '20px'},
                                                                                       id='unmatch-btn-c',
                                                                                       n_clicks_timestamp=0,
                                                                                       type='button',
                                                                                       className='btn btn-primary btn-lg btn-block',
                                                                                       children=['Unmatch Image']),
                                                                               ])
                                                                       ]),

                                                          ]),
                                                 html.Div(
                                                     style={'margin': 'auto'},
                                                     children=[
                                                         dcc.Loading(type='circle',
                                                                     children=[
                                                                         dcc.Graph(id='2d-c-lemniscate',
                                                                                   config={
                                                                                       'modeBarButtonsToRemove': ['sendDataToCloud',
                                                                                                                  'zoom2d', 'pan2d',
                                                                                                                  'select2d',
                                                                                                                  'lasso2d', 'zoomIn2d',
                                                                                                                  'zoomOut2d',
                                                                                                                  'hoverCompareCartesian',
                                                                                                                  'hoverClosestCartesian',
                                                                                                                  'toggleSpikelines'],
                                                                                       'displaylogo':False})]),
                                                     ]),

                                                 html.Br()
                                             ]),
                                    html.Div(className='col card bg-dark text-center',
                                             id='STEREO-A',
                                             children=[
                                                 html.Div(className='card-header row',
                                                          children=[
                                                              html.Button(
                                                                  id='left_move_btn_r',
                                                                  style={'margin-left': '20px'},
                                                                  type='button',
                                                                  n_clicks_timestamp=0,
                                                                  className='btn btn-primary col-sm-1',
                                                                  children=[
                                                                      html.Span(className='fas fa-arrow-left')
                                                                  ]),
                                                              html.Div(className='col',
                                                                       children=[
                                                                           dcc.Dropdown(
                                                                               id='r-image-dropdown',
                                                                               options=[
                                                                                   {
                                                                                       'label': 'STEREO A COR2 - Running difference',
                                                                                       'value': 'Norm'}],
                                                                               value='Norm',
                                                                               searchable=False,
                                                                               clearable=False
                                                                           )]),
                                                              html.Button(
                                                                  id='right_move_btn_r',
                                                                  type='button',
                                                                  style={'margin-right': '20px'},
                                                                  n_clicks_timestamp=0,
                                                                  className='btn btn-primary col-sm-1',
                                                                  children=[
                                                                      html.Span(className='fas fa-arrow-right')
                                                                  ]),
                                                              html.Button(
                                                                  id='time_import_btn_r',
                                                                  className='btn btn-primary col-sm-1',
                                                                  type='button',
                                                                  title='Sync other spacecraft to this timestamp',
                                                                  n_clicks_timestamp=0,
                                                                  style={'margin-right': '20px'},
                                                                  children=[
                                                                      html.Img(src='assets/clock.png', height=24, width=24)
                                                                  ])]),

                                                 html.Div(id='r-image-text',
                                                          style={'color': 'white',
                                                                 'font-size': 'x-large'}),

                                                 html.Div(className='row',
                                                          children=[
                                                              dcc.Slider(
                                                                  className='col',
                                                                  id='r-image-slider',
                                                                  min=1,
                                                                  max=1,
                                                                  value=1,
                                                                  step=1,
                                                                  updatemode='mouseup'),
                                                              html.Div(className='text-center',
                                                                       children=[
                                                                           html.Div(
                                                                               className='btn-group btn-group-sm',
                                                                               role='group',
                                                                               **{
                                                                                   'aria-label': 'button-group-r'},
                                                                               children=[
                                                                                   html.Button(
                                                                                       style={'margin-right': '20px'},
                                                                                       id='r-btn-match',
                                                                                       type='button',
                                                                                       n_clicks_timestamp=0,
                                                                                       className='btn btn-primary btn-lg btn-block',
                                                                                       children=['Match Image']),
                                                                                   html.Button(
                                                                                       style={'margin-right': '20px'},
                                                                                       id='unmatch-btn-r',
                                                                                       n_clicks_timestamp=0,
                                                                                       type='button',
                                                                                       className='btn btn-primary btn-lg btn-block',
                                                                                       children=['Unmatch Image']),
                                                                               ])
                                                                       ]),


                                                          ]),
                                                 html.Div(
                                                     style={'margin': 'auto'},
                                                     children=[
                                                         dcc.Loading(type='circle',
                                                                     children=[
                                                                         dcc.Graph(id='2d-r-lemniscate',
                                                                                   config={
                                                                                       'modeBarButtonsToRemove': [
                                                                                           'sendDataToCloud',
                                                                                           'zoom2d', 'pan2d',
                                                                                           'select2d',
                                                                                           'lasso2d', 'zoomIn2d',
                                                                                           'zoomOut2d',
                                                                                           'hoverCompareCartesian',
                                                                                           'hoverClosestCartesian',
                                                                                           'toggleSpikelines'],
                                                                                       'displaylogo': False})]),
                                                     ]),



                                                 html.Br()

                                             ])
                                ])

                       ]),
    # -----------</Plot-Section>----------

    html.Div(className='container-fluid',
             children=[
                 html.Div(className="row",
                          children=[
                              # -----------<IMG-Controls----------
                              html.Div(className='card col-xl-3 bg-light',
                                       style={'display': 'block'},
                                       children=[
                                           html.Div(className='card-header text-center font-weight-bold',
                                                    style={'text-align': 'left',
                                                           'font-size': 'x-large'},
                                                    children=['IMG-CONTROLS',
                                                              html.Ul(
                                                                  className='nav nav-pills nav-fill card-header-pills',
                                                                  children=[
                                                                      html.Li(className='nav-item',
                                                                              children=[
                                                                                  html.A(className='nav-link active',
                                                                                         **{'data-toggle': 'tab'},
                                                                                         href='#L-tab',
                                                                                         children=['STEREO B'])
                                                                              ]),
                                                                      html.Li(className='nav-item',
                                                                              children=[html.A(className='nav-link',
                                                                                               **{'data-toggle': 'tab'},
                                                                                               href='#C-tab',
                                                                                               children=['SOHO'])
                                                                                        ]),
                                                                      html.Li(className='nav-item',
                                                                              children=[html.A(className='nav-link',
                                                                                               **{'data-toggle': 'tab'},
                                                                                               href='#R-tab',
                                                                                               children=['STEREO A'])
                                                                                        ])
                                                                  ])
                                                              ]),

                                           html.Div(className='card-body',
                                                    children=[
                                                        html.Div(className='tab-content',
                                                                 children=[
                                                                     html.Div(
                                                                         className='tab-pane container active fade-in',
                                                                         id='L-tab',
                                                                         children=[
                                                                             html.Div(id="L-stretch-top-text",
                                                                                      style={'text-align': 'left',
                                                                                             'font-size': 'x-large'}),
                                                                             html.Br(),
                                                                             dcc.Slider(
                                                                                 id='L-stretch-top-slider',
                                                                                 min=0,
                                                                                 max=255,
                                                                                 value=0,
                                                                                 step=1,
                                                                                 marks={0: {'label': '0', 'style': {
                                                                                     'font-size': 'large'}},
                                                                                        63: {'label': '63', 'style': {
                                                                                            'font-size': 'large'}},
                                                                                        127: {'label': '127', 'style': {
                                                                                            'font-size': 'large'}},
                                                                                        191: {'label': '191', 'style': {
                                                                                            'font-size': 'large'}},
                                                                                        255: {'label': '255', 'style': {
                                                                                            'font-size': 'large'}}},
                                                                                 updatemode='mouseup'
                                                                             ),


                                                                             html.Div(id="L-stretch-bot-text",
                                                                                      style={'text-align': 'left',
                                                                                             'font-size': 'x-large'}),

                                                                             html.Br(),

                                                                             dcc.Slider(
                                                                                 id='L-stretch-bot-slider',
                                                                                 min=0,
                                                                                 max=255,
                                                                                 value=255,
                                                                                 step=1,
                                                                                 marks={0: {'label': '0', 'style': {
                                                                                     'font-size': 'large'}},
                                                                                        63: {'label': '63', 'style': {
                                                                                            'font-size': 'large'}},
                                                                                        127: {'label': '127', 'style': {
                                                                                            'font-size': 'large'}},
                                                                                        191: {'label': '191', 'style': {
                                                                                            'font-size': 'large'}},
                                                                                        255: {'label': '255', 'style': {
                                                                                            'font-size': 'large'}}},
                                                                                 updatemode='mouseup'
                                                                             ),

                                                                             html.Div(id="L-gamma-text",
                                                                                      style={'text-align': 'left',
                                                                                             'font-size': 'x-large'}),

                                                                             html.Br(),

                                                                             dcc.Slider(
                                                                                 id='L-gamma-slider',
                                                                                 min=0,
                                                                                 max=1,
                                                                                 value=1,
                                                                                 step=.05,
                                                                                 marks={0: {'label': '0', 'style': {
                                                                                     'font-size': 'large'}},
                                                                                        0.25: {'label': '.25',
                                                                                               'style': {
                                                                                                   'font-size': 'large'}},
                                                                                        .5: {'label': '.5', 'style': {
                                                                                            'font-size': 'large'}},
                                                                                        .75: {'label': '.75', 'style': {
                                                                                            'font-size': 'large'}},
                                                                                        1: {'label': '1', 'style': {
                                                                                            'font-size': 'large'}}},
                                                                                 updatemode='mouseup'
                                                                             ),


                                                                             html.Div(id='L-saturation-text',
                                                                                      style={'text-align': 'left',
                                                                                             'font-size': 'x-large'}),

                                                                             html.Br(),

                                                                             dcc.Slider(
                                                                                 id='L-saturation-slider',
                                                                                 min=0.1,
                                                                                 max=5,
                                                                                 value=.50,
                                                                                 step=.1,
                                                                                 marks={0: {'label': '0', 'style': {
                                                                                     'font-size': 'large'}},
                                                                                        1: {'label': '1', 'style': {
                                                                                            'font-size': 'large'}},
                                                                                        1.5: {'label': '1.5', 'style': {
                                                                                            'font-size': 'large'}},
                                                                                        2.5: {'label': '2.5', 'style': {
                                                                                            'font-size': 'large'}},
                                                                                        3.5: {'label': '3.5', 'style': {
                                                                                            'font-size': 'large'}},
                                                                                        5: {'label': '5', 'style': {
                                                                                            'font-size': 'large'}}},
                                                                                 updatemode='mouseup'),
                                                                             html.Br(),
                                                                             html.Div(className='text-center',
                                                                                      children=[
                                                                                          html.Button(id='L-Reset',
                                                                                                      type='button',
                                                                                                      className='btn btn-primary btn-lg',
                                                                                                      children=[
                                                                                                          'Reset'])]),
                                                                             html.Br(),
                                                                             # html.Div(className='text-center',
                                                                             #          children=[
                                                                             #              html.Div(
                                                                             #                  className='btn-group',
                                                                             #                  role='group',
                                                                             #                  **{
                                                                             #                      'aria-label': 'button-group-L'},
                                                                             #                  children=[
                                                                             #                      html.Button(
                                                                             #                          id='L-copy-C',
                                                                             #                          type='button',
                                                                             #                          className='btn btn-primary  btn-lg',
                                                                             #                          children=[
                                                                             #                              'Copy C']),
                                                                             #                      html.Button(
                                                                             #                          id='L-copy-R',
                                                                             #                          type='button',
                                                                             #                          className='btn btn-primary btn-lg',
                                                                             #                          children=[
                                                                             #                              'Copy R'])])
                                                                             #          ])
                                                                         ]),

                                                                     html.Div(className='tab-pane container fade-in',
                                                                              id='C-tab',
                                                                              children=[
                                                                                  html.Div(id="C-stretch-top-text",
                                                                                           style={'text-align': 'left',
                                                                                                  'font-size': 'x-large'}),
                                                                                  html.Br(),
                                                                                  dcc.Slider(
                                                                                      id='C-stretch-top-slider',
                                                                                      min=0,
                                                                                      max=255,
                                                                                      value=0,
                                                                                      step=1,
                                                                                      marks={0: {'label': '0',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}},
                                                                                             63: {'label': '63',
                                                                                                  'style': {
                                                                                                      'font-size': 'large'}},
                                                                                             127: {'label': '127',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             191: {'label': '191',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             255: {'label': '255',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}}},
                                                                                      updatemode='mouseup'
                                                                                  ),


                                                                                  html.Div(id="C-stretch-bot-text",
                                                                                           style={'text-align': 'left',
                                                                                                  'font-size': 'x-large'}),

                                                                                  html.Br(),

                                                                                  dcc.Slider(
                                                                                      id='C-stretch-bot-slider',
                                                                                      min=0,
                                                                                      max=255,
                                                                                      value=255,
                                                                                      step=1,
                                                                                      marks={0: {'label': '0',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}},
                                                                                             63: {'label': '63',
                                                                                                  'style': {
                                                                                                      'font-size': 'large'}},
                                                                                             127: {'label': '127',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             191: {'label': '191',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             255: {'label': '255',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}}},
                                                                                      updatemode='mouseup'
                                                                                  ),

                                                                                  html.Div(id="C-gamma-text",
                                                                                           style={'text-align': 'left',
                                                                                                  'font-size': 'x-large'}),

                                                                                  html.Br(),

                                                                                  dcc.Slider(
                                                                                      id='C-gamma-slider',
                                                                                      min=0,
                                                                                      max=1,
                                                                                      value=1,
                                                                                      step=.05,
                                                                                      marks={0: {'label': '0',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}},
                                                                                             0.25: {'label': '.25',
                                                                                                    'style': {
                                                                                                        'font-size': 'large'}},
                                                                                             .5: {'label': '.5',
                                                                                                  'style': {
                                                                                                      'font-size': 'large'}},
                                                                                             .75: {'label': '.75',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             1: {'label': '1',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}}},
                                                                                      updatemode='mouseup'
                                                                                  ),


                                                                                  html.Div(id='C-saturation-text',
                                                                                           style={'text-align': 'left',
                                                                                                  'font-size': 'x-large'}),

                                                                                  html.Br(),

                                                                                  dcc.Slider(
                                                                                      id='C-saturation-slider',
                                                                                      min=0.1,
                                                                                      max=5,
                                                                                      value=2,
                                                                                      step=.1,
                                                                                      marks={0: {'label': '0',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}},
                                                                                             1: {'label': '1',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}},
                                                                                             1.5: {'label': '1.5',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             2.5: {'label': '2.5',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             3.5: {'label': '3.5',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             5: {'label': '5',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}}},
                                                                                      updatemode='mouseup'),

                                                                                  html.Br(),

                                                                                  html.Div(
                                                                                      className='text-center',
                                                                                      children=[
                                                                                          html.Button(
                                                                                              id='C-Reset',
                                                                                              type='button',
                                                                                              className='btn btn-primary btn-lg',
                                                                                              children=[
                                                                                                  'Reset'])]),
                                                                                  html.Br(),
                                                                                  #
                                                                                  # html.Div(className='text-center',
                                                                                  #          children=[
                                                                                  #              html.Div(
                                                                                  #                  className='btn-group',
                                                                                  #                  role='group',
                                                                                  #                  **{
                                                                                  #                      'aria-label': 'button-group-C'},
                                                                                  #                  children=[
                                                                                  #                      html.Button(
                                                                                  #                          id='C-copy-L',
                                                                                  #                          type='button',
                                                                                  #                          className='btn btn-primary  btn-lg',
                                                                                  #                          children=[
                                                                                  #                              'Copy L']),
                                                                                  #                      html.Button(
                                                                                  #                          id='C-copy-R',
                                                                                  #                          type='button',
                                                                                  #                          className='btn btn-primary  btn-lg',
                                                                                  #                          children=[
                                                                                  #                              'Copy R'])])
                                                                                  #          ])
                                                                              ]),

                                                                     html.Div(className='tab-pane container fade-in',
                                                                              id='R-tab',
                                                                              children=[
                                                                                  html.Div(id="R-stretch-top-text",
                                                                                           style={'text-align': 'left',
                                                                                                  'font-size': 'x-large'}),
                                                                                  html.Br(),
                                                                                  dcc.Slider(
                                                                                      id='R-stretch-top-slider',
                                                                                      min=0,
                                                                                      max=255,
                                                                                      value=0,
                                                                                      step=1,
                                                                                      marks={0: {'label': '0',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}},
                                                                                             63: {'label': '63',
                                                                                                  'style': {
                                                                                                      'font-size': 'large'}},
                                                                                             127: {'label': '127',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             191: {'label': '191',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             255: {'label': '255',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}}},
                                                                                      updatemode='mouseup'
                                                                                  ),


                                                                                  html.Div(id="R-stretch-bot-text",
                                                                                           style={'text-align': 'left',
                                                                                                  'font-size': 'x-large'}),

                                                                                  html.Br(),

                                                                                  dcc.Slider(
                                                                                      id='R-stretch-bot-slider',
                                                                                      min=0,
                                                                                      max=255,
                                                                                      value=255,
                                                                                      step=1,
                                                                                      marks={0: {'label': '0',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}},
                                                                                             63: {'label': '63',
                                                                                                  'style': {
                                                                                                      'font-size': 'large'}},
                                                                                             127: {'label': '127',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             191: {'label': '191',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             255: {'label': '255',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}}},
                                                                                      updatemode='mouseup'
                                                                                  ),

                                                                                  html.Div(id="R-gamma-text",
                                                                                           style={'text-align': 'left',
                                                                                                  'font-size': 'x-large'}),

                                                                                  html.Br(),

                                                                                  dcc.Slider(
                                                                                      id='R-gamma-slider',
                                                                                      min=0,
                                                                                      max=1,
                                                                                      value=1,
                                                                                      step=.05,
                                                                                      marks={0: {'label': '0',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}},
                                                                                             0.25: {'label': '.25',
                                                                                                    'style': {
                                                                                                        'font-size': 'large'}},
                                                                                             .5: {'label': '.5',
                                                                                                  'style': {
                                                                                                      'font-size': 'large'}},
                                                                                             .75: {'label': '.75',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             1: {'label': '1',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}}},
                                                                                      updatemode='mouseup'
                                                                                  ),


                                                                                  html.Div(id='R-saturation-text',
                                                                                           style={'text-align': 'left',
                                                                                                  'font-size': 'x-large'}),

                                                                                  html.Br(),

                                                                                  dcc.Slider(
                                                                                      id='R-saturation-slider',
                                                                                      min=0.1,
                                                                                      max=5,
                                                                                      value=1,
                                                                                      step=.1,
                                                                                      marks={0: {'label': '0',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}},
                                                                                             1: {'label': '1',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}},
                                                                                             1.5: {'label': '1.5',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             2.5: {'label': '2.5',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             3.5: {'label': '3.5',
                                                                                                   'style': {
                                                                                                       'font-size': 'large'}},
                                                                                             5: {'label': '5',
                                                                                                 'style': {
                                                                                                     'font-size': 'large'}}},
                                                                                      updatemode='mouseup'),

                                                                                  html.Br(),

                                                                                  html.Div(
                                                                                      className='text-center',
                                                                                      children=[
                                                                                          html.Button(
                                                                                              id='R-Reset',
                                                                                              type='button',
                                                                                              className='btn btn-primary btn-lg',
                                                                                              children=[
                                                                                                  'Reset'])]),
                                                                                  html.Br(),

                                                                                  # html.Div(
                                                                                  #     className='text-center',
                                                                                  #     children=[
                                                                                  #         html.Div(
                                                                                  #             className='btn-group',
                                                                                  #             role='group',
                                                                                  #             **{
                                                                                  #                 'aria-label': 'button-group-R'},
                                                                                  #             children=[
                                                                                  #                 html.Button(
                                                                                  #                     id='R-copy-L',
                                                                                  #                     type='button',
                                                                                  #                     className='btn btn-primary  btn-lg',
                                                                                  #                     children=[
                                                                                  #                         'Copy L']),
                                                                                  #                 html.Button(
                                                                                  #                     id='R-copy-C',
                                                                                  #                     type='button',
                                                                                  #                     className='btn btn-primary btn-lg',
                                                                                  #                     children=[
                                                                                  #                         'Copy C'])])
                                                                                  #     ])
                                                                              ])
                                                                 ])
                                                    ])
                                       ]),
                              # -----------</IMG-Controls----------

                              # -----------<CME-Controls----------
                              html.Div(className='col-xl-3 card bg-light',
                                       style={'display': 'flex'},
                                       children=[
                                           html.Div(className='card-header text-center font-weight-bold',
                                                    style={'text-align': 'left',
                                                           'font-size': 'x-large'},
                                                    children=['CME-CONTROLS']
                                                    ),
                                           html.Div(className='card-body',
                                                    children=[

                                                        html.Div(id='radial-text', style={'text-align': 'left',
                                                                                          'font-size': 'x-large'}),

                                                        html.Br(),

                                                        html.Div(className="row",
                                                                 children=[
                                                                     html.Button(
                                                                         id='left_rad_btn',
                                                                         style={'margin-right': '20px'},
                                                                         type='button',
                                                                         className='btn btn-primary col-sm-1',
                                                                         n_clicks_timestamp=0,
                                                                         children=[
                                                                             html.Span(className='fas fa-arrow-left')
                                                                         ]),
                                                                     dcc.Slider(
                                                                         id='radial-slider',
                                                                         className="col",
                                                                         min=1,
                                                                         max=45,
                                                                         value=8,
                                                                         step=.1,
                                                                         marks={1: {'label': '1',
                                                                                    'style': {'font-size': 'large'}},
                                                                                8: {'label': '8',
                                                                                    'style': {'font-size': 'large'}},
                                                                                20: {'label': '20',
                                                                                     'style': {'font-size': 'large'}},
                                                                                45: {'label': '45',
                                                                                     'style': {'font-size': 'large'}}},
                                                                         updatemode='mouseup'
                                                                     ),

                                                                     html.Button(
                                                                         id='right_rad_btn',
                                                                         style={'margin-left': '20px'},
                                                                         type='button',
                                                                         className='btn btn-primary col-sm-1',
                                                                         n_clicks_timestamp=0,
                                                                         children=[
                                                                             html.Span(className='fas fa-arrow-right')
                                                                         ]),
                                                                 ]),

                                                        html.Br(),

                                                        html.Div(id="lat-text", style={'text-align': 'left',
                                                                                       'font-size': 'x-large'}),
                                                        html.Br(),
                                                        html.Div(className="row",
                                                                 children=[
                                                                     html.Button(
                                                                         id='left_lat_btn',
                                                                         style={'margin-right': '20px'},
                                                                         type='button',
                                                                         className='btn btn-primary col-sm-1',
                                                                         n_clicks_timestamp=0,
                                                                         children=[
                                                                             html.Span(className='fas fa-arrow-left')
                                                                         ]),
                                                                     dcc.Slider(
                                                                         id='lat-slider',
                                                                         className="col",
                                                                         min=-90,
                                                                         max=90,
                                                                         value=0,
                                                                         step=1,
                                                                         marks={-90: {'label': '-90',
                                                                                      'style': {'font-size': 'large'}},
                                                                                -45: {'label': '-45',
                                                                                      'style': {'font-size': 'large'}},
                                                                                0: {'label': '0',
                                                                                    'style': {'font-size': 'large'}},
                                                                                45: {'label': '45',
                                                                                     'style': {'font-size': 'large'}},
                                                                                90: {'label': '90',
                                                                                     'style': {'font-size': 'large'}}},
                                                                         updatemode='mouseup'
                                                                     ),
                                                                     html.Button(
                                                                         id='right_lat_btn',
                                                                         style={'margin-left': '20px'},
                                                                         type='button',
                                                                         className='btn btn-primary col-sm-1',
                                                                         n_clicks_timestamp=0,
                                                                         children=[
                                                                             html.Span(className='fas fa-arrow-right')
                                                                         ]),
                                                                 ]),


                                                        html.Br(),
                                                        html.Div(id="long-text", style={'text-align': 'left',
                                                                                        'font-size': 'x-large'}),

                                                        html.Br(),

                                                        html.Div(className="row",
                                                                 children=[
                                                                     html.Button(
                                                                         id='left_long_btn',
                                                                         style={'margin-right': '20px'},
                                                                         type='button',
                                                                         className='btn btn-primary col-sm-1',
                                                                         n_clicks_timestamp=0,
                                                                         children=[
                                                                             html.Span(className='fas fa-arrow-left')
                                                                         ]),
                                                                     dcc.Slider(
                                                                         id='long-slider',
                                                                         className="col",
                                                                         min=-180,
                                                                         max=180,
                                                                         value=0,
                                                                         step=1,
                                                                         marks={-180: {'label': '-180',
                                                                                       'style': {'font-size': 'large'}},
                                                                                -90: {'label': '-90',
                                                                                      'style': {'font-size': 'large'}},
                                                                                -45: {'label': '-45',
                                                                                      'style': {'font-size': 'large'}},
                                                                                0: {'label': '0',
                                                                                    'style': {'font-size': 'large'}},
                                                                                45: {'label': '45',
                                                                                     'style': {'font-size': 'large'}},
                                                                                90: {'label': '90',
                                                                                     'style': {'font-size': 'large'}},
                                                                                180: {'label': '180', 'style': {
                                                                                    'font-size': 'large'}}, },
                                                                         updatemode='mouseup'

                                                                     ),
                                                                     html.Button(
                                                                         id='right_long_btn',
                                                                         style={'margin-left': '20px'},
                                                                         type='button',
                                                                         className='btn btn-primary col-sm-1',
                                                                         n_clicks_timestamp=0,
                                                                         children=[
                                                                             html.Span(className='fas fa-arrow-right')
                                                                         ]),
                                                                 ]),

                                                        html.Br(),

                                                        html.Div(id="angular-text", style={'text-align': 'left',
                                                                                           'font-size': 'x-large'}),

                                                        html.Br(),

                                                        html.Div(className="row",
                                                                 children=[
                                                                     html.Button(
                                                                         id='left_ang_btn',
                                                                         style={'margin-right': '20px'},
                                                                         type='button',
                                                                         className='btn btn-primary col-sm-1',
                                                                         n_clicks_timestamp=0,
                                                                         children=[
                                                                             html.Span(className='fas fa-arrow-left')
                                                                         ]),
                                                                     dcc.Slider(
                                                                         id='angular-slider',
                                                                         className="col",
                                                                         min=20,
                                                                         max=140,
                                                                         value=90,
                                                                         step=1,
                                                                         marks={20: {'label': '20',
                                                                                     'style': {'font-size': 'large'}},
                                                                                40: {'label': '40',
                                                                                     'style': {'font-size': 'large'}},
                                                                                90: {'label': '90',
                                                                                     'style': {'font-size': 'large'}},
                                                                                140: {'label': '140',
                                                                                      'style': {'font-size': 'large'}}},
                                                                         updatemode='mouseup'

                                                                     ),
                                                                     html.Button(
                                                                         id='right_ang_btn',
                                                                         style={'margin-left': '20px'},
                                                                         type='button',
                                                                         className='btn btn-primary col-sm-1',
                                                                         n_clicks_timestamp=0,
                                                                         children=[
                                                                             html.Span(className='fas fa-arrow-right')
                                                                         ]),
                                                                 ]),

                                                        html.Br(),


                                                        html.Div(
                                                            className='text-center',
                                                            children=[
                                                                html.Button(
                                                                    id='CME-Reset',
                                                                    type='button',
                                                                    className='btn btn-primary btn-lg',
                                                                    n_clicks_timestamp=0,
                                                                    title="Reset CME control sliders",
                                                                    children=[
                                                                        'Reset'])]),
                                                        html.Br(),
                                                    ])
                                       ]),

                              # -----------</CME-Controls----------

                              # -----------</Velocity Graph----------

                              html.Div(className='col-xl-4 card bg-light',
                                       style={'display': 'flex'},
                                       children=[
                                           html.Div(className='card-header text-center font-weight-bold',
                                                    style={'text-align': 'left',
                                                           'font-size': 'x-large'},
                                                    children=['Velocity Graph']
                                                    ),
                                           html.Div(className='card-body text-center',
                                                    children=[
                                                        dcc.Loading(id="vel_graph_load",
                                                                    type='circle',
                                                                    children=[
                                                                        dcc.Graph(id='velocity-graph',
                                                                                  config={
                                                                                      'modeBarButtonsToRemove': [
                                                                                          'sendDataToCloud', 'zoom2d',
                                                                                          'pan2d',
                                                                                          'select2d',
                                                                                          'lasso2d', 'zoomIn2d',
                                                                                          'zoomOut2d',
                                                                                          'hoverCompareCartesian',
                                                                                          'hoverClosestCartesian',
                                                                                          'toggleSpikelines'],

                                                                                      'displaylogo':False})])
                                                    ])
                                       ]),
                              # -----------</Velocity Graph----------

                              # -----------<Results----------
                              html.Div(className='col-xl-2 card bg-light',
                                       style={'display': 'flex'},
                                       children=[
                                           html.Div(className='card-header text-center font-weight-bold',
                                                    style={'text-align': 'left',
                                                           'font-size': 'x-large'},
                                                    children=['Results']
                                                    ),
                                           html.Div(className='card-body',
                                                    children=[
                                                        dcc.Loading(id="results_load",
                                                                    type='circle',
                                                                    children=[
                                                                        html.Ul(className='list-group',
                                                                                id='result-block',
                                                                                children=[
                                                                                    html.Li(className='list-group-item',
                                                                                            style={'text-align': 'left',
                                                                                                   'font-size': 'x-large'},
                                                                                            id='lat-result'),
                                                                                    html.Li(className='list-group-item',
                                                                                            style={'text-align': 'left',
                                                                                                   'font-size': 'x-large'},
                                                                                            id='long-result'),
                                                                                    html.Li(className='list-group-item',
                                                                                            style={'text-align': 'left',
                                                                                                   'font-size': 'x-large'},
                                                                                            id='half-width-result'),
                                                                                    html.Li(className='list-group-item',
                                                                                            style={'text-align': 'left',
                                                                                                   'font-size': 'x-large'},
                                                                                            id='velocity-result'),
                                                                                    html.Li(className='list-group-item',
                                                                                            style={'text-align': 'left',
                                                                                                   'font-size': 'x-large'},
                                                                                            id='time-result')
                                                                                ])]),
                                                        html.Div(
                                                            className='text-center',
                                                            children=[
                                                                html.Br(),
                                                                html.Div(className='btn-group',
                                                                         role='group',
                                                                         **{
                                                                             'aria-label': 'button-group-results'},
                                                                         children=[
                                                                             html.Button(
                                                                                 id='calculate-btn',
                                                                                 style={'margin-right': '20px'},
                                                                                 type='button',
                                                                                 n_clicks_timestamp=0,
                                                                                 className='btn btn-primary btn-lg',
                                                                                 children=['Calculate']),

                                                                             html.Button(
                                                                                 id='reset-all-btn',
                                                                                 style={'margin-right': '20px'},
                                                                                 type='button',
                                                                                 className='btn btn-primary btn-lg',
                                                                                 n_clicks_timestamp=0,
                                                                                 title="resets all of the previous matches and the velocity graph",
                                                                                 children=['Reset Matches']),
                                                                         ]),

                                                                html.Button(
                                                                    id='export-btn',
                                                                    type='button',
                                                                    style={'display': 'None'},
                                                                    className='btn btn-primary btn-lg',
                                                                    children=[html.A(id='my-link',
                                                                                     href='',
                                                                                     style={'color': 'white'},
                                                                                     children=['Export Data'])]),
                                                            ])

                                                    ])

                                       ])
                              # -----------</Results>----------
                          ]),
                 # --------------<3D Visuals>-------------
                 # html.Div(className='row',
                 #          children=[
                 #              html.Div(className='card col-xl-12 bg-dark',
                 #                       children=[
                 #                           html.Div(className='card-header text-center text-white font-weight-bold',
                 #                                    style={'text-align': 'left',
                 #                                           'font-size': 'x-large'},
                 #                                    children=['3D Visuals']),
                 #                           html.Div(className='card-body',
                 #                                    children=[dcc.Graph(id='lemniscate-graph',
                 #                                                        config={
                 #                                                            'displayModeBar': False}),
                 #                                              ])
                 #
                 #                       ])
                 #          ]),
                 # --------------</3D Visuals>-------------

                 # hidden divs for image data and header transport accross methods
                 html.Div(id='stereo-a-hidden',
                          style={'display': 'none'}),
                 html.Div(id='soho-c3-hidden',
                          style={'display': 'none'}),
                 html.Div(id='stereo-b-hidden',
                          style={'display': 'none'}),
                 html.Div(id='full-matches-hidden',
                          style={'display': 'none'},
                          children=[]),
                 html.Div(id='instrument-matches-hidden',
                          style={'display': 'none'},
                          children=[]),
                 html.Div(id='radial-velocity-hidden',
                          style={'display': 'none'},
                          children=[]),
                 html.Div(id='time-hidden',
                          style={'display': 'none'},
                          children=[]),
             ]),
    # --------------<Footer>-------------
    html.Footer(className='footer bg-dark text-white',
                children=[html.Div(className='footer-copyright text-center',
                                   children=[html.A(className='text-white',
                                                    href='mailto:ccmc-iswa-support@lists.nasa.gov',
                                                    children='Curator: Juan A. Figueroa '),
                                             '| ',
                                             html.A(className='text-white',
                                                    href='mailto:ccmc-iswa-support@lists.nasa.gov',
                                                    children='NASA Official: Dr. Masha Kuznetsova '),
                                             '| ',
                                             html.A(className='text-white',
                                                    href='https://www.nasa.gov/about/highlights/HP_Privacy.html',
                                                    children=['Privacy and Security Notice ']),
                                             '| ',
                                             html.A(className='text-white',
                                                    href="https://icons8.com",
                                                    children=['Icons8'])
                                             ])
                          ])
    # --------------</Footer>-------------
])


# --------------------------------------------------------------</html section>----------------------------------


# defines function for layout extraction of lemniscate figure
def get_lem_layout(x_lim, y_lim, z_lim):
    return dict(
        scene=dict(
            xaxis=dict(
                gridcolor='rgba(0, 0, 0,0)',
                zerolinecolor='rgba(0, 0, 0, 0)',
                showbackground=True,
                backgroundcolor='rgba(0, 0, 0,0)',
                range=x_lim,
                showticklabels=False
            ),
            yaxis=dict(
                gridcolor='rgba(0, 0, 0, 0)',
                zerolinecolor='rgba(0, 0, 0, 0)',
                showbackground=True,
                backgroundcolor='rgba(0, 0, 0, 0)',
                range=y_lim,
                showticklabels=False
            ),
            zaxis=dict(
                gridcolor='rgba(0, 0, 0, 0)',
                zerolinecolor='rgba(0, 0, 0, 0)',
                showbackground=True,
                backgroundcolor='rgba(0, 0, 0, 0)',
                range=z_lim,
                showticklabels=False
            ),
            aspectratio={
                'x': ((x_lim[1] - x_lim[0]) / 100),
                'y': ((y_lim[1] - y_lim[0]) / 100),
                'z': ((z_lim[1] - z_lim[0]) / 100)}

        ),
        uirevision='true',
        paper_bgcolor='transparent',

    )


# defines function for layout extraction of lemniscate figure
def get_2d_lem_layout(x_lim, y_lim):
    return dict(
        xaxis=dict(range=x_lim,
                   autorange=False,
                   showticklabels=False,
                   showbackground=True,
                   fixedrange=True),
        yaxis=dict(range=y_lim,
                   autorange=False,
                   showticklabels=False,
                   showbackground=True,
                   fixedrange=True),
        margin=dict(
            l=0,
            r=0,
            b=0,
            t=0,
        ),
        hovermode=False,
        showlegend=False,
        height=600,
        width=600,
        # autosize=True
    )


# defines function for layout extraction of an empty  figure
def get_empty_layout(x_lim, y_lim):
    return dict(
        xaxis=dict(range=x_lim,
                   gridcolor='rgba(0, 0, 0, 0)',
                   zerolinecolor='rgba(0, 0, 0, 0)',
                   backgroundcolor='rgba(0, 0, 0, 0)',
                   autorange=False,
                   showticklabels=False,
                   showbackground=True,
                   fixedrange=True),
        yaxis=dict(range=y_lim,
                   gridcolor='rgba(0, 0, 0,0)',
                   zerolinecolor='rgba(0, 0, 0, 0)',
                   backgroundcolor='rgba(0, 0, 0,0)',
                   autorange=False,
                   showticklabels=False,
                   showbackground=True,
                   fixedrange=True),
        paper_bgcolor='transparent',
        plot_bgcolor='transparent',
        hovermode=False,
        showlegend=False)


# defines function for layout extraction of velocity graph
def get_velocity_layout():
    return go.Layout(
        xaxis=dict(title='Time',
                   tickfont=dict(size=14),
                   titlefont=dict(size=16)),
        yaxis=dict(title='Radial Distance (Solar Radius)',
                   tickfont=dict(size=14),
                   titlefont=dict(size=16))
    )


# gets the layout information of the lemniscate
layout_lem = get_lem_layout([-GRID_HALF_WIDTH, GRID_HALF_WIDTH], [-GRID_HALF_WIDTH, GRID_HALF_WIDTH],
                            [-GRID_HALF_WIDTH, GRID_HALF_WIDTH])

# gets the layout information of the 2D lemniscate
layout_two_d_lemniscate = get_2d_lem_layout([-GRID_HALF_WIDTH, GRID_HALF_WIDTH], [-GRID_HALF_WIDTH, GRID_HALF_WIDTH])

# gets the layout information of the velocity graph
layout_velocity = get_velocity_layout()

# define empty layout information for 2d lemniscates
empty_layout = get_empty_layout([-GRID_HALF_WIDTH, GRID_HALF_WIDTH], [-GRID_HALF_WIDTH, GRID_HALF_WIDTH])


# ----------<download btn>--------------------
@app.callback(
    dcd.Output('btn-load-images', 'disabled'),
    [dcd.Input('full-matches-hidden', 'children'),
     dcd.Input('date-time', 'value')],
    [dcd.State('date-time', 'pattern')]
)
def load_btn_disable(matches_json, time_value, pattern):

    matches = json.loads(matches_json)

    if len(matches['matches']) == 0 and re.match(pattern, time_value) is not None:
        return False
    else:
        return True


# ----------</download btn>--------------------

# ---------<IMG-Match-Callback section>-------

# callback for long slider disable
@app.callback(
    [dcd.Output('long-slider', 'disabled'),
     dcd.Output('angular-slider', 'disabled'),
     dcd.Output('lat-slider', 'disabled')],
    [dcd.Input('full-matches-hidden', 'children')])
def img_slider_disable(matches_json):
    matches = json.loads(matches_json)

    if len(matches['matches']) == 0:
        return False, False, False
    else:
        return True, True, True


# ---------</IMG-Match-Callback section>-------

# ---------<IMG-Controls-Callback section>-------

# ---------<L-tab-callback section>-------


# callback for L-stretch-bot value text
@app.callback(
    dcd.Output('L-stretch-bot-text', 'children'),
    [dcd.Input('L-stretch-bot-slider', 'value')]
)
def l_stretch_bot_text_update(stretch):
    return 'Stretch Bottom: {}'.format(stretch)


# callback for L-stretch-bot value reset
@app.callback(
    dcd.Output('L-stretch-bot-slider', 'value'),
    [dcd.Input('L-Reset', 'n_clicks')]
)
def l_stretch_bot_reset(n_clicks):
    return 255


# callback for L-stretch-top value text
@app.callback(
    dcd.Output('L-stretch-top-text', 'children'),
    [dcd.Input('L-stretch-top-slider', 'value')]
)
def l_stretch_top_text_update(stretch):
    return 'Stretch Top: {}'.format(stretch)


# callback for L-stretch-top value reset
@app.callback(
    dcd.Output('L-stretch-top-slider', 'value'),
    [dcd.Input('L-Reset', 'n_clicks')]
)
def l_stretch_top_reset(n_clicks):
    return 0


# callback for L-gamma-text value text
@app.callback(
    dcd.Output('L-gamma-text', 'children'),
    [dcd.Input('L-gamma-slider', 'value')]
)
def l_gamma_text_update(stretch):
    return 'Gamma: {}'.format(stretch)


# callback for L-gamma value reset
@app.callback(
    dcd.Output('L-gamma-slider', 'value'),
    [dcd.Input('L-Reset', 'n_clicks')]
)
def l_gamma_reset(n_clicks):
    return 1


# callback for L-saturation-text value text
@app.callback(
    dcd.Output('L-saturation-text', 'children'),
    [dcd.Input('L-saturation-slider', 'value')]
)
def l_saturation_text_update(stretch):
    return 'Saturation: {}'.format(stretch)


# callback for L-saturation value reset
@app.callback(
    dcd.Output('L-saturation-slider', 'value'),
    [dcd.Input('L-Reset', 'n_clicks')]
)
def l_saturation_reset(n_clicks):
    return 1


# ---------</L-tab-callback section>-------

# ---------<C-tab-callback section>-------


# callback for C-stretch-bot value text
@app.callback(
    dcd.Output('C-stretch-bot-text', 'children'),
    [dcd.Input('C-stretch-bot-slider', 'value')]
)
def c_stretch_bot_text_update(stretch):
    return 'Stretch Bottom: {}'.format(stretch)


# callback for C-stretch-bot value reset
@app.callback(
    dcd.Output('C-stretch-bot-slider', 'value'),
    [dcd.Input('C-Reset', 'n_clicks')]
)
def c_stretch_bot_reset(n_clicks):
    return 255


# callback for C-stretch-top value text
@app.callback(
    dcd.Output('C-stretch-top-text', 'children'),
    [dcd.Input('C-stretch-top-slider', 'value')]
)
def c_stretch_top_text_update(stretch):
    return 'Stretch Top: {}'.format(stretch)


# callback for C-stretch-top value reset
@app.callback(
    dcd.Output('C-stretch-top-slider', 'value'),
    [dcd.Input('C-Reset', 'n_clicks')]
)
def c_stretch_top_reset(n_clicks):
    return 0


# callback for C-gamma-text value text
@app.callback(
    dcd.Output('C-gamma-text', 'children'),
    [dcd.Input('C-gamma-slider', 'value')]
)
def c_gamma_text_update(stretch):
    return 'Gamma: {}'.format(stretch)


# callback for C-gamma value reset
@app.callback(
    dcd.Output('C-gamma-slider', 'value'),
    [dcd.Input('C-Reset', 'n_clicks')]
)
def c_gamma_reset(n_clicks):
    return 1


# callback for C-saturation-text value text
@app.callback(
    dcd.Output('C-saturation-text', 'children'),
    [dcd.Input('C-saturation-slider', 'value')]
)
def c_saturation_text_update(stretch):
    return 'Saturation: {}'.format(stretch)


# callback for C-saturation value reset
@app.callback(
    dcd.Output('C-saturation-slider', 'value'),
    [dcd.Input('C-Reset', 'n_clicks')]
)
def c_saturation_reset(n_clicks):
    return 3


# ---------</C-tab-callback section>-------

# ---------<R-tab-callback section>-------


# callback for R-stretch-bot value text
@app.callback(
    dcd.Output('R-stretch-bot-text', 'children'),
    [dcd.Input('R-stretch-bot-slider', 'value')]
)
def r_stretch_bot_text_update(stretch):
    return 'Stretch Bottom: {}'.format(stretch)


# callback for R-stretch-bot value reset
@app.callback(
    dcd.Output('R-stretch-bot-slider', 'value'),
    [dcd.Input('R-Reset', 'n_clicks')]
)
def r_stretch_bot_reset(n_clicks):
    return 255


# callback for R-stretch-top value text
@app.callback(
    dcd.Output('R-stretch-top-text', 'children'),
    [dcd.Input('R-stretch-top-slider', 'value')]
)
def r_stretch_top_text_update(stretch):
    return 'Stretch Top: {}'.format(stretch)


# callback for R-stretch-top value reset
@app.callback(
    dcd.Output('R-stretch-top-slider', 'value'),
    [dcd.Input('R-Reset', 'n_clicks')]
)
def r_stretch_top_reset(n_clicks):
    return 0


# callback for R-gamma-text value text
@app.callback(
    dcd.Output('R-gamma-text', 'children'),
    [dcd.Input('R-gamma-slider', 'value')]
)
def r_gamma_text_update(stretch):
    return 'Gamma: {}'.format(stretch)


# callback for R-gamma value reset
@app.callback(
    dcd.Output('R-gamma-slider', 'value'),
    [dcd.Input('R-Reset', 'n_clicks')]
)
def r_gamma_reset(n_clicks):
    return 1


# callback for R-saturation-text value text
@app.callback(
    dcd.Output('R-saturation-text', 'children'),
    [dcd.Input('R-saturation-slider', 'value')]
)
def r_saturation_text_update(stretch):
    return 'Saturation: {}'.format(stretch)


# callback for R-saturation value reset
@app.callback(
    dcd.Output('R-saturation-slider', 'value'),
    [dcd.Input('R-Reset', 'n_clicks')]
)
def r_saturation_reset(n_clicks):
    return 1


# ---------</R-tab-callback section>-------

# ---------</IMG-Controls-Callback section>-------

# ---------<CME-Controls-Callback section>-------


# callback for radial value text
@app.callback(
    dcd.Output('radial-text', 'children'),
    [dcd.Input('radial-slider', 'value')]
)
def rad_text_update(radial_v):
    return 'Radial Distance: {:.1f}'.format(radial_v)


# callback for radial value reset
@app.callback(
    dcd.Output('radial-slider', 'value'),
    [dcd.Input('CME-Reset', 'n_clicks_timestamp'),
     dcd.Input('left_rad_btn', 'n_clicks_timestamp'),
     dcd.Input('right_rad_btn', 'n_clicks_timestamp')],
    [dcd.State('radial-slider', 'value')]
)
def radial_reset(reset, left_btn, right_btn, slider_val):
    if right_btn > left_btn and right_btn > reset:
        return slider_val + .1
    if left_btn > reset and left_btn > right_btn:
        return slider_val - .1
    else:
        return 8


# disables left move button l if there are no images
@app.callback(
    dcd.Output('left_rad_btn', 'disabled'),
    [dcd.Input('radial-slider', 'disabled'),
     dcd.Input('radial-slider', 'value')],
    [dcd.State('radial-slider', 'min')]
)
def left_radial_disabled(disabled, value, min):
    if disabled or value == min:
        return True
    else:
        return False


# disables right radial button
@app.callback(
    dcd.Output('right_rad_btn', 'disabled'),
    [dcd.Input('radial-slider', 'disabled'),
     dcd.Input('radial-slider', 'value')],
    [dcd.State('radial-slider', 'max')]
)
def right_radial_disabled(disabled, value, max):
    if disabled or value == max:
        return True
    else:
        return False


# callback for angular value text
@app.callback(
    dcd.Output('angular-text', 'children'),
    [dcd.Input('angular-slider', 'value')]
)
def angular_text_update(angular_v):
    return 'Angular Width: {:.1f}'.format(angular_v)


# callback for angular value reset
@app.callback(
    dcd.Output('angular-slider', 'value'),
    [dcd.Input('CME-Reset', 'n_clicks_timestamp'),
     dcd.Input('left_ang_btn', 'n_clicks_timestamp'),
     dcd.Input('right_ang_btn', 'n_clicks_timestamp')],
    [dcd.State('angular-slider', 'value')]
)
def angular_reset(reset, left_btn, right_btn, slider_val):
    if right_btn > left_btn and right_btn > reset:
        return slider_val + 1
    if left_btn > reset and left_btn > right_btn:
        return slider_val - 1
    else:
        return 90


# disables left angular button
@app.callback(
    dcd.Output('left_ang_btn', 'disabled'),
    [dcd.Input('angular-slider', 'disabled'),
     dcd.Input('angular-slider', 'value')],
    [dcd.State('angular-slider', 'min')]
)
def left_angular_disabled(disabled, value, min):
    if disabled or value == min:
        return True
    else:
        return False


# disables right angular button
@app.callback(
    dcd.Output('right_ang_btn', 'disabled'),
    [dcd.Input('angular-slider', 'disabled'),
     dcd.Input('angular-slider', 'value')],
    [dcd.State('angular-slider', 'max')]
)
def left_angular_disabled(disabled, value, max):
    if disabled or value == max:
        return True
    else:
        return False


# callback for latitude value text
@app.callback(
    dcd.Output('lat-text', 'children'),
    [dcd.Input('lat-slider', 'value')]
)
def lat_text_update(lat):
    return 'Latitude: {:.1f}'.format(lat)


# callback for latitude value reset
@app.callback(
    dcd.Output('lat-slider', 'value'),
    [dcd.Input('CME-Reset', 'n_clicks_timestamp'),
     dcd.Input('left_lat_btn', 'n_clicks_timestamp'),
     dcd.Input('right_lat_btn', 'n_clicks_timestamp')],
    [dcd.State('lat-slider', 'value')]
)
def lat_reset(reset, left_btn, right_btn, slider_val):
    if right_btn > left_btn and right_btn > reset:
        return slider_val + 1
    if left_btn > reset and left_btn > right_btn:
        return slider_val - 1
    else:
        return 0


# disables left angular button
@app.callback(
    dcd.Output('left_lat_btn', 'disabled'),
    [dcd.Input('lat-slider', 'disabled'),
     dcd.Input('lat-slider', 'value')],
    [dcd.State('lat-slider', 'min')]
)
def left_lat_disabled(disabled, value, min):
    if disabled or value == min:
        return True
    else:
        return False


# disables right angular button
@app.callback(
    dcd.Output('right_lat_btn', 'disabled'),
    [dcd.Input('lat-slider', 'disabled'),
     dcd.Input('lat-slider', 'value')],
    [dcd.State('lat-slider', 'max')]
)
def right_lat_disabled(disabled, value, max):
    if disabled or value == max:
        return True
    else:
        return False


# callback for longitude value text
@app.callback(
    dcd.Output('long-text', 'children'),
    [dcd.Input('long-slider', 'value')]
)
def rad_text_update(long):
    return 'Longitude: {:.1f}'.format(long)


# callback for longitude value reset
@app.callback(
    dcd.Output('long-slider', 'value'),
    [dcd.Input('CME-Reset', 'n_clicks_timestamp'),
     dcd.Input('left_long_btn', 'n_clicks_timestamp'),
     dcd.Input('right_long_btn', 'n_clicks_timestamp')],
    [dcd.State('long-slider', 'value')]
)
def long_reset(reset, left_btn, right_btn, slider_val):
    if right_btn > left_btn and right_btn > reset:
        return slider_val + 1
    if left_btn > reset and left_btn > right_btn:
        return slider_val - 1
    else:
        return 0


# disables left long button
@app.callback(
    dcd.Output('left_long_btn', 'disabled'),
    [dcd.Input('long-slider', 'disabled'),
     dcd.Input('long-slider', 'value')],
    [dcd.State('long-slider', 'min')]
)
def left_long_disabled(disabled, value, min):
    if disabled or value == min:
        return True
    else:
        return False


# disables right long button
@app.callback(
    dcd.Output('right_long_btn', 'disabled'),
    [dcd.Input('long-slider', 'disabled'),
     dcd.Input('long-slider', 'value')],
    [dcd.State('long-slider', 'max')]
)
def right_long_disabled(disabled, value, max):
    if disabled or value == max:
        return True
    else:
        return False


# callback for reset btn disabled
@app.callback(
    dcd.Output('CME-Reset', 'disabled'),
    [dcd.Input('full-matches-hidden', 'children')]
)
def reset_disabled(matches_json):

    matches = json.loads(matches_json)

    if len(matches['matches']) == 0:
        return False
    else:
        return True


# ---------</CME-Controls-Callback section>-------

# ---------<3D-Plot-Callback section>-------

#
# # callback for lemniscate plot
# @app.callback(
#     dcd.Output('lemniscate-graph', 'figure'),
#     [dcd.Input('radial-slider', 'value'),
#      dcd.Input('angular-slider', 'value'),
#      dcd.Input('long-slider', 'value'),
#      dcd.Input('lat-slider', 'value')],
#     [dcd.State('lemniscate-graph', 'relayoutData')])
# # function for graph update when slider is changed
# def lemniscate_update(radial, angular, long, lat, relayoutData):
#     global n
#
#     V = swpc_utils.plot_update(radial, angular, long, lat)
#
#     surface_mod = go.Surface(x=V[0], y=V[1], z=V[2], colorscale='Reds', showscale=False)
#
#     return dict(data=[surface_mod], layout=layout_lem)
#

# ---------</3D-Plot-Callback section>-------


# ---------<2D-L-Plot-Callback section>-------
# modifies right slider max property
@app.callback(
    dcd.Output('l-image-slider', 'max'),
    [dcd.Input('stereo-b-hidden', 'children')]
)
def l_slider_max_update(img_arr):
    return len(np.array(pd.read_json(img_arr))) - 1


# disables slider if there are no images
@app.callback(
    dcd.Output('l-image-slider', 'disabled'),
    [dcd.Input('stereo-b-hidden', 'children')]
)
def l_slider_disable(img_arr):
    # extract jsonified image array
    image_dir = np.array(pd.read_json(img_arr)).tolist()

    if len(image_dir) <= 1:
        return True
    else:
        return False


# disables match button if there are no images
@app.callback(
    dcd.Output('l-btn-match', 'disabled'),
    [dcd.Input('l-btn-match', 'className'),
     dcd.Input('full-matches-hidden', 'children')]
)
def l_match_btn_disable(className, match_list):

    matches = json.loads(match_list)

    if any(d["instrument"] == 'Stereo-B' for d in matches["matches"]):

        if className == 'btn btn-success btn-lg':
            return True
        else:
            return False

    else:
        return False


# disables time export button if there are no images
@app.callback(
    dcd.Output('time_import_btn_l', 'disabled'),
    [dcd.Input('l-image-slider', 'disabled')],
)
def l_time_export_btn_disable(disabled):
    if disabled:
        return True
    else:
        return False


# disables dropdown if there are no images
@app.callback(
    dcd.Output('l-image-dropdown', 'disabled'),
    [dcd.Input('l-image-slider', 'disabled')],
)
def l_dropdown_disable(disabled):
    if disabled:
        return True
    else:
        return False


# disables left move button r if there are no images
@app.callback(
    dcd.Output('left_move_btn_l', 'disabled'),
    [dcd.Input('l-image-slider', 'disabled'),
     dcd.Input('l-image-slider', 'value')]
)
def left_btn_l_disabled(disabled, value):
    if disabled or value == 1:
        return True
    else:
        return False


# disables left move button l if there are no images
@app.callback(
    dcd.Output('right_move_btn_l', 'disabled'),
    [dcd.Input('l-image-slider', 'disabled'),
     dcd.Input('l-image-slider', 'value')],
    [dcd.State('l-image-slider', 'max')]
)
def left_btn_r_disabled(disabled, value, max):
    if disabled or (value == max and value != 1):
        return True
    else:
        return False


@app.callback(
    dcd.Output('STEREO-B', 'style'),
    [dcd.Input('l-image-slider', 'disabled')]
)
def show_hide_stereo_b(disabled):
    if disabled:
        return {'display': 'none'}
    else:
        return {'display': 'flex'}


# resets the image slider everytime a new image is loaded
@app.callback(
    dcd.Output('l-image-slider', 'value'),
    [dcd.Input('btn-load-images', 'n_clicks_timestamp'),
     dcd.Input('right_move_btn_l', 'n_clicks_timestamp'),
     dcd.Input('left_move_btn_l', 'n_clicks_timestamp'),
     dcd.Input('time_import_btn_r', 'n_clicks_timestamp'),
     dcd.Input('time_import_btn_c', 'n_clicks_timestamp')],
    [dcd.State('l-image-slider', 'value'),
     dcd.State('stereo-b-hidden', 'children'),
     dcd.State('stereo-a-hidden', 'children'),
     dcd.State('soho-c3-hidden', 'children'),
     dcd.State('r-image-slider', 'value'),
     dcd.State('c-image-slider', 'value')]
)
def l_slider_btn_move(load_btn, right_btn, left_btn, time_import_btn_r, time_import_btn_c, slider_val, stereo_b_json,
                      stereo_a_json, soho_json, r_slider, c_slider):
    if int(load_btn) > int(right_btn) and int(load_btn) > int(left_btn) and int(load_btn) > int(
            time_import_btn_r) and int(load_btn) > int(time_import_btn_c):
        return 1

    elif int(left_btn) > int(load_btn) and int(left_btn) > int(right_btn) and int(left_btn) > int(
            time_import_btn_r) and int(left_btn) > int(time_import_btn_c):
        return slider_val - 1

    elif int(right_btn) > int(load_btn) and int(right_btn) > int(left_btn) and int(right_btn) > int(
            time_import_btn_r) and int(right_btn) > int(time_import_btn_c):
        return slider_val + 1

    elif int(time_import_btn_r) > int(load_btn) and int(time_import_btn_r) > int(left_btn) and int(
            time_import_btn_r) > int(right_btn) and int(time_import_btn_r) > int(time_import_btn_c):
        try:
            stereo_a_dir = np.array(pd.read_json(stereo_a_json)).tolist()

            import_val = stereo_a_dir[r_slider][1].split('/')[-1].split('_')
            import_val = datetime(int(import_val[0][0:4]), int(import_val[0][4:6]), int(import_val[0][6:8]),
                                  int(import_val[1][0:2]), int(import_val[1][2:4]), int(import_val[1][4:6]))

            stereo_b_dir = np.array(pd.read_json(stereo_b_json)).tolist()

            for i in range(0, len(stereo_b_dir)):
                stereo_b_dir[i] = stereo_b_dir[i][1].split('/')[-1].replace('.fts', '').split('_')
                stereo_b_dir[i] = datetime(int(stereo_b_dir[i][0][0:4]), int(stereo_b_dir[i][0][4:6]),
                                           int(stereo_b_dir[i][0][6:8]), int(stereo_b_dir[i][1][0:2]),
                                           int(stereo_b_dir[i][1][2:4]), int(stereo_b_dir[i][1][4:6]))

            return min(range(len(stereo_b_dir)), key=lambda i: abs(stereo_b_dir[i] - import_val))

        except (TypeError, IndexError, AttributeError) as e:

            return slider_val

    elif int(time_import_btn_c) > int(load_btn) and int(time_import_btn_c) > int(left_btn) and int(
            time_import_btn_c) > int(right_btn) and int(time_import_btn_c) > int(time_import_btn_r):
        try:
            soho_dir = np.array(pd.read_json(soho_json)).tolist()

            import_val = soho_dir[c_slider][1].split('/')[-1].replace('.fts', '').split('_')
            import_val = datetime(int(import_val[0][0:4]), int(import_val[0][4:6]), int(import_val[0][6:8]),
                                  int(import_val[1][0:2]), int(import_val[1][2:4]), int(import_val[1][4:6]))

            stereo_b_dir = np.array(pd.read_json(stereo_b_json)).tolist()

            for i in range(0, len(stereo_b_dir)):
                stereo_b_dir[i] = stereo_b_dir[i][1].split('/')[-1].split('_')
                stereo_b_dir[i] = datetime(int(stereo_b_dir[i][0][0:4]), int(stereo_b_dir[i][0][4:6]),
                                           int(stereo_b_dir[i][0][6:8]), int(stereo_b_dir[i][1][0:2]),
                                           int(stereo_b_dir[i][1][2:4]), int(stereo_b_dir[i][1][4:6]))

            return min(range(len(stereo_b_dir)), key=lambda i: abs(stereo_b_dir[i] - import_val))

        except (TypeError, IndexError, AttributeError) as e:

            return slider_val

    else:
        return 1


# loads header data to intermediate hidden div for later extraction in each of the callbacks
@app.callback(dcd.Output('stereo-b-hidden', 'children'),
              [dcd.Input('btn-load-images', 'n_clicks'),
               dcd.Input('l-image-dropdown', 'value')],
              [dcd.State('date-picker', 'date'),
               dcd.State('date-time', 'value'),
               dcd.State('end-time', 'value')])
def stereo_b_img_arr_load(n_clicks, type_im, date, start_time, end_time):
    # test directory link to stereo B

    image_dir = swpc_utils.extract_images(datetime.strptime(date, '%Y-%m-%d'), start_time, end_time, 1)

    if len(image_dir) != 0:

        return json.dumps(image_dir.tolist())

    else:
        return json.dumps(np.empty(1).tolist())


# callback for image  value text
@app.callback(
    dcd.Output('l-image-text', 'children'),
    [dcd.Input('2d-l-lemniscate', 'figure'),
     dcd.Input('l-image-slider', 'value')],
    [dcd.State('stereo-b-hidden', 'children')]
)
def l_image_text_update(trigger, slider_val, image_json):
    try:
        image_dir = np.array(pd.read_json(image_json)).tolist()

        date = datetime.strptime(str(image_dir[slider_val][0]), '%Y-%m-%d %H:%M:%S')

        return date.strftime('%Y-%m-%dT%H:%M:%SZ')

    except (TypeError, IndexError) as e:

        return ''


# callback for 2d-l-lemniscate plot
@app.callback(
    dcd.Output('2d-l-lemniscate', 'figure'),
    [dcd.Input('radial-slider', 'value'),
     dcd.Input('angular-slider', 'value'),
     dcd.Input('long-slider', 'value'),
     dcd.Input('lat-slider', 'value'),
     dcd.Input('L-stretch-bot-slider', 'value'),
     dcd.Input('L-stretch-top-slider', 'value'),
     dcd.Input('L-gamma-slider', 'value'),
     dcd.Input('L-saturation-slider', 'value'),
     dcd.Input('stereo-b-hidden', 'children'),
     dcd.Input('l-image-slider', 'value')
     ])
# function for graph update when sliders are changed
def left_lemniscate_update(radial, angular, long, lat, stretch_bot, stretch_top, gamma, saturation, image_json,
                           slider_val):
    global n

    # extract jsonified image array
    image_dir = np.array(pd.read_json(image_json)).tolist()

    if len(image_dir) != 1:


        observer, current_map, previous_map = swpc_utils.new_map(image_dir[slider_val][1], image_dir[slider_val - 1][1],
                                                                 saturation)

        hull = swpc_utils.return_plot(observer, -1, radial, angular, long, lat)

        image_data = swpc_utils.return_image(observer.data, gamma, stretch_top, stretch_bot)

        trace = go.Scatter(x=hull[0, :], y=hull[1, :], mode='lines',
                           line=dict(color='rgb(255, 255, 0)'))
        trace1 = go.Scatter(x=[hull[0, 0], hull[0, - 1]],
                            y=[hull[1, 0], hull[1, - 1]], mode='lines',
                            line=dict(color='rgb(255, 255, 0)'))

        trace2 = go.Heatmap(z=image_data,
                            x=np.linspace(-GRID_HALF_WIDTH, GRID_HALF_WIDTH, 256),
                            y=np.linspace(-GRID_HALF_WIDTH, GRID_HALF_WIDTH, 256),
                            colorscale='Greys',
                            showscale=False,
                            )
        return dict(data=[trace, trace1, trace2], layout=layout_two_d_lemniscate)

    else:

        return dict(layout=empty_layout)


# ---------</2D-L-Plot-Callback section>-------


# ---------<2D-C-Plot-Callback section>-------

# modifies right slider max property
@app.callback(
    dcd.Output('c-image-slider', 'max'),
    [dcd.Input('soho-c3-hidden', 'children')]
)
def c_slider_max_update(img_arr):
    return len(np.array(pd.read_json(img_arr))) - 1


# disables slider if there are no images
@app.callback(
    dcd.Output('c-image-slider', 'disabled'),
    [dcd.Input('soho-c3-hidden', 'children')]
)
def c_slider_disable(img_arr):
    # extract jsonified image array
    image_dir = np.array(pd.read_json(img_arr)).tolist()

    if len(image_dir) <= 1:
        return True
    else:
        return False


# disables match button if there are no images
@app.callback(
    dcd.Output('c-btn-match', 'disabled'),
    [dcd.Input('c-btn-match', 'className'),
     dcd.Input('full-matches-hidden', 'children')]
)
def c_match_btn_disable(className, match_list):

    matches = json.loads(match_list)

    if any(d["instrument"] == 'SOHO C3' for d in matches["matches"]):

        if className == 'btn btn-success btn-lg':
            return True
        else:
            return False

    else:
        return False


# disables time export button if there are no images
@app.callback(
    dcd.Output('time_import_btn_c', 'disabled'),
    [dcd.Input('c-image-slider', 'disabled')],
)
def c_time_export_btn_disable(disabled):
    if disabled:
        return True
    else:
        return False


# disables dropdown if there are no images
@app.callback(
    dcd.Output('c-image-dropdown', 'disabled'),
    [dcd.Input('c-image-slider', 'disabled')],
)
def c_dropdown_disable(disabled):
    if disabled:
        return True
    else:
        return False


# disables center move button r if there are no images
@app.callback(
    dcd.Output('left_move_btn_c', 'disabled'),
    [dcd.Input('c-image-slider', 'disabled'),
     dcd.Input('c-image-slider', 'value')]
)
def center_btn_l_disabled(disabled, value):
    if disabled or value == 1:
        return True
    else:
        return False


# disables center move button l if there are no images
@app.callback(
    dcd.Output('right_move_btn_c', 'disabled'),
    [dcd.Input('c-image-slider', 'disabled'),
     dcd.Input('c-image-slider', 'value')],
    [dcd.State('c-image-slider', 'max')]
)
def center_btn_r_disabled(disabled, value, max):
    if disabled or (value == max and value != 1):
        return True
    else:
        return False


@app.callback(
    dcd.Output('SOHO', 'style'),
    [dcd.Input('c-image-slider', 'disabled')]
)
def show_hide_soho(disabled):
    if disabled:
        return {'display': 'none'}
    else:
        return {'display': 'flex'}


# resets the image slider eveytime a new image is loaded
@app.callback(
    dcd.Output('c-image-slider', 'value'),
    [dcd.Input('btn-load-images', 'n_clicks_timestamp'),
     dcd.Input('right_move_btn_c', 'n_clicks_timestamp'),
     dcd.Input('left_move_btn_c', 'n_clicks_timestamp'),
     dcd.Input('time_import_btn_r', 'n_clicks_timestamp'),
     dcd.Input('time_import_btn_l', 'n_clicks_timestamp')],
    [dcd.State('c-image-slider', 'value'),
     dcd.State('l-image-slider', 'value'),
     dcd.State('r-image-slider', 'value'),
     dcd.State('soho-c3-hidden', 'children'),
     dcd.State('stereo-a-hidden', 'children'),
     dcd.State('stereo-b-hidden', 'children')]
)
def c_slider_btn_move(load_btn, right_btn, left_btn, time_import_btn_r, time_import_btn_l, slider_val, l_slider,
                      r_slider, soho_json, stereo_a_json, stereo_b_json):
    if int(load_btn) > int(right_btn) and int(load_btn) > int(left_btn) and int(load_btn) > int(
            time_import_btn_r) and int(load_btn) > int(time_import_btn_l):
        return 1

    elif int(left_btn) > int(load_btn) and int(left_btn) > int(right_btn) and int(left_btn) > int(
            time_import_btn_r) and int(left_btn) > int(time_import_btn_l):
        return slider_val - 1

    elif int(right_btn) > int(load_btn) and int(right_btn) > int(left_btn) and int(right_btn) > int(
            time_import_btn_r) and int(right_btn) > int(time_import_btn_l):
        return slider_val + 1

    elif int(time_import_btn_r) > int(load_btn) and int(time_import_btn_r) > int(left_btn) and int(
            time_import_btn_r) > int(right_btn) and int(time_import_btn_r) > int(time_import_btn_l):
        try:
            stereo_a_dir = np.array(pd.read_json(stereo_a_json)).tolist()

            import_val = stereo_a_dir[r_slider][1].split('/')[-1].split('_')
            import_val = datetime(int(import_val[0][0:4]), int(import_val[0][4:6]), int(import_val[0][6:8]),
                                  int(import_val[1][0:2]), int(import_val[1][2:4]), int(import_val[1][4:6]))

            soho_dir = np.array(pd.read_json(soho_json)).tolist()

            for i in range(0, len(soho_dir)):
                soho_dir[i] = soho_dir[i][1].split('/')[-1].replace('.fts', '').split('_')
                soho_dir[i] = datetime(int(soho_dir[i][0][0:4]), int(soho_dir[i][0][4:6]), int(soho_dir[i][0][6:8]),
                                       int(soho_dir[i][1][0:2]), int(soho_dir[i][1][2:4]), int(soho_dir[i][1][4:6]))

            return min(range(len(soho_dir)), key=lambda i: abs(soho_dir[i] - import_val))

        except (TypeError, IndexError, AttributeError) as e:

            return slider_val
    elif int(time_import_btn_l) > int(load_btn) and int(time_import_btn_l) > int(left_btn) and int(
            time_import_btn_l) > int(right_btn) and int(time_import_btn_l) > int(time_import_btn_r):
        try:
            stereo_b_dir = np.array(pd.read_json(stereo_b_json)).tolist()

            import_val = stereo_b_dir[l_slider][1].split('/')[-1].split('_')
            import_val = datetime(int(import_val[0][0:4]), int(import_val[0][4:6]), int(import_val[0][6:8]),
                                  int(import_val[1][0:2]), int(import_val[1][2:4]), int(import_val[1][4:6]))
            soho_dir = np.array(pd.read_json(soho_json)).tolist()

            for i in range(0, len(soho_dir)):
                soho_dir[i] = soho_dir[i][1].split('/')[-1].replace('.fts', '').split('_')
                soho_dir[i] = datetime(int(soho_dir[i][0][0:4]), int(soho_dir[i][0][4:6]), int(soho_dir[i][0][6:8]),
                                       int(soho_dir[i][1][0:2]), int(soho_dir[i][1][2:4]), int(soho_dir[i][1][4:6]))

            return min(range(len(soho_dir)), key=lambda i: abs(soho_dir[i] - import_val))
        except (TypeError, IndexError, AttributeError) as e:

            return slider_val
    else:
        return 1


# loads header data to intermediate hidden div for later extraction in each of the callbacks
@app.callback(dcd.Output('soho-c3-hidden', 'children'),
              [dcd.Input('btn-load-images', 'n_clicks'),
               dcd.Input('c-image-dropdown', 'value')],
              [dcd.State('date-picker', 'date'),
               dcd.State('date-time', 'value'),
               dcd.State('end-time', 'value')])
def soho_img_arr_load(n_clicks, type_im, date, start_time, end_time):

    if type_im == 'C3':

        image_dir = swpc_utils.extract_images(datetime.strptime(date, '%Y-%m-%d'), start_time,end_time, 3)
    else:

        image_dir = swpc_utils.extract_images(datetime.strptime(date, '%Y-%m-%d'), start_time,end_time, 2)

    if len(image_dir) != 0:

        return json.dumps(image_dir.tolist())

    else:
        return json.dumps(np.empty(1).tolist())


# callback for image  value text
@app.callback(
    dcd.Output('c-image-text', 'children'),
    [dcd.Input('2d-c-lemniscate', 'figure'),
     dcd.Input('c-image-slider', 'value')],
    [dcd.State('soho-c3-hidden', 'children')]
)
def c_image_text_update(trigger, slider_val, image_json):
    try:
        image_dir = np.array(pd.read_json(image_json)).tolist()

        date = datetime.strptime(str(image_dir[slider_val][0]), '%Y-%m-%d %H:%M:%S')

        return date.strftime('%Y-%m-%dT%H:%M:%SZ')

    except (TypeError, IndexError) as e:

        return ''


# callback for 2d-c-lemniscate plot
@app.callback(
    dcd.Output('2d-c-lemniscate', 'figure'),
    [dcd.Input('radial-slider', 'value'),
     dcd.Input('angular-slider', 'value'),
     dcd.Input('long-slider', 'value'),
     dcd.Input('lat-slider', 'value'),
     dcd.Input('C-stretch-bot-slider', 'value'),
     dcd.Input('C-stretch-top-slider', 'value'),
     dcd.Input('C-gamma-slider', 'value'),
     dcd.Input('C-saturation-slider', 'value'),
     dcd.Input('soho-c3-hidden', 'children'),
     dcd.Input('c-image-slider', 'value')
     ])
# function for graph update when slider is changed
def center_lemniscate_update(radial, angular, long, lat, stretch_bot, stretch_top, gamma, saturation, image_json,
                             slider_val):

    # extract jsonified image array
    image_dir = np.array(pd.read_json(image_json)).tolist()

    if len(image_dir) != 1:

        observer, current_map, previous_map = swpc_utils.new_map(image_dir[slider_val][1], image_dir[slider_val - 1][1],
                                                                 saturation)

        hull = swpc_utils.return_plot(observer, 0, radial, angular, long, lat)

        image_data = swpc_utils.return_image(observer.data, gamma, stretch_top, stretch_bot)

        trace = go.Scatter(x=hull[0, :], y=hull[1, :], mode='lines',
                           line=dict(color='rgb(255, 255, 0)'))
        trace1 = go.Scatter(x=[hull[0, 0], hull[0, - 1]],
                            y=[hull[1, 0], hull[1, - 1]], mode='lines',
                            line=dict(color='rgb(255, 255, 0)'))

        trace2 = go.Heatmap(z=image_data,
                            x=np.linspace(-GRID_HALF_WIDTH, GRID_HALF_WIDTH, 256),
                            y=np.linspace(-GRID_HALF_WIDTH, GRID_HALF_WIDTH, 256),
                            colorscale='Greys',
                            showscale=False,
                            )

        return dict(data=[trace, trace1, trace2], layout=layout_two_d_lemniscate)

    else:

        return dict(layout=empty_layout)


# ---------</2D-C-Plot-Callback section>-------


# ---------<2D-R-Plot-Callback section>-------

# modifies right slider max property
@app.callback(
    dcd.Output('r-image-slider', 'max'),
    [dcd.Input('stereo-a-hidden', 'children')]
)
def r_slider_max_update(img_arr):
    return len(np.array(pd.read_json(img_arr))) - 1


# disables slider if there are no images
@app.callback(
    dcd.Output('r-image-slider', 'disabled'),
    [dcd.Input('stereo-a-hidden', 'children')]
)
def r_slider_disable(img_arr):
    # extract jsonified image array
    image_dir = np.array(pd.read_json(img_arr)).tolist()

    if len(image_dir) <= 1:
        return True
    else:
        return False


# disables match button if there are no images
@app.callback(
    dcd.Output('r-btn-match', 'disabled'),
    [dcd.Input('r-btn-match', 'className'),
     dcd.Input('full-matches-hidden', 'children')]
)
def r_match_btn_disable(className, match_list):

    matches = json.loads(match_list)

    if any(d["instrument"] == 'Stereo-A' for d in matches["matches"]):

        if className == 'btn btn-success btn-lg':
            return True
        else:
            return False

    else:
        return False


# disables time export button if there are no images
@app.callback(
    dcd.Output('time_import_btn_r', 'disabled'),
    [dcd.Input('r-image-slider', 'disabled')],
)
def r_time_export_btn_disable(disabled):
    if disabled:
        return True
    else:
        return False


# disables dropdown if there are no images
@app.callback(
    dcd.Output('r-image-dropdown', 'disabled'),
    [dcd.Input('r-image-slider', 'disabled')],
)
def r_dropdown_disable(disabled):
    if disabled:
        return True
    else:
        return False


# disables right move button r if there are no images
@app.callback(
    dcd.Output('left_move_btn_r', 'disabled'),
    [dcd.Input('r-image-slider', 'disabled'),
     dcd.Input('r-image-slider', 'value')]
)
def right_btn_l_disabled(disabled, value):
    if disabled or value == 1:
        return True
    else:
        return False


# disables right move button l if there are no images
@app.callback(
    dcd.Output('right_move_btn_r', 'disabled'),
    [dcd.Input('r-image-slider', 'disabled'),
     dcd.Input('r-image-slider', 'value')],
    [dcd.State('r-image-slider', 'max')]
)
def right_btn_r_disabled(disabled, value, max):
    if disabled or (value == max and value != 1):
        return True
    else:
        return False


@app.callback(
    dcd.Output('STEREO-A', 'style'),
    [dcd.Input('r-image-slider', 'disabled')]
)
def show_hide_stereo_a(disabled):
    if disabled:
        return {'display': 'none'}
    else:
        return {'display': 'flex'}


# resets the image slider eveytime a new image is loaded
@app.callback(
    dcd.Output('r-image-slider', 'value'),
    [dcd.Input('btn-load-images', 'n_clicks_timestamp'),
     dcd.Input('right_move_btn_r', 'n_clicks_timestamp'),
     dcd.Input('left_move_btn_r', 'n_clicks_timestamp'),
     dcd.Input('time_import_btn_l', 'n_clicks_timestamp'),
     dcd.Input('time_import_btn_c', 'n_clicks_timestamp')],
    [dcd.State('r-image-slider', 'value'),
     dcd.State('l-image-slider', 'value'),
     dcd.State('c-image-slider', 'value'),
     dcd.State('soho-c3-hidden', 'children'),
     dcd.State('stereo-a-hidden', 'children'),
     dcd.State('stereo-b-hidden', 'children')]
)
def r_image_slider_btn_move(load_btn, right_btn, left_btn, time_import_btn_l, time_import_btn_c, slider_val, l_slider,
                            c_slider, soho_json, stereo_a_json, stereo_b_json):
    if int(load_btn) > int(right_btn) and int(load_btn) > int(left_btn) and int(load_btn) > int(
            time_import_btn_c) and int(load_btn) > int(time_import_btn_l):
        return 1

    elif int(left_btn) > int(load_btn) and int(left_btn) > int(right_btn) and int(left_btn) > int(
            time_import_btn_c) and int(left_btn) > int(time_import_btn_l):
        return slider_val - 1

    elif int(right_btn) > int(load_btn) and int(right_btn) > int(left_btn) and int(right_btn) > int(
            time_import_btn_c) and int(right_btn) > int(time_import_btn_l):
        return slider_val + 1

    elif int(time_import_btn_c) > int(load_btn) and int(time_import_btn_c) > int(left_btn) and int(
            time_import_btn_c) > int(right_btn) and int(time_import_btn_c) > int(time_import_btn_l):
        try:
            soho_dir = np.array(pd.read_json(soho_json)).tolist()

            import_val = soho_dir[c_slider][1].split('/')[-1].replace('.fts', '').split('_')
            import_val = datetime(int(import_val[0][0:4]), int(import_val[0][4:6]), int(import_val[0][6:8]),
                                  int(import_val[1][0:2]), int(import_val[1][2:4]), int(import_val[1][4:6]))

            stereo_a_dir = np.array(pd.read_json(stereo_a_json)).tolist()

            for i in range(0, len(stereo_a_dir)):
                stereo_a_dir[i] = stereo_a_dir[i][1].split('/')[-1].split('_')
                stereo_a_dir[i] = datetime(int(stereo_a_dir[i][0][0:4]), int(stereo_a_dir[i][0][4:6]),
                                           int(stereo_a_dir[i][0][6:8]), int(stereo_a_dir[i][1][0:2]),
                                           int(stereo_a_dir[i][1][2:4]), int(stereo_a_dir[i][1][4:6]))

            return min(range(len(stereo_a_dir)), key=lambda i: abs(stereo_a_dir[i] - import_val))

        except (TypeError, IndexError, AttributeError) as e:

            return slider_val

    elif int(time_import_btn_l) > int(load_btn) and int(time_import_btn_l) > int(left_btn) and int(
            time_import_btn_l) > int(right_btn) and int(time_import_btn_l) > int(time_import_btn_c):
        try:
            stereo_b_dir = np.array(pd.read_json(stereo_b_json)).tolist()

            import_val = stereo_b_dir[l_slider][1].split('/')[-1].split('_')
            import_val = datetime(int(import_val[0][0:4]), int(import_val[0][4:6]), int(import_val[0][6:8]),
                                  int(import_val[1][0:2]), int(import_val[1][2:4]), int(import_val[1][4:6]))

            stereo_a_dir = np.array(pd.read_json(stereo_a_json)).tolist()

            for i in range(0, len(stereo_a_dir)):
                stereo_a_dir[i] = stereo_a_dir[i][1].split('/')[-1].split('_')
                stereo_a_dir[i] = datetime(int(stereo_a_dir[i][0][0:4]), int(stereo_a_dir[i][0][4:6]),
                                           int(stereo_a_dir[i][0][6:8]), int(stereo_a_dir[i][1][0:2]),
                                           int(stereo_a_dir[i][1][2:4]), int(stereo_a_dir[i][1][4:6]))

            return min(range(len(stereo_a_dir)), key=lambda i: abs(stereo_a_dir[i] - import_val))

        except (TypeError, IndexError, AttributeError) as e:

            return slider_val

    else:
        return 1


# loads header data to intermediate hidden div for later extraction in each of the callbacks
@app.callback(dcd.Output('stereo-a-hidden', 'children'),
              [dcd.Input('btn-load-images', 'n_clicks'),
               dcd.Input('l-image-dropdown', 'value')],
              [dcd.State('date-picker', 'date'),
               dcd.State('date-time', 'value'),
               dcd.State('end-time', 'value')])
def stereo_a_img_arr_load(n_clicks, type_im, date, start_time, end_time):

    image_dir = swpc_utils.extract_images(datetime.strptime(date, '%Y-%m-%d'), start_time, end_time, 4)

    if len(image_dir) != 0:

        return json.dumps(image_dir.tolist())

    else:
        return json.dumps(np.empty(1).tolist())


# callback for image  value text
@app.callback(
    dcd.Output('r-image-text', 'children'),
    [dcd.Input('2d-r-lemniscate', 'figure'),
     dcd.Input('r-image-slider', 'value')],
    [dcd.State('stereo-a-hidden', 'children')]
)
def r_image_text_update(trigger, slider_val, image_json):
    try:
        image_dir = np.array(pd.read_json(image_json)).tolist()

        date = datetime.strptime(str(image_dir[slider_val][0]), '%Y-%m-%d %H:%M:%S')

        return date.strftime('%Y-%m-%dT%H:%M:%SZ')

    except (TypeError, IndexError) as e:

        return ''


# callback for 2d-r-lemniscate plot
@app.callback(
    dcd.Output('2d-r-lemniscate', 'figure'),
    [dcd.Input('radial-slider', 'value'),
     dcd.Input('angular-slider', 'value'),
     dcd.Input('long-slider', 'value'),
     dcd.Input('lat-slider', 'value'),
     dcd.Input('R-stretch-bot-slider', 'value'),
     dcd.Input('R-stretch-top-slider', 'value'),
     dcd.Input('R-gamma-slider', 'value'),
     dcd.Input('R-saturation-slider', 'value'),
     dcd.Input('stereo-a-hidden', 'children'),
     dcd.Input('r-image-slider', 'value')])
# function for graph update when slider is changed
def right_lemniscate_update(radial, angular, long, lat, stretch_bot, stretch_top, gamma, saturation, image_json,
                            slider_val):
    global n

    # extract jsonified image array
    image_dir = np.array(pd.read_json(image_json)).tolist()

    if len(image_dir) != 1:

        observer, current_map, previous_map = swpc_utils.new_map(image_dir[slider_val][1], image_dir[slider_val - 1][1],
                                                                 saturation)

        hull = swpc_utils.return_plot(observer, 1, radial, angular, long, lat)

        image_data = swpc_utils.return_image(observer.data, gamma, stretch_top, stretch_bot)

        trace = go.Scatter(x=hull[0, :], y=hull[1, :], mode='lines',
                           line=dict(color='rgb(255, 255, 0)'))
        trace1 = go.Scatter(x=[hull[0, 0], hull[0, - 1]],
                            y=[hull[1, 0], hull[1, - 1]], mode='lines',
                            line=dict(color='rgb(255, 255, 0)'))

        trace2 = go.Heatmap(z=image_data,
                            x=np.linspace(-GRID_HALF_WIDTH, GRID_HALF_WIDTH, 256),
                            y=np.linspace(-GRID_HALF_WIDTH, GRID_HALF_WIDTH, 256),
                            colorscale='Greys',
                            showscale=False,
                            )

        return dict(data=[trace, trace1, trace2], layout=layout_two_d_lemniscate)

    else:

        return dict(layout=empty_layout)


# ---------</2D-R-Plot-Callback section>-------

# ---------<Velocity Graph section>-------

# takes care of plotting the velocity graph based on event time and radial distance

@app.callback(dcd.Output('velocity-graph', 'figure'),
              [dcd.Input('full-matches-hidden','children')],
              )
def velocity_graph_update(match_list):

    matches = json.loads(match_list)

    if len(matches["matches"]) > 0:
        full_match_list = []
        stereo_b_list = []
        soho_list = []
        stereo_a_list = []

        for d in matches["matches"]:

            if d['instrument'] == "Stereo-B":
                stereo_b_list.append(d['timestamp'])
                stereo_b_list.append(d['radial'])

            if d['instrument'] == "SOHO C3":
                soho_list.append(d['timestamp'])
                soho_list.append(d['radial'])

            if d['instrument'] == "Stereo-A":
                stereo_a_list.append(d['timestamp'])
                stereo_a_list.append(d['radial'])

        trace = go.Scatter(x=stereo_b_list[0::2], y=stereo_b_list[1::2], mode='markers', name='Stereo B', marker=dict(
            size=20,
            color='rgba(0,0,255,1)',
            symbol='square',
            line=dict(
                width=2)))
        trace1 = go.Scatter(x=soho_list[0::2], y=soho_list[1::2], mode='markers', name='SOHO', marker=dict(
            size=20,
            color='rgba(0,128,0,1)',
            symbol='square',
            line=dict(
                width=2)))
        trace2 = go.Scatter(x=stereo_a_list[0::2], y=stereo_a_list[1::2], mode='markers', name='Stereo A', marker=dict(
            size=20,
            color='rgba( 255, 0, 0,1)',
            symbol='square',
            line=dict(
                width=2)))

        if len(matches["matches"]) > 1:
            # Generated linear fit
            time_series_seconds = np.zeros(len(matches["matches"]))
            rad_matches = []

            for i in range(0, len(matches["matches"])):

                full_match_list.append(matches["matches"][i]['timestamp'])
                time_series_seconds[i] = datetime.strptime(matches["matches"][i]['timestamp'],
                                                           '%Y-%m-%d %H:%M:%S').timestamp()
                rad_matches.append(matches["matches"][i]['radial'])

            slope, intercept, r_value, p_value, std_err = stats.linregress(time_series_seconds, rad_matches)
            line = slope * time_series_seconds + intercept

            trace3 = go.Scatter(x=full_match_list, y=line, mode='lines', name='Linear fit', marker=dict(
                size=2,
                color='rgba(242, 38, 19, 1)',
                line=dict(
                    width=2)))

            return dict(data=[trace, trace1, trace2, trace3], layout=layout_velocity)

        else:

            return dict(data=[trace, trace1, trace2], layout=layout_velocity)

    return dict(data=[], layout=empty_layout)


# ---------</Velocity Graph section>-------


# ---------<Matching section>-------

# changes the color of the left match button to green if the image was matched before
# if that's not the case it stays blue
@app.callback(dcd.Output('l-btn-match', 'className'),
              [dcd.Input('l-image-slider', 'value'),
               dcd.Input('full-matches-hidden', 'children')],
              [dcd.State('stereo-b-hidden', 'children')])
def l_matched_button_check(slider_val, match_list, image_list):

    matches = json.loads(match_list)

    if any(d["instrument"] == 'Stereo-B' for d in matches["matches"]):

        image_dir = np.array(pd.read_json(image_list)).tolist()

        if any(d["link"] == image_dir[slider_val][1] for d in matches["matches"]):
            return 'btn btn-success btn-lg'
        else:
            return 'btn btn-primary btn-lg'
    else:
        return 'btn btn-primary btn-lg'


# changes the color of the center match button to green if the image was matched before
# if that's not the case it stays blue
@app.callback(dcd.Output('c-btn-match', 'className'),
              [dcd.Input('c-image-slider', 'value'),
               dcd.Input('full-matches-hidden', 'children')],
              [dcd.State('soho-c3-hidden', 'children')])
def c_matched_button_check(slider_val, match_list, image_list):

    matches = json.loads(match_list)

    if any(d["instrument"] == 'SOHO C3' for d in matches["matches"]):

        image_dir = np.array(pd.read_json(image_list)).tolist()

        if any(d["link"] == image_dir[slider_val][1] for d in matches["matches"]):
            return 'btn btn-success btn-lg'
        else:
            return 'btn btn-primary btn-lg'
    else:
        return 'btn btn-primary btn-lg'


# changes the color of the right match button to green if the image was matched before
# if that's not the case it stays blue
@app.callback(dcd.Output('r-btn-match', 'className'),
              [dcd.Input('r-image-slider', 'value'),
               dcd.Input('full-matches-hidden', 'children')],
              [dcd.State('stereo-a-hidden', 'children')])
def r_matched_button_check(slider_val, match_list, image_list):

    matches = json.loads(match_list)

    if any(d["instrument"] == 'Stereo-A' for d in matches["matches"]):

        image_dir = np.array(pd.read_json(image_list)).tolist()

        if any(d["link"] == image_dir[slider_val][1] for d in matches["matches"]):
            return 'btn btn-success btn-lg'
        else:
            return 'btn btn-primary btn-lg'
    else:
        return 'btn btn-primary btn-lg'


# save full matched image array
@app.callback(dcd.Output('full-matches-hidden', 'children'),
              [dcd.Input('l-btn-match', 'n_clicks'),
               dcd.Input('c-btn-match', 'n_clicks'),
               dcd.Input('r-btn-match', 'n_clicks'),
               dcd.Input('unmatch-btn-l', 'n_clicks'),
               dcd.Input('unmatch-btn-c', 'n_clicks'),
               dcd.Input('unmatch-btn-r', 'n_clicks'),
               dcd.Input('reset-all-btn', 'n_clicks')],
              [dcd.State('stereo-b-hidden', 'children'),
               dcd.State('soho-c3-hidden', 'children'),
               dcd.State('stereo-a-hidden', 'children'),
               dcd.State('full-matches-hidden', 'children'),
               dcd.State('l-image-slider', 'value'),
               dcd.State('c-image-slider', 'value'),
               dcd.State('r-image-slider', 'value'),
               dcd.State('radial-slider', 'value')]
              )
def match_arr_calc(match_btn1, match_btn2, match_btn3, unmatch_btn1, unmatch_btn2, unmatch_btn3, reset_all_btn,
                   stereo_b_json, soho_json, stereo_a_json, matches, l_slider, c_slider, r_slider, radial):
    ctx = dash.callback_context

    if not ctx.triggered:
        return json.dumps({"matches": []})
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    matches = json.loads(matches)

    if button_id == 'l-btn-match':
        image_dir = np.array(pd.read_json(stereo_b_json)).tolist()
        matches["matches"].append({"instrument": "Stereo-B", "timestamp": str(image_dir[l_slider][0]),
                                   "link" :image_dir[l_slider][1], "radial": radial})

    if button_id == 'c-btn-match':
        image_dir = np.array(pd.read_json(soho_json)).tolist()
        matches["matches"].append({"instrument": "SOHO C3", "timestamp": str(image_dir[c_slider][0]),
                                   "link": image_dir[c_slider][1],"radial": radial})

    if button_id == 'r-btn-match':
        image_dir = np.array(pd.read_json(stereo_a_json)).tolist()
        matches["matches"].append({"instrument": "Stereo-A", "timestamp": str(image_dir[r_slider][0]),
                                   "link":image_dir[r_slider][1], "radial": radial})

    if button_id == 'unmatch-btn-l':
        image_dir = np.array(pd.read_json(stereo_b_json)).tolist()
        for idx in range(0, len(matches["matches"])):
            if matches["matches"][idx]["link"] == image_dir[l_slider][1]:
                del matches["matches"][idx]
                break

    if button_id == 'unmatch-btn-c':
        image_dir = np.array(pd.read_json(soho_json)).tolist()
        for idx in range(0, len(matches["matches"])):
            if matches["matches"][idx]["link"] == image_dir[c_slider][1]:
                del matches["matches"][idx]
                break

    if button_id == 'unmatch-btn-r':
        image_dir = np.array(pd.read_json(stereo_a_json)).tolist()
        for idx in range(0, len(matches["matches"])):
            if matches["matches"][idx]["link"] == image_dir[r_slider][1]:
                del matches["matches"][idx]
                break

    if button_id == 'reset-all-btn':
        return json.dumps({"matches": []})

    return json.dumps(matches)


# ---------</Matching section>-------

# ---------<Un-matching section>-------

@app.callback(dcd.Output('unmatch-btn-l', 'disabled'),
              [dcd.Input('full-matches-hidden', 'children'),
               dcd.Input('l-image-slider', 'disabled'),
               dcd.Input('l-image-slider', 'value')],
              [dcd.State('stereo-b-hidden', 'children')]
              )
def disable_unmatch_l(match_list, image_slider, l_slider, stereo_b_json):

    if image_slider:
        return True

    matches = json.loads(match_list)

    image_dir = np.array(pd.read_json(stereo_b_json)).tolist()

    for idx in range(0, len(matches["matches"])):
        if matches["matches"][idx]["link"] == image_dir[l_slider][1]:
            return False

    return True


@app.callback(dcd.Output('unmatch-btn-c', 'disabled'),
              [dcd.Input('full-matches-hidden', 'children'),
               dcd.Input('c-image-slider', 'disabled'),
               dcd.Input('c-image-slider', 'value')],
              [dcd.State('soho-c3-hidden', 'children')]
              )
def disable_unmatch_c(match_list, image_slider, c_slider, soho_json):
    if image_slider:
        return True

    matches = json.loads(match_list)

    image_dir = np.array(pd.read_json(soho_json)).tolist()

    for idx in range(0, len(matches["matches"])):
        if matches["matches"][idx]["link"] == image_dir[c_slider][1]:
            return False

    return True

@app.callback(dcd.Output('unmatch-btn-r', 'disabled'),
              [dcd.Input('full-matches-hidden', 'children'),
               dcd.Input('r-image-slider', 'disabled'),
               dcd.Input('r-image-slider', 'value')],
              [dcd.State('stereo-a-hidden', 'children')])
def disable_unmatch_r(match_list, image_slider, r_slider, stereo_a_json):
    if image_slider:
        return True

    matches = json.loads(match_list)

    image_dir = np.array(pd.read_json(stereo_a_json)).tolist()

    for idx in range(0, len(matches["matches"])):
        if matches["matches"][idx]["link"] == image_dir[r_slider][1]:
            return False

    return True


# ---------</Un-matching section>-------

# ---------<Results Section>---------

@app.callback(dcd.Output('lat-result', 'hidden'),
              [dcd.Input('calculate-btn', 'n_clicks_timestamp'),
               dcd.Input('reset-all-btn', 'n_clicks_timestamp'),
               dcd.Input('time-hidden', 'children')])
def hide_lat(n_clicks, reset, trigger):
    if n_clicks > reset and trigger != '0':
        return False
    else:
        return True


@app.callback(dcd.Output('long-result', 'hidden'),
              [dcd.Input('calculate-btn', 'n_clicks_timestamp'),
               dcd.Input('reset-all-btn', 'n_clicks_timestamp'),
               dcd.Input('time-hidden', 'children')])
def hide_long(n_clicks, reset, trigger):
    if n_clicks > reset and trigger != '0':
        return False
    else:
        return True


@app.callback(dcd.Output('half-width-result', 'hidden'),
              [dcd.Input('calculate-btn', 'n_clicks_timestamp'),
               dcd.Input('reset-all-btn', 'n_clicks_timestamp'),
               dcd.Input('time-hidden', 'children')])
def hide_width(n_clicks, reset, trigger):
    if n_clicks > reset and trigger != '0':
        return False
    else:
        return True


@app.callback(dcd.Output('velocity-result', 'hidden'),
              [dcd.Input('calculate-btn', 'n_clicks_timestamp'),
               dcd.Input('reset-all-btn', 'n_clicks_timestamp'),
               dcd.Input('time-hidden', 'children')])
def hide_velocity(n_clicks, reset, trigger):
    if n_clicks > reset and trigger != '0':
        return False
    else:
        return True


@app.callback(dcd.Output('time-result', 'hidden'),
              [dcd.Input('calculate-btn', 'n_clicks_timestamp'),
               dcd.Input('reset-all-btn', 'n_clicks_timestamp'),
               dcd.Input('time-hidden', 'children')])
def hide_time(n_clicks, reset, trigger):
    if n_clicks > reset and trigger != '0':
        return False
    else:
        return True


# prints the latitude to the results section
@app.callback(dcd.Output('lat-result', 'children'),
              [dcd.Input('velocity-result', 'children')],
              [dcd.State('lat-slider', 'value')])
def print_lat_result(json, lat_val):
    return 'Latitude: {}'.format(lat_val)


# prints the longitude to the results section
@app.callback(dcd.Output('long-result', 'children'),
              [dcd.Input('velocity-result', 'children')],
              [dcd.State('long-slider', 'value')])
def print_long_result(json, long_val):
    return 'Longitude: {}'.format(long_val)


# prints the half-width to the results section
@app.callback(dcd.Output('half-width-result', 'children'),
              [dcd.Input('velocity-result', 'children')],
              [dcd.State('angular-slider', 'value')])
def print_width_result(json, angular_val):
    return 'Half-Width: {}'.format(angular_val / 2)


# calculate velocity to the results section
@app.callback(dcd.Output('radial-velocity-hidden', 'children'),
              [dcd.Input('full-matches-hidden', 'children')])
def calc_velocity_result( match_list):

    matches = json.loads(match_list)

    if len(matches["matches"]) < 2:
        return "0"

    time_arr = []
    rad_arr = []

    for idx in range(0, len(matches["matches"])):
        time_arr.append(datetime.strptime(matches["matches"][idx]["timestamp"], '%Y-%m-%d %H:%M:%S'))
        rad_arr.append(matches["matches"][idx]["radial"])

    start_time = julian.to_jd(time_arr[0], fmt='jd')

    for idx in range(0, len(time_arr)):
        time_arr[idx] = julian.to_jd(time_arr[idx], fmt='jd') - start_time

    results = np.polyfit(time_arr, rad_arr, 1)

    radial_velocity = results[0] * u.solRad.to(u.km) / u.day.to(u.s)

    return json.dumps(radial_velocity)


# prints radial velocity
@app.callback(dcd.Output('velocity-result', 'children'),
              [dcd.Input('radial-velocity-hidden', 'children')])
def print_velocity(velocity_json):

    if velocity_json == '0':
        return ""

    radial_velocity = json.loads(velocity_json)

    return 'Radial Velocity: {:.2f}'.format(radial_velocity)


# calculate time at 21.5Rs to the results section
@app.callback(dcd.Output('time-hidden', 'children'),
              [dcd.Input('full-matches-hidden', 'children')])
def calc_time_result(match_list):

    matches = json.loads(match_list)

    if len(matches["matches"]) < 2:
        return "0"

    time_arr = []
    rad_arr = []

    for idx in range(0, len(matches["matches"])):
        time_arr.append(datetime.strptime(matches["matches"][idx]["timestamp"], '%Y-%m-%d %H:%M:%S'))
        rad_arr.append(matches["matches"][idx]["radial"])

    start_time = julian.to_jd(time_arr[0], fmt='jd')

    for idx in range(0, len(time_arr)):
        time_arr[idx] = julian.to_jd(time_arr[idx], fmt='jd') - start_time

    results = np.polyfit(time_arr, rad_arr, 1)

    radial_velocity = results[0] * u.solRad.to(u.km) / u.day.to(u.s)

    intercept = results[1] * u.solRad.to(u.km)

    time_at21 = (21.5 * u.solRad.to(u.km) - intercept) / radial_velocity + start_time * u.day.to(u.s)

    time_at21_jd = time_at21 * u.s.to(u.day)

    return json.dumps(time_at21_jd)


# prints time at 21.5R
@app.callback(dcd.Output('time-result', 'children'),
              [dcd.Input('time-hidden', 'children')])
def print_time(time_json):

    if time_json == '0':
        return ""

    time_val = json.loads(time_json)

    datetime_at21 = julian.from_jd(time_val, fmt='jd').strftime("%Y-%m-%d %H:%M:%SZ")

    return 'Time at 21.5 Rsun: \n {0}'.format(datetime_at21)


# disables reset all button if theres less than 2 matches
@app.callback(dcd.Output('reset-all-btn', 'disabled'),
              [dcd.Input('calculate-btn', 'disabled')])
def disable_reset_all(disabled):
    if disabled:
        return True
    else:
        return False


# calculate and print velocity to the results section
@app.callback(dcd.Output('calculate-btn', 'disabled'),
              [dcd.Input('full-matches-hidden', 'children')])
def calculate_disable(match_list):

    matches = json.loads(match_list)

    if len(matches["matches"]) > 1:
        return False
    else:
        return True


# @app.callback(dcd.Output('export-btn', 'hidden'),
#               [dcd.Input('calculate-btn', 'disabled'),
#                dcd.Input('calculate-btn', 'n_clicks'),
#                dcd.Input('velocity-result', 'children')])
# def export_hidden(disabled, n_clicks, json_test):
#
#     if disabled or (n_clicks is None and json_test == 'Radial Velocity: 0.00'):
#         return True
#     else:
#         return False


# # callback creates all of the relevant measurement information for URL transfer
# @app.callback(dcd.Output('my-link', 'href'),
#               [dcd.Input('full-matches-hidden', 'children'),
#                dcd.Input('radial-velocity-hidden', 'children')],
#               [dcd.State('radial-matches-hidden', 'children'),
#                dcd.State('instrument-matches-hidden', 'children'),
#                dcd.State('lat-slider', 'value'),
#                dcd.State('long-slider', 'value'),
#                dcd.State('angular-slider', 'value')])
# def update_link(full_json, radial_val, radial_json, instrument_json, lat_val, long_val, angular_val):
#     try:
#         time_arr = json.loads(full_json)
#         radial_arr = json.loads(radial_json)
#         instrument_arr = json.loads(instrument_json)
#         radial_vel = json.loads(radial_val)
#         for idx in range(0, len(time_arr)):
#             time_arr[idx] = time_arr[idx]
#
#         time_results = ','.join(time_arr)
#         radial_results = ','.join(str(x) for x in radial_arr)
#         instrument_results = ','.join(str(x) for x in instrument_arr)
#         return '/dash/urlToDownload?value={}'.format(
#             time_results + ' | ' + radial_results + '|' + instrument_results + '|'
#             + str(angular_val) + '|' + str(lat_val) + '|' + str(long_val) + '|'
#             + str(radial_vel))
#     except TypeError:
#
#         return '/dash/urlToDownload?value=0 | 0 | 0 | 0 | 0 | 0 | 0 '
#
#
# # dynamic file creation method for export of measurement data
# @app.server.route('/dash/urlToDownload')
# def download_txt():
#     # allow for divs to be populated
#     # create a dynamic csv or file here using `StringIO`
#     # (instead of writing to the file system)
#     value = flask.request.args.get('value')
#     time_arr, radial, instruments, angular_val, lat, long, radial_vel = value.split('|')
#     time_arr = time_arr.split(',')
#     radial = radial.split(',')
#     instruments = instruments.split(',')
#
#     str_io = io.StringIO()
#
#     str_io.write('Date: ' + datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S') + '\n')
#     str_io.write('Date of CME measured: ' + time_arr[0] + '\n \n')
#     str_io.write('Timestamp of CME measurement \t Radial Distance \t Instrument \n')
#
#     for i in range(0, len(time_arr)):
#         str_io.write(time_arr[i] + '\t' + radial[i] + '\t\t' + instruments[i] + '\n')
#
#     str_io.write('\nLatitude:{:.3f}'.format(float(lat)) + '\n')
#     str_io.write('Longitude: {:.3f}'.format(float(long)) + '\n')
#     str_io.write('CME Half-width: {:.3f}'.format(float(angular_val) / 2) + '\n')
#     str_io.write('Radial Velocity: {:.3f} '.format(float(radial_vel)) + '\n')
#
#     mem = io.BytesIO()
#     mem.write(str_io.getvalue().encode('utf-8'))
#     mem.seek(0)
#     str_io.close()
#     return flask.send_file(mem,
#                            mimetype='text/*',
#                            attachment_filename='MeasurementResults' + datetime.strftime(datetime.today(),
#                                                                                         '%Y-%m-%d %H:%M:%S') + '.txt',
#                            as_attachment=True)
#

# ---------</Results Section>--------

if __name__ == '__main__':
    if DEVMODE:
        app.run_server(debug=False)
    else:
        app.run_server(debug=False, host="0.0.0.0", port=8000)
        

server = app.server
