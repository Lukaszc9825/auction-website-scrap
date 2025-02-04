import grequests
import json
from bs4 import BeautifulSoup as bs
from Otodom_scraper import Scraper
from Otodom_scraper import Json_file
import pandas as pd

df1 = pd.read_json('otodom_rent_data')
df2 = pd.read_json('otodom_sale_data')

#read data with all districts in Poland and delete useless columns
districts = pd.read_excel('districts.xlsx')
districts = districts.drop(columns = ['Gmina', 'Województwo',
 'Identyfikator miejscowości z krajowego rejestru urzędowego podziału terytorialnego kraju TERYT','Dopełniacz','Przymiotnik'])


# add new columns and clear data from trash characters
def add_column(*args):
	for arg in args:
		arg_temp = arg.copy()
		# arg['Rent'] = 'no data'
		# arg['Deposit'] = 'no data'
		# arg['Number of rooms'] = 'no data'
		# arg['built in'] = 'no data'
		# arg['floor'] = 'no data'
		# arg['number of floors'] = 'no data'
		arg['price'] = arg['price'].str.replace('zł', '').str.replace(',', '.').str.replace(' ','').str.replace('~','')
		arg['area'] = arg['area'].str.replace('m²', '').str.replace(',','.').str.replace(' ','')
		arg['localization'] = arg_temp['localization'].str.split(',',expand = True)[0]
		arg['localization 1'] = arg_temp['localization'].str.split(',',expand = True)[1]
		arg['localization 2'] = arg_temp['localization'].str.split(',',expand = True)[2]
		arg['district'] = add_district(arg)
		arg = arg.reset_index()


# add columns with district population and area
def add_pop_data(data):

	pop = pd.read_excel('population.xlsx')
	pop = pop.rename(columns = {'Powiat':'district','Powierzchnia [km²]': 'area of district','Liczba ludności [osoby]':'population' })

	# somoe of the districts dont have "Powiat" in name so this loop add this word
	for i, p in enumerate(pop['district']):
		if p.split(' ')[0] != 'powiat':
			
			pop.at[i,'district'] = 'powiat ' + p

	# change data type and add some extra columns
	df = data
	df = df[df['price'] != 'Zapytajocenę']
	df = df.reset_index()
	df['price'] = df.price.astype(float)
	df['area'] = df.area.astype(float)
	df['price/m'] = df['price']/df['area']
	df['counts'] = 0
	df['population'] = 0
	df['area of district'] = 0

	# add values with population and area of districts
	for i, dis in enumerate(df['district']):

		if pop[pop['district'] == dis].empty == False:
			temp = pop[pop['district'] == dis]
			temp = temp.groupby(['district']).agg({'population': 'sum', 'area of district': 'sum'})
			temp = temp.reset_index()
			df.at[i,'population'] = temp.iloc[0]['population']
			df.at[i,'area of district'] = temp.iloc[0]['area of district']

	return df


