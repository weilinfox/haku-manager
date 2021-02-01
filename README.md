# haku-manager


自娱自乐式服务器状态监控

[py-hakuBot](https://github.com/weilinfox/py-hakuBot/)

## 报文格式

### heartBeat

小于15s一次，否则视为offline。

```
{'post_type': 'haku-manager', 'server_name': 'name', 'message_type': 'heartBeat'}
```

### status

```
{'post_type': 'haku-manager', 'server_name': 'name', 'message_type': 'status', 'status': {'time':{'uptime':'tm'}, 'temp':{'cpu_temp':0, 'sys_temp':0}, 'cpu':{'cpu_cores':4, 'load_average':0.0, 'wa':0}, 'disk':{'bi':0, 'bo':0}, 'memory':{'free':0, 'buff':0, 'cache':0}, 'swap':{'si':0, 'so':0}, 'process':{'r':0, 'b':0}, 'net':{'card_name':{'bytes':0, 'packets':0, 'errors':0, 'drops':0}, ...}}
```

### error

```
{'post_type': 'haku-manager', 'server_name': 'name', 'message_type': 'error', 'message': 'errMsg'}
```