"""
py-pokernow: A Python library for interacting with pokernow.club

This module provides classes and methods to interact with the PokerNow Club API,
allowing you to manage clubs, players, games, and transactions programmatically.
"""

from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable


class PokerNowPlayer:
    """
    Represents a player in a PokerNow club.
    
    Attributes:
        id: Unique identifier for the club player
        username: Player's username
        display_name: Player's display name
        user_id: User's network ID
        chips_balance: Current chip balance
        club_role: Role in the club ('owner', 'manager', 'member')
        player_id: PokerNow player ID
        email: Player's email address (if available)
        credit_limit: Credit limit for the player
        disabled_chat: Whether chat is disabled for this player
        left_club: Whether the player has left the club
    """
    
    def __init__(self, player_data: Dict[str, Any]):
        """
        Initialize a PokerNowPlayer from API data.
        
        Args:
            player_data: Dictionary containing player information from the API
        """
        self._data = player_data
    
    @property
    def id(self) -> str:
        """Club player ID."""
        return self._data.get('id', '')
    
    @property
    def username(self) -> str:
        """Player's username."""
        return self._data.get('username', '')
    
    @property
    def display_name(self) -> str:
        """Player's display name."""
        return self._data.get('display_name', '')
    
    @property
    def user_id(self) -> str:
        """Network user ID."""
        return self._data.get('user_id', '')
    
    @property
    def chips_balance(self) -> int:
        """Current chip balance."""
        return self._data.get('chips_balance', 0)
    
    @property
    def club_role(self) -> str:
        """Role in the club (owner, manager, member)."""
        return self._data.get('club_role', 'member')
    
    @property
    def player_id(self) -> str:
        """PokerNow player ID."""
        return self._data.get('player_id', '')
    
    @property
    def email(self) -> Optional[str]:
        """Player's email address."""
        return self._data.get('email')
    
    @property
    def credit_limit(self) -> int:
        """Credit limit for the player."""
        return self._data.get('credit_limit', 0)
    
    @property
    def disabled_chat(self) -> bool:
        """Whether chat is disabled for this player."""
        return self._data.get('disabled_chat', False)
    
    @property
    def left_club(self) -> bool:
        """Whether the player has left the club."""
        return self._data.get('left_club', False)
    
    def __repr__(self) -> str:
        return f"PokerNowPlayer(username='{self.username}', chips={self.chips_balance})"


class PokerNowGame:
    """
    Represents a poker game/table in a club.
    
    Attributes:
        id: Unique identifier for the club game
        club_id: ID of the club this game belongs to
        poker_now_game_id: PokerNow game identifier
        custom_table_name: Custom name for the table
        chips_balance: Chip balance in the game
        status: Game status (running, paused, etc.)
        game_type: Type of poker game (th, plo, etc.)
        small_blind: Small blind amount
        big_blind: Big blind amount
        max_players: Maximum number of players
        hands_played: Number of hands played
        expired: Whether the game has expired
    """
    
    def __init__(self, game_data: Dict[str, Any]):
        """
        Initialize a PokerNowGame from API data.
        
        Args:
            game_data: Dictionary containing game information from the API
        """
        self._data = game_data
        self.game_config = game_data.get('game', {})
    
    @property
    def id(self) -> str:
        """Club game ID."""
        return self._data.get('id', '')
    
    @property
    def club_id(self) -> str:
        """ID of the club this game belongs to."""
        return self._data.get('club_id', '')
    
    @property
    def poker_now_game_id(self) -> str:
        """PokerNow game identifier."""
        return self._data.get('poker_now_game_id', '')
    
    @property
    def custom_table_name(self) -> str:
        """Custom name for the table."""
        return self._data.get('custom_table_name', '')
    
    @property
    def chips_balance(self) -> int:
        """Chip balance in the game."""
        balance = self._data.get('chips_balance', 0)
        return int(balance) if isinstance(balance, str) else balance
    
    @property
    def status(self) -> str:
        """Game status."""
        return self.game_config.get('status', '')
    
    @property
    def game_type(self) -> str:
        """Type of poker game (th=Texas Hold'em, plo=PLO, etc.)."""
        return self.game_config.get('gameType', '')
    
    @property
    def small_blind(self) -> int:
        """Small blind amount."""
        return self.game_config.get('smallBlind', 0)
    
    @property
    def big_blind(self) -> int:
        """Big blind amount."""
        return self.game_config.get('bigBlind', 0)
    
    @property
    def max_players(self) -> int:
        """Maximum number of players."""
        return int(self.game_config.get('maxQuantityPlayers', 0))
    
    @property
    def hands_played(self) -> int:
        """Number of hands played in this game."""
        return self.game_config.get('handsPlayed', 0)
    
    @property
    def expired(self) -> bool:
        """Whether the game has expired."""
        return self._data.get('expired', False)
    
    def __repr__(self) -> str:
        return f"PokerNowGame(name='{self.custom_table_name}', blinds={self.small_blind}/{self.big_blind}, status='{self.status}')"