# Now i don't use this function
# It make request for every single advertisment to scrap more accurate data 
# for exaple number of rooms, floor, year of build
# It's over 100 000 request so it takes some time 		
def find_data(*args):
	for arg in args:

		reqs = [grequests.get(url,headers=headers) for url in arg['href']]
		resp = grequests.map(reqs, size =10)

		for index, r in enumerate(resp):
			print(r)
			soup = bs(r.content, 'html.parser')
			mess = soup.find_all(class_ ='section-overview')
			for m in mess:
				data = m.find('ul')
				data = data.find_all('li')
				temp = {}
				for d in data:
					temp[d.get_text().split(":")[0]] = d.get_text().split(":")[1].strip()
	      
				# add rent price to data frame
				if 'Czynsz - dodatkowo' in temp:
					arg.at[index,'Rent'] = "+" + temp.get('Czynsz - dodatkowo')
				elif 'Czynsz' in temp:
					arg.at[index,'Rent'] = temp.get('Czynsz')
				elif 'Czynsz - dodatkowo' in temp == False and 'Czynsz' in temp == False:
					arg.at[index,'Rent'] = 0
	      
				# add deposit to data frame
				if 'Kaucja' in temp:
					arg.at[index,'Deposit'] = temp.get('Kaucja')
				elif 'Kaucja' in temp == False:
					arg.at[index,'Deposit'] = 0
	      
				# add number of rooms to data frame
				if 'Liczba pokoi' in temp:
					arg.at[index,'Number of rooms'] = temp.get('Liczba pokoi')
				elif 'Liczba pokoi' in temp == False:
					arg.at[index,'Number of rooms'] = 0

				# add year of building to data frame
				if 'Rok budowy' in temp:
					arg.at[index,'built in'] = temp.get('Rok budowy')
				elif 'Rok budowy' in temp == False:
					arg.at[index,'built in'] = 0

				# add floor to data frame
				if 'Piętro' in temp:
					if temp.get('Piętro') == 'parter':
						arg.at[index,'floor'] = '0'
					else:
						arg.at[index,'floor'] = temp.get('Piętro')
				elif 'Piętro' in temp == False:
					arg.at[index,'floor'] = 'no data'

				# add number of floors to data frame
				if 'Liczba pięter' in temp:
					arg.at[index,'number of floors'] = temp.get('Liczba pięter')
				elif 'Liczba pięter' in temp == False:
					arg.at[index,'number of floors'] = 0


# It add district to each location
# I have to make an improvement of this because of a lot of time needed to done
def add_district(df):
	temp =[]
	for city in df['localization']:

		if districts.loc[(districts['Nazwa miejscowości '] == city) & (districts['Rodzaj'] == 'miasto')].empty ==  False:
			d = districts.loc[(districts['Nazwa miejscowości '] == city) & (districts['Rodzaj'] == 'miasto')]
			temp.append('powiat ' + d.iloc[0]['Powiat (miasto na prawach powiatu)'])
		
		elif districts.loc[(districts['Nazwa miejscowości '] == city) & (districts['Rodzaj'] == 'wieś')].empty ==  False:
			d = districts.loc[(districts['Nazwa miejscowości '] == city) & (districts['Rodzaj'] == 'wieś')]
			temp.append('powiat ' + d.iloc[0]['Powiat (miasto na prawach powiatu)'])

		elif districts.loc[(districts['Nazwa miejscowości '] == city) & (districts['Rodzaj'] == 'osada')].empty ==  False:
			d = districts.loc[(districts['Nazwa miejscowości '] == city) & (districts['Rodzaj'] == 'osada')]
			temp.append('powiat ' + d.iloc[0]['Powiat (miasto na prawach powiatu)'])

		elif districts.loc[(districts['Nazwa miejscowości '] == city) & (districts['Rodzaj'] == 'kolonia')].empty ==  False:
			d = districts.loc[(districts['Nazwa miejscowości '] == city) & (districts['Rodzaj'] == 'kolonia')]
			temp.append('powiat ' + d.iloc[0]['Powiat (miasto na prawach powiatu)'])

		elif city == 'Stargard':
			temp.append('powiat stargardzki')

		else:
			d = districts.loc[(districts['Nazwa miejscowości '] == city)]
			temp.append('powiat ' + d.iloc[0]['Powiat (miasto na prawach powiatu)'])

	return temp


if __name__ == '__main__':

	url1 = 'https://www.otodom.pl/wynajem/'
	url2 = 'https://www.otodom.pl/sprzedaz/'
	headers = {"User-Agent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
	(KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'}

	scraper1 = Scraper(url1, headers)
	scraper2 = Scraper(url2, headers)
	j = Json_file()
	j.save("otodom_rent_data", scraper1.apartments_list)
	j.save("otodom_sale_data", scraper2.apartments_list)

	add_column(df1,df2)
	# find_data(df1,df2)
	df3 = pd.concat([df1, df2], ignore_index=True)
	df3 = add_pop_data(df3)
	df3.to_json('otodom_full_data', orient= 'split')