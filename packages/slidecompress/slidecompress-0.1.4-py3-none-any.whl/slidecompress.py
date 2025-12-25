import argparse
import os
import re
import tempfile
from collections import Counter, defaultdict
from subprocess import run, CalledProcessError
from zipfile import ZipFile, ZIP_DEFLATED


_re_unsafe = re.compile(r"[^A-Za-z0-9_]+")
slug = lambda s: "-".join(word for word in _re_unsafe.split(s.lower()) if word)
default_title = "PowerPoint Presentation"
_png_cmd = 'magick "%s" -resize "1000x1000^>" -colors 255 -type optimize "%s"'
_jpg_cmd = 'magick "%s" -resize "1000x1000^>" -quality 75 "%s"'


def basename(path):
    filename = os.path.split(path)[-1]
    return os.path.splitext(filename)[0]


def compress_media(path):
    size = os.stat(path).st_size
    cmdpath = path.replace(os.path.sep, "/")  # For Cygwin
    ext = os.path.splitext(os.path.basename(cmdpath))[1]
    fmt = ext[1:].lower()

    if fmt in {"png"}:
        cmd, ext = _png_cmd, ".png"
    elif fmt in {"jpg", "jpeg", "jpg-large"}:
        cmd, ext = _jpg_cmd, ext
    elif fmt in {"tif", "tiff", "emf"}:
        cmd, ext = _png_cmd, ".png"
    else:
        return ext, size, size

    with tempfile.NamedTemporaryFile(suffix=ext) as handle:
        temp = handle.name
        run(cmd % (cmdpath, temp), shell=True, check=True)
        # If the image has been compressed by at least 100 bytes, use it instead
        new_size = os.stat(temp).st_size
        if new_size < size - 100:
            with open(path, "wb") as f2:
                f2.write(handle.read())
            return ext, size, new_size
        return ext, size, size


def compress(source, width=1024, force=False):
    # Compress compresses all images in a PPT
    source = os.path.abspath(source)
    output = basename(source) + ".compressed.pptx" if not force else source

    with tempfile.TemporaryDirectory() as tmpdir:
        with ZipFile(source) as archive:
            archive.extractall(tmpdir)

        # Compress images
        ppt_dir = os.path.join(tmpdir, "ppt")
        media_dir = os.path.join(ppt_dir, "media")
        sizes, slides = Counter(), defaultdict(list)
        for root, dirs, files in os.walk(media_dir):
            for filename in files:
                path = os.path.join(root, filename)
                ppt_path = "../" + os.path.relpath(path, ppt_dir).replace("\\", "/")
                current_ext = os.path.splitext(filename)[1]
                try:
                    ext, size, new_size = compress_media(path)
                except Exception as exc:
                    msg = "{:>16s}: {:>8,.1f}KB -> ERROR: {}"
                    params = (filename, size / 1000.0, str(exc))
                else:
                    sizes[ppt_path] = new_size
                    size, new_size = size / 1000.0, new_size / 1000.0
                    # Print the extent of compression (if any)
                    if new_size < size:
                        change = f" ({ext})" if ext != current_ext else ""
                        msg = "{:>16s}: {:>8,.1f}KB -> {:>8,.1f}KB{}"
                        params = (filename, size, size - new_size, change)
                    else:
                        msg = "{:>16s}: {:>8,.1f}KB"
                        params = (filename, size)
                print(msg.format(*params))
        # # If image file names changed, replace names in the XML files
        for root, dirs, files in os.walk(tmpdir):
            for filename in files:
                if not filename.lower().endswith(".xml.rels"):
                    continue
                path = os.path.join(root, filename)
                with open(path, encoding="utf-8") as handle:
                    new_contents = contents = handle.read()
                for img_path in sizes:
                    if img_path in new_contents:
                        slides[img_path].append(
                            filename.replace(".xml.rels", "").replace("slide", "")
                        )
                if new_contents != contents:
                    with open(path, "w", encoding="utf-8") as fp:
                        fp.write(new_contents)
        # Print the largest files and where the are present
        print("Largest media after compression:")
        for img_path, size in sizes.most_common(10):
            usage = ", ".join(slides[img_path])
            filename = os.path.basename(img_path)
            print("{:>16s}: {:>8,.1f}KB in slide {}".format(filename, size / 1000.0, usage))
        # Recompress the files
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            for root, dirnames, files in os.walk(tmpdir):
                for filename in files:
                    path = os.path.join(root, filename)
                    archive.write(path, os.path.relpath(path, tmpdir))


def main():
    parser = argparse.ArgumentParser(description="Compress PowerPoint presentations")
    parser.add_argument("--width", type=int, default=1024, help="Width of image output")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite original file")
    parser.add_argument("source", help="PPTX file to compress")

    args = parser.parse_args()
    compress(args.source, width=args.width, force=args.force)


if __name__ == "__main__":
    main()
