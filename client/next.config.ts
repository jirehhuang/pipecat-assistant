import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    allowedDevOrigins: [process.env.ALLOWED_DEV_ORIGIN || ""]
};

export default nextConfig;
