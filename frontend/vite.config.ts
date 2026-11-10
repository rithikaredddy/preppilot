import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    dedupe: ["react", "react-dom"],
  },
  build: {
    rolldownOptions: {
      output: {
        // Heavy libraries get their own cached chunks, loaded only by the pages that use them.
        codeSplitting: {
          groups: [
            {
              name: "codemirror",
              // Core editor only; the language grammars stay in their own lazily loaded chunks.
              test: /node_modules[\\/](@codemirror[\\/](?!lang-)|@lezer[\\/](?!java|cpp|python)|@uiw|style-mod|w3c-keyname|crelt)/,
              priority: 2,
            },
            { name: "charts", test: /node_modules[\\/](recharts|d3-|victory-vendor|decimal\.js-light|internmap|lodash|react-smooth|recharts-scale|eventemitter3|tiny-invariant|clsx)/, priority: 2 },
            { name: "react", test: /node_modules[\\/](react|react-dom|react-router|scheduler|cookie|set-cookie-parser)[\\/]/, priority: 1 },
          ],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:5001",
    },
  },
})
