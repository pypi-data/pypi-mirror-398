# BobrTools

---

## Содержание

- [Установка](#установка)
- [Переменные окружения](#переменные-окружения)
- [GoogleDocs](#класс-googledocs)
  - [get_dataframe](#метод-get_dataframe)
  - [write_dataframe](#метод-write_dataframe)
  - [write_dataframes](#метод-write_dataframes)
- [SnowflakeConnector](#класс-snowflakeconnector)
  - [upload_dataframe](#метод-upload_dataframe)
  - [get_dataframe](#метод-get_dataframe)
- [TelegramClient](#класс-telegramclient)
  - [send_message](#метод-send_message)
- [SlackClient](#класс-slackclient)
  - [send_message](#метод-send_message-1)
- [Обновление библиотеки](#обновление-библиотеки)


---

## Установка

Установить библиотеку можно с помощью pip:

```bash
pip install BobrTools
```

## Переменные окружения

Перед использованием библиотеки необходимо настроить следующие переменные окружения:

- **SNOWFLAKE_USER**: Ваше имя пользователя для Snowflake.
- **SNOWFLAKE_PASSWORD**: Ваш пароль для Snowflake.
- **SNOWFLAKE_ACCOUNT**: Идентификатор вашего аккаунта в Snowflake.
- **SNOWFLAKE_ROLE**: Роль для использования в Snowflake.
- **SNOWFLAKE_WAREHOUSE**: Склад данных (warehouse) для Snowflake.
- **SNOWFLAKE_DATABASE**: База данных для Snowflake.
- **SNOWFLAKE_SCHEMA**: Схема для Snowflake.
- **PROXY_HOST**: Хост прокси-сервера (если используется).
- **PROXY_PORT**: Порт прокси-сервера (если используется).
- **PROXY_USERNAME**: Имя пользователя прокси (если используется).
- **PROXY_PASSWORD**: Пароль прокси (если используется).
- **SNOWFLAKE_USER**: Ваше имя пользователя для Snowflake.
- **TELEGRAM_BOT_TOKEN**: Токен вашего бота Telegram для отправки сообщений.

После того как эти переменные будут настроены, библиотека будет автоматически их использовать, и нет необходимости прописывать их в коде.

---

## Класс GoogleDocs

#### Параметры:
- **`keyfile`** (str, необязательный, по умолчанию `None`): Путь к файлу JSON, содержащему учетные данные сервисного аккаунта Google API. Если параметр не передан, используется значение по умолчанию `./credentials.json`.

### Метод `get_dataframe`

Метод для получения данных из Google Таблицы и преобразования их в pandas DataFrame.

#### Параметры:
- **`spreadsheet_key`** (str, обязательный): Идентификатор Google Spreadsheet, который можно найти в URL таблицы.
- **`worksheet_index`** (int, необязательный, по умолчанию 0): Индекс листа в таблице (начинается с 0).
- **`worksheet_title`** (str, необязательный, по умолчанию None): Заголовок листа. Если задан, он будет использован вместо индекса для поиска листа.

#### Пример использования:
```python
docs = GoogleDocs()

df = docs.get_dataframe(
    spreadsheet_key="1A580_BbPyrhWLrbAq0342EmPqipDhqSFGQFx4TWvX56", 
    worksheet_title="Выгрузка"
)
print(df)
```

### Метод `write_dataframe`

Метод для записи pandas DataFrame в Google Таблицу.

#### Параметры:
- **`dataframe`** (pd.DataFrame, обязательный): Данные, которые нужно записать в Google Таблицу. Это объект pandas DataFrame, который будет преобразован в таблицу.
- **`worksheet_title`** (str, обязательный): Заголовок листа, в который будет записан DataFrame. Если лист с таким заголовком уже существует, он будет перезаписан, иначе будет создан новый лист с таким именем.
- **`default_dataframe_formatting`** (bool, необязательный, по умолчанию False): Если True, то данные на листе будут отформатированы. Это включает в себя заморозку первой строки (с заголовками столбцов).
- **`spreadsheet_key`** (str, необязательный, по умолчанию None): Идентификатор Google Spreadsheet. Если не указан, будет создан новый документ.

#### Пример использования:
```python
docs = GoogleDocs()

df = pd.DataFrame({'Column1': [1, 2, 3], 'Column2': ['A', 'B', 'C']})
docs.write_dataframe(
    dataframe=df, 
    worksheet_title="Sheet1", 
    default_dataframe_formatting=True, 
    spreadsheet_key="1A580_BbPyrhWLrbAq0342EmPqipDhqSFGQFx4TWvX56"
)
```

### Метод `write_dataframes`

Метод для записи нескольких pandas DataFrame в Google Таблицу.

#### Параметры:
- **`dataframes`** (Dict[str, pd.DataFrame], обязательный): Словарь, где ключ – название листа, а значение – соответствующий pandas DataFrame, который будет записан в этот лист.
- **`spreadsheet_key`** (str, необязательный, по умолчанию `None`): Идентификатор Google Spreadsheet, в который будут записаны данные. Если не указан, будет создан новый документ.
- **`spreadsheet_title`** (str, необязательный, по умолчанию `None`): Заголовок Google Spreadsheet, используемый при создании нового документа.
- **`folder_id`** (str, необязательный, по умолчанию `None`): Идентификатор папки на Google Диске, в которую будет сохранён новый документ.
- **`default_dataframe_formatting`** (bool, необязательный, по умолчанию `False`): Если True, к каждому DataFrame будет применено форматирование по умолчанию (например, заморозка первой строки с заголовками).
- **`drop_existing_sheets`** (bool, необязательный, по умолчанию `True`): Если True, из документа будут удалены все листы, имена которых отсутствуют среди ключей словаря `dataframes`.

#### Пример использования:
```python
docs = GoogleDocs()

df = pd.DataFrame({'Column1': [1, 2, 3], 'Column2': ['A', 'B', 'C']})
docs.write_dataframe(
    dataframe=df, 
    worksheet_title="Sheet1", 
    default_dataframe_formatting=True, 
    spreadsheet_key="1A580_BbPyrhWLrbAq0342EmPqipDhqSFGQFx4TWvX56"
)
```

---

## Класс SnowflakeConnector

### Метод `upload_dataframe`

Метод для загрузки pandas DataFrame в таблицу Snowflake.

#### Параметры:
- **`dataframe`** (pd.DataFrame, обязательный): pandas DataFrame, который нужно загрузить.
- **`table_name`** (str, обязательный): Имя таблицы в Snowflake, в которую будут загружены данные.
- **`overwrite`** (bool, необязательный, по умолчанию True): Если True, то таблица будет перезаписана, если она существует.
- **`auto_create_table`** (bool, необязательный, по умолчанию True): Если True, то таблица будет автоматически создана, если не существует.
- **`warehouse`** (str, необязательный, по умолчанию None): Имя склада данных для подключения. Если не указано, будет использовано значение из окруженной переменной `SNOWFLAKE_WAREHOUSE`.
- **`database`** (str, необязательный, по умолчанию None): Имя базы данных для подключения. Если не указано, будет использовано значение из окруженной переменной `SNOWFLAKE_DATABASE`.
- **`schema`** (str, необязательный, по умолчанию None): Имя схемы для подключения. Если не указано, будет использовано значение из окруженной переменной `SNOWFLAKE_SCHEMA`.

#### Пример использования:
```python
snowflake = SnowflakeConnector()

data = pd.DataFrame({'Column1': [1, 2, 3], 'Column2': ['A', 'B', 'C']})
snowflake.upload_dataframe(
    data, 
    table_name="my_table", 
    overwrite=True, 
    auto_create_table=True
)
```

### Метод `get_dataframe`

Метод для выполнения SQL-запроса в Snowflake и преобразования результата в pandas DataFrame.

#### Параметры:
- **`query`** (str, обязательный): SQL-запрос для получения данных. Можно передавать набор разделенных `;`
- **`warehouse`** (str, необязательный, по умолчанию None): Имя склада данных для подключения. Если не указано, будет использовано значение из окруженной переменной `SNOWFLAKE_WAREHOUSE`.
- **`database`** (str, необязательный, по умолчанию None): Имя базы данных для подключения. Если не указано, будет использовано значение из окруженной переменной `SNOWFLAKE_DATABASE`.
- **`schema`** (str, необязательный, по умолчанию None): Имя схемы для подключения. Если не указано, будет использовано значение из окруженной переменной `SNOWFLAKE_SCHEMA`.

#### Возвращаемое значение:
- **pandas DataFrame**: Результат выполнения SQL-запроса, преобразованный в pandas DataFrame, где имена столбцов соответствуют именам колонок в ответе SQL-запроса.

#### Пример использования:
```python
snowflake = SnowflakeConnector()

query = "USE WAREHOUSE MY_WAREHOUSE; SELECT * FROM my_table"
data = snowflake.get_dataframe(
    query=query
)
print(data)
```


---

## Класс `TelegramClient`

#### Параметры:
- **`token`** (str, необязательный, по умолчанию `None`): Токен бота Telegram. Если параметр не передан, то значение токена будет взято из окруженной переменной `TELEGRAM_BOT_TOKEN`.


### Метод `send_message`

Метод для отправки сообщений в Telegram чат или канал через бота.

#### Параметры:
- **`chat_id`** (int или str, обязательный): Идентификатор чата или канала, куда будет отправлено сообщение. 
- **`text`** (str, обязательный): Текст сообщения, которое будет отправлено в чат.
- **`parse_mode`** (str, необязательный, по умолчанию None): Форматирование текста (например, "HTML" или "Markdown"). Если не указано, то форматирование будет отключено.
- **`disable_notification`** (bool, необязательный, по умолчанию False): Если True, сообщение будет отправлено без уведомления (по умолчанию уведомление будет включено).
- **`max_retries`** (int, необязательный, по умолчанию 5): Максимальное количество попыток отправить сообщение в случае ошибки. Если метод не может отправить сообщение, он попробует повторить отправку до достижения максимального числа попыток.
- **`timeout_delay`** (int, необязательный, по умолчанию 5): Время (в секундах), которое бот будет ожидать перед повторной попыткой отправки сообщения в случае ошибки тайм-аута (например, при временной потере соединения).


#### Пример использования:
```python
telegram = TelegramClient()

await telegram_client.send_message(
    chat_id=-1002181072995,
    text="Hello, world!",
    parse_mode="HTML",
    disable_notification=True
)
```

---

## Класс `SlackClient`

#### Параметры:
- **`token`** (str, необязательный, по умолчанию `None`): Токен для доступа к Slack API. Если параметр не передан, то значение токена будет взято из окруженной переменной `SLACK_BOT_TOKEN`.

### Метод `send_message`

Метод для отправки сообщения в Slack канал через API.

#### Параметры:
- **`channel`** (str, обязательный): Идентификатор канала, куда будет отправлено сообщение (например, `#general` или ID канала).
- **`text`** (str, обязательный): Текст сообщения, которое будет отправлено.
- **`thread_ts`** (str, необязательный, по умолчанию `None`): Временная метка родительского сообщения для отправки ответа в треде.
- **`parse`** (str, необязательный, по умолчанию `None`): Параметр, определяющий форматирование сообщения).

#### Пример использования:
```python
slack = SlackClient()

slack_client.send_message(
    channel="#general",
    text="Привет, Slack!"
)
```

---

## Обновление библиотеки
Для обновления библиотеки до следующей версии нужно:
1) В файле setup.py указать следующую версию  
2) Для сборки и обновления библиотеки в pypi используйте команды:

```bash

python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/*
```