from random import randint, choice
from time import sleep


class BoardOutException(Exception):
    def __str__(self):
        return ("Координаты выходят"
                " за диапазоны игрового поля")


class BoardUsedException(Exception):
    def __str__(self):
        return "Эта клетка уже была расстреляна"


class BoardShipException(Exception):
    pass


class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Ship:
    def __init__(self, point_bow, length, orientation_vertical):
        self.point_bow = point_bow
        self.length = length
        self.orientation_vertical = orientation_vertical
        self.lives = length

    @property
    def dots(self):
        # возвращает список всех точек корабля.
        dots_ship = []
        for i in range(self.length):
            curr_x = self.point_bow.x
            curr_y = self.point_bow.y
            if self.orientation_vertical:
                curr_y += i
            else:
                curr_x += i
            dots_ship.append(Dot(curr_x, curr_y))
        return dots_ship

    def is_hit(self, dot):
        return dot in self.dots


class Board:
    def __init__(self, size, hid=False):
        self.size = size
        self.hid = hid
        self.field = [['O'] * size for _ in range(size)]
        self.busy = []
        self.ships = []
        self.last_hit = []
        self.count_destr_ships = 0

    def contour(self, ship, visible=False):
        # Метод, который обводит корабль по контуру.
        around = [(i, j) for i in range(-1, 2) for j in range(-1, 2)]
        for dot in ship.dots:
            for dx, dy in around:
                curr_dot = Dot(dot.x + dx, dot.y + dy)
                if not self.out(curr_dot) and curr_dot not in self.busy:
                    if visible:      # видимость контура
                        self.field[curr_dot.x][curr_dot.y] = '.'
                    self.busy.append(curr_dot)

    def add_ship(self, ship):
        # Метод который ставит корабль на доску
        for d in ship.dots:
            if d in self.busy or self.out(d):
                raise BoardShipException()
        for d in ship.dots:
            self.field[d.x][d.y] = '■'
            self.busy.append(d)
        self.ships.append(ship)
        self.contour(ship)

    def out(self, dot):
        # Метод, который для точки (объекта класса Dot) возвращает True,
        # если точка выходит за пределы поля, и False, если не выходит.
        return not (0 <= dot.x < self.size and 0 <= dot.y < self.size)

    def shot(self, dot):
        # Метод, который делает выстрел по доске (если есть попытка выстрелить
        # за пределы и в использованную точку, нужно выбрасывать исключения).
        if dot in self.busy:
            raise BoardUsedException()
        if self.out(dot):
            raise BoardOutException(dot.x, dot.y)
        self.busy.append(dot)
        for ship in self.ships:
            if ship.is_hit(dot):
                self.field[dot.x][dot.y] = 'X'
                print('Попадание!')
                ship.lives -= 1
                if ship.lives == 0:
                    self.count_destr_ships += 1
                    self.contour(ship, visible=True)
                    print('Корабль уничтожен!')
                    self.last_hit = []
                    return False
                else:
                    print('Корабль ранен!')
                    self.last_hit.append(dot)
                    return True
        self.field[dot.x][dot.y] = '.'
        print('Мимо!')
        return False

    def begin(self):
        self.busy = []

    def defeat(self):
        return self.count_destr_ships == len(self.ships)

    def __str__(self):
        res = '  | ' + ' | '.join(map(str, range(1, self.size + 1))) + ' |'
        for i, row in enumerate(self.field):
            res += f'\n{i + 1} | ' + ' | '.join(row) + ' |'
        if self.hid:
            res = res.replace('■', 'O')
        return res


class Player:
    def __init__(self, board, opponent):
        self.board = board
        self.opponent = opponent

    def ask(self):
        # метод, который «спрашивает» игрока, в какую клетку он делает выстрел.
        while True:
            try:
                x = int(input("Введите координату x: "))
                y = int(input("Введите координату y: "))
                return Dot(x, y)
            except Exception:
                print("Неверный формат координат")

    def move(self):
        # метод, который делает ход в игре.
        while True:
            try:
                coordinates = self.ask()
                repeat = self.opponent.shot(coordinates)
                sleep(2)
                return repeat
            except BoardOutException as e:
                print(f"Ошибка: {e}")


class AI(Player):
    def ask(self):
        last = self.opponent.last_hit
        while True:
            if last:
                if len(last) == 1:
                    near = ((0, 1), (0, -1), (1, 0), (-1, 0))
                else:
                    if last[0].x == last[-1].x:
                        near = ((0, 1), (0, -1))
                    else:
                        near = ((1, 0), (-1, 0))
                dx, dy = choice(near)
                d = choice((Dot(last[-1].x + dx, last[-1].y + dy),
                           Dot(last[0].x + dx, last[0].y + dy)))
            else:
                d = Dot(randint(0, 5), randint(0, 5))
            if d not in self.opponent.busy and not self.opponent.out(d):
                break
        sleep(0.1 * randint(15, 50))
        print(f'Ход компьютера: {d.x + 1} {d.y + 1}')
        return d


class User(Player):
    def ask(self):
        while True:
            coords = input('Введите координаты выстрела:\t').split()
            if len(coords) != 2:
                print('Введите 2 координаты')
                continue
            x, y = coords
            if not all((x.isdigit(), y.isdigit())):
                print('Координаты должны быть числами')
                continue
            return Dot(int(x) - 1, int(y) - 1)


class Game:
    def __init__(self, size=6):
        self.lens = (3, 2, 2, 1, 1, 1, 1)
        self.size = size
        ai_board = self.random_board()
        user_board = self.random_board()
        ai_board.hid = True

        self.ai = AI(ai_board, user_board)
        self.pl = User(user_board, ai_board)

    def generate_board(self):
        attempts = 0
        board = Board(size=self.size)
        for len in self.lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None
                ship = Ship(Dot(randint(0, self.size), (randint(0,
                                self.size))), len, bool(randint(0, 1)))
                try:
                    board.add_ship(ship)
                    break
                except BoardShipException:
                    pass
        board.begin()
        return board

    def random_board(self):
        # метод генерирует случайную доску.
        board = None
        while board is None:
            board = self.generate_board()
        return board

    @staticmethod
    def greet():
        # метод, который в консоли приветствует пользователя
        #  и рассказывает о формате ввода.
        print("Добро пожаловать в игру Морской Бой!")
        print("Формат ввода координат: [строка][столбец] (например, 1 3)")

    def print_boards(self):  # вывод двух досок рядом по горизонтали
        print('-' * self.size * 10)
        print('Ваша доска:'.ljust((self.size + 1) * 4 - 1)
              + ' ' * self.size + 'Доска компьютера:')
        for s1, s2 in zip(self.pl.board.__str__().split('\n'),
                          self.ai.board.__str__().split('\n')):
            print(s1 + ' ' * self.size + s2)

    def loop(self):
        step = 0
        while True:
            self.print_boards()
            if step % 2 == 0:
                print('Ваш ход!')
                repeat = self.pl.move()
            else:
                print('Ходит компьютер!')
                repeat = self.ai.move()
            if repeat:
                step -= 1

            if self.ai.board.defeat():
                self.print_boards()
                print('Вы выиграли!')
                break
            if self.pl.board.defeat():
                self.print_boards()
                print('Компьютер выиграл!')
                break
            step += 1

    def start(self):
        self.greet()
        self.loop()


g = Game()
g.start()
