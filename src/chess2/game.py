from chess2.board import Board
from chess2 import Color, Action
from chess2.gui import GameLoop
import pygame



class Game():
    def __init__(self, in_gui = True, width = 700, height = 800):
        self.board = Board()
        self.gui = GameLoop(width, height, self.board)
        self.turn = Color.WHITE
        self.in_gui = in_gui
        self.action = None

    def start_game(self, ):
        self.board.initialize()
        if not self.in_gui: self.board.print(self.turn)

    def translate_input(self, input_string):
        '''
        könnte man hier noch einfügen um make_move ein bisschen übersichtlicher zu gestalten
        '''
        pass
    

    def swap_turns(self):
        self.turn = Color.BLACK if self.turn == Color.WHITE else Color.WHITE


    def make_move(self):
        move_dict = {
            'a' : 0,
            'b' : 1,
            'c' : 2,
            'd' : 3,
            'e' : 4,
            'f' : 5,
            'g' : 6,
            'h' : 7,
            '1' : 0,
            '2' : 1,
            '3' : 2,
            '4' : 3,
            '5' : 4,
            '6' : 5,
            '7' : 6,
            '8' : 7
        }

        while True:
            move_str = input("Encode your move coordinates like this: a2a4 and press Enter when you are done\n")

            if move_str == "quit":
                return False
            
            if len(move_str) == 4:
                try:
                    x_old, y_old = move_dict[move_str[0]], move_dict[move_str[1]]
                    new_pos = move_dict[move_str[2]], move_dict[move_str[3]]
                except:
                    print("Not the right format")
                    continue
            else:
                print("Not the right format")
                continue

            if not self.board.grid[y_old][x_old] == None:
                if self.board.grid[y_old][x_old]._color == self.turn:
                    if new_pos in self.board.grid[y_old][x_old].get_legal_moves(): # eigentlich muss ich das hier nicht mehr checken, da ich das schon in der move() function der Piece Klasse checke
                        self.board.grid[y_old][x_old].move(new_pos)
                        break

            print('Not a legal move')

        return True
        

    def game_loop_terminal(self):
        self.start_game()
        while True:
            go_on = self.make_move()
            if not go_on:
                print("Game Quit")
                break
            self.board.update_grid()
            self.board.update_checks()
            self.swap_turns()
            self.board.print(self.turn)
            if self.board.check_if_mate(self.turn): 
                winning_color = Color.BLACK if self.turn == Color.WHITE else Color.WHITE
                print(f"Check Mate! {winning_color.name} won!")
                break

    def game_loop_gui(self):
        self.start_game()
        while True:
            action = self.gui.gameloop(turn = self.turn, side = self.turn)
            if action == Action.MOVED:
                # self.board.update_grid()
                self.board.update_checks()
                self.swap_turns()
                if self.board.check_if_mate(self.turn):
                    winning_color = Color.BLACK if self.turn == Color.WHITE else Color.WHITE
                    print(f"Check Mate! {winning_color.name} won!")
                    pygame.quit()
                    raise SystemExit
            self.gui.tick(60)
