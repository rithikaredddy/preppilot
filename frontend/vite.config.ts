import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // One copy of each CodeMirror core package: two copies of @codemirror/state
    // break the editor ("Unrecognized extension value") and blank the page.
    dedupe: [
      "react",
      "react-dom",
      "@codemirror/state",
      "@codemirror/view",
      "@codemirror/language",
      "@lezer/common",
      "@lezer/highlight",
      "@lezer/lr",
    ],
  },
  optimizeDeps: {
    // Pre-bundle every editor grammar together at start-up. Otherwise the dev
    // server bundles Java/C++ separately the first time they are picked, with
    // their own copy of the editor core.
    include: [
      "@uiw/react-codemirror",
      "@codemirror/state",
      "@codemirror/view",
      "@codemirror/language",
      "@codemirror/lang-python",
      "@codemirror/lang-java",
      "@codemirror/lang-cpp",
    ],
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
