<h1 align='center'>mrid</h1>

mrid is a library for preprocessing of 3D images, particularly medical images.

It provide interfaces for many medical image processing tools such as [SimpleElastix](https://simpleelastix.github.io/), [HD-BET](https://github.com/MIC-DKFZ/HD-BET#Installation), [SynthStrip](https://surfer.nmr.mgh.harvard.edu/docs/synthstrip/), [CTSeg](https://github.com/WCHN/CTseg). Note that those libraries are not bundled, installation instructions are included in all examples below.

### Installation

Either run

```
pip install mrid-python
```

or

```
pip install git+https://github.com/inikishev/mrid
```

### Registering images with SimpleITK-SimpleElastix

[SimpleElastix](https://simpleelastix.github.io/) is a robust tool for image registration which works really well out-of-the-box. It works on both Windows and Linux.

See [this notebook](https://github.com/inikishev/mrid/blob/main/notebooks/SimpleElastix%20tutorial.ipynb) for how to install and use it.
<img width="828" height="839" alt="image" src="https://github.com/user-attachments/assets/f083178a-82f0-411d-9d46-ffff774248e0" />

### Skullstripping MRI scans with HD-BET

[HD-BET](https://github.com/MIC-DKFZ/HD-BET) is a model that performs skullstripping of pre- and post-constrast T1, T2 and FALIR MRIs. It works on both Windows and Linux.

See [this notebook](https://github.com/inikishev/mrid/blob/main/notebooks/HD-BET%20tutorial.ipynb) for how to install and use it
<img width="828" height="840" alt="image" src="https://github.com/user-attachments/assets/ec3a8a39-0554-419f-9df9-b8e5bebc9232" />

### Skullstripping with SynthStrip

[SynthStrip](https://surfer.nmr.mgh.harvard.edu/docs/synthstrip/) is a skull-stripping tool that works with many different image types and modalities, including MRI, DWI, CT, PET, etc.

See [this notebook](https://github.com/inikishev/mrid/blob/main/notebooks/SynthStrip%20tutorial.ipynb) for how to install and use it
<img width="828" height="840" alt="image" src="https://github.com/user-attachments/assets/60fdca28-054d-4e62-93f1-6b84daa3fb9a" />

### Skullstripping and segmentation of CT images with CTseg

[CTseg](https://github.com/WCHN/CTseg) can skull-strip CT images and perform their segmentation, it also registers them to a common space (see its README). Note that it can be very slow for 512x512 series (can take few hours), but you can downsample to 256x256. If you only need to quickly skullstrip CT scans without warping them you can use SynthStrip.

TODO！！！

### Example workflow - preprocessing MRIs to BraTS format

Many [BraTS](https://www.synapse.org/brats) datasets are provided as skullstripped images in SRI24 space. See [this notebook](https://github.com/inikishev/mrid/blob/main/notebooks/BraTS%20preprocessing%20workflow.ipynb) for how to process raw scans to this format.

<img width="828" height="849" alt="image" src="https://github.com/user-attachments/assets/f1b38db3-6648-4660-a381-d68a2eb8508d" />

(T1n image looks weird because that's just how it is in the zenodo dataset)

### References
The MRIs for all images above are from https://zenodo.org/records/7213153.

> Colin Vanden Bulcke. (2022). Open-Access DICOM MRI session (1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.7213153
