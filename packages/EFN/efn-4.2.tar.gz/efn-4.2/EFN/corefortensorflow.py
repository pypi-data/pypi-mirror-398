import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from typing import Callable, Tuple, List, Optional

Array = np.ndarray

class Tensor:
    def __init__(self, data: Array, requiresGradient: bool = False, context=None):
        self.data = np.array(data, dtype=float)
        self.shape = self.data.shape
        self.requiresGradient = requiresGradient
        self.gradient: Optional[Array] = None
        self.context = context

    def __repr__(self):
        return f"Tensor(shape={self.shape}, requiresGradient={self.requiresGradient}, data={self.data})"

    def __add__(self, other):
        return Add.apply(self, ensureTensor(other))

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        return Multiply.apply(self, ensureTensor(other))

    def __matmul__(self, other):
        return MatrixMultiply.apply(self, ensureTensor(other))

    def sum(self):
        return Sum.apply(self)

    def relu(self):
        return ReLU.apply(self)

    def numpy(self):
        return self.data.copy()

    def backward(self, gradient: Optional[Array] = None):
        if not self.requiresGradient:
            raise RuntimeError("Called backward on a tensor that does not require gradients.")

        if gradient is None:
            if self.data.size != 1:
                raise RuntimeError("Gradient must be specified for non-scalar tensors")
            gradient = np.ones_like(self.data)

        topo = []
        visited = set()

        def build(t):
            if t not in visited:
                visited.add(t)
                if t.context:
                    for p in t.context.parents:
                        build(p)
                topo.append(t)

        build(self)
        self.gradient = gradient.copy()

        for t in reversed(topo):
            if t.context is None:
                continue
            grads = t.context.backwardFunction(t, t.gradient)
            if not isinstance(grads, tuple):
                grads = (grads,)
            for parent, g in zip(t.context.parents, grads):
                if not parent.requiresGradient:
                    continue
                if parent.gradient is None:
                    parent.gradient = g.copy()
                else:
                    parent.gradient += g

def ensureTensor(x):
    if isinstance(x, Tensor):
        return x
    return Tensor(x, requiresGradient=False)

def unbroadcast(grad, shape):
    while grad.ndim > len(shape):
        grad = grad.sum(axis=0)
    for i, s in enumerate(shape):
        if s == 1:
            grad = grad.sum(axis=i, keepdims=True)
    return grad

class Context:
    def __init__(self, parents: Tuple[Tensor, ...], backwardFunction: Callable):
        self.parents = parents
        self.backwardFunction = backwardFunction

class Function:
    @classmethod
    def apply(cls, *inputs: Tensor):
        arrays = [t.data for t in inputs]
        out, saved = cls.forward(*arrays)
        requiresGrad = any(t.requiresGradient for t in inputs)

        def backwardFunction(resultTensor, gradOutput):
            return cls.backward(resultTensor.data, gradOutput, saved, *inputs)

        context = Context(inputs, backwardFunction)
        return Tensor(out, requiresGrad, context)

    @staticmethod
    def forward(*arrays):
        raise NotImplementedError

    @staticmethod
    def backward(resultData, gradOutput, savedContext, *inputs):
        raise NotImplementedError

class Add(Function):
    @staticmethod
    def forward(a, b):
        return a + b, {}

    @staticmethod
    def backward(resultData, gradOutput, _, a, b):
        return unbroadcast(gradOutput, a.shape), unbroadcast(gradOutput, b.shape)

class Multiply(Function):
    @staticmethod
    def forward(a, b):
        return a * b, {}

    @staticmethod
    def backward(resultData, gradOutput, _, a, b):
        return (
            unbroadcast(gradOutput * b.data, a.shape),
            unbroadcast(gradOutput * a.data, b.shape),
        )


class MatrixMultiply(Function):
    @staticmethod
    def forward(a, b):
        return a @ b, {}

    @staticmethod
    def backward(resultData, gradOutput, _, a, b):
        return gradOutput @ b.data.T, a.data.T @ gradOutput

class Sum(Function):
    @staticmethod
    def forward(a):
        return np.array(a.sum()), {"shape": a.shape}

    @staticmethod
    def backward(resultData, gradOutput, saved, a):
        return np.ones(saved["shape"]) * gradOutput

class ReLU(Function):
    @staticmethod
    def forward(a):
        return np.maximum(0, a), {"mask": a > 0}

    @staticmethod
    def backward(resultData, gradOutput, saved, a):
        return gradOutput * saved["mask"]

def tensor(data, requiresGradient=False):
    return Tensor(np.array(data), requiresGradient=requiresGradient)

def randn(shape, requiresGradient=False):
    return Tensor(np.random.randn(*shape), requiresGradient=requiresGradient)

def zeros(shape, requiresGradient=False):
    return Tensor(np.zeros(shape), requiresGradient=requiresGradient)

