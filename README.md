#Full Stack Nanodegree Project 4 Refresh

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer. 
 
##Game Play Notes:

 - **create_user** 
    - the user_name is required to start a new game
 - **new_game**
    - number_of_players is required to set to 2 for a 2 player game
    - urlsafe_game_key is required to take actions about the game
 - **place_ship**
    - urlsafe_game_key, and user_name are required
    - ship_type should be entered in the Enumaration format:
        CARRIER or BATTLESHIP or SUBMARINE or CRUISER or DESTROYER
    - start_position should be entered in letter and digit format such as 'A5'
    - end_position should be entered in letter and digit format such as 'A9'
    - start_position and end_position should be associated that, the number of squares between
        start_position and end_position shall be equal to the ship length. For example, for CARRIER
        there shall be 5 squares, A5 and A9 has 5 squares between that are : A5, A6, A7, A8 ,A9
        another correct example is B2 and F2. The squares between are : B2, C2, D2, E2, F2.
 - **make_move**
    - It is required to set the position in letter and digit format.

##Score Keeping:
 - When a game ends, two score records are created for each user. There is a flag for each record to show
 whether the user won the game or lost the game. When a user makes a move and takes a guess, and if hits
 a ship, it is controlled that whether the ship is sunk or not. If the ship is sunk, then it is controlled 
 if the opponent has any other ships. If the opponent has no other ships, then the player who made the move 
 wins the game. 
 - When a player cancels the game, they automatically lose the game, and the score for that player for the 
 given game will be recorded with a loss. The opponent's score will be recorded with a win.
 - Total number of guesses made by the winning user will be recorded as well.
 - When generating ranking list, the user which has more wins will come first.
 - If the number of wins are equal for two users, then the sum of guesses for each game the users have played
 will compared. The user with a smaller number of total guesses will come first.

##Game Description:
Battleship is a guessing game for two players. It is known worldwide as a pencil and paper game 
which dates from World War I. It was published by various companies as a pad-and-pencil game in the 1930s.
Both players has a board, which is 10x10 by default. Players are needed to place their ships.
There are five ships Carrier, Battleship, Submarine, Cruiser and Destroyer. Their lengths are as follows:
5, 4, 3, 3, 2. Each ship is need to be placed horizontal or vertical but not diagonal. After ships have 
been placed, each player guesses a location to fire from the board of the opponent. The opponent needs to
give information about the guess that if there is a ship or not. Moreover players needed to tell their 
opponents when a ship is sunk. When a player has all of their ships sunken, they lose the game.

Required parameters are user_name, opponent_name, and number_of_players.
number_of_players shows whether the game is a 2 player game or a game against AI.
However, the against AI game is not implemented in this version of the game.
Optional parameters are rows and columns. They are equal to 10 by default.
Many different Battleship games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, opponent_name, number_of_players, rows (optional) ,columns(optional)
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name and opponent_name provided must correspond to an
    existing user - will raise a NotFoundException if not. number_of_players is required to set 2 for 
    a 2 player game. It is required to set 1 for playing against AI, but AI is not implemented.
    rows and columns are optional parameters to change board size.
    
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
     
 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}/cancel_game'
    - Method: POST
    - Parameters: urlsafe_game_key, user_name
    - Returns: GameForm with current game state.
    - Description: Resigns player from the game, and end the game. The player who resigns will lose.
    
 - **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: HistoryForms
    - Description: Returns the history of a given game. History includes every guess.
    
 - **place_ship**
    - Path: 'game/{urlsafe_game_key}/place_ship'
    - Method: POST
    - Parameters: urlsafe_game_key, user_name, ship_type, start_position, end_position
    - Returns: GameForm with current game state.
    - Description: In order to place ships, the correct urlsafe_game_key and user_name should be provided.
    There are five types of ships. The type should be provided with enumaration. start_position and end_position
    should be set by a letter followed by a number. These position values will be controled to check whether
    they are in the boundaries of the boards.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, user_name, position
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created. Each guess is an attempt to
    find the ships of the opponent. If a guess hits a ship, the user will be informed.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_user_games**
    - Path: 'game/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms. 
    - Description: Returns all Games that continuing and the player involved.
    Will raise a NotFoundException if the User does not exist.
    
 - **get_user_rankings**
    - Path: 'rankings'
    - Method: GET
    - Parameters: -
    - Returns: RankingForms. 
    - Description: Returns player rankings sorted by the winloss_ratio descending and then by total guesses
    

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    - Stores wins, losses, winloss_ratio, and total_guesses for ranking
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    - Stores number_of_players, player1, player2, board_ship1, board_ship2,
    board_hit1, board_hit2, ships1, ships2, rows, columns, turn, player1_turn,
    player2_turn and game_over
    
 - **History**
    - Stores each guess for a game. user, turn, player_turn, guess, result properties.
    
 - **Ship**
    - Stores ships of a player for a specific game. User, game, type, position, hits
    are stored properties.
 
 - **Point**
    - Stores coordinates of a point on the board. Moreover, can convert coordinates to XY pair
    and 1 dimension index.
     
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key,user_name, opponent_name,
    game_over).
 - **GameForms**
    - Multiple GameForm container.    
 - **NewGameForm**
    - Used to create a new game (urlsafe_key,number_of_players,user_name, opponent_name, rows, columns)
 - **CancelGameForm**
    - Used to resign from a new game (urlsafe_key,user_name)
 - **PlaceShipForm**
    - Used to place a ship for a user (urlsafe_key,user_name, ship_type,
    start_position, end_position).    
 - **MakeMoveForm**
    - Inbound make move form (urlsafe_key,user_name, position).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).
 - **HistoryForm**
    - Representation of a game's History (user_name, turn, player_turn,
    guess, result).
 - **ScoreForm**
    - Representation of user Ranking (user_name, winloss, guesses).    
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **HistoryForms**
    - Multiple HistoryForm container.
 - **RankingForms**
    - Multiple RankingForm container.    
 - **StringMessage**
    - General purpose String container.