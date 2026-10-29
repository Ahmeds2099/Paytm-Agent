import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    allowedDevOrigins: ['localhost:3000', '192.168.1.11:3000', '192.168.56.1:3000'],
};


export default nextConfig;
