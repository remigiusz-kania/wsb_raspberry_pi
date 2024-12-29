from flask import Flask, request, jsonify
import psycopg2
app = Flask(__name__)

DB_CONFIG = {
    "dbname": "raspberry",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": "5432"
}

def log_to_database(temperature, timestamp):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO temperature_log (temperature, timestamp) VALUES (%s, %s)",
            (temperature, timestamp)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error logging to database: {error}")

@app.route('/receive_data', methods=['POST'])
def receive_data():
    try:
        data = request.json
        temperature = data.get('temperature')
        timestamp = data.get('timestamp')

        if temperature is None or timestamp is None:
            return jsonify({"error": "temperature and timestamp are required"}), 400

        log_to_database(temperature, timestamp)
        print(f"Received data: {temperature}, {timestamp}")
        return jsonify({"temperature": temperature, "timestamp": timestamp}), 200
    except Exception as error:
        print(f"Error processing request: {error}")
        return jsonify({"error": f"Failed to process data {error}"}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)