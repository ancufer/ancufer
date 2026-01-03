# Функция для отрисовки игрового поля
def print_board(board):
    print("-" * 13)
    for row in board:
        # Форматируем строку: заменяем None на пробелы, красиво разделяем символы
        row_display = [cell if cell is not None else ' ' for cell in row]
        print(f"| {row_display[0]} | {row_display[1]} | {row_display[2]} |")
        print("-" * 13)


# Функция для проверки наличия победителя
def check_winner(board, player):
    # Проверка строк
    for row in board:
        if all(cell == player for cell in row):
            return True
    # Проверка столбцов
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True
    # Проверка диагоналей
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True
    return False


# Функция для проверки, заполнено ли поле (ничья)
def is_board_full(board):
    for row in board:
        for cell in row:
            if cell is None:
                return False
    return True


# Основная функция игры
def play_game():
    # Инициализация поля 3x3 (None означает пустую клетку)
    board = [[None, None, None],
             [None, None, None],
             [None, None, None]]

    current_player = 'X'  # Первым ходит 'X'
    game_over = False

    print("Добро пожаловать в игру 'Крестики-нолики'!")
    print("Для хода введите номер строки (0, 1, 2) и номер столбца (0, 1, 2) через пробел.")
    print("Пример: '1 2' — это вторая строка, третий столбец.\n")

    print_board(board)

    while not game_over:
        try:
            # Получаем ход от игрока
            move = input(f"Ход игрока {current_player}: ").split()
            if len(move) != 2:
                print("Ошибка! Нужно ввести ДВА числа через пробел.")
                continue

            row, col = int(move[0]), int(move[1])

            # Проверяем, что координаты в пределах поля
            if row < 0 or row > 2 or col < 0 or col > 2:
                print("Ошибка! Числа должны быть от 0 до 2.")
                continue

            # Проверяем, свободна ли клетка
            if board[row][col] is not None:
                print("Эта клетка уже занята! Выберите другую.")
                continue

            # Делаем ход
            board[row][col] = current_player
            print_board(board)

            # Проверяем, выиграл ли текущий игрок
            if check_winner(board, current_player):
                print(f"Поздравляем! Игрок {current_player} победил!")
                game_over = True
            # Проверяем, наступила ли ничья
            elif is_board_full(board):
                print("Ничья! Поле полностью заполнено.")
                game_over = True
            else:
                # Меняем игрока
                current_player = 'O' if current_player == 'X' else 'X'

        except ValueError:
            print("Ошибка! Пожалуйста, вводите только числа.")
        except KeyboardInterrupt:
            print("\nИгра прервана. До свидания!")
            break
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")


# Запуск игры
if __name__ == "__main__":
    play_game()