/* User-attested source-selection recipe for the uploaded scenarios.
 * Reproducible prospective script, NOT independent proof of completed tasks.
 * Historical T100 already exists: task creation intentionally skipped for it.
 */
var district = ee.FeatureCollection('FAO/GAUL/2025/level2')
 .filter(ee.Filter.eq('ISO3_CODE','IND')).filter(ee.Filter.eq('GAUL1_NAME','Bihar'))
 .filter(ee.Filter.eq('GAUL2_NAME','Patna'));
if(district.size().getInfo()!==1) throw new Error('Patna is not unique');
var region=district.geometry().buffer(500).bounds(1);
var collection='WRI/Aqueduct_Flood_Hazard_Maps/V2/';
var climates=[['Historical','historical','000000000WATCH',1980],
 ['RCP45_2050','rcp4p5','0000HadGEM2-ES',2050],['RCP85_2050','rcp8p5','0000HadGEM2-ES',2050]];
climates.forEach(function(s){
 function id(rp){return collection+'inunriver_'+s[1]+'_'+s[2]+'_'+s[3]+'_rp'+('00000'+rp).slice(-5);}
 var reference=ee.Image(id(100)).select('inundation_depth').projection().getInfo();
 [25,50,100,250,500].forEach(function(rp){
  var image=ee.Image(id(rp));
  var props=image.toDictionary(['floodtype','climatescenario','model','year','returnperiod']).getInfo();
  if(props.floodtype!=='inunriver'||props.climatescenario!==s[1]||props.model!==s[2]||
     Number(props.year)!==s[3]||Number(props.returnperiod)!==rp) throw new Error('Unexpected source: '+id(rp));
  print(id(rp),props,image.projection());
  if(s[0]==='Historical'&&rp===100)return;
  var name='FloodCAT_Patna_WRI_'+s[0]+'_T'+rp;
  Export.image.toDrive({image:image.select('inundation_depth').toFloat().unmask(-9999,false),
   description:name,fileNamePrefix:name,folder:'Flood_CAT_Patna',region:region,
   crs:reference.crs||reference.wkt,crsTransform:reference.transform,maxPixels:1e9,
   fileFormat:'GeoTIFF',formatOptions:{cloudOptimized:true,noData:-9999}});
 });
});
