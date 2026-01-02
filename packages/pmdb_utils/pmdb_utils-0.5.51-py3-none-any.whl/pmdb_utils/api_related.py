# pip3 install requests
import requests
import time


def retry_request(
    method="GET",
    url=None,
    status_forcelist=[],
    total=3,
    delay=10,
    **kwargs,
):
    """
    Sends an HTTP request with retry logic for specified status codes or connection errors.

    Parameters:
    method (str): The HTTP method to use (e.g., 'GET', 'POST'). Default is 'GET'.
    url (str): The URL to send the request to. Default is None.
    status_forcelist (list): A list of HTTP status codes that should trigger a retry. Default is an empty list.
    total (int): The total number of retry attempts. Default is 3.
    delay (int): The delay (in seconds) between retries. Default is 10.
    **kwargs: Additional arguments to pass to the `requests.request` method.

    Returns:
    response (requests.Response): The final response object if successful.
    last_response (requests.Response): The last response object after retries if the request fails.

    Notes:
    - If a `requests.exceptions.ConnectionError` occurs, the function will retry.
    - If the response status code is in `status_forcelist`, the function will retry after waiting for `delay` seconds.
    - After exhausting all retries, the last response object is returned.
    - Inspired by https://www.zenrows.com/blog/python-requests-retry#code-your-retry-wrapper

    Example:
        response = retry_request(
            method="GET",
            url="https://httpstat.us/406",
            total=5,
            delay=2,
            status_forcelist=[406]
        )
    """
    # Store the last response in an empty variable
    last_response = None

    # Implement retry logic
    for _ in range(total):
        try:
            response = requests.request(method, url, **kwargs)
            if response.status_code in status_forcelist:
                # Track the last response
                last_response = response
                print(
                    f" Got status code {response.status_code} for url {url} will retry in {delay} seconds retry number {_ + 1}/{total}"
                )
                time.sleep(delay)
                # Retry request
                continue
            else:
                return response

        except requests.exceptions.ConnectionError:
            pass

    # Log the response after the retry
    return last_response
