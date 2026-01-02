
from plexflow.core.plex.hooks.plex_authorized import PlexAuthorizedHttpHook
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Optional

@dataclass_json
@dataclass
class User:
    id: Optional[str]
    avatar: Optional[str]
    username: Optional[str]
    displayName: Optional[str]
    isBlocked: Optional[bool]
    isMuted: Optional[bool]
    isHidden: Optional[bool]

@dataclass_json
@dataclass
class Comment:
    date: Optional[str]
    id: Optional[str]
    message: Optional[str]
    user: Optional[User]

def get_comments(activity_id):
    """
    Retrieves comments for a specific activity.

    Args:
        activity_id (str): The ID of the activity to retrieve comments for.

    Returns:
        list: A list of Comment objects representing the comments for the activity.

    Raises:
        HTTPError: If there was an error while making the API request.

    Example:
        >>> comments = get_comments("12345")
        >>> for comment in comments:
        ...     print(comment.message)
    """
    hook = PlexAuthorizedHttpHook(method="POST", http_conn_id="plex_community", config_folder="config")
    
    data = {
        "query": "query getActivityComments($id: ID!, $first: PaginationInt, $after: String, $last: PaginationInt, $before: String) { activityComments(first: $first after: $after id: $id last: $last before: $before) { nodes { date id message user { id avatar username displayName isBlocked isMuted isHidden } } pageInfo { endCursor hasNextPage hasPreviousPage startCursor } } }",
        "variables": {"first": 50, "id": activity_id},
        "operationName": "getActivityComments"
    }
            
    response = hook.run(
        endpoint="/api",
        json=data,
    )
    
    response.raise_for_status()
    
    return [Comment.from_dict(node) for node in response.json()["data"]["activityComments"]["nodes"]]

def create_comment(activity_id, message):
    """
    Create a comment for a given activity.

    Args:
        activity_id (str): The ID of the activity to create the comment for.
        message (str): The content of the comment.

    Returns:
        Comment: The created comment object.

    Raises:
        HTTPError: If the request to create the comment fails.

    Example:
        >>> create_comment("12345", "Great work!")
    """
    hook = PlexAuthorizedHttpHook(method="POST", http_conn_id="plex_community", config_folder="config")
    
    data = {
        "query": "mutation createComment($input: CreateCommentInput!) { createComment(input: $input) { date id message user { id avatar username displayName isHidden isMuted isBlocked } } }",
        "variables": {"input": {"activity": activity_id, "message": message}},
        "operationName": "createComment"
    }
    
    response = hook.run(endpoint="/api", json=data)
    response.raise_for_status()
