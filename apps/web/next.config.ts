import type { NextConfig } from 'next';
const config: NextConfig = {
  output: 'export', trailingSlash: true, poweredByHeader: false,
  generateBuildId: async () => 'civicproof-local-v1',
  images: { unoptimized: true },
};
export default config;
