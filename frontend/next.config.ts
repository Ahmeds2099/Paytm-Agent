import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    allowedDevOrigins: ['localhost:3100', '192.168.1.11:3100', '192.168.56.1:3100', 'http://[IP_ADDRESS]', 'http://192.168.56.1:3100', 'http://127.0.0.1:8100'],
};


export default nextConfig;
