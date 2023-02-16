from flask import Flask, request
from flask_cors import cross_origin
from web import search_web

app = Flask(__name__)

@app.route('/web')
@cross_origin()
def find():
    keyword = request.args.get('keyword')
    region = request.args.get('region')
    time = request.args.get('time')
    group = request.args.get('group')
    return search_web(query=(keyword or None), region=(region or None), time=(time or None), group=(int(group or 1)))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port=8080)