def loadfromhub(toload):
    return hub.load(toload)

def converttotensor(value, dtype=None, dtypehint=None, name=None):
    return tf.convert_to_tenssor(value, dtype=dtype, dtype_hint=dtypehint, name=name)

def clipbyvalue(tensor, minimum, maximum, name=None):
    return tf.clip_by_value(tensor, minimum, maximum, name=name)

class FixedLenFeatureClass(tf.io.FixedLenFeature):
    def __init__(self, shape, dtype, defaultvalue=None):
        super().__init__(shape, dtype, defaultvalue)

class FixedLenSequenceFeatureClass(tf.io.FixedLenSequenceFeature):
    def __init__(self, shape, dtype, allowmissing=False, defaultvalue=None):
        super().__init__(shape, dtype, allowmissing, defaultvalue)

class RaggedFeatureClass(tf.io.RaggedFeature):
    def __init__(self, dtype, valueshape=None, partitions=None, rowsplitsdtype=tf.dtypes.int64):
        super().__init__(dtype, valueshape, partitions, rowsplitsdtype)

class SparseFeatureClass(tf.io.SparseFeature):
    def __init__(self, indexkey, valuekey, dtype, size, alreadysorted=False):
        super().__init__(indexkey, valuekey, dtype, size, alreadysorted)

class VarLenFeatureClass(tf.io.VarLenFeature):
    def __init__(self, dtype):
        super().__init__(dtype)

class TfRecordOptionsClass(tf.io.TFRecordOptions):
    def __init__(self, compressiontype=None):
        super().__init__(compressiontype)

class TfRecordWriterClass(tf.io.TFRecordWriter):
    def __init__(self, filename, options=None):
        super().__init__(filename, options)

def decodeAndCropJpeg(contents, cropwindow, channels=0, dctmethod="", fancyupscaling=True, tryrecovertruncated=False, acceptablefraction=1, ratio=1):
    return tf.io.decode_and_crop_jpeg(contents, cropwindow, channels, dctmethod, fancyupscaling, tryrecovertruncated, acceptablefraction, ratio)

def decodeBase64(input, dtype=tf.dtypes.string):
    return tf.io.decode_base64(input, dtype)

def decodeBmp(contents):
    return tf.io.decode_bmp(contents)

def decodeCompressed(contents, compressiontype="", dtype=tf.dtypes.string):
    return tf.io.decode_compressed(contents, compressiontype, dtype)

def decodeCsv(records, recorddefaults, fielddelim=",", usequotedelim=True, navalue="", selectcols=None):
    return tf.io.decode_csv(records, recorddefaults, fielddelim, usequotedelim, navalue, selectcols)

def decodeGif(contents):
    return tf.io.decode_gif(contents)

def decodeImage(contents, channels=None, dtype=tf.dtypes.uint8, expandanimations=True):
    return tf.io.decode_image(contents, channels, dtype, expandanimations)

def decodeJpeg(contents, channels=0, dctmethod="", fancyupscaling=True, tryrecovertruncated=False, acceptablefraction=1, ratio=1):
    return tf.io.decode_jpeg(contents, channels, dctmethod, fancyupscaling, tryrecovertruncated, acceptablefraction, ratio)

def decodeJsonExample(jsonexamples):
    return tf.io.decode_json_example(jsonexamples)

def decodePng(contents, channels=0, dtype=tf.dtypes.uint8):
    return tf.io.decode_png(contents, channels, dtype)

def decodeProto(serialized, messagetype, fieldnames=None, fieldtypes=None, descriptorsource="local://", messageformat="binary", sanitize=False):
    return tf.io.decode_proto(serialized, messagetype, fieldnames, fieldtypes, descriptorsource, messageformat, sanitize)

def decodeRaw(bytes, outtype, littleendian=True, fixedlength=None):
    return tf.io.decode_raw(bytes, outtype, littleendian, fixedlength)

def deserializeManySparse(serializedsparse, dtype, rank=None):
    return tf.io.deserialize_many_sparse(serializedsparse, dtype, rank)

def encodeBase64(input, pad=False):
    return tf.io.encode_base64(input, pad)

def encodeJpeg(image, format="", quality=95, progressive=False, optimizesize=False, chromadownsampling=True, densityunit="in", xdensity=300, ydensity=300, xmpmetadata=""):
    return tf.io.encode_jpeg(image, format, quality, progressive, optimizesize, chromadownsampling, densityunit, xdensity, ydensity, xmpmetadata)

def encodePng(image, compression=-1):
    return tf.io.encode_png(image, compression)

def encodeProto(sizes, values, fieldnames, messagetype, descriptorsource="local://", messageformat="binary"):
    return tf.io.encode_proto(sizes, values, fieldnames, messagetype, descriptorsource, messageformat)

