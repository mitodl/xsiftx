"""
This handles file uploads and hashing for placing the
file on s3 using the edX platform settings
"""
import hashlib
import mimetypes
import os
import urllib

from boto.s3.connection import S3Connection
from boto.s3.key import Key


class FSStore(object):
    """
    This writes out the file to a local path
    """

    def __init__(self, settings):
        self.root_path = settings['root_path']

    def path_for(self, course_id, filename):
        """
        This returns the path to write the file to
        """
        return os.path.join(self.root_path,
                            urllib.quote(course_id, safe=''),
                            filename)

    def store(self, course_id, filename, srcfile):
        """
        Actually writes out the file from wherever srcfile has been
        seeked to.
        """
        full_path = self.path_for(course_id, filename)
        directory = os.path.dirname(full_path)
        if not os.path.exists(directory):
            os.makedirs(directory, 0o755)
        with open(full_path, "wb") as output_file:
            output_file.write(srcfile.read())


class S3Store(object):
    """
    This manages the connection and uploading of files
    generated by the sifter
    """

    def __init__(self, settings):
        self.root_path = settings['root_path']

        conn = S3Connection(
            settings['aws_key_id'],
            settings['aws_key']
        )
        self.bucket = conn.get_bucket(settings['bucket'])

    def key_for(self, course_id, filename):
        """
        Return the S3 key we would use to store and retrive the data for the
        given filename.
        """
        hashed_course_id = hashlib.sha1(course_id)

        key = Key(self.bucket)
        key.key = "{}/{}/{}".format(
            self.root_path,
            hashed_course_id.hexdigest(),
            filename
        )
        return key

    def store(self, course_id, filename, srcfile):
        """
        This actually stores the file into s3
        """

        key = self.key_for(course_id, filename)

        type_guess = mimetypes.guess_type(filename)
        data = srcfile.read()
        key.size = len(data)
        key.content_type = type_guess[0]
        key.content_encoding = type_guess[1]

        key.set_contents_from_string(data)
