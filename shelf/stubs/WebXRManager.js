// 선반은 WebXR 을 쓰지 않는다. WebGLRenderer 가 부르는 자리만 비워 둔 대역(묶음을 줄인다)
class WebXRManager {
  constructor() { this.enabled = false; this.isPresenting = false; this.cameraAutoUpdate = true; }
  addEventListener() {}
  removeEventListener() {}
  dispose() {}
  setAnimationLoop() {}
  getCamera() { return null; }
  updateCamera() {}
  getDepthSensingMesh() { return null; }
  hasDepthSensing() { return false; }
  getEnvironmentBlendMode() { return undefined; }
}
export { WebXRManager };