def extractJpegShape(contents):
    return tf.io.extract_jpeg_shape(contents)

def isJpeg(contents):
    return tf.io.is_jpeg(contents)

def matchFilenamesOnce(pattern):
    return tf.io.match_filenames_once(pattern)

def matchingFiles(pattern):
    return tf.io.matching_files(pattern)

def parseExample(serialized, features, examplenames=None):
    return tf.io.parse_example(serialized, features, examplenames)

def parseSequenceExample(serialized, contextfeatures=None, sequencefeatures=None, examplename=None):
    return tf.io.parse_sequence_example(serialized, contextfeatures, sequencefeatures, examplename)

def parseSingleExample(serialized, features, examplename=None):
    return tf.io.parse_single_example(serialized, features, examplename)

def parseSingleSequenceExample(serialized, contextfeatures=None, sequencefeatures=None, examplename=None):
    return tf.io.parse_single_sequence_example(serialized, contextfeatures, sequencefeatures, examplename)

def parseTensor(serialized, outtype):
    return tf.io.parse_tensor(serialized, outtype)

def readFile(filename, name=None):
    return tf.io.read_file(filename, name)

def serializeManySparse(spinput, outtype):
    return tf.io.serialize_many_sparse(spinput, outtype)

def serializeSparse(spinput):
    return tf.io.serialize_sparse(spinput)

def serializeTensor(tensor):
    return tf.io.serialize_tensor(tensor)

def writeFile(filename, contents, name=None):
    return tf.io.write_file(filename, contents, name)

def writeGraph(graphdef, directory, name, astext=True):
    return tf.io.write_graph(graphdef, directory, name, astext)

sysioConst = tf.io._sys
gfileConst = tf.io.gfile

class InputClass(tf.keras.layers.InputLayer):
    def __init__(self, shape=None, batchsize=None, name=None, dtype=None, sparse=None, tensor=None, ragged=None):
        super().__init__(input_shape=shape, batch_size=batchsize, name=name, dtype=dtype, sparse=sparse, input_tensor=tensor, ragged=ragged)

class ModelClass(tf.keras.Model):
    def __init__(self, inputs, outputs, name=None):
        super().__init__(inputs=inputs, outputs=outputs, name=name)

class SequentialClass(tf.keras.Sequential):
    def __init__(self, layers=None, name=None):
        super().__init__(layers=layers, name=name)

activationsConst = tf.keras.activations
applicationsConst = tf.keras.applications
backendConst = tf.keras.backend
callbacksConst = tf.keras.callbacks
constraintsConst = tf.keras.constraints
datasetsConst = tf.keras.datasets
dtensorConst = tf.keras.dtensor
estimatorConst = tf.keras.estimator
experimentalConst = tf.keras.experimental
exportConst = tf.keras.export
initializersConst = tf.keras.initializers
layersConst = tf.keras.layers
lossesConst = tf.keras.losses
metricsConst = tf.keras.metrics
mixedPrecisionConst = tf.keras.mixed_precision
modelsConst = tf.keras.models
optimizersConst = tf.keras.optimizers
preprocessingConst = tf.keras.preprocessing
regularizersConst = tf.keras.regularizers
savingConst = tf.keras.saving
utilsConst = tf.keras.utils

resizeMethodConst = tf.image.ResizeMethod

def adjustBrightness(image, delta):
    return tf.image.adjust_brightness(image, delta)

def adjustContrast(image, contrastFactor, minValue=None, maxValue=None):
    if minValue is None and maxValue is None:
        return tf.image.adjust_contrast(image, contrastFactor)
    return tf.image.adjust_contrast(image, contrastFactor, minValue, maxValue)

def adjustGamma(image, gamma, gain=1.0):
    return tf.image.adjust_gamma(image, gamma, gain)

def adjustHue(image, delta):
    return tf.image.adjust_hue(image, delta)

def adjustJpegQuality(contents, jpegQuality):
    return tf.image.adjust_jpeg_quality(contents, jpegQuality)

def adjustSaturation(image, saturationFactor):
    return tf.image.adjust_saturation(image, saturationFactor)

def centralCrop(image, centralFraction):
    return tf.image.central_crop(image, centralFraction)

def combinedNonMaxSuppression(boxes, scores, maxOutputSizePerClass, maxTotalSize, iouThreshold=0.5, scoreThreshold=float("-inf"), padPerClass=False, clipBoxes=True, name=None):
    return tf.image.combined_non_max_suppression(boxes, scores, maxOutputSizePerClass, maxTotalSize, iouThreshold, scoreThreshold, padPerClass, clipBoxes, name)

def convertImageDtype(image, dtype, saturate=False):
    return tf.image.convert_image_dtype(image, dtype, saturate)

