import { watch } from "fs";
import path from "node:path";
import fs from "node:fs";
import { Glob } from "bun";

// User's project directory (cwd)
const projectDir = process.cwd();
const vegabaseDir = path.join(projectDir, ".vegabase");

/**
 * Scan frontend/pages and generate the page map
 */
async function generatePageMap(): Promise<string> {
  const glob = new Glob("**/*.{jsx,tsx}");
  const pagesDir = path.join(projectDir, "frontend/pages");
  const pages: string[] = [];

  for await (const file of glob.scan(pagesDir)) {
    pages.push(file);
  }

  const imports = pages
    .map((file) => {
      const name = file.replace(/\.(jsx|tsx)$/, "");
      const absPath = `${projectDir}/frontend/pages/${file}`;
      return `"${name}": () => import("${absPath}")`;
    })
    .join(",\n  ");

  return `export default {\n  ${imports}\n};`;
}

/**
 * Generate all entry files in the user's project
 */
async function generateEntryFiles() {
  // Ensure .vegabase directory exists
  if (!fs.existsSync(vegabaseDir)) {
    fs.mkdirSync(vegabaseDir, { recursive: true });
  }

  // Generate page map (scans frontend/pages)
  const pageMapCode = await generatePageMap();

  // Client entry
  const clientEntry = `
import '../frontend/styles.css';
import { createInertiaApp } from '@inertiajs/react';
import { createRoot, hydrateRoot } from 'react-dom/client';
import pageMap from './pages.js';

// Hot Reload Logic for Development
if (typeof window !== 'undefined' && window.location.hostname === "localhost") {
    const ws = new WebSocket("ws://localhost:3001/ws");
    ws.onmessage = (event) => {
        if (event.data === "reload") {
            console.log("♻️ Refreshing...");
            window.location.reload();
        }
    };
}

createInertiaApp({
    resolve: name => {
        const importPage = pageMap[name];
        if (!importPage) throw new Error(\`Page not found: \${name}\`);
        return importPage();
    },
    setup({ el, App, props }) {
        // Use createRoot for client mode, hydrateRoot for SSR/cached modes
        const mode = props.initialPage.mode;
        if (mode === "client") {
            createRoot(el).render(<App {...props} />);
        } else {
            hydrateRoot(el, <App {...props} />);
        }
    },
});
`;

  // SSR entry
  const ssrEntry = `
import { createInertiaApp } from '@inertiajs/react';
import ReactDOMServer from 'react-dom/server';
import pageMap from './pages.js';

export default function render(page) {
    return createInertiaApp({
        page,
        render: ReactDOMServer.renderToString,
        resolve: name => {
            const importPage = pageMap[name];
            if (!importPage) {
                throw new Error(\`Page not found: \${name}\`);
            }
            return importPage();
        },
        setup: ({ App, props }) => {
            return <App {...props} />;
        },
    });
}
`;

  // SSR Server entry
  const ssrServerEntry = `
import render from './ssr.jsx';

const port = Number(process.env.PORT) || 13714;

console.log(\`Starting native Bun SSR server on port \${port}...\`);

Bun.serve({
    port,
    async fetch(req) {
        const url = new URL(req.url);

        if (req.method === "GET" && url.pathname === "/health") {
            return Response.json({ status: "OK", timestamp: Date.now() });
        }

        if (req.method === "GET" && url.pathname === "/shutdown") {
            process.exit(0);
        }

        if (req.method === "POST" && url.pathname === "/render") {
            try {
                const page = await req.json();
                const result = await render(page);
                return Response.json(result);
            } catch (error) {
                console.error("SSR Error:", error);
                return Response.json({ error: error.message }, { status: 500 });
            }
        }

        return new Response("Not Found", { status: 404 });
    },
});
`;

  fs.writeFileSync(path.join(vegabaseDir, "pages.js"), pageMapCode);
  fs.writeFileSync(path.join(vegabaseDir, "client.jsx"), clientEntry.trim());
  fs.writeFileSync(path.join(vegabaseDir, "ssr.jsx"), ssrEntry.trim());
  fs.writeFileSync(path.join(vegabaseDir, "ssr-server.jsx"), ssrServerEntry.trim());

  console.log("📝 Generated files in .vegabase/");
}

// Entry points in user's project
const entryClient = path.join(vegabaseDir, "client.jsx");
const entrySSR = path.join(vegabaseDir, "ssr.jsx");
const entrySSRServer = path.join(vegabaseDir, "ssr-server.jsx");

