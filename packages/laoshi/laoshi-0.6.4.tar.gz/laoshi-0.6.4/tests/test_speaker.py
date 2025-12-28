import unittest
import tempfile
import uuid
import os
import shutil
from laoshi.speaker import Speaker


class SpeakerTest(unittest.TestCase):
    def setUp(self):
        self.tempfolder = tempfile.mkdtemp()
        self.name = f"{str(uuid.uuid4())}.mp3"
        self.path = f"{self.tempfolder}/{self.name}"

    def tearDown(self):
        if os.path.exists(self.tempfolder):
            shutil.rmtree(self.tempfolder)

    def test_to_speech(self):
        Speaker.text_to_speech("阿弥陀佛").save(self.name, self.path)
