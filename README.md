# Pano-Movie panoramic movie creator

This is a simple Python script that can transform a  *[PTGui](https://ptgui.com/)* panorama into a movie that zooms in- and out- and rotates through that panorama.
The script uses a json file describing the sequence of operations that is to be applied to an original PTGui .pts file.
It will then generate a number of .pts files, one for each frame in the movie.
After that, you can use PTGui's Batch Stitcher to batch-process all these .pts files.
Make sure your initial panaroma settings are what you are intending for the movie frames. E.g. the output type is taken from the original pts file.

After having generated your frames, you can use your favorite tool (e.g. MovieMaker) to combine them into a movie.

See the example json file for possible transformations.
