from playrip import Dowload
import sys

def main():
    url = sys.argv[1]
    print("abaixando")
    if("youtu" in url):
        print("------Abaixando video do Youtube------")
        if(len(sys.argv) > 2):
            tipo = sys.argv[2]
            Dowload.Youtube(url=url, tipo=tipo)
    if("spotify" in url):
        print("------Abaixando musica do spotify------")
        Dowload.Spotify(url=url)
