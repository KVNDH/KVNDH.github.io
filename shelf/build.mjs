// 허브 선반 묶음을 만든다: shelf/main.js + three(쓰는 것만) + shelf.css -> static/hub-shelf.js
// 사용: node shelf/build.mjs
// node_modules(three r186, esbuild)는 저장소에 넣지 않는다. 기본은 ../tmp/site-motion-2026-09-30/node_modules,
// 다른 곳이면 SHELF_NODE_MODULES 로 준다.
// 줄이는 법: three 를 src 모듈로 묶어 쓰지 않는 클래스를 털고, WebXR 과 환경맵 PMREM 은 shelf/stubs 의 대역으로 바꾸고, 셰이더 조각은 이 선반이 실제로 쓰는 것
// (shelf.js 의 셰이더와 그림자 지도의 깊이 재질이 #include 로 닿는 것)만 남겨 주석과 들여쓰기를 걷는다.
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '..');
const nm = process.env.SHELF_NODE_MODULES || path.resolve(repo, '..', 'tmp', 'site-motion-2026-09-30', 'node_modules');
const esbuild = createRequire(path.join(nm, 'noop.js'))('esbuild');
const shaders = path.join(nm, 'three', 'src', 'renderers', 'shaders');

const KEEP_LIB = new Set(['depth']);                     // 쓰는 내장 재질(그림자 지도의 깊이 재질)
const ALWAYS = ['colorspace_pars_fragment'];              // WebGLProgram 이 직접 붙이는 조각(톤 매핑은 쓰지 않는다)
const INCLUDE = /#include +<(\w+)>/g;

function includesOf(text) { return [...text.matchAll(INCLUDE)].map(m => m[1]); }
function usedChunks() {
  const seeds = new Set(ALWAYS);
  includesOf(fs.readFileSync(path.join(here, 'shelf.js'), 'utf8')).forEach(n => seeds.add(n));
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
// 쓰지 않는 기능(WebXR, 환경맵 PMREM)은 대역으로 바꾼다
const stubs = {
  name: 'stubs',
  setup(b) {
    b.onLoad({ filter: /[\\/]three[\\/]src[\\/].*[\\/](WebXRManager|PMREMGenerator)\.js$/ }, args => {
      if (/[\\/]common[\\/]/.test(args.path)) return undefined;
      return { contents: fs.readFileSync(path.join(here, 'stubs', path.basename(args.path)), 'utf8'), loader: 'js' };
    });
  }
};
// shelf.css 는 줄여서 글자열로 넣는다(main.js 가 <style> 로 붙인다)
const cssText = {
  name: 'css-text',
  setup(b) {
    b.onLoad({ filter: /\.css$/ }, async args => {
      const r = await esbuild.transform(fs.readFileSync(args.path, 'utf8'), { loader: 'css', minify: true });
      return { contents: 'export default ' + JSON.stringify(r.code.trim()) + ';', loader: 'js' };
    });
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
  outfile: path.join(repo, 'static', 'hub-shelf.js'),
  bundle: true, minify: true, format: 'iife', target: ['es2020'],
  nodePaths: [nm], legalComments: 'eof',
  plugins: [trimShaders, stubs, cssText], metafile: true, logLevel: 'warning',
  banner: { js: '/* kvndh 허브 선반. three.js r186 (MIT, Copyright 2010-2025 Three.js Authors) 일부를 묶었다. 원본: shelf/ */' }
});
const out = Object.entries(res.metafile.outputs)[0];
console.log(path.relative(repo, out[0]), Math.round(out[1].bytes / 1024) + 'KB', '셰이더 조각', USED.size);
if (process.env.SHELF_META) console.log(await esbuild.analyzeMetafile(res.metafile, { verbose: false }));
// 크기 보고: three 몫만 따로 묶어 gzip 으로 잰다(목표 130KB 이하)
const zlib = await import('node:zlib');
const gz = buf => (zlib.gzipSync(buf, { level: 9 }).length / 1024).toFixed(1) + 'KB';
const three = await esbuild.build({ entryPoints: [path.join(here, 'three-lite.js')], bundle: true, minify: true, format: 'iife',
  globalName: 'T', target: ['es2020'], nodePaths: [nm], plugins: [trimShaders, stubs], write: false, logLevel: 'warning' });
console.log('gzip: 전체', gz(fs.readFileSync(path.join(repo, 'static', 'hub-shelf.js'))), '/ three', gz(three.outputFiles[0].contents));
