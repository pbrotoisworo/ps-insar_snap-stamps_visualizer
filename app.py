import os
from datetime import date, timedelta

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.graph_objs as go

from utils.processing import read_data, export_data
from utils.plots import plot_ts

st.set_page_config(page_title='PS-InSAR StAMPS Visualizer', initial_sidebar_state='expanded', layout='wide')


def main():
	st.header('PS-InSAR SNAP - StAMPS Workflow Visualizer')
	st.markdown(f"""
		<p align="justify">A simple web app to visualize the Persistent Scatterers (PS) identified using the
		<a href=https://forum.step.esa.int/t/snap-stamps-workflow-documentation/13985>SNAP - StAMPS workflow </a>. You can <strong>visualize your own data</strong> by uploading the
		Matlab file <strong>(i.e., <font color="#2D8632">'ps_plot_ts_v-do.mat', ps_plot_v-do.mat</font>)</strong> outputs from the SNAP-StAMPS workflow.</p>
		
		<p align="justify">This is inspired by the <a href=https://forum.step.esa.int/t/stamps-visualizer-snap-stamps-workflow/9613>StAMPS visualizer based on R</a>. If you have 
		suggestions on how to improve this, just let me know.</p>
		""", unsafe_allow_html=True)

	with st.expander('Data Ingestion', expanded=True):
		c1, c2, c3 = st.columns(3)
		with c1:
			mat_files = st.file_uploader('Upload mat files', accept_multiple_files=True, type=['mat'])
		with c2:
			subset_shp = st.file_uploader('Upload GeoJSON to subset data', type=['geojson'])
		with c3:
			mask_shp = st.file_uploader('Upload GeoJSON to mask data', type=['geojson'])
		if len(mat_files) < 2:
			st.info('Get started by uploading the required .mat files.')
			st.stop()

	with st.expander('Data Points Control Panel', expanded=True):
		c1, c2, _ = st.columns(3)
		with c1:
			ps_count = st.empty()
			nmax_input = st.empty()
			nmax = nmax_input.number_input('Maximum points to visualize', min_value=0, value=1000, max_value=50000)
		with c2:
			st.markdown('#')
			ps_filter_input = st.empty()
			ps_filter = ps_filter_input.text_input(
				label='Select specific PS objects',
				help='Must be comma separated value with no space'
			)
			ps_filter = ps_filter.split(',')
			if len(ps_filter) > 1 and ps_filter[0] != '':
				ps_filter = [int(x) for x in ps_filter]

		# a1, a2 = st.columns((5,3))
		b1, b2 = st.columns(2)

		mat_files = [mat_files[i].name for i in range(2)]
		df, bperp_df, slave_days, master_day, nmax_out = read_data(fn=mat_files, upload_subset=subset_shp, upload_mask=mask_shp, n=nmax)
		if nmax_out != nmax:
			nmax_input.number_input('Maximum points to visualize', value=nmax_out)
		ps_count.markdown(f'PS objects in dataset: `{nmax_out}`')

		selectdate = b1.select_slider('Select Date', df.Date.unique().tolist(), value=df.Date.unique().tolist()[3], help='Defines the date to be considered in the plot of PS')
		mapbox_df = df[df.Date.isin([selectdate])]

		# Filtered DF for timeline graph
		if len(ps_filter) > 1 and ps_filter[0] != '':
			filtered_df = df[df['ps'].isin(ps_filter)]
		else:
			# If there is no input it will get the first 5 PS values by default
			filtered_df = df.copy()
			ps_filter = filtered_df['ps'].tolist()[:5]
			filtered_df = filtered_df[filtered_df['ps'].isin(pd.Series(ps_filter))]
			# ps_filter_input.text_input(label='Select PS by ID', value=','.join([str(x) for x in ps_filter]), help='Must be comma separated values')

		st.markdown(f"""<p align="justify">Number of selected PS: <strong>{len(ps_filter)}</strong> (<font color="#6DD929">green markers</font>).
				<br>Use the map customization panel to change the appearance of the plots. You can change the color scale, 
				base map style and/or the size of the markers.</p>
				""", unsafe_allow_html=True)

	with st.expander('Map Customization Panel'):
		m1, m2, m3 = st.columns(3)
		style_dict = {'Carto-Positron':'carto-positron', 'Openstreetmap':'open-street-map', 'Carto Dark':'carto-darkmatter', 
			'Stamen Terrain':'stamen-terrain', 'Stamen Toner':'stamen-toner', 'Stamen Watercolor':'stamen-watercolor'}

		style = m1.selectbox('Select map style', ['Carto-Positron', 'Openstreetmap', 'Carto Dark', 
			'Stamen Terrain', 'Stamen Toner', 'Stamen Watercolor'], index=2) 

		colorscale = m2.selectbox('Select color scale', ['Greys','YlGnBu','Greens','YlOrRd','Bluered','RdBu','Reds','Blues','Picnic',
			'Rainbow','Portland','Jet','Hot','Blackbody','Earth','Electric','Viridis','Cividis'], index=15)

		msize = m3.slider('Select marker size', min_value=2, max_value=15, value=5, step=1)

	mean_los = st.checkbox('Click to plot mean LOS Displacement')

	if mean_los:
		colr = mapbox_df.ave
		txt = 'Mean '
		txt1 = '/yr'
		histX = 'ave'
		velocity = ' Velocity'
	else:
		colr = mapbox_df.Displacement
		txt = ''
		txt1 = ''
		histX = 'Displacement'
		velocity = ''

	data = go.Scattermapbox(name='', lat=mapbox_df.lat, lon=mapbox_df.lon, 
		mode='markers',
		marker=dict(size=msize, opacity=.8, color=colr.values, colorscale=colorscale, cmid=0,
			colorbar=dict(thicknessmode='pixels', 
				title=dict(text=f'{txt}LOS Displacement (mm{txt1})', side='right'))), 
		) # , selected=dict(marker=dict(color='rgb(255,0,0)', size=msize, opacity=.8))

	layout = go.Layout(width=950, height=500, 
		mapbox = dict(center= dict(lat=(mapbox_df.lat.max() + mapbox_df.lat.min())/2, 
			lon=(mapbox_df.lon.max() + mapbox_df.lon.min())/2), 
		# accesstoken= token, 
		zoom=10.7,
		style=style_dict[style]), 
		margin=dict(l=0, r=0, t=0, b=0), autosize=True,
		clickmode='event+select')
	
	fig = go.FigureWidget(data=data, layout=layout)
	hover_text = np.stack((mapbox_df.ps.values, 
							colr.values, 
							mapbox_df.Date.values), axis=1)

	fig.update_traces(customdata=hover_text,
						hovertemplate='<br><b>PS ID</b>: %{customdata[0]}</br>' +\
							'<b>Displacement</b>: %{customdata[1]} mm'+ f'{txt1}')

	filters = filtered_df[filtered_df.Date.isin([selectdate])]
	fig.add_trace(go.Scattermapbox(name='', 
		lat=filters.lat, 
		lon=filters.lon,
		text=filters.ps, 
		mode='markers',
		hovertemplate='<b>PS ID</b>: %{text} (Selected)', 
		marker=dict(size=msize+5, color='#51ED5A')
		))

	st.plotly_chart(fig, use_container_width=True)
	
	# safeguard for empty selection 
	if len(ps_filter) == 0:
		return
	st.markdown('---')
	filters.reset_index(inplace=True, drop=True)
	filters = filters.rename(columns={'ps': 'PS ID', 'lon': 'Longitude', 'lat': 'Latitude',
						'ave': 'Average Disp'})
	filters = filters[['PS ID', 'Latitude', 'Longitude', 'Average Disp']]
	st.markdown(f'<center>Additional information on the selected points (count = {len(ps_filter)})</center>', unsafe_allow_html=True)
	st.table(filters)

	st.markdown(f"""<center>Time series plot of the selected PS (count: {len(ps_filter)})</center>
			""", unsafe_allow_html=True)

	filtered_df.drop(['geometry'], axis=1, inplace=True)

	ts_reg_selection = st.selectbox('Trend line for timeseries', ('Linear Regression', 'LOESS'))
	st.altair_chart(plot_ts(filtered_df, reg=ts_reg_selection), use_container_width=True)

	st.markdown(f'Descriptive statistics for {txt}PS displacement{velocity} (mm{txt1}) of selection (n = {len(mapbox_df)}).')
	c1, c2, c3 = st.columns(3)
	n = st.slider('Select bin width', min_value=1, max_value=10, value=1, help='Adjusts the width of bins. Default: 1 unit')
	c1.info(f'Highest: {colr.max():0.2f}')
	c2.info(f'Lowest: {colr.min():0.2f}')
	c3.info(f'Average: {colr.mean():0.2f}')

	altHist = alt.Chart(mapbox_df.drop(['geometry'], axis=1)).mark_bar().encode(
		x=alt.X(f'{histX}:Q', bin=alt.Bin(step=n), title=f'{txt}Displacement (mm{txt1})'),
		y='count()',
		color=alt.Color('count()', legend=alt.Legend(title='Count', orient='top-left'), scale=alt.Scale(scheme='Redblue')), # )
		tooltip=[alt.Tooltip('count()', format=',.0f', title='Count', bin={'binned':True, 'step':int(f'{n}')})]).interactive(bind_y=False)
	st.markdown(f'<center>Distribution of PS Displacement{velocity} (bins = {n})</center>', unsafe_allow_html=True)
	st.altair_chart(altHist, use_container_width=True)

	md = date(1, 1, 1) + timedelta(int(master_day[0])) - timedelta(367)
	with st.expander('Metadata'):
		a1, a2 = st.columns((2))
		a1.info(f'Master Date: {md}')
		a2.info(f'Number of slave images: {len(slave_days)}')
		bperp_chart = alt.Chart(bperp_df).mark_circle(size=72).encode(
			x=alt.X('Temporal:Q', title='Temporal Baseline (days)'),
			y=alt.Y('Bperp:Q', title='Perpendicular Baseline (m)'),
			color=alt.Color('Day:N', legend=alt.Legend(title=None, orient='top-right')),
			tooltip=[alt.Tooltip('Day:N', title='Type'),
						alt.Tooltip('Date:T'),
						alt.Tooltip('Bperp:Q', format='.2f'),
						alt.Tooltip('Temporal:Q')]
			)

		st.altair_chart(bperp_chart, use_container_width=True)

	if os.environ.get('DEPLOYMENT') == 1:
		pass
	else:
		download = st.button('Process data')
		if download:
			with st.spinner('Processing data...'):
				export_data(mat_files, 'export', 'velocity.tif')
			st.success('Data exported to app root!')

	# with st.expander('Download data'):
	# 	st.download_button('Download processed data', data=df.to_csv().encode('utf-8'), mime='text/csv')

	st.markdown('---')
	st.info("""
		Using a modified version of PS-InSAR StAMPS Visualizer originally created by Created by: **K. Quisado** 
		[GitHub](https://github.com/kenquix/ps-insar_visualizer) as part of course project on Microwave RS under the MS
		Geomatics Engineering (Remote Sensing) Program, University of the Philippines - Diliman
		""")

if __name__ == '__main__':
	main()
