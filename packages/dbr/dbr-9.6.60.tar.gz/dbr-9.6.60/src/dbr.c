#include <Python.h>
#include "DynamsoftBarcodeReader.h"
#include "DynamsoftCommon.h"
#include <structmember.h>
#include <string.h>

#ifndef DEBUG
#define DEBUG 0
#endif

#if PY_MAJOR_VERSION >= 3
#ifndef IS_PY3K
#define IS_PY3K 1
#endif
#endif

struct module_state
{
    PyObject *error;
};

#if defined(IS_PY3K)
#define GETSTATE(m) ((struct module_state *)PyModule_GetState(m))
#else
#define GETSTATE(m) (&_state)
static struct module_state _state;
#endif

static PyObject * ErrorOut(PyObject *m)
{
    struct module_state *st = GETSTATE(m);
    PyErr_SetString(st->error, "something bad happened");
	Py_RETURN_NONE;
}

#define DBR_NO_MEMORY 0
#define DBR_SUCCESS 1

// #define LOG_OFF

#ifdef LOG_OFF

#define printf(MESSAGE, __VA_ARGS__)

#endif

#define DEFAULT_MEMORY_SIZE 4096

typedef struct
{
    PyObject_HEAD
    // Barcode reader handler
    void *hBarcode;
    // Callback function for video mode
    PyObject *py_cb_textResult;
    PyObject *py_cb_intermediateResult;
    PyObject *py_cb_errorCode;
    PyObject *py_UserData;
    PyObject *py_cb_uniqueTextResult;
    IntermediateResultArray * pInnerIntermediateResults;
} DynamsoftBarcodeReader;

void ToHexString(unsigned char* pSrc, int iLen, char* pDest)
{
	const char HEXCHARS[16] = { '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F' };

	int i;
	char* ptr = pDest;

	for(i = 0; i < iLen; ++i)
	{
		snprintf(ptr, 4, "%c%c ", HEXCHARS[ ( pSrc[i] & 0xF0 ) >> 4 ], HEXCHARS[ ( pSrc[i] & 0x0F ) >> 0 ]);
		ptr += 3;
	}
}

static PyObject * CreatePyRuntimeSettings(PublicRuntimeSettings pSettings)
{
    PyObject * pySettings = PyDict_New();
    if(pySettings == NULL)
    {
        Py_RETURN_NONE;
    }

    PyObject * terminatePhase               = Py_BuildValue("i", pSettings.terminatePhase);
    PyObject * terminatePhaseKey            = Py_BuildValue("s", "TerminatePhase");
    PyDict_SetItem(pySettings, terminatePhaseKey,           terminatePhase);
    Py_DECREF(terminatePhase);
    Py_DECREF(terminatePhaseKey);

    PyObject * timeout                      = Py_BuildValue("i", pSettings.timeout);
    PyObject * timeoutKey                   = Py_BuildValue("s", "Timeout");
    PyDict_SetItem(pySettings, timeoutKey, timeout);
    Py_DECREF(timeout);
    Py_DECREF(timeoutKey);

    PyObject * maxAlgorithmThreadCount      = Py_BuildValue("i", pSettings.maxAlgorithmThreadCount );
    PyObject * maxAlgorithmThreadCountKey   = Py_BuildValue("s", "MaxAlgorithmThreadCount");
    PyDict_SetItem(pySettings, maxAlgorithmThreadCountKey,  maxAlgorithmThreadCount);
    Py_DECREF(maxAlgorithmThreadCount);
    Py_DECREF(maxAlgorithmThreadCountKey);

    PyObject * expectedBarcodesCount        = Py_BuildValue("i", pSettings.expectedBarcodesCount);
    PyObject * expectedBarcodesCountKey     = Py_BuildValue("s", "ExpectedBarcodesCount");
    PyDict_SetItem(pySettings, expectedBarcodesCountKey,    expectedBarcodesCount);
    Py_DECREF(expectedBarcodesCount);
    Py_DECREF(expectedBarcodesCountKey);

    PyObject * barcodeFormatIds             = Py_BuildValue("i", pSettings.barcodeFormatIds);
    PyObject * BarcodeFormatIdsKey          = Py_BuildValue("s", "BarcodeFormatIds");
    PyDict_SetItem(pySettings, BarcodeFormatIdsKey,         barcodeFormatIds);
    Py_DECREF(barcodeFormatIds);
    Py_DECREF(BarcodeFormatIdsKey);

    PyObject * barcodeFormatIds_2           = Py_BuildValue("i", pSettings.barcodeFormatIds_2);
    PyObject * barcodeFormatIds_2Key        = Py_BuildValue("s", "BarcodeFormatIds_2");
    PyDict_SetItem(pySettings, barcodeFormatIds_2Key,       barcodeFormatIds_2);
    Py_DECREF(barcodeFormatIds_2);
    Py_DECREF(barcodeFormatIds_2Key);

    PyObject * pdfRasterDPI                 = Py_BuildValue("i", pSettings.pdfRasterDPI);
    PyObject * pdfRasterDPIKey              = Py_BuildValue("s", "PDFRasterDPI");
    PyDict_SetItem(pySettings, pdfRasterDPIKey,             pdfRasterDPI);
    Py_DECREF(pdfRasterDPI);
    Py_DECREF(pdfRasterDPIKey);

    PyObject * scaleDownThreshold           = Py_BuildValue("i", pSettings.scaleDownThreshold);
    PyObject * scaleDownThresholdKey        = Py_BuildValue("s", "ScaleDownThreshold");
    PyDict_SetItem(pySettings, scaleDownThresholdKey,       scaleDownThreshold);
    Py_DECREF(scaleDownThreshold);
    Py_DECREF(scaleDownThresholdKey);

    PyObject * binarizationModes            = PyList_New(8);
    PyObject * localizationModes            = PyList_New(8);
    PyObject * colourClusteringModes        = PyList_New(8);
    PyObject * colourConversionModes        = PyList_New(8);
    PyObject * grayscaleTransformationModes = PyList_New(8);
    PyObject * regionPredetectionModes      = PyList_New(8);
    PyObject * imagePreprocessingModes      = PyList_New(8);
    PyObject * textureDetectionModes        = PyList_New(8);
    PyObject * textFilterModes              = PyList_New(8);
    PyObject * dpmCodeReadingModes          = PyList_New(8);
    PyObject * deformationResistingModes    = PyList_New(8);
    PyObject * barcodeComplementModes       = PyList_New(8);
    PyObject * barcodeColourModes           = PyList_New(8);
    PyObject * textResultOrderModes         = PyList_New(8);
	PyObject * accompanyingTextRecognitionModes = PyList_New(8);
	PyObject * scaleUpModes = PyList_New(8);
    PyObject * deblurModes = PyList_New(10);

    for(int i = 0; i < 8; ++i)
    {
        PyObject * tempBM                   = Py_BuildValue("i", pSettings.binarizationModes[i]);
        PyList_SetItem(binarizationModes,        i, tempBM);
        PyObject * tempLM                   = Py_BuildValue("i", pSettings.localizationModes[i]);
        PyList_SetItem(localizationModes,        i, tempLM);
        PyObject * tempCCM                  = Py_BuildValue("i", pSettings.furtherModes.colourClusteringModes[i]);
        PyList_SetItem(colourClusteringModes,    i, tempCCM);
        PyObject * tempCICM                 = Py_BuildValue("i", pSettings.furtherModes.colourConversionModes[i]);
        PyList_SetItem(colourConversionModes,    i, tempCICM);
        PyObject * tempGTM                  = Py_BuildValue("i", pSettings.furtherModes.grayscaleTransformationModes[i]);
        PyList_SetItem(grayscaleTransformationModes, i, tempGTM);
        PyObject * tempRPM                  = Py_BuildValue("i", pSettings.furtherModes.regionPredetectionModes[i]);
        PyList_SetItem(regionPredetectionModes,  i, tempRPM);
        PyObject * tempIPM                  = Py_BuildValue("i", pSettings.furtherModes.imagePreprocessingModes[i]);
        PyList_SetItem(imagePreprocessingModes,  i, tempIPM);
        PyObject * tempTDM                  = Py_BuildValue("i", pSettings.furtherModes.textureDetectionModes[i]);
        PyList_SetItem(textureDetectionModes,    i, tempTDM);
        PyObject * tempTFM                  = Py_BuildValue("i", pSettings.furtherModes.textFilterModes[i]);
        PyList_SetItem(textFilterModes,          i, tempTFM);
        PyObject * tempDPMCRM               = Py_BuildValue("i", pSettings.furtherModes.dpmCodeReadingModes[i]);
        PyList_SetItem(dpmCodeReadingModes,      i, tempDPMCRM);
        PyObject * tempDRM                  = Py_BuildValue("i", pSettings.furtherModes.deformationResistingModes[i]);
        PyList_SetItem(deformationResistingModes, i, tempDRM);
        PyObject * tempBCM                  = Py_BuildValue("i", pSettings.furtherModes.barcodeComplementModes[i]);
        PyList_SetItem(barcodeComplementModes,   i, tempBCM);
        PyObject * tempBICM                 = Py_BuildValue("i", pSettings.furtherModes.barcodeColourModes[i]);
        PyList_SetItem(barcodeColourModes,       i, tempBICM);
        PyObject * tempTROM                 = Py_BuildValue("i", pSettings.textResultOrderModes[i]);
        PyList_SetItem(textResultOrderModes,     i, tempTROM);
		PyObject * tempATRM                 = Py_BuildValue("i", pSettings.furtherModes.accompanyingTextRecognitionModes[i]);
		PyList_SetItem(accompanyingTextRecognitionModes, i, tempATRM);
		PyObject * tempSUM                  = Py_BuildValue("i", pSettings.scaleUpModes[i]);
		PyList_SetItem(scaleUpModes, i, tempSUM);
    }

    PyObject * binarizationModesKey         = Py_BuildValue("s", "BinarizationModes");
    PyDict_SetItem(pySettings, binarizationModesKey,        binarizationModes);
    Py_DECREF(binarizationModes);
    Py_DECREF(binarizationModesKey);

    PyObject * localizationModesKey         = Py_BuildValue("s", "LocalizationModes");
    PyDict_SetItem(pySettings, localizationModesKey,        localizationModes);
    Py_DECREF(localizationModes);
    Py_DECREF(localizationModesKey);

    PyObject * colourClusteringModesKey     = Py_BuildValue("s", "ColourClusteringModes");
    PyDict_SetItem(pySettings, colourClusteringModesKey,    colourClusteringModes);
    Py_DECREF(colourClusteringModes);
    Py_DECREF(colourClusteringModesKey);

    PyObject * colourConversionModesKey     = Py_BuildValue("s", "ColourConversionModes");
    PyDict_SetItem(pySettings, colourConversionModesKey,    colourConversionModes);
    Py_DECREF(colourConversionModes);
    Py_DECREF(colourConversionModesKey);

    PyObject * grayscaleTransformationModesKey = Py_BuildValue("s", "GrayscaleTransformationModes");
    PyDict_SetItem(pySettings, grayscaleTransformationModesKey, grayscaleTransformationModes);
    Py_DECREF(grayscaleTransformationModes);
    Py_DECREF(grayscaleTransformationModesKey);
    
    PyObject * regionPredetectionModesKey   = Py_BuildValue("s", "RegionPredetectionModes");
    PyDict_SetItem(pySettings, regionPredetectionModesKey,  regionPredetectionModes);
    Py_DECREF(regionPredetectionModes);
    Py_DECREF(regionPredetectionModesKey);

    PyObject * imagePreprocessingModesKey   = Py_BuildValue("s", "ImagePreprocessingModes");
    PyDict_SetItem(pySettings, imagePreprocessingModesKey,  imagePreprocessingModes);
    Py_DECREF(imagePreprocessingModes);
    Py_DECREF(imagePreprocessingModesKey);

    PyObject * textureDetectionModesKey     = Py_BuildValue("s", "TextureDetectionModes");
    PyDict_SetItem(pySettings, textureDetectionModesKey,    textureDetectionModes);
    Py_DECREF(textureDetectionModes);
    Py_DECREF(textureDetectionModesKey);

    PyObject * textFilterModesKey           = Py_BuildValue("s", "TextFilterModes");
    PyDict_SetItem(pySettings, textFilterModesKey,          textFilterModes);
    Py_DECREF(textFilterModes);
    Py_DECREF(textFilterModesKey);

    PyObject * dpmCodeReadingModesKey       = Py_BuildValue("s", "DPMCodeReadingModes");
    PyDict_SetItem(pySettings, dpmCodeReadingModesKey,      dpmCodeReadingModes);
    Py_DECREF(dpmCodeReadingModes);
    Py_DECREF(dpmCodeReadingModesKey);

    PyObject * deformationResistingModesKey = Py_BuildValue("s", "DeformationResistingModes");
    PyDict_SetItem(pySettings, deformationResistingModesKey, deformationResistingModes);
    Py_DECREF(deformationResistingModes);
    Py_DECREF(deformationResistingModesKey);

    PyObject * barcodeComplementModesKey    = Py_BuildValue("s", "BarcodeComplementModes");
    PyDict_SetItem(pySettings, barcodeComplementModesKey,   barcodeComplementModes);
    Py_DECREF(barcodeComplementModes);
    Py_DECREF(barcodeComplementModesKey);

    PyObject * barcodeColourModesKey        = Py_BuildValue("s", "BarcodeColourModes");
    PyDict_SetItem(pySettings, barcodeColourModesKey,       barcodeColourModes);
    Py_DECREF(barcodeColourModes);
    Py_DECREF(barcodeColourModesKey);

    PyObject * textResultOrderModesKey      = Py_BuildValue("s", "TextResultOrderModes");
    PyDict_SetItem(pySettings, textResultOrderModesKey,     textResultOrderModes);
    Py_DECREF(textResultOrderModes);
    Py_DECREF(textResultOrderModesKey);

	PyObject * accompanyingTextRecognitionModesKey = Py_BuildValue("s", "AccompanyingTextRecognitionModes");
	PyDict_SetItem(pySettings, accompanyingTextRecognitionModesKey, accompanyingTextRecognitionModes);
	Py_DECREF(accompanyingTextRecognitionModes);
	Py_DECREF(accompanyingTextRecognitionModesKey);

	PyObject * scaleUpModesKey = Py_BuildValue("s", "ScaleUpModes");
	PyDict_SetItem(pySettings, scaleUpModesKey, scaleUpModes);
	Py_DECREF(scaleUpModes);
	Py_DECREF(scaleUpModesKey);

    for(int i = 0; i < 10; ++i)
    {
        PyObject * tempDM                  = Py_BuildValue("i", pSettings.deblurModes[i]);
		PyList_SetItem(deblurModes, i, tempDM);
    }
    PyObject * deblurModesKey = Py_BuildValue("s", "DeblurModes");
	PyDict_SetItem(pySettings, deblurModesKey, deblurModes);
	Py_DECREF(deblurModes);
	Py_DECREF(deblurModesKey);

    PyObject * textAssistedCorrectionMode   = Py_BuildValue("i", pSettings.furtherModes.textAssistedCorrectionMode);
    PyObject * textAssistedCorrectionModeKey =Py_BuildValue("s", "TextAssistedCorrectionMode");
    PyDict_SetItem(pySettings, textAssistedCorrectionModeKey, textAssistedCorrectionMode);
    Py_DECREF(textAssistedCorrectionMode);
    Py_DECREF(textAssistedCorrectionModeKey);

    PyObject * deblurLevel                  = Py_BuildValue("i", pSettings.deblurLevel);
    PyObject * deblurLevelKey               = Py_BuildValue("s", "DeblurLevel");
    PyDict_SetItem(pySettings, deblurLevelKey,              deblurLevel);
    Py_DECREF(deblurLevel);
    Py_DECREF(deblurLevelKey);

    PyObject * intermediateResultTypes      = Py_BuildValue("i", pSettings.intermediateResultTypes);
    PyObject * intermediateResultTypesKey   = Py_BuildValue("s", "IntermediateResultTypes");
    PyDict_SetItem(pySettings, intermediateResultTypesKey,  intermediateResultTypes);
    Py_DECREF(intermediateResultTypes);
    Py_DECREF(intermediateResultTypesKey);

    PyObject * intermediateResultSavingMode = Py_BuildValue("i", pSettings.intermediateResultSavingMode);
    PyObject * intermediateResultSavingModeKey = Py_BuildValue("s", "IntermediateResultSavingMode");
    PyDict_SetItem(pySettings, intermediateResultSavingModeKey, intermediateResultSavingMode);
    Py_DECREF(intermediateResultSavingMode);
    Py_DECREF(intermediateResultSavingModeKey);

    PyObject * resultCoordinateType         = Py_BuildValue("i", pSettings.resultCoordinateType);
    PyObject * resultCoordinateTypeKey      = Py_BuildValue("s", "ResultCoordinateType");
    PyDict_SetItem(pySettings, resultCoordinateTypeKey,     resultCoordinateType);
    Py_DECREF(resultCoordinateType);
    Py_DECREF(resultCoordinateTypeKey);

    PyObject * returnBarcodeZoneClarity     = Py_BuildValue("i", pSettings.returnBarcodeZoneClarity);
    PyObject * returnBarcodeZoneClarityKey  = Py_BuildValue("s", "ReturnBarcodeZoneClarity");
    PyDict_SetItem(pySettings, returnBarcodeZoneClarityKey, returnBarcodeZoneClarity);
    Py_DECREF(returnBarcodeZoneClarity);
    Py_DECREF(returnBarcodeZoneClarityKey);

    PyObject * regionTop                    = Py_BuildValue("i", pSettings.region.regionTop);
    PyObject * regionTopKey                 = Py_BuildValue("s", "RegionTop");
    PyDict_SetItem(pySettings, regionTopKey,                regionTop);
    Py_DECREF(regionTop);
    Py_DECREF(regionTopKey);

    PyObject * regionBottom                 = Py_BuildValue("i", pSettings.region.regionBottom);
    PyObject * regionBottomKey              = Py_BuildValue("s", "RegionBottom");
    PyDict_SetItem(pySettings, regionBottomKey,             regionBottom);
    Py_DECREF(regionBottom);
    Py_DECREF(regionBottomKey);

    PyObject * regionLeft                   = Py_BuildValue("i", pSettings.region.regionLeft);
    PyObject * regionLeftKey                = Py_BuildValue("s", "RegionLeft");
    PyDict_SetItem(pySettings, regionLeftKey,               regionLeft);
    Py_DECREF(regionLeft);
    Py_DECREF(regionLeftKey);

    PyObject * regionRight                  = Py_BuildValue("i", pSettings.region.regionRight);
    PyObject * regionRightKey               = Py_BuildValue("s", "RegionRight");
    PyDict_SetItem(pySettings, regionRightKey,              regionRight);
    Py_DECREF(regionRight);
    Py_DECREF(regionRightKey);

    PyObject * regionMeasuredByPercentage   = Py_BuildValue("i", pSettings.region.regionMeasuredByPercentage);
    PyObject * regionMeasuredByPercentageKey =Py_BuildValue("s", "RegionMeasuredByPercentage");
    PyDict_SetItem(pySettings, regionMeasuredByPercentageKey, regionMeasuredByPercentage);
    Py_DECREF(regionMeasuredByPercentage);
    Py_DECREF(regionMeasuredByPercentageKey);

    PyObject * minBarcodeTextLength         = Py_BuildValue("i", pSettings.minBarcodeTextLength);
    PyObject * minBarcodeTextLengthKey      = Py_BuildValue("s", "MinBarcodeTextLength");
    PyDict_SetItem(pySettings, minBarcodeTextLengthKey,     minBarcodeTextLength);
    Py_DECREF(minBarcodeTextLength);
    Py_DECREF(minBarcodeTextLengthKey);

    PyObject * minResultConfidence          = Py_BuildValue("i", pSettings.minResultConfidence);
    PyObject * minResultConfidenceKey       = Py_BuildValue("s", "MinResultConfidence");
    PyDict_SetItem(pySettings, minResultConfidenceKey,      minResultConfidence);
    Py_DECREF(minResultConfidence);
    Py_DECREF(minResultConfidenceKey);

    PyObject * pdfReadingMode   = Py_BuildValue("i", pSettings.pdfReadingMode);
    PyObject * pdfReadingModeKey =Py_BuildValue("s", "PDFReadingMode");
    PyDict_SetItem(pySettings, pdfReadingModeKey, pdfReadingMode);
    Py_DECREF(pdfReadingMode);
    Py_DECREF(pdfReadingModeKey);

    PyObject * barcodeZoneMinDistanceToImageBorders   = Py_BuildValue("i", pSettings.barcodeZoneMinDistanceToImageBorders);
    PyObject * barcodeZoneMinDistanceToImageBordersKey =Py_BuildValue("s", "BarcodeZoneMinDistanceToImageBorders");
    PyDict_SetItem(pySettings, barcodeZoneMinDistanceToImageBordersKey, barcodeZoneMinDistanceToImageBorders);
    Py_DECREF(barcodeZoneMinDistanceToImageBorders);
    Py_DECREF(barcodeZoneMinDistanceToImageBordersKey);

    return pySettings;
}