class PokerNowTransaction:
    """
    Represents a transaction/movement in the club wallet.
    
    Attributes:
        id: Unique identifier for the transaction
        receiving_club_player_id: ID of the player receiving chips
        reason: Reason for the transaction
        poker_now_game_id: Associated game ID (if any)
        quantity: Amount of chips (positive for add, negative for remove)
        created_at: When the transaction was created
        updated_at: When the transaction was last updated
        sending_club_player_id: ID of the player/admin who initiated the transaction
        poker_now_movement_id: PokerNow movement ID
        now_coin_product_id: Now Coin product ID (if applicable)
        now_coin_product_category: Now Coin product category (if applicable)
    """
    
    def __init__(self, transaction_data: Dict[str, Any]):
        """
        Initialize a PokerNowTransaction from API data.
        
        Args:
            transaction_data: Dictionary containing transaction information from the API
        """
        self._data = transaction_data
    
    @property
    def id(self) -> str:
        """Transaction ID."""
        return self._data.get('id', '')
    
    @property
    def receiving_club_player_id(self) -> str:
        """ID of the player receiving chips."""
        return self._data.get('club_player_id', '')
    
    @property
    def reason(self) -> str:
        """Reason for the transaction."""
        return self._data.get('reason', '')
    
    @property
    def poker_now_game_id(self) -> Optional[str]:
        """Associated game ID."""
        return self._data.get('poker_now_game_id')
    
    @property
    def quantity(self) -> int:
        """Amount of chips (positive=add, negative=remove)."""
        qty = self._data.get('quantity', 0)
        return int(qty) if isinstance(qty, str) else qty
    
    @property
    def created_at(self) -> Optional[datetime]:
        """When the transaction was created."""
        date_str = self._data.get('created_at')
        if date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return None
    
    @property
    def updated_at(self) -> Optional[datetime]:
        """When the transaction was last updated."""
        date_str = self._data.get('updated_at')
        if date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return None
    
    @property
    def sending_club_player_id(self) -> str:
        """ID of the player/admin who initiated the transaction."""
        return self._data.get('author_club_player_id', '')
    
    @property
    def poker_now_movement_id(self) -> Optional[str]:
        """PokerNow movement ID."""
        return self._data.get('poker_now_movement_id')
    
    @property
    def now_coin_product_id(self) -> Optional[str]:
        """Now Coin product ID."""
        return self._data.get('now_coin_product_id')
    
    @property
    def now_coin_product_category(self) -> Optional[str]:
        """Now Coin product category."""
        return self._data.get('now_coin_product_category')
    
    def __repr__(self) -> str:
        return f"PokerNowTransaction(reason='{self.reason}', quantity={self.quantity})"


