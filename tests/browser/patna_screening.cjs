/* Development-only browser checks; no provider tiles downloaded. */
const {chromium,expect}=require('playwright/test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 try{
  const out=process.env.FLOODCAT_SCREENSHOTS||'/tmp/floodcat-screening';fs.mkdirSync(out,{recursive:true});
  const p=await b.newPage({viewport:{width:1440,height:1100}});
  await p.route('https://tile.openstreetmap.org/**',r=>r.abort());
  const errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.goto(process.env.FLOODCAT_URL||'http://localhost:8501');
  await p.getByText('REAL — Patna',{exact:true}).click();
  await p.getByText('Vulnerability',{exact:true}).click();
  await expect(p.getByText('Depth-weighted exposure screening — not a validated vulnerability model.',{exact:true})).toBeVisible();
  await expect(p.getByText('2,923,558',{exact:true})).toBeVisible();
  const frame=p.frameLocator('iframe[title="st.iframe"]');
  await frame.getByText('Fit study area',{exact:true}).waitFor();
  const f=p.frames().find(f=>f!==p.mainFrame());
  await f.waitForFunction(()=>window.floodcatMap?.weightedLayer&&window.floodcatMap.map.hasLayer(window.floodcatMap.weightedLayer));
  await expect(frame.locator('#legend')).toContainText('person-metres');
  const top=await f.evaluate(()=>{
   const a=window.floodcatMap;return{info:a.cellInfo(25.6375,85.4125),point:a.map.latLngToContainerPoint([25.6375,85.4125]),drawMs:a.weightedLayer.lastDrawMs};
  });
  assert(Math.abs(top.info.population-5126.351453354646)<1e-8);
  assert(Math.abs(top.info.weightedPopulation-top.info.population*top.info.depth)<1e-8);
  await frame.locator('#map').scrollIntoViewIfNeeded();
  const box=await p.locator('iframe').boundingBox();
  await p.mouse.click(box.x+top.point.x,box.y+top.point.y);
  await expect(frame.locator('.leaflet-popup-content')).toContainText('Cell 12, 88');
  await expect(frame.locator('.leaflet-popup-content')).toContainText('person-metres');
  await expect(frame.locator('.leaflet-popup-content')).toContainText('Complete common cell');
  await p.screenshot({path:out+'/screening-map.png',fullPage:true});
  await expect(p.getByText('Top 10 complete-cell screening priorities',{exact:true})).toBeVisible();
  const downloadEvent=p.waitForEvent('download');
  await p.getByText('Download screening indicators CSV',{exact:true}).click();
  const download=await downloadEvent;const stream=await download.createReadStream();let csv='';for await(const chunk of stream)csv+=chunk;
  assert(csv.includes('person-metres'));assert(csv.includes('m²·m'));assert(csv.includes('2923557.7298654984'));
  assert(csv.includes('not flood volume'));
  const prioritiesEvent=p.waitForEvent('download');
  await p.getByText('Download raster-cell priorities CSV',{exact:true}).click();
  const prioritiesDownload=await prioritiesEvent;const prioritiesStream=await prioritiesDownload.createReadStream();let prioritiesCsv='';
  for await(const chunk of prioritiesStream)prioritiesCsv+=chunk;
  fs.writeFileSync(out+'/priorities.csv',prioritiesCsv);
  assert(prioritiesCsv.includes('27866.62094754255'));
  assert(prioritiesCsv.includes('Common-data footprint; not all of Patna district.'));
  assert(prioritiesCsv.includes('not a validated vulnerability model'));

  const slider=p.getByRole('slider');await slider.press('End');
  await expect(p.getByText('No complete flooded cells above the selected threshold; no cell priorities are ranked.',{exact:true})).toBeVisible();
  await expect(p.getByText('Download raster-cell priorities CSV',{exact:true})).toHaveCount(0);
  await slider.press('Home');
  await expect(p.getByText('2,923,558',{exact:true})).toBeVisible();
  // A mobile map screenshot verifies the new layer selector/legend fit.
  const close=p.getByTestId('stSidebarCollapseButton').getByRole('button');if(await close.isVisible())await close.click();
  await p.setViewportSize({width:390,height:844});
  const mobileFrame=p.frameLocator('iframe[title="st.iframe"]');
  await mobileFrame.locator('#map').scrollIntoViewIfNeeded();
  const mf=p.frames().find(f=>f!==p.mainFrame());
  await mf.waitForFunction(()=>window.floodcatMap?.map.getSize().x<400);
  await mobileFrame.getByText('Fit study area',{exact:true}).click();
  const fitBox=await mobileFrame.getByText('Fit study area',{exact:true}).boundingBox();
  const layersBox=await mobileFrame.locator('.leaflet-control-layers').boundingBox();
  assert(fitBox.x+fitBox.width<=layersBox.x || fitBox.y>=layersBox.y+layersBox.height,'Mobile fit/layers overlap');
  await p.screenshot({path:out+'/screening-mobile.png',fullPage:true});
  const mobile=await mf.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,drawMs:window.floodcatMap.weightedLayer.lastDrawMs}));
  assert(mobile.scrollWidth<=mobile.width+1);
  assert.equal(errors.length,0,errors.join('\n'));
  console.log(JSON.stringify({status:'passed',top,mobile,checks:['weighted default layer','native complete-cell popup and units','actual screening CSV contents','empty threshold selection','mobile weighted map','no JavaScript errors']},null,2));
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exit(1)});
