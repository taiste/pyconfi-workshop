from zipfile import ZipFile
from itertools import chain
from time import time
from StringIO import StringIO

import Image
import sys

def convert_image(zipfile, size, source, destination):
    f = zipfile.open(source) 
    im = Image.open(StringIO(f.read()))
    im.thumbnail((size, size,), Image.ANTIALIAS)
    im.save(destination, "JPEG", quality=95, optimize=True)
    f.close()

def convert(zipfile, sizes, frame_select=None):
    def _targets(zipfile, index, name):
        output = lambda size: name.split('_0')[0] + "_scaled_%s_%05d.jpg" % (size, index,)
        return [ (zipfile, s, name, output(s),) for s in sizes ]

    def _convert_image(*args, **kwargs):
        convert_image(*args, **kwargs)
        _done()

    def _done(*args, **kwargs):
        sys.stdout.write('.')
        sys.stdout.flush()

    if not frame_select:
        frame_select = lambda x: (x % 4) == 0

    images_file = ZipFile(zipfile)
    images = [ image 
            for index, image in 
            enumerate(images_file.namelist()[1:]) 
            if frame_select(index) ] 

    converted = [
        _convert_image(*target) 
            for target in 
            chain.from_iterable([
                _targets(images_file, index, image) 
                for index, image in enumerate(images) ])
        ]

    return len(converted)

if __name__ == '__main__':
    start = time()
    num_images = convert('/Users/maharj/Downloads/HayHee_tuoli.zip', (240, 360, 480,))
    print "\nConverted %d images in %.2lf secs" % (num_images, time() - start,)
