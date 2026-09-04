import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class OXOGUIClient(QWidget):
    def __init__(self): #Initialise the GUI window and all widgets
        QWidget.__init__(self)
        self.setWindowTitle("OXO Game") #Setting window title to OXO Game
        #self.setFixedSize(590, 800)
        self.setGeometry(200, 100, 590, 800) #Using setGeometry to set the size of the window to be able to be resized
        #self.setStyleSheet("background-color")
        self.setStyleSheet("background-color") #This sets the background but no colour yet since this is still a prototype
        self.shape = None # This defines and stores the player's shape (X OR O)


        QLabel("Enter server:", self).setGeometry(20, 20, 70, 25) #This is for the server label for the server input field

        self.input = QLineEdit(self) # This is for the input text field
        self.input.setGeometry(90, 20, 190, 25)
        self.input.setPlaceholderText("e.g. 127.0.0.1") #This is for giving the players at least least a hint of what kind of tet they should put in.
        
       # The connect button is created to make connection to server
        self.connect_button = QPushButton("Connect", self)
        self.connect_button.setGeometry(290, 18, 100, 28)
        self.connect_button.clicked.connect(self.on_connect) # This links to the handler
        
        #The disconnect button is created to terminate connection to the server
        self.disconnect_button = QPushButton("Disconnect", self)
        self.disconnect_button.setGeometry(400, 18, 110, 28)
        self.disconnect_button.clicked.connect(self.on_disconnect)

        # welcome message labels
        self.welcome_label = QLabel("Welcome to OXO Game", self)
        self.welcome_label.setGeometry(0, 60, 590, 30)
        self.welcome_label.setAlignment(Qt.AlignCenter) #Aligns the texts to the center
        self.welcome_label.setFont(QFont("Arial", 14)) #Changing the font style and size

        self.name_of_player = QLabel("You are player: X/O", self) # This tells the client what player it is (X or Y)
        self.name_of_player.setGeometry(0, 90, 590, 25)
        self.name_of_player.setAlignment(Qt.AlignCenter)
        self.name_of_player.setFont(QFont("Arial", 11))

        self.game_title = QLabel("The Game", self) #This title is just for accurate and showing the client the game
        self.game_title.setGeometry(0, 118, 590, 25)
        self.game_title.setAlignment(Qt.AlignCenter)
        self.game_title.setFont(QFont("Arial", 12, QFont.Bold))

        # We are creating the board
        CELL    = 110 # Size of each cell in pixels
        start_x = (590 - CELL * 3) // 2 # Calculate X position to center the board horizontally
        start_y = 148  # Starting Y position
        ##self.btn = QPushButton("")
        ##self.btn.setIcon(QIcon("blank.gif"))
        ##self.btn.setIconSize(self.btn.size())
        
        ##self.btn.setGeometry(x_, y_, self.cell, self.cell)
        ##self.row_cells.append(self.btn)
    ##self.cells.append(self.row_cells)        

        self.cells = [] # 2D list to store button references
        for row in range(3): # Loop through 3 rows
            row_cells = []
            for col in range(3): # Loop through 3 columns
                btn = QPushButton("", self) # Create button for this cell
                #for x in range(0,8,2):
                if (row+col) % 2==0:
                    btn.setIcon(QIcon("cross.gif"))
                else:
                    btn.setIcon(QIcon("nought.gif"))                
                    #btn.setIcon(QIcon("cross.gif"))
                # Position the button using calculated coordinates
                btn.setGeometry(start_x + col * CELL, start_y + row * CELL, CELL, CELL)
                btn.setIconSize(QSize(CELL - 10, CELL - 10)) # Size for X/O images
                btn.setEnabled(True) # Ensures that button is clickable
                btn.clicked.connect(self.make_cell_handler(row, col)) # Connect click event with row and col parameters
                row_cells.append(btn)
            self.cells.append(row_cells)

        #  # Label for the messages section
        QLabel("Messages from the server:", self).setGeometry(20, 488, 250, 22)
        
        # Text area that displays server messages and is set to (read-only) so that the client is not able to edit the messages
        self.messages_box = QTextEdit(self)
        self.messages_box.setGeometry(20, 512, 540, 120)
        self.messages_box.setReadOnly(True) # User cannot type here
        self.messages_box.setStyleSheet("background-color")

        # New Game button enables to starts a fresh/mew game
        self.new_game_btn = QPushButton("New game", self)
        self.new_game_btn.setGeometry(20, 648, 180, 60)
        self.new_game_btn.setFont(QFont("Arial", 16, QFont.Bold))
        self.new_game_btn.clicked.connect(self.on_new_game)
        
        # Exit button will closes the application
        self.exit_btn = QPushButton("Exit", self)
        self.exit_btn.setGeometry(380, 648, 180, 60)
        self.exit_btn.setFont(QFont("Arial", 16, QFont.Bold))
        self.exit_btn.clicked.connect(self.on_exit)

    # handlers 
    def make_cell_handler(self, row, col):  #Creates a handler function for a specific cell button.
        def handler():
            self.on_cell_clicked(row, col)
        return handler

    def on_connect(self): # Handles Connect button click and establishes connection to server
        self.messages_box.append(">> Connect button clicked")

    def on_disconnect(self): # Handles Disconnect button click and closes connection to server
        self.messages_box.append(">> Disconnect button clicked")

    def on_cell_clicked(self, row, col): # Handles when a player clicks on a game cell.Sends the move to the server.
        self.messages_box.append(">> Cell ({0},{1}) clicked".format(row, col))

    def on_new_game(self): # Handles New Game button click and requests a fresh game
        self.messages_box.append(">> New game button clicked")
        
        
    def on_exit(self): #handles Exit button click and closes the application
        self.close() # Close the window after the exit button is clicked
 
    def handle_message(self, msg): # Processes incoming messages from the server.
        self.messages_box.append("Received: " + msg)
        parts = msg.split(",")
 
        # NEW GAME: Server randomly assigns player shape
        if parts[0] == "new game":
            self.shape = parts[1] # Extract X or O
            self.name_of_player.setText("You are player: " + self.shape)
            self.messages_box.append("New game started! You are '" + self.shape + "'")
            self.clear_board() # Reset the board display
 
        elif msg == "your move": # YOUR MOVE: Player's turn to play
            self.messages_box.append(">> Your turn")
            self.enable_board(True) # Enable all empty cells
 
        elif msg == "opponents move": # OPPONENT'S MOVE: Waiting for opponent...
            self.messages_box.append(">> Waiting for opponent...")
            self.enable_board(False) # Disable all cells while waiting
 
        elif parts[0] == "valid move": # VALID MOVE: Server confirms a valid move
            shape    = parts[1] # X or O
            position = int(parts[2]) # 0-8 position on board
            row = position // 3 # Calculate row from position
            col = position % 3 # Calculate column from position
            if shape == "X": # Set appropriate icon based on shape
                self.cells[row][col].setIcon(QIcon("cross.gif"))
            else:
                self.cells[row][col].setIcon(QIcon("nought.gif"))
            self.cells[row][col].setEnabled(False) # Disable this cell
 
        elif msg == "invalid move": # INVALID MOVE: Player tried illegal move
            self.messages_box.append(">> Invalid move. Try again.")
            self.enable_board(True) # Re-enable board for another try
 
        elif parts[0] == "game over":  # GAME OVER: Game has ended
            winner = parts[1] # 'X', 'O', or 'T' for tie
            self.enable_board(False) # Disable all cells
            if winner == "T":
                self.messages_box.append(">> It's a draw!")
            elif winner == self.shape:
                self.messages_box.append(">> You win!")
            else:
                self.messages_box.append(">> You lose!")
 
        elif msg == "play again":  # PLAY AGAIN: Server asks if player wants another round
            reply = QMessageBox.question(self, "Play Again?", "Would you like to play again?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.messages_box.append(">> Play again: yes") # TODO: Send "yes" to server
            else:
                self.messages_box.append(">> Play again: no") # TODO: Send "no" to server
 
        elif msg == "exit game": # EXIT GAME: Opponent disconnected
            self.messages_box.append(">> The other player has left. Goodbye.")
 
        else: # UNKNOWN MESSAGE: Unexpected message format
            self.messages_box.append(">> Unknown message: " + msg)

    
def main():
    app = QApplication(sys.argv)
    window = OXOGUIClient()
    window.show()
    sys.exit(app.exec_())

main()
