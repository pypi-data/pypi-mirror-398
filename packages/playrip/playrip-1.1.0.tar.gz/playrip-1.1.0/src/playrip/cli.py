from Dowload import Youtube
from Dowload import Spotify
import sys

def main():
    url = sys.argv[1]
    print("abaixando")
    if("youtu" in url):
        print("toutube")
        if(len(sys.argv) > 2):
            tipo = sys.argv[2]
            Youtube(url=url, tipo=tipo)
    if("spotify" in url):
        print("spotify")
        Spotify(url=url)
