#from GameClient import *

#class OXOTextClient(GameClient):

    #def __init__(self):
        #GameClient.__init__(self)
        #self.board = [' '] * BOARD_SIZE
        #self.shape = None
        
    #def clear_board(self):
        #self.board = [' '] * BOARD_SIZE
        
    #def input_server(self):
        #return input('enter server:')
     
    #def input_move(self):
        #return input('enter move(0-8):')
     
    #def input_play_again(self):
        #return input('play again(y/n):')

    #def display_board(self):
        ## implement this method
        #pass
    
    #def handle_message(self,msg):
        ## implement this method
        #pass
    
    #def play_loop(self):
        #while True:
            #msg = self.receive_message()
            #if len(msg): self.handle_message(msg)
            #else: break
            
#def main():
    #otc = OXOTextClient()
    #while True:
        #try:
            #otc.connect_to_server(otc.input_server())
            #break
        #except:
            #print('Error connecting to server!')
    #otc.play_loop()
    #input('Press click to exit.')
        
#main()

from GameClient import *

class OXOTextClient(GameClient):

    def __init__(self):
        GameClient.__init__(self)
        self.board = [' '] * BOARD_SIZE
        self.shape = None
        
    def clear_board(self):
        self.board = [' '] * BOARD_SIZE
        
    def input_server(self):
        return input('enter server:')
     
    def input_move(self):
        return input('your move(0-8):')
     
    def input_play_again(self):
        return input('play again(y/n):')
    
    def display_board(self):# Iterate over the board in rows of 3 (indices 0, 3, 6)
        for i in range(0, 9, 3):
            row = [] # Build each row by checking the 3 cells in this row
            for j in range(3):
                value = self.board[i + j]
                # show position number if cell is empty
                if value == ' ':
                    row.append(str(i + j))
                else: # Otherwise show the player's shape (X or O)
                    row.append(value) # Print the row with cells separated by pipes
            print(' | '.join(row)) # Print a divider after every row except the last
            if i < 6:
                print('-----------')      
        
    def handle_message(self, msg):
        print('Received:', msg)
        # Split the message on commas to extract any additional data
        parts = msg.split(',')

        if parts[0] == 'new game':
            # Assign this client's shape (X or O) from the server message
            self.shape = parts[1]
            print(f"New game started! You are '{self.shape}'")
            # Reset the board and show its initial state
            self.clear_board()
            self.display_board()

        elif msg == 'your move':
            # Prompt the player for their chosen position and send it to the server
            move = self.input_move()
            self.send_message(str(move))

        elif msg == 'opponents move':
            # Server signals it is the opponent's turn to play.... just notify the player
            print('Waiting for your opponent to play...')

        elif parts[0] == 'valid move':
            # format: "valid move,S,P"... place shape S at position P on the board
            # format: "valid move,S,P"
            shape    = parts[1]
            position = int(parts[2])
            self.board[position] = shape
            # Redisplay the board to reflect the new move
            self.display_board()

        elif msg == 'invalid move': # Notify the player their move was rejected and they must try again
            print('Invalid move.Try again.')

        elif parts[0] == 'game over': # Display the final board state before announcing the result
            winner = parts[1]
            self.display_board()
            if winner == 'T': # 'T' indicates a tie/draw, neither player has won the game
                print("It's a draw!")
            elif winner == self.shape: # The winner's shape matches this client's shape
                print('You win!')
            else: # The winner's shape belongs to the opponent
                print('You lose!')

        elif msg == 'play again': # Ask the player if they want another round and relay their answer
            answer = self.input_play_again()
            self.send_message(answer)

        elif msg == 'exit game': #The other player has disconnected, inform this player and close the game
            print('The other player has left. Goodbye.')

        else: # for any unrecognised message types
            print('Unknown message:', msg)
    
    def play_loop(self):
        while True:
            msg = self.receive_message()
            if len(msg): self.handle_message(msg)
            else: break
            
def main():
    otc = OXOTextClient()
    while True:
        try:
            otc.connect_to_server(otc.input_server())
            break
        except:
            print('Error connecting to server!')
    otc.play_loop()
    input('Press click to exit.')
        
main()