def cropAndResize(image, boxes, boxInd, cropSize, method="bilinear", extrapolationValue=0):
    return tf.image.crop_and_resize(image, boxes, boxInd, cropSize, method, extrapolationValue)

def cropToBoundingBox(image, offsetHeight, offsetWidth, targetHeight, targetWidth):
    return tf.image.crop_to_bounding_box(image, offsetHeight, offsetWidth, targetHeight, targetWidth)

def decodeAndCropJpeg(contents, cropWindow, channels=0, dctMethod=""):
    return tf.image.decode_and_crop_jpeg(contents, cropWindow, channels, dctMethod)

def decodeBmp(contents):
    return tf.image.decode_bmp(contents)

def decodeGif(contents):
    return tf.image.decode_gif(contents)

def decodeImage(contents, channels=None, dtype=tf.dtypes.uint8, expandAnimations=True):
    return tf.image.decode_image(contents, channels, dtype, expandAnimations)

def decodeJpeg(contents, channels=0, ratio=1, fancyUpscaling=True, tryRecoverTruncated=False, acceptableFraction=1.0, dctMethod=""):
    return tf.image.decode_jpeg(contents, channels, ratio, fancyUpscaling, tryRecoverTruncated, acceptableFraction, dctMethod)

def decodePng(contents, channels=0, dtype=tf.dtypes.uint8):
    return tf.image.decode_png(contents, channels, dtype)

def drawBoundingBoxes(images, boxes):
    return tf.image.draw_bounding_boxes(images, boxes)

def encodeJpeg(image, format=None, quality=95, progressive=False, optimizeSize=False, chromaDownsampling=True, densityUnit="in", xDensity=300, yDensity=300, xmpMetadata=""):
    return tf.image.encode_jpeg(image, format, quality, progressive, optimizeSize, chromaDownsampling, densityUnit, xDensity, yDensity, xmpMetadata)

def encodePng(image, compression=-1):
    return tf.image.encode_png(image, compression)

def extractGlimpse(input, size, offsets, centered=True, normalized=True, uniformNoise=True, name=None):
    return tf.image.extract_glimpse(input, size, offsets, centered, normalized, uniformNoise, name)

def extractJpegShape(contents):
    return tf.image.extract_jpeg_shape(contents)

def extractPatches(images, sizes, strides, rates, padding):
    return tf.image.extract_patches(images, sizes, strides, rates, padding)

def flipLeftRight(image):
    return tf.image.flip_left_right(image)

def flipUpDown(image):
    return tf.image.flip_up_down(image)

def generateBoundingBoxProposals(boxes, scores, imageShape, maxOutputSize=1000, iouThreshold=0.5, scoreThreshold=0.0):
    return tf.image.generate_bounding_box_proposals(boxes, scores, imageShape, maxOutputSize, iouThreshold, scoreThreshold)

def grayscaleToRgb(image):
    return tf.image.grayscale_to_rgb(image)

def hsvToRgb(hsv):
    return tf.image.hsv_to_rgb(hsv)

def imageGradients(image):
    return tf.image.image_gradients(image)

def isJpeg(contents):
    return tf.image.is_jpeg(contents)

def nonMaxSuppression(boxes, scores, maxOutputSize, iouThreshold=0.5, scoreThreshold=float("-inf"), name=None):
    return tf.image.non_max_suppression(boxes, scores, maxOutputSize, iouThreshold, scoreThreshold, name)

def nonMaxSuppressionOverlaps(boxes, scores, maxOutputSize, iouThreshold=0.5, scoreThreshold=float("-inf"), name=None):
    return tf.image.non_max_suppression_overlaps(boxes, scores, maxOutputSize, iouThreshold, scoreThreshold, name)

def nonMaxSuppressionPadded(boxes, scores, maxOutputSize, iouThreshold=0.5, scoreThreshold=float("-inf"), padToMaxOutputSize=False, name=None):
    return tf.image.non_max_suppression_padded(boxes, scores, maxOutputSize, iouThreshold, scoreThreshold, padToMaxOutputSize, name)

def nonMaxSuppressionWithScores(boxes, scores, maxOutputSize, iouThreshold=0.5, scoreThreshold=float("-inf"), softNmsSigma=0.0, name=None):
    return tf.image.non_max_suppression_with_scores(boxes, scores, maxOutputSize, iouThreshold, scoreThreshold, softNmsSigma, name)

def padToBoundingBox(image, offsetHeight, offsetWidth, targetHeight, targetWidth):
    return tf.image.pad_to_bounding_box(image, offsetHeight, offsetWidth, targetHeight, targetWidth)

def perImageStandardization(image):
    return tf.image.per_image_standardization(image)

def psnr(image1, image2, maxVal):
    return tf.image.psnr(image1, image2, maxVal)

