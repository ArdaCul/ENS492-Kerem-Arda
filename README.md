# ENS492-Kerem-Arda

# Smart Home Automation Project

## 📌 Project Overview

This project is a **smart home automation system** that allows users to manage and control various home devices over **local Wi-Fi** using **ESP32 microcontrollers**. The system is designed to be easy to configure and does not require writing custom firmware, thanks to **ESPHome**. The backend runs on a **Raspberry Pi** and communicates with the ESP32 devices using a **Flask API**.

## ⚙️ Features

- **Remote Device Control:** Manage and control home appliances using ESP32 devices.
- **ESPHome Integration:** No need to write firmware; ESPHome handles communication with ESP32.
- **Local Network Communication:** Devices communicate over the local Wi-Fi network.
- **Web API:** A Flask-based backend that provides APIs for controlling devices.
- **Scalability:** Supports multiple ESP32 devices for different home automation needs.

---

## 🏗️ Project Architecture

### **1. ESP32 with ESPHome**

- ESP32 devices are flashed with **ESPHome** firmware.
- Connects to the local Wi-Fi network and communicates with the Flask backend.
- Can control relays, sensors, and other smart home components.

### **2. Raspberry Pi as Backend Server**

- Runs **Flask** to provide a REST API for interacting with ESPHome devices.
- Manages device status, controls, and automation rules.

### **3. Communication Flow**

1. Flask backend receives API requests.
2. It communicates with ESPHome devices over the local network.
3. ESPHome executes commands on the ESP32 hardware.
4. Device status is updated in the backend.

---

## 🛠️ Setup & Installation

### **1. Prerequisites**

- **ESP32** (Recommended: ESP32 DevKit v1, ESP32-WROOM-32, or ESP32-WROVER)
- **Raspberry Pi** (Recommended: Raspberry Pi 4 or higher)
- **MicroSD card** (for Raspberry Pi OS)
- **Wi-Fi Router** (for local network communication)
- **ESPHome** installed on your computer
- **Python 3.9+** for the Flask backend

### **2. Flashing ESPHome on ESP32**

1. Install ESPHome:
   ```sh
   pip install esphome
   ```
2. Create a configuration file for ESP32:
   ```sh
   esphome wizard my_device.yaml
   ```
3. Modify `my_device.yaml` with Wi-Fi credentials:
   ```yaml
   wifi:
     ssid: "Your_WiFi_Name"
     password: "Your_WiFi_Password"
   ```
4. Flash ESPHome onto ESP32:
   ```sh
   esphome run my_device.yaml
   ```
5. Once flashed, ESP32 will connect to the local network and register itself with ESPHome.

### **3. Setting Up the Flask Backend on Raspberry Pi**

1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/smart-home.git
   cd smart-home
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the Flask server:
   ```sh
   python app.py
   ```
4. API will be available at: `http://<raspberry-pi-ip>:5000`

---

## 🔌 API Endpoints

### **Device Control**

- **Turn On Device:**
  ```http
  POST /device/on
  ```
  **Request Body:**
  ```json
  {
    "device_id": "living_room_light"
  }
  ```
- **Turn Off Device:**
  ```http
  POST /device/off
  ```
  **Request Body:**
  ```json
  {
    "device_id": "living_room_light"
  }
  ```
- **Get Device Status:**
  ```http
  GET /device/status?device_id=living_room_light
  ```

---

## 🛠️ Future Enhancements

- Add **MQTT support** for better real-time communication.
- Implement **WebSockets** to provide live updates to the frontend.
- Expand device types and add **voice assistant integration**.

---

## 👨‍💻 Contributors

- **Your Name** – [GitHub](https://github.com/your-profile)
- **Other Team Members**

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

---

## 📢 Support

For any issues or feature requests, open an issue in the GitHub repository or contact the project maintainers.
