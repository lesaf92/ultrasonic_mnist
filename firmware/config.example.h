// Copy to config.h (gitignored, so your WiFi password stays out of git) and fill in. Reflash after editing.

// WiFi network the ESP32 joins; 2.4 GHz only
#define WIFI_SSID     "your-network"
#define WIFI_PASSWORD "your-password"

// The computer running server.py: its address on that network (`ip route get 1.1.1.1` shows it after "src"),
// and [esp32] udp_port in config.toml
#define SERVER_IP     "192.168.1.10"
#define SERVER_PORT   8001

// HC-SR04 pins, named after what each sensor measures (docs/apparatus.jpeg):
// X is the sensor on the Y axis, facing along x (the drawing's "Y-Axis Sensor");
// Y is the sensor on the X axis, facing along y (the drawing's "X-Axis Sensor").
// The HC-SR04 needs 5 V and its ECHO output is 5 V, too much for an ESP32-S3 pin: put a divider between each ECHO
// and its pin (1 kΩ from ECHO to the pin, 2 kΩ from the pin to GND). TRIG works from 3.3 V.
// Avoid strapping pins (0, 3, 45, 46), USB (19, 20) and flash/PSRAM pins (26-37).
#define TRIG_X 4
#define ECHO_X 5
#define TRIG_Y 6
#define ECHO_Y 7

#define MAX_MM 600       // echoes from farther count as none (-1); a shorter wait gives more points per second
#define PING_GAP_MS 25   // pause after each ping: the beams cross, so one sensor's echo can reach the other
