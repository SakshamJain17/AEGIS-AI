"use strict";

const {
  app,
  BrowserWindow,
  shell,
  session
} = require("electron");

const path = require("path");
const { spawn } = require("child_process");

let mainWindow = null;
let backendProcess = null;

const BACKEND_HOST = "127.0.0.1";
const BACKEND_PORT = 8000;

const FRONTEND_URL =
  "http://localhost:5173";

function getBackendDirectory() {
  return path.resolve(
    __dirname,
    "../backend"
  );
}

function getPythonExecutable() {
  return path.join(
    getBackendDirectory(),
    ".venv",
    "bin",
    "python"
  );
}

function startBackend() {
  const python =
    getPythonExecutable();

  console.log(
    "[AEGIS] Starting Python backend..."
  );

  backendProcess = spawn(
    python,
    [
      "-m",
      "uvicorn",
      "app.main:app",
      "--host",
      BACKEND_HOST,
      "--port",
      String(BACKEND_PORT)
    ],
    {
      cwd: getBackendDirectory(),

      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1"
      },

      stdio: [
        "ignore",
        "pipe",
        "pipe"
      ]
    }
  );

  backendProcess.stdout.on(
    "data",
    (data) => {
      console.log(
        `[AEGIS BACKEND] ${data}`
      );
    }
  );

  backendProcess.stderr.on(
    "data",
    (data) => {
      console.error(
        `[AEGIS BACKEND] ${data}`
      );
    }
  );

  backendProcess.on(
    "exit",
    (code, signal) => {
      console.log(
        `[AEGIS BACKEND] exited: code=${code}, signal=${signal}`
      );

      backendProcess = null;
    }
  );
}

async function waitForBackend() {
  for (let i = 0; i < 60; i++) {
    try {
      const response =
        await fetch(
          `http://${BACKEND_HOST}:${BACKEND_PORT}/health`
        );

      if (response.ok) {
        console.log(
          "[AEGIS] Backend ready."
        );

        return true;
      }
    } catch {
      // Backend still starting.
    }

    await new Promise(
      (resolve) =>
        setTimeout(resolve, 250)
    );
  }

  return false;
}

async function waitForFrontend() {
  for (let i = 0; i < 60; i++) {
    try {
      const response =
        await fetch(
          FRONTEND_URL
        );

      if (response.ok) {
        console.log(
          "[AEGIS] Frontend ready."
        );

        return true;
      }
    } catch {
      // Vite still starting.
    }

    await new Promise(
      (resolve) =>
        setTimeout(resolve, 250)
    );
  }

  return false;
}

async function createMainWindow() {
  mainWindow =
    new BrowserWindow({
      width: 1680,
      height: 1050,

      minWidth: 1200,
      minHeight: 760,

      backgroundColor: "#06050A",

      title: "AEGIS",

      show: false,

      titleBarStyle: "hiddenInset",

      trafficLightPosition: {
        x: 18,
        y: 18
      },

      webPreferences: {
        preload: path.join(
          __dirname,
          "preload.js"
        ),

        contextIsolation: true,
        nodeIntegration: false,
        sandbox: true,

        spellcheck: false
      }
    });

  mainWindow.removeMenu();

  mainWindow.webContents.setWindowOpenHandler(
    ({ url }) => {
      shell.openExternal(url);

      return {
        action: "deny"
      };
    }
  );

  const backendReady =
    await waitForBackend();

  if (!backendReady) {
    throw new Error(
      "AEGIS backend failed to start."
    );
  }

  const frontendReady =
    await waitForFrontend();

  if (!frontendReady) {
    throw new Error(
      "AEGIS frontend failed to start."
    );
  }

  await mainWindow.loadURL(
    FRONTEND_URL
  );

  mainWindow.once(
    "ready-to-show",
    () => {
      mainWindow.show();

      if (process.env.AEGIS_DEVTOOLS === "1") {
        mainWindow.webContents.openDevTools();
      }
    }
  );

  mainWindow.on(
    "closed",
    () => {
      mainWindow = null;
    }
  );
}

function stopBackend() {
  if (!backendProcess) {
    return;
  }

  console.log(
    "[AEGIS] Stopping backend..."
  );

  try {
    backendProcess.kill(
      "SIGTERM"
    );
  } catch {
    // Already stopped.
  }

  backendProcess = null;
}

app.whenReady().then(
  async () => {
    session.defaultSession.setPermissionRequestHandler(
      (
        _webContents,
        permission,
        callback
      ) => {
        callback(
          permission === "media"
        );
      }
    );

    startBackend();

    try {
      await createMainWindow();
    } catch (error) {
      console.error(
        "[AEGIS] Failed to launch:",
        error
      );

      stopBackend();
      app.quit();

      return;
    }

    app.on(
      "activate",
      async () => {
        if (
          BrowserWindow
            .getAllWindows()
            .length === 0
        ) {
          await createMainWindow();
        }
      }
    );
  }
);

app.on(
  "before-quit",
  () => {
    stopBackend();
  }
);

app.on(
  "window-all-closed",
  () => {
    if (
      process.platform !== "darwin"
    ) {
      app.quit();
    }
  }
);