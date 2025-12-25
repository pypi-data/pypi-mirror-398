from flask import Flask
from flask import jsonify
app=Flask(__name__)
# 解决接口返回内容是中文时，乱码的问题
app.config['JSON_AS_ASCII'] = False
# 请求地址映射
@app.route('/index', methods=['GET'])
def test_get():
    # 定义响应结果
    result = {}
    result['code'] = 200
    result['message'] = '请求成功'
    return jsonify(result)
@app.route('/index', methods=['POST'])
def test_post():
    # 定义响应结果
    result = {}
    result['code'] = 200
    result['message'] = '请求成功'
    return jsonify(result)
if __name__ == '__main__':
    app.run(debug=True, port=8899)