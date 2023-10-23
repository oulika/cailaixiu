import time
import requests
import hashlib
timestamp = str(time.time())[:10]
ori_str = timestamp + 'a9964a84-680a-11ee-915f-202b20a7956c'
signature = hashlib.md5(ori_str.encode(encoding='utf-8')).hexdigest()


headers = dict(signature=signature, timestamp=timestamp, appname='client', username='root')

# get
get_data = dict(per_page=20, category='all')
r = requests.get('http://127.0.0.1:6060/api/v1.0/workflows/1/init_state', headers=headers, params=get_data)
result = r.json()
print(result)

# # post
# data = dict(workflow_id=1, suggestion='请协助提供更多信息', transition_id=1)
# r = requests.post('http://127.0.0.1:6060/api/v1.0/tickets', headers=headers, json=data)
# result = r.json()