# enebular-sdk

[enebular](https://www.enebular.com/ja/)のクラウド実行環境上で動作するアプリケーションを開発するためのSDKです。
本SDKを利用することにより、enebularのデータストアを利用するアプリケーションを開発できます。

## 対応環境

* 実行環境: enebularのクラウド実行環境
* ランタイム: Python 3.13

## インストール

```bash
pip install enebular-sdk
```

## クイックスタート

```python
from enebular_sdk import CloudDataStoreClient
import time
import json

datastore = CloudDataStoreClient()

def handler(event, context):
    # データの保存
    datastore.put_item({
        'table_id': 'sensor-data',
        'item': {
            'deviceId': 'device-001',
            'timestamp': int(time.time() * 1000),
            'temperature': 25.5
        }
    })

    result = datastore.query({
        'table_id': 'sensor-data',
        'expression': '#deviceId = :deviceId',
        'values': {'deviceId': 'device-001'},
        'order': False,  # False = descending
        'limit': 10
    })

    return {
        'statusCode': 200,
        'body': json.dumps(result.get('params', {}).get('Items'))
    }
```

## 機能

### データストア

enebularのデータストアのテーブルに対してデータの読み書き削除等の操作を行います。
主な操作の種類は以下の通りです。

- **CloudDataStoreClient** - データストア操作のインスタンス作成
- **get_item** - データの取得
- **put_item** - データの保存
- **delete_item** - データの削除
- **query** - データのクエリ

あらかじめenebularで、操作対象のテーブルを作成しておく必要があります。

以下に使い方を示します。

#### データストア操作のインスタンス作成

```python
from enebular_sdk import CloudDataStoreClient

datastore = CloudDataStoreClient()
```
以降の使用例ではこのdatastoreインスタンスを利用して、データストアの操作を行います。

#### データの取得

```python
result = datastore.get_item({
    'table_id': 'sensor-data',
    'key': {'deviceId': 'device-001', 'timestamp': 1234567890}
})

if result['result'] == 'success':
    print(result.get('params', {}).get('Item'))
```

`get_item`の戻り値の形式:
```python
{
    "result": "success" | "fail",  # 成功(success)/失敗(fail)を表します
    "error": str,                  # 失敗の場合、エラーメッセージを保持します
    "params": {"Item": any}        # 成功した場合、Itemに取得したデータを保持します
}
```

#### データの保存

```python
datastore.put_item({
    'table_id': 'sensor-data',
    'item': {
        'deviceId': 'device-001',
        'timestamp': int(time.time() * 1000),
        'temperature': 25.5,
        'humidity': 60
    }
})
```

`put_item`の戻り値の形式:
```python
{
    "result": "success" | "fail",  # 成功(success)/失敗(fail)を表します
    "params": {"Item": any},       # 成功した場合、Itemに登録したデータを保持します
    "error": str                   # 失敗の場合、エラーメッセージを保持します
}
```

#### データの削除

```python
datastore.delete_item({
    'table_id': 'sensor-data',
    'key': {'deviceId': 'device-001', 'timestamp': 1234567890}
})
```

`delete_item`の戻り値の形式:
```python
{
    "result": "success" | "fail",  # 成功(success)/失敗(fail)を表します
    "error": str,                  # 失敗の場合、エラーメッセージを保持します
    "params": {"Item": any}        # 成功した場合、Itemに削除したデータを保持します
}
```

#### データの検索

```python
import time

result = datastore.query({
    'table_id': 'sensor-data',
    'expression': '#deviceId = :deviceId and #timestamp > :timestamp',
    'values': {
        'deviceId': 'device-001',
        'timestamp': int(time.time() * 1000) - 86400000  # 過去24時間
    },
    'order': True,  # True=昇順, False=降順
    'limit': 100  # limitを設定しない場合は10とする
})
```

`query`の戻り値の形式:
```python
{
    "result": "success" | "fail",  # 成功(success)/失敗(fail)を表します
    "error": str,                  # 失敗の場合、エラーメッセージを保持します
    "params": {
        "Items": [any],            # 成功した場合、Itemに取得したデータを保持します
        "LastEvaluatedKey": str,   # 今回取得したデータの続きのデータを取得するキーを保持します*1
        "Count": int               # 取得したデータ数を保持します
    }
}
```
*1: `LastEvaluatedKey`の値を`query`実行時のパラメーターに`start_key`として追加することで続きを取得できます

### ロガー

ログを出力します。
出力したログは、enebularのクラウド実行環境画面で閲覧できます。

以下に使い方を示します。

```python
from enebular_sdk import Logger

logger = Logger("MyContext")

logger.error("エラーメッセージ", error)
logger.warn("警告メッセージ", data)
logger.info("情報メッセージ", data)
logger.debug("デバッグメッセージ", data)
```

ログの出力例:
```
[Dec 19th 2025, 13:00:50]:  2025-12-19T04:00:50.491Z	adfff29c-658d-4c44-9530-9a33298950b6	ERROR	2025-12-19T04:00:50.491Z [enebular-sdk] [ERROR] [MyContext] エラーメッセージ
```

出力対象のログは環境変数 `LOG_LEVEL` で設定できます。
* **ERROR**: error関数のログのみ出力します
* **WARN**: error、warn関数のログを出力します
* **INFO**: error、warn、info関数のログを出力します
* **DEBUG**: error、warn、info、debug関数のログを出力します
* **TRACE**: error、warn、info、debug、trace関数のログを出力します

環境変数は、enebularのクラウド実行環境画面で設定できます。

## 型ヒントサポート

このSDKは型ヒントを提供しています。IDEでの自動補完やタイプチェックが利用できます。

## enebularへのデプロイ

作成したプログラムをenebularのクラウド実行環境にデプロイして実行します。
デプロイする方法については、[enebularのチュートリアル](https://docs.enebular.com/ja/getstarted/ZIPFileDeployment)をご参照ください。

## ライセンス

MIT