class PokerNowClub:
    """
    Represents a PokerNow club with all its data and operations.
    
    This class provides access to club information and convenience methods
    for managing players, games, and settings.
    
    Attributes:
        id: Unique identifier for the club
        name: Club name
        slug: Club URL slug
        description: Club description
        created_at: When the club was created
        updated_at: When the club was last updated
        plan_type: Subscription plan type
        paid_until: When the subscription expires
        max_players: Maximum number of players allowed
        use_cents: Whether the club uses cents
        players: List of all players in the club
        games: List of all games in the club
        me: Current user's player object (if available)
        is_premium: Whether this is a premium club
    """
    
    def __init__(self, club_data: Dict[str, Any], session: 'PokerNowSession' = None):
        """
        Initialize a PokerNowClub from API data.
        
        Args:
            club_data: Dictionary containing club information from the API
            session: Optional PokerNowSession for making API calls
        """
        self._data = club_data
        self._session = session
        self._players = [PokerNowPlayer(p) for p in club_data.get('players', [])]
        self._games = [PokerNowGame(g) for g in club_data.get('games', [])]
        
        self._me = None
        if 'me' in club_data:
            self._me = PokerNowPlayer(club_data['me'])

    @property
    def id(self) -> str:
        """Club ID."""
        return self._data.get('id', '')
    
    @property
    def name(self) -> str:
        """Club name."""
        return self._data.get('name', '')
    
    @property
    def slug(self) -> str:
        """Club URL slug."""
        return self._data.get('slug', '')
    
    @property
    def description(self) -> str:
        """Club description."""
        return self._data.get('description', '')
    
    @property
    def created_at(self) -> Optional[datetime]:
        """When the club was created."""
        date_str = self._data.get('created_at')
        if date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return None
    
    @property
    def updated_at(self) -> Optional[datetime]:
        """When the club was last updated."""
        date_str = self._data.get('updated_at')
        if date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return None
    
    @property
    def plan_type(self) -> str:
        """Subscription plan type."""
        return self._data.get('plan_type', '')
    
    @property
    def paid_until(self) -> Optional[datetime]:
        """When the subscription expires."""
        date_str = self._data.get('paid_until')
        if date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return None
    
    @property
    def max_players(self) -> int:
        """Maximum number of players allowed in the club."""
        return self._data.get('maxplayers', 0)
    
    @property
    def use_cents(self) -> bool:
        """Whether the club uses cents."""
        return self._data.get('use_cents', False)
    
    @property
    def players(self) -> List[PokerNowPlayer]:
        """List of all players in the club."""
        return self._players
    
    @property
    def games(self) -> List[PokerNowGame]:
        """List of all games in the club."""
        return self._games
    
    @property
    def me(self) -> Optional[PokerNowPlayer]:
        """Current user's player object."""
        return self._me
    
    @property
    def is_premium(self) -> bool:
        """Whether this is a premium club."""
        return self._data.get('isPremium', False)
    
    def get_player_by_username(self, username: str) -> Optional[PokerNowPlayer]:
        """
        Find a player by username (case-insensitive).
        
        Args:
            username: The username to search for
            
        Returns:
            PokerNowPlayer object if found, None otherwise
        """
        for player in self.players:
            if player.username.lower() == username.lower():
                return player
        return None
    
    def get_player_by_id(self, player_id: str) -> Optional[PokerNowPlayer]:
        """
        Find a player by their club player ID.
        
        Args:
            player_id: The player ID to search for
            
        Returns:
            PokerNowPlayer object if found, None otherwise
        """
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def get_game_by_name(self, name: str) -> Optional[PokerNowGame]:
        """
        Find a game by its custom table name (case-insensitive).
        
        Args:
            name: The table name to search for
            
        Returns:
            PokerNowGame object if found, None otherwise
        """
        for game in self.games:
            if game.custom_table_name.lower() == name.lower():
                return game
        return None
    
    def get_active_games(self) -> List[PokerNowGame]:
        """
        Get all games that are not expired.
        
        Returns:
            List of active PokerNowGame objects
        """
        return [g for g in self.games if not g.expired]
    
    def get_players_with_balance(self) -> List[PokerNowPlayer]:
        """
        Get all players with a positive chip balance.
        
        Returns:
            List of PokerNowPlayer objects with chips > 0
        """
        return [p for p in self.players if p.chips_balance > 0]
    
    def total_chips_in_club(self) -> int:
        """
        Calculate the total chips across all players in the club.
        
        Returns:
            Total chip count
        """
        return sum(p.chips_balance for p in self.players)
    
    # Convenience methods that delegate to the session
    
    def _require_session(self):
        """Raise an error if no session is available."""
        if not self._session:
            raise RuntimeError(
                "This club instance does not have an associated session. "
                "Obtain the club via session.get_club() to use this method."
            )
    
    def add_chips_to_player(self, player_id: str, amount: int, reason: str) -> None:
        """
        Add chips to a player's balance.
        
        Args:
            player_id: The club player ID
            amount: Amount of chips to add
            reason: Reason for adding chips
        """
        self._require_session()
        self._session.add_club_chips_to_player(self.id, player_id, amount, reason)
    
    def remove_chips_from_player(self, player_id: str, amount: int, reason: str) -> None:
        """
        Remove chips from a player's balance.
        
        Args:
            player_id: The club player ID
            amount: Amount of chips to remove
            reason: Reason for removing chips
        """
        self._require_session()
        self._session.remove_club_chips_from_player(self.id, player_id, amount, reason)
    
    def set_credit_limit_for_player(self, player_id: str, amount: int) -> None:
        """
        Set the credit limit for a player.
        
        Args:
            player_id: The club player ID
            amount: New credit limit amount
        """
        self._require_session()
        self._session.set_club_credit_limit_for_player(self.id, player_id, amount)
    
    def get_player_transactions(self, player_id: str) -> List[PokerNowTransaction]:
        """
        Get transaction history for a player.
        
        Args:
            player_id: The club player ID
            
        Returns:
            List of PokerNowTransaction objects
        """
        self._require_session()
        return self._session.get_club_player_transactions(self.id, player_id)
    
    def set_player_role(self, player_user_id: str, role: str) -> None:
        """
        Set a player's role in the club.
        
        Args:
            player_user_id: The user's network ID (not club player ID)
            role: New role ('owner', 'manager', 'member')
        """
        self._require_session()
        self._session.set_club_player_role(self.id, player_user_id, role)
    
    def create_game(self, config: 'PokerGameConfig') -> str:
        """
        Create a new game in the club.
        
        Args:
            config: PokerGameConfig object with game settings
            
        Returns:
            Game ID of the created game
        """
        self._require_session()
        return self._session.create_club_game(self.id, config)
    
    def create_preset(self, config: 'PokerGameConfig') -> None:
        """
        Create a game preset in the club.
        
        Args:
            config: PokerGameConfig object with preset settings
        """
        self._require_session()
        self._session.create_club_preset(self.id, config)
    
    def close_game(self, game_id: str) -> None:
        """
        Close an active game.
        
        Args:
            game_id: The game ID to close
        """
        self._require_session()
        self._session.close_club_game(self.id, game_id)
    
    def set_ledger_visibility(self, show: bool) -> None:
        """
        Set ledger visibility for all members.
        
        Args:
            show: True to show ledger to all members, False to restrict
        """
        self._require_session()
        self._session.set_club_ledger_visibility(self.id, show)
    
    def set_play_report_visibility(self, show: bool) -> None:
        """
        Set play report visibility for all members.
        
        Args:
            show: True to show play report to all members, False to restrict
        """
        self._require_session()
        self._session.set_club_play_report_visibility(self.id, show)
    
    def set_game_archive_visibility(self, show: bool) -> None:
        """
        Set game archive visibility for all members.
        
        Args:
            show: True to show archive to all members, False to restrict
        """
        self._require_session()
        self._session.set_club_game_archive_visibility(self.id, show)
    
    def set_p2p_transfers(self, enabled: bool) -> None:
        """
        Enable or disable player-to-player chip transfers.
        
        Args:
            enabled: True to enable P2P transfers, False to disable
        """
        self._require_session()
        self._session.set_club_p2p_transfers(self.id, enabled)
    
    def set_exclusivity(self, option: str, message: str = "") -> None:
        """
        Set club exclusivity settings.
        
        Args:
            option: Exclusivity option ('manual', 'approve', 'reject')
            message: Rejection message (only used if option is 'reject')
        """
        self._require_session()
        self._session.set_club_exclusivity(self.id, option, message)
    
    def __repr__(self) -> str:
        return f"PokerNowClub(name='{self.name}', players={len(self.players)}, games={len(self.games)})"


