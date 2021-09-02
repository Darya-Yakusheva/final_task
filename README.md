# epam_final_task
Final task in EPAM Python training

## Вариант 7
### Визуализация цен недвижимости

0. Найти (crawling с сайтов недвижимости) актуальную базу данных по стоимости недвижимости в Санкт-Петербурге, Москве, Екатеринбурге

На основе собранных данных сделать следующие виды визуализации:
1. Тепловая карта цен недвижимости. Представляет из себя карту города с наложенным на неё слоем, в котором цветом показана цена недвижимости в пересчёте на квадратный метр.
2. Гистограмма с отображением средних цен по муниципальным округам указанных выше городов
3. Гистограмма с отображением средней площади квартиры по муниципальным округам указанных выше городов

Под визуализацией понимается png картинка с достаточным разрешением. При желании это может быть так же web frontend или оконное приложение.

___

# How to run

1. Clone this repo using terminal (to open it, press `ctrl+alt+T`):
```
git clone https://github.com/Darya-Yakusheva/epam_final_task.git
```
2. Create and activate virtual environment in a created directory:
```
cd epam_final_task
python3 -m venv <your_new_virtual_environment_name>
source <your_new_virtual_environment_name>/bin/activate
```
3. Install requirements and run script "main.py"
```
pip install -r requirements.txt
python3 main.py
```
:+1: now script will run in the terminal. Follow the instructions on the screen.
___

# What does it do
1. Asks a user to input an abbreviation for city he is interested with.
![Main menu](https://user-images.githubusercontent.com/76222596/131891971-f641eb39-f9b0-4602-9543-7f7b27c0853f.png)

2. Once the city is selected, asks a user to choose an action to perform.
![Action choice](https://user-images.githubusercontent.com/76222596/131889513-f1750753-c7d6-437e-989f-ab9d327f9bc2.png)

3. When the action selected, runs corresponding script to either collect data and save it to a database or visualize existing data. After finishing, returns to main menu.
___

### Examples of visualization:
Histograms with average area and average price per district

![Average area](https://user-images.githubusercontent.com/76222596/131889736-0b320462-8683-49cd-9050-9bff73fc632a.png)
![Average price](https://user-images.githubusercontent.com/76222596/131889760-926dd35b-9e53-4c3b-889e-2670172c5b3d.png)

Html page with prices per meter visualization on a city map.
Not actually a heatmap, but yet allows to see prices levels for different locations due to different colors of circles.
![Prices on map](https://user-images.githubusercontent.com/76222596/131889849-aa25ab22-0655-4f43-8cf2-137a3d3fd7f1.png)

