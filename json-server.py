import json
from http.server import HTTPServer
from nss_handler import HandleRequests, status

<<<<<<< jn/ft/api_view_detail_post
from views.post import (
    create_post,
    get_user_posts,
    get_post_details,
    update_post,
    get_all_posts,
)

from views.user import (
    create_user,
    login_user,
)
=======
# Add your imports below this line
from views import (
    create_user,
    login_user,
    create_post,
    get_user_posts,
    get_post_by_id,
    update_post,
    get_all_posts,
    get_user,
    list_users,
)
from views import get_unapproved_posts, approve_post
from views import get_all_categories, create_category, get_category_by_id
>>>>>>> develop


class JSONServer(HandleRequests):
    """Server class to handle incoming HTTP requests"""

    def do_GET(self):
        """Handle GET requests from a client"""
        response_body = ""
        url = self.parse_url(self.path)
        query_params = url["query_params"]

<<<<<<< jn/ft/api_view_detail_post
        if url["requested_resource"] == "user":
            return self.response(
                "{}", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value
            )

        elif url["requested_resource"] == "posts":
            # IMPORTANT: query param routes must be checked BEFORE pk==0 list route
=======
        if url["requested_resource"] == "users":
            if url["pk"] != 0:
                response_body = get_user(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
            response_body = list_users()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)
          

        elif url["requested_resource"] == "posts":
            if url["pk"] != 0:
                response_body = get_post_by_id(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
>>>>>>> develop
            if "user_id" in query_params:
                user_id = query_params["user_id"][0]
                response_body = get_user_posts(user_id)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
<<<<<<< jn/ft/api_view_detail_post

            # /posts/<id>
            if url["pk"] != 0:
                response_body = get_post_details(url["pk"])
                # optional: if empty object returned, you could send 404 here
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            # /posts
            response_body = get_all_posts()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

=======
            elif "approved" in query_params:
                approved = query_params["approved"][0].lower == "true"
                if not approved:
                    response_body = get_unapproved_posts()
                    return self.response(response_body, status.HTTP_200_SUCCESS.value)
            else:
                response_body = get_all_posts()
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
        elif url["requested_resource"] == "categories":
            if url["pk"] != 0:
                response_body = get_category_by_id(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
            response_body = get_all_categories()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)
>>>>>>> develop
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
<<<<<<< jn/ft/api_view_detail_post
                succesfully_updated = update_post(request_body)
                if succesfully_updated:
                    return self.response(
                        succesfully_updated, status.HTTP_200_SUCCESS.value
                    )
=======
                if "approved" in request_body and len(request_body) == 1:
                    response_body = approve_post(pk)
                else:
                    response_body = update_post(request_body)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
>>>>>>> develop

        return self.response(
            "Requested resource not found",
            status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value,
        )

    def do_DELETE(self):
        """Handle DELETE requests from a client"""
        url = self.parse_url(self.path)

        if url["requested_resource"] == "user":
<<<<<<< jn/ft/api_view_detail_post
            return self.response(
                "{}", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value
            )
=======
            pass
        # Example of deleting a user
        #         if pk != 0:
        #             successfully_deleted = delete_user(pk)
        #             if successfully_deleted:
        #                 return self.response(
        #                     "", status.HTTP_204_SUCCESS_NO_RESPONSE_BODY.value
        #                 )

        #             return self.response(
        #                 "Requested resource not found",
        #                 status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value,
        #             )
>>>>>>> develop

        else:
            return self.response(
                "Not found", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value
            )

    def do_POST(self):
        """Handle POST requests from a client"""
        response_body = ""
        url = self.parse_url(self.path)

        content_len = int(self.headers.get("content-length", 0))
        request_body = self.rfile.read(content_len)
        request_body = json.loads(request_body)

        if url["requested_resource"] == "register":
            response_body = create_user(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)

<<<<<<< jn/ft/api_view_detail_post
=======
        # Login a user
>>>>>>> develop
        elif url["requested_resource"] == "login":
            response_body = login_user(request_body)
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        elif url["requested_resource"] in ("new_post", "posts"):
            response_body = create_post(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)
<<<<<<< jn/ft/api_view_detail_post

=======
        elif url["requested_resource"] == "categories":
            response_body = create_category(request_body)
            return self.response(response_body, status.HTTP_201_SUCCESS_CREATED.value)
>>>>>>> develop
        else:
            return self.response(
                "", status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value
            )


#
# THE CODE BELOW THIS LINE IS NOT IMPORTANT FOR REACHING YOUR LEARNING OBJECTIVES
#
def main():
    host = ""
    port = 8000
    HTTPServer((host, port), JSONServer).serve_forever()


if __name__ == "__main__":
    main()