PublicRuntimeSettings CreateCRuntimeSettings(PyObject *o)
{
    PublicRuntimeSettings pSettings;
    pSettings.terminatePhase            = (TerminatePhase)(PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "TerminatePhase"))));
    pSettings.timeout                   = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "Timeout")));
    pSettings.maxAlgorithmThreadCount   = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "MaxAlgorithmThreadCount")));
    pSettings.expectedBarcodesCount     = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "ExpectedBarcodesCount")));
    pSettings.barcodeFormatIds          = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "BarcodeFormatIds")));
    pSettings.barcodeFormatIds_2        = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "BarcodeFormatIds_2")));
    pSettings.pdfRasterDPI              = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "PDFRasterDPI")));
    pSettings.scaleDownThreshold        = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "ScaleDownThreshold")));

    PyObject * binarizationModes            = PyDict_GetItem(o, Py_BuildValue("s", "BinarizationModes"));
    PyObject * localizationModes            = PyDict_GetItem(o, Py_BuildValue("s", "LocalizationModes"));
    PyObject * colourClusteringModes        = PyDict_GetItem(o, Py_BuildValue("s", "ColourClusteringModes"));
    PyObject * colourConversionModes        = PyDict_GetItem(o, Py_BuildValue("s", "ColourConversionModes"));
    PyObject * grayscaleTransformationModes = PyDict_GetItem(o, Py_BuildValue("s", "GrayscaleTransformationModes"));
    PyObject * regionPredetectionModes      = PyDict_GetItem(o, Py_BuildValue("s", "RegionPredetectionModes"));
    PyObject * imagePreprocessingModes      = PyDict_GetItem(o, Py_BuildValue("s", "ImagePreprocessingModes"));
    PyObject * textureDetectionModes        = PyDict_GetItem(o, Py_BuildValue("s", "TextureDetectionModes"));
    PyObject * textFilterModes              = PyDict_GetItem(o, Py_BuildValue("s", "TextFilterModes"));
    PyObject * dpmCodeReadingModes          = PyDict_GetItem(o, Py_BuildValue("s", "DPMCodeReadingModes"));
    PyObject * deformationResistingModes    = PyDict_GetItem(o, Py_BuildValue("s", "DeformationResistingModes"));
    PyObject * barcodeComplementModes       = PyDict_GetItem(o, Py_BuildValue("s", "BarcodeComplementModes"));
    PyObject * barcodeColourModes           = PyDict_GetItem(o, Py_BuildValue("s", "BarcodeColourModes"));
    PyObject * textResultOrderModes         = PyDict_GetItem(o, Py_BuildValue("s", "TextResultOrderModes"));
	PyObject * accompanyingTextRecognitionModes = PyDict_GetItem(o, Py_BuildValue("s", "AccompanyingTextRecognitionModes"));
	PyObject * scaleUpModes					= PyDict_GetItem(o, Py_BuildValue("s", "ScaleUpModes"));
	PyObject * deblurModes					= PyDict_GetItem(o, Py_BuildValue("s", "DeblurModes"));

    for(int i = 0; i < 8; ++i)
    {
        pSettings.binarizationModes[i]                          = (BinarizationMode)(PyLong_AsLong(PyList_GetItem(binarizationModes, i)));
        pSettings.localizationModes[i]                          = (LocalizationMode)(PyLong_AsLong(PyList_GetItem(localizationModes, i)));
        pSettings.furtherModes.colourClusteringModes[i]         = (ColourClusteringMode)(PyLong_AsLong(PyList_GetItem(colourClusteringModes, i)));
        pSettings.furtherModes.colourConversionModes[i]         = (ColourConversionMode)(PyLong_AsLong(PyList_GetItem(colourConversionModes, i)));
        pSettings.furtherModes.grayscaleTransformationModes[i]  = (GrayscaleTransformationMode)(PyLong_AsLong(PyList_GetItem(grayscaleTransformationModes, i)));
        pSettings.furtherModes.regionPredetectionModes[i]       = (RegionPredetectionMode)(PyLong_AsLong(PyList_GetItem(regionPredetectionModes, i)));
        pSettings.furtherModes.imagePreprocessingModes[i]       = (ImagePreprocessingMode)(PyLong_AsLong(PyList_GetItem(imagePreprocessingModes, i)));
        pSettings.furtherModes.textureDetectionModes[i]         = (TextureDetectionMode)(PyLong_AsLong(PyList_GetItem(textureDetectionModes, i)));
        pSettings.furtherModes.textFilterModes[i]               = (TextFilterMode)(PyLong_AsLong(PyList_GetItem(textFilterModes, i)));
        pSettings.furtherModes.dpmCodeReadingModes[i]           = (DPMCodeReadingMode)(PyLong_AsLong(PyList_GetItem(dpmCodeReadingModes, i)));
        pSettings.furtherModes.deformationResistingModes[i]     = (DeformationResistingMode)(PyLong_AsLong(PyList_GetItem(deformationResistingModes, i)));
        pSettings.furtherModes.barcodeComplementModes[i]        = (BarcodeComplementMode)(PyLong_AsLong(PyList_GetItem(barcodeComplementModes, i)));
        pSettings.furtherModes.barcodeColourModes[i]            = (BarcodeColourMode)(PyLong_AsLong(PyList_GetItem(barcodeColourModes, i)));
        pSettings.textResultOrderModes[i]                       = (TextResultOrderMode)(PyLong_AsLong(PyList_GetItem(textResultOrderModes, i)));
		pSettings.furtherModes.accompanyingTextRecognitionModes[i] = (AccompanyingTextRecognitionMode)(PyLong_AsLong(PyList_GetItem(accompanyingTextRecognitionModes, i)));
		pSettings.scaleUpModes[i]								= (ScaleUpMode)(PyLong_AsLong(PyList_GetItem(scaleUpModes, i)));
	}

    for(int i = 0; i < 10; ++i)
    {
        pSettings.deblurModes[i]								= (DeblurMode)(PyLong_AsLong(PyList_GetItem(deblurModes, i)));
    }

    pSettings.furtherModes.textAssistedCorrectionMode               = (TextAssistedCorrectionMode)(PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "TextAssistedCorrectionMode"))));
    pSettings.deblurLevel                                           = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "DeblurLevel")));
    pSettings.intermediateResultTypes                               = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "IntermediateResultTypes")));
    pSettings.intermediateResultSavingMode                          = (IntermediateResultSavingMode)(PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "IntermediateResultSavingMode"))));
    pSettings.resultCoordinateType                                  = (ResultCoordinateType)(PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "ResultCoordinateType"))));
    pSettings.returnBarcodeZoneClarity                              = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "ReturnBarcodeZoneClarity")));
    pSettings.region.regionTop                                      = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "RegionTop")));
    pSettings.region.regionBottom                                   = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "RegionBottom")));
    pSettings.region.regionLeft                                     = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "RegionLeft")));
    pSettings.region.regionRight                                    = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "RegionRight")));
    pSettings.region.regionMeasuredByPercentage                     = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "RegionMeasuredByPercentage")));
    pSettings.minBarcodeTextLength                                  = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "MinBarcodeTextLength")));
    pSettings.minResultConfidence                                   = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "MinResultConfidence")));
    pSettings.pdfReadingMode                                        = (PDFReadingMode)(PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "PDFReadingMode"))));
    pSettings.deblurLevel                                           = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "DeblurLevel")));
    pSettings.barcodeZoneMinDistanceToImageBorders                  = PyLong_AsLong(PyDict_GetItem(o, Py_BuildValue("s", "BarcodeZoneMinDistanceToImageBorders")));

    return pSettings;
}

static PyObject * CreatePySamplingImageData(SamplingImageData samplingImage)
{
    //create SamplingImage
    PyObject * pySamplingImage = PyDict_New();
    if(pySamplingImage == NULL)
    { 
        Py_RETURN_NONE;
    }

    if(samplingImage.bytes != NULL)
    {
        PyObject * pySamplingImageBytes     = PyByteArray_FromStringAndSize(samplingImage.bytes, samplingImage.width * samplingImage.height);
        PyObject * pySamplingImageBytesKey  = Py_BuildValue("s", "Bytes");
        PyDict_SetItem(pySamplingImage, pySamplingImageBytesKey, pySamplingImageBytes);
        Py_DECREF(pySamplingImageBytes);
        Py_DECREF(pySamplingImageBytesKey);
    }
    else
    {
        //PyObject * pySamplingImageBytes     = Py_None;
        PyObject * pySamplingImageBytesKey  = Py_BuildValue("s", "Bytes");
        PyDict_SetItem(pySamplingImage, pySamplingImageBytesKey, Py_None);
       // Py_DECREF(pySamplingImageBytes);
        Py_DECREF(pySamplingImageBytesKey);
    }

    PyObject * pySamplingImageWidth     = Py_BuildValue("i", samplingImage.width);
    PyObject * pySamplingImageWidthKey  = Py_BuildValue("s", "Width");
    PyDict_SetItem(pySamplingImage, pySamplingImageWidthKey, pySamplingImageWidth);
    Py_DECREF(pySamplingImageWidth);
    Py_DECREF(pySamplingImageWidthKey);

    PyObject * pySamplingImageHeight    = Py_BuildValue("i", samplingImage.height);
    PyObject * pySamplingImageHeightKey = Py_BuildValue("s", "Height");
    PyDict_SetItem(pySamplingImage, pySamplingImageHeightKey, pySamplingImageHeight);
    Py_DECREF(pySamplingImageHeight);
    Py_DECREF(pySamplingImageHeightKey);

    return pySamplingImage;
}

static PyObject * CreatePyDetailedResult(void * pResult, int format)
{
    PyObject * pyResult = PyDict_New();
    if(pyResult == NULL)
    {
        Py_RETURN_NONE;
    }

    if((format & BF_ONED) != 0)
    {
        PyObject * pyModuleSize         = Py_BuildValue("i", ((OneDCodeDetails *)pResult)->moduleSize);
        PyObject * pyModuleSizeKey      = Py_BuildValue("s", "ModuleSize");
        PyDict_SetItem(pyResult, pyModuleSizeKey, pyModuleSize);
        Py_DECREF(pyModuleSize);
        Py_DECREF(pyModuleSizeKey);

        if(((OneDCodeDetails *)pResult)->startCharsBytes != NULL)
        {
            PyObject * pyStartCharsBytes    = PyByteArray_FromStringAndSize(((OneDCodeDetails *)pResult)->startCharsBytes, ((OneDCodeDetails *)pResult)->startCharsBytesLength);
            PyObject * pyStartCharsBytesKey = Py_BuildValue("s", "StartCharsBytes");
            PyDict_SetItem(pyResult, pyStartCharsBytesKey, pyStartCharsBytes);
            Py_DECREF(pyStartCharsBytes);
            Py_DECREF(pyStartCharsBytesKey);

        }
        else
        {
            //PyObject * pyStartCharsBytes    = Py_BuildValue("o", NULL);
            PyObject * pyStartCharsBytesKey = Py_BuildValue("s", "StartCharsBytes");
            PyDict_SetItem(pyResult, pyStartCharsBytesKey, Py_None);
            //Py_DECREF(pyStartCharsBytes);
            Py_DECREF(pyStartCharsBytesKey);
        }

        if(((OneDCodeDetails *)pResult)->stopCharsBytes != NULL)
        {
            PyObject * pyStopCharsBytes     = PyByteArray_FromStringAndSize(((OneDCodeDetails *)pResult)->stopCharsBytes, ((OneDCodeDetails *)pResult)->stopCharsBytesLength);
            PyObject * pyStopCharsBytesKey  = Py_BuildValue("s", "StopCharsBytes");
            PyDict_SetItem(pyResult, pyStopCharsBytesKey, pyStopCharsBytes);
            Py_DECREF(pyStopCharsBytes);
            Py_DECREF(pyStopCharsBytesKey);
        }
        else
        {
            //PyObject * pyStopCharsBytes     = Py_BuildValue("o", NULL);
            PyObject * pyStopCharsBytesKey  = Py_BuildValue("s", "StopCharsBytes");
            PyDict_SetItem(pyResult, pyStopCharsBytesKey, Py_None);
            //Py_DECREF(pyStopCharsBytes);
            Py_DECREF(pyStopCharsBytesKey);
        }
        

        if(((OneDCodeDetails *)pResult)->checkDigitBytes != NULL)
        {
            PyObject * pyCheckDigitBytes    = PyByteArray_FromStringAndSize(((OneDCodeDetails *)pResult)->checkDigitBytes, ((OneDCodeDetails *)pResult)->checkDigitBytesLength);
            PyObject * pyCheckDigitBytesKey = Py_BuildValue("s", "CheckDigitBytes");
            PyDict_SetItem(pyResult, pyCheckDigitBytesKey, pyCheckDigitBytes);
            Py_DECREF(pyCheckDigitBytes);
            Py_DECREF(pyCheckDigitBytesKey);
        }
        else
        {
            //PyObject * pyCheckDigitBytes    = Py_BuildValue("o", NULL);
            PyObject * pyCheckDigitBytesKey = Py_BuildValue("s", "CheckDigitBytes");
            PyDict_SetItem(pyResult, pyCheckDigitBytesKey, Py_None);
            //Py_DECREF(pyCheckDigitBytes);
            Py_DECREF(pyCheckDigitBytesKey);
        }

        PyObject * pyStartPatternRange = PyList_New(2);
        for(int j = 0; j < 2; ++j)
        {
            PyObject * temp = Py_BuildValue("d",((OneDCodeDetails *)pResult)->startPatternRange[j]);
            PyList_SetItem(pyStartPatternRange, j, temp);
        }
        PyObject * pyStartPatternRangeKey   = Py_BuildValue("s", "StartPatternRange");
        PyDict_SetItem(pyResult, pyStartPatternRangeKey, pyStartPatternRange);
        Py_DECREF(pyStartPatternRange);
        Py_DECREF(pyStartPatternRangeKey);

        PyObject * pyMiddlePatternRange = PyList_New(2);
        for(int j = 0; j < 2; ++j)
        {
            PyObject * temp = Py_BuildValue("d",((OneDCodeDetails *)pResult)->middlePatternRange[j]);
            PyList_SetItem(pyMiddlePatternRange, j, temp);
        }
        PyObject * pyMiddlePatternRangeKey   = Py_BuildValue("s", "MiddlePatternRange");
        PyDict_SetItem(pyResult, pyMiddlePatternRangeKey, pyMiddlePatternRange);
        Py_DECREF(pyMiddlePatternRange);
        Py_DECREF(pyMiddlePatternRangeKey);

        PyObject * pyEndPatternRange = PyList_New(2);
        for(int j = 0; j < 2; ++j)
        {
            PyObject * temp = Py_BuildValue("d",((OneDCodeDetails *)pResult)->endPatternRange[j]);
            PyList_SetItem(pyEndPatternRange, j, temp);
        }
        PyObject * pyEndPatternRangeKey   = Py_BuildValue("s", "EndPatternRange");
        PyDict_SetItem(pyResult, pyEndPatternRangeKey, pyEndPatternRange);
        Py_DECREF(pyEndPatternRange);
        Py_DECREF(pyEndPatternRangeKey);
    }
    else if(format == BF_QR_CODE)
    {
        PyObject * pyModuleSize         = Py_BuildValue("i", ((QRCodeDetails *)pResult)->moduleSize);
        PyObject * pyModuleSizeKey      = Py_BuildValue("s", "ModuleSize");
        PyDict_SetItem(pyResult, pyModuleSizeKey, pyModuleSize);
        Py_DECREF(pyModuleSize);
        Py_DECREF(pyModuleSizeKey);

        PyObject * pyRows               = Py_BuildValue("i", ((QRCodeDetails *)pResult)->rows);
        PyObject * pyRowsKey            = Py_BuildValue("s", "Rows");
        PyDict_SetItem(pyResult, pyRowsKey, pyRows);
        Py_DECREF(pyRows);
        Py_DECREF(pyRowsKey);

        PyObject * pyColumns            = Py_BuildValue("i", ((QRCodeDetails *)pResult)->columns);
        PyObject * pyColumnsKey         = Py_BuildValue("s", "Columns");
        PyDict_SetItem(pyResult, pyColumnsKey, pyColumns);
        Py_DECREF(pyColumns);
        Py_DECREF(pyColumnsKey);
        
        PyObject * pyErrorCorrectionLevel    = Py_BuildValue("i", ((QRCodeDetails *)pResult)->errorCorrectionLevel);
        PyObject * pyErrorCorrectionLevelKey = Py_BuildValue("s", "ErrorCorrectionLevel");
        PyDict_SetItem(pyResult, pyErrorCorrectionLevelKey, pyErrorCorrectionLevel);
        Py_DECREF(pyErrorCorrectionLevel);
        Py_DECREF(pyErrorCorrectionLevelKey);
        
        PyObject * pyVersion            = Py_BuildValue("i", ((QRCodeDetails *)pResult)->version);
        PyObject * pyVersionKey         = Py_BuildValue("s", "Version");
        PyDict_SetItem(pyResult, pyVersionKey, pyVersion);
        Py_DECREF(pyVersion);
        Py_DECREF(pyVersionKey);

        PyObject * pyModel              = Py_BuildValue("i", ((QRCodeDetails *)pResult)->model);
        PyObject * pyModelKey           = Py_BuildValue("s", "Model");
        PyDict_SetItem(pyResult, pyModelKey, pyModel);
        Py_DECREF(pyModel);
        Py_DECREF(pyModelKey);

        PyObject * pyMode              = Py_BuildValue("i", ((QRCodeDetails *)pResult)->mode);
        PyObject * pyModeKey           = Py_BuildValue("s", "Mode");
        PyDict_SetItem(pyResult, pyModeKey, pyMode);
        Py_DECREF(pyMode);
        Py_DECREF(pyModeKey);

        PyObject * pyPage              = Py_BuildValue("i", ((QRCodeDetails *)pResult)->page);
        PyObject * pyPageKey           = Py_BuildValue("s", "Page");
        PyDict_SetItem(pyResult, pyPageKey, pyPage);
        Py_DECREF(pyPage);
        Py_DECREF(pyPageKey);

        PyObject * pyTotalPage              = Py_BuildValue("i", ((QRCodeDetails *)pResult)->totalPage);
        PyObject * pyTotalPageKey           = Py_BuildValue("s", "TotalPage");
        PyDict_SetItem(pyResult, pyTotalPageKey, pyTotalPage);
        Py_DECREF(pyTotalPage);
        Py_DECREF(pyTotalPageKey);

        PyObject * pyParityData              = Py_BuildValue("i", ((QRCodeDetails *)pResult)->parityData);
        PyObject * pyParityDataKey           = Py_BuildValue("s", "ParityData");
        PyDict_SetItem(pyResult, pyParityDataKey, pyParityData);
        Py_DECREF(pyParityData);
        Py_DECREF(pyParityDataKey);

    }
    else if(format == BF_DATAMATRIX)
    {
        PyObject * pyModuleSize         = Py_BuildValue("i", ((DataMatrixDetails *)pResult)->moduleSize);
        PyObject * pyModuleSizeKey      = Py_BuildValue("s", "ModuleSize");
        PyDict_SetItem(pyResult, pyModuleSizeKey, pyModuleSize);
        Py_DECREF(pyModuleSize);
        Py_DECREF(pyModuleSizeKey);

        PyObject * pyRows               = Py_BuildValue("i", ((DataMatrixDetails *)pResult)->rows);
        PyObject * pyRowsKey            = Py_BuildValue("s", "Rows");
        PyDict_SetItem(pyResult, pyRowsKey, pyRows);
        Py_DECREF(pyRows);
        Py_DECREF(pyRowsKey);

        PyObject * pyColumns            = Py_BuildValue("i", ((DataMatrixDetails *)pResult)->columns);
        PyObject * pyColumnsKey         = Py_BuildValue("s", "Columns");
        PyDict_SetItem(pyResult, pyColumnsKey, pyColumns); 
        Py_DECREF(pyColumns);
        Py_DECREF(pyColumnsKey);

        PyObject * pyDataRegionRows     = Py_BuildValue("i", ((DataMatrixDetails *)pResult)->dataRegionRows);
        PyObject * pyDataRegionRowsKey  = Py_BuildValue("s", "DataRegionRows");
        PyDict_SetItem(pyResult, pyDataRegionRowsKey, pyDataRegionRows);
        Py_DECREF(pyDataRegionRows);
        Py_DECREF(pyDataRegionRowsKey);

        PyObject * pyDataRegionColumns  = Py_BuildValue("i", ((DataMatrixDetails *)pResult)->dataRegionColumns);
        PyObject * pyDataRegionColumnsKey = Py_BuildValue("s", "DataRegionColumns");
        PyDict_SetItem(pyResult, pyDataRegionColumnsKey, pyDataRegionColumns);
        Py_DECREF(pyDataRegionColumns);
        Py_DECREF(pyDataRegionColumnsKey);

        PyObject * pyDataRegionNumber   = Py_BuildValue("i", ((DataMatrixDetails *)pResult)->dataRegionNumber);
        PyObject * pyDataRegionNumberKey= Py_BuildValue("s", "DataRegionNumber");
        PyDict_SetItem(pyResult, pyDataRegionNumberKey, pyDataRegionNumber); 
        Py_DECREF(pyDataRegionNumber);
        Py_DECREF(pyDataRegionNumberKey);
    }
    else if(format == BF_PDF417)
    {
        PyObject * pyModuleSize         = Py_BuildValue("i", ((PDF417Details *)pResult)->moduleSize);
        PyObject * pyModuleSizeKey      = Py_BuildValue("s", "ModuleSize");
        PyDict_SetItem(pyResult, pyModuleSizeKey, pyModuleSize);
        Py_DECREF(pyModuleSize);
        Py_DECREF(pyModuleSizeKey);

        PyObject * pyRows               = Py_BuildValue("i", ((PDF417Details *)pResult)->rows);
        PyObject * pyRowsKey            = Py_BuildValue("s", "Rows");
        PyDict_SetItem(pyResult, pyRowsKey, pyRows);
        Py_DECREF(pyRows);
        Py_DECREF(pyRowsKey);

        PyObject * pyColumns            = Py_BuildValue("i", ((PDF417Details *)pResult)->columns);
        PyObject * pyColumnsKey         = Py_BuildValue("s", "Columns");
        PyDict_SetItem(pyResult, pyColumnsKey, pyColumns);
        Py_DECREF(pyColumns);
        Py_DECREF(pyColumnsKey);
        
        PyObject * pyErrorCorrectionLevel    = Py_BuildValue("i", ((PDF417Details *)pResult)->errorCorrectionLevel);
        PyObject * pyErrorCorrectionLevelKey = Py_BuildValue("s", "ErrorCorrectionLevel");
        PyDict_SetItem(pyResult, pyErrorCorrectionLevelKey, pyErrorCorrectionLevel);
        Py_DECREF(pyErrorCorrectionLevel);
        Py_DECREF(pyErrorCorrectionLevelKey);

        PyObject * pyLeftRowIndicatorExists   = Py_BuildValue("i", ((PDF417Details *)pResult)->hasLeftRowIndicator);
        PyObject * pyLeftRowIndicatorExistsKey = Py_BuildValue("s", "HasLeftRowIndicator");
        PyDict_SetItem(pyResult, pyLeftRowIndicatorExistsKey, pyLeftRowIndicatorExists);
        Py_DECREF(pyLeftRowIndicatorExists);
        Py_DECREF(pyLeftRowIndicatorExistsKey);

        PyObject * pyRightRowIndicatorExists   = Py_BuildValue("i", ((PDF417Details *)pResult)->hasRightRowIndicator);
        PyObject * pyRightRowIndicatorExistsKey = Py_BuildValue("s", "HasRightRowIndicator");
        PyDict_SetItem(pyResult, pyRightRowIndicatorExistsKey, pyRightRowIndicatorExists);
        Py_DECREF(pyRightRowIndicatorExists);
        Py_DECREF(pyRightRowIndicatorExistsKey);
    }
    else if(format == BF_AZTEC)
    {
        PyObject * pyModuleSize         = Py_BuildValue("i", ((AztecDetails *)pResult)->moduleSize);
        PyObject * pyModuleSizeKey      = Py_BuildValue("s", "ModuleSize");
        PyDict_SetItem(pyResult, pyModuleSizeKey, pyModuleSize);
        Py_DECREF(pyModuleSize);
        Py_DECREF(pyModuleSizeKey);

        PyObject * pyRows               = Py_BuildValue("i", ((AztecDetails *)pResult)->rows);
        PyObject * pyRowsKey            = Py_BuildValue("s", "Rows");
        PyDict_SetItem(pyResult, pyRowsKey, pyRows);
        Py_DECREF(pyRows);
        Py_DECREF(pyRowsKey);

        PyObject * pyColumns            = Py_BuildValue("i", ((AztecDetails *)pResult)->columns);
        PyObject * pyColumnsKey         = Py_BuildValue("s", "Columns");
        PyDict_SetItem(pyResult, pyColumnsKey, pyColumns); 
        Py_DECREF(pyColumns);
        Py_DECREF(pyColumnsKey);

        PyObject * pyLayerNumber        = Py_BuildValue("i", ((AztecDetails *)pResult)->layerNumber);
        PyObject * pyLayerNumberKey     = Py_BuildValue("s", "LayerNumber");
        PyDict_SetItem(pyResult, pyLayerNumberKey, pyLayerNumber);
        Py_DECREF(pyLayerNumber);
        Py_DECREF(pyLayerNumberKey);
    }
    return pyResult;
}

