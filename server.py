from flask import Flask, jsonify
import rpyc

def setup_rpc_connection():
    conn = rpyc.connect("localhost", 18860)
    app.config['rpc_conn'] = conn

app = Flask(__name__)

@app.route('/example', methods=['GET'])
def example():
    try:
        rpc_conn = app.config['rpc_conn']
        message = rpc_conn.root.hello("Alice")
        response = jsonify({"message": message})
        response.status_code = 200
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    setup_rpc_connection()
    app.run(debug=True, host='0.0.0.0', port=54789)
