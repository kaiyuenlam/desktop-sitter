from PIL import Image
import time

def showimage(emotion):
    if emotion == 'neutral':
        imagefile = Image.open(r"C:\Users\lewis\Documents\GitHub\desktop-sitter\core\Idle.jpg")
    elif emotion == 'happy' or emotion == 'surprise' or emotion == 'fear':
        imagefile = Image.open('Happy.jpg')
    elif emotion == 'angry' or emotion == 'sad' or emotion == 'disgust':
        imagefile = Image.open('Sad.jpg')
    elif emotion == 'sleepy':
        imagefile = Image.open('Sleep.jpg')
    imagefile.show()
    time.sleep(1)
    imagefile.close()

showimage(input())
showimage(input())
showimage(input())