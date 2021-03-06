import curses
import logging

logging.basicConfig(filename='sokoban.log', filemode='a', level=logging.DEBUG)
log = logging.getLogger(__file__)

KEYS = {
    'movement': {
        # vim
        ord('h'): 'left',
        ord('j'): 'down',
        ord('k'): 'up',
        ord('l'): 'right',
        # wasd
        ord('w'): 'up',
        ord('a'): 'left',
        ord('s'): 'down',
        ord('d'): 'right',
        # arrow keys
        259: 'up',
        258: 'down',
        260: 'left',
        261: 'right',
    },
    'quit': ord('q'),
}

CHAR_TO_NAME = {
    '@': 'player',
    '#': 'wall',
    'o': 'box',
    '.': 'slot',
    '*': 'filled',
    ' ': 'space',
}
NAME_TO_CHAR = dict(map(reversed, CHAR_TO_NAME.items()))

class GameMap(object):
    def __init__(self, window):
        self.window = window
        self.map = []
        self.prev_char = 'space'

    def update(self, coord, char_name):
        """
        Updates coordinates with new character.
        """
        x, y = coord
        self.map[y][x] = NAME_TO_CHAR[char_name]

    def get_char(self, coord):
        """
        Returns character at given coordinates.
        """
        x, y = coord
        try:
            return CHAR_TO_NAME[self.map[y][x]]
        except IndexError:
            return None

    @property
    def player_coord(self):
        """
        Returns player's current coord on game map.
        """
        for y, row in enumerate(self.map):
            for x, char in enumerate(row):
                if char == NAME_TO_CHAR['player']:
                    return (x, y)
        else:
            raise Exception, "Error finding player coordition. Make sure there is an @ in your map!"

    def load(self, map_filename):
        """
        Loads map from file.
        """
        try:
            with open(map_filename) as f:
                self.map = [[x for x in y.rstrip()] for y in f if not y.startswith(';')]
        except:
            raise Exception, 'Could not import map'

    def draw(self):
        """
        Draws map.
        """
        for y, row in enumerate(self.map):
            for x, char in enumerate(row):
                self.window.addstr(y, x, char)
                self.window.refresh()

    def next_coord(self, coord, key):
        """
        Returns updated coordinates based on key press.
        """
        return {
            'up':   lambda x, y: (x, y-1),
            'down': lambda x, y: (x, y+1),
            'left': lambda x, y: (x-1, y),
            'right':lambda x, y: (x+1, y),
        }[KEYS['movement'][key]](*coord)

    def move_player(self, key):
        """
        Moves player. Returns new player coord,
        and character previously under new player coord.
        """
        next_coord = self.next_coord(self.player_coord, key)
        next_char = self.get_char(next_coord)

        def box():
            box_coord = self.next_coord(next_coord, key)
            replaced_char = self.get_char(box_coord)
            if replaced_char == 'slot':
                self.update(box_coord, 'filled')
            elif replaced_char == 'space':
                self.update(box_coord, 'box')
            else:
                return invalid_movement()
            self.update(self.player_coord, self.prev_char)
            self.update(next_coord, 'player')
            self.draw()
            if next_char == 'filled':
                self.prev_char = 'slot'
            else:
                self.prev_char = 'space'

        def move():
            self.update(self.player_coord, self.prev_char)
            self.update(next_coord, 'player')
            self.draw()
            self.prev_char = next_char

        def invalid_movement():
            pass

        states = {
            'box': box,
            'filled': box,
            'slot': move,
            'space': move,
        }
        states.get(next_char, invalid_movement)()
        if not filter(lambda x: NAME_TO_CHAR['box'] in x, self.map):
            self.victory()

    def victory(self):
        """
        Draws victory notification
        """
        self.window.erase()
        self.window.addstr('YAY VICTORY')
        self.window.refresh()

class Game(object):
    def __init__(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.curs_set(0)
        self.stdscr.keypad(1)
        curses.raw()
        self.title_win = self.stdscr.subwin(2, 50, 0, 0)
        self.score_win = self.stdscr.subwin(2, 29, 0, 51)
        self.game_win = self.stdscr.subwin(2, 0)
        self.map = GameMap(self.game_win)
        self.score = 0

    def load_map(self, map_name):
        self.map.load(map_name)
        self.map.draw()
        self.update_title('sokoban! map: %s' % map_name)
        self.update_score()

    def update_title(self, title):
        self.score_win.erase()
        self.title_win.addstr(title)
        self.title_win.refresh()

    def update_score(self):
        self.score_win.erase()
        self.score += 1
        self.score_win.addstr('score: %s' % self.score)
        self.score_win.refresh()

    def loop(self):
        log.info("Sokuban has started.")
        self.load_map('test_map')
        try:
            while True:
                key = self.stdscr.getch()
                if key in KEYS['movement']:
                    self.map.move_player(key)
                    self.update_score()
                if key == KEYS['quit']:
                    break
        except Exception:
            log.exception('Exception occured')
        finally:
            self.quit()

    def quit(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

if __name__ == '__main__':
    game = Game()
    game.loop()
