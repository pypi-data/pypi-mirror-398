import urllib.request

def url(url, savepath):
    """
    
    Parameters
    ----------
    url : the source website \n
    savepath : the path to save the downloaded file, including the name of the file.
    
    """
    
    urllib.request.urlretrieve(url, savepath)