static PyObject * CreatePyLocalizationResult(LocalizationResult * pResult)
{
    PyObject * pyResult = PyDict_New();
    if(pyResult == NULL)
    {  
        Py_RETURN_NONE;
    }

    PyObject * pyTerminatePhase         = Py_BuildValue("i", pResult->terminatePhase);
    PyObject * pyTerminatePhaseKey      = Py_BuildValue("s", "TerminatePhase");
    PyDict_SetItem(pyResult, pyTerminatePhaseKey, pyTerminatePhase);
    Py_DECREF(pyTerminatePhase);
    Py_DECREF(pyTerminatePhaseKey);

    PyObject * pyBarcodeFormat          = Py_BuildValue("i", pResult->barcodeFormat);
    PyObject * pyBarcodeFormatKey       = Py_BuildValue("s", "BarcodeFormat");
    PyDict_SetItem(pyResult, pyBarcodeFormatKey, pyBarcodeFormat);
    Py_DECREF(pyBarcodeFormat);
    Py_DECREF(pyBarcodeFormatKey);

    if(pResult->barcodeFormatString != NULL)
    {
        PyObject * pyBarcodeFormatString     = Py_BuildValue("s", pResult->barcodeFormatString);
        PyObject * pyBarcodeFormatStringKey = Py_BuildValue("s", "BarcodeFormatString");
        PyDict_SetItem(pyResult, pyBarcodeFormatStringKey, pyBarcodeFormatString);
        Py_DECREF(pyBarcodeFormatString);
        Py_DECREF(pyBarcodeFormatStringKey);
    }
    else
    {
       // PyObject *pyBarcodeFormatString     = Py_None;
        PyObject * pyBarcodeFormatStringKey = Py_BuildValue("s", "BarcodeFormatString");
        PyDict_SetItem(pyResult, pyBarcodeFormatStringKey, Py_None);
       // Py_DECREF(pyBarcodeFormatString);
        Py_DECREF(pyBarcodeFormatStringKey);
    }
    

    PyObject * pyBarcodeFormat_2        = Py_BuildValue("i", pResult->barcodeFormat_2);
    PyObject * pyBarcodeFormatKey_2     = Py_BuildValue("s", "BarcodeFormat_2");
    PyDict_SetItem(pyResult, pyBarcodeFormatKey_2, pyBarcodeFormat_2);
    Py_DECREF(pyBarcodeFormat_2);
    Py_DECREF(pyBarcodeFormatKey_2);

    if(pResult->barcodeFormatString_2 != NULL)
    {
        PyObject * pyBarcodeFormatString_2    = Py_BuildValue("s", pResult->barcodeFormatString_2);
        PyObject * pyBarcodeFormatStringKey_2 = Py_BuildValue("s", "BarcodeFormatString_2");
        PyDict_SetItem(pyResult, pyBarcodeFormatStringKey_2, pyBarcodeFormatString_2);
        Py_DECREF(pyBarcodeFormatString_2);
        Py_DECREF(pyBarcodeFormatStringKey_2);
    }
    else
    {
       // PyObject * pyBarcodeFormatString_2    = Py_None;
        PyObject * pyBarcodeFormatStringKey_2 = Py_BuildValue("s", "BarcodeFormatString_2");
        PyDict_SetItem(pyResult, pyBarcodeFormatStringKey_2, Py_None);
       // Py_DECREF(pyBarcodeFormatString_2);
        Py_DECREF(pyBarcodeFormatStringKey_2);
    }
    

    PyObject * pyX1                     = Py_BuildValue("i", pResult->x1);
    PyObject * pyX1Key                  = Py_BuildValue("s", "X1");
    PyDict_SetItem(pyResult, pyX1Key, pyX1);
    Py_DECREF(pyX1);
    Py_DECREF(pyX1Key);

    PyObject * pyY1                     = Py_BuildValue("i", pResult->y1);
    PyObject * pyY1Key                  = Py_BuildValue("s", "Y1");
    PyDict_SetItem(pyResult, pyY1Key, pyY1);
    Py_DECREF(pyY1);
    Py_DECREF(pyY1Key);

    PyObject * pyX2                     = Py_BuildValue("i", pResult->x2);
    PyObject * pyX2Key                  = Py_BuildValue("s", "X2");
    PyDict_SetItem(pyResult, pyX2Key, pyX2);
    Py_DECREF(pyX2);
    Py_DECREF(pyX2Key);

    PyObject * pyY2                     = Py_BuildValue("i", pResult->y2);
    PyObject * pyY2Key                  = Py_BuildValue("s", "Y2");
    PyDict_SetItem(pyResult, pyY2Key, pyY2);
    Py_DECREF(pyY2);
    Py_DECREF(pyY2Key);

    PyObject * pyX3                     = Py_BuildValue("i", pResult->x3);
    PyObject * pyX3Key                  = Py_BuildValue("s", "X3");
    PyDict_SetItem(pyResult, pyX3Key, pyX3);
    Py_DECREF(pyX3);
    Py_DECREF(pyX3Key);

    PyObject * pyY3                     = Py_BuildValue("i", pResult->y3);
    PyObject * pyY3Key                  = Py_BuildValue("s", "Y3");
    PyDict_SetItem(pyResult, pyY3Key, pyY3);
    Py_DECREF(pyY3);
    Py_DECREF(pyY3Key);

    PyObject * pyX4                     = Py_BuildValue("i", pResult->x4);
    PyObject * pyX4Key                  = Py_BuildValue("s", "X4");
    PyDict_SetItem(pyResult, pyX4Key, pyX4);
    Py_DECREF(pyX4);
    Py_DECREF(pyX4Key);

    PyObject * pyY4                     = Py_BuildValue("i", pResult->y4);
    PyObject * pyY4Key                  = Py_BuildValue("s", "Y4");
    PyDict_SetItem(pyResult, pyY4Key, pyY4);
    Py_DECREF(pyY4);
    Py_DECREF(pyY4Key);

    PyObject * pyAngle                  = Py_BuildValue("i", pResult->angle);
    PyObject * pyAngleKey               = Py_BuildValue("s", "Angle");
    PyDict_SetItem(pyResult, pyAngleKey, pyAngle);
    Py_DECREF(pyAngle);
    Py_DECREF(pyAngleKey);

    PyObject * pyModuleSize             = Py_BuildValue("i", pResult->moduleSize);
    PyObject * pyModuleSizeKey          = Py_BuildValue("s", "ModuleSize");
    PyDict_SetItem(pyResult, pyModuleSizeKey, pyModuleSize);
    Py_DECREF(pyModuleSize);
    Py_DECREF(pyModuleSizeKey);

    PyObject * pyPageNumber             = Py_BuildValue("i", pResult->pageNumber);
    PyObject * pyPageNumberKey          = Py_BuildValue("s", "PageNumber");
    PyDict_SetItem(pyResult, pyPageNumberKey, pyPageNumber);
    Py_DECREF(pyPageNumber);
    Py_DECREF(pyPageNumberKey);

    if(pResult->regionName != NULL)
    {
        PyObject * pyRegionName             = Py_BuildValue("s", pResult->regionName);
        PyObject * pyRegionNameKey          = Py_BuildValue("s", "RegionName");
        PyDict_SetItem(pyResult, pyRegionNameKey, pyRegionName);
        Py_DECREF(pyRegionName);
        Py_DECREF(pyRegionNameKey);
    }
    else
    {
      //  PyObject * pyRegionName             = Py_None;
        PyObject * pyRegionNameKey          = Py_BuildValue("s", "RegionName");
        PyDict_SetItem(pyResult, pyRegionNameKey, Py_None);
       // Py_DECREF(pyRegionName);
        Py_DECREF(pyRegionNameKey);
    }
    

    if(pResult->documentName != NULL)
    {
        PyObject * pyDocumentName           = Py_BuildValue("s", pResult->documentName);
        PyObject * pyDocumentNameKey        = Py_BuildValue("s", "DocumentName");
        PyDict_SetItem(pyResult, pyDocumentNameKey, pyDocumentName);
        Py_DECREF(pyDocumentName);
        Py_DECREF(pyDocumentNameKey);
    }
    else
    {
     //   PyObject * pyDocumentName           = Py_None;
        PyObject * pyDocumentNameKey        = Py_BuildValue("s", "DocumentName");
        PyDict_SetItem(pyResult, pyDocumentNameKey, Py_None);
       // Py_DECREF(pyDocumentName);
        Py_DECREF(pyDocumentNameKey);
    }
    

    PyObject * pyResultCoordinateType   = Py_BuildValue("i", pResult->resultCoordinateType);
    PyObject * pyResultCoordinateTypeKey= Py_BuildValue("s", "ResultCoordinateType");
    PyDict_SetItem(pyResult, pyResultCoordinateTypeKey, pyResultCoordinateType);
    Py_DECREF(pyResultCoordinateType);
    Py_DECREF(pyResultCoordinateTypeKey);

   // PyObject * pyAccompanyingTextBytes    = Py_None;
    PyObject * pyAccompanyingTextBytesKey = Py_BuildValue("s", "AccompanyingTextBytes");
    PyDict_SetItem(pyResult, pyAccompanyingTextBytesKey, Py_None);
   // Py_DECREF(pyAccompanyingTextBytes);
    Py_DECREF(pyAccompanyingTextBytesKey);
    
    PyObject * pyConfidence             = Py_BuildValue("i", pResult->confidence);
    PyObject * pyConfidenceKey          = Py_BuildValue("s", "Confidence");
    PyDict_SetItem(pyResult, pyConfidenceKey, pyConfidence);
    Py_DECREF(pyConfidence);
    Py_DECREF(pyConfidenceKey);

    PyObject * pyTransMatrix = PyList_New(9);
    for(int j = 0; j < 9; ++j)
    {
        PyObject * temp = Py_BuildValue("d",pResult->transformationMatrix[j]);
        PyList_SetItem(pyTransMatrix, j, temp);
    }
    PyObject * pyTransMatrixKey   = Py_BuildValue("s", "TransformationMatrix");
    PyDict_SetItem(pyResult, pyTransMatrixKey, pyTransMatrix);
    Py_DECREF(pyTransMatrix);
    Py_DECREF(pyTransMatrixKey);

    return pyResult;
}

LocalizationResult * CreateCLocalizationResult(PyObject * pyLocalizationResult)
{
    LocalizationResult * pLocalizationResult = (LocalizationResult*)malloc(sizeof(LocalizationResult));

    pLocalizationResult->terminatePhase = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "TerminatePhase")));
    pLocalizationResult->barcodeFormat = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "BarcodeFormat")));

    PyObject * pyBarcodeFormatString = PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "BarcodeFormatString"));
    if(pyBarcodeFormatString == Py_None)
    {
        pLocalizationResult->barcodeFormatString = NULL;
    }
    else
    {
        pLocalizationResult->barcodeFormatString = PyBytes_AsString(pyBarcodeFormatString);
    }

    pLocalizationResult->barcodeFormat_2 = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "BarcodeFormat_2")));

    PyObject * pyBarcodeFormatString_2 = PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "BarcodeFormatString_2"));
    if(pyBarcodeFormatString_2 == Py_None)
    {
        pLocalizationResult->barcodeFormatString_2 = NULL;
    }
    else
    {
        pLocalizationResult->barcodeFormatString_2 = PyBytes_AsString(pyBarcodeFormatString_2);
    }
    
    pLocalizationResult->x1 = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "X1")));
    pLocalizationResult->y1 = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "Y1")));
    pLocalizationResult->x2 = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "X2")));
    pLocalizationResult->y2 = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "Y2")));
    pLocalizationResult->x3 = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "X3")));
    pLocalizationResult->y3 = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "Y3")));
    pLocalizationResult->x4 = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "X4")));
    pLocalizationResult->y4 = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "Y4")));
    pLocalizationResult->angle = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "Angle")));
    pLocalizationResult->moduleSize = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "ModuleSize")));
    pLocalizationResult->pageNumber = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "PageNumber")));

    PyObject * pyRegionName = PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "RegionName"));
    if(pyRegionName == Py_None)
    {
        pLocalizationResult->regionName = NULL;
    }
    else
    {
        pLocalizationResult->regionName = PyBytes_AsString(pyRegionName);
    }

    PyObject * pyDocumentName = PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "DocumentName"));
    if(pyDocumentName == Py_None)
    {
        pLocalizationResult->documentName = NULL;
    }
    else
    {
        pLocalizationResult->documentName = PyBytes_AsString(pyDocumentName);
    }

    pLocalizationResult->resultCoordinateType = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "ResultCoordinateType")));

    pLocalizationResult->accompanyingTextBytes = NULL;
    pLocalizationResult->accompanyingTextBytesLength = 0;
    pLocalizationResult->confidence = PyLong_AsLong(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "Confidence")));

    for(int j = 0; j < 9; ++j)
    {
        pLocalizationResult->transformationMatrix[j] = PyFloat_AsDouble(PyList_GetItem(PyDict_GetItem(pyLocalizationResult, Py_BuildValue("s", "TransformationMatrix")), j));
    }

    return pLocalizationResult;
}

static PyObject * CreatePyExtendedResult(ExtendedResult * pResult)
{
    PyObject * pyResult = PyDict_New();
    if(pyResult == NULL)
    { 
        Py_RETURN_NONE;
    }

    PyObject * pyResultType             = Py_BuildValue("i", pResult->resultType);
    PyObject * pyResultTypeKey          = Py_BuildValue("s", "ResultType");
    PyDict_SetItem(pyResult, pyResultTypeKey, pyResultType);
    Py_DECREF(pyResultType);
    Py_DECREF(pyResultTypeKey);

    PyObject * pyBarcodeFormat          = Py_BuildValue("i", pResult->barcodeFormat);
    PyObject * pyBarcodeFormatKey       = Py_BuildValue("s", "BarcodeFormat");
    PyDict_SetItem(pyResult, pyBarcodeFormatKey, pyBarcodeFormat);
    Py_DECREF(pyBarcodeFormat);
    Py_DECREF(pyBarcodeFormatKey);

    if(pResult->barcodeFormatString != NULL)
    {
        PyObject * pyBarcodeFormatString    = Py_BuildValue("s", pResult->barcodeFormatString);
        PyObject * pyBarcodeFormatStringKey = Py_BuildValue("s", "BarcodeFormatString");
        PyDict_SetItem(pyResult, pyBarcodeFormatStringKey, pyBarcodeFormatString);
        Py_DECREF(pyBarcodeFormatString);
        Py_DECREF(pyBarcodeFormatStringKey);
    }
    else
    {
       // PyObject * pyBarcodeFormatString    = Py_None;
        PyObject * pyBarcodeFormatStringKey = Py_BuildValue("s", "BarcodeFormatString");
        PyDict_SetItem(pyResult, pyBarcodeFormatStringKey, Py_None);
       // Py_DECREF(pyBarcodeFormatString);
        Py_DECREF(pyBarcodeFormatStringKey);
    }
    

    PyObject * pyBarcodeFormat_2        = Py_BuildValue("i", pResult->barcodeFormat_2);
    PyObject * pyBarcodeFormatKey_2     = Py_BuildValue("s", "BarcodeFormat_2");
    PyDict_SetItem(pyResult, pyBarcodeFormatKey_2, pyBarcodeFormat_2);
    Py_DECREF(pyBarcodeFormat_2);
    Py_DECREF(pyBarcodeFormatKey_2);

    if(pResult->barcodeFormatString_2 != NULL)
    {
        PyObject * pyBarcodeFormatString_2    = Py_BuildValue("s", pResult->barcodeFormatString_2);
        PyObject * pyBarcodeFormatStringKey_2 = Py_BuildValue("s", "BarcodeFormatString_2");
        PyDict_SetItem(pyResult, pyBarcodeFormatStringKey_2, pyBarcodeFormatString_2);
        Py_DECREF(pyBarcodeFormatString_2);
        Py_DECREF(pyBarcodeFormatStringKey_2);
    }
    else
    {
       // PyObject * pyBarcodeFormatString_2    = Py_None;
        PyObject * pyBarcodeFormatStringKey_2 = Py_BuildValue("s", "BarcodeFormatString_2");
        PyDict_SetItem(pyResult, pyBarcodeFormatStringKey_2, Py_None);
       // Py_DECREF(pyBarcodeFormatString_2);
        Py_DECREF(pyBarcodeFormatStringKey_2);
    }

    PyObject * pyConfidence             = Py_BuildValue("i",pResult->confidence);
    PyObject * pyConfidenceKey          = Py_BuildValue("s", "Confidence");
    PyDict_SetItem(pyResult, pyConfidenceKey, pyConfidence);
    Py_DECREF(pyConfidence);
    Py_DECREF(pyConfidenceKey);

    if(pResult->bytes != NULL)
    {
        PyObject * pyBytes                  = PyByteArray_FromStringAndSize(pResult->bytes, pResult->bytesLength);
        PyObject * pyBytesKey               = Py_BuildValue("s", "Bytes");
        PyDict_SetItem(pyResult, pyBytesKey, pyBytes);
        Py_DECREF(pyBytes);
        Py_DECREF(pyBytesKey);
    }
    else
    {
        //PyObject * pyBytes                  = Py_BuildValue("o", NULL);
        PyObject * pyBytesKey               = Py_BuildValue("s", "Bytes");
        PyDict_SetItem(pyResult, pyBytesKey, Py_None);
        //Py_DECREF(pyBytes);
        Py_DECREF(pyBytesKey);
    }

    if(pResult->accompanyingTextBytes != NULL)
    {
        PyObject * pyAccompanyingTextBytes    = PyByteArray_FromStringAndSize(pResult->accompanyingTextBytes, pResult->accompanyingTextBytesLength);
        PyObject * pyAccompanyingTextBytesKey = Py_BuildValue("s", "AccompanyingTextBytes");
        PyDict_SetItem(pyResult, pyAccompanyingTextBytesKey, pyAccompanyingTextBytes);
		Py_DECREF(pyAccompanyingTextBytes);
		Py_DECREF(pyAccompanyingTextBytesKey);
    }
    else
    {
        //PyObject * pyAccompanyingTextBytes    = Py_BuildValue("o", NULL);
        PyObject * pyAccompanyingTextBytesKey = Py_BuildValue("s", "AccompanyingTextBytes");
        PyDict_SetItem(pyResult, pyAccompanyingTextBytesKey, Py_None);
        //Py_DECREF(pyAccompanyingTextBytes);
        Py_DECREF(pyAccompanyingTextBytesKey);
    }
    
    PyObject * pyDeformation            = Py_BuildValue("i", pResult->deformation);
    PyObject * pyDeformationKey         = Py_BuildValue("s", "Deformation");
    PyDict_SetItem(pyResult, pyDeformationKey, pyDeformation);
    Py_DECREF(pyDeformation);
    Py_DECREF(pyDeformationKey);

    if(pResult->detailedResult != NULL)
    {
        PyObject * pyDetailedResult         = CreatePyDetailedResult(pResult->detailedResult, pResult->barcodeFormat);
        PyObject * pyDetailedResultKey      = Py_BuildValue("s", "DetailedResult");
        PyDict_SetItem(pyResult, pyDetailedResultKey, pyDetailedResult);
        Py_DECREF(pyDetailedResult);
        Py_DECREF(pyDetailedResultKey);
    }
    else
    {
        //PyObject * pyDetailedResult         = Py_BuildValue("o", NULL);
        PyObject * pyDetailedResultKey      = Py_BuildValue("s", "DetailedResult");
        PyDict_SetItem(pyResult, pyDetailedResultKey, Py_None);
        //Py_DECREF(pyDetailedResult);
        Py_DECREF(pyDetailedResultKey);
    }
    
    
    PyObject * pySamplingImage          = CreatePySamplingImageData(pResult->samplingImage);
	if (pySamplingImage != NULL)
	{
		PyObject * pySamplingImageKey = Py_BuildValue("s", "SamplingImage");
		PyDict_SetItem(pyResult, pySamplingImageKey, pySamplingImage);
		Py_DECREF(pySamplingImage);
		Py_DECREF(pySamplingImageKey);
	}
	else
	{
		PyObject * pySamplingImageKey = Py_BuildValue("s", "SamplingImage");
		PyDict_SetItem(pyResult, pySamplingImageKey, Py_None);
		Py_DECREF(pySamplingImage);
		Py_DECREF(pySamplingImageKey);
	}

    PyObject * pyClarity                = Py_BuildValue("i",pResult->clarity);
    PyObject * pyClarityKey             = Py_BuildValue("s", "Clarity");
    PyDict_SetItem(pyResult, pyClarityKey, pyClarity);
    Py_DECREF(pyClarity);
    Py_DECREF(pyClarityKey);

    // PyObject * pyReservedy                = Py_BuildValue("i",((int*)(pResult->reserved))[0]);
    // PyObject * pyReservedKey             = Py_BuildValue("s", "Reserved");
    // PyDict_SetItem(pyResult, pyReservedKey, pyReserved);
    // Py_DECREF(pyReserved);
    // Py_DECREF(pyReservedKey);

    return pyResult;
}

