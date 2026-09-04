# DO NOT MODIFY THIS FILE

PORT = 12345 # This is the port number. It’s like a communication door for the server. The server listens on this port. The client connects using this same port
BUFFER_SIZE = 32 #This controls message size. Messages sent between client and server are limited to 32 characters. Keeps communication consistent. Prevents sending too much data at once.
BUFFER_STR = '{0:^'+ str(BUFFER_SIZE) +'}' #It’s a formatting rule for messages. It makes every message exactly 32 characters long and centered.

GAME_NAME = 'OXO' # Name of the game and is used for display and identification.
BOARD_SIZE = 9 # The OXOTextClient will use the board size to manage the board