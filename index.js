// Flatcap is a declarative theme plugin: everything it contributes lives in
// openclaw.plugin.json and themes/flatcap.json, which OpenClaw reads as static data.
// OpenClaw's plugin discovery still expects a runtime entry, so this one registers nothing.
export default {
  id: "flatcap",
  name: "Flatcap",
  description: "Flatcap 2.0 appearance theme for the OpenClaw Control UI.",
  register() {},
};
