import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    allowedDevOrigins: ['localhost:3100', '192.168.1.11:3100', '192.168.56.1:3100'],
};


export default nextConfig;
