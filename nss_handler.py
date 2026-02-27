from enum import Enum
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler
import io
import cgi


class status(Enum):
    HTTP_200_SUCCESS = 200
    HTTP_201_SUCCESS_CREATED = 201
    HTTP_204_SUCCESS_NO_RESPONSE_BODY = 204
    HTTP_400_CLIENT_ERROR_BAD_REQUEST_DATA = 400
    HTTP_404_CLIENT_ERROR_RESOURCE_NOT_FOUND = 404
    HTTP_409_CONFLICT = 409
    HTTP_500_SERVER_ERROR = 500


class HandleRequests(BaseHTTPRequestHandler):

    def response(self, body, code):
        self.set_response_code(code)
        self.wfile.write(body.encode())

    def parse_url(self, path):
        """Parse the url into the resource and id"""
        parsed_url = urlparse(path)
        path_params = parsed_url.path.split("/")
        resource = path_params[1]

        url_dictionary = {"requested_resource": resource, "query_params": {}, "pk": 0}

        if parsed_url.query:
            query = parse_qs(parsed_url.query)
            url_dictionary["query_params"] = query

        try:
            pk = int(path_params[2])
            url_dictionary["pk"] = pk
        except (IndexError, ValueError):
            pass

        return url_dictionary

    def set_response_code(self, status):
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        self.send_header(
            "Access-Control-Allow-Headers",
            "X-Requested-With, Content-Type, Accept, Authorization",
        )
        self.end_headers()

    def parse_multipart(self):
        """Parse multipart/form-data"""
        content_type = self.headers["content-type"]
        content_length = int(self.headers["content-length"])

        # Read body
        body = self.rfile.read(content_length)

        # Create environment for cgi.FieldStorage
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": str(content_length),
        }

        # Parse the form data
        form = cgi.FieldStorage(
            fp=io.BytesIO(body), environ=environ, keep_blank_values=True
        )

        # Extract fields into a dictionary
        parsed_data = {}
        for key in form.keys():
            field = form[key]
            if field.filename:  # It's a file
                parsed_data[key] = field.file.read()  # Binary data
            else:
                parsed_data[key] = field.value  # Text data

        return parsed_data
