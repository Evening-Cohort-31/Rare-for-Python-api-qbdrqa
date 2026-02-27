import json
from http.server import ThreadingHTTPServer
from nss_handler import HandleRequests, status
import imghdr


from views.comment import create_comment, get_comments_by_post_id
from views.post import (
    create_post,
    get_user_posts,
    update_post,
    get_all_posts,
    get_post_by_id,
    get_posts_by_tag_id,
    get_unapproved_posts,
    approve_post,
    search_posts_by_title,
    delete_post,
    get_subscribed_posts,
    get_post_header_image,
)

from views.user import (
    create_user,
    login_user,
    update_user,
    get_user,
    list_users,
    add_subscription,
    delete_subscription,
    get_user_profile_image,
)
from views.category import get_all_categories, create_category, get_category_by_id
from views.tag import get_tags, get_tag_by_id, create_tag


class JSONServer(HandleRequests):
    """Server class to handle incoming HTTP requests"""

    def do_GET(self):
        """Handle GET requests from a client"""
        url = self.parse_url(self.path)
        query_params = url["query_params"]

        if url["requested_resource"] == "user":
            return self.response(
                "{}", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value
            )

        if url["requested_resource"] == "users":
            if url["pk"] != 0:
                response_body = get_user(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
            if "image" in query_params:
                user_id = query_params["image"][0]
                image_data = get_user_profile_image(user_id)
                if image_data:
                    try:
                        # Detect actual image type
                        image_type = imghdr.what(None, h=image_data)
                        content_type = (
                            f"image/{image_type}" if image_type else "image/jpeg"
                        )

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
            if url["pk"] != 0:
                if (
                    "subscriptions" in query_params
                    and query_params["subscriptions"][0].lower() == "true"
                ):
                    response_body = get_subscribed_posts(url["pk"])
                    return self.response(response_body, status.HTTP_200_SUCCESS.value)
                response_body = get_post_by_id(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            if "user_id" in query_params:
                user_id = query_params["user_id"][0]
                response_body = get_user_posts(user_id)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            if "approved" in query_params:
                approved = query_params["approved"][0].lower() == "true"
                if not approved:
                    response_body = get_unapproved_posts()
                    return self.response(response_body, status.HTTP_200_SUCCESS.value)

            if "tag_id" in query_params:
                tag_id = query_params["tag_id"][0]
                response_body = get_posts_by_tag_id(tag_id)
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
                        # Detect actual image type
                        image_type = imghdr.what(None, h=image_data)
                        content_type = (
                            f"image/{image_type}" if image_type else "image/jpeg"
                        )

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
            if url["pk"] != 0:
                response_body = get_tag_by_id(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
            response_body = get_tags()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "categories":
            if url["pk"] != 0:
                response_body = get_category_by_id(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
            response_body = get_all_categories()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "comments":
            if "post_id" in query_params:
                post_id = query_params["post_id"][0]
                response_body = get_comments_by_post_id(post_id)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
            return self.response("[]", status.HTTP_200_SUCCESS.value)

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
            if "approved" in request_body and len(request_body) == 1:
                response_body = approve_post(pk)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            successfully_updated = update_post(request_body)
            return self.response(successfully_updated, status.HTTP_200_SUCCESS.value)

        if url["requested_resource"] == "users":
            if pk != 0:
                response_body = update_user(request_body)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

        return self.response(
            "Requested resource not found",
            status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value,
        )

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

        return self.response("", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value)


def main():
    host = ""
    port = 8000
    ThreadingHTTPServer((host, port), JSONServer).serve_forever()


if __name__ == "__main__":
    main()
