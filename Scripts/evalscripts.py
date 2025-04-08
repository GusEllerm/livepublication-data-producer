discover_evalscript = """
  //VERSION=3
function setup() {
  return {
    input: [{
      bands: [], 
      metadata: ["bounds"]
    }],
    mosaicking: Mosaicking.ORBIT,
    output: {
      bands: 0,
    },
  }
}

function evaluatePixel(sample) {
  return []
}

function updateOutputMetadata(scenes, inputMetadata, outputMetadata) {
  outputMetadata.userData = {
    orbits: scenes.orbits.map(function(orbit, index) {
      return {
        dateFrom: orbit.dateFrom,
        dateTo: orbit.dateTo,
        tiles: orbit.tiles.map(function(tile, tIndex) {
          return {
            tileId: tile.shId,
            productId: tile.productId,
            date: tile.date,
            cloudCoverage: tile.cloudCoverage,
            dataEnvelope: tile.dataEnvelope
          };
        })
      };
    }),
    description: "Test description"
  };
}
"""

evalscript_raw_bands = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B02", "B03", "B04", "B08", "B11", "B12", "SCL"] }],
    output: { bands: 7, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(sample) {
  return [
    sample.B02, 
    sample.B03, 
    sample.B04, 
    sample.B08, 
    sample.B11, 
    sample.B12,
    sample.SCL
    ];
}
"""