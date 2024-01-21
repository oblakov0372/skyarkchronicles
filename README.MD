# Софт для [skyarkchronicles](https://skygate.skyarkchronicles.com/)

## [Telegram](https://t.me/CryptoOblakov_0372)

## Если вдруг кто-то захочет порадовать меня копеечкой): 0x5149Ae7F9445E70331608EA03C592c078aE7399D(кошель новый)EVM

### Шаг1: Скачиваем проект

### Шаг 2: Перейдите в директорию проекта.

```bash
cd "путь_к_софту"
```

### Шаг 3: Установите зависимости.

```bash
pip install -r requirements.txt
```

### Шаг 4: В папке account создайте два файла private_keys.txt,proxies.txt

```
privatekey1
privatekey2
privatekey3
...
```

Формат прокси http://login:password@ip:port

```
http://login:password@ip:port
http://login:password@ip:port
http://login:password@ip:port
...
```

### Шаг 5: Изменение конфига

```python
# Кошель на который будут капать рефки
REFER_WALLET = ''

# Сон между активностями и попытками
SLEEP_RANGE = range(3, 6)

# Количество одновременных потоков
NUMBER_OF_THREADS = 10
```

### Шаг 6: Запуск

```bash
py main.py
```

### Выбираем действие

```bash
Select the option:
1) Register and daily check in
2) Daily check in
3) Get the number of points
4) Exploration transaction
```

Вводим цифру нажимаем enter.
После выполнения активности база данных изменяется.

### База данных json в папке `status` файл `data.json`

Вот такой у нее формат

```json
{
  "0x0000000000000000000000000000000000000000": {
    "proxy": "http://login:password@ip:port",
    "useragent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "last_check_in": "2024-01-21",
    "jwt": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1SWQiOiIyNjExOTg0MiIsInVXYWxsZXRBZGRyIjoiMHgwMDM1OGM5MjEyYTk0M2E4MDI4MjNlYjAyOTU4ZGVhNDc5NGMwNGqweqw.dwqwdsqwed-KSkbrVqqH-U6duIjvWCNETivp8srzX_7VaIvW9egIS4s4C0p2tMJrIXoIc6kapeJKYwXI2gmY3MY_C8-KZF2a83bUakmEk2fVDu_AbkRJOaBdv7jFefrPEFdHHY5l4pH2jRrQnSo0qSIai09FpArYHeQGKJmMsUg",
    "points": "110",
    "last_exploration": "2024-01-21"
  }
}
```
