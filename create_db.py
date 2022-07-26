import psycopg2
import yaml
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


with open('settings.yml') as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)

# Устанавливаем соединение с postgres
connection = psycopg2.connect(user=config['user'], password=config['password]'])
connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

# Создаем курсор для выполнения операций с базой данных
cursor = connection.cursor()
# Создаем базу данных
cursor.execute('create database postgres')
# Закрываем соединение
cursor.close()
connection.close()