'''
this module handles metadata, like checkmate, or which player is to turn and implements the final game loop
'''


from chess2.board import Board
from chess2 import Color, Action
from chess2.gui import GameLoop
from chess2.move import Move
import pygame
import time



class Game():
    def __init__(self, in_gui = True, width = 700, height = 800):
        self.board = Board()
        self.gui = GameLoop(width, height, self.board, self.on_undo, self.on_redo)
        self.move = Move()
        self.in_gui = in_gui
        self.action = None


    def start_game(self, ):
        self.board.initialize()
        if not self.in_gui: self.board.print(self.board.turn)
    

    def swap_turns(self, turn_board):
        if turn_board: time.sleep(0.5)
        self.board.turn = Color.BLACK if self.board.turn == Color.WHITE else Color.WHITE


    def translate_input(self, input_string):
        '''
        könnte man hier noch einfügen um make_move ein bisschen übersichtlicher zu gestalten
        '''
        pass


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
                if self.board.grid[y_old][x_old]._color == self.board.turn:
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
            self.board.print(self.board.turn)
            if self.board.check_if_mate(): 
                winning_color = Color.BLACK if self.board.turn == Color.WHITE else Color.WHITE
                print(f"Check Mate! {winning_color.name} won!")
                break
    

    def on_undo(self):
        print("self.board.load_state(self.move.cached_boards[self.move.move-1])")


    def on_redo(self):
        print("self.board.load_state(self.move.cached_boards[self.move.move+1])")


    def game_loop_gui(self, turn_board, show_legal_moves, side = Color.WHITE):
        self.start_game()
        self.move.cache_board_state(self.board)

        while True:
            action = self.gui.gameloop(turn = self.board.turn, side = self.board.turn if turn_board else side, show_legal_moves = show_legal_moves)

            if action == Action.MOVED:
                self.swap_turns(turn_board)
                self.move.cache_board_state(self.board)
                if self.board.check_if_mate():
                    winning_color = Color.BLACK if self.board.turn == Color.WHITE else Color.WHITE
                    print(f"Check Mate! {winning_color.name} won!")
                    pygame.quit()
                    raise SystemExit

            self.gui.tick(60)
