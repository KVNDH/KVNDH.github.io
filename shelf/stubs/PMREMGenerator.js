// 선반은 환경맵을 쓰지 않는다. WebGLEnvironments 가 환경맵이 있을 때만 만드는 것을 비워 둔 대역
class PMREMGenerator {
  fromEquirectangular() { return null; }
  fromCubemap() { return null; }
  fromScene() { return null; }
  dispose() {}
}
export { PMREMGenerator };
