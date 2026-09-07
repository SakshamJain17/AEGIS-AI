"use strict";

const {
  contextBridge
} = require("electron");

contextBridge.exposeInMainWorld(
  "aegisDesktop",
  {
    platform:
      process.platform,

    electronVersion:
      process.versions.electron
  }
);