static PyObject * CreatePyTextResults(TextResultArray *pResults)
{
    // Get barcode results
    int count = pResults->resultsCount;

    // Create a Python object to store results
    PyObject *pyTextResults = PyList_New(count);
	if (pyTextResults == NULL)
	{
        Py_RETURN_NONE;
	}

    for (int i = 0; i < count; i++)
    {
        PyObject * pyTextResult = PyDict_New();
        if(pyTextResult == NULL)
        {
            Py_RETURN_NONE;
        }

        PyObject * pyBarcodeFormat      = Py_BuildValue("i", pResults->results[i]->barcodeFormat);
        PyObject * pyBarcodeFormatKey   = Py_BuildValue("s", "BarcodeFormat");
        PyDict_SetItem(pyTextResult, pyBarcodeFormatKey, pyBarcodeFormat);
        Py_DECREF(pyBarcodeFormat);
        Py_DECREF(pyBarcodeFormatKey);

        if(pResults->results[i]->barcodeFormatString != NULL)
        {
            PyObject * pyBarcodeFormatString    = Py_BuildValue("s", pResults->results[i]->barcodeFormatString);
            PyObject * pyBarcodeFormatStringKey = Py_BuildValue("s", "BarcodeFormatString");
            PyDict_SetItem(pyTextResult, pyBarcodeFormatStringKey, pyBarcodeFormatString);
            Py_DECREF(pyBarcodeFormatString);
            Py_DECREF(pyBarcodeFormatStringKey);
        }
        else
        {
          //  PyObject * pyBarcodeFormatString    = Py_None;
            PyObject * pyBarcodeFormatStringKey = Py_BuildValue("s", "BarcodeFormatString");
            PyDict_SetItem(pyTextResult, pyBarcodeFormatStringKey, Py_None);
           // Py_DECREF(pyBarcodeFormatString);
            Py_DECREF(pyBarcodeFormatStringKey);
        }    

        PyObject * pyBarcodeFormat_2    = Py_BuildValue("i", pResults->results[i]->barcodeFormat_2);
        PyObject * pyBarcodeFormatKey_2 = Py_BuildValue("s", "BarcodeFormat_2");
        PyDict_SetItem(pyTextResult, pyBarcodeFormatKey_2, pyBarcodeFormat_2);
        Py_DECREF(pyBarcodeFormat_2);
        Py_DECREF(pyBarcodeFormatKey_2);

        PyObject * pyIsDPM    = Py_BuildValue("i", pResults->results[i]->isDPM);
        PyObject * pyIsDPMKey = Py_BuildValue("s", "IsDPM");
        PyDict_SetItem(pyTextResult, pyIsDPMKey, pyIsDPM);
        Py_DECREF(pyIsDPM);
        Py_DECREF(pyIsDPMKey);

        PyObject * pyIsMirrored    = Py_BuildValue("i", pResults->results[i]->isMirrored);
        PyObject * pyIsMirroredKey = Py_BuildValue("s", "IsMirrored");
        PyDict_SetItem(pyTextResult, pyIsMirroredKey, pyIsMirrored);
        Py_DECREF(pyIsMirrored);
        Py_DECREF(pyIsMirroredKey);

        if(pResults->results[i]->barcodeFormatString_2 != NULL)
        {
            PyObject * pyBarcodeFormatString_2    = Py_BuildValue("s", pResults->results[i]->barcodeFormatString_2);
            PyObject * pyBarcodeFormatStringKey_2 = Py_BuildValue("s", "BarcodeFormatString_2");
            PyDict_SetItem(pyTextResult, pyBarcodeFormatStringKey_2, pyBarcodeFormatString_2);
            Py_DECREF(pyBarcodeFormatString_2);
            Py_DECREF(pyBarcodeFormatStringKey_2);
        }
        else
        {
           // PyObject * pyBarcodeFormatString_2    = Py_None;
            PyObject * pyBarcodeFormatStringKey_2 = Py_BuildValue("s", "BarcodeFormatString_2");
            PyDict_SetItem(pyTextResult, pyBarcodeFormatStringKey_2, Py_None);
           // Py_DECREF(pyBarcodeFormatString_2);
            Py_DECREF(pyBarcodeFormatStringKey_2);
        }

        if(pResults->results[i]->barcodeText != NULL)
        {
            PyObject * pyBarcodeText        = Py_BuildValue("s", pResults->results[i]->barcodeText);
            if(pyBarcodeText == NULL)
            {
                PyErr_Clear();
                Py_XDECREF(pyBarcodeText);
                PyObject * pyBarcodeText2        = Py_BuildValue("s", "Warning: Character set invalid, please convert the BarcodeBytes manually.");
                PyObject * pyBarcodeTextKey     = Py_BuildValue("s", "BarcodeText");
                PyDict_SetItem(pyTextResult, pyBarcodeTextKey, pyBarcodeText2);
                Py_DECREF(pyBarcodeText2);
                Py_DECREF(pyBarcodeTextKey);
            }
            else
            {
                PyObject * pyBarcodeTextKey     = Py_BuildValue("s", "BarcodeText");
                PyDict_SetItem(pyTextResult, pyBarcodeTextKey, pyBarcodeText);
                Py_DECREF(pyBarcodeText);
                Py_DECREF(pyBarcodeTextKey);
            }
        }
        else
        {
           // PyObject * pyBarcodeText        = Py_None;
            PyObject * pyBarcodeTextKey     = Py_BuildValue("s", "BarcodeText");
            PyDict_SetItem(pyTextResult, pyBarcodeTextKey, Py_None);
           // Py_DECREF(pyBarcodeText);
            Py_DECREF(pyBarcodeTextKey);
        }

        if(!(pResults->results[i]->barcodeBytes == NULL || pResults->results[i]->barcodeBytesLength == 0))
        {
            PyObject * pyBarcodeBytes       = PyByteArray_FromStringAndSize(pResults->results[i]->barcodeBytes, pResults->results[i]->barcodeBytesLength);
            PyObject * pyBarcodeBytesKey    = Py_BuildValue("s", "BarcodeBytes");
            PyDict_SetItem(pyTextResult, pyBarcodeBytesKey, pyBarcodeBytes);
            Py_DECREF(pyBarcodeBytes);
            Py_DECREF(pyBarcodeBytesKey);
        }
        else
        {
            //PyObject * pyBarcodeBytes       = Py_BuildValue("o", NULL);
            PyObject * pyBarcodeBytesKey    = Py_BuildValue("s", "BarcodeBytes");
            PyDict_SetItem(pyTextResult, pyBarcodeBytesKey, Py_None);
            //Py_DECREF(pyBarcodeBytes);
            Py_DECREF(pyBarcodeBytesKey);
        }

        if(pResults->results[i]->exception != NULL)
        {
            PyObject * pyException    = Py_BuildValue("s", pResults->results[i]->exception);
            PyObject * pyExceptionKey = Py_BuildValue("s", "Exception");
            PyDict_SetItem(pyTextResult, pyExceptionKey, pyException);
            Py_DECREF(pyException);
            Py_DECREF(pyExceptionKey);
        }
        else
        {
          //  PyObject * pyException    = Py_None;
            PyObject * pyExceptionKey = Py_BuildValue("s", "Exception");
            PyDict_SetItem(pyTextResult, pyExceptionKey, Py_None);
          //  Py_DECREF(pyException);
            Py_DECREF(pyExceptionKey);
        }
        
        if(pResults->results[i]->localizationResult != NULL)
        {
            PyObject * pyLocalizationResult     = CreatePyLocalizationResult(pResults->results[i]->localizationResult);
            PyObject * pyLocalizationResultKey  = Py_BuildValue("s", "LocalizationResult");
            PyDict_SetItem(pyTextResult, pyLocalizationResultKey, pyLocalizationResult);
            Py_DECREF(pyLocalizationResult);
            Py_DECREF(pyLocalizationResultKey);
        }
        else
        {
            //PyObject * pyLocalizationResult     = Py_BuildValue("o", NULL);
            PyObject * pyLocalizationResultKey  = Py_BuildValue("s", "LocalizationResult");
            PyDict_SetItem(pyTextResult, pyLocalizationResultKey, Py_None);
            //Py_DECREF(pyLocalizationResult);
            Py_DECREF(pyLocalizationResultKey);
        }

        if(pResults->results[i]->detailedResult != NULL)
        {
            PyObject * pyDetailedResult     = CreatePyDetailedResult(pResults->results[i]->detailedResult, pResults->results[i]->barcodeFormat);
            PyObject * pyDetailedResultKey  = Py_BuildValue("s", "DetailedResult");
            PyDict_SetItem(pyTextResult, pyDetailedResultKey, pyDetailedResult);
            Py_DECREF(pyDetailedResult);
            Py_DECREF(pyDetailedResultKey);
        }
        else
        {
            //PyObject * pyDetailedResult     = Py_BuildValue("o", NULL);
            PyObject * pyDetailedResultKey  = Py_BuildValue("s", "DetailedResult");
            PyDict_SetItem(pyTextResult, pyDetailedResultKey, Py_None);
            //Py_DECREF(pyDetailedResult);
            Py_DECREF(pyDetailedResultKey);
        }

        if(pResults->results[i]->resultsCount != 0 && pResults->results[i]->results != NULL)
        {
            PyObject * pyExtendedResults    = PyList_New(pResults->results[i]->resultsCount);
            for(int j = 0; j < pResults->results[i]->resultsCount; ++j)
            {
                PyObject * pyExtendedResult = CreatePyExtendedResult(pResults->results[i]->results[j]);
                PyList_SetItem(pyExtendedResults, j, pyExtendedResult);
				//Py_DECREF(pyExtendedResult);
            }
            PyObject * pyExtendedResultsKey = Py_BuildValue("s", "ExtendedResults");
            PyDict_SetItem(pyTextResult, pyExtendedResultsKey, pyExtendedResults);
            Py_DECREF(pyExtendedResults);
            Py_DECREF(pyExtendedResultsKey);
        }
        else
        {
            //PyObject * pyExtendedResults = Py_BuildValue("o", NULL);
            PyObject * pyExtendedResultsKey = Py_BuildValue("s", "ExtendedResults");
            PyDict_SetItem(pyTextResult, pyExtendedResultsKey, Py_None);
            //Py_DECREF(pyExtendedResults);
            Py_DECREF(pyExtendedResultsKey);
        }

        PyList_SetItem(pyTextResults, i, pyTextResult);
    }

    // Release memory
    // DBR_FreeTextResults(&pResults);

    return pyTextResults;
}

static PyObject * CreatePyImageData(ImageData * pImageData)
{
    PyObject * pyImageData = PyDict_New();

    if(pImageData->bytes != NULL)
    {
        PyObject * pyBytes       = PyByteArray_FromStringAndSize(pImageData->bytes, pImageData->bytesLength);
        PyObject * pyBytesKey    = Py_BuildValue("s", "Bytes");
        PyDict_SetItem(pyImageData, pyBytesKey, pyBytes);
        Py_DECREF(pyBytes);
        Py_DECREF(pyBytesKey);
    }
    else
    {
        //PyObject * pyBytes       = Py_BuildValue("o", NULL);
        PyObject * pyBytesKey    = Py_BuildValue("s", "Bytes");
        PyDict_SetItem(pyImageData, pyBytesKey, Py_None);
        //Py_DECREF(pyBytes);
        Py_DECREF(pyBytesKey);
    }
    

    PyObject * pyWidth      = Py_BuildValue("i", pImageData->width);
    PyObject * pyWidthKey   = Py_BuildValue("s", "Width");
    PyDict_SetItem(pyImageData, pyWidthKey, pyWidth);
    Py_DECREF(pyWidth);
    Py_DECREF(pyWidthKey);

    PyObject * pyHeight      = Py_BuildValue("i", pImageData->height);
    PyObject * pyHeightKey   = Py_BuildValue("s", "Height");
    PyDict_SetItem(pyImageData, pyHeightKey, pyHeight);
    Py_DECREF(pyHeight);
    Py_DECREF(pyHeightKey);

    PyObject * pyStride      = Py_BuildValue("i", pImageData->stride);
    PyObject * pyStrideKey   = Py_BuildValue("s", "Stride");
    PyDict_SetItem(pyImageData, pyStrideKey, pyStride);
    Py_DECREF(pyStride);
    Py_DECREF(pyStrideKey);

    PyObject * pyImagePixelFormat      = Py_BuildValue("i", pImageData->format);
    PyObject * pyImagePixelFormatKey   = Py_BuildValue("s", "ImagePixelFormat");
    PyDict_SetItem(pyImageData, pyImagePixelFormatKey, pyImagePixelFormat);
    Py_DECREF(pyImagePixelFormat);
    Py_DECREF(pyImagePixelFormatKey);

    PyObject * pyImageOrientation    = Py_BuildValue("i", pImageData->orientation);
    PyObject * pyImageOrientationKey   = Py_BuildValue("s", "Orientation");
    PyDict_SetItem(pyImageData, pyImageOrientationKey, pyImageOrientation);
    Py_DECREF(pyImageOrientation);
    Py_DECREF(pyImageOrientationKey);

    return pyImageData;
}

ImageData * CreateCImageData(PyObject * pyImageData)
{
    ImageData* pImageData = (ImageData*)malloc(sizeof(ImageData));
                        
    PyObject * pyBytes = PyDict_GetItem(pyImageData, Py_BuildValue("s","Bytes"));

    if(PyBytes_Check(pyBytes))
    {
        pImageData->bytesLength = (int)PyBytes_Size(pyBytes);
        pImageData->bytes = (unsigned char *)malloc(sizeof(unsigned char) * pImageData->bytesLength);
        memcpy(pImageData->bytes, (unsigned char *)PyBytes_AsString(pyBytes), pImageData->bytesLength);
        // pImageData->bytes = (unsigned char *)PyBytes_AsString(pyBytes);
    }
    else if(PyByteArray_Check(pyBytes))
    {
        pImageData->bytesLength = (int)PyByteArray_Size(pyBytes);
        pImageData->bytes = (unsigned char *)malloc(sizeof(unsigned char) * pImageData->bytesLength);
        memcpy(pImageData->bytes, (unsigned char *)PyByteArray_AsString(pyBytes), pImageData->bytesLength);
        // pImageData->bytes = (unsigned char *)PyByteArray_AsString(pyBytes);
    }
    else if(pyBytes == Py_None)
    {
        pImageData->bytes = NULL;
        pImageData->bytesLength = 0;
    }

    pImageData->format = (ImagePixelFormat)PyLong_AsLong(PyDict_GetItem(pyImageData, Py_BuildValue("s","ImagePixelFormat")));
    pImageData->width = PyLong_AsLong(PyDict_GetItem(pyImageData, Py_BuildValue("s","Width")));
    pImageData->height = PyLong_AsLong(PyDict_GetItem(pyImageData, Py_BuildValue("s","Height")));
    pImageData->stride = PyLong_AsLong(PyDict_GetItem(pyImageData, Py_BuildValue("s","Stride")));
    pImageData->orientation = PyLong_AsLong(PyDict_GetItem(pyImageData,Py_BuildValue("s","Orientation")));
    return pImageData;
}

static PyObject * CreatePyContour(Contour * pContour)
{
    PyObject * pyContour = PyDict_New();
    int pointCount = pContour->pointsCount;
    if(pointCount != 0)
    {
        PyObject * pyPoints = PyList_New(pointCount);
        for(int j = 0; j < pointCount; ++j)
        {
            PyObject * pyPoint = PyDict_New();

            PyObject * pyPointX = Py_BuildValue("i", pContour->points[j].x);
            PyObject * pyPointXKey   = Py_BuildValue("s", "X");
            PyDict_SetItem(pyPoint, pyPointXKey, pyPointX);
            Py_DECREF(pyPointX);
            Py_DECREF(pyPointXKey);

            PyObject * pyPointY = Py_BuildValue("i", pContour->points[j].y);
            PyObject * pyPointYKey   = Py_BuildValue("s", "Y");
            PyDict_SetItem(pyPoint, pyPointYKey, pyPointY);
            Py_DECREF(pyPointY);
            Py_DECREF(pyPointYKey);

            PyList_SetItem(pyPoints, j, pyPoint);
        }
        PyObject * pyPointsKey   = Py_BuildValue("s", "Points");
        PyDict_SetItem(pyContour, pyPointsKey, pyPoints);
        Py_DECREF(pyPoints);
        Py_DECREF(pyPointsKey);
    }
    else
    {
        //PyObject * pyPoints   = Py_BuildValue("o", NULL);
        PyObject * pyPointsKey   = Py_BuildValue("s", "Points");
        PyDict_SetItem(pyContour, pyPointsKey, Py_None);
        //Py_DECREF(pyPoints);
        Py_DECREF(pyPointsKey);
    }

    return pyContour;
}

Contour * CreateCContour(PyObject * pyContour)
{
    Contour* pContour = (Contour*)malloc(sizeof(Contour));

    PyObject * pyPoints = PyDict_GetItem(pyContour, Py_BuildValue("s", "Points"));

    int len = (int)PyList_Size(pyPoints);
    pContour->pointsCount = len;
    pContour->points = (DBRPoint *)malloc(sizeof(DBRPoint) * len);

    for(int m = 0; m < len; ++m)
    {
        PyObject * pyPoint = PyList_GetItem(pyPoints, m);
        pContour->points[m].x = PyLong_AsLong(PyDict_GetItem(pyPoint, Py_BuildValue("s","X"))); 
        pContour->points[m].y = PyLong_AsLong(PyDict_GetItem(pyPoint, Py_BuildValue("s","Y")));                         
    }

    return pContour;
}

static PyObject * CreatePyLineSegment(LineSegment * pLineSegment)
{
    PyObject * pyLineSegment = PyDict_New();

    PyObject * pyStartPoint = PyDict_New();
    PyObject * pyStartPointX = Py_BuildValue("i", pLineSegment->startPoint.x);
    PyObject * pyStartPointXKey   = Py_BuildValue("s", "X");
    PyDict_SetItem(pyStartPoint, pyStartPointXKey, pyStartPointX);
    Py_DECREF(pyStartPointX);
    Py_DECREF(pyStartPointXKey);

    PyObject * pyStartPointY = Py_BuildValue("i", pLineSegment->startPoint.y);
    PyObject * pyStartPointYKey   = Py_BuildValue("s", "Y");
    PyDict_SetItem(pyStartPoint, pyStartPointYKey, pyStartPointY);
    Py_DECREF(pyStartPointY);
    Py_DECREF(pyStartPointYKey);
    PyObject * pyStartPointKey   = Py_BuildValue("s", "StartPoint");
    PyDict_SetItem(pyLineSegment, pyStartPointKey, pyStartPoint);
    Py_DECREF(pyStartPoint);
    Py_DECREF(pyStartPointKey);

    PyObject * pyEndPoint = PyDict_New();
    PyObject * pyEndPointX = Py_BuildValue("i", pLineSegment->endPoint.x);
    PyObject * pyEndPointXKey   = Py_BuildValue("s", "X");
    PyDict_SetItem(pyEndPoint, pyEndPointXKey, pyEndPointX);
    Py_DECREF(pyEndPointX);
    Py_DECREF(pyEndPointXKey);

    PyObject * pyEndPointY = Py_BuildValue("i", pLineSegment->endPoint.y);
    PyObject * pyEndPointYKey   = Py_BuildValue("s", "Y");
    PyDict_SetItem(pyEndPoint, pyEndPointYKey, pyEndPointY);
    Py_DECREF(pyEndPointY);
    Py_DECREF(pyEndPointYKey);
    PyObject * pyEndPointKey   = Py_BuildValue("s", "EndPoint");
    PyDict_SetItem(pyLineSegment, pyEndPointKey, pyEndPoint);
    Py_DECREF(pyEndPoint);
    Py_DECREF(pyEndPointKey);

    if(pLineSegment->linesConfidenceCoefficients != NULL)
    {
        PyObject * pyLinesConfidenceCoefficients = PyList_New(4);
        for(int j = 0; j < 4; ++j)
        {
            PyObject * pyLinesConfidenceCoefficient = Py_BuildValue("i", pLineSegment->linesConfidenceCoefficients[j]);
            PyList_SetItem(pyLinesConfidenceCoefficients, j, pyLinesConfidenceCoefficient);
        }
        PyObject * pyLinesConfidenceCoefficientsKey   = Py_BuildValue("s", "LinesConfidenceCoefficients");
        PyDict_SetItem(pyLineSegment, pyLinesConfidenceCoefficientsKey, pyLinesConfidenceCoefficients);
        Py_DECREF(pyLinesConfidenceCoefficients);
        Py_DECREF(pyLinesConfidenceCoefficientsKey);
    }
    else
    {
        //PyObject * pyLinesConfidenceCoefficients   = Py_BuildValue("o", NULL);
        PyObject * pyLinesConfidenceCoefficientsKey   = Py_BuildValue("s", "LinesConfidenceCoefficients");
        PyDict_SetItem(pyLineSegment, pyLinesConfidenceCoefficientsKey, Py_None);
        //Py_DECREF(pyLinesConfidenceCoefficients);
        Py_DECREF(pyLinesConfidenceCoefficientsKey);
    }

    return pyLineSegment;
}

LineSegment * CreateCLineSegment(PyObject * pyLineSegment)
{
    LineSegment* pLineSegment = (LineSegment*)malloc(sizeof(LineSegment));

    PyObject * pyStartPoint = PyDict_GetItem(pyLineSegment, Py_BuildValue("s","StartPoint"));
    PyObject * pyEndPoint = PyDict_GetItem(pyLineSegment, Py_BuildValue("s","EndPoint"));
    PyObject * pyLinesConfidenceCoefficients = PyDict_GetItem(pyLineSegment, Py_BuildValue("s","LinesConfidenceCoefficients"));
    pLineSegment->startPoint.x = PyLong_AsLong(PyDict_GetItem(pyStartPoint, Py_BuildValue("s","X")));
    pLineSegment->startPoint.y = PyLong_AsLong(PyDict_GetItem(pyStartPoint, Py_BuildValue("s","Y")));
    pLineSegment->endPoint.x = PyLong_AsLong(PyDict_GetItem(pyEndPoint, Py_BuildValue("s","X")));
    pLineSegment->endPoint.y = PyLong_AsLong(PyDict_GetItem(pyEndPoint, Py_BuildValue("s","Y")));

    if(pyLinesConfidenceCoefficients != Py_None)
    {
        pLineSegment->linesConfidenceCoefficients = (unsigned char*)malloc(sizeof(unsigned char)*4);
        for(int m = 0; m < 4; ++m)
        {
            pLineSegment->linesConfidenceCoefficients[m] = (unsigned char)PyLong_AsLong(PyList_GetItem(pyLinesConfidenceCoefficients, m));
        }
    }
    else
    {
        pLineSegment->linesConfidenceCoefficients = NULL;
    }

    return pLineSegment;
}

