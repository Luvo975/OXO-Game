import sys # Import system functions
import socket # Import networking functions for client-server communication
import threading # Import threading so the GUI and server communication can run together
from datetime import datetime # Import date and time for timestamps in the message box
from PyQt5.QtWidgets import * # Import PyQt5 widgets
from PyQt5.QtCore import * # Import PyQt5 core functions
from PyQt5.QtGui import * # Import PyQt5 GUI tools such as fonts, icons and images
 
PORT = 12345 # Port number used for connecting to the server
BUFFER_SIZE = 32 # Maximum size of messages received from the server
BUFFER_STR = '{0:^' + str(BUFFER_SIZE) + '}' # Format used to keep all messages the same size


class ResultPopup(QWidget): # Popup window used to display win, lose or draw messages at the end of each game...
    def __init__(self, parent, message, bg_color, flicker=False): # Constructor method
        super().__init__(parent) # Initialize the QWidget parent class
        self.setWindowFlags(Qt.FramelessWindowHint) # Remove the normal window border
        self.setAttribute(Qt.WA_ShowWithoutActivating) # Allow popup to appear without stealing focus

        self.setFixedSize(300, 150) # Set popup size
        self.setStyleSheet(f"background-color: {bg_color}; border-radius: 15px;") # Set popup background colour and rounded corners

        layout = QVBoxLayout() # Create a vertical layout for the popup window
        label = QLabel(message) # Create a label to display the popup message
        label.setAlignment(Qt.AlignCenter) # Align the text to the center of the label
        label.setFont(QFont("Arial", 18, QFont.Bold)) # Set the font style, size and boldness of the text
        label.setStyleSheet("color: white;") # Change the text colour to white
        layout.addWidget(label) # Add the label widget into the layout
        self.setLayout(layout) # Set the popup layout

        self.flicker_timer = None # Initially there is no flicker timer
        if flicker: # Check if the popup should flicker
            self.flicker_timer = QTimer(self) # Create a timer object
            self.flicker_timer.timeout.connect(self.toggle_bg) # Connect the timer to the toggle_bg method
            self.flicker_timer.start(150) # Start the timer every 150 milliseconds
            self.flip = False # Variable used to switch between colours

        QTimer.singleShot(5000, self.safe_close) # Automatically close the popup after 5 seconds
        self.raise_() # Bring the popup to the front of the window

    def toggle_bg(self):
        if not self.isVisible(): # Check if the popup is visible
            return # Stop the method if the popup is hidden
        self.flip = not self.flip # Change the flip value from True to False or False to True
        new_color = "#8B0000" if self.flip else "#CC0000" # Choose the background colour depending on flip value
        self.setStyleSheet(f"background-color: {new_color}; border-radius: 15px;") # Update the popup background colour

    def safe_close(self):
        if self.flicker_timer: # Check if the flicker timer exists
            self.flicker_timer.stop() # Stop the timer
        self.close() # Close the popup window
        self.deleteLater() # Delete the popup object from memory safely


