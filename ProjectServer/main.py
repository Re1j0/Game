import socket
import sqlite3


def Server_main(username, password, action, record=0):
    # Подключение к базе данных
    conn = sqlite3.connect('users.sqlite')
    cursor = conn.cursor()
    if action == "1":
        # Проверка, существует ли пользователь с таким именем
        cursor.execute('SELECT Username FROM users WHERE Username = ?', (username,))
        if cursor.fetchone():
            print("Ошибка: пользователь с таким именем уже существует.")
            conn.close()
            return False

        # Вставка нового пользователя в таблицу
        try:
            cursor.execute('''
                INSERT INTO users (Username, Password, Record)
                VALUES (?, ?, ?)
                ''', (username, password, 0))  # Record по умолчанию 0

            # Сохранение изменений
            conn.commit()
            print(f"Пользователь {username} успешно зарегистрирован!")
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при регистрации: {e}")
            return False
        finally:
            # Закрытие соединения с базой данных
            conn.close()
    elif action == "2":
        # Поиск пользователя в базе данных
        cursor.execute('''
            SELECT Username, Password FROM users WHERE Username = ?
            ''', (username,))
        user = cursor.fetchone()

        # Закрытие соединения с базой данных
        conn.close()

        # Проверка, существует ли пользователь и совпадает ли пароль
        if user and user[1] == password:
            print(f"Вход выполнен успешно! Добро пожаловать, {username}!")
            return True
        else:
            print("Ошибка: неверное имя пользователя или пароль.")
            return False
    elif action == "3":
        cursor.execute("SELECT record FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        return result[0]
    elif action == "4":
        cursor.execute(
            "UPDATE users SET record = ? WHERE username = ?",
            (record, username)
        )
        conn.commit()
    return False


def start_server(host='127.0.0.1', port=65432):
    # Создаем сокет
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Привязываем сокет к адресу и порту
        server_socket.bind((host, port))
        # Слушаем входящие соединения
        server_socket.listen()
        print(f"Сервер запущен и слушает на {host}:{port}...")
        # Принимаем соединение
        conn, addr = server_socket.accept()
        with conn:
            print(f"Подключен клиент: {addr}")
            while True:
                # Получаем данные от клиента
                data = conn.recv(1024)
                if not data:
                    break
                try:
                    username, password, action, record = data.decode('utf-8').split(";")
                    conn.sendall(f"{Server_main(username, password, action, record)}".encode('utf-8'))
                except:
                    username, password, action = data.decode('utf-8').split(";")
                    conn.sendall(f"{Server_main(username, password, action)}".encode('utf-8'))


if __name__ == "__main__":
    while True:
        try:
            start_server()
        except:
            pass
