import tkinter as tk
from tkinter import messagebox
import math
import random
from copy import deepcopy

class TicTacToe:
    def __init__(self):
        self.board = [' '] * 9
        self.current_player = 'X'

    def available_moves(self):
        return [i for i, spot in enumerate(self.board) if spot == ' ']

    def make_move(self, position, player):
        if 0 <= position < len(self.board) and self.board[position] == ' ':
            self.board[position] = player
            return True
        return False

    def unmake_move(self, position):
        self.board[position] = ' '

    def check_winner(self):
        for i in range(0, 9, 3):
            if self.board[i] == self.board[i+1] == self.board[i+2] != ' ':
                return self.board[i]
        for i in range(3):
            if self.board[i] == self.board[i+3] == self.board[i+6] != ' ':
                return self.board[i]
        if self.board[0] == self.board[4] == self.board[8] != ' ':
            return self.board[0]
        if self.board[2] == self.board[4] == self.board[6] != ' ':
            return self.board[2]
        return None

    def is_full(self):
        return ' ' not in self.board

    def get_state(self):
        return tuple(self.board), self.current_player

    def switch_player(self):
        self.current_player = 'O' if self.current_player == 'X' else 'X'

class Node:
    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.children = {}
        self.visits = 0
        self.wins = 0

    def is_fully_expanded(self, game):
        original_board = game.board
        original_player = game.current_player
        game.board = list(self.state[0])
        game.current_player = self.state[1]
        fully_expanded = len(self.children) == len(game.available_moves())
        game.board = original_board
        game.current_player = original_player
        return fully_expanded

class MCTS:
    def __init__(self, game, iterations=1000, exploration_constant=math.sqrt(2)):
        self.game = game
        self.iterations = iterations
        self.exploration_constant = exploration_constant

    def select(self, node):
        original_board = self.game.board
        original_player = self.game.current_player

        self.game.board = list(node.state[0])
        self.game.current_player = node.state[1]

        while not self.game.check_winner() and node.is_fully_expanded(self.game):
            node = self._select_child(node)
            self.game.board = list(node.state[0])
            self.game.current_player = node.state[1]

        self.game.board = original_board
        self.game.current_player = original_player
        return node

    def _select_child(self, node):
        best_child = None
        best_ucb = -float('inf')
        if node.visits == 0:
            return random.choice(list(node.children.values()))

        for child in node.children.values():
            if child.visits == 0:
                return child

            ucb = (child.wins / child.visits) + self.exploration_constant * math.sqrt(math.log(node.visits) / child.visits)
            if ucb > best_ucb:
                best_ucb = ucb
                best_child = child
        return best_child

    def expand(self, node):
        original_board = self.game.board
        original_player = self.game.current_player
        self.game.board = list(node.state[0])
        self.game.current_player = node.state[1]

        available_moves = self.game.available_moves()
        random.shuffle(available_moves)

        expanded_node = None
        for move in available_moves:
            temp_board = list(self.game.board)
            temp_board[move] = self.game.current_player
            new_state_tuple = (tuple(temp_board), 'O' if self.game.current_player == 'X' else 'X')

            if new_state_tuple not in node.children:
                self.game.make_move(move, self.game.current_player)
                new_state = self.game.get_state()
                new_node = Node(new_state, parent=node, move=move)
                node.children[new_state] = new_node
                self.game.unmake_move(move)
                expanded_node = new_node
                break

        self.game.board = original_board
        self.game.current_player = original_player

        return expanded_node

    def simulate(self, game_state_instance):
        simulation_game = deepcopy(game_state_instance)
        current_sim_player = simulation_game.current_player

        while not simulation_game.is_full() and not simulation_game.check_winner():
            possible_moves = simulation_game.available_moves()
            if not possible_moves:
                break
            move = random.choice(possible_moves)
            simulation_game.make_move(move, current_sim_player)
            winner = simulation_game.check_winner()
            if winner:
                return 1 if winner == 'O' else -1
            current_sim_player = 'X' if current_sim_player == 'O' else 'O'

        return 0

    def backpropagate(self, node, result):
        while node is not None:
            node.visits += 1
            if node.parent and node.parent.state[1] == ('O' if result == 1 else 'X' if result == -1 else None) and result != 0:
                node.wins += 1
            node = node.parent

    def run(self):
        root_state = self.game.get_state()
        root_node = Node(root_state)

        for _ in range(self.iterations):
            original_board = self.game.board
            original_player = self.game.current_player
            self.game.board = list(root_state[0])
            self.game.current_player = root_state[1]

            selected_node = self.select(root_node)
            winner = self.game.check_winner()
            is_full = self.game.is_full()

            if winner or is_full:
                simulation_result = 1 if winner == 'O' else -1 if winner == 'X' else 0
                self.backpropagate(selected_node, simulation_result)
            else:
                expanded_node = self.expand(selected_node)
                if expanded_node:
                    sim_original_board = self.game.board
                    sim_original_player = self.game.current_player
                    self.game.board = list(expanded_node.state[0])
                    self.game.current_player = expanded_node.state[1]
                    simulation_result = self.simulate(self.game)
                    self.backpropagate(expanded_node, simulation_result)
                    self.game.board = sim_original_board
                    self.game.current_player = sim_original_player

            self.game.board = original_board
            self.game.current_player = original_player

        best_child = None
        best_win_rate = -1
        for child in root_node.children.values():
            win_rate = child.wins / child.visits if child.visits > 0 else 0
            if win_rate > best_win_rate:
                best_win_rate = win_rate
                best_child = child

        return best_child.move if best_child else None