class OXOGUIClient(QWidget): # Main OXO GUI client class
    message_signal = pyqtSignal(str) # Signal used for safely updating the GUI from another thread

    def __init__(self): # Constructor method
        QWidget.__init__(self) # Initialize QWidget
        self.setWindowTitle("OXO Game") # Set the title of the window
        self.setGeometry(200, 100, 590, 800) # Set the window position and size
        self.setStyleSheet("background-color: #E8EDF5;") # Set the background color of the window/widget
        self.shape = None # Variable to store the current shape (e.g., game piece or UI shape)
        self.socket = None # Network socket (used for communication, likely client/server)
        self.running = False # Flag to indicate if the game/application loop is running
        self.my_turn = False # Flag to track if it is currently this player's turn
        self.waiting_for_play_again = False # Flag to indicate waiting state for a "play again" response
        self.message_signal.connect(self.handle_message) # Connect a signal to handle incoming messages
        self.active_popup = None # Stores the currently active popup window/dialog (if any)

        self.color_map = {"Light Blue-Gray": "#E8EDF5","White":           "#FFFFFF","Light Orange":    "#FFE0B2","Light Green":     "#C8E6C9","Light Blue":      "#BBDEFB","Light Pink":      "#F8BBD0","Light Purple":    "#D1C4E9"} # Dictionary mapping friendly color names to hex values for UI theme selection
        
        self.server_label = QLabel("Enter server:") # Label prompting user to enter server address
        self.server_label.setStyleSheet("color: #1B2A4A; font-weight: bold;") # Style for server label (dark text + bold)
        self.input = QLineEdit() # Input field for entering server IP/address
        self.input.setPlaceholderText("e.g. 127.0.0.1") # Placeholder text shown inside input field
        self.input.setStyleSheet("border: 1px solid #D0D8E8; border-radius: 6px; padding: 5px; background: #F8FAFF;") # Styling for input field (border, padding, background color)

        self.connect_button = QPushButton("Connect") # Button used to connect to server
        self.connect_button.setStyleSheet("QPushButton { background-color: #28A745; color: white; border-radius: 6px; padding: 6px 14px; font-weight: bold; }""QPushButton:hover { background-color: #218838; }") # Styling for connect button (green theme + hover effect)
        self.connect_button.clicked.connect(self.on_connect) # Connect button click event to connection function

        self.disconnect_button = QPushButton("Disconnect") # Button used to disconnect from server
        self.disconnect_button.setStyleSheet("QPushButton { background-color: #DC3545; color: white; border-radius: 6px; padding: 6px 14px; font-weight: bold; }""QPushButton:hover { background-color: #C82333; }") # Styling for disconnect button (red theme + hover effect)
        self.disconnect_button.clicked.connect(self.on_disconnect) # Connect disconnect button to handler function

        self.help_button = QPushButton("? Help") # Help button (opens help/instructions)
        self.help_button.setFixedSize(70, 40) # Fixed size for help button
        self.help_button.setStyleSheet("QPushButton { background-color: #17A2B8; color: white; border-radius: 6px; font-weight: bold; }""QPushButton:hover { background-color: #138496; }") # Styling for help button (blue theme)
        self.help_button.clicked.connect(self.show_help) # Connect help button to function that shows help dialog

        self.color_label = QLabel("  Color:") # Label for color selection section
        self.color_label.setStyleSheet("color: #1B2A4A; font-weight: bold;") # Styling for color label

        self.color_combo = QComboBox() # Dropdown (combo box) for selecting theme color
        self.color_combo.addItems(self.color_map.keys()) # Add color names (keys from dictionary) to dropdown
        self.color_combo.setCurrentIndex(0)   # Set default selected color (first item in list)
        self.color_combo.currentIndexChanged.connect(self.on_color_change) # Trigger function when selected color changes
        self.color_combo.setStyleSheet("border: 1px solid #D0D8E8; border-radius: 4px; padding: 2px;") # Styling for dropdown box

        self.welcome_label = QLabel("Welcome to OXO Game") # Main welcome label text
        self.welcome_label.setAlignment(Qt.AlignCenter) # Center align welcome label
        self.welcome_label.setFont(QFont("Arial", 18, QFont.Bold)) # Font style for welcome label
        self.welcome_label.setStyleSheet("color: #1B2A4A;") # Text color styling for welcome label

        self.name_of_player = QLabel("You are player: X/O") # Label showing player's role (X or O)
        self.name_of_player.setAlignment(Qt.AlignCenter) # Center align player label
        self.name_of_player.setFont(QFont("Arial", 16, QFont.Bold)) # Font styling for player label
        self.name_of_player.setStyleSheet("color: #1B2A4A; background-color: #EEF2F7; border-radius: 14px; padding: 4px 20px;") # Styling for player label background and text

        self.game_title = QLabel("THE GAME") # Game title label
        self.game_title.setAlignment(Qt.AlignCenter) # Center align game title
        self.game_title.setFont(QFont("Arial", 12, QFont.Bold)) # Font styling for game title
        self.game_title.setStyleSheet("color: #2979FF;") # Color styling for game title
 
        self.cells = [] # List that will store all rows of game buttons (3x3 grid)
        for r in range(3): # Loop through rows (0–2)
            row = [] # store buttons for this row
            for c in range(3): # Loop through columns (0–2)
                btn = QPushButton("") # Create a button for each cell in grid
                btn.setIconSize(QSize(90, 90)) # Set icon size (used if X/O images are added later)
                btn.clicked.connect(self.make_handler(r, c)) # Connect button click to handler for that grid position
                btn.setStyleSheet("QPushButton {border: 2px solid #1B2A4A;background-color: white;border-radius: 10px;}QPushButton:hover { background-color: #F0F4FF; }QPushButton:disabled {border: 2px solid #1B2A4A;background-color: white;border-radius: 10px;}")# Styling for each game cell button
                row.append(btn) # Add button to current row list
            self.cells.append(row) # Add completed row to grid list

        self.messages_label = QLabel("Messages from the server:") # Label for server message section
        self.messages_label.setFont(QFont("Arial", 14, QFont.Bold)) # Font styling for messages label
        self.messages_label.setStyleSheet("color: #1B2A4A;") # Color styling for messages label

        self.messages_box = QTextEdit() # Text box for displaying server messages/logs
        self.messages_box.setReadOnly(True) # Make text box read-only (no user editing)
        self.messages_box.setStyleSheet("background-color: #FAFBFF; border: 1px solid #D0D8E8; border-radius: 6px; padding: 4px;""font-family: Consolas; font-size: 11px;") # Styling for message box (background, border, font)

        self.new_game_btn = QPushButton("New game") # Button for starting a new game
        self.new_game_btn.setFont(QFont("Arial", 16, QFont.Bold)) # Set font style for "New game" button
        self.new_game_btn.setStyleSheet("QPushButton { background-color: #2979FF; color: white; border-radius: 8px; padding: 8px; font-weight: bold; }""QPushButton:hover { background-color: #1565C0; }""QPushButton:disabled { background-color: #AAAAAA; }") # Style the "New game" button (blue theme + hover + disabled state)
        self.new_game_btn.clicked.connect(self.on_new_game)  # Connect "New game" button to its handler function
        self.new_game_btn.setEnabled(False) # Disable the button initially (enabled later during gameplay)

        self.exit_btn = QPushButton("Exit") # Exit button to close the application
        self.exit_btn.setFont(QFont("Arial", 16, QFont.Bold)) # Set font style for exit button
        self.exit_btn.clicked.connect(self.on_exit) # Connect exit button to exit function
        self.exit_btn.setStyleSheet("background-color: #C82333; color: white;")  # Style exit button (red theme for danger/exit action)

        
        main_layout = QVBoxLayout() # Main vertical layout that holds all UI elements
        main_layout.setSpacing(8) # Set spacing between widgets in main layout
        main_layout.setContentsMargins(15, 15, 15, 15) # Set margins (left, top, right, bottom)
        self.setLayout(main_layout) # Apply main layout to the window/widget

        hbox1 = QHBoxLayout() # Horizontal layout for server connection controls
        hbox1.addWidget(self.server_label) # Add server label ("Enter server:")
        hbox1.addWidget(self.input)  # Add server input field
        hbox1.addWidget(self.connect_button) # Add connect button
        hbox1.addWidget(self.disconnect_button) # Add disconnect button
        hbox1.addStretch() # Add flexible space (pushes help button to far right)
        hbox1.addWidget(self.help_button) # Add help button at far right
        main_layout.addLayout(hbox1) # Add first row layout to main layout
        
        
        hbox2 = QHBoxLayout() # Horizontal layout for color selection
        hbox2.addStretch() # Push color selector to the right side
        hbox2.addWidget(self.color_label) # Add color label
        hbox2.addWidget(self.color_combo) # Add color dropdown
        main_layout.addLayout(hbox2) # Add second row to main layout
 
        separator = QFrame() # Create a horizontal line separator
        separator.setFrameShape(QFrame.HLine) # Set line shape to horizontal line
        separator.setFrameShadow(QFrame.Sunken) # Set line shape to horizontal line
        main_layout.addWidget(separator) # Add separator to layout

        main_layout.addWidget(self.welcome_label) # Add welcome message label
        main_layout.addWidget(self.name_of_player) # Add player identity label (X/O)
        main_layout.addWidget(self.game_title) # Add game title label

        grid = QGridLayout() # Grid layout for game board buttons
        grid.setSpacing(5) # Set spacing between grid cells
        grid.setAlignment(Qt.AlignCenter) # Center align grid in layout
        for r in range(3): # Loop through rows
            for c in range(3): # Loop through columns
                self.cells[r][c].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Allow button to expand inside grid cell
                self.cells[r][c].setMinimumSize(80, 80) # Set minimum size for each cell
                grid.addWidget(self.cells[r][c], r, c) # Add button to grid at position (row, column)
        main_layout.addLayout(grid) # Add grid layout to main layout

        main_layout.addWidget(self.messages_label) # Add label for server messages
        self.messages_box.setMaximumHeight(150) # Set maximum height for message box
        main_layout.addWidget(self.messages_box) # Add message display box to layout

        hbox2 = QHBoxLayout() # Horizontal layout for bottom action buttons
        hbox2.addWidget(self.new_game_btn, 1) # Add "New game" button (stretch factor = 1 for equal spacing)
        hbox2.addWidget(self.exit_btn, 1) # Add "Exit" button (stretch factor = 1 for equal spacing)
        main_layout.addLayout(hbox2) # Add bottom button row to main layout

        self.blank_icon = self.create_icon("blank.gif") # Load blank cell icon
        self.cross_icon = self.create_icon("cross.gif") # Load cross (X) icon
        self.nought_icon = self.create_icon("nought.gif") # Load nought (O) icon
        self.clear_board() # Clear/reset game board at startup

    def on_color_change(self, index): # Function triggered when user selects a new color
        name = self.color_combo.currentText() # Get selected color name from dropdown
        hex_color = self.color_map.get(name, "#E8EDF5") # Convert name to hex color value (fallback to default if not found)
        self.setStyleSheet(f"background-color: {hex_color};") # Apply background color to main window
        if self.active_popup and self.active_popup.isVisible(): # If popup exists and is visible, re-center it after color change
            self.center_popup(self.active_popup)

    def create_icon(self, path): # Function to create a QIcon from image file
        pixmap = QPixmap(path) # Load image into pixmap
        pixmap = pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation) # Scale image to 90x90 while keeping aspect ratio
        icon = QIcon() # Create icon object
        icon.addPixmap(pixmap, QIcon.Normal) # Add pixmap for normal state
        icon.addPixmap(pixmap, QIcon.Disabled) # Add pixmap for disabled state
        return icon # Return completed icon

    def make_handler(self, r, c): # Creates a handler function for each cell in the grid
        return lambda: self.on_cell_clicked(r, c) # Returns a lambda that captures row and column values

    def append_coloured_message(self, text, colour=None, prefix=None, prefix_colour=None): # Appends a message to the message box with optional colours and prefix
        timestamp = datetime.now().strftime("[%H:%M:%S]") # Get current time for message timestamp
        if prefix and prefix_colour: # If prefix (e.g. "Received:") is provided with a colour
            html = f'{timestamp} <span style="color:{prefix_colour};">{prefix}</span> {text}' # Format message using HTML styling for prefix + text
        elif colour: # If only message colour is provided
            html = f'{timestamp} <span style="color:{colour};">{text}</span>' # Format message with coloured text only
        else: # Default formatting (no colour)
            html = f'{timestamp} {text}' # Plain text message with timestamp
        self.messages_box.append(html) # Append formatted message to message box
        self.messages_box.setHtml(self.messages_box.toHtml()) # Force HTML refresh of message box
        self.messages_box.verticalScrollBar().setValue(self.messages_box.verticalScrollBar().maximum()) # Scroll to bottom of message box 

    def show_help(self): # Displays help popup explaining how to play the game
        help_text = ("<b>How to Play OXO (Tic‑Tac‑Toe)</b><br><br>""1. <b>Connect:</b> Enter the server IP address and click 'Connect'.<br>""2. <b>Your Symbol:</b> The server assigns you either <span style='color:#E74C3C;'>X (red)</span> or <span style='color:#2980B9;'>O (blue)</span>.<br>""3. <b>Gameplay:</b> Players take turns clicking empty cells to place their symbol. When it's your turn, the board cells become clickable.<br>""4. <b>Winning:</b> Get three of your symbols in a row (horizontally, vertically, or diagonally) to win.<br>""5. <b>Draw:</b> If all nine cells are filled without a winner, the game ends in a draw.<br>""6. <b>Game Over Popup:</b> After a game finishes, a colored popup appears inside the main window: Green for a win, Red (flickering) for a loss, and Dark Gray for a draw. It disappears after 5 seconds.<br>""7. <b>Play Again:</b> After a game, click 'New game' to request another round (opponent must agree). Click 'Exit' to quit.<br>""8. <b>Window Color:</b> You can customize the background color using the 'Color' dropdown at the top. Choose from 7 different colors to suit your style.<br>""9. <b>Disconnect:</b> Use the 'Disconnect' button to end the current session.<br>""<br></br>""<b>Tip:</b> Watch the 'Messages from the server' box for turn notifications and results.") # Full HTML help content shown in message box popup
        QMessageBox.information(self, "OXO Game Help", help_text) # Show help dialog

    def center_popup(self, popup): # Centers popup inside main window
        if popup is None:  # If popup does not exist, do nothing
            return
        parent_rect = self.rect() # Get parent window rectangle
        popup_size = popup.size()  # Get popup size
        x = parent_rect.x() + (parent_rect.width() - popup_size.width()) // 2 # Calculate X position (center horizontally)
        y = parent_rect.y() + (parent_rect.height() - popup_size.height()) // 2 # Calculate Y position (center vertically)
        popup.move(x, y) # Move popup to calculated position

    def close_existing_popup(self): # Closes any existing popup safely
        if self.active_popup is not None: # Check if popup exists
            try:
                self.active_popup.safe_close()  # Attempt to safely close popup
            except: # Ignore errors silently (not ideal but prevents crash)
                pass
            self.active_popup = None   # Remove reference to popup

    def show_win_popup(self):  # Shows WIN popup
        self.close_existing_popup() # Close any previous popup first
        self.active_popup = ResultPopup(self, "YOU WIN!", "#2E7D32", flicker=False)  # Create win popup (green, no flicker)
        self.active_popup.destroyed.connect(lambda: setattr(self, 'active_popup', None)) # Reset reference when popup is destroyed
        self.active_popup.show() # Show popup
        self.center_popup(self.active_popup) # Center popup

    def show_lose_popup(self): # Shows LOSE popup
        self.close_existing_popup() # Close previous popup
        self.active_popup = ResultPopup(self, "YOU LOSE!", "#CC0000", flicker=True) # Create red flickering popup
        self.active_popup.destroyed.connect(lambda: setattr(self, 'active_popup', None)) # Reset reference on destroy
        self.active_popup.show() # Show popup
        self.center_popup(self.active_popup) # Center popup

    def show_draw_popup(self): # Shows DRAW popup
        self.close_existing_popup()# Close previous popup
        self.active_popup = ResultPopup(self, "IT'S A DRAW!", "#455A64", flicker=False) # Create gray popup
        self.active_popup.destroyed.connect(lambda: setattr(self, 'active_popup', None))  # Reset reference on destroy
        self.active_popup.show() # Show popup
        self.center_popup(self.active_popup) # Center popup

    def resizeEvent(self, event): # Called when window is resized
        super().resizeEvent(event) # Call parent resize event
        if self.active_popup and self.active_popup.isVisible(): # If popup exists and is visible
            new_width = int(self.width() * 0.3) # Resize popup relative to window size
            new_height = int(self.height() * 0.2)
            self.active_popup.setFixedSize(new_width, new_height) # Apply new size
            self.center_popup(self.active_popup) # Re-center popup

    def moveEvent(self, event): # Called when window is moved
        super().moveEvent(event) # Call parent move event
        if self.active_popup and self.active_popup.isVisible(): # Re-center popup if visible
            self.center_popup(self.active_popup) # Re-centers the active popup window inside the main window

    
    def on_connect(self): 
        addr = self.input.text().strip() # Get server address from input field and remove spaces
        if not addr: # If no address is entered
            self.append_coloured_message("Enter server address", "#E74C3C") # Show error message in red
            return # Stop function execution
        try: 
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP socket (IPv4 + Stream socket)
            self.socket.connect((addr, PORT)) # Connect to server using provided address and port
            self.socket.settimeout(1.0)  # Set timeout for socket operations (prevents infinite blocking)
            self.append_coloured_message("Connected to server", "#27AE60") # Show success message in green
            self.running = True  # Mark client as running
            threading.Thread(target=self.play_loop, daemon=True).start() # Start background thread for receiving messages from server
        except Exception: # If connection fails, show error messag
            self.append_coloured_message("Connection failed: Enter a correct address", "#E74C3C")

    def on_disconnect(self):
        self.running = False # Stop game loop
        if self.socket: # If socket exists
            try:
                self.socket.close() # Close socket connection
            except: # Ignore any errors during closing
                pass
        self.append_coloured_message("Disconnected", None) # Show disconnected message

    def send(self, msg): # Display sent message in UI
        self.append_coloured_message(f"Sent: {msg}", None)
        if self.socket: # Check if socket exists
            try:
                self.socket.sendall(BUFFER_STR.format(msg).encode()) # Send encoded message to server
            except: # Ignore send errors (e.g. broken connection)
                pass

    def play_loop(self): # Main loop that continuously listens for messages from the server
        #while self.running:
            #try:
                #data = self.socket.recv(BUFFER_SIZE).decode().strip()
                #if data:
                    #self.message_signal.emit(data)
                #else:
                    #self.message_signal.emit("exit game") # If the other player has left  mid game then the socket will emmit and clear all board cells.
                    #break
            #except:
                #self.message_signal.emit("exit game") # If the other player has left then the socket will emmit and clear all board cells.
                #break
        # Keep listening while the game is running
            #while self.running:
        
                #try:
                    ## Receive data from the socket
                    #data = self.socket.recv(BUFFER_SIZE).decode().strip()
        
                    ## If valid data is received
                    #if data:
        
                        ## Send message to UI thread
                        #self.message_signal.emit(data)
        
                    #else:
                        ## Empty data means the other player disconnected
                        #self.message_signal.emit("exit game")
        
                        ## Stop loop
                        #break
        
                #except Exception as e:
                    ## Print actual error for debugging
                    #print("Socket error:", e)
        
                    ## Notify UI that player exited
                    #self.message_signal.emit("exit game")
        
                    ## Exit loop
                    #break
        
        while self.running: # Keep running while the game is active
            try: # Receive raw bytes from the server (blocking call with timeout)
                data = self.socket.recv(BUFFER_SIZE)# Receive raw data from socket
                if not data: # If recv returns empty bytes, the connection has been closed
                    self.message_signal.emit("exit game") # Notify GUI that the other player disconnected
                    break # Exit the loop
                msg = data.decode(errors = "ignore").strip() # Decode bytes into string and clean whitespace
                if msg: # Only process message if it's not empty
                    self.message_signal.emit(msg) # Send message safely to the GUI thread using signal
                    
            except socket.timeout: # If no data is received within timeout period, just continue listening
                continue
            except (ConnectionResetError, ConnectionAbortedError, OSError): # Handle cases where the connection is forcibly closed
                self.message_signal.emit("exit game") # Notify GUI that the opponent disconnected unexpectedly
                break
            except Exception: # Catch any other unexpected errors to prevent crashing
                self.message_signal.emit("exit game") # Notify GUI of disconnection for safety
                break # Exit loop
                #else:
                    #self.message_signal.emit("exit game") # Connection closed by server/other player
                    #break # Stop loop
            #except socket.timeout: # Handle socket timeout (no data received, but connection still alive)
                #continue # keep waiting for data
            #except: # Handle all other network errors
                #self.message_signal.emit("exit game") # Notify UI that connection is lost
                #break   # Exit loop 

    def handle_message(self, msg): # Display received message in message box
        self.append_coloured_message(msg, prefix="Received:", prefix_colour="#2980B9") # Display received message in message box
        parts = msg.split(",") # Split message into parts (protocol uses commas)

        if parts[0] == "new game":
            self.shape = parts[1] # Assign player symbol (X or O)
            symbol = self.shape
            if symbol == 'X': # Style X in red
                coloured_sym = '<span style="color:#E74C3C; font-weight:bold;">X</span>'
            else: # Style O in blue
                coloured_sym = '<span style="color:#2980B9; font-weight:bold;">O</span>'
            self.name_of_player.setText(f"You are player: {coloured_sym}") # Show player assignment
            self.name_of_player.setTextFormat(Qt.RichText) # Enable HTML formatting for label
            self.clear_board() # Reset board
            self.my_turn = False # Reset turn state
            self.waiting_for_play_again = False # Reset waiting flag
            self.new_game_btn.setEnabled(False) # Disable new game button

        elif msg == "your move":
            self.my_turn = True # Allow player to move
            self.enable_board(True) # Enable board interaction

        elif msg == "opponents move":
            self.my_turn = False # Disable player turn
            self.enable_board(False)  # Disable board interaction

        elif parts[0] == "valid move":
            shape, pos = parts[1], int(parts[2]) # Extract symbol and position
            r, c = pos // 3, pos % 3 # Convert position into row and column
            icon = self.cross_icon if shape == "X" else self.nought_icon # Choose correct icon based on player symbol
            self.cells[r][c].setIcon(icon) # Set icon on board cell
            self.cells[r][c].setEnabled(False) # Disable that cell

        elif msg == "invalid move":
            self.append_coloured_message("Invalid move. Please try again", "#E74C3C") # Show error message
            self.enable_board(True) # Re-enable board for retry

        elif parts[0] == "game over":
            winner = parts[1] # Get winner
            self.my_turn = False # Stop player turn
            self.enable_board(False) # Disable board
            if winner == "T":  # If draw
                self.append_coloured_message("It's a draw!", "#27AE60") # Show draw messag
                self.show_draw_popup() # Show draw popup
            elif winner == self.shape: # If player wins
                self.append_coloured_message("You win!", "#27AE60")  # Show win message
                self.show_win_popup() # Show win popup
            else: # If player loses
                self.append_coloured_message("You lose!", "#E74C3C") # Show lose message
                self.show_lose_popup() # Show lose popup
            self.waiting_for_play_again = True # Allow replay
            self.new_game_btn.setEnabled(True) # Enable new game button
            self.append_coloured_message("Click 'New game' to play again, or 'Exit' to quit.", None) # Prompt user for next action

        elif msg == "play again":
            pass # placeholder (no action needed)

        elif msg == "exit game": # Notify user opponent left
            self.append_coloured_message("Other player left. Goodbye.", None)  # Notify user opponent left
            self.running = False # Stop running loop
            self.new_game_btn.setEnabled(False) # Disable new game button
            if self.socket: # Close socket safely
                try:
                    self.socket.close()
                except:
                    pass
        else:
            self.append_coloured_message(f"Unknown message: {msg}", "#E74C3C")  # Show unknown message warning
        
    def on_cell_clicked(self, r, c):
        if not self.my_turn: # If not player's turn
            self.append_coloured_message("Not your turn", "#E74C3C") # Show error
            return
        if self.cells[r][c].icon().cacheKey() != self.blank_icon.cacheKey(): # If cell already used
            self.append_coloured_message("Cell already taken", "#E74C3C") # Show error
            return
        pos = r * 3 + c # Convert row/col to single position index
        self.send(str(pos)) # Send move to server
        self.my_turn = False # End turn
        self.enable_board(False) # Disable board

    def on_new_game(self):
        if self.waiting_for_play_again: # If waiting for replay confirmation
            self.send('y') # Send accept replay
            self.waiting_for_play_again = False # Reset flag
            self.new_game_btn.setEnabled(False) # Disable button
            self.append_coloured_message("Requesting new game...", None) # Show message
        else:
            self.append_coloured_message("No game finished yet, keep playing", "#E74C3C") # If game not finished yet

    def on_exit(self): # If waiting for replay decision
        if self.waiting_for_play_again: # Send decline replay
            self.send('n')
            QTimer.singleShot(100, self._close) # Delay close
        else:
            self._close() # Close immediately

    def _close(self):
        if self.socket: # Close socket if exists
            try:
                self.socket.close()
            except:
                pass
        self.close() # Close window

    def clear_board(self):
        for row in self.cells: # Loop through all rows
            for btn in row: # Loop through buttons
                btn.setIcon(self.blank_icon) # Reset icon
                btn.setEnabled(False) # Disable button

    def enable_board(self, enabled):
        for row in self.cells: # Loop through rows
            for btn in row:  # Loop through buttons
                if enabled and btn.icon().cacheKey() == self.blank_icon.cacheKey(): # Enable only empty cells.
                    btn.setEnabled(True)
                else:
                    btn.setEnabled(False)


def main():
    app = QApplication(sys.argv)
    win = OXOGUIClient()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()