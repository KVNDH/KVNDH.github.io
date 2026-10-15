// 화첩 3D 판 묶음을 만든다: canvas/main.js + three(쓰는 것만) -> assets/kvndh-canvas.js (build.py 가 docs/assets 로 복사)
// 사용: (cd canvas && npm ci) 한 번, 그 뒤 node canvas/build.mjs
// 판은 canvas/package.json 과 package-lock.json 이 고정한다(three 0.186.1, esbuild 0.28.2). node_modules 는 커밋하지 않는다.
// canvas/node_modules 가 없으면 CANVAS_NODE_MODULES, 그다음 옛 shelf/node_modules 를 쓴다.
// 묶음 머리 주석에 원본 해시(src:)를 적는다. check.py 가 다시 재어 다르면 '묶음 다시 만들 것'으로 실패한다.
// 줄이는 법: three 를 src 모듈로 묶어 쓰지 않는 클래스를 털고, WebXR 은 canvas/stubs 의 대역으로 바꾸고, 셰이더 조각은
// 판이 실제로 쓰는 재질(유약 몸 MeshPhysical, RoomEnvironment 의 MeshStandard 와 MeshLambert, 그림자 MeshBasic)이 #include 로 닿는 것만 남긴다.
import { createRequire } from 'node:module';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '..');
const nm = [path.join(here, 'node_modules'), process.env.CANVAS_NODE_MODULES, path.join(repo, 'shelf', 'node_modules')]
  .find(d => d && fs.existsSync(path.join(d, 'three', 'package.json')));
if (!nm) throw new Error('three 와 esbuild 가 없습니다. cd canvas && npm ci');
const outfile = process.env.CANVAS_OUT || path.join(repo, 'assets', 'kvndh-canvas.js');
// 원본 해시: check.py 의 canvas_source_hash 와 같은 방법(상대 경로와 내용을 차례로)
function sourceHash() {
  const files = ['build.mjs', 'main.js', 'package-lock.json']
    .concat(fs.readdirSync(path.join(here, 'stubs')).sort().map(f => 'stubs/' + f));
  const h = crypto.createHash('sha256');
  for (const f of files) { h.update(f + '\0'); h.update(fs.readFileSync(path.join(here, f))); h.update('\0'); }
  return h.digest('hex').slice(0, 16);
}
const esbuild = createRequire(path.join(nm, 'noop.js'))('esbuild');
const shaders = path.join(nm, 'three', 'src', 'renderers', 'shaders');

const KEEP_LIB = new Set(['meshphysical', 'meshbasic', 'meshlambert']);  // 쓰는 내장 재질(MeshStandard 도 meshphysical, RoomEnvironment 의 빛 상자는 lambert)
const ALWAYS = ['colorspace_pars_fragment'];               // WebGLProgram 이 직접 붙이는 조각(톤 매핑은 쓰지 않는다)
const INCLUDE = /#include +<(\w+)>/g;
function includesOf(text) { return [...text.matchAll(INCLUDE)].map(m => m[1]); }
function usedChunks() {
  const seeds = new Set(ALWAYS);
  for (const lib of KEEP_LIB) includesOf(fs.readFileSync(path.join(shaders, 'ShaderLib', lib + '.glsl.js'), 'utf8')).forEach(n => seeds.add(n));
  const used = new Set(), todo = [...seeds];
  while (todo.length) {
    const n = todo.pop();
    if (used.has(n)) continue;
    used.add(n);
    const f = path.join(shaders, 'ShaderChunk', n + '.glsl.js');
    if (fs.existsSync(f)) includesOf(fs.readFileSync(f, 'utf8')).forEach(m => todo.push(m));
  }
  return used;
}
const stubs = {
  name: 'stubs',
  setup(b) {
    b.onResolve({ filter: /^three$/ }, () => ({ path: path.join(nm, 'three', 'src', 'Three.js') }));
    b.onLoad({ filter: /[\\/]three[\\/]src[\\/]renderers[\\/]webxr[\\/]WebXRManager\.js$/ }, () =>
      ({ contents: fs.readFileSync(path.join(here, 'stubs', 'WebXRManager.js'), 'utf8'), loader: 'js' }));
  }
};
// 템플릿 문자열 속 GLSL 의 주석, 들여쓰기, 빈 줄을 걷는다(# 지시문은 줄 그대로)
function squeezeGlsl(js) {
  return js.replace(/`([^`]*)`/g, (all, body) => {
    if (body.includes('${')) return all;
    const out = body.replace(/\/\*[\s\S]*?\*\//g, '').split('\n')
      .map(l => l.replace(/\/\/.*$/, '').replace(/\s+/g, ' ').trim()).filter(Boolean).join('\n');
    return '`' + out + '\n`';
  });
}
const USED = usedChunks();
const trimShaders = {
  name: 'trim-shaders',
  setup(b) {
    b.onLoad({ filter: /[\\/]renderers[\\/]shaders[\\/]Shader(Chunk|Lib)[\\/]\w+\.glsl\.js$/ }, args => {
      const kind = path.basename(path.dirname(args.path)), name = path.basename(args.path, '.glsl.js');
      if (kind === 'ShaderLib' && !KEEP_LIB.has(name)) return { contents: "export const vertex = '', fragment = '';", loader: 'js' };
      if (kind === 'ShaderChunk' && !USED.has(name)) return { contents: "export default '';", loader: 'js' };
      return { contents: squeezeGlsl(fs.readFileSync(args.path, 'utf8')), loader: 'js' };
    });
  }
};

const res = await esbuild.build({
  entryPoints: [path.join(here, 'main.js')],
  outfile,
  bundle: true, minify: true, format: 'iife', target: ['es2020'],
  nodePaths: [nm], legalComments: 'eof',
  plugins: [trimShaders, stubs], metafile: true, logLevel: 'warning',
  banner: { js: '/* kvndh 화첩 판. three.js r186 (MIT, Copyright 2010-2025 Three.js Authors) 일부를 묶었다. 원본: canvas/ src:' + sourceHash() + ' */' }
});
const out = Object.entries(res.metafile.outputs)[0];
const zlib = await import('node:zlib');
console.log(path.relative(repo, out[0]), Math.round(out[1].bytes / 1024) + 'KB', 'gzip', (zlib.gzipSync(fs.readFileSync(outfile), { level: 9 }).length / 1024).toFixed(1) + 'KB', '셰이더 조각', USED.size);