def randomBrightness(image, maxDelta):
    return tf.image.random_brightness(image, maxDelta)

def randomContrast(image, lower, upper):
    return tf.image.random_contrast(image, lower, upper)

def randomCrop(value, size):
    return tf.image.random_crop(value, size)

def randomFlipLeftRight(image):
    return tf.image.random_flip_left_right(image)

def randomFlipUpDown(image):
    return tf.image.random_flip_up_down(image)

def randomHue(image, maxDelta):
    return tf.image.random_hue(image, maxDelta)

def randomJpegQuality(contents, minJpegQuality, maxJpegQuality):
    return tf.image.random_jpeg_quality(contents, minJpegQuality, maxJpegQuality)

def randomSaturation(image, lower, upper):
    return tf.image.random_saturation(image, lower, upper)

def resize(images, size, method=tf.image.ResizeMethod.BILINEAR, preserveAspectRatio=False, antialias=False, name=None):
    return tf.image.resize(images, size, method, preserveAspectRatio, antialias, name)

def resizeWithCropOrPad(image, targetHeight, targetWidth):
    return tf.image.resize_with_crop_or_pad(image, targetHeight, targetWidth)

def resizeWithPad(image, targetHeight, targetWidth, method=tf.image.ResizeMethod.BILINEAR, antialias=False):
    return tf.image.resize_with_pad(image, targetHeight, targetWidth, method, antialias)

def rgbToGrayscale(images):
    return tf.image.rgb_to_grayscale(images)

def rgbToHsv(images):
    return tf.image.rgb_to_hsv(images)

def rgbToYiq(images):
    return tf.image.rgb_to_yiq(images)

def rgbToYuv(images):
    return tf.image.rgb_to_yuv(images)

def rot90(image, k=1, name=None):
    return tf.image.rot90(image, k, name)

def sampleDistortedBoundingBox(imageSize, boundingBoxes, minObjectCovered=0.1, aspectRatioRange=(0.75,1.33), areaRange=(0.05,1.0), maxAttempts=100, useImageIfNoBoundingBoxes=True, seed=None, name=None):
    return tf.image.sample_distorted_bounding_box(imageSize, boundingBoxes, minObjectCovered, aspectRatioRange, areaRange, maxAttempts, useImageIfNoBoundingBoxes, seed, name)

def sobelEdges(images):
    return tf.image.sobel_edges(images)

def ssim(img1, img2, maxVal, filterSize=11, filterSigma=1.5, k1=0.01, k2=0.03):
    return tf.image.ssim(img1, img2, maxVal, filterSize, filterSigma, k1, k2)

def ssimMultiscale(img1, img2, maxVal, powerFactors=None, filterSize=11, filterSigma=1.5, k1=0.01, k2=0.03):
    return tf.image.ssim_multiscale(img1, img2, maxVal, powerFactors, filterSize, filterSigma, k1, k2)

def statelessRandomBrightness(image, maxDelta, seed):
    return tf.image.stateless_random_brightness(image, maxDelta, seed)

def statelessRandomContrast(image, lower, upper, seed):
    return tf.image.stateless_random_contrast(image, lower, upper, seed)

def statelessRandomCrop(value, size, seed):
    return tf.image.stateless_random_crop(value, size, seed)

def statelessRandomFlipLeftRight(image, seed):
    return tf.image.stateless_random_flip_left_right(image, seed)

def statelessRandomFlipUpDown(image, seed):
    return tf.image.stateless_random_flip_up_down(image, seed)

def statelessRandomHue(image, maxDelta, seed):
    return tf.image.stateless_random_hue(image, maxDelta, seed)

def statelessRandomJpegQuality(contents, minJpegQuality, maxJpegQuality, seed):
    return tf.image.stateless_random_jpeg_quality(contents, minJpegQuality, maxJpegQuality, seed)

def statelessRandomSaturation(image, lower, upper, seed):
    return tf.image.stateless_random_saturation(image, lower, upper, seed)

def statelessSampleDistortedBoundingBox(imageSize, boundingBoxes, minObjectCovered=0.1, aspectRatioRange=(0.75,1.33), areaRange=(0.05,1.0), maxAttempts=100, useImageIfNoBoundingBoxes=True, seed=None, name=None):
    return tf.image.stateless_sample_distorted_bounding_box(imageSize, boundingBoxes, minObjectCovered, aspectRatioRange, areaRange, maxAttempts, useImageIfNoBoundingBoxes, seed, name)

def totalVariation(image):
    return tf.image.total_variation(image)

def transpose(image, perm):
    return tf.image.transpose(image, perm)

def yiqToRgb(yiq):
    return tf.image.yiq_to_rgb(yiq)

def yuvToRgb(yuv):
    return tf.image.yuv_to_rgb(yuv)

def mathmod(x, y, name=None):
    return tf.math.mod(x, y, name=name)

