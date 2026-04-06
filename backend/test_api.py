import requests
import json

try:
    with open('test.jpg', 'wb') as f:
        f.write(b'fake_image_data_here_or_download_dummy')
    
    # We will just see if we can trigger the internal server error with bad image or real image
    # We can also check recent exceptions in python if we log them to file.
except Exception as e:
    print(e)
