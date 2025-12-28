# py-pokernow

A Python library for primarily interacting with [pokernow.club](https://pokernow.club)'s club API. 

## Features

-  **Club Management**: Create and manage poker clubs (chips, games, etc)
- 🔐 **Authentication**: Easy login through api
- ~~🎮 **Play API**~~: Maybe one day

## Contributing

If someone could actually implement the api/websocket for playing, you would be the goat.

## Installation

```bash
pip install py-pokernow
```

## Quick Start

```python
from pokernow import PokerNowSession

# Initialize session with your authentication token
session = PokerNowSession(apt_token="your_apt_token_here")

# Get club information
club = session.get_club("your-club-slug")
print(f"Club: {club.name}")
print(f"Players: {len(club.players)}")
print(f"Total chips: {club.total_chips_in_club()}")

# Add chips to a player using the club object
player = club.get_player_by_username("player_name")
if player:
    club.add_chips_to_player(
        player_id=player.id,
        amount=1000,
        reason="Bonus chips"
    )

# Create a new game using the club object
from pokernow import PokerGameConfig

config = PokerGameConfig(
    name="High Stakes",
    small_blind=50,
    big_blind=100,
    maxQuantityPlayers='9',
    gameType='th'  # Texas Hold'em
)

game_id = club.create_game(config)
print(f"Created game: {game_id}")
```

## Core Classes

### PokerNowSession
Main session class for API interactions.

```python
session = PokerNowSession(apt_token="your_token")
```

### PokerNowClub
Represents a poker club with all its data.

```python
club = session.get_club("club-slug")
print(club.name)
print(club.description)
print(club.players)  # List of PokerNowPlayer objects
print(club.games)    # List of PokerNowGame objects
```

### PokerNowPlayer
Represents a player in the club.

```python
player = club.get_player_by_username("username")
print(player.chips_balance)
print(player.club_role)
print(player.credit_limit)
```

### PokerNowGame
Represents a game/table.

```python
game = club.games[0]
print(game.custom_table_name)
print(game.small_blind, game.big_blind)
print(game.status)
```

### PokerNowTransaction
Represents a wallet transaction.

```python
transactions = club.get_player_transactions(player.id)
for tx in transactions:
    print(f"{tx.reason}: {tx.quantity} chips")
```

## API Methods

### PokerNowSession Methods

**Club Management:**
- `get_club(slug)` - Get club information (returns club with session attached)
- `create_club(slug, name, description, use_cents)` - Create a new club

**User Profile:**
- `update_user(username, email)` - Update current user's profile

**Payment & Subscription:**
- `create_stripe_checkout(mode, plan, receiver_player_id)` - Create checkout session
- `handle_payment_callback(session_id)` - Handle payment callback

### PokerNowClub Methods

Once you have a club object (via `session.get_club()`), you can call these methods directly on it:

**Settings:**
- `club.set_ledger_visibility(show)` - Toggle ledger visibility
- `club.set_play_report_visibility(show)` - Toggle play report visibility
- `club.set_game_archive_visibility(show)` - Toggle archive visibility
- `club.set_p2p_transfers(enabled)` - Enable/disable P2P transfers
- `club.set_exclusivity(option, message)` - Set club exclusivity settings

**Player Management:**
- `club.add_chips_to_player(player_id, amount, reason)` - Add chips
- `club.remove_chips_from_player(player_id, amount, reason)` - Remove chips
- `club.set_credit_limit_for_player(player_id, amount)` - Set credit limit
- `club.get_player_transactions(player_id)` - Get transaction history
- `club.set_player_role(player_user_id, role)` - Set player role

**Game Management:**
- `club.create_game(config)` - Create a new game
- `club.create_preset(config)` - Create a game preset
- `club.close_game(game_id)` - Close a game

## Game Configuration

Create custom game configurations using `PokerGameConfig`:

```python
config = PokerGameConfig(
    name="My Game",
    small_blind=10,
    big_blind=20,
    # Optional parameters
    maxQuantityPlayers='6',
    gameType='plo',  # Pot Limit Omaha
    decisionTime='30',
    timebank='15',
    straddle='true',
    runItTwice='ask_players'
)
```

### Game Types
- `'th'` - Texas Hold'em
- `'plo'` - Pot Limit Omaha
- `'plo5'` - 5-Card PLO
- `'ofc'` - Open Face Chinese

## Authentication

Get your `apt_token` by logging into pokernow.club and inspecting your cookies.

For programmatic login (requires OTP):

```python
from pokernow import login

def otp_callback(email):
    return input(f"Enter OTP sent to {email}: ")

session = login("your@email.com", otp_callback)
```

## Requirements

- Python 3.7+
- beautifulsoup4 >= 4.9.0
- requests >= 2.25.0

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/py-pokernow.git
cd py-pokernow

# Install development dependencies
pip install -e ".[dev]"
```

## Disclaimer

This is an unofficial library and is not affiliated with or endorsed by pokernow.club. Use at your own risk and ensure compliance with pokernow.club's terms of service.