static PyObject * CreatePyRegionOfInterest(RegionOfInterest * pRegionOfInterest)
{
    PyObject * pyRegionOfInterest = PyDict_New();

    PyObject * pyROIId      = Py_BuildValue("i", pRegionOfInterest->roiId);
    PyObject * pyROIIdKey   = Py_BuildValue("s", "ROIId");
    PyDict_SetItem(pyRegionOfInterest, pyROIIdKey, pyROIId);
    Py_DECREF(pyROIId);
    Py_DECREF(pyROIIdKey);

    PyObject * pyPoint = PyDict_New();

    PyObject * pyPointX = Py_BuildValue("i", pRegionOfInterest->point.x);
    PyObject * pyPointXKey   = Py_BuildValue("s", "X");
    PyDict_SetItem(pyPoint, pyPointXKey, pyPointX);
    Py_DECREF(pyPointX);
    Py_DECREF(pyPointXKey);

    PyObject * pyPointY = Py_BuildValue("i", pRegionOfInterest->point.y);
    PyObject * pyPointYKey   = Py_BuildValue("s", "Y");
    PyDict_SetItem(pyPoint, pyPointYKey, pyPointY);
    Py_DECREF(pyPointY);
    Py_DECREF(pyPointYKey);
    PyObject * pyPointKey   = Py_BuildValue("s", "Point");
    PyDict_SetItem(pyRegionOfInterest, pyPointKey, pyPoint);
    Py_DECREF(pyPoint);
    Py_DECREF(pyPointKey);

    PyObject * pyWidth      = Py_BuildValue("i", pRegionOfInterest->width);
    PyObject * pyWidthKey   = Py_BuildValue("s", "Width");
    PyDict_SetItem(pyRegionOfInterest, pyWidthKey, pyWidth);
    Py_DECREF(pyWidth);
    Py_DECREF(pyWidthKey);

    PyObject * pyHeight      = Py_BuildValue("i", pRegionOfInterest->height);
    PyObject * pyHeightKey   = Py_BuildValue("s", "Height");
    PyDict_SetItem(pyRegionOfInterest, pyHeightKey, pyHeight);
    Py_DECREF(pyHeight);
    Py_DECREF(pyHeightKey);

    return pyRegionOfInterest;
}

RegionOfInterest * CreateCRegionOfInterest(PyObject * pyRegionOfInterest)
{
    RegionOfInterest * pRegionOfInterest = (RegionOfInterest *)malloc(sizeof(RegionOfInterest));
    pRegionOfInterest->height = PyLong_AsLong(PyDict_GetItem(pyRegionOfInterest, Py_BuildValue("s","Height")));
    pRegionOfInterest->width = PyLong_AsLong(PyDict_GetItem(pyRegionOfInterest, Py_BuildValue("s","Width")));
    pRegionOfInterest->roiId = PyLong_AsLong(PyDict_GetItem(pyRegionOfInterest, Py_BuildValue("s","ROIId")));

    PyObject * pyPoint = PyDict_GetItem(pyRegionOfInterest, Py_BuildValue("s", "Point"));
    pRegionOfInterest->point.x = PyLong_AsLong(PyDict_GetItem(pyPoint, Py_BuildValue("s","X")));
    pRegionOfInterest->point.y = PyLong_AsLong(PyDict_GetItem(pyPoint, Py_BuildValue("s","Y")));

    return pRegionOfInterest;
}

static PyObject * CreatePyQuadrilateral(Quadrilateral * pQuadrilateral)
{
    PyObject * pyQuadrilateral = PyDict_New();
    
    PyObject * pyPoints = PyList_New(4);
    for(int j = 0; j < 4; ++j)
    {
        PyObject * pyPoint = PyDict_New();

        PyObject * pyPointX = Py_BuildValue("i",pQuadrilateral->points[j].x);
        PyObject * pyPointXKey   = Py_BuildValue("s", "X");
        PyDict_SetItem(pyPoint, pyPointXKey, pyPointX);
        Py_DECREF(pyPointX);
        Py_DECREF(pyPointXKey);

        PyObject * pyPointY = Py_BuildValue("i",pQuadrilateral->points[j].y);
        PyObject * pyPointYKey   = Py_BuildValue("s", "Y");
        PyDict_SetItem(pyPoint, pyPointYKey, pyPointY);
        Py_DECREF(pyPointY);
        Py_DECREF(pyPointYKey);

        PyList_SetItem(pyPoints, j, pyPoint);
    }
    PyObject * pyPointsKey   = Py_BuildValue("s", "Points");
    PyDict_SetItem(pyQuadrilateral, pyPointsKey, pyPoints);
    Py_DECREF(pyPoints);
    Py_DECREF(pyPointsKey);

    return pyQuadrilateral;
}

Quadrilateral * CreateCQuadrilateral(PyObject * pyQuadrilateral)
{
    Quadrilateral * pQuadrilateral = (Quadrilateral *)malloc(sizeof(Quadrilateral));
                        
    PyObject * pyPoints = PyDict_GetItem(pyQuadrilateral, Py_BuildValue("s","Points"));

    for(int m = 0; m < 4; ++m)
    {
        PyObject * pyPoint = PyList_GetItem(pyPoints, m);
        pQuadrilateral->points[m].x = PyLong_AsLong(PyDict_GetItem(pyPoint, Py_BuildValue("s","X")));
        pQuadrilateral->points[m].y = PyLong_AsLong(PyDict_GetItem(pyPoint, Py_BuildValue("s","Y")));
    }
    return pQuadrilateral;
}

static PyObject * CreatePyIntermediateResultDatas(const void** ppResults, int count, IMResultDataType dataType)
{
    PyObject * pyResults = PyList_New(count);
	if (pyResults == NULL)
	{
        Py_RETURN_NONE;
	}

    if(dataType == IMRDT_IMAGE)
    {
        for(int i = 0; i < count; ++i)
        {
            PyObject * pyImageData = CreatePyImageData((ImageData *)(ppResults[i]));
            PyList_SetItem(pyResults, i, pyImageData);
        }
    }
    else if(dataType == IMRDT_CONTOUR)
    {
        for(int i = 0; i < count; ++i)
        {
            PyObject * pyContour = CreatePyContour((Contour *)(ppResults[i]));
            PyList_SetItem(pyResults, i, pyContour);
        }
    }
    else if(dataType == IMRDT_LINESEGMENT)
    {
        for(int i = 0; i < count; ++i)
        {
            PyObject * pyLineSegment = CreatePyLineSegment((LineSegment *)(ppResults[i]));
            PyList_SetItem(pyResults, i, pyLineSegment);
        }
    }
    else if(dataType == IMRDT_LOCALIZATIONRESULT)
    {
        for(int i = 0; i < count; ++i)
        {
            PyObject * pyLocalizationResult = CreatePyLocalizationResult((LocalizationResult *)(ppResults[i]));
            if(pyLocalizationResult != NULL)
            {
                PyList_SetItem(pyResults, i, pyLocalizationResult);
            }
            else
            {
                PyList_SetItem(pyResults, i, Py_None);
            }
        }  
    }
    else if(dataType == IMRDT_REGIONOFINTEREST)
    {
        for(int i = 0; i < count; ++i)
        {
            PyObject * pyRegionOfInterest = CreatePyRegionOfInterest((RegionOfInterest *)(ppResults[i]));
            PyList_SetItem(pyResults, i, pyRegionOfInterest);
        }
    }
    else if(dataType == IMRDT_QUADRILATERAL)
    {
        for(int i = 0; i < count; ++i)
        {
            PyObject * pyQuadrilateral = CreatePyQuadrilateral((Quadrilateral *)(ppResults[i]));
            PyList_SetItem(pyResults, i, pyQuadrilateral);
        }
    }
    else if(dataType == IMRDT_REFERENCE)
    {
        long long iRefs = (long long)(ppResults);
        PyObject * pyReferences = PyLong_FromLongLong(iRefs);
        PyList_SetItem(pyResults, 0, pyReferences);
        for(int i = 1; i < count; ++i)
        {
            long long iRef = (long long)(ppResults[i-1]);
            PyObject * pyReference = PyLong_FromLongLong(iRef);
            PyList_SetItem(pyResults, i, pyReference);
        }
    }

    return pyResults;
}

static PyObject * CreatePyIntermediateResult(IntermediateResult * pIntermediateResult)
{
    PyObject * pyIntermediateResult = PyDict_New();

    if(pyIntermediateResult == NULL)
    {
        Py_RETURN_NONE;
    }

    PyObject * pyDataType      = Py_BuildValue("i", pIntermediateResult->dataType);
    PyObject * pyDataTypeKey   = Py_BuildValue("s", "DataType");
    PyDict_SetItem(pyIntermediateResult, pyDataTypeKey, pyDataType);
    Py_DECREF(pyDataType);
    Py_DECREF(pyDataTypeKey);

    if(pIntermediateResult->results != NULL)
    {
        if(pIntermediateResult->dataType == IMRDT_REFERENCE)
        {
            PyObject * pyResults      = CreatePyIntermediateResultDatas(pIntermediateResult->results, pIntermediateResult->resultsCount + 1, pIntermediateResult->dataType);
            PyObject * pyResultsKey   = Py_BuildValue("s", "IMResults");
            PyDict_SetItem(pyIntermediateResult, pyResultsKey, pyResults);
            Py_DECREF(pyResults);
            Py_DECREF(pyResultsKey);
        }
        else
        {
            PyObject * pyResults      = CreatePyIntermediateResultDatas(pIntermediateResult->results, pIntermediateResult->resultsCount, pIntermediateResult->dataType);
            PyObject * pyResultsKey   = Py_BuildValue("s", "IMResults");
            PyDict_SetItem(pyIntermediateResult, pyResultsKey, pyResults);
            Py_DECREF(pyResults);
            Py_DECREF(pyResultsKey);
        }
    }
    else
    {
        PyObject * pyResultsKey   = Py_BuildValue("s", "IMResults");
        PyDict_SetItem(pyIntermediateResult, pyResultsKey, Py_None);
        Py_DECREF(pyResultsKey);
    }
    

    PyObject * pyResultType      = Py_BuildValue("i", pIntermediateResult->resultType);
    PyObject * pyResultTypeKey   = Py_BuildValue("s", "ResultType");
    PyDict_SetItem(pyIntermediateResult, pyResultTypeKey, pyResultType);
    Py_DECREF(pyResultType);
    Py_DECREF(pyResultTypeKey);

    PyObject * pyBarcodeComplementMode      = Py_BuildValue("i", pIntermediateResult->barcodeComplementMode);
    PyObject * pyBarcodeComplementModeKey   = Py_BuildValue("s", "BarcodeComplementMode");
    PyDict_SetItem(pyIntermediateResult, pyBarcodeComplementModeKey, pyBarcodeComplementMode);
    Py_DECREF(pyBarcodeComplementMode);
    Py_DECREF(pyBarcodeComplementModeKey);

    PyObject * pyBCMIndex      = Py_BuildValue("i", pIntermediateResult->bcmIndex);
    PyObject * pyBCMIndexKey   = Py_BuildValue("s", "BCMIndex");
    PyDict_SetItem(pyIntermediateResult, pyBCMIndexKey, pyBCMIndex);
    Py_DECREF(pyBCMIndex);
    Py_DECREF(pyBCMIndexKey);

    PyObject * pyDeformationResistingMode = Py_BuildValue("i", pIntermediateResult->deformationResistingMode);
    PyObject * pyDeformationResistingModeKey = Py_BuildValue("s", "DeformationResistingMode");
    PyDict_SetItem(pyIntermediateResult, pyDeformationResistingModeKey, pyDeformationResistingMode);
    Py_DECREF(pyDeformationResistingMode);
    Py_DECREF(pyDeformationResistingModeKey);

    PyObject * pyDRMIndex = Py_BuildValue("i", pIntermediateResult->bcmIndex);
    PyObject * pyDRMIndexKey = Py_BuildValue("s", "DRMIndex");
    PyDict_SetItem(pyIntermediateResult, pyDRMIndexKey, pyDRMIndex);
    Py_DECREF(pyDRMIndex);
    Py_DECREF(pyDRMIndexKey);

    PyObject * pyDPMCodeReadingMode      = Py_BuildValue("i", pIntermediateResult->dpmCodeReadingMode);
    PyObject * pyDPMCodeReadingModeKey   = Py_BuildValue("s", "DPMCodeReadingMode");
    PyDict_SetItem(pyIntermediateResult, pyDPMCodeReadingModeKey, pyDPMCodeReadingMode);
    Py_DECREF(pyDPMCodeReadingMode);
    Py_DECREF(pyDPMCodeReadingModeKey);

    PyObject * pyDPMCRMIndex      = Py_BuildValue("i", pIntermediateResult->dpmcrmIndex);
    PyObject * pyDPMCRMIndexKey   = Py_BuildValue("s", "DPMCRMIndex");
    PyDict_SetItem(pyIntermediateResult, pyDPMCRMIndexKey, pyDPMCRMIndex);
    Py_DECREF(pyDPMCRMIndex);
    Py_DECREF(pyDPMCRMIndexKey);

    PyObject * pyRotationMatrix = PyList_New(9);
    for(int j = 0; j < 9; ++j)
    {
        PyObject * temp = Py_BuildValue("d",pIntermediateResult->rotationMatrix[j]);
        PyList_SetItem(pyRotationMatrix, j, temp);
    }
    PyObject * pyRotationMatrixKey   = Py_BuildValue("s", "RotationMatrix");
    PyDict_SetItem(pyIntermediateResult, pyRotationMatrixKey, pyRotationMatrix);
    Py_DECREF(pyRotationMatrix);
    Py_DECREF(pyRotationMatrixKey);

    PyObject * pyTextFilterMode      = Py_BuildValue("i", pIntermediateResult->textFilterMode);
    PyObject * pyTextFilterModeKey   = Py_BuildValue("s", "TextFilterMode");
    PyDict_SetItem(pyIntermediateResult, pyTextFilterModeKey, pyTextFilterMode);
    Py_DECREF(pyTextFilterMode);
    Py_DECREF(pyTextFilterModeKey);

    PyObject * pyTFMIndex      = Py_BuildValue("i", pIntermediateResult->tfmIndex);
    PyObject * pyTFMIndexKey   = Py_BuildValue("s", "TFMIndex");
    PyDict_SetItem(pyIntermediateResult, pyTFMIndexKey, pyTFMIndex);
    Py_DECREF(pyTFMIndex);
    Py_DECREF(pyTFMIndexKey);

    PyObject * pyLocalizationMode      = Py_BuildValue("i", pIntermediateResult->localizationMode);
    PyObject * pyLocalizationModeKey   = Py_BuildValue("s", "LocalizationMode");
    PyDict_SetItem(pyIntermediateResult, pyLocalizationModeKey, pyLocalizationMode);
    Py_DECREF(pyLocalizationMode);
    Py_DECREF(pyLocalizationModeKey);

    PyObject * pyLMIndex      = Py_BuildValue("i", pIntermediateResult->lmIndex);
    PyObject * pyLMIndexKey   = Py_BuildValue("s", "LMIndex");
    PyDict_SetItem(pyIntermediateResult, pyLMIndexKey, pyLMIndex);
    Py_DECREF(pyLMIndex);
    Py_DECREF(pyLMIndexKey);

    PyObject * pyBinarizationMode      = Py_BuildValue("i", pIntermediateResult->binarizationMode);
    PyObject * pyBinarizationModeKey   = Py_BuildValue("s", "BinarizationMode");
    PyDict_SetItem(pyIntermediateResult, pyBinarizationModeKey, pyBinarizationMode);
    Py_DECREF(pyBinarizationMode);
    Py_DECREF(pyBinarizationModeKey);

    PyObject * pyBMIndex      = Py_BuildValue("i", pIntermediateResult->bmIndex);
    PyObject * pyBMIndexKey   = Py_BuildValue("s", "BMIndex");
    PyDict_SetItem(pyIntermediateResult, pyBMIndexKey, pyBMIndex);
    Py_DECREF(pyBMIndex);
    Py_DECREF(pyBMIndexKey);

    PyObject * pyImagePreprocessingMode      = Py_BuildValue("i", pIntermediateResult->imagePreprocessingMode);
    PyObject * pyImagePreprocessingModeKey   = Py_BuildValue("s", "ImagePreprocessingMode");
    PyDict_SetItem(pyIntermediateResult, pyImagePreprocessingModeKey, pyImagePreprocessingMode);
    Py_DECREF(pyImagePreprocessingMode);
    Py_DECREF(pyImagePreprocessingModeKey);

    PyObject * pyIPMIndex      = Py_BuildValue("i", pIntermediateResult->ipmIndex);
    PyObject * pyIPMIndexKey   = Py_BuildValue("s", "IPMIndex");
    PyDict_SetItem(pyIntermediateResult, pyIPMIndexKey, pyIPMIndex);
    Py_DECREF(pyIPMIndex);
    Py_DECREF(pyIPMIndexKey);

    PyObject * pyROIId      = Py_BuildValue("i", pIntermediateResult->roiId);
    PyObject * pyROIIdKey   = Py_BuildValue("s", "ROIId");
    PyDict_SetItem(pyIntermediateResult, pyROIIdKey, pyROIId);
    Py_DECREF(pyROIId);
    Py_DECREF(pyROIIdKey);

    PyObject * pyRegionPredetectionMode      = Py_BuildValue("i", pIntermediateResult->regionPredetectionMode);
    PyObject * pyRegionPredetectionModeKey   = Py_BuildValue("s", "RegionPredetectionMode");
    PyDict_SetItem(pyIntermediateResult, pyRegionPredetectionModeKey, pyRegionPredetectionMode);
    Py_DECREF(pyRegionPredetectionMode);
    Py_DECREF(pyRegionPredetectionModeKey);

    PyObject * pyRPMIndex      = Py_BuildValue("i", pIntermediateResult->rpmIndex);
    PyObject * pyRPMIndexKey   = Py_BuildValue("s", "RPMIndex");
    PyDict_SetItem(pyIntermediateResult, pyRPMIndexKey, pyRPMIndex);
    Py_DECREF(pyRPMIndex);
    Py_DECREF(pyRPMIndexKey);

    PyObject * pyGrayscaleTransformationMode      = Py_BuildValue("i", pIntermediateResult->grayscaleTransformationMode);
    PyObject * pyGrayscaleTransformationModeKey   = Py_BuildValue("s", "GrayscaleTransformationMode");
    PyDict_SetItem(pyIntermediateResult, pyGrayscaleTransformationModeKey, pyGrayscaleTransformationMode);
    Py_DECREF(pyGrayscaleTransformationMode);
    Py_DECREF(pyGrayscaleTransformationModeKey);

    PyObject * pyGTMIndex      = Py_BuildValue("i", pIntermediateResult->gtmIndex);
    PyObject * pyGTMIndexKey   = Py_BuildValue("s", "GTMIndex");
    PyDict_SetItem(pyIntermediateResult, pyGTMIndexKey, pyGTMIndex);
    Py_DECREF(pyGTMIndex);
    Py_DECREF(pyGTMIndexKey);

    PyObject * pyColourConversionMode      = Py_BuildValue("i", pIntermediateResult->colourConversionMode);
    PyObject * pyColourConversionModeKey   = Py_BuildValue("s", "ColourConversionMode");
    PyDict_SetItem(pyIntermediateResult, pyColourConversionModeKey, pyColourConversionMode);
    Py_DECREF(pyColourConversionMode);
    Py_DECREF(pyColourConversionModeKey);

    PyObject * pyCICMIndex      = Py_BuildValue("i", pIntermediateResult->cicmIndex);
    PyObject * pyCICMIndexKey   = Py_BuildValue("s", "CICMIndex");
    PyDict_SetItem(pyIntermediateResult, pyCICMIndexKey, pyCICMIndex);
    Py_DECREF(pyCICMIndex);
    Py_DECREF(pyCICMIndexKey);

    PyObject * pyColourClusteringMode      = Py_BuildValue("i", pIntermediateResult->colourClusteringMode);
    PyObject * pyColourClusteringModeKey   = Py_BuildValue("s", "ColourClusteringMode");
    PyDict_SetItem(pyIntermediateResult, pyColourClusteringModeKey, pyColourClusteringMode);
    Py_DECREF(pyColourClusteringMode);
    Py_DECREF(pyColourClusteringModeKey);

    PyObject * pyCCMIndex      = Py_BuildValue("i", pIntermediateResult->ccmIndex);
    PyObject * pyCCMIndexKey   = Py_BuildValue("s", "CCMIndex");
    PyDict_SetItem(pyIntermediateResult, pyCCMIndexKey, pyCCMIndex);
    Py_DECREF(pyCCMIndex);
    Py_DECREF(pyCCMIndexKey);

    PyObject * pyScaleDownRatio      = Py_BuildValue("i", pIntermediateResult->scaleDownRatio);
    PyObject * pyScaleDownRatioKey   = Py_BuildValue("s", "ScaleDownRatio");
    PyDict_SetItem(pyIntermediateResult, pyScaleDownRatioKey, pyScaleDownRatio);
    Py_DECREF(pyScaleDownRatio);
    Py_DECREF(pyScaleDownRatioKey);

    PyObject * pyFrameId      = Py_BuildValue("i", pIntermediateResult->frameId);
    PyObject * pyFrameIdKey   = Py_BuildValue("s", "FrameId");
    PyDict_SetItem(pyIntermediateResult, pyFrameIdKey, pyFrameId);
    Py_DECREF(pyFrameId);
    Py_DECREF(pyFrameIdKey);

    PyObject * pyRPMColourArgumentIndex      = Py_BuildValue("i", pIntermediateResult->rpmColourArgumentIndex);
    PyObject * pyRPMColourArgumentIndexKey   = Py_BuildValue("s", "RPMColourArgumentIndex");
    PyDict_SetItem(pyIntermediateResult, pyRPMColourArgumentIndexKey, pyRPMColourArgumentIndex);
    Py_DECREF(pyRPMColourArgumentIndex);
    Py_DECREF(pyRPMColourArgumentIndexKey);

    return pyIntermediateResult;
}

