/* Optional browser smoke: node tests/browser/patna_map.cjs
 * Requires development Playwright + Chromium, not hosted Python dependencies.
 * Tiles are deliberately aborted: this deterministic check never bulk-fetches OSM.
 * Run against an already-started Streamlit server. Screenshots go to scratch.
 */
const {chromium, expect} = require('playwright/test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const output=process.env.FLOODCAT_SCREENSHOTS || '/tmp/floodcat-ui-smoke';
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 try {
  fs.mkdirSync(output,{recursive:true});
  const page=await browser.newPage({viewport:{width:1440,height:1100}});
  await page.route('https://tile.openstreetmap.org/**',r=>r.abort());
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const started=Date.now();
  await page.goto(process.env.FLOODCAT_URL||'http://localhost:8501');
  await page.getByText('REAL — Patna',{exact:true}).click();
  await expect(page.getByText('2,840,321',{exact:true})).toBeVisible();
  const frame=page.frameLocator('iframe[title="st.iframe"]');
  await frame.getByText('Fit study area',{exact:true}).waitFor();
  const f=page.frames().find(f=>f!==page.mainFrame());
  await f.waitForFunction(()=>window.floodcatMap && document.querySelector('canvas.native-grid'));
  const initializedMs=Date.now()-started;
  const initial=await f.evaluate(()=>{
   const {map,grid,depthLayer,cellInfo}=window.floodcatMap;
   const ctx=depthLayer.canvas.getContext('2d');
   return {zoom:map.getZoom(),center:map.getCenter(),bounds:grid.bounds,
    size:[grid.rows,grid.cols],drawMs:depthLayer.lastDrawMs,
    first:cellInfo(25.7375,84.67916666666667),last:cellInfo(25.20416666666667,86.07083333333334),
    outside:cellInfo(25.19,85),pixels:Array.from(ctx.getImageData(0,0,depthLayer.canvas.width,depthLayer.canvas.height).data).filter((v,i)=>i%4===3&&v>0).length};
  });
  assert.deepEqual(initial.size,[65,168]);
  assert.equal(initial.first.row,0);assert.equal(initial.first.col,0);
  assert.equal(initial.last.row,64);assert.equal(initial.last.col,167);
  assert.equal(initial.outside,null);assert(initial.pixels>10000);
  assert(Math.abs(initial.bounds[0][0]-25.2)<1e-12);
  assert(Math.abs(initial.bounds[0][1]-84.675)<1e-12);
  assert(Math.abs(initial.bounds[1][1]-86.075)<1e-12);
  await frame.getByTitle('Zoom in',{exact:true}).click();
  await f.waitForFunction(z=>window.floodcatMap.map.getZoom()===z,initial.zoom+1);
  await frame.getByTitle('Zoom out',{exact:true}).click();
  await f.waitForFunction(z=>window.floodcatMap.map.getZoom()===z,initial.zoom);
  const mapBox=await page.locator('iframe').boundingBox();
  await page.mouse.move(mapBox.x+mapBox.width/2,mapBox.y+200);
  await page.mouse.wheel(0,-500);
  await f.waitForFunction(z=>window.floodcatMap.map.getZoom()>z,initial.zoom);
  const before=await f.evaluate(()=>window.floodcatMap.map.getCenter().lng);
  await page.mouse.move(mapBox.x+mapBox.width/2,mapBox.y+200);
  await page.mouse.down();await page.mouse.move(mapBox.x+mapBox.width/2+90,mapBox.y+240,{steps:10});await page.mouse.up();
  await f.waitForFunction(v=>Math.abs(window.floodcatMap.map.getCenter().lng-v)>.001,before);
  await frame.getByText('Fit study area',{exact:true}).click();
  await f.waitForFunction(z=>window.floodcatMap.map.getZoom()===z,initial.zoom);
  await frame.getByText('Joint exposure coverage',{exact:true}).click();
  await f.waitForFunction(()=>window.floodcatMap.map.hasLayer(window.floodcatMap.coverageLayer));
  await expect(frame.locator('#legend')).toContainText('Incomplete / excluded');
  await frame.getByText('Depth-weighted population exposure',{exact:true}).click();
  await f.waitForFunction(()=>window.floodcatMap.map.hasLayer(window.floodcatMap.weightedLayer));
  await expect(frame.locator('#legend')).toContainText('person-metres');
  const top=await f.evaluate(()=>window.floodcatMap.cellInfo(25.6375,85.4125));
  assert.equal(top.row,12);assert.equal(top.col,88);assert.equal(top.common,true);
  assert(Math.abs(top.weightedPopulation-27866.62094754255)<1e-8);
  assert.equal(initial.first.population,null);assert.equal(initial.first.weightedPopulation,null);
  await frame.getByText('Flood Depth (m)',{exact:true}).click();
  await f.waitForFunction(()=>window.floodcatMap.map.hasLayer(window.floodcatMap.depthLayer));
  // Click known source-cell centre; inspect popup reads actual native value.
  const point=await f.evaluate(()=>{const p=window.floodcatMap.map.latLngToContainerPoint([25.7375,84.67916666666667]);return{x:p.x,y:p.y}});
  await page.mouse.click(mapBox.x+point.x,mapBox.y+point.y);
  await expect(frame.locator('.leaflet-popup-content')).toContainText('Cell 0, 0');
  await expect(frame.locator('#tile-status')).toContainText('unavailable');
  await page.getByText('Export summaries',{exact:true}).click();
  await expect(page.getByText('Download current exposure CSV',{exact:true})).toBeVisible();
  await page.screenshot({path:output+'/desktop.png',fullPage:true});
  await frame.getByRole('button',{name:'Close popup'}).click();
  const stats=await f.evaluate(()=>({drawMs:window.floodcatMap.depthLayer.lastDrawMs,canvas:document.querySelector('canvas.native-grid').width}));
  const close=page.getByTestId('stSidebarCollapseButton').getByRole('button');
  if(await close.isVisible())await close.click();
  await page.setViewportSize({width:390,height:844});
  await expect(page.getByText('2,840,321',{exact:true})).toBeVisible();
  await f.waitForFunction(()=>window.floodcatMap.map.getSize().x<400);
  await frame.getByText('Fit study area',{exact:true}).click();
  await frame.locator('#map').scrollIntoViewIfNeeded();
  await page.screenshot({path:output+'/mobile.png',fullPage:true});
  const mobile=await f.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,canvas:document.querySelector('canvas.native-grid').width,drawMs:window.floodcatMap.depthLayer.lastDrawMs}));
  assert(mobile.scrollWidth<=mobile.width+1);assert(mobile.width>=250);
  assert.equal(errors.length,0,errors.join('\n'));
  console.log(JSON.stringify({status:'passed',initializedMs,initial,stats,mobile,checks:['native bounds/values','zoom +/-','wheel zoom','drag pan','fit/reset','layer switching','cell popup','blocked-tiles fallback','CSV controls','desktop/mobile']},null,2));
 } finally {await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
