import React, { useEffect, useState } from "react";

const HomePage: React.FC = () => {
  const [deviceId, setDeviceId] = useState("living_room_light");
  const [status, setStatus] = useState<string>("");

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(
          `http://<raspberry-pi-ip>:5000/device/status?device_id=${deviceId}`
        );
        if (res.ok) {
          const data = await res.json();
          setStatus(data.status);
        }
      } catch (err) {
        console.error("Error fetching device status:", err);
      }
    };
    fetchStatus();
  }, [deviceId]);

  const handleOn = async () => {
    try {
      await fetch(`http://<raspberry-pi-ip>:5000/device/on`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: deviceId }),
      });
      setStatus("on");
    } catch (err) {
      console.error("Error turning device on:", err);
    }
  };

  const handleOff = async () => {
    try {
      await fetch(`http://<raspberry-pi-ip>:5000/device/off`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: deviceId }),
      });
      setStatus("off");
    } catch (err) {
      console.error("Error turning device off:", err);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>Smart Home Automation</h1>
      <label>
        Device ID:
        <input
          type="text"
          value={deviceId}
          onChange={(e) => setDeviceId(e.target.value)}
          style={{ marginLeft: 10 }}
        />
      </label>
      <div style={{ marginTop: 10 }}>
        <button onClick={handleOn} style={{ marginRight: 10 }}>
          Turn On
        </button>
        <button onClick={handleOff}>Turn Off</button>
      </div>
      <p style={{ marginTop: 10 }}>
        Current status for <strong>{deviceId}</strong>:{" "}
        <strong>{status}</strong>
      </p>
    </div>
  );
};

export default HomePage;