IntermediateResult * CreateCIntermediateResult(PyObject * pyIntermediateResult)
{
    IntermediateResult* intermediateResult = (IntermediateResult*)malloc(sizeof(IntermediateResult));

    intermediateResult->dataType = (IMResultDataType)PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "DataType")));
    intermediateResult->resultType = (IntermediateResultType)PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "ResultType")));
    intermediateResult->barcodeComplementMode = (BarcodeComplementMode)PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "BarcodeComplementMode")));
    intermediateResult->bcmIndex = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "BCMIndex")));
    intermediateResult->binarizationMode = (BinarizationMode)PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "BinarizationMode")));
    intermediateResult->bmIndex = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "BMIndex")));
    intermediateResult->colourClusteringMode = (ColourClusteringMode)PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "ColourClusteringMode")));
    intermediateResult->ccmIndex = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "CCMIndex")));
    intermediateResult->colourConversionMode = (ColourConversionMode)PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "ColourConversionMode")));
    intermediateResult->cicmIndex = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "CICMIndex")));
    intermediateResult->deformationResistingMode = (DeformationResistingMode)PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "DeformationResistingMode")));
    intermediateResult->drmIndex = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "DRMIndex")));
    intermediateResult->dpmCodeReadingMode = (DPMCodeReadingMode)PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "DPMCodeReadingMode")));
    intermediateResult->dpmcrmIndex = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "DPMCRMIndex")));
    intermediateResult->grayscaleTransformationMode = (GrayscaleTransformationMode)PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "GrayscaleTransformationMode")));
    intermediateResult->gtmIndex = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "GTMIndex")));
    intermediateResult->imagePreprocessingMode = (ImagePreprocessingMode)PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "ImagePreprocessingMode")));
    intermediateResult->ipmIndex = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "IPMIndex")));
    intermediateResult->localizationMode = (LocalizationMode)PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "LocalizationMode")));
    intermediateResult->lmIndex = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "LMIndex")));
    intermediateResult->regionPredetectionMode = (RegionPredetectionMode)PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "RegionPredetectionMode")));
    intermediateResult->rpmIndex = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "RPMIndex")));
    intermediateResult->textFilterMode = (TextFilterMode)PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "TextFilterMode")));
    intermediateResult->tfmIndex = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "TFMIndex")));
    
    intermediateResult->roiId = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "ROIId")));
    intermediateResult->scaleDownRatio = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "ScaleDownRatio")));
    intermediateResult->frameId = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "FrameId")));
    intermediateResult->rpmColourArgumentIndex = PyLong_AsLong(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "RPMColourArgumentIndex")));
    
    for(int j = 0; j < 9; ++j)
    {
        intermediateResult->rotationMatrix[j] = PyFloat_AsDouble(PyList_GetItem(PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "RotationMatrix")), j));
    }

    PyObject * pyIMResults = PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "IMResults"));
    int resultsCount = (int)PyList_Size(pyIMResults);

    if(resultsCount != 0)
    {
        PyObject * pyIMResults = PyDict_GetItem(pyIntermediateResult, Py_BuildValue("s", "IMResults"));
        if(intermediateResult->dataType != IMRDT_REFERENCE)
        {
            intermediateResult->resultsCount = resultsCount;
            intermediateResult->results = malloc(sizeof(void*)*resultsCount);
            for(int j = 0; j < resultsCount; ++j)
            {
                if(intermediateResult->dataType == IMRDT_IMAGE)
                {
                    PyObject * pyImageData = PyList_GetItem(pyIMResults, j);
                    ImageData* pImageData = CreateCImageData(pyImageData);
                    intermediateResult->results[j] = (void*)pImageData;
                }
                else if(intermediateResult->dataType == IMRDT_CONTOUR)
                {
                    PyObject * pyContour = PyList_GetItem(pyIMResults, j);
                    Contour* pContour = CreateCContour(pyContour);
                    intermediateResult->results[j] = (void*)pContour;
                }
                else if(intermediateResult->dataType == IMRDT_LINESEGMENT)
                {
                    PyObject * pyLineSegment = PyList_GetItem(pyIMResults, j);
                    LineSegment* pLineSegment = CreateCLineSegment(pyLineSegment);
                    intermediateResult->results[j] = (void*)pLineSegment;
                }
                else if(intermediateResult->dataType == IMRDT_LOCALIZATIONRESULT)
                {
                    PyObject * pyLocalizationResult = PyList_GetItem(pyIMResults, j);
                    LocalizationResult* pLocalizationResult = CreateCLocalizationResult(pyLocalizationResult);
                    intermediateResult->results[j] = (void*)pLocalizationResult;
                }
                else if(intermediateResult->dataType == IMRDT_REGIONOFINTEREST)
                {
                    PyObject * pyRegionOfInterest = PyList_GetItem(pyIMResults, j);
                    RegionOfInterest * pRegionOfInterest = CreateCRegionOfInterest(pyRegionOfInterest);
                    intermediateResult->results[j] = (void*)pRegionOfInterest;
                }
                else if(intermediateResult->dataType == IMRDT_QUADRILATERAL)
                {
                    PyObject * pyQuadrilateral = PyList_GetItem(pyIMResults, j);
                    Quadrilateral * pQuadrilateral = CreateCQuadrilateral(pyQuadrilateral);
                    intermediateResult->results[j] = (void*)pQuadrilateral;
                }
            }
        }
        else
        {
            intermediateResult->resultsCount = resultsCount - 1;
            if(intermediateResult->dataType == IMRDT_REFERENCE)
            {
                intermediateResult->results = (const void**)PyLong_AsLongLong(PyList_GetItem(pyIMResults, 0));
                for(int j = 1; j < resultsCount; ++j)
                {
                    intermediateResult->results[j-1] = (const void*)PyLong_AsLongLong(PyList_GetItem(pyIMResults, j));
                }
            }
        }
    }
    else
    {
        intermediateResult->results = NULL;
    }
    return intermediateResult;
}

static PyObject * CreatePyIntermediateResults(IntermediateResultArray * pResults)
{
    // Get barcode results
    int count = pResults->resultsCount;

    // Create a Python object to store results
    PyObject * pyIntermediateResults = PyList_New(count);

    for(int i = 0; i < count; ++i)
    {
        PyObject * pyIntermediateResult = CreatePyIntermediateResult(pResults->results[i]);

        PyList_SetItem(pyIntermediateResults, i, pyIntermediateResult);
    }

    // DBR_FreeIntermediateResults(&pResults);

    return pyIntermediateResults;
}

IntermediateResultArray * CreateCIntermediateResults(PyObject * pyIntermediateResults)
{
    IntermediateResultArray * intermediateResultArray = (IntermediateResultArray *)malloc(sizeof(IntermediateResultArray));

    int intermediateResultCount = (int)PyList_Size(pyIntermediateResults);

    if(intermediateResultCount != 0)
    {
        intermediateResultArray->resultsCount = intermediateResultCount;
        intermediateResultArray->results = (IntermediateResult**)malloc(sizeof(IntermediateResult*)*intermediateResultCount);
        for(int i = 0; i < intermediateResultCount; ++i)
        {
            PyObject * pyIntermediateResult = PyList_GetItem(pyIntermediateResults, i);
            IntermediateResult* intermediateResult = CreateCIntermediateResult(pyIntermediateResult);
            
            intermediateResultArray->results[i] = intermediateResult;
        }
    }
    else
    {
        intermediateResultArray->resultsCount = 0;
        intermediateResultArray->results = NULL;
    }
    

    return intermediateResultArray;
} 

static PyObject * CreatePyFrameDecodingParameters(FrameDecodingParameters * pParameters)
{
    PyObject * pyParameters = PyDict_New();
    if(pyParameters == NULL)
    { 
        Py_RETURN_NONE;
    }

    PyObject * pyMaxQueueLength             = Py_BuildValue("i", pParameters->maxQueueLength);
    PyObject * pyMaxQueueLengthKey          = Py_BuildValue("s", "MaxQueueLength");
    PyDict_SetItem(pyParameters, pyMaxQueueLengthKey, pyMaxQueueLength);
    Py_DECREF(pyMaxQueueLength);
    Py_DECREF(pyMaxQueueLengthKey);

    PyObject * pyMaxResultQueueLength             = Py_BuildValue("i", pParameters->maxResultQueueLength);
    PyObject * pyMaxResultQueueLengthKey          = Py_BuildValue("s", "MaxResultQueueLength");
    PyDict_SetItem(pyParameters, pyMaxResultQueueLengthKey, pyMaxResultQueueLength);
    Py_DECREF(pyMaxResultQueueLength);
    Py_DECREF(pyMaxResultQueueLengthKey);

    PyObject * pyWidth             = Py_BuildValue("i", pParameters->width);
    PyObject * pyWidthKey          = Py_BuildValue("s", "Width");
    PyDict_SetItem(pyParameters, pyWidthKey, pyWidth);
    Py_DECREF(pyWidth);
    Py_DECREF(pyWidthKey);

    PyObject * pyHeight             = Py_BuildValue("i", pParameters->height);
    PyObject * pyHeightKey          = Py_BuildValue("s", "Height");
    PyDict_SetItem(pyParameters, pyHeightKey, pyHeight);
    Py_DECREF(pyHeight);
    Py_DECREF(pyHeightKey);

    PyObject * pyStride             = Py_BuildValue("i", pParameters->stride);
    PyObject * pyStrideKey          = Py_BuildValue("s", "Stride");
    PyDict_SetItem(pyParameters, pyStrideKey, pyStride);
    Py_DECREF(pyStride);
    Py_DECREF(pyStrideKey);

    PyObject * pyImagePixelFormat             = Py_BuildValue("i", pParameters->imagePixelFormat);
    PyObject * pyImagePixelFormatKey          = Py_BuildValue("s", "ImagePixelFormat");
    PyDict_SetItem(pyParameters, pyImagePixelFormatKey, pyImagePixelFormat);
    Py_DECREF(pyImagePixelFormat);
    Py_DECREF(pyImagePixelFormatKey);

    PyObject * pyRegionTop             = Py_BuildValue("i", pParameters->region.regionTop);
    PyObject * pyRegionTopKey          = Py_BuildValue("s", "RegionTop");
    PyDict_SetItem(pyParameters, pyRegionTopKey, pyRegionTop);
    Py_DECREF(pyRegionTop);
    Py_DECREF(pyRegionTopKey);

    PyObject * pyRegionLeft             = Py_BuildValue("i", pParameters->region.regionLeft);
    PyObject * pyRegionLeftKey          = Py_BuildValue("s", "RegionLeft");
    PyDict_SetItem(pyParameters, pyRegionLeftKey, pyRegionLeft);
    Py_DECREF(pyRegionLeft);
    Py_DECREF(pyRegionLeftKey);

    PyObject * pyRegionRight             = Py_BuildValue("i", pParameters->region.regionRight);
    PyObject * pyRegionRightKey          = Py_BuildValue("s", "RegionRight");
    PyDict_SetItem(pyParameters, pyRegionRightKey, pyRegionRight);
    Py_DECREF(pyRegionRight);
    Py_DECREF(pyRegionRightKey);

    PyObject * pyRegionBottom             = Py_BuildValue("i", pParameters->region.regionBottom);
    PyObject * pyRegionBottomKey          = Py_BuildValue("s", "RegionBottom");
    PyDict_SetItem(pyParameters, pyRegionBottomKey, pyRegionBottom);
    Py_DECREF(pyRegionBottom);
    Py_DECREF(pyRegionBottomKey);

    PyObject * pyRegionMeasuredByPercentage             = Py_BuildValue("i", pParameters->region.regionMeasuredByPercentage);
    PyObject * pyRegionMeasuredByPercentageKey          = Py_BuildValue("s", "RegionMeasuredByPercentage");
    PyDict_SetItem(pyParameters, pyRegionMeasuredByPercentageKey, pyRegionMeasuredByPercentage);
    Py_DECREF(pyRegionMeasuredByPercentage);
    Py_DECREF(pyRegionMeasuredByPercentageKey);

    PyObject * pyThreshold             = Py_BuildValue("f", pParameters->threshold);
    PyObject * pyThresholdKey          = Py_BuildValue("s", "Threshold");
    PyDict_SetItem(pyParameters, pyThresholdKey, pyThreshold);
    Py_DECREF(pyThreshold);
    Py_DECREF(pyThresholdKey);

    PyObject * pyFPS             = Py_BuildValue("i", pParameters->fps);
    PyObject * pyFPSKey          = Py_BuildValue("s", "FPS");
    PyDict_SetItem(pyParameters, pyFPSKey, pyFPS);
    Py_DECREF(pyFPS);
    Py_DECREF(pyFPSKey);

	PyObject * pyAutoFilter = Py_BuildValue("i", pParameters->autoFilter);
	PyObject * pyAutoFilterKey = Py_BuildValue("s", "AutoFilter");
	PyDict_SetItem(pyParameters, pyAutoFilterKey, pyAutoFilter);
	Py_DECREF(pyAutoFilter);
	Py_DECREF(pyAutoFilterKey);

    PyObject * pyClarityCalculationMethod = Py_BuildValue("i", pParameters->clarityCalculationMethod);
	PyObject * pyClarityCalculationMethodKey = Py_BuildValue("s", "ClarityCalculationMethod");
	PyDict_SetItem(pyParameters, pyClarityCalculationMethodKey, pyClarityCalculationMethod);
	Py_DECREF(pyClarityCalculationMethod);
	Py_DECREF(pyClarityCalculationMethodKey);

    PyObject * pyClarityFilterMode = Py_BuildValue("i", pParameters->clarityFilterMode);
	PyObject * pyClarityFilterModeKey = Py_BuildValue("s", "ClarityFilterMode");
	PyDict_SetItem(pyParameters, pyClarityFilterModeKey, pyClarityFilterMode);
	Py_DECREF(pyClarityFilterMode);
	Py_DECREF(pyClarityFilterModeKey);

    PyObject * pyDuplicateForgetTime  = Py_BuildValue("i", pParameters->duplicateForgetTime);
    PyObject * pyDuplicateForgetTimeKey = Py_BuildValue("s", "DuplicateForgetTime");
    PyDict_SetItem(pyParameters, pyDuplicateForgetTimeKey, pyDuplicateForgetTime);
    Py_DECREF(pyDuplicateForgetTime);
    Py_DECREF(pyDuplicateForgetTimeKey);

    PyObject * pyOrientation  = Py_BuildValue("i", pParameters->orientation);
    PyObject * pyOrientationKey = Py_BuildValue("s", "Orientation");
    PyDict_SetItem(pyParameters, pyOrientationKey, pyOrientation);
    Py_DECREF(pyOrientation);
    Py_DECREF(pyOrientationKey);


    return pyParameters;
}

FrameDecodingParameters CreateCFrameDecodingParameters(PyObject * pyParameters)
{
    FrameDecodingParameters parameters;
    parameters.maxQueueLength                       = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "MaxQueueLength")));
    parameters.maxResultQueueLength                 = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "MaxResultQueueLength")));
    parameters.width                                = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "Width")));
    parameters.height                               = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "Height")));
    parameters.stride                               = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "Stride")));
    parameters.imagePixelFormat                     = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "ImagePixelFormat")));
    parameters.region.regionBottom                  = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "RegionBottom")));
    parameters.region.regionLeft                    = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "RegionLeft")));
    parameters.region.regionRight                   = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "RegionRight")));
    parameters.region.regionTop                     = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "RegionTop")));
    parameters.region.regionMeasuredByPercentage    = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "RegionMeasuredByPercentage")));
    parameters.threshold                            = (float)PyFloat_AsDouble(PyDict_GetItem(pyParameters, Py_BuildValue("s", "Threshold")));
    parameters.fps                                  = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "FPS")));
	parameters.autoFilter							= PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "AutoFilter")));
	parameters.clarityCalculationMethod				= (ClarityCalculationMethod)(PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "ClarityCalculationMethod"))));
	parameters.clarityFilterMode				    = (ClarityFilterMode)(PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "ClarityFilterMode"))));
    parameters.duplicateForgetTime                  = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "DuplicateForgetTime")));
    parameters.orientation                          = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "Orientation")));
    return parameters;
}

static PyObject * CreatePyDMDLSConnectionParameters(DM_DLSConnectionParameters * pParameters)
{
    PyObject * pyParameters = PyDict_New();
    if(pyParameters == NULL)
    { 
        Py_RETURN_NONE;
    }

    PyObject * pyMainServerURL             = Py_BuildValue("s", pParameters->mainServerURL);
    PyObject * pyMainServerURLKey          = Py_BuildValue("s", "MainServerURL");
    PyDict_SetItem(pyParameters, pyMainServerURLKey, pyMainServerURL);
    Py_DECREF(pyMainServerURL);
    Py_DECREF(pyMainServerURLKey);

    PyObject * pyStandbyServerURL           = Py_BuildValue("s", pParameters->standbyServerURL);
    PyObject * pyStandbyServerURLKey        = Py_BuildValue("s", "StandbyServerURL");
    PyDict_SetItem(pyParameters, pyStandbyServerURLKey, pyStandbyServerURL);
    Py_DECREF(pyStandbyServerURL);
    Py_DECREF(pyStandbyServerURLKey);

    PyObject * pyHandshakeCode              = Py_BuildValue("s", pParameters->handshakeCode);
    PyObject * pyHandshakeCodeKey           = Py_BuildValue("s", "HandshakeCode");
    PyDict_SetItem(pyParameters, pyHandshakeCodeKey, pyHandshakeCode);
    Py_DECREF(pyHandshakeCode);
    Py_DECREF(pyHandshakeCodeKey);

    PyObject * pySessionPassword             = Py_BuildValue("s", pParameters->sessionPassword);
    PyObject * pySessionPasswordKey          = Py_BuildValue("s", "SessionPassword");
    PyDict_SetItem(pyParameters, pySessionPasswordKey, pySessionPassword);
    Py_DECREF(pySessionPassword);
    Py_DECREF(pySessionPasswordKey);

    PyObject * pyDeploymentType              = Py_BuildValue("i", pParameters->deploymentType);
    PyObject * pyDeploymentTypeKey           = Py_BuildValue("s", "DeploymentType");
    PyDict_SetItem(pyParameters, pyDeploymentTypeKey, pyDeploymentType);
    Py_DECREF(pyDeploymentType);
    Py_DECREF(pyDeploymentTypeKey);

    PyObject * pyChargeWay              = Py_BuildValue("i", pParameters->chargeWay);
    PyObject * pyChargeWayKey           = Py_BuildValue("s", "ChargeWay");
    PyDict_SetItem(pyParameters, pyChargeWayKey, pyChargeWay);
    Py_DECREF(pyChargeWay);
    Py_DECREF(pyChargeWayKey);

    PyObject * pyUUIDGenerationMethod              = Py_BuildValue("i", pParameters->UUIDGenerationMethod);
    PyObject * pyUUIDGenerationMethodKey           = Py_BuildValue("s", "UUIDGenerationMethod");
    PyDict_SetItem(pyParameters, pyUUIDGenerationMethodKey, pyUUIDGenerationMethod);
    Py_DECREF(pyUUIDGenerationMethod);
    Py_DECREF(pyUUIDGenerationMethodKey);

    PyObject * pyMaxBufferDays              = Py_BuildValue("i", pParameters->maxBufferDays);
    PyObject * pyMaxBufferDaysKey           = Py_BuildValue("s", "MaxBufferDays");
    PyDict_SetItem(pyParameters, pyMaxBufferDaysKey, pyMaxBufferDays);
    Py_DECREF(pyMaxBufferDays);
    Py_DECREF(pyMaxBufferDaysKey);

    PyObject * pyLimitedLicenseModulesCount              = Py_BuildValue("i", pParameters->limitedLicenseModulesCount);
    PyObject * pyLimitedLicenseModulesCountKey           = Py_BuildValue("s", "LimitedLicenseModulesCount");
    PyDict_SetItem(pyParameters, pyLimitedLicenseModulesCountKey, pyLimitedLicenseModulesCount);
    Py_DECREF(pyLimitedLicenseModulesCount);
    Py_DECREF(pyLimitedLicenseModulesCountKey);

    PyObject * pyLimitedLicenseModules            = PyList_New(pParameters->limitedLicenseModulesCount);
    for(int i = 0; i < pParameters->limitedLicenseModulesCount; ++i)
    {
        PyObject * tempLimitedLicenseModule            = Py_BuildValue("i", pParameters->limitedLicenseModules[i]);
        PyList_SetItem(pyLimitedLicenseModules,        i, tempLimitedLicenseModule);
    }
    PyObject * pyLimitedLicenseModulesKey         = Py_BuildValue("s", "LimitedLicenseModules");
    PyDict_SetItem(pyParameters, pyLimitedLicenseModulesKey, pyLimitedLicenseModules);
    Py_DECREF(pyLimitedLicenseModules);
    Py_DECREF(pyLimitedLicenseModulesKey);

    PyObject * pyMaxConcurrentInstanceCount              = Py_BuildValue("i", pParameters->maxConcurrentInstanceCount);
    PyObject * pyMaxConcurrentInstanceCountKey           = Py_BuildValue("s", "MaxConcurrentInstanceCount");
    PyDict_SetItem(pyParameters, pyMaxConcurrentInstanceCountKey, pyMaxConcurrentInstanceCount);
    Py_DECREF(pyMaxConcurrentInstanceCount);
    Py_DECREF(pyMaxConcurrentInstanceCountKey);

    PyObject * pyOrganizationID             = Py_BuildValue("s", pParameters->organizationID);
    PyObject * pyOrganizationIDKey          = Py_BuildValue("s", "OrganizationID");
    PyDict_SetItem(pyParameters, pyOrganizationIDKey, pyOrganizationID);
    Py_DECREF(pyOrganizationID);
    Py_DECREF(pyOrganizationIDKey);

    PyObject * pyProducts              = Py_BuildValue("i", pParameters->products);
    PyObject * pyProductsKey           = Py_BuildValue("s", "Products");
    PyDict_SetItem(pyParameters, pyProductsKey, pyProducts);
    Py_DECREF(pyProducts);
    Py_DECREF(pyProductsKey);

    return pyParameters;
}

DBRPoint CreateCPoint(PyObject *pt)
{
    DBRPoint rpoint;
    rpoint.x = PyLong_AsLong(PyDict_GetItem(pt, Py_BuildValue("s", "X")));
    rpoint.y = PyLong_AsLong(PyDict_GetItem(pt, Py_BuildValue("s", "Y")));
    return rpoint;
}

static PyObject * CreatePyPoint(DBRPoint pt)
{
    PyObject * pypoint = PyDict_New();

    PyObject * pyx     = Py_BuildValue("i", pt.x);
    PyObject * pyxKey   = Py_BuildValue("s", "X");
    PyDict_SetItem(pypoint, pyxKey, pyx);
    Py_DECREF(pyx);
    Py_DECREF(pyxKey);

    PyObject * pyPointy = Py_BuildValue("i", pt.y);
    PyObject * pyPointyKey   = Py_BuildValue("s", "Y");
    PyDict_SetItem(pypoint, pyPointyKey, pyPointy);
    Py_DECREF(pyPointy);
    Py_DECREF(pyPointyKey);

    return pypoint;
}

