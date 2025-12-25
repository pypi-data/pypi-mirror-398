# オブジェクトのハッシュ化 [obj_hash]

import sys
import json
import blake3

# オブジェクトのハッシュ化 [obj_hash]
def obj_hash_func(
	target,	# ハッシュ化対象のオブジェクト (json化可能なもの)
	length = 16,	# バイト数
):
	# json化 (ここでjson化不能な場合は自動的に例外が送出される)
	json_str = json.dumps(target, sort_keys = True, ensure_ascii = False)
	# バイト列にする
	b = json_str.encode("utf-8")
	# ハッシュ化
	h = blake3.blake3(b)
	return h.hexdigest(length = length)

# モジュールをobj_hash_func関数と同一視
sys.modules[__name__] = obj_hash_func
