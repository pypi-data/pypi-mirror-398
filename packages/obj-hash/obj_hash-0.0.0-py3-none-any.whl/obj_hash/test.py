# オブジェクトのハッシュ化 [obj_hash]
# 【動作確認 / 使用例】

import sys
import ezpip
obj_hash = ezpip.load_develop("obj_hash", "../", develop_flag = True)

h = obj_hash("hogehoge")
print(h)

print(obj_hash({"23": "hoge", "list": []}))

print(obj_hash({"23": "hoge", "list": []}, length = 100))

print(obj_hash({"23": "hoge", "list": []}) == obj_hash({"list": [], "23": "hoge"}))