class PokerGameConfig:
    """
    Configuration for creating a poker game or preset.
    
    This class handles the default settings and conversion to the format
    required by the PokerNow API.
    """
    
    DEFAULTS = {
        'gameType': 'th',
        'showdownSpeed': 'n',
        'rabbitHunting': 'true',
        'runItTwice': 'ask_players',
        'straddle': 'true',
        'guestChat': 'true',
        'dealAway': 'false',
        'allowWaitlist': 'false',
        'finishedTimerForceAway': 'true',
        'revealAllHands': 'true',
        'spectatorMode': 'false',
        'allowAddOns': 'true',
        'recordHighHand': 'false',
        'filterBadWords': 'false',
        'uniqueIpCheck': 'false',
        'tableNameColor': '#ffffff',
        'maxQuantityPlayers': '10',
        'minBuyIn': '',
        'maxBuyIn': '',
        'decisionTime': '20',
        'timebank': '10',
        'timebankResetHands': '10',
        'ratholingMinutesLimit': '',
        'feltPortrait': '',
        'feltLandscape': '',
        'bombPotProbability': '10',
        'bombPotBBQty': '5',
        'sevenDeuceBounty': '500',
        'rake': 'false',
        'rakeRequiresFlop': 'true',
        'rakePercentage': '',
        'maxRakeValue': '',
        'minPotRakeValue': '',
        'rakeMaxPlayers2': '',
        'rakePercentage2': '',
        'maxRakeValue2': '',
        'minPotRakeValue2': '',
        'onFinishRakeCredits': 'stop-game',
        'doubleBoard': '',
        'bustOutAction': 'standUp',
        'collectedRakeVisibility': 'owner',
        'maxRebuyCount': '-1',
        'rebuyIntervalSeconds': '20',
        'waitlistOfflineTimeoutSeconds': '',
        'themeId': 'undefined',
        'gameTypeCycling': '',
        'gameTypeCyclingSchema': '',
        'gameTypeCyclingStopAtBlindLevel': '',
        'gameTypeCyclingSchemaLastGameType': '',
    }

    def __init__(self, name: str, small_blind: int, big_blind: int, **kwargs):
        """
        Initialize a game configuration.
        
        Args:
            name: Table name
            small_blind: Small blind amount
            big_blind: Big blind amount
            **kwargs: Additional game settings (override defaults)
        """
        self.name = name
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.settings = {**self.DEFAULTS, **kwargs}

    def to_dict(self, is_preset: bool = False) -> Dict[str, Any]:
        """
        Convert configuration to API format.
        
        Args:
            is_preset: Whether this is for a preset or a game
            
        Returns:
            Dictionary formatted for the API
        """
        def prefix_key(k: str) -> str:
            """Add config[] prefix for presets."""
            if not is_preset:
                return k
            if '[' in k:
                return f"config[{k.replace('[', '][', 1)}]"
            return f"config[{k}]"
        
        return {
            prefix_key("tableName"): self.name,
            prefix_key("blinds[0][]"): [
                str(self.small_blind),
                str(self.big_blind),
                '', '', 'false'
            ],
            prefix_key("blindString"): f"[[{self.small_blind},{self.big_blind},null,null,false]]",
            **{prefix_key(k): v for k, v in self.settings.items()}
        }


