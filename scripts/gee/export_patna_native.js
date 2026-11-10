/* User-supplied M2C-1 export recipe, transcribed from the supplied script.
 * Map/print-only presentation was omitted; source selection and export operations
 * are retained. Not executed here; task IDs and acquisition times were not supplied.
 * Export is the buffered district BOUNDING RECTANGLE, not a district polygon clip.
 */
var FOLDER = 'Flood_CAT_Patna';
var NODATA = -9999;
var HALO_METRES = 500;
var patna = ee.FeatureCollection('FAO/GAUL/2025/level2')
  .filter(ee.Filter.eq('ISO3_CODE', 'IND'))
  .filter(ee.Filter.eq('GAUL1_NAME', 'Bihar'))
  .filter(ee.Filter.eq('GAUL2_NAME', 'Patna'));
if (patna.size().getInfo() !== 1) throw new Error('Patna boundary not unique');
var district = patna.geometry();
var exportRegion = district.buffer(HALO_METRES).bounds(1);
var wri = ee.Image('WRI/Aqueduct_Flood_Hazard_Maps/V2/' +
  'inunriver_historical_000000000WATCH_1980_rp00100').select('inundation_depth');
var wpCollection = ee.ImageCollection('WorldPop/GP/100m/pop')
  .filter(ee.Filter.eq('country', 'IND')).filter(ee.Filter.eq('year', 2020));
if (wpCollection.size().getInfo() !== 1) throw new Error('WorldPop match not unique');
var wpImage = ee.Image(wpCollection.first());
if (wpImage.get('system:index').getInfo() !== 'IND_2020') throw new Error('Unexpected WorldPop version');
var worldpop = wpImage.select('population');
var ghsl = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/2020').select('built_surface');
function exportNative(image, name) {
  var proj = image.projection();
  var info = proj.getInfo();
  var nativeCRS = info.crs || info.wkt;
  var nativeTransform = info.transform;
  if (!nativeTransform) nativeTransform = proj.transform().getInfo();
  if (!nativeCRS || !nativeTransform || nativeTransform.length !== 6)
    throw new Error('Missing native projection metadata');
  var output = image.toFloat().unmask(NODATA, false);
  Export.image.toDrive({image: output, description: name, folder: FOLDER,
    fileNamePrefix: name, region: exportRegion, crs: nativeCRS,
    crsTransform: nativeTransform, maxPixels: 1e9, fileFormat: 'GeoTIFF',
    formatOptions: {cloudOptimized: true, noData: NODATA}});
}
exportNative(wri, 'FloodCAT_Patna_WRI_Historical_T100');
exportNative(worldpop, 'FloodCAT_Patna_WorldPop_2020');
exportNative(ghsl, 'FloodCAT_Patna_GHSL_BuiltSurface_2020');
