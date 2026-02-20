import json
from http.server import HTTPServer
from nss_handler import HandleRequests, status

from views.comment import create_comment, get_comments_by_post_id
from views.post import (
    create_post,
    get_user_posts,
    get_post_details,
    update_post,
    get_all_posts,
)
from views.user import create_user, login_user


class JSONServer(HandleRequests):
    """Server class to handle incoming HTTP requests"""

    def do_GET(self):
        """Handle GET requests from a client"""
        response_body = ""
        url = self.parse_url(self.path)
        query_params = url["query_params"]

        if url["requested_resource"] == "user":
            return self.response(
                "{}", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value
            )

        elif url["requested_resource"] == "posts":
            # /posts?user_id=#
            if "user_id" in query_params:
                user_id = query_params["user_id"][0]
                response_body = get_user_posts(user_id)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            # /posts/<id>
            if url["pk"] != 0:
                response_body = get_post_details(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            # /posts
            response_body = get_all_posts()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        elif url["requested_resource"] == "comments":
            # /comments?post_id=#
            if "post_id" in query_params:
                post_id = query_params["post_id"][0]
                response_body = get_comments_by_post_id(post_id)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            # If no post_id is provided, return empty list
            return self.response("[]", status.HTTP_200_SUCCESS.value)

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

        if url["requested_resource"] == "posts":
            if pk != 0:
                succesfully_updated = update_post(request_body)
                if succesfully_updated:
                    return self.response(
                        succesfully_updated, status.HTTP_200_SUCCESS.value
                    )

        return self.response(
            "Requested resource not found",
            status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value,
        )

    def do_DELETE(self):
        """Handle DELETE requests from a client"""
        url = self.parse_url(self.path)

        if url["requested_resource"] == "user":
            return self.response(
                "{}", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value
            )

        return self.response(
            "Not found", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value
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

        elif url["requested_resource"] == "comments":
            response_body = create_comment(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)

        elif url["requested_resource"] in ("new_post", "posts"):
            response_body = create_post(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)

        return self.response("", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value)


def main():
    host = ""
    port = 8000
    HTTPServer((host, port), JSONServer).serve_forever()


if __name__ == "__main__":
    main()