class PokerNowSession:
    """
    Session for interacting with the PokerNow API.
    
    This class handles authentication and provides methods for
    managing clubs, players, and games.
    """
    
    def __init__(self, apt_token: str):
        """
        Initialize a PokerNow session.
        
        Args:
            apt_token: Authentication token from pokernow.club cookies
        """
        self.session = requests.Session()
        self.session.cookies.update({'apt': apt_token})
        
    def get_club(self, slug: str) -> PokerNowClub:
        """
        Fetch club data from PokerNow.
        
        Args:
            slug: The club's URL slug
            
        Returns:
            PokerNowClub object with session attached
            
        Raises:
            ValueError: If the club cannot be found
        """
        response = self.session.get(f'https://www.pokernow.club/clubs/{slug}')
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        embedded_club = soup.find(id="embedded-club")
        
        if not embedded_club:
            raise ValueError(f"Could not find club data for club slug: {slug}")
        
        club_data = json.loads(embedded_club.string)
        return PokerNowClub(club_data, session=self)
    
    def create_club(self, slug: str, name: str, description: str, use_cents: bool = False) -> PokerNowClub:
        """
        Create a new club (requires premium subscription).
        
        Args:
            slug: Desired club URL slug
            name: Club name
            description: Club description
            use_cents: Whether to use cents in the club
            
        Returns:
            PokerNowClub object for the created club
            
        Raises:
            ValueError: If club creation fails
        """
        data = {
            'slug': slug,
            'name': name,
            'description': description,
            'use_cents': 'true' if use_cents else 'false',
        }

        response = self.session.post('https://www.pokernow.club/clubs/club/create', data=data)
        response.raise_for_status()
        
        result = response.json()
        if not result.get('success', False):
            raise ValueError(f"Could not create club: {result.get('errmsg', 'Unknown error')}")
        
        return PokerNowClub(result.get('club'), session=self)
        
    def create_stripe_checkout(self, mode: str, plan: str, receiver_player_id: str = "") -> str:
        """
        Create a Stripe checkout session for subscription payment.
        
        Args:
            mode: Payment mode (e.g., 'month', 'year')
            plan: Plan type (e.g., 'platinum')
            receiver_player_id: Optional player ID to receive the subscription
            
        Returns:
            URL for the Stripe checkout session
        """
        params = {
            'mode': mode,
            'plan': plan,
            'receiver_player_id': receiver_player_id,
        }
        
        response = self.session.get('https://www.pokernow.club/subscription/checkout', params=params)
        return response.url
    
    def handle_payment_callback(self, session_id: str) -> str:
        """
        Handle payment callback from Stripe.
        
        Args:
            session_id: Stripe session ID
            
        Returns:
            Response text from the callback
        """
        params = {'session_id': session_id}
        response = self.session.get('https://www.pokernow.club/subscription/payment-back', params=params)
        return response.text
    
    def set_club_ledger_visibility(self, club_id: str, show: bool) -> None:
        """
        Toggle ledger visibility for all club members.
        
        Args:
            club_id: The club ID
            show: True to show ledger to all members
        """
        data = {
            'clubId': club_id,
            'enabled': 'true' if show else 'false',
        }
        response = self.session.post('https://www.pokernow.club/clubs/club/ledger/all', data=data)
        response.raise_for_status()
    
    def set_club_play_report_visibility(self, club_id: str, show: bool) -> None:
        """
        Toggle play report visibility for all club members.
        
        Args:
            club_id: The club ID
            show: True to show play report to all members
        """
        data = {
            'clubId': club_id,
            'enabled': 'true' if show else 'false',
        }
        response = self.session.post('https://www.pokernow.club/clubs/club/playreport/all', data=data)
        response.raise_for_status()
    
    def set_club_game_archive_visibility(self, club_id: str, show: bool) -> None:
        """
        Toggle game archive visibility for all club members.
        
        Args:
            club_id: The club ID
            show: True to show archive to all members
        """
        data = {
            'clubId': club_id,
            'enabled': 'true' if show else 'false',
        }
        response = self.session.post('https://www.pokernow.club/clubs/club/archive/all', data=data)
        response.raise_for_status()
    
    def set_club_p2p_transfers(self, club_id: str, enabled: bool) -> None:
        """
        Enable or disable player-to-player chip transfers.
        
        Args:
            club_id: The club ID
            enabled: True to enable P2P transfers
        """
        data = {
            'clubId': club_id,
            'enabled': 'true' if enabled else 'false',
        }
        response = self.session.post('https://www.pokernow.club/clubs/club/player/2/player', data=data)
        response.raise_for_status()
    
    def set_club_exclusivity(self, club_id: str, option: str, message: str = "") -> None:
        """
        Set club exclusivity settings.
        
        Args:
            club_id: The club ID
            option: Exclusivity option ('manual', 'approve', 'reject')
            message: Rejection message (for 'reject' option)
        """
        data = {
            'clubId': club_id,
            'otherDomainAction': option,
            'otherRejectMessage': message,
        }
        response = self.session.post(
            'https://www.pokernow.club/clubs/club/updatesettingattributes',
            data=data
        )
        response.raise_for_status()
    
    def create_club_preset(self, club_id: str, config: PokerGameConfig) -> None:
        """
        Create a game preset in the club.
        
        Args:
            club_id: The club ID
            config: PokerGameConfig object with preset settings
        """
        data = config.to_dict(is_preset=True)
        data.update({'clubId': club_id, 'presetName': config.name})
        
        response = self.session.post('https://www.pokernow.club/clubs/club-preset', data=data)
        response.raise_for_status()

    def create_club_game(self, club_id: str, config: PokerGameConfig) -> str:
        """
        Create a new game in the club.
        
        Args:
            club_id: The club ID
            config: PokerGameConfig object with game settings
            
        Returns:
            Game ID of the created game
        """
        data = config.to_dict(is_preset=False)
        data['clubId'] = club_id
        
        response = self.session.post('https://www.pokernow.club/clubs/club/game/create', data=data)
        response.raise_for_status()
        
        return response.json().get('game', {}).get('game', {}).get('id', '')

    def close_club_game(self, club_id: str, game_id: str) -> None:
        """
        Close an active game in the club.
        
        Args:
            club_id: The club ID
            game_id: The game ID to close
            
        Raises:
            ValueError: If the game cannot be closed
        """
        data = {
            'clubId': club_id,
            'gameId': game_id,
        }
        
        response = self.session.post('https://www.pokernow.club/clubs/club/game/close', data=data)
        response.raise_for_status()
        
        if not response.json().get('success', False):
            raise ValueError(f"Could not close game: {response.text}")

    def add_club_chips_to_player(self, club_id: str, player_id: str, amount: int, reason: str) -> None:
        """
        Add chips to a player's balance.
        
        Args:
            club_id: The club ID
            player_id: The club player ID
            amount: Amount of chips to add
            reason: Reason for adding chips
        """
        data = {
            'quantity': str(amount),
            'reason': reason,
        }
        response = self.session.post(
            f'https://www.pokernow.club/clubs/chips/add/{club_id}/{player_id}',
            data=data
        )
        response.raise_for_status()
    
    def remove_club_chips_from_player(self, club_id: str, player_id: str, amount: int, reason: str) -> None:
        """
        Remove chips from a player's balance.
        
        Args:
            club_id: The club ID
            player_id: The club player ID
            amount: Amount of chips to remove
            reason: Reason for removing chips
            
        Raises:
            ValueError: If chips cannot be removed
        """
        data = {
            'quantity': str(amount),
            'reason': reason,
        }
        response = self.session.post(
            f'https://www.pokernow.club/clubs/chips/remove/{club_id}/{player_id}',
            data=data
        )
        response.raise_for_status()
        
        if not response.json().get('success', False):
            raise ValueError(f"Could not remove chips: {response.json().get('errmsg', 'Unknown error')}")
        
    def set_club_credit_limit_for_player(self, club_id: str, player_id: str, amount: int) -> None:
        """
        Set the credit limit for a player.
        
        Args:
            club_id: The club ID
            player_id: The club player ID
            amount: New credit limit amount
            
        Raises:
            ValueError: If credit limit cannot be set
        """
        data = {
            'clubId': club_id,
            'networkUserId': player_id,
            'creditLimit': str(amount),
        }
        response = self.session.post('https://www.pokernow.club/clubs/chips/creditlimit', data=data)
        response.raise_for_status()
        
        if not response.json().get('success', False):
            raise ValueError(f"Could not set credit limit: {response.json().get('errmsg', 'Unknown error')}")
        
    def get_club_player_transactions(self, club_id: str, player_id: str) -> List[PokerNowTransaction]:
        """
        Get transaction history for a player.
        
        Args:
            club_id: The club ID
            player_id: The club player ID
            
        Returns:
            List of PokerNowTransaction objects
        """
        response = self.session.get(
            f'https://www.pokernow.club/clubs/wallet/movements/{club_id}/{player_id}'
        )
        response.raise_for_status()
        
        data = response.json()
        return [PokerNowTransaction(m) for m in data.get('movements', [])]

    def set_club_player_role(self, club_id: str, player_user_id: str, role: str) -> None:
        """
        Set a player's role in the club.
        
        Args:
            club_id: The club ID
            player_user_id: The user's network ID (not club player ID)
            role: New role ('owner', 'manager', 'member')
            
        Raises:
            ValueError: If role cannot be set
        """
        data = {
            'clubId': club_id,
            'user_id': player_user_id,
            'club_role': role,
        }
        response = self.session.post('https://www.pokernow.club/clubs/club/player/role', data=data)
        response.raise_for_status()
        
        if not response.json().get('success', False):
            raise ValueError(f"Could not set player role: {response.json().get('errmsg', 'Unknown error')}")

    def update_user(self, username: str, email: str) -> None:
        """
        Update the current user's profile information.
        
        Args:
            username: The username to set
            email: The email address to set
            
        Raises:
            ValueError: If the user update fails
        """
        # Get CSRF token from edit page
        response = self.session.get('https://network.pokernow.club/current_user/edit')
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('meta', attrs={'name': 'csrf-token'})['content']
        
        # Update user profile
        data = {
            'utf8': '✓',
            '_method': 'patch',
            'authenticity_token': csrf_token,
            'back_to': '',
            'current_user_update[username]': username,
            'current_user_update[email]': email,
        }
        
        response = self.session.post('https://network.pokernow.club/current_user', data=data)
        response.raise_for_status()


