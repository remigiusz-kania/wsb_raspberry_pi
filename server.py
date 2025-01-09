from flask import Flask, request, jsonify
import psycopg2
import requests
from datetime import datetime

app = Flask(__name__)

DB_CONFIG = {
    "dbname": "raspberry",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": "5432"
}

def log_to_database(timestamp, temperature_in, temperature_out):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO temperature_log (timestamp, temperature_in, temperature_out) 
               VALUES (%s, %s, %s)""",
            (timestamp, temperature_in, temperature_out)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error logging to database: {error}")


def fetch_outdoor_temperature(target_timestamp):
    try:
        latitude = 52.2297
        longitude = 21.0122
        time_str = target_timestamp.strftime("%Y-%m-%dT%H:00")
        print(time_str)
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'hourly': 'temperature_2m',
            'timezone': 'auto',
            'start_hour': time_str,
            'end_hour': time_str,
        }

        response = requests.get("https://api.open-meteo.com/v1/forecast", params=params)

        if response.status_code != 200:
            print(f"Błąd połączenia z Open Meteo API: {response.status_code}, {response.text}")
            return None

        weather_data = response.json()

        hourly_data = weather_data.get('hourly', {})
        temperatures = hourly_data.get('temperature_2m', [])

        if not temperatures:
            print("Brak danych pogodowych w odpowiedzi API.")
            return None

        return temperatures[0]

    except Exception as error:
        print(f"Wystąpił błąd podczas pobierania temperatury zewnętrznej: {error}")
        return None

@app.route('/receive_data', methods=['POST'])
def receive_data():
    try:
        data = request.json
        temperature_in = data.get('temperature')
        timestamp_str = data.get('timestamp')

        if temperature_in is None or timestamp_str is None:
            return jsonify({"error": "temperature and timestamp are required"}), 400

        timestamp = datetime.fromisoformat(timestamp_str)

        try:
            temperature_out = fetch_outdoor_temperature(timestamp)
            if temperature_out is None:
                print("Nie udało się pobrać temperatury zewnętrznej z Open Meteo API.")
        except Exception as error:
            print(f"Błąd podczas próby pobrania temperatury zewnętrznej: {error}")
            temperature_out = None

        log_to_database(timestamp, temperature_in, temperature_out)

        return jsonify({
            "timestamp": timestamp.isoformat(),
            "temperature_in": temperature_in,
            "temperature_out": temperature_out,
            "message": "Temperature logged successfully"
        }), 200
    except Exception as error:
        print(f"Error processing request: {error}")
        return jsonify({"error": f"Failed to process data {error}"}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)