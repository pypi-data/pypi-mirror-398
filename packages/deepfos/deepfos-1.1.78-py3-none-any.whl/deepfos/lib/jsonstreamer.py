import os

from deepfos.boost import jstream


class JsonStreamer:
    def __init__(self, file, key: str):
        self.key = key.encode('utf-8')
        # 是否在引号内
        self.in_double_quotation = False
        # 是否在转义符内
        self.in_escape = False
        # 花括号个数
        self.lbrace = 0
        self.rbrace = 0
        # 匹配的键是否已开始
        self.is_started = False
        # 当前已匹配的键段
        self.matched_index = 0
        # 是否已找到完整的值
        self.finished = False

        if isinstance(file, str):
            if os.path.exists(file):
                self.file = open(file, 'rb')
                self.should_close = True
            else:
                raise ValueError('Filename or IO value expected.')
        elif isinstance(file, JsonStreamer):
            self.should_close = True
            self.file = file
        else:
            self.should_close = False
            self.file = file

    def read(self, length: int = 1024):
        result = b''
        read_size = length
        while len(result) < length:
            if self.finished:
                break
            temp = self.file.read(read_size)
            if len(temp) == 0:
                break
            result = result + jstream.read(temp, self)
            read_size = length - len(result)
        return result

    def __del__(self):
        self.close()

    def close(self):
        if getattr(self, 'should_close', False):
            self.file.close()
            self.should_close = False


class JsonStreamMultiKeyPath:
    def __init__(self, file, key_path: str):
        all_key = key_path.split('.')
        streamer = JsonStreamer(file, all_key[0])
        for key in all_key[1::]:
            streamer = JsonStreamer(streamer, key)
        self.streamer = streamer

    def __enter__(self):
        return self.streamer

    def __exit__(self, *args):
        self.streamer.close()

    def read(self, length: int = 1024):
        return self.streamer.read(length)

    def close(self):
        self.streamer.close()

    def __del__(self):
        if getattr(self, 'streamer', None):
            self.streamer.close()