sysimgConst = tf.image._sys
newaxis = tf.newaxis

def absVal(x, name=None):
    return tf.math.abs(x, name=name)

def accumulateN(inputs, shape=None, dtype=None, name=None):
    return tf.math.accumulate_n(inputs, shape=shape, dtype=dtype, name=name)

def acosVal(x, name=None):
    return tf.math.acos(x, name=name)

def acoshVal(x, name=None):
    return tf.math.acosh(x, name=name)

def addVal(x, y, name=None):
    return tf.math.add(x, y, name=name)

def addN(inputs, name=None):
    return tf.math.add_n(inputs, name=name)

def angleVal(x, name=None):
    return tf.math.angle(x, name=name)

def approxMaxK(input, k, sorted=True, name=None):
    return tf.math.approx_max_k(input, k, sorted=sorted, name=name)

def approxMinK(input, k, sorted=True, name=None):
    return tf.math.approx_min_k(input, k, sorted=sorted, name=name)

def argMax(input, axis=None, output_type=tf.int64, name=None):
    return tf.math.argmax(input, axis=axis, output_type=output_type, name=name)

def argMin(input, axis=None, output_type=tf.int64, name=None):
    return tf.math.argmin(input, axis=axis, output_type=output_type, name=name)

def asinVal(x, name=None):
    return tf.math.asin(x, name=name)

def asinhVal(x, name=None):
    return tf.math.asinh(x, name=name)

def atanVal(x, name=None):
    return tf.math.atan(x, name=name)

def atan2Val(y, x, name=None):
    return tf.math.atan2(y, x, name=name)

def atanhVal(x, name=None):
    return tf.math.atanh(x, name=name)

def besselI0(x, name=None):
    return tf.math.bessel_i0(x, name=name)

def besselI0e(x, name=None):
    return tf.math.bessel_i0e(x, name=name)

def besselI1(x, name=None):
    return tf.math.bessel_i1(x, name=name)

def besselI1e(x, name=None):
    return tf.math.bessel_i1e(x, name=name)

def betainc(a, b, x, name=None):
    return tf.math.betainc(a, b, x, name=name)

def bincount(values, weights=None, minlength=None, dtype=tf.int32, name=None):
    return tf.math.bincount(values, weights=weights, minlength=minlength, dtype=dtype, name=name)

def ceilVal(x, name=None):
    return tf.math.ceil(x, name=name)

def confusionMatrix(labels, predictions, numClasses=None, weights=None, dtype=tf.int32, name=None):
    return tf.math.confusion_matrix(labels, predictions, num_classes=numClasses, weights=weights, dtype=dtype, name=name)

def conjVal(x, name=None):
    return tf.math.conj(x, name=name)

def cosVal(x, name=None):
    return tf.math.cos(x, name=name)

def coshVal(x, name=None):
    return tf.math.cosh(x, name=name)

def countNonzero(x, axis=None, keepdims=False, dtype=tf.int64, name=None):
    return tf.math.count_nonzero(x, axis=axis, keepdims=keepdims, dtype=dtype, name=name)

def cumprodVal(x, axis=0, exclusive=False, reverse=False, name=None):
    return tf.math.cumprod(x, axis=axis, exclusive=exclusive, reverse=reverse, name=name)

def cumsumVal(x, axis=0, exclusive=False, reverse=False, name=None):
    return tf.math.cumsum(x, axis=axis, exclusive=exclusive, reverse=reverse, name=name)

def cumulativeLogsumexp(x, axis=None, exclusive=False, reverse=False, name=None):
    return tf.math.cumulative_logsumexp(x, axis=axis, exclusive=exclusive, reverse=reverse, name=name)

def digammaVal(x, name=None):
    return tf.math.digamma(x, name=name)

def divideVal(x, y, name=None):
    return tf.math.divide(x, y, name=name)

def divideNoNan(x, y, name=None):
    return tf.math.divide_no_nan(x, y, name=name)

def equalVal(x, y, name=None):
    return tf.math.equal(x, y, name=name)

def erfVal(x, name=None):
    return tf.math.erf(x, name=name)

def erfcVal(x, name=None):
    return tf.math.erfc(x, name=name)

def erfcinvVal(x, name=None):
    return tf.math.erfcinv(x, name=name)

def erfinvVal(x, name=None):
    return tf.math.erfinv(x, name=name)

def expVal(x, name=None):
    return tf.math.exp(x, name=name)

def expm1Val(x, name=None):
    return tf.math.expm1(x, name=name)

def floorVal(x, name=None):
    return tf.math.floor(x, name=name)

def floorDiv(x, y, name=None):
    return tf.math.floordiv(x, y, name=name)

def floorMod(x, y, name=None):
    return tf.math.floormod(x, y, name=name)

