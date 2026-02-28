import json
from http.server import HTTPServer
from nss_handler import HandleRequests, status

from views.user import (
    create_user,
    login_user,
    get_user,
    list_users,
)

from views.post import (
    create_post,
    get_all_posts,
    get_user_posts,
    get_post_by_id,
    get_post_details,
    update_post,
    get_unapproved_posts,
    approve_post,
)

from views.comment import (
    create_comment,
    get_comments_by_post_id,
    get_comment_by_id,
    update_comment,
    delete_comment,
)

from views.category import (
    get_all_categories,
    get_category_by_id,
    create_category,
)

from views.tag import (
    get_tags,
    get_tag_by_id,
    create_tag,
)


class JSONServer(HandleRequests):
    """Server class to handle incoming HTTP requests"""

    def do_GET(self):
        """Handle GET requests from a client"""
        url = self.parse_url(self.path)
        query_params = url["query_params"]
        response_body = ""

        if url["requested_resource"] == "user":
            return self.response(
                "{}", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value
            )

        elif url["requested_resource"] == "users":
            # /users or /users/<id>
            if url["pk"] != 0:
                response_body = get_user(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            response_body = list_users()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        elif url["requested_resource"] == "posts":
            # /posts/<id>
            if url["pk"] != 0:
                response_body = get_post_by_id(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            # /posts?user_id=#
            if "user_id" in query_params:
                user_id = query_params["user_id"][0]
                response_body = get_user_posts(user_id)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            # /posts?approved=false  (admin unapproved list)
            if "approved" in query_params:
                approved_value = query_params["approved"][0].lower()
                if approved_value == "false":
                    response_body = get_unapproved_posts()
                    return self.response(response_body, status.HTTP_200_SUCCESS.value)

            # /posts  (approved + published feed)
            response_body = get_all_posts()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        elif url["requested_resource"] == "comments":
            # /comments/<id>
            if url["pk"] != 0:
                response_body = get_comment_by_id(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            # /comments?post_id=#
            if "post_id" in query_params:
                post_id = query_params["post_id"][0]
                response_body = get_comments_by_post_id(post_id)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            # If no post_id provided, return empty list
            return self.response("[]", status.HTTP_200_SUCCESS.value)

        elif url["requested_resource"] == "tags":
            # /tags or /tags/<id>
            if url["pk"] != 0:
                response_body = get_tag_by_id(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            response_body = get_tags()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        elif url["requested_resource"] == "categories":
            # /categories or /categories/<id>
            if url["pk"] != 0:
                response_body = get_category_by_id(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            response_body = get_all_categories()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        else:
            return self.response(
                "", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value
            )

    def do_POST(self):
        """Handle POST requests from a client"""
        url = self.parse_url(self.path)

        content_len = int(self.headers.get("content-length", 0))
        request_body = self.rfile.read(content_len)
        request_body = json.loads(request_body)

        if url["requested_resource"] == "register":
            response_body = create_user(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)

        elif url["requested_resource"] == "login":
            response_body = login_user(request_body)
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        elif url["requested_resource"] in ("post", "posts"):
            response_body = create_post(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)

        elif url["requested_resource"] == "comments":
            response_body = create_comment(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)

        elif url["requested_resource"] == "categories":
            response_body = create_category(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)

        elif url["requested_resource"] == "tags":
            response_body = create_tag(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)

        else:
            return self.response(
                "", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value
            )

    def do_PUT(self):
        """Handle PUT requests from a client"""
        url = self.parse_url(self.path)
        pk = url["pk"]

        content_len = int(self.headers.get("content-length", 0))
        request_body = self.rfile.read(content_len)
        request_body = json.loads(request_body)

        if url["requested_resource"] == "posts" and pk != 0:
            # special admin approve route: PUT /posts/<id> with body {"approved": true}
            if "approved" in request_body and len(request_body) == 1:
                response_body = approve_post(pk)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            response_body = update_post(request_body)
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "comments" and pk != 0:
            response_body = update_comment(pk, request_body)
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        return self.response(
            "Requested resource not found",
            status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value,
        )

    def do_DELETE(self):
        """Handle DELETE requests from a client"""
        url = self.parse_url(self.path)
        pk = url["pk"]

        if url["requested_resource"] == "comments" and pk != 0:
            successfully_deleted = delete_comment(pk)
            if successfully_deleted:
                return self.response("", status.HTTP_204_SUCCESS_NO_RESPONSE_BODY.value)

            return self.response(
                "Requested resource not found",
                status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value,
            )

        return self.response(
            "Not found",
            status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value,
        )


def main():
    host = ""
    port = 8000
    HTTPServer((host, port), JSONServer).serve_forever()


if __name__ == "__main__":
    main()
