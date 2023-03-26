# Pano-Movie panoramic move creator

This is a simple Python script that can transform a PtGui panorama into a movie that zooms in- and out- and rotates through a panorama.
The script uses a json file describing the sequence of operations that is to be applied to an original PtGui .pts file.
It will then generate a number of .pts files, one for each frame in the movie.
After that, you can use PyGui's Batch Stitcher to batch-process all the .pts files.
Make sure your initial panaroma settings are what you are intending for the movie frames. E.g. the output type is taken from the original pts file.

After have generated your frames, you can use your favorite tool (e.g. MovieMaker) to combine them into a movie.
