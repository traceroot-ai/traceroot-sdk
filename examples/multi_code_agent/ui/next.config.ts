import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  webpack: (config, { isServer }) => {
    if (isServer) {
      // Handle traceroot-sdk-ts server-side bundling issues
      config.externals = config.externals || [];
      config.externals.push({
        'winston-cloudwatch-logs': 'commonjs winston-cloudwatch-logs',
        '@aws-sdk/node-http-handler': 'commonjs @aws-sdk/node-http-handler',
        'http2': 'commonjs http2',
        'fs': 'commonjs fs',
        'path': 'commonjs path',
        'os': 'commonjs os',
        'coffee-script': 'commonjs coffee-script',
        'vm2': 'commonjs vm2'
      });

      // Resolve modules properly
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        os: false,
        http2: false,
        'coffee-script': false,
        vm2: false,
      };
    }

    return config;
  },
  serverExternalPackages: ['traceroot-sdk-ts'],
  eslint: {
    // 🚫 Completely skip ESLint during builds
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
