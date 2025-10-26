import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    allowedDevOrigins: [process.env.ALLOWED_DEV_ORIGIN]
        .filter((origin): origin is string => Boolean(origin))
};

export default nextConfig;
