import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const DEFAULT_UPSTREAM = "https://sports-api.sportsdata365.com";

function msdataProxy(target: string, apim: string, live: string) {
  return {
    "/msdata": {
      target,
      changeOrigin: true,
      secure: true,
      configure(proxy: { on: (event: string, fn: (...args: unknown[]) => void) => void }) {
        proxy.on("proxyReq", (...args: unknown[]) => {
          const proxyReq = args[0] as { setHeader: (k: string, v: string) => void };
          if (apim) proxyReq.setHeader("x-apim-key", apim);
          if (live) proxyReq.setHeader("X-Live-Key", live);
        });
      },
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const deployed = (env.MSDATA_BASE_URL || "").replace(/\/$/, "");
  const target = deployed.replace(/\/msdata\/?$/, "") || DEFAULT_UPSTREAM;
  const apim = env.MSDATA_API_KEY || "";
  const live = env.MSDATA_LIVE_KEY || "";
  const port = Number(env.WEB_PORT || 5176);
  const proxy = msdataProxy(target, apim, live);

  return {
    plugins: [react()],
    server: {
      host: "127.0.0.1",
      port,
      proxy,
    },
    preview: {
      host: "127.0.0.1",
      port,
      proxy,
    },
  };
});