def greaterVal(x, y, name=None):
    return tf.math.greater(x, y, name=name)

def greaterEqualVal(x, y, name=None):
    return tf.math.greater_equal(x, y, name=name)

def igammaVal(a, x, name=None):
    return tf.math.igamma(a, x, name=name)

def igammacVal(a, x, name=None):
    return tf.math.igammac(a, x, name=name)

def imagVal(x, name=None):
    return tf.math.imag(x, name=name)

def inTopK(predictions, targets, k):
    return tf.math.in_top_k(predictions, targets, k)

def invertPermutation(p, name=None):
    return tf.math.invert_permutation(p, name=name)

def isFinite(x, name=None):
    return tf.math.is_finite(x, name=name)

def isInf(x, name=None):
    return tf.math.is_inf(x, name=name)

def isNan(x, name=None):
    return tf.math.is_nan(x, name=name)

def isNonDecreasing(x, name=None):
    return tf.math.is_non_decreasing(x, name=name)

def isStrictlyIncreasing(x, name=None):
    return tf.math.is_strictly_increasing(x, name=name)

def l2Normalize(x, axis=None, epsilon=1e-12, name=None):
    return tf.math.l2_normalize(x, axis=axis, epsilon=epsilon, name=name)

def lbetaVal(a, b, name=None):
    return tf.math.lbeta(a, b, name=name)

def lessVal(x, y, name=None):
    return tf.math.less(x, y, name=name)

def lessEqualVal(x, y, name=None):
    return tf.math.less_equal(x, y, name=name)

def lgammaVal(x, name=None):
    return tf.math.lgamma(x, name=name)

def logVal(x, name=None):
    return tf.math.log(x, name=name)

def log1pVal(x, name=None):
    return tf.math.log1p(x, name=name)

def logSigmoid(x, name=None):
    return tf.math.log_sigmoid(x, name=name)

def logSoftmax(x, axis=None, name=None):
    return tf.math.log_softmax(x, axis=axis, name=name)

def logicalAnd(x, y, name=None):
    return tf.math.logical_and(x, y, name=name)

def logicalNot(x, name=None):
    return tf.math.logical_not(x, name=name)

def logicalOr(x, y, name=None):
    return tf.math.logical_or(x, y, name=name)

def logicalXor(x, y, name=None):
    return tf.math.logical_xor(x, y, name=name)

def maximumVal(x, y, name=None):
    return tf.math.maximum(x, y, name=name)

def minimumVal(x, y, name=None):
    return tf.math.minimum(x, y, name=name)

def modVal(x, y, name=None):
    return tf.math.mod(x, y, name=name)

def multiplyVal(x, y, name=None):
    return tf.math.multiply(x, y, name=name)

def multiplyNoNan(x, y, name=None):
    return tf.math.multiply_no_nan(x, y, name=name)

def ndtriVal(p, name=None):
    return tf.math.ndtri(p, name=name)

def negativeVal(x, name=None):
    return tf.math.negative(x, name=name)

def nextAfter(x, y, name=None):
    return tf.math.nextafter(x, y, name=name)

def notEqualVal(x, y, name=None):
    return tf.math.not_equal(x, y, name=name)

def polygammaVal(n, x, name=None):
    return tf.math.polygamma(n, x, name=name)

def polyvalVal(coeffs, x, name=None):
    return tf.math.polyval(coeffs, x, name=name)

def powVal(x, y, name=None):
    return tf.math.pow(x, y, name=name)

def realVal(x, name=None):
    return tf.math.real(x, name=name)

def reciprocalVal(x, name=None):
    return tf.math.reciprocal(x, name=name)

def reciprocalNoNan(x, y, name=None):
    return tf.math.reciprocal_no_nan(x, y, name=name)

def reduceAll(input, axis=None, keepdims=False, name=None):
    return tf.math.reduce_all(input, axis=axis, keepdims=keepdims, name=name)

def reduceAny(input, axis=None, keepdims=False, name=None):
    return tf.math.reduce_any(input, axis=axis, keepdims=keepdims, name=name)

def reduceEuclideanNorm(input, axis=None, keepdims=False, name=None):
    return tf.math.reduce_euclidean_norm(input, axis=axis, keepdims=keepdims, name=name)

def reduceLogsumexp(input, axis=None, keepdims=False, name=None):
    return tf.math.reduce_logsumexp(input, axis=axis, keepdims=keepdims, name=name)

def reduceMax(input, axis=None, keepdims=False, name=None):
    return tf.math.reduce_max(input, axis=axis, keepdims=keepdims, name=name)

def reduceMean(input, axis=None, keepdims=False, name=None):
    return tf.math.reduce_mean(input, axis=axis, keepdims=keepdims, name=name)

def reduceMin(input, axis=None, keepdims=False, name=None):
    return tf.math.reduce_min(input, axis=axis, keepdims=keepdims, name=name)

