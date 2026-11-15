# The VR room (a Fabric App)

This folder is a complete Fabric App project: Microsoft's Fabric App template (MIT license, see `LICENSE`) with the
VR room from the video on top of it. The install steps are in the [README one level up](../README.md).

Where the room is:

| What | Where |
|---|---|
| The room itself (three.js, WebXR) | `packages/frontend/src/vr/` |
| The page that loads the model and starts the room | `packages/frontend/src/App.tsx`, `VrRoom.tsx` |
| The one DAX query the room asks | `packages/frontend/src/queries/aurora-cube.dax` |
| The picture of the guide | `packages/frontend/public/guide.png` (put your own picture there) |
| The question to a Fabric data agent (optional) | `packages/functions/src/function_app.ts`, `agent_endpoint.ts` |
| The connection to your semantic model | `rayfin/rayfin.yml` (two ids to fill in) |
| A page to look at the room on your PC, with sample numbers and no Fabric | `packages/frontend/preview.html` |
