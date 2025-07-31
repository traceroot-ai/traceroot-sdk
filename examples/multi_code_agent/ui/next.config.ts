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
        'os': 'commonjs os'
      });
      
      // Resolve modules properly
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        os: false,
        http2: false,
      };
    }
    
    return config;
  },
  experimental: {
    serverComponentsExternalPackages: ['traceroot-sdk-ts']
  }
};

export default nextConfig;
