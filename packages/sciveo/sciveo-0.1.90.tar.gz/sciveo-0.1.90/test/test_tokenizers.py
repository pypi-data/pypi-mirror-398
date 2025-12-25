#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2024
#

import math
import unittest

from sciveo.ml.nlp.tokenizers.bpe import *


class TestTokenizers(unittest.TestCase):
  def test_BPE(self):
    text = "節樂，《漢語大詞典》一則：「《史記．樂書》：凡作樂者，所以節槳。張守義正義：音洛，言不樂至荒淫也, 網站有中、英文版本，也有繁、簡體版，可通過每頁左上角的連結隨時調整 Ｕｎｉｃｏｄｅ! 🅤🅝🅘🅒🅞🅓🅔‽ 🇺‌🇳‌🇮‌🇨‌🇴‌🇩‌🇪! 😄 The very name strikes fear and awe into the hearts of programmers worldwide. We all know we ought to “support Unicode” in our software (whatever that means—like using wchar_t for all the strings, right?)"
    text += "Using a row in the above table to encode a code point less than 'First code point' (thus using more bytes than necessary) is termed an overlong encoding. These are a security problem because they allow the same code point to be encoded in multiple ways. Overlong encodings (of ../ for example) have been used to bypass security validations in high-profile products including Microsoft's IIS web server[14] and Apache's Tomcat servlet container.[15] Overlong encodings should therefore be considered an error and never decoded. Modified UTF-8 allows an overlong encoding of U+0000."

    T = BPETokenizer(max_size=512)
    T.train(text)

    t = "你好世界，美好的一天"
    self.assertTrue(T.decode(T.encode(t)) == t)

    t = "hello world and testing"
    self.assertTrue(T.decode(T.encode(t)) == t)


if __name__ == '__main__':
  unittest.main()