/** @type {import('next').NextConfig} */
const nextConfig = {
    // Empty turbopack config to silence the webpack warning in dev mode
    turbopack: {},
    output: 'standalone',
};

export default nextConfig;