// ==================== DEV COMMAND ====================
async function dev() {
  await generateEntryFiles();

  // Import tailwind plugin from user's project
  const { default: tailwindcss } = await import(
    path.join(projectDir, "node_modules", "bun-plugin-tailwind")
  );

  async function build() {
    // Regenerate page map on each build (picks up new pages)
    const pageMapCode = await generatePageMap();
    fs.writeFileSync(path.join(vegabaseDir, "pages.js"), pageMapCode);

    console.log("⚡ Building...");

    // Bundle Client
    await Bun.build({
      entrypoints: [entryClient],
      outdir: "./static/dist",
      naming: "client.[ext]",
      target: "browser",
      splitting: true,
      plugins: [tailwindcss],
    });

    // Bundle SSR (Library for Dev Server)
    await Bun.build({
      entrypoints: [entrySSR],
      outdir: "./backend",
      naming: { entry: "ssr_dev.js" },
      target: "bun",
      external: ["react", "react-dom", "@inertiajs/react", "@inertiajs/react/server"],
      plugins: [tailwindcss],
    });

    console.log("✅ Build complete.");
  }

  await build();

  const server = Bun.serve({
    port: 3001,
    async fetch(req, server) {
      const url = new URL(req.url);

      // SSR Render Endpoint
      if (req.method === "POST" && url.pathname === "/render") {
        try {
          const buildPath = `${projectDir}/backend/ssr_dev.js`;
          const { default: render } = await import(buildPath + `?t=${Date.now()}`);
          const page = await req.json();
          const result = await render(page);
          return Response.json(result);
        } catch (error: any) {
          console.error("SSR Error:", error);
          return new Response(JSON.stringify({ error: error.message }), { status: 500 });
        }
      }

      const corsHeaders = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      };

      if (req.method === "OPTIONS") {
        return new Response(null, { headers: corsHeaders });
      }

      if (url.pathname === "/ws") {
        if (server.upgrade(req)) return;
        return new Response("Upgrade failed", { status: 500 });
      }

      if (url.pathname.endsWith(".js")) {
        const filePath = `./static/dist${url.pathname}`;
        const file = Bun.file(filePath);
        if (await file.exists()) {
          return new Response(file, {
            headers: { ...corsHeaders, "Content-Type": "application/javascript" },
          });
        }
      }

      if (url.pathname === "/client.css") {
        return new Response(Bun.file("./static/dist/client.css"), {
          headers: { ...corsHeaders, "Content-Type": "text/css" },
        });
      }

      return new Response("Not Found", { status: 404, headers: corsHeaders });
    },
    websocket: {
      message() { },
      open(_ws) {
        console.log("Browser connected to Hot Reload");
      },
    },
  });

  console.log(`👀 Watcher & Asset Server running on http://localhost:${server.port}`);

  const _watcher = watch("./frontend", { recursive: true }, async (event, filename) => {
    if (filename) {
      await build();
      server.publish("reload", "reload");
    }
  });
}

// ==================== BUILD COMMAND ====================
async function build() {
  await generateEntryFiles();

  // Import tailwind plugin from user's project
  const { default: tailwindcss } = await import(
    path.join(projectDir, "node_modules", "bun-plugin-tailwind")
  );

  // Bundle the Client (for Browser)
  await Bun.build({
    entrypoints: [entryClient],
    outdir: "./static/dist",
    naming: "client.[ext]",
    target: "browser",
    splitting: true,
    minify: true,
    plugins: [tailwindcss],
  });
  console.log("✅ Client Bundle Built");

  // Bundle the Server (for SSR)
  await Bun.build({
    entrypoints: [entrySSRServer],
    outdir: "./backend",
    naming: { entry: "ssr.js" },
    target: "bun",
    external: ["react", "react-dom", "@inertiajs/react", "@inertiajs/react/server"],
    plugins: [tailwindcss],
  });
  console.log("✅ SSR Bundles Built");
}

// ==================== SSR COMMAND ====================
async function ssr() {
  const ssrPath = path.join(projectDir, "backend", "ssr.js");

  if (!fs.existsSync(ssrPath)) {
    console.error("❌ Error: SSR server bundle not found at backend/ssr.js");
    console.error("   Run 'vegabase build' first to create the production bundle.");
    process.exit(1);
  }

  const port = Number(process.env.PORT) || 13714;

  console.log(`🚀 Starting SSR server on port ${port}...`);
  console.log(`   Bundle: ${ssrPath}`);
  console.log(`   Press Ctrl+C to stop`);
  console.log("");

  try {
    await import(ssrPath);
  } catch (error: any) {
    console.error("❌ Error starting SSR server:");
    console.error(error.message);
    process.exit(1);
  }
}

// ==================== CLI ROUTER ====================
const command = process.argv[2];

switch (command) {
  case "dev":
    await dev();
    break;
  case "build":
    await build();
    break;
  case "ssr":
    await ssr();
    break;
  default:
    console.error("Unknown command. Available commands: dev, build, ssr");
    process.exit(1);
}
