import curses
import os
import requests
from copy import deepcopy

class Sudoku():
    def __init__(self, stdscr: curses.window):
        '''Initialize the game and terminal screen'''
        self.stdscr = stdscr # initialize the screen, clearing etc

        curses.noecho() # do not display input
        curses.cbreak() # react to keys instantly without enter
        self.stdscr.keypad(True) # enable special keys, eg arrow keys

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)

        term_size = os.get_terminal_size()
        self.height = term_size.lines
        self.width = term_size.columns

        curses.curs_set(2) # very visible

        req = requests.get("https://sudoku-api.vercel.app/api/dosuku")
        self.initial_board = req.json()["newboard"]["grids"][0]["value"]

        self.board = deepcopy(self.initial_board)

        self.pregame()

        self.init_board()

        end_condition = self.play()
        if end_condition == "quit":
            self.quit_postgame()
        elif end_condition == "win":
            self.win_postgame()

        self._end()

    def _end(self):
        '''End the game, restoring the terminal to normal'''
        curses.echo()
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.curs_set(1)

        curses.endwin()

    def play(self) -> str:
        '''Main game loop. Handles input and checks for win condition. Returns "quit" or "win".'''
        self.stdscr.move(1, 1)

        while True:
            c = self.stdscr.getkey()
            y, x = self.stdscr.getyx()

            if c == "":
                return "quit"
            elif c == "KEY_UP":
                self.try_move(y-1, x, c)
            elif c == "KEY_DOWN":
                self.try_move(y+1, x, c)
            elif c == "KEY_LEFT":
                self.try_move(y, x-1, c)
            elif c == "KEY_RIGHT":
                self.try_move(y, x+1, c)
            elif len(c) == 1 and c.isdigit() and c != "0":
                self.try_place(y, x, c)

                if self.is_completed():
                    return "win"
            elif c in ("KEY_BACKSPACE", "\b", "\x7f"):
                self.try_del(y, x)

    def pregame(self) -> None:
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, "Welcome to Sudoku!\n\nPress ESC to quit. Use arrow keys to move around and enter numbers. Press Backspace to delete a number.\nPress any key to start...")
        self.stdscr.refresh()
        self.stdscr.getch()
        self.stdscr.clear()

    def quit_postgame(self) -> None:
        self.stdscr.addstr(14, 0, "You quit the game. Press any key to exit...")
        self.stdscr.refresh()
        self.stdscr.getch()

    def win_postgame(self) -> None:
        self.stdscr.addstr(14, 0, "You won! Press any key to exit...")
        self.stdscr.refresh()
        self.stdscr.getch()

    def try_move(self, y: int, x: int, dir: str) -> None:
        '''Moves the cursor to y, x if it is a valid location. If the location is a border, skips over the border.'''
        # movement within grid
        if self.is_on_grid(y, x):
            self.stdscr.move(y, x)
        # check direction to skip borders
        elif dir == "KEY_UP" and self.is_on_grid(y-1, x):
            self.stdscr.move(y-1, x)
        elif dir == "KEY_DOWN" and self.is_on_grid(y+1, x):
            self.stdscr.move(y+1, x)
        elif dir == "KEY_LEFT" and self.is_on_grid(y, x-1):
            self.stdscr.move(y, x-1)
        elif dir == "KEY_RIGHT" and self.is_on_grid(y, x+1):
            self.stdscr.move(y, x+1)

    def try_place(self, y: int, x: int, num: str) -> None:
        '''Places the number at y, x if it is a valid location and placement.'''
        if self.is_on_grid(y, x) and not self.is_on_initial(y, x):
            i, j = self.yx_to_ij(y, x)

            this_row = self.board[i]
            this_col = [self.board[k][j] for k in range(9)]
            this_square = [self.board[k][l] for k in range(i//3*3, i//3*3+3) for l in range(j//3*3, j//3*3+3)]

            numint = int(num)

            if numint in this_row or numint in this_col or numint in this_square:
                return

            self.stdscr.addch(y, x, num)
            self.board[i][j] = numint

            self.stdscr.move(y, x) # move cursor back to that position

    def try_del(self, y: int, x: int) -> None:
        '''Deletes the number at y, x if it is not an initial number.'''
        if self.is_on_grid(y, x) and not self.is_on_initial(y, x):
            i, j = self.yx_to_ij(y, x)
            self.stdscr.addch(y, x, " ")
            self.board[i][j] = 0

            self.stdscr.move(y, x)

    def init_board(self) -> None:
        '''Draws the initial board with the initial numbers.'''
        for x in range(1, 12):
            for y in range(1, 12):
                i, j = self.yx_to_ij(y, x)
                if x % 4 == 0:
                    self.stdscr.addch(y, x, "|")
                elif y % 4 == 0:
                    self.stdscr.addch(y, x, "-")
                elif self.initial_board[i][j] != 0:
                    self.stdscr.addch(y, x, str(self.initial_board[i][j]), curses.color_pair(1))
                elif self.board[i][j] != 0:
                    self.stdscr.addch(y, x, str(self.board[i][j]))
        self.stdscr.refresh()

    def is_completed(self, deep_check: bool = True) -> bool:
        '''Checks if the board is completed and correct.
        If proper input validation is given, deep_check may be False.'''
        digits = list(range(1, 10))
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    return False
                else:
                    assert self.board[i][j] in digits

        if deep_check:
            for i in range(9):
                row = set()
                col = set()
                for j in range(9):
                    row.add(self.board[i][j])
                    col.add(self.board[j][i])
                if len(row) != 9 or len(col) != 9 or sum(row) != 45 or sum(col) != 45:
                    return False
                
            for k in range(0, 9, 3):
                for l in range(0, 9, 3):
                    square = set()
                    for i in range(k, k+3):
                        for j in range(l, l+3):
                            square.add(self.board[i][j])
                    if len(square) != 9 or sum(square) != 45:
                        return False
                
        return True

    def is_on_initial(self, y: int, x: int) -> bool:
        '''Checks if y, x is on an initial number on the board.'''
        i, j = self.yx_to_ij(y, x)
        return self.initial_board[i][j] != 0

    def is_on_grid(self, y: int, x: int) -> bool:
        '''Checks if y, x is in a playable location on the grid.'''
        if not self.is_safe_pos(y, x):
            # safe bounds
            return False

        if not 0 <= y <= 12 or not 0 <= x <= 12:
            # board bounds
            return False

        # not on a wall
        return x % 4 != 0 and y % 4 != 0

    def is_safe_pos(self, y: int, x: int) -> bool:
        '''Checks if y, x is within the safe bounds of the terminal.'''
        return 0 <= y <= self.height and 0 <= x <= self.width - 2

    def yx_to_ij(self, y: int, x: int) -> tuple[int]:
        '''Converts y, x screen coordinates to i, j board indexes. If y, x not on grid, returns None, None.'''
        if not self.is_on_grid(y, x):
            return None, None
        return (y-1)-(y//4), (x-1)-(x//4)

def main(stdscr: curses.window):
    sudoku = Sudoku(stdscr)

if __name__ == "__main__":
    stdscr = curses.initscr()
    curses.wrapper(main)
