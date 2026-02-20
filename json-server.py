import json
from http.server import HTTPServer
from nss_handler import HandleRequests, status

from views.post import (
    create_post,
    get_user_posts,
    update_post,
    get_all_posts,
    get_post_by_id,
    get_posts_by_tag_id,
    get_unapproved_posts,
    approve_post,
    search_posts_by_title
)

from views.user import (
    create_user,
    login_user,
    get_user, 
    list_users
)

# Add your imports below this line
from views import get_all_categories, create_category, get_category_by_id
from views import get_tags, get_tag_by_id, create_tag

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

        elif url["requested_resource"] == "users":
            if url["pk"] != 0:
                response_body = get_user(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
            response_body = list_users()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)          

        elif url["requested_resource"] == "posts":
            if url["pk"] != 0:
                response_body = get_post_by_id(url["pk"])
                # optional: if empty object returned, you could send 404 here
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
                        
            if "user_id" in query_params:
                user_id = query_params["user_id"][0]
                response_body = get_user_posts(user_id)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)

            if "approved" in query_params:
                approved = query_params["approved"][0].lower == "true"
                if not approved:
                    response_body = get_unapproved_posts()
                    return self.response(response_body, status.HTTP_200_SUCCESS.value)

            if "tag_id" in query_params:
                tag_id = query_params['tag_id'][0]
                response_body = get_posts_by_tag_id(tag_id)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
            
            if "title" in query_params:
                search_term = query_params['title'][0]
                response_body = search_posts_by_title(search_term)
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
            
            response_body = get_all_posts()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)
        
        elif url["requested_resource"] == "tags":
            if url["pk"] !=0:
                response_body = get_tag_by_id(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
            response_body = get_tags()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)
        
        elif url["requested_resource"] == "categories":
            if url["pk"] != 0:
                response_body = get_category_by_id(url["pk"])
                return self.response(response_body, status.HTTP_200_SUCCESS.value)
            response_body = get_all_categories()
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

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
                if "approved" in request_body and len(request_body) == 1:
                    response_body = approve_post(pk)
                    return self.response(
                        response_body, status.HTTP_200_SUCCESS.value
                    )
                successfully_updated = update_post(request_body)
                if successfully_updated:
                    return self.response(
                        successfully_updated, status.HTTP_200_SUCCESS.value
                    )

        return self.response(
            "Requested resource not found",
            status.HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND.value,
        )

    def do_DELETE(self):
        """Handle DELETE requests from a client"""
        url = self.parse_url(self.path)

        if url["requested_resource"] == "user":
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



        # Login a user

        elif url["requested_resource"] == "login":
            response_body = login_user(request_body)
            return self.response(response_body, status.HTTP_200_SUCCESS.value)

        elif url["requested_resource"] in ("post", "posts"):
            response_body = create_post(request_body)
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


#
# THE CODE BELOW THIS LINE IS NOT IMPORTANT FOR REACHING YOUR LEARNING OBJECTIVES
#
def main():
    host = ""
    port = 8000
    HTTPServer((host, port), JSONServer).serve_forever()


if __name__ == "__main__":
    main()