class TicTacToeGUI:
    def __init__(self, master, mcts_starts=True, mcts_iterations=1000):
        self.master = master
        master.title("Tic Tac Toe (MCTS)")
        self.mcts_starts = mcts_starts
        self.mcts_iterations = mcts_iterations
        self.restart_game()

    def create_widgets(self):
        self.buttons = [None] * 9
        for i in range(9):
            row, col = divmod(i, 3)
            self.buttons[i] = tk.Button(self.master, text=" ", font=('Arial', 40), width=2, height=1,
                                        command=lambda pos=i: self.human_move(pos))
            self.buttons[i].grid(row=row, column=col, padx=5, pady=5)

        restart_button = tk.Button(self.master, text="Restart", font=('Arial', 16), command=self.restart_game)
        restart_button.grid(row=3, column=0, columnspan=3, pady=10)

    def restart_game(self):
        self.game = TicTacToe()
        self.mcts_agent = MCTS(self.game, iterations=self.mcts_iterations)
        self.mcts_player = 'X' if self.mcts_starts else 'O'
        self.human_player = 'O' if self.mcts_starts else 'X'
        self.game_over = False

        # Destroy old widgets if they exist
        for widget in self.master.winfo_children():
            widget.destroy()

        self.create_widgets()

        if self.mcts_starts:
            self.master.after(100, self.mcts_turn)

    def human_move(self, position):
        if not self.game_over and self.game.current_player == self.human_player and self.game.board[position] == ' ':
            if self.game.make_move(position, self.human_player):
                self.buttons[position].config(text=self.human_player)
                winner = self.game.check_winner()
                if winner:
                    self.end_game(winner)
                elif self.game.is_full():
                    self.end_game(None)
                else:
                    self.game.switch_player()
                    self.master.after(100, self.mcts_turn)

    def mcts_turn(self):
        if not self.game_over and self.game.current_player == self.mcts_player:
            self.master.config(cursor="wait")
            move = self.mcts_agent.run()
            self.master.config(cursor="")
            if move is not None and self.game.make_move(move, self.mcts_player):
                self.buttons[move].config(text=self.mcts_player)
                winner = self.game.check_winner()
                if winner:
                    self.end_game(winner)
                elif self.game.is_full():
                    self.end_game(None)
                else:
                    self.game.switch_player()

    def end_game(self, winner):
        self.game_over = True
        if winner:
            messagebox.showinfo("Game Over", f"{winner} wins!")
        else:
            messagebox.showinfo("Game Over", "It's a draw!")

def main():
    root = tk.Tk()
    gui = TicTacToeGUI(root, mcts_starts=True, mcts_iterations=2000)
    root.mainloop()

if __name__ == "__main__":
    main()