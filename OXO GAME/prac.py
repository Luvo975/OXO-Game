import sys # For system operations and exiting the app
import socket  # For networking (connecting to the server)
import threading # To run the message receiving loop without freez
from datetime import datetime # To add timestamps to messages
from PyQt5.QtWidgets import * # All the GUI widgets (buttons, labels, layouts, etc.)
from PyQt5.QtCore import * # Core Qt functionality (signals, slots, threading, etc.)
from PyQt5.QtGui import * # GUI extras (fonts, icons, colors)

PORT = 12345 # The port number on which the game server listens
BUFFER_SIZE = 32 # Number of bytes to receive at a time (small because OXO messages are short)
BUFFER_STR = '{0:^' + str(BUFFER_SIZE) + '}' # Template to center the message in a fixed width (for alignment)


#This is our GUI class
class OXOGUIClient(QWidget):
    message_signal = pyqtSignal(str)# A custom signal that emits a string message from the background thread. This allows safe cross‑thread communication (the signal will be processed in the GUI thread
    def __init__(self):
        QWidget.__init__(self) # Initialise the base Qt widget and the parent class.
        self.setWindowTitle("OXO Game") # Title shown on the title bar
        self.setGeometry(200, 100, 590, 800) # Position and initial size (x, y, width, height)
        self.setStyleSheet("background-color: #E8EDF5;") # Soft light blue‑grey background
        self.shape = None # Will be 'X' or 'O' once the server assigns it. But if the server has not assigned it, it will be None
        self.socket = None # The network socket used to talk to the server
        self.running = False # Flag to keep the network receiver thread alive
        self.my_turn = False # True when it's this client's turn to play
        self.waiting_for_play_again = False # True after a game ends, waiting for "New game" click
        self.message_signal.connect(self.handle_message) # Connect the custom signal to the slot that processes incoming messages. When the background thread emits this signal, handle_message() will be called.
        
        self.server_label = QLabel("Enter server:")
        self.server_label.setStyleSheet("color: #1B2A4A; font-weight: bold;")
        
        self.input = QLineEdit()
        self.input.setPlaceholderText("e.g. 127.0.0.1")
        self.input.setStyleSheet("border: 1px solid #D0D8E8;""border-radius: 6px;""padding: 5px;""background: #F8FAFF;")
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("QPushButton { background-color: #28A745; color: white;""border-radius: 6px; padding: 6px 14px; font-weight: bold; }""QPushButton:hover { background-color: #218838; }")        
        self.connect_button.clicked.connect(self.on_connect) # Call on_connect when clicked
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setStyleSheet("QPushButton { background-color: #DC3545; color: white;""border-radius: 6px; padding: 6px 14px; font-weight: bold; }""QPushButton:hover { background-color: #C82333; }")        
        self.disconnect_button.clicked.connect(self.on_disconnect) # Calls on_disconnect when clicked

        self.welcome_label = QLabel("Welcome to OXO Game")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.welcome_label.setStyleSheet("color: #1B2A4A;")

        self.name_of_player = QLabel("You are player: X/O")
        self.name_of_player.setAlignment(Qt.AlignCenter)
        self.name_of_player.setFont(QFont("Arial", 16, QFont.Bold))
        self.name_of_player.setStyleSheet("color: #1B2A4A;""background-color: #EEF2F7;""border-radius: 14px;""padding: 4px 20px;")
        
        self.game_title = QLabel("THE GAME")
        self.game_title.setAlignment(Qt.AlignCenter)
        self.game_title.setFont(QFont("Arial", 12, QFont.Bold))
        self.game_title.setStyleSheet("color: #2979FF;")

        
        self.cells = [] # 2D list: self.cells[row][col] = QPushButton
        for r in range(3):
            row = []
            for c in range(3):
                btn = QPushButton("") # Empty text. We will use icons (X / O)
                btn.setIconSize(QSize(90, 90)) # Each button gets a lambda handler that knows its row and column
                btn.clicked.connect(self.make_handler(r, c))
                btn.setStyleSheet("""QPushButton {border: 2px solid #1B2A4A;background-color: white;border-radius: 10px;}QPushButton:hover { background-color: #F0F4FF; }QPushButton:disabled {border: 2px solid #1B2A4A;background-color: white;border-radius: 10px;}""")
                row.append(btn)
            self.cells.append(row)

        
        self.messages_label = QLabel("Messages from the server:")
        self.messages_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.messages_label.setStyleSheet("color: #1B2A4A;")
        
        self.messages_box = QTextEdit() # Text area where all messages from the server appear
        self.messages_box.setReadOnly(True) # The user cannot type here in the box, but can only get messagesa and read.
        self.messages_box.setStyleSheet("background-color: #FAFBFF;""border: 1px solid #D0D8E8;""border-radius: 6px;""padding: 4px;""font-family: Consolas;""font-size: 11px;")
                

        self.new_game_btn = QPushButton("New game")
        self.new_game_btn.setFont(QFont("Arial", 16, QFont.Bold))
        self.new_game_btn.setStyleSheet("QPushButton { background-color: #2979FF; color: white;""border-radius: 8px; padding: 8px; font-weight: bold; }""QPushButton:hover { background-color: #1565C0; }""QPushButton:disabled { background-color: #AAAAAA; }")
        self.new_game_btn.clicked.connect(self.on_new_game)
        self.new_game_btn.setEnabled(False) # Disabled until a game actually finishes

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setFont(QFont("Arial", 16, QFont.Bold))
        self.exit_btn.clicked.connect(self.on_exit)
        self.exit_btn.setStyleSheet("background-color: #C82333; color: white;")
        
        main_layout = QVBoxLayout() # Main vertical layout (everything stacked top‑to‑bottom)
        main_layout.setSpacing(8) # Gap between items
        main_layout.setContentsMargins(15, 15, 15, 15) # Inner margins
        self.setLayout(main_layout)
        
        hbox = QHBoxLayout() # Row 1: Server controls (horizontal)
        hbox.addWidget(self.server_label)
        hbox.addWidget(self.input)
        hbox.addWidget(self.connect_button)
        hbox.addWidget(self.disconnect_button)
        main_layout.addLayout(hbox)
        
        separator = QFrame() # A horizontal line separator
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        main_layout.addWidget(self.welcome_label) # Row 2: Welcome label, player label, game title
        main_layout.addWidget(self.name_of_player)
        main_layout.addWidget(self.game_title)
       
        grid = QGridLayout() # Row 3: The game board (3x3 grid)
        grid.setSpacing(5)
        grid.setAlignment(Qt.AlignCenter) # Keep the board at the center
        for r in range(3):
            for c in range(3): 
                self.cells[r][c].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Buttons will expand when the window is resized
                self.cells[r][c].setMinimumSize(80, 80)
                grid.addWidget(self.cells[r][c], r, c)
        main_layout.addLayout(grid)
        
        main_layout.addWidget(self.messages_label) # Row 4: Messages label and the text area (with a limited height)
        self.messages_box.setMaximumHeight(150)
        main_layout.addWidget(self.messages_box)

        hbox2 = QHBoxLayout() # Row 5: New Game and Exit buttons side‑by‑side
        hbox2.addWidget(self.new_game_btn, 1) # 1 = stretch factor (both buttons take equal space)
        hbox2.addWidget(self.exit_btn, 1)
        main_layout.addLayout(hbox2)

        # Load icons (X, O, and a blank placeholder)
        self.blank_icon = self.create_icon("blank.gif")
        self.cross_icon = self.create_icon("cross.gif")
        self.nought_icon = self.create_icon("nought.gif")
        self.clear_board() # Clear the board visually (all buttons get the blank icon and are disabled)

    def create_icon(self, path): #Load an image file, scale it to 90x90 pixels, and turn it into a QIconthat can be used on buttons. The icon will be shown both in normal stateand when the button is disabled
        pixmap = QPixmap(path)
        pixmap = pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon = QIcon()
        icon.addPixmap(pixmap, QIcon.Normal)
        icon.addPixmap(pixmap, QIcon.Disabled)
        return icon

    def make_handler(self, r, c): # Returns a function (lambda) that calls on_cell_clicked with the given (r,c). This is needed because the clicked signal does not automatically pass row/column.
        return lambda: self.on_cell_clicked(r, c)

    
    def append_coloured_message(self, text, colour=None, prefix=None, prefix_colour=None): # Add a message to the messages_box with timestamp and colours. text: the main message string, colour: HTML colour for the whole message, prefix: a word or tag shown before the message (e.g. "Received:"), prefix_colour: colour for that prefix.
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        if prefix and prefix_colour:
            html = f'{timestamp} <span style="color:{prefix_colour};">{prefix}</span> {text}'
        elif colour:
            html = f'{timestamp} <span style="color:{colour};">{text}</span>'
        else:
            html = f'{timestamp} {text}'
        self.messages_box.append(html)
        self.messages_box.setHtml(self.messages_box.toHtml()) # Scroll automatically to the bottom so the user always sees the latest message
        self.messages_box.verticalScrollBar().setValue(self.messages_box.verticalScrollBar().maximum())

    def on_connect(self): # Called when the user clicks the Connect button.
        addr = self.input.text().strip()
        if not addr:
            self.append_coloured_message("Enter server address", "#E74C3C")
            return
        try: # Create a TCP socket and connect to the given address and fixed PORT
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((addr, PORT))
            self.append_coloured_message("Connected to server", "#27AE60")  # green
            self.running = True # Start a background thread that constantly listens for server messages
            threading.Thread(target=self.play_loop, daemon=True).start()
        except Exception as e:
            #self.append_coloured_message(f"Connection failed: {e}", "#E74C3C")
            self.append_coloured_message(f"Connection failed: Enter a correct address", "#E74C3C")

    def on_disconnect(self): # Disconnect from the server and clean up.
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.append_coloured_message("Disconnected", None)

    def send(self, msg): # Send a message to the server.The message is formatted to a fixed width (BUFFER_SIZE) using the BUFFER_STR template
        self.append_coloured_message(f"Sent: {msg}", None)
        if self.socket:
            try:
                self.socket.sendall(BUFFER_STR.format(msg).encode())
            except:
                pass

    def play_loop(self): # This runs in a separate thread. It keeps receiving data from the server.Whenever a complete message arrives, it emits the message_signal signal, which will be handled in the main (GUI) thread.
        while self.running:
            try:
                data = self.socket.recv(BUFFER_SIZE).decode().strip()
                if data:
                    self.message_signal.emit(data)  # Send the message to the GUI thread
                else:
                    break
            except:
                break

    def handle_message(self, msg): # Processes every message received from the server.This method is invoked via the message_signal, so it runs safely in the GUI thread.
        self.append_coloured_message(msg, prefix="Received:", prefix_colour="#2980B9") # Show the raw message in the log with a blue "Received:" prefix
        parts = msg.split(",")
        if parts[0] == "new game":
            self.shape = parts[1]
            symbol = self.shape
            if symbol == 'X':
                coloured_sym = '<span style="color:#E74C3C; font-weight:bold;">X</span>'
            else:
                coloured_sym = '<span style="color:#2980B9; font-weight:bold;">O</span>' 
            self.name_of_player.setText(f"You are player: {coloured_sym}") # Update the label using rich text so that colours show
            self.name_of_player.setTextFormat(Qt.RichText)
            self.clear_board() # Reset all cells to blank
            self.my_turn = False
            self.waiting_for_play_again = False
            self.new_game_btn.setEnabled(False) # Disable "New game" until the current game finishes

        elif msg == "your move":
            self.my_turn = True
            self.enable_board(True) # Let the player click empty button

        elif msg == "opponents move":
            self.my_turn = False
            self.enable_board(False) # Disable all buttons while waiting

        elif parts[0] == "valid move": # Format: "valid move,X,4"  (place X at position 4)
            shape, pos = parts[1], int(parts[2])
            r, c = pos // 3, pos % 3
            icon = self.cross_icon if shape == "X" else self.nought_icon
            self.cells[r][c].setIcon(icon)
            self.cells[r][c].setEnabled(False)

        elif msg == "invalid move":
            self.append_coloured_message("Invalid move. Please try again", "#E74C3C")
            self.enable_board(True) # Let the player try again

        elif parts[0] == "game over":
            winner = parts[1] # "X", "O", or "T" for tie
            self.my_turn = False
            self.enable_board(False) # No more moves allowed now
            if winner == "T":
                self.append_coloured_message("It's a draw!", "#27AE60")
            elif winner == self.shape:
                self.append_coloured_message("You win!", "#27AE60")
            else:
                self.append_coloured_message("You lose!", "#E74C3C")
            self.waiting_for_play_again = True
            self.new_game_btn.setEnabled(True) # Now "New game" becomes usable
            self.append_coloured_message("Click 'New game' to play again, or 'Exit' to quit.", None)

        elif msg == "play again": # server asks if the user wants to play again.
            pass # Nothing to do here; the server waits for our answer (sent by on_new_game)

        elif msg == "exit game": # "exit game" when opponent disconnected
            self.append_coloured_message("Other player left. Goodbye.", None)
            self.running = False
            self.new_game_btn.setEnabled(False)
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
        else: # Any unrecognised message
            self.append_coloured_message(f"Unknown message: {msg}", "#E74C3C")        

    def on_cell_clicked(self, r, c): # Called when the user clicks one of the board buttons.
        if not self.my_turn:
            self.append_coloured_message("Not your turn", "#E74C3C")
            return
        if self.cells[r][c].icon().cacheKey() != self.blank_icon.cacheKey():
            self.append_coloured_message("Cell already taken", "#E74C3C")
            return

        pos = r * 3 + c
        self.send(str(pos)) # Send the move to the server (as a single digit 0..8)
        self.my_turn = False
        self.enable_board(False) # Disable all buttons until the server replies

    def on_new_game(self):
        if self.waiting_for_play_again:
            self.send('y') # Tell server we want to play again
            self.waiting_for_play_again = False
            self.new_game_btn.setEnabled(False) # Disable again until the next game ends
            self.append_coloured_message("Requesting new game...", None)
        else:
            self.append_coloured_message("No game finished yet, keep playing", "#E74C3C")

    def on_exit(self): # Called when the user clicks the Exit button.
        if self.waiting_for_play_again:
            self.send('n') # Tell server we don't want a rematch
            QTimer.singleShot(100, self._close) # Wait a little for the message to be sent
        else:
            self._close()

    def _close(self): # Actually close the socket and the window.
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.close()

    def clear_board(self): # Reset all buttons to the blank icon and disable them.
        for row in self.cells:
            for btn in row:
                btn.setIcon(self.blank_icon)
                btn.setEnabled(False)

    def enable_board(self, enabled): # Enable or disable buttons that are still empty. Buttons that already have an X or O stay disabled.
        for row in self.cells:
            for btn in row:
                if enabled and btn.icon().cacheKey() == self.blank_icon.cacheKey():
                    btn.setEnabled(True) # Only empty cells become clickable
                else:
                    btn.setEnabled(False)
                    
def main():
    app = QApplication(sys.argv)
    win = OXOGUIClient()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()