def login(email: str, otp_callback: 'Callable[[str], str]') -> PokerNowSession:
    """
    Login to PokerNow using email and OTP.
    
    Args:
        email: Email address for login
        otp_callback: Function that takes email and returns the OTP code
        
    Returns:
        PokerNowSession object for the authenticated user
        
    Example:
        >>> def get_otp(email):
        ...     return input(f"Enter OTP sent to {email}: ")
        >>> session = login("your@email.com", get_otp)
    """
    session = requests.Session()
    
    # Get CSRF token from login page
    res = session.get("https://network.pokernow.club/sessions/new")
    soup = BeautifulSoup(res.text, 'html.parser')
    csrf_token = soup.find('meta', attrs={'name': 'csrf-token'})['content']
    
    # Request OTP
    params = {'back_to': 'https://www.pokernow.club/'}
    data = {
        'utf8': '✓',
        'authenticity_token': csrf_token,
        'user_login_form[email]': email,
        'commit': 'Send me the Login Code',
    }
    response = session.post('https://network.pokernow.club/sessions', params=params, data=data)
    
    # Get new CSRF token
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('meta', attrs={'name': 'csrf-token'})['content']
    
    # Get OTP from callback
    otp = otp_callback(email)
    
    # Submit OTP
    params = {
        'back_to': 'https://www.pokernow.club/',
        'code_confirmation': 'true',
    }
    data = {
        'utf8': '✓',
        'authenticity_token': csrf_token,
        'user_login_code_form[code]': otp,
        'commit': 'Confirm my Login Code',
    }
    response = session.post('https://network.pokernow.club/sessions', params=params, data=data)
    
    # Extract apt token from cookies
    apt_token = session.cookies.get('apt')
    if not apt_token:
        raise ValueError("Login failed: Could not retrieve authentication token")
    
    return PokerNowSession(apt_token)
