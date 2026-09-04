# Glossary

- **Module**: one HB-Laser 3D HydroMatrix HD Single Module. Ten jets and ten pixels in a row at 50 mm pitch.
- **Jet**: one water fountain in a module. Its height is controlled.
- **Pixel**: one RGBW LED that sits with a jet.
- **Strip**: two modules end to end, twenty jets in one line, about 1 m long.
- **Walker**: a person moving past the strip in the hallway.
- **Wave**: the group of jets and pixels that is up around the walker's position, with a small lead ahead and lag behind, moving with them.
- **Follow**: the strip keeping the wave under the walker as they move.
- **Control path**: everything between a sensor reading and the DMX frames the modules receive.
- **Hill**: the wave's shape. The middle jet is highest and the edge jets are lower.
- **Attract**: what the strip does when nobody is there. One slow, half-height hill rolls end to end.
- **Hold**: the hill staying under a walker who has stopped beside the strip.
- **Base colour**: the dim colour on every pixel outside a hill.
- **Scan plane**: the flat, level slice the LiDAR sweeps. Anything above or below it is invisible.
- **Track**: the running guess at one walker's position and speed. One track per walker. A track starts when the walker is first seen and ends when they leave.
- **Shadow**: the space a track cannot be seen in, because something nearer to the sensor blocks it.
