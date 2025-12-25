
HTML_403 = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Erreur 403</title>
  </head>
  <body>
    <h1>403 Accès restreint</h1>

    <p style='color: rgb(20, 100, 120);'><b>Désolé ! Ce contenu est en accès restreint...</b></p>

    <p><strong>Si vous souhaitez faire parti des V.I.P... envoyez votre demande à Brigitte Bigi : 
    <code> contact@sppas.org </code> 
    </p>
  </body>
</html>
"""

HTML_404 = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Erreur 404</title>
  </head>
  <body>
    <h1>404 Non trouvé</h1>

    <p style='color: rgb(20, 100, 120);'><b>Désolé, on l'a bien cherché, mais on ne l'a pas trouvé !</b></p>

    <blockquote style='color: rgb(200, 20, 20); border: 1px solid gray; padding: 10px;'>
        Le contenu que vous cherchez s'est volatilisé ou n'a jamais existé...
    </blockquote>

    <p><strong>Si vous rencontrez des difficultés à accéder à un fichier, contactez </strong>
    Brigitte Bigi : <code> contact@sppas.org </code> 
    </p>
  </body>
</html>
"""

# ----------------------------------------------------------------------------


class WhakerkitErrorMiddleware:
    """WSGI Middleware to intercept HTTP error responses.

    This middleware checks the status code of the response. If it matches a
    known error (403, 404), it returns a custom HTML response instead
    of the default one.

    """

    def __init__(self, app):
        """Initialize the middleware with the WSGI application.

        :param app: The WSGI application to wrap.

        """
        self.app = app

    def __call__(self, environ, start_response):
        """Intercept the response and modify it if a known error occurs.

        :param environ: The WSGI environment dictionary containing request data.
        :param start_response: The function to start the HTTP response.
        :return: (list of bytes) The modified response body if an error occurs,
        otherwise the original response.

        """
        response_body = None  # Placeholder for the custom error response

        def custom_start_response(status, headers, exc_info=None):
            """Custom start_response function to capture and modify error responses.

            :param status: The HTTP status string (e.g., "404 Not Found").
            :param headers: The list of HTTP headers.
            :param exc_info: Optional exception info.
            :return: The modified status code and headers.

            """
            nonlocal response_body  # Allow modification of the response_body variable
            status_code = int(status.split()[0])  # Extract the HTTP status code

            if status_code == 403:
                response_body = [line.encode("utf-8") for line in HTML_403]
            elif status_code == 404:
                response_body = [line.encode("utf-8") for line in HTML_404]

            return start_response(status, headers, exc_info)

        response = self.app(environ, custom_start_response)

        # Return the custom error response if an error occurred
        if response_body is not None:
            return response_body

        # Otherwise, return the original response
        return response
