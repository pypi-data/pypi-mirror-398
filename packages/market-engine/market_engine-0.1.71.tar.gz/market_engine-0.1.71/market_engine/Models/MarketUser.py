import asyncio
from typing import Dict, List, Union, Any

from ..Common import fetch_api_data, cache_manager, session_manager


class MarketUser:
    """
    Represents a user on warframe.market
    """
    base_api_url: str = "https://api.warframe.market/v1"  # Base URL for warframe.market API
    base_api_url_v2: str = "https://api.warframe.market/v2"  # Base URL for warframe.market API v2
    base_url: str = "https://warframe.market/profile"  # Base URL for warframe.market profiles
    asset_url: str = "https://warframe.market/static/assets"  # Base URL for warframe.market assets

    def __init__(self, database: "MarketDatabase", user_id: str, username: str):
        """
        Initializes a MarketUser object.
        :param database: database object
        :param user_id: the user's warframe.market id
        :param username: the user's warframe.market username
        """
        self.database = database
        self.user_id = user_id
        self.username = username
        # Keep slug (API provides 'slug') separate but keep username in sync where possible
        self.slug: Union[str, None] = username
        self.profile_url: str = f"{MarketUser.base_url}/{self.username}"
        self.last_seen = None
        self.avatar = None
        self.avatar_url = None
        self.locale = None
        self.background = None
        self.about = None
        self.reputation = None
        self.platform = None
        self.banned = None
        self.status = None
        self.region = None
        # New fields from the updated API
        self.role = None
        self.tier = None
        self.mastery_rank = None
        self.crossplay = None
        self.activity: Dict[str, Any] = {}

        self.orders: Dict[str, List[Dict[str, Union[str, int]]]] = {'buy': [], 'sell': []}
        self.reviews: List[str] = []

    @classmethod
    async def create(cls, database: "MarketDatabase", user_id: str, username: str,
                     fetch_user_data: bool = True, fetch_orders: bool = True, fetch_reviews: bool = True,
                     review_page_nums: Union[int, List[int]] = 1):
        """
        Creates a MarketUser object.
        :param database: database object
        :param user_id: the user's warframe.market id
        :param username: the user's warframe.market username
        :param fetch_user_data: whether or not to fetch the user's data from warframe.market
        :param fetch_orders: whether or not to fetch the user's orders from warframe.market
        :param fetch_reviews: whether or not to fetch the user's reviews from warframe.market
        :param review_page_nums: the page number(s) to fetch reviews from (integer or list of integers)
        :return: MarketUser object with the specified data
        """
        obj = cls(database, user_id, username)

        tasks = []
        if fetch_user_data:
            profile = await MarketUser.fetch_user_data(username)
            if profile is not None:
                obj.set_user_data(profile)
            else:
                return None

        if fetch_orders:
            tasks.append(obj.fetch_orders())

        if fetch_reviews:
            tasks.append(obj.fetch_reviews(review_page_nums))

        await asyncio.gather(*tasks)

        return obj

    @staticmethod
    async def fetch_user_data(username) -> Union[None, Dict]:
        """
        Fetches a user's data from warframe.market
        :param username: the user's warframe.market username, case-sensitive
        :return: the user's data
        """
        async with cache_manager() as cache, session_manager() as session:
            user_data = await fetch_api_data(session=session,
                                             cache=cache,
                                             url=f"{MarketUser.base_api_url_v2}/user/{username}",
                                             expiration=20)

        if user_data is None:
            return

        # Load the user profile
        try:
            profile = user_data['data']
        except KeyError:
            return

        return profile

    def set_user_data(self, profile: Dict[str, Any]) -> None:
        """
        Sets the user's data based on the values returned from the API.
        :param profile: the user's profile data
        :return: None
        """
        # The API now returns camelCase keys (e.g. id, slug, ingameName, lastSeen, masteryRank, crossplay)
        # Map them to our internal snake_case attributes and maintain backwards compatibility.

        # id -> user_id
        if 'id' in profile:
            self.user_id = profile.get('id')

        # username can come as 'slug' or 'ingameName' (prefer slug for URLs)
        if 'slug' in profile:
            self.username = profile.get('slug')
            self.slug = profile.get('slug')
        elif 'ingameName' in profile:
            # fall back to ingameName if slug not provided
            self.username = profile.get('ingameName')
            self.slug = profile.get('ingameName')

        # lastSeen -> last_seen
        if 'lastSeen' in profile:
            self.last_seen = profile.get('lastSeen')
        elif 'last_seen' in profile:
            self.last_seen = profile.get('last_seen')

        # avatar and background and about
        if 'avatar' in profile:
            self.avatar = profile.get('avatar')
        elif 'avatarUrl' in profile:
            # some older formats might use avatarUrl
            self.avatar = profile.get('avatarUrl')

        if 'background' in profile:
            self.background = profile.get('background')
        elif 'backgroundUrl' in profile:
            self.background = profile.get('backgroundUrl')

        if 'about' in profile:
            self.about = profile.get('about')

        # reputation
        if 'reputation' in profile:
            self.reputation = profile.get('reputation')

        # mastery rank
        if 'masteryRank' in profile:
            self.mastery_rank = profile.get('masteryRank')
        elif 'mastery_rank' in profile:
            self.mastery_rank = profile.get('mastery_rank')

        # status, platform, locale
        if 'status' in profile:
            self.status = profile.get('status')
        if 'platform' in profile:
            self.platform = profile.get('platform')
        if 'locale' in profile:
            self.locale = profile.get('locale')

        # crossplay
        if 'crossplay' in profile:
            self.crossplay = profile.get('crossplay')

        # role and tier
        if 'role' in profile:
            self.role = profile.get('role')
        if 'tier' in profile:
            self.tier = profile.get('tier')

        # activity (object)
        if 'activity' in profile:
            self.activity = profile.get('activity') or {}

        # backwards-compatible fields
        for key, value in profile.items():
            # set any attribute that matches existing attribute names
            if hasattr(self, key):
                setattr(self, key, value)

        # recompute derived URLs
        if self.avatar is not None:
            # avatar from API is a path; build a full URL to the asset
            # Keep original querystring if present
            self.avatar_url = f"{MarketUser.asset_url}/{self.avatar}"

        # ensure profile_url reflects current username/slug
        if self.username:
            self.profile_url = f"{MarketUser.base_url}/{self.username}"

    def parse_orders(self, orders: List[Dict[str, Any]]) -> None:
        """
        Parses the user's orders from the new flat list format returned by the API.
        :param orders: the user's orders from the API (flat list)
        :return: None
        """
        self.orders: Dict[str, List[Dict[str, Union[str, int]]]] = {'buy': [], 'sell': []}

        for order in orders:
            # New format: flat list with 'type' field indicating 'buy' or 'sell'
            order_type = order.get('type', 'sell')  # 'buy' or 'sell'

            parsed_order = {
                'order_id': order.get('id'),
                'item_id': order.get('itemId'),
                'last_update': order.get('updatedAt'),
                'quantity': order.get('quantity'),
                'price': order.get('platinum'),
                'visible': order.get('visible'),
                'created_at': order.get('createdAt'),
                'item_id': order.get('itemId'),
            }


            item = self.database.get_item_by_id(parsed_order['item_id'])
            if item is not None:
                parsed_order['item'] = item['item_name']
                parsed_order['item_url_name'] = item['url_name']

            # Handle rank if present
            if 'rank' in order and order['rank'] is not None and order['rank'] > 0:
                parsed_order['subtype'] = f"R{order['rank']}"

            # Handle perTrade if needed
            if 'perTrade' in order:
                parsed_order['per_trade'] = order['perTrade']

            self.orders[order_type].append(parsed_order)

    def parse_reviews(self, reviews: List[Dict[str, Any]]) -> None:
        """
        Parses the user's reviews.
        :param reviews: the user's reviews from the API
        :return: None
        """
        for review in reviews:
            parsed_review = {
                'user': review['user_from']['ingame_name'],
                'user_id': review['user_from']['id'],
                'user_avatar': review['user_from']['avatar'],
                'user_region': review['user_from']['region'],
                'text': review['text'],
                'date': review['date'],
            }

            if parsed_review not in self.reviews:
                self.reviews.append(parsed_review)

    async def fetch_orders(self) -> None:
        """
        Fetches the user's orders from warframe.market
        :return: None
        """
        async with cache_manager() as cache, session_manager() as session:
            orders = await fetch_api_data(cache=cache,
                                          session=session,
                                          url=f"{self.base_api_url_v2}/orders/user/{self.username}",
                                          expiration=60)

        if orders is None:
            return

        self.parse_orders(orders['data'])

    async def fetch_reviews(self, page_nums: Union[int, List[int]]) -> None:
        """
        Fetches the user's reviews from warframe.market for the specified page numbers.
        :param page_nums: the page number(s) to fetch (integer or list of integers)
        :return: None
        """
        if isinstance(page_nums, int):
            page_nums = [page_nums]

        tasks = []
        async with session_manager() as session, cache_manager() as cache:
            for page_num in page_nums:
                url = f"{self.base_api_url}/profile/{self.username}/reviews/{page_num}"
                tasks.append(fetch_api_data(session=session,
                                            url=url,
                                            cache=cache,
                                            expiration=60))

            results = await asyncio.gather(*tasks)

            for reviews in results:
                if reviews is not None:
                    self.parse_reviews(reviews['payload']['reviews'])

    def to_dict(self):
        """
        Convert the MarketUser object to a dictionary suitable for JSON serialization.
        """
        user_dict = {
            'user_id': self.user_id,
            'username': self.username,
            'slug': self.slug,
            'profile_url': self.profile_url,
            'last_seen': self.last_seen,
            'avatar': self.avatar,
            'avatar_url': self.avatar_url,
            'locale': self.locale,
            'background': self.background,
            'about': self.about,
            'reputation': self.reputation,
            'platform': self.platform,
            'crossplay': self.crossplay,
            'role': self.role,
            'tier': self.tier,
            'mastery_rank': self.mastery_rank,
            'status': self.status,
            'region': self.region,
            'activity': self.activity,
            'orders': self.orders,
            'reviews': self.reviews
        }
        return user_dict

