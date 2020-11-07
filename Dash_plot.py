import pandas as pd
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import json
from urllib.request import urlopen


app = dash.Dash(__name__)

token = 'pk.eyJ1IjoibGNpZXNsdWsiLCJhIjoiY2toNnM3MG9lMDBhNDJydDM4a3EwYnEyYiJ9.-6g_IQr9CFIe_Z7UtG_tkw'

pop = pd.read_excel('area_population.xlsx')
pop = pop.drop(['Miasto','Województwo','Gęstość zaludnienia [osoby/km²] (01.01.2020)'], axis =1)
pop = pop.rename(columns = {'Powiat':'district','Powierzchnia [ha] (01.01.2020)': 'area of district','Liczba ludności (01.01.2020)':'population' })
pop['district'] = 'powiat '+ pop['district']


# load geojson to use in Choropleth map
with open('poland', encoding = 'utf-8') as f:
	poland = json.load(f)

# dict with colors of background and text
colors = {
    'background': '#3D3A3E',
    'text': '#0ABAB5'
}

#------------------------------------------------------------------------------------
#add new columns
df = pd.read_json('otodom_full_data', orient = 'split')
df = df[df['price'] != 'Zapytajocenę']
df['price'] = df.price.astype(float)
df['area'] = df.area.astype(float)
df['price/m'] = df['price']/df['area']
df['counts'] = 0

#------------------------------------------------------------------------------------



#------------------------------------------------------------------------------------
#Group dataframe to use in graphs
df1 = df.groupby(['localization','for rent/sale','district']).agg({'localization':'count','price/m':'mean'})\
	.rename(columns={'localization':'count','price/m':'mean price/m'})
df1 = df1.reset_index()
print(df1)
df2 = df.groupby(['district', 'for rent/sale'])['counts'].count()
df2 = df2.reset_index()

df3 = df.groupby(['district', 'for rent/sale'])['counts'].count()
df3 = df3.reset_index()

#------------------------------------------------------------------------------------


#------------------------------------------------------------------------------------
# Page html
app.layout = html.Div([
	
	html.Div(
		
		html.H1('Otodom data analyze'),
		className = 'banner'
	),
	
	dcc.Dropdown(

		id = 'rent/sale',
		options = [
			{'label': 'rent', 'value': 'rent'},
			{'label': 'sale', 'value': 'sale'}],
		multi = False,
		value = 'sale',
		style = {'width': '40%','backgroundColor':colors['background'],'color': colors['text'] }

	),
	html.Div([
		html.Div(

			dcc.Graph(id = 'map'),
			className = 'six columns'
		),

		html.Div(

			dcc.Graph(id = 'graph'),
			className = 'six columns'
		)],
		className = 'row'
	),

	dcc.Graph(id = 'count_city')

])
#------------------------------------------------------------------------------------


@app.callback(
    [Output(component_id='graph', component_property='figure'),
    Output(component_id = 'count_city', component_property = 'figure'),
    Output(component_id = 'map', component_property = 'figure')],
    [Input(component_id='rent/sale', component_property='value')])


def update_graph(option_slctd):

	dff = df1.copy()
	dff = dff[dff['for rent/sale'] == option_slctd]

	dff2 = df2.copy()
	dff2 = dff2[dff2['for rent/sale'] == option_slctd]

	dff3 = df3.copy()
	dff3 = dff3[dff3['for rent/sale'] == option_slctd]

	#------------------------------------------------------------------------------------
	# scatter graph
	fig = px.scatter(dff, x = 'mean price/m', y = 'count', color = 'district',
		hover_name = 'localization',
		labels ={'count': 'number of apartments'})

	fig.update_layout(
		height = 900,
		plot_bgcolor=colors['background'],
		paper_bgcolor=colors['background'],
		font_color=colors['text']
	)
	#------------------------------------------------------------------------------------


	fig2 = px.bar(dff2, x = 'district', y = 'counts',text = 'counts', labels ={'counts': 'number of apartments'})
	fig2.update_traces(textposition='outside')
	fig2.update_layout(uniformtext_minsize=4, uniformtext_mode='hide')

	fig2.update_layout(
		plot_bgcolor=colors['background'],
		paper_bgcolor=colors['background'],
		font_color=colors['text']
	)
	#------------------------------------------------------------------------------------


	#------------------------------------------------------------------------------------
	# Map graph
	fig3 = px.choropleth_mapbox(
		dff3,
		geojson = poland,
		locations = 'district',
		color = 'counts',
		featureidkey='properties.nazwa',
		color_continuous_scale='Cividis',
		range_color = (0,round(dff3['counts'].max(),-2)),
		zoom=6,
		center = {"lat": 52.1127, "lon": 19.2119},
		labels = {'counts': 'number of apartments'}
	)

	fig3.update_layout(mapbox_accesstoken=token,
		mapbox_style='mapbox://styles/lciesluk/ckh6savza1jn719qe0y5lzd4i',
		height = 900, margin = {'r':0, 'l':20, 't':20, 'b':20},
	    plot_bgcolor=colors['background'],
    	paper_bgcolor=colors['background'],
    	font_color=colors['text']
	)
	#------------------------------------------------------------------------------------

	return fig, fig2, fig3

if __name__ == '__main__':
	app.run_server(debug = True)