DM_DLSConnectionParameters CreateCDMDLSConnectionParameters(PyObject * pyParameters)
{
    DM_DLSConnectionParameters parameters;
    PyObject * pyMainServerURL = PyDict_GetItem(pyParameters, Py_BuildValue("s", "MainServerURL"));
    if(pyMainServerURL != Py_None)
    {
        parameters.mainServerURL = PyUnicode_AsUTF8(pyMainServerURL);
    }
    else
    {
        parameters.mainServerURL = NULL;
    }

    PyObject * pyStandbyServeURL = PyDict_GetItem(pyParameters, Py_BuildValue("s", "StandbyServerURL"));
    if(pyStandbyServeURL != Py_None)
    {
        parameters.standbyServerURL = PyUnicode_AsUTF8(pyStandbyServeURL);
    }
    else
    {
        parameters.standbyServerURL = NULL;
    }
    

    PyObject * pyHandshakeCode = PyDict_GetItem(pyParameters, Py_BuildValue("s", "HandshakeCode"));
    if(pyHandshakeCode != Py_None)
    {
        parameters.handshakeCode = PyUnicode_AsUTF8(pyHandshakeCode);
    }
    else
    {
        parameters.handshakeCode = NULL;
    }   

    PyObject * pySessionPassword = PyDict_GetItem(pyParameters, Py_BuildValue("s", "SessionPassword"));
    if(pySessionPassword != Py_None)
    {
        parameters.sessionPassword = PyUnicode_AsUTF8(pySessionPassword);
    }
    else
    {
        parameters.sessionPassword = NULL;
    }

    parameters.deploymentType = (DM_DeploymentType)PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "DeploymentType")));
    parameters.chargeWay = (DM_ChargeWay)PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "ChargeWay")));
    parameters.UUIDGenerationMethod = (DM_UUIDGenerationMethod)PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "UUIDGenerationMethod")));
    parameters.maxBufferDays = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "MaxBufferDays")));
    parameters.limitedLicenseModulesCount = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "LimitedLicenseModulesCount")));

    if(parameters.limitedLicenseModulesCount != 0)
    {
        parameters.limitedLicenseModules = (DM_LicenseModule*)malloc(sizeof(int) * parameters.limitedLicenseModulesCount);
        PyObject * pyLimitedLicenseModules = PyDict_GetItem(pyParameters, Py_BuildValue("s", "LimitedLicenseModules"));
        for(int i = 0; i < parameters.limitedLicenseModulesCount; ++i)
        {
            parameters.limitedLicenseModules[i] = PyLong_AsLong(PyList_GetItem(pyLimitedLicenseModules, i));
        }
    }
    else
    {
        parameters.limitedLicenseModules = NULL;
    }

    parameters.maxConcurrentInstanceCount = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "MaxConcurrentInstanceCount")));

    PyObject * pyOrganizationID = PyDict_GetItem(pyParameters, Py_BuildValue("s", "OrganizationID"));
    if(pyOrganizationID != Py_None)
    {
        parameters.organizationID = PyUnicode_AsUTF8(pyOrganizationID);
    }
    else
    {
        parameters.organizationID = NULL;
    }

    parameters.products = PyLong_AsLong(PyDict_GetItem(pyParameters, Py_BuildValue("s", "Products")));

    return parameters;
}

static PyObject * GetDBRVersion(PyObject *obj, PyObject *args)
{
	DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
	const char * version = DBR_GetVersion();
	return Py_BuildValue("s", version);
}

static PyObject * GetErrorString(PyObject *obj, PyObject *args)
{
	DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
	int errorCode = 0;
	if (!PyArg_ParseTuple(args, "i", &errorCode))
	{
		Py_RETURN_NONE;
	}

	const char* errorString = DBR_GetErrorString(errorCode);
	return Py_BuildValue("s", errorString);
}

static PyObject * InitLicense(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *pszLicense;
    if (!PyArg_ParseTuple(args, "s", &pszLicense))
    {
		Py_RETURN_NONE;
    }
	char errorBuffer[512];
    int ret = DBR_InitLicense(pszLicense,errorBuffer, 512);
    const char* errorString = DBR_GetErrorString(ret);
	if(ret == DBR_OK)
    {
        return Py_BuildValue("(i,s)", ret, errorString);
    }
    else
    {
        return Py_BuildValue("(i,s)", ret, errorBuffer);
    }
}

void FreeDMDLSConnectionParameters(DM_DLSConnectionParameters* parameters)
{
    if(parameters->limitedLicenseModules != NULL)
    {
        free(parameters->limitedLicenseModules); 
        parameters->limitedLicenseModules = NULL;
    }
}

static PyObject * InitLicenseFromDLS(PyObject * obj, PyObject *args)
{
    DynamsoftBarcodeReader * self = (DynamsoftBarcodeReader*)obj;

    PyObject * pyParameters;
    if (!PyArg_ParseTuple(args, "O", &pyParameters))
    {
		Py_RETURN_NONE;
    }

    DM_DLSConnectionParameters parameters = CreateCDMDLSConnectionParameters(pyParameters);

    char errorBuffer[512];
    int ret = DBR_InitLicenseFromDLS(&parameters, errorBuffer, 512);

    FreeDMDLSConnectionParameters(&parameters);

    const char* errorString = DBR_GetErrorString(ret);
    if(ret == DBR_OK)
    {
        return Py_BuildValue("(i,s)", ret, errorString);
    }
    else
    {
        return Py_BuildValue("(i,s)", ret, errorBuffer);
    }
}

static PyObject * InitDLSConnectionParameters(PyObject *obj, PyObject *args)
{
    DM_DLSConnectionParameters parameters;
    int errorCode = DBR_InitDLSConnectionParameters(&parameters);

    PyObject * pyParameters = CreatePyDMDLSConnectionParameters(&parameters);

    return pyParameters;
}

static PyObject * InitIntermediateResult(PyObject *obj, PyObject *args)
{
    int resultType;
    if (!PyArg_ParseTuple(args, "i", &resultType))
    {
		Py_RETURN_NONE;
    }

    IntermediateResult imResult;
    DBR_InitIntermediateResult((IntermediateResultType)resultType, &imResult);

    PyObject * pyResult = CreatePyIntermediateResult(&imResult);
    return pyResult;
}

static PyObject * SetDeviceFriendlyName(PyObject *obj, PyObject *args)
{
    char *name;
    if (!PyArg_ParseTuple(args, "s", &name))
    {
		Py_RETURN_NONE;
    }
    int ret = DBR_SetDeviceFriendlyName(name);
    return Py_BuildValue("i", ret);
}

static PyObject * TransformCoords(PyObject *obj, PyObject *args)
{
    PyObject * point;
    PyObject * matrix;
    if (!PyArg_ParseTuple(args, "OO", &point,&matrix))
    {
		Py_RETURN_NONE;
    }
    DBRPoint pt = CreateCPoint(point);

    double m[9];
    for(int j = 0; j < 9; ++j)
    {
        m[j] = PyFloat_AsDouble(PyList_GetItem(matrix, j));
    }
    DBRPoint rpt = DBR_TransformCoordinates(pt,m);
    
    return CreatePyPoint(rpt);
}

static PyObject * SetMaxConcurrentInstanceCount(PyObject *obj, PyObject *args)
{
    int v1;
    int v2;
    int v3;
    if (!PyArg_ParseTuple(args, "iii", &v1,&v2,&v3))
    {
		Py_RETURN_NONE;
    }
    DBR_SetMaxConcurrentInstanceCount(v1,v2,v3);
    Py_RETURN_NONE;
}

static PyObject * SetLicenseCachePath(PyObject *obj, PyObject *args)
{
    char *path;
    if (!PyArg_ParseTuple(args, "s", &path))
    {
		Py_RETURN_NONE;
    }
    int ret = DBR_SetLicenseCachePath(path);
    return Py_BuildValue("i", ret);
}

static PyObject * GetDeviceUUID(PyObject *obj, PyObject *args)
{
    int method;
     if (!PyArg_ParseTuple(args, "i", &method))
    {
		Py_RETURN_NONE;
    }
    char* uuid = NULL;
    int ret = DBR_GetDeviceUUID(method,&uuid);
    if(ret == 0)
    {
        PyObject *result =  Py_BuildValue("(i,s)", ret, uuid);
        DBR_FreeString(&uuid);
        return result;
    }
    else
    {
        const char* errorString = DBR_GetErrorString(ret);
        return  Py_BuildValue("(i,s)", ret, errorString);
    }
}

static PyObject * GetInstance(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
    self->hBarcode = DBR_GetInstance();
    if(self->hBarcode == NULL)
        return Py_BuildValue("i", -1);
    return Py_BuildValue("i", 0);
}

static PyObject * RecycleInstance(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
    if(self->hBarcode != NULL)
    {
        DBR_RecycleInstance(self->hBarcode);
        self->hBarcode = NULL;
    }
    Py_RETURN_NONE;
}

static PyObject * GetIdleInstancesCount(PyObject *obj, PyObject *args)
{
    int count = DBR_GetIdleInstancesCount();
    return Py_BuildValue("i", count);
}

static PyObject * GetRuntimeSettings(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    PublicRuntimeSettings settings;
    int errorCode = DBR_GetRuntimeSettings(self->hBarcode, &settings);

    PyObject * pySettings = CreatePyRuntimeSettings(settings);
	
    return pySettings;
}

static PyObject * UpdataRuntimeSettings(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
    PyObject *pyParameters;
    if (!PyArg_ParseTuple(args, "O", &pyParameters))
    {
		Py_RETURN_NONE;
    }
    
    PublicRuntimeSettings settings = CreateCRuntimeSettings(pyParameters);
    char szErrorMsgBuffer[256];
    int errorCode = DBR_UpdateRuntimeSettings(self->hBarcode, &settings, szErrorMsgBuffer, 256);
	return Py_BuildValue("(i,s)", errorCode, szErrorMsgBuffer);
}

static PyObject * ResetRuntimeSettings(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    DBR_ResetRuntimeSettings(self->hBarcode);

	Py_RETURN_NONE;
}

static PyObject * SetModeArgument(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
    char * pModesName;
    int index;
    char * pArgumentName;
    char * pArgumentValue;
    if (!PyArg_ParseTuple(args, "siss", &pModesName, &index, &pArgumentName, &pArgumentValue))
    {
		Py_RETURN_NONE;
    }
    char szErrorMsgBuffer[256];
    int errorCode = DBR_SetModeArgument(self->hBarcode, pModesName, index, pArgumentName, pArgumentValue, szErrorMsgBuffer, 256);
    return Py_BuildValue("(i,s)", errorCode, szErrorMsgBuffer);
}

static PyObject * GetModeArgument(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
    char * pModesName;
    int index;
    char * pArgumentName;
    if (!PyArg_ParseTuple(args, "sis", &pModesName, &index, &pArgumentName))
    {
		Py_RETURN_NONE;
    }
    char szErrorMsgBuffer[256];
    char pArgumentValue[512];
    int errorCode = DBR_GetModeArgument(self->hBarcode, pModesName, index, pArgumentName, pArgumentValue, 512, szErrorMsgBuffer, 256);
    if(errorCode != 0)
    {
		return Py_BuildValue("(i,s)", errorCode, szErrorMsgBuffer);
    }
    else
    {
		return Py_BuildValue("s", pArgumentValue);
    }
}

static PyObject * GetAllTextResults(PyObject *obj, PyObject *args)
{
	DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

	TextResultArray *pResults = NULL;
	DBR_GetAllTextResults(self->hBarcode, &pResults);

	if (pResults == NULL || pResults->resultsCount == 0)
	{
		Py_RETURN_NONE;
	}
	else
	{
		PyObject * pyTextResults = CreatePyTextResults(pResults);
		DBR_FreeTextResults(&pResults);
		if(pyTextResults == NULL)
		{
			Py_RETURN_NONE;
		}
		else
		{
			return pyTextResults;
		}
	}
}

static PyObject * GetAllIntermediateResults(PyObject *obj, PyObject *args)
{
	DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    if(self->pInnerIntermediateResults != NULL)
    {
        DBR_FreeIntermediateResults(&self->pInnerIntermediateResults);
    }

	IntermediateResultArray * pIResults = NULL;
	DBR_GetIntermediateResults(self->hBarcode, &pIResults);

	if (pIResults == NULL || pIResults->resultsCount == 0)
		Py_RETURN_NONE;
	else
	{
        self->pInnerIntermediateResults = pIResults;
		PyObject * pyIntermediateResults = CreatePyIntermediateResults(pIResults);
		// DBR_FreeIntermediateResults(&pIResults);
		if (pyIntermediateResults == NULL)
		{
			Py_RETURN_NONE;
		}
		else
		{
			return pyIntermediateResults;
		}
	}
}

static PyObject * DecodeFile(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *pFileName; // File name
    char *templateName = NULL;
    if (!PyArg_ParseTuple(args, "ss", &pFileName, &templateName))
    {
		Py_RETURN_NONE;
    }

    if(templateName == NULL)
    {
        templateName = "";
    }

    // Barcode detection

    int ret = DBR_DecodeFile(self->hBarcode, pFileName, templateName);
	return Py_BuildValue("i", ret);
}

static PyObject * DecodeBuffer(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    PyObject *o;
    char *templateName = NULL;
    int width, height, stride;
    int imagePixelFormat = IPF_RGB_888;
    int orientation = 0;
    if (!PyArg_ParseTuple(args, "Oiiiisi", &o, &height, &width, &stride, &imagePixelFormat, &templateName,&orientation))
		Py_RETURN_NONE;

#if defined(IS_PY3K)
    //Refer to numpy/core/src/multiarray/ctors.c
    Py_buffer *view;
    // int nd;
    PyObject *memoryview = PyMemoryView_FromObject(o);
    if (memoryview == NULL)
    {
        PyErr_Clear();
		Py_RETURN_NONE;
    }

    view = PyMemoryView_GET_BUFFER(memoryview);
    char *buffer = (char *)(view->buf);

#else

    PyObject *ao = PyObject_GetAttrString(o, "__array_struct__");

    if ((ao == NULL) || !PyCObject_Check(ao))
    {
        PyErr_SetString(PyExc_TypeError, "object does not have array interface");
		Py_RETURN_NONE;
    }

    PyArrayInterface *pai = (PyArrayInterface *)PyCObject_AsVoidPtr(ao);

    if (pai->two != 2)
    {
        PyErr_SetString(PyExc_TypeError, "object does not have array interface");
        Py_DECREF(ao);
		Py_RETURN_NONE;
    }

    // Get image information
    char *buffer = (char *)pai->data;  // The address of image data

#endif

    // Initialize Dynamsoft Barcode Reader

    if(templateName == NULL)
    {
        templateName = "";
    }
    int ret = 0;
    if(orientation == 0)
    {
        ret = DBR_DecodeBuffer(self->hBarcode, buffer, width, height, stride, imagePixelFormat, templateName);
    }
    else
    {
        ImageData data;
        data.bytes = buffer;
        data.format = (ImagePixelFormat)imagePixelFormat;
        data.width = width;
        data.height = height;
        data.stride = stride;
        data.orientation = orientation;
        ret = DBR_DecodeImageData(self->hBarcode, &data,templateName);
    }
#if defined(IS_PY3K)
	Py_DECREF(memoryview);
#else
	Py_DECREF(ao);
#endif
	return Py_BuildValue("i", ret);
}

static PyObject * DecodeBufferManually(PyObject * obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;  

    PyObject *o;
    char *templateName = NULL;
    int width, height, stride;
    int imagePixelFormat = IPF_RGB_888;
    int orientation = 0;
    if (!PyArg_ParseTuple(args, "Oiiiisi", &o, &height, &width, &stride, &imagePixelFormat, &templateName,&orientation))
		Py_RETURN_NONE;

    char * barcodeBuffer = NULL;
    if(PyByteArray_Check(o))
    {
        barcodeBuffer = PyByteArray_AsString(o);
    }
    else if(PyBytes_Check(o))
    {
        barcodeBuffer = PyBytes_AsString(o);
    }
    else
    {
        printf("The first parameter should be a byte array or bytes object.");
		Py_RETURN_NONE;
    }
    
    if(templateName == NULL)
    {
        templateName = "";
    }

    int ret = 0;
    if(orientation == 0)
    {
        ret = DBR_DecodeBuffer(self->hBarcode, barcodeBuffer, width, height, stride, imagePixelFormat, templateName);
    }
    else
    {
        ImageData data;
        data.bytes = barcodeBuffer;
        data.format = (ImagePixelFormat)imagePixelFormat;
        data.width = width;
        data.height = height;
        data.stride = stride;
        data.orientation = orientation;
        ret = DBR_DecodeImageData(self->hBarcode, &data,templateName);
    }
    
    return Py_BuildValue("i", ret);
}

static PyObject * DecodeBase64String(PyObject *obj, PyObject *args)
{
     DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *filestream = NULL;
    char *templateName = NULL;
    if (!PyArg_ParseTuple(args, "ss", &filestream, &templateName))
    {
		Py_RETURN_NONE;
    }

    if(templateName == NULL)
    {
        templateName = "";
    }
    // Barcode detection
    int ret = DBR_DecodeBase64String(self->hBarcode, filestream, templateName);
	return Py_BuildValue("i", ret);
}

static PyObject * DecodeFileStream(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    PyObject *op; 
    int fileSize;
    char *templateName = NULL;
    if (!PyArg_ParseTuple(args, "Ois", &op, &fileSize, &templateName))
    {
		Py_RETURN_NONE;
    }

    // https://docs.python.org/2/c-api/bytearray.html
    char *filestream = NULL;

    if(PyByteArray_Check(op))
    {
        filestream = PyByteArray_AsString(op);
    }
    else if(PyBytes_Check(op))
    {
        filestream = PyBytes_AsString(op);
    }
    else
    {
        printf("The first parameter should be a byte array or bytes object.");
		Py_RETURN_NONE;
    }

    if(templateName == NULL)
    {
        templateName = "";
    }
    // Barcode detection
    int ret = DBR_DecodeFileInMemory(self->hBarcode, filestream, fileSize, templateName);
	return Py_BuildValue("i", ret);
}

void FreeInnerIntermediateResult(IntermediateResult** ppResults)
{
    if (ppResults == NULL || (*ppResults) == NULL) 
    {
        return;
    }
    if ((*ppResults)->dataType == IMRDT_IMAGE) 
    {
        ImageData** pData = (ImageData**)((*ppResults)->results);
        for (int j = 0; j < (*ppResults)->resultsCount; j++) 
        {
            if (pData[j]->bytesLength > 0) {
                free(pData[j]->bytes);
                pData[j]->bytes = NULL;
            }
            free(pData[j]);
            pData[j] = NULL;
        }
        free(pData);
        pData = NULL;
    }
    else if ((*ppResults)->dataType == IMRDT_CONTOUR) 
    {
        Contour** pData = (Contour**)((*ppResults)->results);
        for (int j = 0; j < (*ppResults)->resultsCount; j++) 
        {
            if (pData[j]->pointsCount > 0) 
            {
                free(pData[j]->points);
                pData[j]->points = NULL;
            }
            free(pData[j]);
            pData[j] = NULL;
        }
        free(pData);
        pData = NULL;
    }
    else if ((*ppResults)->dataType == IMRDT_LINESEGMENT) 
    {
        LineSegment** pData = (LineSegment**)((*ppResults)->results);
        for (int j = 0; j < (*ppResults)->resultsCount; j++) 
        {
            free(pData[j]->linesConfidenceCoefficients);
            pData[j]->linesConfidenceCoefficients = NULL;
            free(pData[j]);
            pData[j] = NULL;
        }
        free(pData);
        pData = NULL;
    }
    else if ((*ppResults)->dataType == IMRDT_LOCALIZATIONRESULT) 
    {
        LocalizationResult** pData = (LocalizationResult**)((*ppResults)->results);
        for (int j = 0; j < (*ppResults)->resultsCount; j++) 
        {
            // if (pData[j]->accompanyingTextBytesLength > 0) 
            // {
            //     free(pData[j]->accompanyingTextBytes);
            //     pData[j]->accompanyingTextBytes = NULL;
            // }
            free(pData[j]);
            pData[j] = NULL;
        }
        free(pData);
        pData = NULL;
    }
    else if ((*ppResults)->dataType == IMRDT_REGIONOFINTEREST) 
    {
        RegionOfInterest** pData = (RegionOfInterest**)((*ppResults)->results);
        for (int j = 0; j < (*ppResults)->resultsCount; j++) 
        {
            free(pData[j]);
            pData[j] = NULL;
        }
        free(pData);
        pData = NULL;
    }
    else if ((*ppResults)->dataType == IMRDT_QUADRILATERAL) 
    {
        Quadrilateral** pData = (Quadrilateral**)((*ppResults)->results);
        for (int j = 0; j < (*ppResults)->resultsCount; j++) 
        {
            free(pData[j]);
            pData[j] = NULL;
        }
        free(pData);
        pData = NULL;
    }
}

void FreeInnerIntermediateResults(IntermediateResultArray ** ppResults)
{
    if (ppResults == NULL || (*ppResults) == NULL) 
    {
        return;
    }
    
    if ((*ppResults)->results == NULL) 
    {
        free(*ppResults);
        (*ppResults) = NULL;
        return;
    }
    
    for (int i = 0; i < (*ppResults)->resultsCount; i++) 
    {
        IntermediateResult* pTmp = (*ppResults)->results[i];
        FreeInnerIntermediateResult(&pTmp);
    }
    if ((*ppResults)->resultsCount > 0) 
    {
        free((*ppResults)->results);
        (*ppResults)->results = NULL;
    }
    free(*ppResults);
    (*ppResults) = NULL;
    return;
}

static PyObject * DecodeIntermediateResults(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    PyObject *pyIntermediateResults; 
    char *templateName = NULL;
    if (!PyArg_ParseTuple(args, "Os", &pyIntermediateResults, &templateName))
    {
		Py_RETURN_NONE;
    }
    if(templateName == NULL)
    {
        templateName = "";
    }
    IntermediateResultArray * intermediateResults = CreateCIntermediateResults(pyIntermediateResults);
    int ret = DBR_DecodeIntermediateResults(self->hBarcode, intermediateResults, templateName);
    FreeInnerIntermediateResults(&intermediateResults);
    return Py_BuildValue("i", ret);
}

static PyObject * GetLengthOfFrameQueue(PyObject *obj, PyObject *args)
{
	DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

	int length = DBR_GetLengthOfFrameQueue(self->hBarcode);
	return Py_BuildValue("i", length);
}

void OnTextResultCallback(int frameId, TextResultArray *pResults, void *pUser)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)pUser;
    // Get barcode results
    int count = pResults->resultsCount;
    int i = 0;

    // https://docs.python.org/2/c-api/init.html
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();

    PyObject * pyTextResults = CreatePyTextResults(pResults);
    if(pyTextResults != NULL)
    {
        PyObject * result = PyObject_CallFunction(self->py_cb_textResult, "iOO", frameId, pyTextResults, self->py_UserData);
        Py_DECREF(pyTextResults);
        if (result != NULL)
            Py_DECREF(result);
    }

    PyGILState_Release(gstate);
    /////////////////////////////////////////////

    // Release memory
    DBR_FreeTextResults(&pResults);
}

void OnIntermediateResultCallback(int frameId, IntermediateResultArray *pResults, void *pUser)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)pUser;
    // Get barcode results
    int count = pResults->resultsCount;

    // https://docs.python.org/2/c-api/init.html
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();

    PyObject * pyIntermediateResults = CreatePyIntermediateResults(pResults);
    if(pyIntermediateResults != NULL)
    {
        PyObject * result = PyObject_CallFunction(self->py_cb_intermediateResult, "iOO", frameId, pyIntermediateResults, self->py_UserData);
        Py_DECREF(pyIntermediateResults);
        if (result != NULL)
            Py_DECREF(result);
    }

    PyGILState_Release(gstate);
    /////////////////////////////////////////////

    // Release memory
    DBR_FreeIntermediateResults(&pResults);
}