def reduceProd(input, axis=None, keepdims=False, name=None):
    return tf.math.reduce_prod(input, axis=axis, keepdims=keepdims, name=name)

def reduceStd(input, axis=None, keepdims=False, name=None):
    return tf.math.reduce_std(input, axis=axis, keepdims=keepdims, name=name)

def reduceSum(input, axis=None, keepdims=False, name=None):
    return tf.math.reduce_sum(input, axis=axis, keepdims=keepdims, name=name)

def reduceVariance(input, axis=None, keepdims=False, name=None):
    return tf.math.reduce_variance(input, axis=axis, keepdims=keepdims, name=name)

def rintVal(x, name=None):
    return tf.math.rint(x, name=name)

def roundVal(x, name=None):
    return tf.math.round(x, name=name)

def rsqrtVal(x, name=None):
    return tf.math.rsqrt(x, name=name)

def scalarMul(scalar, x, name=None):
    return tf.math.scalar_mul(scalar, x, name=name)

def segmentMax(data, segmentIds, name=None):
    return tf.math.segment_max(data, segmentIds, name=name)

def segmentMean(data, segmentIds, name=None):
    return tf.math.segment_mean(data, segmentIds, name=name)

def segmentMin(data, segmentIds, name=None):
    return tf.math.segment_min(data, segmentIds, name=name)

def segmentProd(data, segmentIds, name=None):
    return tf.math.segment_prod(data, segmentIds, name=name)

def segmentSum(data, segmentIds, name=None):
    return tf.math.segment_sum(data, segmentIds, name=name)

def sigmoidVal(x, name=None):
    return tf.math.sigmoid(x, name=name)

def signVal(x, name=None):
    return tf.math.sign(x, name=name)

def sinVal(x, name=None):
    return tf.math.sin(x, name=name)

def sinhVal(x, name=None):
    return tf.math.sinh(x, name=name)

def sobolSample(dim, numResults, skip=0, dtype=tf.float32, seed=None, name=None):
    return tf.math.sobol_sample(dim, numResults, skip=skip, dtype=dtype, seed=seed, name=name)

def softmaxVal(logits, axis=None, name=None):
    return tf.math.softmax(logits, axis=axis, name=name)

def softplusVal(x, name=None):
    return tf.math.softplus(x, name=name)

def softsignVal(x, name=None):
    return tf.math.softsign(x, name=name)

def sqrtVal(x, name=None):
    return tf.math.sqrt(x, name=name)

def squareVal(x, name=None):
    return tf.math.square(x, name=name)

def squaredDifference(x, y, name=None):
    return tf.math.squared_difference(x, y, name=name)

def subtractVal(x, y, name=None):
    return tf.math.subtract(x, y, name=name)

def tanVal(x, name=None):
    return tf.math.tan(x, name=name)

def tanhVal(x, name=None):
    return tf.math.tanh(x, name=name)

def topK(input, k=1, sorted=True, name=None):
    return tf.math.top_k(input, k=k, sorted=sorted, name=name)

def trueDiv(x, y, name=None):
    return tf.math.truediv(x, y, name=name)

def unsortedSegmentMax(data, segmentIds, numSegments, name=None):
    return tf.math.unsorted_segment_max(data, segmentIds, num_segments=numSegments, name=name)

def unsortedSegmentMean(data, segmentIds, numSegments, name=None):
    return tf.math.unsorted_segment_mean(data, segmentIds, num_segments=numSegments, name=name)

def unsortedSegmentMin(data, segmentIds, numSegments, name=None):
    return tf.math.unsorted_segment_min(data, segmentIds, num_segments=numSegments, name=name)

def unsortedSegmentProd(data, segmentIds, numSegments, name=None):
    return tf.math.unsorted_segment_prod(data, segmentIds, num_segments=numSegments, name=name)

def unsortedSegmentSqrtN(data, segmentIds, numSegments, name=None):
    return tf.math.unsorted_segment_sqrt_n(data, segmentIds, num_segments=numSegments, name=name)

def unsortedSegmentSum(data, segmentIds, numSegments, name=None):
    return tf.math.unsorted_segment_sum(data, segmentIds, num_segments=numSegments, name=name)

def xdivyVal(x, y, name=None):
    return tf.math.xdivy(x, y, name=name)

def xlog1pyVal(x, y, name=None):
    return tf.math.xlog1py(x, y, name=name)

def xlogyVal(x, y, name=None):
    return tf.math.xlogy(x, y, name=name)

def zeroFraction(x, name=None):
    return tf.math.zero_fraction(x, name=name)

def zetaVal(x, q, name=None):
    return tf.math.zeta(x, q, name=name)

sysmathConst = tf.math._sys
specialConst = tf.math.special
