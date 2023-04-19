from flask import Flask, jsonify
import subprocess
import rpyc
import sys
import os
import time

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
    try:
        child_process = subprocess.Popen(['python', 'rover.py'])
        time.sleep(5)
        setup_rpc_connection()

        app.run(debug=False, host='0.0.0.0', port=54789)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

    finally:
        child_process.terminate()
        child_process.wait()