void OnErrorCallback(int frameId, int errorCode, void *pUser)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)pUser;

    int i = 0;

    // https://docs.python.org/2/c-api/init.html
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();

    PyObject * result = PyObject_CallFunction(self->py_cb_errorCode, "iiO", frameId, errorCode, self->py_UserData);
    // Py_DECREF(pyErrorCode);
    if (result != NULL)
        Py_DECREF(result);

    PyGILState_Release(gstate);
}

void OnUniqueTextResultCallback(int frameId, TextResultArray *pResults, void *pUser)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)pUser;

    // https://docs.python.org/2/c-api/init.html
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();

    PyObject * pyTextResults = CreatePyTextResults(pResults);
    if(pyTextResults != NULL)
    {
        PyObject * result = PyObject_CallFunction(self->py_cb_uniqueTextResult, "iOO", frameId, pyTextResults, self->py_UserData);
        Py_DECREF(pyTextResults);
        if (result != NULL)
            Py_DECREF(result);
    }

    PyGILState_Release(gstate);
    /////////////////////////////////////////////

    // Release memory
    DBR_FreeTextResults(&pResults);
}

static PyObject * InitFrameDecodingParameters(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
    FrameDecodingParameters pSettings;
    DBR_InitFrameDecodingParameters(self->hBarcode, &pSettings);
    PyObject * frameParameters = CreatePyFrameDecodingParameters(&pSettings);
    return frameParameters;
}

static PyObject * StartVideoMode(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    PyObject *pyParameters = NULL;
    PyObject *textResultCallback = NULL;
    PyObject *intermediateResultCallback = NULL;
    PyObject *errorCodeCallback = NULL;
    PyObject *uniqueBarcodeCallback = NULL;
    PyObject *pUserData = NULL;
    char * templateName = NULL;
    if (!PyArg_ParseTuple(args, "OOs|OOOO",&pyParameters, &textResultCallback, &templateName, &intermediateResultCallback, &errorCodeCallback,&uniqueBarcodeCallback ,&pUserData))
    {
		Py_RETURN_NONE;
    }

    if(!PyDict_Check(pyParameters))
    {
        printf("the first parameter should be a dictionary.");
		Py_RETURN_NONE;
    }

    self->py_UserData = pUserData;

    if(textResultCallback != Py_None && textResultCallback != NULL)
    {
        if (!PyCallable_Check(textResultCallback))
        {
            PyErr_SetString(PyExc_TypeError, "parameter must be callable");
            Py_RETURN_NONE;
        }
        else
        {
            Py_XINCREF(textResultCallback);    /* Add a reference to new callback */
            Py_XDECREF(self->py_cb_textResult); /* Dispose of previous callback */
            self->py_cb_textResult = textResultCallback;
        }

        DBR_SetTextResultCallback(self->hBarcode, OnTextResultCallback, self);
    }

    if(intermediateResultCallback != Py_None && intermediateResultCallback != NULL)
    {
        if (!PyCallable_Check(intermediateResultCallback))
        {
            PyErr_SetString(PyExc_TypeError, "parameter must be callable");
            Py_RETURN_NONE;
        }
        else
        {
            Py_XINCREF(intermediateResultCallback);    /* Add a reference to new callback */
            Py_XDECREF(self->py_cb_intermediateResult); /* Dispose of previous callback */
            self->py_cb_intermediateResult = intermediateResultCallback;
        }

        DBR_SetIntermediateResultCallback(self->hBarcode, OnIntermediateResultCallback, self);
    }

    if(errorCodeCallback != Py_None && errorCodeCallback != NULL)
    {
        if (!PyCallable_Check(errorCodeCallback))
        {
            PyErr_SetString(PyExc_TypeError, "parameter must be callable");
            Py_RETURN_NONE;
        }
        else
        {
            Py_XINCREF(errorCodeCallback);    /* Add a reference to new callback */
            Py_XDECREF(self->py_cb_errorCode); /* Dispose of previous callback */
            self->py_cb_errorCode = errorCodeCallback;
        }

        DBR_SetErrorCallback(self->hBarcode, OnErrorCallback, self);
    }

    if(uniqueBarcodeCallback != Py_None && uniqueBarcodeCallback != NULL)
    {
        if (!PyCallable_Check(uniqueBarcodeCallback))
        {
            PyErr_SetString(PyExc_TypeError, "parameter must be callable");
            Py_RETURN_NONE;
        }
        else
        {
            Py_XINCREF(uniqueBarcodeCallback);    /* Add a reference to new callback */
            Py_XDECREF(self->py_cb_uniqueTextResult); /* Dispose of previous callback */
            self->py_cb_uniqueTextResult = uniqueBarcodeCallback;
        }

        DBR_SetUniqueBarcodeCallback(self->hBarcode, OnUniqueTextResultCallback, self);
    }

    FrameDecodingParameters parameters = CreateCFrameDecodingParameters(pyParameters);

    if(templateName == NULL)
    {
        templateName = "";
    }
    //int ret = 0;
    int ret = DBR_StartFrameDecodingEx(self->hBarcode, parameters, templateName);
    return Py_BuildValue("i", ret);
}

static PyObject * StopVideoMode(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
    printf("Stop the video mode\n");
    if (self->hBarcode)
    {
        int ret = DBR_StopFrameDecoding(self->hBarcode);
        return Py_BuildValue("i", ret);
    }

    return Py_BuildValue("i", 0);
}

static PyObject * AppendVideoFrame(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    PyObject *o;
    if (!PyArg_ParseTuple(args, "O", &o))
		Py_RETURN_NONE;

#if defined(IS_PY3K)
    //Refer to numpy/core/src/multiarray/ctors.c
    Py_buffer *view;
    PyObject *memoryview = PyMemoryView_FromObject(o);
    if (memoryview == NULL)
    {
        PyErr_Clear();
		Py_RETURN_NONE;
    }

    view = PyMemoryView_GET_BUFFER(memoryview);
    unsigned char *buffer = (unsigned char *)view->buf;
    Py_DECREF(memoryview);

#else

    PyObject *ao = PyObject_GetAttrString(o, "__array_struct__");

    if ((ao == NULL) || !PyCObject_Check(ao))
    {
        PyErr_SetString(PyExc_TypeError, "object does not have array interface");
		Py_RETURN_NONE;
    }

    PyArrayInterface *pai = (PyArrayInterface *)PyCObject_AsVoidPtr(ao);

    if (pai->two != 2)
    {
        PyErr_SetString(PyExc_TypeError, "object does not have array interface");
        Py_DECREF(ao);
		Py_RETURN_NONE;
    }

    // Get image information
    unsigned char *buffer = (unsigned char *)pai->data; // The address of image data
    Py_DECREF(ao);

#endif

    int frameId = DBR_AppendFrame(self->hBarcode, buffer);
    return Py_BuildValue("i",frameId);
}

static PyObject * InitLicenseFromLicenseContent(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *pszLicenseKey;
    char *pszLicenseContent;
    if (!PyArg_ParseTuple(args, "ss", &pszLicenseKey, &pszLicenseContent))
    {
		Py_RETURN_NONE;
    }

    int ret = DBR_InitLicenseFromLicenseContent(self->hBarcode, pszLicenseKey, pszLicenseContent);
	const char* errorString = DBR_GetErrorString(ret);
	return Py_BuildValue("(i,s)", ret, errorString);
}

static PyObject * OutputLicenseToString(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char* content = NULL;
    int ret = DBR_OutputLicenseToStringPtr(self->hBarcode, &content);
    if (ret)
    {
        return Py_BuildValue("i", ret);
    }
    else
    {
        PyObject * licenseString = Py_BuildValue("s", content);
        DBR_FreeLicenseString(&content);
        return licenseString;
    }
}

static PyObject * InitLicenseFromServer(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *pszLicenseKey, *pLicenseServer;
    if (!PyArg_ParseTuple(args, "ss", &pLicenseServer, &pszLicenseKey))
    {
		Py_RETURN_NONE;
    }

    int ret = DBR_InitLicenseFromServer(self->hBarcode, pLicenseServer, pszLicenseKey);
	const char* errorString = DBR_GetErrorString(ret);
	return Py_BuildValue("(i,s)", ret, errorString);
}

static PyObject * InitRuntimeSettingsByJsonString(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *json;
	int conflictMode;
    if (!PyArg_ParseTuple(args, "si", &json, &conflictMode))
    {
		Py_RETURN_NONE;
    }

    char errorMessage[512];
    int ret = DBR_InitRuntimeSettingsWithString(self->hBarcode, json, conflictMode, errorMessage, 512);
    return Py_BuildValue("(i,s)", ret, errorMessage);
}

static PyObject * InitRuntimeSettingsByJsonFile(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *jsonPath;
	int conflictMode;
    if (!PyArg_ParseTuple(args, "si", &jsonPath, &conflictMode))
    {
		Py_RETURN_NONE;
    }

    char errorMessage[512];
    int ret = DBR_InitRuntimeSettingsWithFile(self->hBarcode, jsonPath, conflictMode, errorMessage, 512);
	return Py_BuildValue("(i,s)", ret, errorMessage);
}

static PyObject * OutputSettingsToJsonString(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char * pContent = NULL;

    int ret = DBR_OutputSettingsToStringPtr(self->hBarcode, &pContent, "CurrentRuntimeSettings");
    PyObject * content = Py_BuildValue("s", pContent);
    DBR_FreeSettingsString(&pContent);
    return content;
}

static PyObject * OutputSettingsToJsonFile(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char * jsonPath;
    if (!PyArg_ParseTuple(args, "s", &jsonPath))
    {
		Py_RETURN_NONE;
    }

    int ret = DBR_OutputSettingsToFile(self->hBarcode, jsonPath, "CurrentRuntimeSettings");

	const char* errorString = DBR_GetErrorString(ret);
	return Py_BuildValue("(i,s)", ret, errorString);
}

static PyObject * AppendTplFileToRuntimeSettings(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *jsonPath;
    int conflictMode;
    if (!PyArg_ParseTuple(args, "si", &jsonPath, &conflictMode))
    {
		Py_RETURN_NONE;
    }

    char errorMessage[512];
    int ret = DBR_AppendTplFileToRuntimeSettings(self->hBarcode, jsonPath, conflictMode, errorMessage, 512);

    return Py_BuildValue("(i,s)", ret, errorMessage);
}

static PyObject * AppendTplStringToRuntimeSettings(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *json;
    int conflictMode;
    if (!PyArg_ParseTuple(args, "si", &json, &conflictMode))
    {
		Py_RETURN_NONE;
    }

    char errorMessage[512];
    int ret = DBR_AppendTplStringToRuntimeSettings(self->hBarcode, json, conflictMode, errorMessage, 512);

	return Py_BuildValue("(i,s)", ret, errorMessage);
}

static PyObject * GetAllTemplateNames(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    int count = DBR_GetParameterTemplateCount(self->hBarcode);
	if (count == 0)
		Py_RETURN_NONE;

    PyObject * nameList = PyList_New(count);
	if (nameList == NULL)
		Py_RETURN_NONE;
    for(int i = 0; i < count; ++i)
    {
        char templateName[256];
        DBR_GetParameterTemplateName(self->hBarcode, i, templateName, 256);
        PyObject * pyTemplateName = Py_BuildValue("s", templateName);
        PyList_SetItem(nameList, i, pyTemplateName);
    }
    return nameList;
}

static PyObject * CreateInstance(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    self->hBarcode = DBR_CreateInstance();
    Py_RETURN_NONE;
}

static PyObject * DestoryInstance(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
    if(self->hBarcode != NULL)
        DBR_DestroyInstance(self->hBarcode);
    self->hBarcode = NULL;
    Py_RETURN_NONE;
}

static PyObject * IsInstanceValid(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
    int ret = DBR_IsInstanceValid(self->hBarcode);
    return Py_BuildValue("i",ret);
}

static PyObject * GetInstancePoolStatus(PyObject *obj,PyObject *args)
{
    InstancePoolStatus ps = DBR_GetInstancePoolStatus();

    PyObject * pyParameters = PyDict_New();
    if(pyParameters == NULL)
    { 
        Py_RETURN_NONE;
    }

    PyObject * pyV1             = Py_BuildValue("i", ps.authorizedInstancesCount);
    PyObject * pyV1Key          = Py_BuildValue("s", "AuthorizedInstancesCount");
    PyDict_SetItem(pyParameters, pyV1Key, pyV1);
    Py_DECREF(pyV1);
    Py_DECREF(pyV1Key);

    PyObject * pyV2             = Py_BuildValue("i", ps.remainingInstancesCount);
    PyObject * pyV2Key          = Py_BuildValue("s", "RemainingInstancesCount");
    PyDict_SetItem(pyParameters, pyV2Key, pyV2);
    Py_DECREF(pyV2);
    Py_DECREF(pyV2Key);

    PyObject * pyV3             = Py_BuildValue("i", ps.waitingCreationInstances);
    PyObject * pyV3Key          = Py_BuildValue("s", "WaitingCreationInstances");
    PyDict_SetItem(pyParameters, pyV3Key, pyV3);
    Py_DECREF(pyV3);
    Py_DECREF(pyV3Key);

    PyObject * pyV4             = Py_BuildValue("i", ps.totalWaitOccurrences);
    PyObject * pyV4Key          = Py_BuildValue("s", "TotalWaitOccurrences");
    PyDict_SetItem(pyParameters, pyV4Key, pyV4);
    Py_DECREF(pyV4);
    Py_DECREF(pyV4Key);
    
    return pyParameters;
}

static PyMemberDef dbr_members[] = {
    {NULL}
};

static PyMethodDef dbr_methods[] = {
	{"CreateInstance",					CreateInstance,						METH_VARARGS, NULL},
	{"DestoryInstance",					DestoryInstance,					METH_VARARGS, NULL},
	{"GetDBRVersion",					GetDBRVersion,						METH_VARARGS, NULL},
	{"GetErrorString",                  GetErrorString,                     METH_VARARGS, NULL},
	{"GetAllTextResults",               GetAllTextResults,                  METH_VARARGS, NULL},
	{"GetAllIntermediateResults",       GetAllIntermediateResults,          METH_VARARGS, NULL},
	{"GetLengthOfFrameQueue",			GetLengthOfFrameQueue,				METH_VARARGS, NULL},
    {"InitLicense",                     InitLicense,                        METH_VARARGS, NULL},
    {"DecodeFile",                      DecodeFile,                         METH_VARARGS, NULL},
    {"DecodeBuffer",                    DecodeBuffer,                       METH_VARARGS, NULL},
    {"DecodeBufferManually",            DecodeBufferManually,               METH_VARARGS, NULL},
    {"StartVideoMode",                  StartVideoMode,                     METH_VARARGS, NULL},
    {"StopVideoMode",                   StopVideoMode,                      METH_VARARGS, NULL},
    {"AppendVideoFrame",                AppendVideoFrame,                   METH_VARARGS, NULL},
    {"InitLicenseFromLicenseContent",   InitLicenseFromLicenseContent,      METH_VARARGS, NULL},
    {"OutputLicenseToString",           OutputLicenseToString,              METH_VARARGS, NULL},
    {"InitLicenseFromServer",           InitLicenseFromServer,              METH_VARARGS, NULL},
    {"InitRuntimeSettingsByJsonString", InitRuntimeSettingsByJsonString,    METH_VARARGS, NULL},
    {"OutputSettingsToJsonString",      OutputSettingsToJsonString,         METH_VARARGS, NULL},
    {"InitRuntimeSettingsByJsonFile",   InitRuntimeSettingsByJsonFile,      METH_VARARGS, NULL},
    {"OutputSettingsToJsonFile",        OutputSettingsToJsonFile,           METH_VARARGS, NULL},
    {"AppendTplFileToRuntimeSettings",  AppendTplFileToRuntimeSettings,     METH_VARARGS, NULL},
    {"AppendTplStringToRuntimeSettings",AppendTplStringToRuntimeSettings,   METH_VARARGS, NULL},
    {"GetAllTemplateNames",             GetAllTemplateNames,                METH_VARARGS, NULL},
    {"DecodeFileStream",                DecodeFileStream,                   METH_VARARGS, NULL},
    {"DecodeBase64String",              DecodeBase64String,                 METH_VARARGS, NULL},
    {"GetRuntimeSettings",              GetRuntimeSettings,                 METH_VARARGS, NULL},
    {"UpdataRuntimeSettings",           UpdataRuntimeSettings,              METH_VARARGS, NULL},
    {"ResetRuntimeSettings",            ResetRuntimeSettings,               METH_VARARGS, NULL},
    {"SetModeArgument",                 SetModeArgument,                    METH_VARARGS, NULL},
    {"GetModeArgument",                 GetModeArgument,                    METH_VARARGS, NULL},
    {"InitFrameDecodingParameters",     InitFrameDecodingParameters,        METH_VARARGS, NULL},
    {"InitDLSConnectionParameters",     InitDLSConnectionParameters,        METH_VARARGS, NULL},
    {"InitLicenseFromDLS",              InitLicenseFromDLS,                 METH_VARARGS, NULL},
    {"InitIntermediateResult",          InitIntermediateResult,             METH_VARARGS, NULL},
    {"DecodeIntermediateResults",       DecodeIntermediateResults,          METH_VARARGS, NULL},
    {"GetIdleInstancesCount",           GetIdleInstancesCount,              METH_VARARGS, NULL},
    {"SetDeviceFriendlyName",           SetDeviceFriendlyName,              METH_VARARGS, NULL},
    {"TransformCoords",                 TransformCoords,                    METH_VARARGS, NULL},
    {"IsInstanceValid",                 IsInstanceValid,                    METH_VARARGS, NULL},
    {"GetInstance",                     GetInstance,                        METH_VARARGS, NULL},
    {"RecycleInstance",                 RecycleInstance,                    METH_VARARGS, NULL},
    {"SetMaxConcurrentInstanceCount",   SetMaxConcurrentInstanceCount,      METH_VARARGS, NULL},
    {"SetLicenseCachePath",             SetLicenseCachePath,                METH_VARARGS, NULL},
    {"GetDeviceUUID",                   GetDeviceUUID,                      METH_VARARGS, NULL},
    {"GetInstancePoolStatus",           GetInstancePoolStatus,              METH_VARARGS, NULL},
    {NULL,                              NULL,                               0,            NULL}
};

static PyMethodDef module_methods[] =
{
    {NULL}
};

static int DynamsoftBarcodeReader_clear(DynamsoftBarcodeReader *self)
{
    Py_XDECREF(self->py_cb_errorCode);
    Py_XDECREF(self->py_cb_intermediateResult);
    Py_XDECREF(self->py_cb_textResult);
    Py_XDECREF(self->py_cb_uniqueTextResult);
    DBR_FreeIntermediateResults(&self->pInnerIntermediateResults);
    if(self->hBarcode != NULL)
        DBR_DestroyInstance(self->hBarcode);
    self->hBarcode = NULL;
    return 0;
}

static void DynamsoftBarcodeReader_dealloc(DynamsoftBarcodeReader *self)
{
#if defined(IS_PY3K)
    DynamsoftBarcodeReader_clear(self);
    Py_TYPE(self)->tp_free((PyObject *)self);
#else
    DynamsoftBarcodeReader_clear(self);
    self->ob_type->tp_free((PyObject *)self);
#endif
}

static PyObject * DynamsoftBarcodeReader_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    DynamsoftBarcodeReader *self;

    self = (DynamsoftBarcodeReader *)type->tp_alloc(type, 0);
    if (self != NULL)
    {
        // self->hBarcode = DBR_CreateInstance();
        self->hBarcode = NULL;
        self->pInnerIntermediateResults = NULL;
        self->py_cb_errorCode = NULL;
        self->py_cb_intermediateResult = NULL;
        self->py_cb_textResult = NULL;
        self->py_cb_uniqueTextResult = NULL;
    }

    return (PyObject *)self;
}

static int DynamsoftBarcodeReader_init(DynamsoftBarcodeReader *self, PyObject *args, PyObject *kwds)
{
    return 0;
}

static PyTypeObject DynamsoftBarcodeReaderType = {
    PyVarObject_HEAD_INIT(NULL, 0) "dbr.DynamsoftBarcodeReader", /* tp_name */
    sizeof(DynamsoftBarcodeReader),                              /* tp_basicsize */
    0,                                                           /* tp_itemsize */
    (destructor)DynamsoftBarcodeReader_dealloc,                  /* tp_dealloc */
    0,                                                           /* tp_print */
    0,                                                           /* tp_getattr */
    0,                                                           /* tp_setattr */
    0,                                                           /* tp_reserved */
    0,                                                           /* tp_repr */
    0,                                                           /* tp_as_number */
    0,                                                           /* tp_as_sequence */
    0,                                                           /* tp_as_mapping */
    0,                                                           /* tp_hash  */
    0,                                                           /* tp_call */
    0,                                                           /* tp_str */
    0,                                                           /* tp_getattro */
    0,                                                           /* tp_setattro */
    0,                                                           /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,                    /*tp_flags*/
    "Dynamsoft Barcode Reader objects",                          /* tp_doc */
    0,                                                           /* tp_traverse */
    0,                                                           /* tp_clear */
    0,                                                           /* tp_richcompare */
    0,                                                           /* tp_weaklistoffset */
    0,                                                           /* tp_iter */
    0,                                                           /* tp_iternext */
    dbr_methods,                                                 /* tp_methods */
    dbr_members,                                                 /* tp_members */
    0,                                                           /* tp_getset */
    0,                                                           /* tp_base */
    0,                                                           /* tp_dict */
    0,                                                           /* tp_descr_get */
    0,                                                           /* tp_descr_set */
    0,                                                           /* tp_dictoffset */
    (initproc)DynamsoftBarcodeReader_init,                       /* tp_init */
    0,                                                           /* tp_alloc */
    DynamsoftBarcodeReader_new,                                  /* tp_new */
};

#if defined(IS_PY3K)
static int dbr_traverse(PyObject *m, visitproc visit, void *arg)
{
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int dbr_clear(PyObject *m)
{
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "dbr",
    "Extension with Dynamsoft Barcode Reader.",
    -1,
    NULL, NULL, NULL, NULL, NULL};

#define INITERROR return NULL

PyMODINIT_FUNC
PyInit_dbr(void)

#else
#define INITERROR return
void initdbr(void)
#endif
{
    if (PyType_Ready(&DynamsoftBarcodeReaderType) < 0)
        INITERROR;

#if defined(IS_PY3K)
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("dbr", module_methods);
#endif
    if (module == NULL)
        INITERROR;

    Py_INCREF(&DynamsoftBarcodeReaderType);
    PyModule_AddObject(module, "DynamsoftBarcodeReader", (PyObject *)&DynamsoftBarcodeReaderType);
#if defined(IS_PY3K)
    return module;
#endif
}
