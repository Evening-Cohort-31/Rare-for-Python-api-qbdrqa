import json
import filetype

from http.server import ThreadingHTTPServer
from nss_handler import HandleRequests, status

from views.comment import (
    create_comment,
    get_comments_by_post_id,
    update_comment,
    get_comment_by_id,
    delete_comment,
)

from views.post import (
    create_post,
    get_user_posts,
    update_post,
    get_all_posts,
    get_post_by_id,
    get_posts_by_tag_id,
    get_unapproved_posts,
    approve_post,
    reject_post,
    submit_post,
    search_posts_by_title,
    delete_post,
    add_reaction,
    get_subscribed_posts,
    get_post_header_image,
    get_posts_by_category_id,
    get_reactions,
    remove_reaction,
)

from views.user import (
    create_user,
    login_user,
    update_user,
    get_user_profile_image,
    get_user,
    list_users,
    delete_subscription,
    add_subscription,
)
from views.category import (
    get_all_categories,
    create_category,
    get_category_by_id,
    update_category,
    delete_category,
)
from views.tag import (
    get_tags,
    get_tag_by_id,
    create_tag,
    update_tag,
    delete_tag,
)

from views.reaction import create_reaction, update_reaction, delete_reaction


class JSONServer(HandleRequests):
    """Server class to handle incoming HTTP requests"""

    def _respond_single_resource(self, response_body):
        """Responds with 404 when a single-resource payload is empty"""
        try:
            parsed = json.loads(response_body)
        except (TypeError, ValueError):
            parsed = None

        if parsed in ({}, None):
            return self.response(
                response_body, status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value
            )

        return self.response(response_body, status.HTTP_200_SUCCESS.value)

    def do_GET(self):
        """Handle GET requests from a client"""
        url = self.parse_url(self.path)
        query_params = url["query_params"]
        response_body = ""

        if url["requested_resource"] == "users":
            # /users or /users/<id>
            if url["pk"] != 0:
                response_body = get_user(url["pk"])
                return self._respond_single_resource(response_body)
            if "image" in query_params:
                user_id = query_params["image"][0]
                image_data = get_user_profile_image(user_id)
                if image_data:
                    try:
                        kind = filetype.guess(image_data)
                        content_type = kind.mime if kind else "image/jpeg"

                        self.send_response(200)
                        self.send_header("Content-Type", content_type)
                        self.send_header("Content-Length", str(len(image_data)))
                        self.send_header("Cache-Control", "max-age=86400")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        self.wfile.write(image_data)
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                else:
                    # Send 404 with no body to avoid ORB blocking
                    self.send_response(404)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                return
            response_body = list_users()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "posts":
            # /posts/<id>
            if url["pk"] != 0:
                if (
                    "subscriptions" in query_params
                    and query_params["subscriptions"][0].lower() == "true"
                ):
                    response_body = get_subscribed_posts(url["pk"])
                    return self.response(response_body, status.HTTP_200_SUCCESS.value)

                # Get user_id from query params (user requesting the post)
                if "user_id" in query_params:
                    user_id = query_params.get("user_id", [None])[0]
                    if user_id:
                        user_id = int(user_id)
                    response_body = get_post_by_id(url["pk"], user_id)
                    return self._respond_single_resource(response_body)

            # /posts?user_id=# or /posts?user_id=#&own_posts=true
            if "user_id" in query_params:
                user_id = query_params["user_id"][0]
                own_posts = (
                    query_params.get("own_posts", ["false"])[0].lower() == "true"
                )
                response_body = get_user_posts(user_id, own_posts)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            # /posts?status=submitted  (admin review queue)
            if "status" in query_params:
                status_value = query_params["status"][0].lower()
                if status_value == "submitted":
                    response_body = get_unapproved_posts()
                    return self.response(response_body, status.HTTP_200_SUCCESS.value)

            if "tag_id" in query_params:
                tag_id = query_params["tag_id"][0]
                response_body = get_posts_by_tag_id(tag_id)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            if "category_id" in query_params:
                category_id = query_params["category_id"][0]
                response_body = get_posts_by_category_id(category_id)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            if "title" in query_params:
                search_term = query_params["title"][0]
                response_body = search_posts_by_title(search_term)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            if "image" in query_params:
                post_id = query_params["image"][0]
                image_data = get_post_header_image(post_id)
                if image_data:
                    try:
                        kind = filetype.guess(image_data)
                        content_type = kind.mime if kind else "image/jpeg"

                        self.send_response(200)
                        self.send_header("Content-Type", content_type)
                        self.send_header("Content-Length", str(len(image_data)))
                        self.send_header("Cache-Control", "max-age=86400")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        self.wfile.write(image_data)
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                else:
                    # Send 404 with no body to avoid ORB blocking
                    self.send_response(404)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                return
            response_body = get_all_posts()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "tags":
            # /tags or /tags/<id>
            if url["pk"] != 0:
                response_body = get_tag_by_id(url["pk"])
                return self._respond_single_resource(response_body)

            response_body = get_tags()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "categories":
            # /categories or /categories/<id>
            if url["pk"] != 0:
                response_body = get_category_by_id(url["pk"])
                return self._respond_single_resource(response_body)

            response_body = get_all_categories()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "comments":
            if url["pk"] != 0:
                response_body = get_comment_by_id(url["pk"])
                return self._respond_single_resource(response_body)
            if "post_id" in query_params:
                post_id = query_params["post_id"][0]
                response_body = get_comments_by_post_id(post_id)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
            return self.response("[]", status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "reactions":
            if url["pk"] != 0:
                pass
            else:
                response_body = get_reactions()
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

        return self.response("", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value)

    def do_DELETE(self):
        """Handle DELETE requests from a client"""
        url = self.parse_url(self.path)
        query_params = url["query_params"]

        if url["requested_resource"] == "posts" and url["pk"] != 0:
            response_body = delete_post(url["pk"])
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "users":
            if url["pk"] != 0:
                if "sub_id" in query_params:
                    response_body = delete_subscription(
                        url["pk"], query_params["sub_id"][0]
                    )
                    return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "categories" and url["pk"] != 0:
            successfully_deleted = delete_category(url["pk"])
            if successfully_deleted:
                return self.response("", status.HTTP_204_SUCCESS_NO_RESPONSE_BODY.value)

        if url["requested_resource"] == "comments" and url["pk"] != 0:
            response_body = delete_comment(url["pk"])
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "tags" and url["pk"] != 0:
            response_body = delete_tag(url["pk"])
            return self.response(response_body, status.HTTP_204_SUCCESS_NO_RESPONSE_BODY.value)

        if url["requested_resource"] == "post_reaction" and url["pk"] != 0:
            response_body = remove_reaction(url["pk"])
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "reactions" and url["pk"] != 0:
            response_body = delete_reaction(url["pk"])
            return self.response(response_body, status.HTTP_200_SUCCESS.value)
        return self.response(
            "Not found", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value
        )

    def do_POST(self):
        """Handle POST requests from a client"""
        url = self.parse_url(self.path)
        query_params = url["query_params"]

        content_type = self.headers.get("content-type", "")
        if content_type.startswith("multipart/form-data"):
            request_body = self.parse_multipart()
        else:
            content_len = int(self.headers.get("content-length", 0))
            request_body = self.rfile.read(content_len)
            if request_body:
                request_body = json.loads(request_body)
            else:
                request_body = {}

        if url["requested_resource"] == "register":
            response_body = create_user(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)

        if url["requested_resource"] == "login":
            response_body = login_user(request_body)
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "comments":
            response_body = create_comment(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)
        if url["requested_resource"] == "postReactions":
            response_body = add_reaction(
                request_body["post_id"],
                request_body["user_id"],
                request_body["reaction_id"],
            )
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)

        if url["requested_resource"] in ("new_post", "post", "posts"):
            response_body = create_post(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)

        if url["requested_resource"] == "categories":
            response_body = create_category(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)

        if url["requested_resource"] == "tags":
            response_body = create_tag(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)

        if url["requested_resource"] == "users":
            if url["pk"] != 0:
                if "sub_id" in query_params:
                    response_body = add_subscription(
                        url["pk"], query_params["sub_id"][0]
                    )
                    return self.response(
                        response_body, status.HTTP_201_SUCCESS_CREATED.value
                    )

        if url["requested_resource"] == "reactions":
            if url["pk"] != 0:
                pass
            else:
                response_body = create_reaction(request_body)
                json_body = json.loads(response_body)
                if json_body.get("ok") is False:
                    return self.response(response_body, status.HTTP_409_CONFLICT.value)
                return self.response(
                    response_body, status.HTTP_201_SUCCESS_CREATED.value
                )

        return self.response("", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value)

    def do_PUT(self):
        """Handle PUT requests from a client"""
        url = self.parse_url(self.path)
        pk = url["pk"]

        content_type = self.headers.get("content-type", "")
        if content_type.startswith("multipart/form-data"):
            request_body = self.parse_multipart()
        else:
            content_len = int(self.headers.get("content-length", 0))
            request_body = self.rfile.read(content_len)
            if request_body:
                request_body = json.loads(request_body)
            else:
                request_body = {}

        if url["requested_resource"] == "posts" and pk != 0:
            # special admin approval/rejection/submission routes: PUT /posts/<id> with body
            # {"action": "approve", "reviewer_id": #} for approval
            # {"action": "reject", "reviewer_id": #, "admin_comments": "..."} for rejection
            # {"action": "submit"} for submission
            if "action" in request_body:
                action = request_body.get("action")

                if action == "approve":
                    reviewer_id = request_body.get("reviewer_id")
                    if not reviewer_id:
                        return self.response(
                            json.dumps(
                                {"error": "'reviewer_id' is required for approval"}
                            ),
                            status.HTTP_400_CLIENT_ERROR_BAD_REQUEST_DATA.value,
                        )
                    response_body = approve_post(pk, reviewer_id)
                    return self.response(response_body, status.HTTP_200_SUCCESS.value)

                elif action == "reject":
                    reviewer_id = request_body.get("reviewer_id")
                    if not reviewer_id:
                        return self.response(
                            json.dumps(
                                {"error": "'reviewer_id' is required for rejection"}
                            ),
                            status.HTTP_400_CLIENT_ERROR_BAD_REQUEST_DATA.value,
                        )
                    admin_comments = request_body.get("admin_comments")
                    response_body = reject_post(pk, reviewer_id, admin_comments)
                    return self.response(response_body, status.HTTP_200_SUCCESS.value)

                elif action == "submit":
                    response_body = submit_post(pk)
                    return self.response(response_body, status.HTTP_200_SUCCESS.value)

                else:
                    return self.response(
                        json.dumps({"error": f"Unknown action: {action}"}),
                        status.HTTP_400_CLIENT_ERROR_BAD_REQUEST_DATA.value,
                    )

            response_body = update_post(request_body)
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "users":
            if pk != 0:
                response_body = update_user(request_body)
                json_body = json.loads(response_body)
                if json_body.get("ok") is False:
                    return self.response(response_body, status.HTTP_409_CONFLICT.value)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "comments" and pk != 0:
            response_body = update_comment(pk, request_body)
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "categories" and pk != 0:
            response_body = update_category(pk, request_body)
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "tags" and pk != 0:
            response_body = update_tag(pk, request_body)
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "reactions" and pk != 0:
            response_body = update_reaction(request_body)
            json_body = json.loads(response_body)
            if json_body.get("ok") is False:
                return self.response(response_body, status.HTTP_409_CONFLICT.value)
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        return self.response(
            "Requested resource not found",
            status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value,
        )


def main():
    host = ""
    port = 8000
    ThreadingHTTPServer((host, port), JSONServer).serve_forever()


if __name__ == "__main__":
    main()
