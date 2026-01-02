import datetime
from typing import Optional, Any
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json, Undefined
from plexflow.core.plex.hooks.plex_authorized import PlexAuthorizedHttpHook
from plexflow.core.plex.discover.comment import Comment, create_comment, get_comments


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MetadataItem:
    id: Optional[str] = None
    images: Optional[dict] = None
    userState: Optional[dict] = None
    title: Optional[str] = None
    key: Optional[str] = None
    type: Optional[str] = None
    index: Optional[int] = None
    publicPagesURL: Optional[str] = None
    parent: Optional[dict] = None
    grandparent: Optional[dict] = None
    publishedAt: Optional[str] = None
    leafCount: Optional[int] = None
    year: Optional[int] = None
    originallyAvailableAt: Optional[str] = None
    childCount: Optional[int] = None
    catchall: Optional[Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.parent:
            self.parent = MetadataItem(**self.parent)
        if self.grandparent:
            self.grandparent = MetadataItem(**self.grandparent)
        if self.images:
            self.images = ImageUrls(**self.images)
        if self.userState:
            self.userState = UserState(**self.userState)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class UserV2:
    id: Optional[str] = None
    username: Optional[str] = None
    displayName: Optional[str] = None
    avatar: Optional[str] = None
    friendStatus: Optional[str] = None
    isMuted: Optional[bool] = None
    isBlocked: Optional[bool] = None
    mutualFriends: Optional[dict] = None

    def __post_init__(self):
        if self.mutualFriends:
            self.mutualFriends = MutualFriends(**self.mutualFriends)

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ImageUrls:
    coverArt: Optional[str] = None
    coverPoster: Optional[str] = None
    thumbnail: Optional[str] = None
    art: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class UserState:
    viewCount: Optional[int] = None
    viewedLeafCount: Optional[int] = None
    watchlistedAt: Optional[str] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MutualFriends:
    count: Optional[int] = None
    friends: Optional[list] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ActivityData:
    typename: Optional[str] = field(default= None, metadata=config(field_name="__typename"))
    id: Optional[str] = None
    date: Optional[str] = None
    isPrimary: Optional[bool] = None
    commentCount: Optional[int] = None
    privacy: Optional[str] = None
    isMuted: Optional[bool] = None
    metadataItem: Optional[MetadataItem] = None
    userV2: Optional[UserV2] = None
    catchall: Optional[Any] = field(default_factory=dict)

from datetime import datetime
from typing import List
import requests

class Activity:
    """
    Represents an activity in Plex.

    Attributes:
        WATCH_HISTORY (str): Constant representing the watch history activity.
        METADATA_MESSAGE (str): Constant representing the metadata message activity.
        WATCHLIST (str): Constant representing the watchlist activity.
    """

    WATCH_HISTORY = "ActivityWatchHistory"
    METADATA_MESSAGE = "ActivityMetadataMessage"
    WATCHLIST = "ActivityWatchlist"
    
    def __init__(self, data: dict):
        """
        Initializes a new instance of the Activity class.

        Args:
            data (dict): The data for the activity.
            hook (PlexAuthorizedHttpHook): The Plex authorized HTTP hook.
        """
        self.data = ActivityData.from_dict(data)

    def __str__(self):
        """
        Returns a string representation of the activity.

        Returns:
            str: The string representation of the activity.
        """
        return f"{self.data.typename} with ID {self.data.id}"

    def __repr__(self):
        """
        Returns a string representation of the activity.

        Returns:
            str: The string representation of the activity.
        """
        return f"{self.data.typename} with ID {self.data.id}"
    
    @property
    def typename(self):
        """
        Gets the typename of the activity.

        Returns:
            str: The typename of the activity.
        """
        return self.data.typename
    
    @property
    def id(self):
        """
        Gets the ID of the activity.

        Returns:
            str: The ID of the activity.
        """
        return self.data.id
    
    @property
    def date(self):
        """
        Gets the date of the activity.

        Returns:
            datetime: The date of the activity.
        """
        return datetime.fromisoformat(self.data.date.replace("Z", "+00:00"))
    
    @property
    def isPrimary(self):
        """
        Gets a value indicating whether the activity is primary.

        Returns:
            bool: True if the activity is primary, False otherwise.
        """
        return self.data.isPrimary
    
    @property
    def commentCount(self):
        """
        Gets the comment count of the activity.

        Returns:
            int: The comment count of the activity.
        """
        return self.data.commentCount
    
    @property
    def privacy(self):
        """
        Gets the privacy of the activity.

        Returns:
            str: The privacy of the activity.
        """
        return self.data.privacy
    
    @property
    def isMuted(self):
        """
        Gets a value indicating whether the activity is muted.

        Returns:
            bool: True if the activity is muted, False otherwise.
        """
        return self.data.isMuted
    
    @property
    def metadataItem(self):
        """
        Gets the metadata item of the activity.

        Returns:
            str: The metadata item of the activity.
        """
        return self.data.metadataItem
    
    @property
    def userV2(self):
        """
        Gets the userV2 of the activity.

        Returns:
            str: The userV2 of the activity.
        """
        return self.data.userV2

    @property
    def comments(self) -> List[Comment]:
        """
        Gets the comments for the activity.

        Returns:
            list: The comments for the activity.
        """
        return get_comments(self.id)

    def create_comment(self, message: str):
        """
        Creates a comment for the activity.

        Args:
            message (str): The message for the comment.
        """
        return create_comment(self.id, message)

def get_activities(total: int = 24) -> List[Activity]:
    """
    Retrieves a list of activities from the Plex server.

    Args:
        total (int, optional): The maximum number of activities to retrieve. Defaults to 24.

    Returns:
        list: A list of Activity objects representing the retrieved activities.

    Raises:
        HTTPError: If there is an error in the HTTP request.

    Example:
        >>> activities = get_activities(total=10)
        >>> for activity in activities:
        ...     print(activity.metadataItem.title)
    """
    hook = PlexAuthorizedHttpHook(
        method="POST", http_conn_id="plex_community", config_folder="config"
    )

    query = """
        query GetActivityFeed($first: PaginationInt!, $after: String, $metadataID: ID, $types: [ActivityType!]!, $skipUserState: Boolean = false, $includeDescendants: Boolean = false, $skipWatchSession: Boolean = true) {
            activityFeed(
                first: $first
                after: $after
                metadataID: $metadataID
                types: $types
                includeDescendants: $includeDescendants
            ) {
                nodes {
                    __typename
                    id
                    date
                    isPrimary
                    commentCount
                    privacy
                    isMuted
                    metadataItem {
                        id
                        images {
                            coverArt
                            coverPoster
                            thumbnail
                            art
                        }
                        userState @skip(if: $skipUserState) {
                            viewCount
                            viewedLeafCount
                            watchlistedAt
                        }
                        title
                        key
                        type
                        index
                        publicPagesURL
                        parent {
                            index
                            title
                            publishedAt
                            key
                            type
                            images {
                                coverArt
                                coverPoster
                                thumbnail
                                art
                            }
                            userState @skip(if: $skipUserState) {
                                viewCount
                                viewedLeafCount
                                watchlistedAt
                            }
                        }
                        grandparent {
                            index
                            title
                            publishedAt
                            key
                            type
                            images {
                                coverArt
                                coverPoster
                                thumbnail
                                art
                            }
                            userState @skip(if: $skipUserState) {
                                viewCount
                                viewedLeafCount
                                watchlistedAt
                            }
                        }
                        publishedAt
                        leafCount
                        year
                        originallyAvailableAt
                        childCount
                    }
                    userV2 {
                        id
                        username
                        displayName
                        avatar
                        friendStatus
                        isMuted
                        isBlocked
                        mutualFriends {
                            count
                            friends {
                                avatar
                                displayName
                                id
                                username
                            }
                        }
                    }
                    ... on ActivityMetadataMessage {
                        message
                        otherRecipientsV2 {
                            id
                            username
                            displayName
                            avatar
                            friendStatus
                            isMuted
                            isBlocked
                            mutualFriends {
                                count
                                friends {
                                    avatar
                                    displayName
                                    id
                                    username
                                }
                            }
                        }
                    }
                    ... on ActivityMetadataReport {
                        message
                        otherRecipientsV2 {
                            id
                            username
                            displayName
                            avatar
                            friendStatus
                            isMuted
                            isBlocked
                            mutualFriends {
                                count
                                friends {
                                    avatar
                                    displayName
                                    id
                                    username
                                }
                            }
                        }
                    }
                    ... on ActivityRating {
                        rating
                    }
                    ... on ActivityPost {
                        message
                    }
                    ... on ActivityWatchHistory {
                        watchSession @skip(if: $skipWatchSession)
                    }
                    ... on ActivityWatchSession {
                        episodeCount
                    }
                    ... on ActivityWatchRating {
                        rating
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    """

    data = {
        "query": query,
        "variables": {
            "first": total,
            "types": ["METADATA_MESSAGE", "RATING", "WATCH_HISTORY", "WATCHLIST", "POST", "WATCH_SESSION", "WATCH_RATING"],
            "includeDescendants": True,
            "skipUserState": False,
            "skipWatchSession": True
        },
        "operationName": "GetActivityFeed"
    }

    try:
        response = hook.run(
            endpoint="/api",
            json=data,
        )
        response.raise_for_status()
        return [Activity(node) for node in response.json()["data"]["activityFeed"]["nodes"]]
    except requests.exceptions.HTTPError as e:
        raise requests.HTTPError(f"HTTP request error: {e}")