import moviepy

class ClipClass(moviepy.Clip.Clip):
    def __init__(self, duration=None, ismask=False):
        super().__init__(duration=duration, ismask=ismask)

def applyToAudio(clip, function):
    return moviepy.Clip.apply_to_audio(clip, function)

def applyToMask(clip, function):
    return moviepy.Clip.apply_to_mask(clip, function)

def convertToSeconds(value, fps=None):
    return moviepy.Clip.convert_to_seconds(value, fps=fps)

def copyClip(clip):
    return moviepy.Clip.copy(clip)

def outplaceClip(clip, function):
    return moviepy.Clip.outplace(clip, function)

def requiresDuration(clip):
    return moviepy.Clip.requires_duration(clip)

def tqdmProgress(iterable, desc=None, total=None, leave=True, file=None, ncols=None, mininterval=0.1, maxinterval=10.0, miniters=1, ascii=False, disable=False, unit="it", unitScale=False, dynamicNcols=False, smoothing=0.3, barFormat=None, initial=0, position=None, postfix=None, unitDivisor=1000, writeBytes=False, lockArgs=None, nrows=None, colour=None, delay=0, gui=False):
    return moviepy.Clip.tqdm(iterable, desc, total, leave, file, ncols, mininterval, maxinterval, miniters, ascii, disable, unit, unitScale, dynamicNcols, smoothing, barFormat, initial, position, postfix, unitDivisor, writeBytes, lockArgs, nrows, colour, delay, gui)

def useClipFpsByDefault(clip):
    return moviepy.Clip.use_clip_fps_by_default(clip)

AudioModule = moviepy.audio
AudioFxModule = moviepy.audio.fx
AudioIoModule = moviepy.audio.io

class AudioArrayClipClass(moviepy.audio.AudioClip.AudioArrayClip):
    def __init__(self, array, fps=44100):
        super().__init__(array, fps=fps)

class AudioClipClass(moviepy.audio.AudioClip.AudioClip):
    def __init__(self, makeFrame, duration=None, fps=44100, nchannels=1, ismask=False, name=None):
        super().__init__(make_frame=makeFrame, duration=duration, fps=fps, nchannels=nchannels, ismask=ismask, name=name)

class CompositeAudioClipClass(moviepy.audio.AudioClip.CompositeAudioClip):
    def __init__(self, clips):
        super().__init__(clips)

def concatenateAudioClips(clips):
    return moviepy.audio.AudioClip.concatenate_audioclips(clips)

def deprecatedVersionOf(function, oldName, newName):
    return moviepy.audio.AudioClip.deprecated_version_of(function, oldName, newName)

audioExtensionsDict = moviepy.audio.AudioClip.extensions_dict
audioNp = moviepy.audio.AudioClip.np
audioOs = moviepy.audio.AudioClip.os
audioProglog = moviepy.audio.AudioClip.proglog

def ffmpegAudioWrite(audioClip, filename, fps=44100, nbytes=2, buffersize=2000, codec="pcm_s16le", bitrate=None, writeLogfile=False, verbose=True, ffmpegParams=None, logger=None):
    return moviepy.audio.AudioClip.ffmpeg_audiowrite(audioClip, filename, fps, nbytes, buffersize, codec, bitrate, writeLogfile, verbose, ffmpegParams, logger)

def requiresDurationAudio(clip):
    return moviepy.audio.AudioClip.requires_duration(clip)

def tqdmAudio(iterable, desc=None, total=None, leave=True, file=None, ncols=None, mininterval=0.1, maxinterval=10.0, miniters=1, ascii=False, disable=False, unit="it", unitScale=False, dynamicNcols=False, smoothing=0.3, barFormat=None, initial=0, position=None, postfix=None, unitDivisor=1000, writeBytes=False, lockArgs=None, nrows=None, colour=None, delay=0, gui=False):
    return moviepy.audio.AudioClip.tqdm(iterable, desc, total, leave, file, ncols, mininterval, maxinterval, miniters, ascii, disable, unit, unitScale, dynamicNcols, smoothing, barFormat, initial, position, postfix, unitDivisor, writeBytes, lockArgs, nrows, colour, delay, gui)

def audioFadeIn(clip, duration):
    return moviepy.audio.fx.all.audio_fadein(clip, duration)

def audioFadeOut(clip, duration):
    return moviepy.audio.fx.all.audio_fadeout(clip, duration)

def audioLeftRight(audioClip, left=1.0, right=1.0, merge=True):
    return moviepy.audio.fx.all.audio_left_right(audioClip, left, right, merge)

def audioLoop(audioClip, nLoops=None, duration=None):
    return moviepy.audio.fx.all.audio_loop(audioClip, nLoops, duration)

def audioNormalize(clip):
    return moviepy.audio.fx.all.audio_normalize(clip)

def volumeX(clip, factor):
    return moviepy.audio.fx.all.volumex(clip, factor)

audioFxName = moviepy.audio.fx.all.name

def audioFadeInFx(clip, duration):
    return moviepy.audio.fx.audio_fadein.audio_fadein(clip, duration)

def audioVideoFxFromFadeIn(function, clip):
    return moviepy.audio.fx.audio_fadein.audio_video_fx(function, clip)

def audioFadeOutFx(clip, duration):
    return moviepy.audio.fx.audio_fadeout.audio_fadeout(clip, duration)

def audioVideoFxFromFadeOut(function, clip):
    return moviepy.audio.fx.audio_fadeout.audio_video_fx(function, clip)

def requiresDurationFromFadeOut(clip):
    return moviepy.audio.fx.audio_fadeout.requires_duration(clip)

def audioLeftRightFx(audioClip, left=1.0, right=1.0, merge=True):
    return moviepy.audio.fx.audio_left_right.audio_left_right(audioClip, left, right, merge)

def audioLoopFx(audioClip, nLoops=None, duration=None):
    return moviepy.audio.fx.audio_loop.audio_loop(audioClip, nLoops, duration)

def concatenateAudioClipsFromLoop(clips):
    return moviepy.audio.fx.audio_loop.concatenate_audioclips(clips)

def audioNormalizeFx(clip):
    return moviepy.audio.fx.audio_normalize.audio_normalize(clip)

def audioVideoFxFromNormalize(function, clip):
    return moviepy.audio.fx.audio_normalize.audio_video_fx(function, clip)

def volumeXFromNormalize(clip, factor):
    return moviepy.audio.fx.audio_normalize.volumex(clip, factor)

def audioVideoFxFromVolumex(function, clip):
    return moviepy.audio.fx.volumex.audio_video_fx(function, clip)

def volumeXFx(clip, factor):
    return moviepy.audio.fx.volumex.volumex(clip, factor)

class AudioClipEditor(moviepy.audio.io.AudioFileClip.AudioClip):
    def __init__(self, makeFrame, duration=None, fps=44100):
        super().__init__(makeFrame, duration, fps)

class AudioFileClipClass(moviepy.audio.io.AudioFileClip.AudioFileClip):
    def __init__(self, filename, buffersize=2000, nbytes=2, fps=None):
        super().__init__(filename, buffersize, nbytes, fps)

class FFMPEGAudioReaderClass(moviepy.audio.io.AudioFileClip.FFMPEG_AudioReader):
    def __init__(self, filename, buffersize=2000, printInfos=False, fps=None, nbytes=2, nchannels=2):
        super().__init__(filename, buffersize, printInfos, fps, nbytes, nchannels)

audioDivisionConst = moviepy.audio.io.AudioFileClip.division

audioWriterDevnull = moviepy.audio.io.ffmpeg_audiowriter.DEVNULL

class FFMPEGAudioWriterClass(moviepy.audio.io.ffmpeg_audiowriter.FFMPEG_AudioWriter):
    def __init__(self, filename, fpsInput, nbytes, nchannels, codec, bitrate=None, inputVideo=None, logfile=None, ffmpegParams=None):
        super().__init__(filename, fpsInput, nbytes, nchannels, codec, bitrate, inputVideo, logfile, ffmpegParams)

def ffmpegAudioWriteIo(clip, filename, fps=44100, nbytes=2, buffersize=2000, codec="pcm_s16le", bitrate=None, writeLogfile=False, verbose=True, ffmpegParams=None, logger=None):
    return moviepy.audio.io.ffmpeg_audiowriter.ffmpeg_audiowrite(clip, filename, fps, nbytes, buffersize, codec, bitrate, writeLogfile, verbose, ffmpegParams, logger)

def getAudioSettingIo(varName):
    return moviepy.audio.io.ffmpeg_audiowriter.get_setting(varName)

def requiresDurationAudioIo(clip):
    return moviepy.audio.io.ffmpeg_audiowriter.requires_duration(clip)

def previewAudioIo(clip, fps=None, buffersize=2000, nbytes=2, audioFlag=True, videoFlag=False):
    return moviepy.audio.io.preview.preview(clip, fps, buffersize, nbytes, audioFlag, videoFlag)

def requiresDurationPreviewAudio(clip):
    return moviepy.audio.io.preview.requires_duration(clip)

audioReadersDevnull = moviepy.audio.io.readers.DEVNULL

class FFMPEGAudioReaderIo(moviepy.audio.io.readers.FFMPEG_AudioReader):
    def __init__(self, filename, buffersize=2000, printInfos=False, fps=None, nbytes=2, nchannels=2):
        super().__init__(filename, buffersize, printInfos, fps, nbytes, nchannels)

audioReadersPy3 = moviepy.audio.io.readers.PY3

def ffmpegParseInfosAudio(filename, printInfos=False, checkDuration=True, fpsSource="fps"):
    return moviepy.audio.io.readers.ffmpeg_parse_infos(filename, printInfos, checkDuration, fpsSource)

def getAudioSettingReaders(varName):
    return moviepy.audio.io.readers.get_setting(varName)

def findAudioPeriod(clip, tMin=None, tMax=None, tRes=None):
    return moviepy.audio.tools.cuts.find_audio_period(clip, tMin, tMax, tRes)

compatDevnull = moviepy.compat.DEVNULL
compatPy3 = moviepy.compat.PY3

configDevnull = moviepy.config.DEVNULL
configFfmpegBinary = moviepy.config.FFMPEG_BINARY
configImageMagickBinary = moviepy.config.IMAGEMAGICK_BINARY

def changeSettings(newSettings, filename=None):
    return moviepy.config.change_settings(newSettings, filename)

def getExe():
    return moviepy.config.get_exe()

def getSettingConfig(varName):
    return moviepy.config.get_setting(varName)

def tryCmd(command):
    return moviepy.config.try_cmd(command)

defaultsFfmpegBinary = moviepy.config_defaults.FFMPEG_BINARY
defaultsImageMagickBinary = moviepy.config_defaults.IMAGEMAGICK_BINARY

def addMaskIfNoneDecorator(clip):
    return moviepy.decorators.add_mask_if_none(clip)

def applyToAudioDecorator(clip, function):
    return moviepy.decorators.apply_to_audio(clip, function)

def applyToMaskDecorator(clip, function):
    return moviepy.decorators.apply_to_mask(clip, function)

def audioVideoFxDecorator(function, clip):
    return moviepy.decorators.audio_video_fx(function, clip)

def convertMasksToRgbDecorator(clip):
    return moviepy.decorators.convert_masks_to_RGB(clip)

def convertToSecondsDecorator(value, fps=None):
    return moviepy.decorators.convert_to_seconds(value, fps=fps)

def cvsecsValue(timeValue, fps=None):
    return moviepy.decorators.cvsecs(timeValue, fps)

def outplaceDecorator(clip, function):
    return moviepy.decorators.outplace(clip, function)

def preprocessArgs(function, varNames):
    return moviepy.decorators.preprocess_args(function, varNames)

def requiresDurationDecorator(clip):
    return moviepy.decorators.requires_duration(clip)

def useClipFpsByDefaultDecorator(clip):
    return moviepy.decorators.use_clip_fps_by_default(clip)

import moviepy
import moviepy.video as moviepy_video
import moviepy.video.compositing as moviepy_video_compositing
import moviepy.video.fx as moviepy_video_fx
import moviepy.video.io as moviepy_video_io
import moviepy.video.tools as moviepy_video_tools
import moviepy.video.compositing.on_color as moviepy_on_color
import moviepy.video.compositing.concatenate as moviepy_concatenate
import moviepy.video.compositing.transitions as moviepy_transitions
import moviepy.video.compositing.positioning as moviepy_positioning
import moviepy.video.fx.accel_decel as moviepy_fx_accel_decel
import moviepy.video.fx.blackwhite as moviepy_fx_blackwhite
import moviepy.video.fx.blink as moviepy_fx_blink
import moviepy.video.fx.colorx as moviepy_fx_colorx
import moviepy.video.fx.crop as moviepy_fx_crop
import moviepy.video.fx.even_size as moviepy_fx_even_size
import moviepy.video.fx.fadein as moviepy_fx_fadein
import moviepy.video.fx.fadeout as moviepy_fx_fadeout
import moviepy.video.fx.freeze as moviepy_fx_freeze
import moviepy.video.fx.freeze_region as moviepy_fx_freeze_region
import moviepy.video.fx.gamma_corr as moviepy_fx_gamma_corr
import moviepy.video.fx.headblur as moviepy_fx_headblur
import moviepy.video.fx.invert_colors as moviepy_fx_invert_colors
import moviepy.video.fx.loop as moviepy_fx_loop
import moviepy.video.fx.lum_contrast as moviepy_fx_lum_contrast
import moviepy.video.fx.make_loopable as moviepy_fx_make_loopable
import moviepy.video.fx.margin as moviepy_fx_margin
import moviepy.video.fx.mask_and as moviepy_fx_mask_and
import moviepy.video.fx.mask_color as moviepy_fx_mask_color
import moviepy.video.fx.mask_or as moviepy_fx_mask_or
import moviepy.video.fx.mirror_x as moviepy_fx_mirror_x
import moviepy.video.fx.mirror_y as moviepy_fx_mirror_y
import moviepy.video.fx.painting as moviepy_fx_painting
import moviepy.video.fx.resize as moviepy_fx_resize
import moviepy.video.fx.rotate as moviepy_fx_rotate
import moviepy.video.fx.scroll as moviepy_fx_scroll
import moviepy.video.fx.speedx as moviepy_fx_speedx
import moviepy.video.fx.supersample as moviepy_fx_supersample
import moviepy.video.fx.time_mirror as moviepy_fx_time_mirror
import moviepy.video.fx.time_symmetrize as moviepy_fx_time_symmetrize

class CompositeVideoClipClass(moviepy_video_compositing.CompositeVideoClip.CompositeVideoClip):
    def __init__(self, clips, size=None, bg_color=None, use_bgclip=False):
        super().__init__(clips, size=size, bg_color=bg_color, use_bgclip=use_bgclip)

def compositeVideoClip(clips, size=None, bgColor=None, useBgClip=False):
    return moviepy_video_compositing.CompositeVideoClip(clips, size=size, bg_color=bgColor, use_bgclip=useBgClip)

def concatenateClips(clips, method="compose", padding=0):
    return moviepy_concatenate.concatenate(clips, method=method, padding=padding)

def onColor(size, color, pos=(0, 0), colOpacity=1.0):
    return moviepy_on_color.on_color(size, color, pos, col_opacity=colOpacity)

def transitionAddMaskIfNone(clip):
    return moviepy_transitions.add_mask_if_none(clip)

def transitionCrossfadeIn(clip, duration):
    return moviepy_transitions.crossfadein(clip, duration)

def transitionCrossfadeOut(clip, duration):
    return moviepy_transitions.crossfadeout(clip, duration)

def transitionFadeIn(clip, duration, initialColor=None):
    return moviepy_transitions.fadein(clip, duration, initial_color=initialColor)

def transitionFadeOut(clip, duration, finalColor=None):
    return moviepy_transitions.fadeout(clip, duration, final_color=finalColor)

def transitionMakeLoopable(clip, crossDuration):
    return moviepy_transitions.make_loopable(clip, crossDuration)

def transitionSlideIn(clip, duration, side="left"):
    return moviepy_transitions.slide_in(clip, duration, side)

def transitionSlideOut(clip, duration, side="right"):
    return moviepy_transitions.slide_out(clip, duration, side)

def fxAccelDecel(clip, newDuration, abruptness=1.0, soonness=0.5):
    return moviepy_fx_accel_decel.accel_decel(clip, newDuration, abruptness, soonness)

def fxFAccelDecel(t, oldDuration, newDuration, abruptness=1.0, soonness=0.5):
    return moviepy_fx_accel_decel.f_accel_decel(t, oldDuration, newDuration, abruptness, soonness)

def fxBlackWhite(clip, RGB=False, preserveLuminosity=True):
    return moviepy_fx_blackwhite.blackwhite(clip, RGB, preserve_luminosity=preserveLuminosity)

def fxBlink(clip, dOn=0.1, dOff=0.1):
    return moviepy_fx_blink.blink(clip, dOn, dOff)

def fxColorX(clip, factor):
    return moviepy_fx_colorx.colorx(clip, factor)

def fxCrop(clip, x1=None, y1=None, x2=None, y2=None, width=None, height=None, xCenter=None, yCenter=None):
    return moviepy_fx_crop.crop(clip, x1=x1, y1=y1, x2=x2, y2=y2, width=width, height=height, x_center=xCenter, y_center=yCenter)

def fxEvenSize(clip):
    return moviepy_fx_even_size.even_size(clip)

def fxFadeIn(clip, duration, initialColor=None):
    return moviepy_fx_fadein.fadein(clip, duration, initial_color=initialColor)

def fxFadeOut(clip, duration, finalColor=None):
    return moviepy_fx_fadeout.fadeout(clip, duration, final_color=finalColor)

def fxFreeze(clip, t, freezeDuration=None, totalDuration=None, paddingEnd=0):
    return moviepy_fx_freeze.freeze(clip, t, freezeDuration, totalDuration, paddingEnd)

def fxFreezeRegion(clip, t, region, outsideRegion=False, mask=None):
    return moviepy_fx_freeze_region.freeze_region(clip, t, region, outsideRegion, mask)

def fxGammaCorr(clip, gamma):
    return moviepy_fx_gamma_corr.gamma_corr(clip, gamma)

def fxHeadBlur(clip, fx=1.0, fy=1.0, rZone=50, rBlur=15):
    return moviepy_fx_headblur.headblur(clip, fx, fy, rZone, rBlur)

def fxInvertColors(clip):
    return moviepy_fx_invert_colors.invert_colors(clip)

def fxLoop(clip, n=None, duration=None):
    return moviepy_fx_loop.loop(clip, n, duration)

def fxLumContrast(clip, lum=0.0, contrast=1.0, contrastThr=0.0):
    return moviepy_fx_lum_contrast.lum_contrast(clip, lum, contrast, contrastThr)

def fxMakeLoopable(clip, crossDuration=0.5):
    return moviepy_fx_make_loopable.make_loopable(clip, crossDuration)

def fxMargin(clip, left=0, top=0, right=0, bottom=0, color=(0, 0, 0), opacity=1.0):
    return moviepy_fx_margin.margin(clip, left, top, right, bottom, color=color, opacity=opacity)

def fxMaskAnd(clip, otherClip):
    return moviepy_fx_mask_and.mask_and(clip, otherClip)

def fxMaskColor(clip, color=(0, 0, 0), thr=0.1, s=1.0):
    return moviepy_fx_mask_color.mask_color(clip, color, thr, s)

def fxMaskOr(clip, otherClip):
    return moviepy_fx_mask_or.mask_or(clip, otherClip)

def fxMirrorX(clip, applyToMask=False):
    return moviepy_fx_mirror_x.mirror_x(clip, apply_to=applyToMask)

def fxMirrorY(clip, applyToMask=False):
    return moviepy_fx_mirror_y.mirror_y(clip, apply_to=applyToMask)

def fxPainting(clip, saturation=1.0, black=0.0):
    return moviepy_fx_painting.painting(clip, saturation, black)

def fxResize(clip, newSize=None, height=None, width=None, applyToMask=False):
    return moviepy_fx_resize.resize(clip, newSize, height=height, width=width, apply_to_mask=applyToMask)

def fxRotate(clip, angle, unit="deg", resample=False, expand=False):
    return moviepy_fx_rotate.rotate(clip, angle, unit=unit, resample=resample, expand=expand)

def fxScroll(clip, h, w, xSpeed=0, ySpeed=0, xStart=0, yStart=0, applyTo=None):
    return moviepy_fx_scroll.scroll(clip, h, w, xSpeed, ySpeed, xStart, yStart, applyTo)

def fxSpeedX(clip, factor, finalDuration=None):
    return moviepy_fx_speedx.speedx(clip, factor, finalDuration)

def fxSupersample(clip, d=1, nFrames=2):
    return moviepy_fx_supersample.supersample(clip, d, nFrames)

def fxTimeMirror(clip):
    return moviepy_fx_time_mirror.time_mirror(clip)

def fxTimeSymmetrize(clip):
    return moviepy_fx_time_symmetrize.time_symmetrize(clip)

def pilToNpimage(pilImage, dtype="uint8"):
    return moviepy_video_io.bindings.PIL_to_npimage(pilImage, dtype=dtype)

def mplfigToNpimage(fig, dpi=None):
    return moviepy_video_io.bindings.mplfig_to_npimage(fig, dpi=dpi)

def downloadWebfile(url, filename=None, timeout=None):
    return moviepy_video_io.downloader.download_webfile(url, filename, timeout=timeout)

class FFMPEGVideoReaderClass(moviepy_video_io.ffmpeg_reader.FFMPEG_VideoReader):
    def __init__(self, filename, printInfos=False, bufSize=10, fpsSource="fps"):
        super().__init__(filename, print_infos=printInfos, bufsize=bufSize, fps_source=fpsSource)

def ffmpegParseInfos(filename, printInfos=False, checkDuration=True, fpsSource="fps"):
    return moviepy_video_io.ffmpeg_reader.ffmpeg_parse_infos(filename, printInfos, checkDuration, fpsSource)

def ffmpegReadImage(filename, t, withMask=False):
    return moviepy_video_io.ffmpeg_reader.ffmpeg_read_image(filename, t, with_mask=withMask)

ffmpegReaderDevnull = moviepy_video_io.ffmpeg_reader.DEVNULL
ffmpegReaderPy3 = moviepy_video_io.ffmpeg_reader.PY3
ffmpegReaderNp = moviepy_video_io.ffmpeg_reader.np
ffmpegReaderOs = moviepy_video_io.ffmpeg_reader.os
ffmpegReaderRe = moviepy_video_io.ffmpeg_reader.re
ffmpegReaderSp = moviepy_video_io.ffmpeg_reader.sp
ffmpegReaderWarnings = moviepy_video_io.ffmpeg_reader.warnings

def ffmpegExtractAudio(videoFilename, outputFilename, startTime=None, endTime=None, codec="copy", bitrate=None):
    return moviepy_video_io.ffmpeg_tools.ffmpeg_extract_audio(videoFilename, outputFilename, startTime, endTime, codec=codec, bitrate=bitrate)

def ffmpegExtractSubclip(filename, t1, t2, targetname=None):
    return moviepy_video_io.ffmpeg_tools.ffmpeg_extract_subclip(filename, t1, t2, targetname=targetname)

def ffmpegMergeVideoAudio(videoFilename, audioFilename, outputFilename, vcodec="copy", acodec="copy"):
    return moviepy_video_io.ffmpeg_tools.ffmpeg_merge_video_audio(videoFilename, audioFilename, outputFilename, vcodec=vcodec, acodec=acodec)

def ffmpegMovieFromFrames(framesDir, outputFilename, fps=24, codec="libx264", bitrate=None):
    return moviepy_video_io.ffmpeg_tools.ffmpeg_movie_from_frames(framesDir, outputFilename, fps=fps, codec=codec, bitrate=bitrate)

def ffmpegResize(inputFile, outputFile, size=None, bitrate=None, codec="libx264"):
    return moviepy_video_io.ffmpeg_tools.ffmpeg_resize(inputFile, outputFile, size=size, bitrate=bitrate, codec=codec)

class FFMPEGVideoWriterClass(moviepy_video_io.ffmpeg_writer.FFMPEG_VideoWriter):
    def __init__(self, filename, size, fps=24, codec="libx264", bitrate=None, preset="medium"):
        super().__init__(filename, size, fps=fps, codec=codec, bitrate=bitrate, preset=preset)

def ffmpegWriteImage(image, filename, quality=95, codec=None):
    return moviepy_video_io.ffmpeg_writer.ffmpeg_write_image(image, filename, quality=quality, codec=codec)

def ffmpegWriteVideo(clip, filename, fps=24, codec="libx264", bitrate=None, preset="medium"):
    return moviepy_video_io.ffmpeg_writer.ffmpeg_write_video(clip, filename, fps=fps, codec=codec, bitrate=bitrate, preset=preset)

ffmpegWriterDevnull = moviepy_video_io.ffmpeg_writer.DEVNULL
ffmpegWriterPy3 = moviepy_video_io.ffmpeg_writer.PY3
ffmpegWriterNp = moviepy_video_io.ffmpeg_writer.np
ffmpegWriterOs = moviepy_video_io.ffmpeg_writer.os
ffmpegWriterProglog = moviepy_video_io.ffmpeg_writer.proglog
ffmpegWriterSp = moviepy_video_io.ffmpeg_writer.sp

def gifWrite(clip, filename, fps=10, program="imageio", loop=0, colors=256):
    return moviepy_video_io.gif_writers.write_gif(clip, filename, fps=fps, program=program, loop=loop, colors=colors)

def gifWriteWithImageIo(clip, filename, fps=10, loop=0, colors=256):
    return moviepy_video_io.gif_writers.write_gif_with_image_io(clip, filename, fps=fps, loop=loop, colors=colors)

def gifWriteWithTempfiles(clip, filename, fps=10, program="imageio", loop=0, colors=256):
    return moviepy_video_io.gif_writers.write_gif_with_tempfiles(clip, filename, fps=fps, program=program, loop=loop, colors=colors)

gifWritersDevnull = moviepy_video_io.gif_writers.DEVNULL
gifImageioFound = moviepy_video_io.gif_writers.IMAGEIO_FOUND
gifImageio = moviepy_video_io.gif_writers.imageio
gifNp = moviepy_video_io.gif_writers.np
gifOs = moviepy_video_io.gif_writers.os
gifProglog = moviepy_video_io.gif_writers.proglog
gifSp = moviepy_video_io.gif_writers.sp

def htmlB64encode(data):
    return moviepy_video_io.html_tools.b64encode(data)

def htmlEmbed(htmlString, width=640, height=360, autoplay=False):
    return moviepy_video_io.html_tools.html_embed(htmlString, width=width, height=height, autoplay=autoplay)

def htmlIpythonDisplay(htmlString, width=640, height=360):
    return moviepy_video_io.html_tools.ipython_display(htmlString, width=width, height=height)

htmlExtensionsDict = moviepy_video_io.html_tools.extensions_dict
htmlIpythonAvailable = moviepy_video_io.html_tools.ipython_available
htmlOs = moviepy_video_io.html_tools.os
htmlSorry = moviepy_video_io.html_tools.sorry
htmlTemplates = moviepy_video_io.html_tools.templates

def previewImdisplay(image, title=None, cmap=None):
    return moviepy_video_io.preview.imdisplay(image, title=title, cmap=cmap)

def previewShow(clip, audio=True, fullscreen=False):
    return moviepy_video_io.preview.show(clip, audio=audio, fullscreen=fullscreen)

previewNp = moviepy_video_io.preview.np
previewPg = moviepy_video_io.preview.pg
previewThreading = moviepy_video_io.preview.threading
previewTime = moviepy_video_io.preview.time

def sliderButton(x, y, width=100, height=30, label="Button"):
    return moviepy_video_io.sliders.Button(x, y, width=width, height=height, label=label)

def sliderSlider(x, y, length=200, minValue=0, maxValue=1, initial=0.5):
    return moviepy_video_io.sliders.Slider(x, y, length=length, minValue=minValue, maxValue=maxValue, initial=initial)

sliderPlt = moviepy_video_io.sliders.plt

def creditsResize(clip, newSize):
    return moviepy_video_tools.credits.resize(clip, newSize)

def detectScenes(videoPath, threshold=30):
    return moviepy_video_tools.cuts.detect_scenes(videoPath, threshold=threshold)

def findVideoPeriod(array, fps=24):
    return moviepy_video_tools.cuts.find_video_period(array, fps=fps)

def blitDrawing(surface, image, pos=(0, 0)):
    return moviepy_video_tools.drawing.blit(surface, image, pos)

def circleDrawing(surface, center, radius, color=(255, 255, 255)):
    return moviepy_video_tools.drawing.circle(surface, center, radius, color)

def colorGradient(width, height, startColor, endColor, horizontal=True):
    return moviepy_video_tools.drawing.color_gradient(width, height, startColor, endColor, horizontal=horizontal)

def createInterpolator(points, duration):
    return moviepy_video_tools.interpolators.Interpolator(points, duration)

def createTrajectory(points):
    return moviepy_video_tools.interpolators.Trajectory(points)

def findObjects(image):
    return moviepy_video_tools.segmenting.findObjects(image)

def createSubtitlesClip(subtitles, font="Arial", fontsize=24, color="white"):
    return moviepy_video_tools.subtitles.SubtitlesClip(subtitles, font=font, fontsize=fontsize, color=color)

def createTrackingTrajectory(points):
    return moviepy_video_tools.tracking.Trajectory(points)

def autoTrack(videoClip, startFrame=0, endFrame=None):
    return moviepy_video_tools.tracking.autoTrack(videoClip, startFrame, endFrame)

def manualTracking(frames, points):
    return moviepy_video_tools.tracking.manual_tracking(frames, points)

def findExtension(filename):
    return moviepy.tools.find_extension(filename)

def isString(value):
    return moviepy.tools.is_string(value)

def subprocessCall(cmd, logger=None, errorPrint=True):
    return moviepy.tools.subprocess_call(cmd, logger=logger, errorprint=errorPrint)

def sysWriteFlush(text):
    return moviepy.tools.sys_write_flush(text)

def verbosePrint(verbose, text):
    return moviepy.tools.verbose_print(verbose, text)

def closeAllClips(objects=None, types=None):
    return moviepy.utils.close_all_clips(objects, types)

clipTypes = moviepy.utils.CLIP_TYPES

import moviepy.editor as moviepy_editor

def createAudioClip(makeFrame, duration=None, fps=44100, nchannels=1, ismask=False, name=None):
    return moviepy_editor.AudioClip(make_frame=makeFrame, duration=duration, fps=fps, nchannels=nchannels, ismask=ismask, name=name)

def createAudioFileClip(filename, fps=None, buffersize=2000, nbytes=2, nchannels=2, duration=None):
    return moviepy_editor.AudioFileClip(filename, fps=fps, buffersize=buffersize, nbytes=nbytes, nchannels=nchannels, duration=duration)

def createColorClip(size, color=(0, 0, 0), ismask=False, duration=None):
    return moviepy_editor.ColorClip(size=size, color=color, ismask=ismask, duration=duration)

def createCompositeAudioClip(clips, size=None):
    return moviepy_editor.CompositeAudioClip(clips, size=size)

def createCompositeVideoClip(clips, size=None, bgColor=None, useBgClip=False):
    return moviepy_editor.CompositeVideoClip(clips, size=size, bg_color=bgColor, use_bgclip=useBgClip)

def createImageClip(image, duration=None, ismask=False):
    return moviepy_editor.ImageClip(image, duration=duration, ismask=ismask)

def createImageSequenceClip(images, fps=24, durations=None, withMask=False):
    return moviepy_editor.ImageSequenceClip(images, fps=fps, durations=durations, with_mask=withMask)

def createTextClip(txt, fontsize=24, color="white", font="Arial", strokeWidth=0, strokeColor="black", bgColor=None, size=None, method="label"):
    return moviepy_editor.TextClip(txt, fontsize=fontsize, color=color, font=font, stroke_width=strokeWidth, stroke_color=strokeColor, bg_color=bgColor, size=size, method=method)

def createVideoClip(makeFrame, duration=None, ismask=False, fps=24):
    return moviepy_editor.VideoClip(make_frame=makeFrame, duration=duration, ismask=ismask, fps=fps)

def editorClipsArray(arrayOfClips, rowsWidths=None, colsHeights=None):
    return moviepy_editor.clips_array(arrayOfClips, rows_widths=rowsWidths, cols_heights=colsHeights)

def editorConcatenate(clips, method="compose", padding=0):
    return moviepy_editor.concatenate(clips, method=method, padding=padding)

def editorConcatenateAudioClips(clips):
    return moviepy_editor.concatenate_audioclips(clips)

def editorConcatenateVideoClips(clips, method="compose", padding=0):
    return moviepy_editor.concatenate_videoclips(clips, method=method, padding=padding)

def editorDownloadWebfile(url, filename=None, overwrite=False):
    return moviepy_editor.download_webfile(url, filename, overwrite=overwrite)

def editorIpythonDisplay(clip, filetype="mp4", maxduration=None, t=None, fps=None, rdKwargs=None, center=True, htmlKwargs=None):
    return moviepy_editor.ipython_display(clip, filetype=filetype, maxduration=maxduration, t=t, fps=fps, rd_kwargs=rdKwargs, center=center, html_kwargs=htmlKwargs)

def editorPreview(clip, fps=None, buffersize=2000, nbytes=2, audioFlag=True, videoFlag=True):
    return moviepy_editor.preview(clip, fps=fps, buffersize=buffersize, nbytes=nbytes, audioFlag=audioFlag, videoFlag=videoFlag)

def editorShow(clip, t=None, withMask=False, interactive=False):
    return moviepy_editor.show(clip, t=t, with_mask=withMask, interactive=interactive)

def editorSliders(function, slidersProperties, waitForValidation=True):
    return moviepy_editor.sliders(function, slidersProperties, wait_for_validation=waitForValidation)

moviepyVersion = moviepy.version
pygameInfo = getattr(moviepy, "pygame", None)

import moviepy
import moviepy.video as moviepy_video
import moviepy.video.compositing as moviepy_video_compositing
import moviepy.video.fx as moviepy_video_fx
import moviepy.video.io as moviepy_video_io
import moviepy.video.tools as moviepy_video_tools
import moviepy.audio as moviepy_audio
import moviepy.audio.fx as moviepy_audio_fx
import moviepy.audio.io as moviepy_audio_io
import moviepy.tools as moviepy_tools
import moviepy.utils as moviepy_utils
import moviepy.editor as moviepy_editor

def fxAccelDecelDetailed(clip, newDuration, abruptness=1.0, soonness=0.5):
    return moviepy_video_fx.accel_decel.accel_decel(clip, newDuration, abruptness, soonness)

def fxBlackWhiteDetailed(clip, keepLuminosity=True):
    return moviepy_video_fx.blackwhite.blackwhite(clip, RGB=False, preserve_luminosity=keepLuminosity)

def fxBlinkDetailed(clip, dOn=0.1, dOff=0.1, n=1):
    return moviepy_video_fx.blink.blink(clip, dOn, dOff, n=n)

def fxColorXDetailed(clip, factor):
    return moviepy_video_fx.colorx.colorx(clip, factor)

def fxCropDetailed(clip, x1=None, y1=None, x2=None, y2=None, width=None, height=None, xCenter=None, yCenter=None):
    return moviepy_video_fx.crop.crop(clip, x1=x1, y1=y1, x2=x2, y2=y2, width=width, height=height, x_center=xCenter, y_center=yCenter)

def fxEvenSizeDetailed(clip):
    return moviepy_video_fx.even_size.even_size(clip)

def fxFadeInDetailed(clip, duration, initialColor=None):
    return moviepy_video_fx.fadein.fadein(clip, duration, initial_color=initialColor)

def fxFadeOutDetailed(clip, duration, finalColor=None):
    return moviepy_video_fx.fadeout.fadeout(clip, duration, final_color=finalColor)

def fxFreezeDetailed(clip, t, freezeDuration=None, totalDuration=None, paddingEnd=0):
    return moviepy_video_fx.freeze.freeze(clip, t, freezeDuration, totalDuration, paddingEnd)

def fxFreezeRegionDetailed(clip, t, region, outsideRegion=False, mask=None):
    return moviepy_video_fx.freeze_region.freeze_region(clip, t, region, outside_region=outsideRegion, mask=mask)

def fxGammaCorrDetailed(clip, gamma):
    return moviepy_video_fx.gamma_corr.gamma_corr(clip, gamma)

def fxHeadBlurDetailed(clip, fx=1.0, fy=1.0, rZone=50, rBlur=15):
    return moviepy_video_fx.headblur.headblur(clip, fx, fy, rZone, rBlur)

def fxInvertColorsDetailed(clip):
    return moviepy_video_fx.invert_colors.invert_colors(clip)

def fxLoopDetailed(clip, n=None, duration=None):
    return moviepy_video_fx.loop.loop(clip, n, duration)

def fxLumContrastDetailed(clip, lum=0.0, contrast=1.0, contrastThr=0.0):
    return moviepy_video_fx.lum_contrast.lum_contrast(clip, lum, contrast, contrastThr)

def fxMakeLoopableDetailed(clip, crossDuration=0.5):
    return moviepy_video_fx.make_loopable.make_loopable(clip, crossDuration)

def fxMarginDetailed(clip, left=0, top=0, right=0, bottom=0, color=(0,0,0), opacity=1.0):
    return moviepy_video_fx.margin.margin(clip, left, top, right, bottom, color=color, opacity=opacity)

def fxMaskAndDetailed(clip, otherClip):
    return moviepy_video_fx.mask_and.mask_and(clip, otherClip)

def fxMaskColorDetailed(clip, color=(0,0,0), thr=0.1, s=1.0):
    return moviepy_video_fx.mask_color.mask_color(clip, color, thr, s)

def fxMaskOrDetailed(clip, otherClip):
    return moviepy_video_fx.mask_or.mask_or(clip, otherClip)

def fxMirrorXDetailed(clip, applyToMask=False):
    return moviepy_video_fx.mirror_x.mirror_x(clip, apply_to=applyToMask)

def fxMirrorYDetailed(clip, applyToMask=False):
    return moviepy_video_fx.mirror_y.mirror_y(clip, apply_to=applyToMask)

def fxPaintingDetailed(clip, method="sobel"):
    return moviepy_video_fx.painting.painting(clip, method=method)

def fxResizeDetailed(clip, newSize=None, height=None, width=None, applyToMask=False):
    return moviepy_video_fx.resize.resize(clip, newSize, height=height, width=width, apply_to_mask=applyToMask)

def fxRotateDetailed(clip, angle, unit="deg", resample=False, expand=False):
    return moviepy_video_fx.rotate.rotate(clip, angle, unit=unit, resample=resample, expand=expand)

def fxScrollDetailed(clip, w, h, xSpeed=0, ySpeed=0, xStart=0, yStart=0, applyTo=None):
    return moviepy_video_fx.scroll.scroll(clip, w, h, xSpeed, ySpeed, xStart, yStart, applyTo)

def fxSpeedXDetailed(clip, factor, finalDuration=None):
    return moviepy_video_fx.speedx.speedx(clip, factor, finalDuration)

def fxSupersampleDetailed(clip, d=1, nFrames=2):
    return moviepy_video_fx.supersample.supersample(clip, d, nFrames)

def fxTimeMirrorDetailed(clip):
    return moviepy_video_fx.time_mirror.time_mirror(clip)

def fxTimeSymmetrizeDetailed(clip):
    return moviepy_video_fx.time_symmetrize.time_symmetrize(clip)

def createCompositeVideoClip(clips, size=None, bgColor=None, useBgClip=False):
    return moviepy_video_compositing.CompositeVideoClip(clips, size=size, bg_color=bgColor, use_bgclip=useBgClip)

def compositeClipAddMaskIfNone(clip):
    return moviepy_video_compositing.CompositeVideoClip.add_mask_if_none(clip)

def compositeClipBlit(clip, otherClip, position=(0,0)):
    return moviepy_video_compositing.CompositeVideoClip.blit(clip, otherClip, position)

def compositeClipsArray(arrayOfClips, rowsWidths=None, colsHeights=None, bgColor=None):
    return moviepy_video_compositing.clips_array(arrayOfClips, rows_widths=rowsWidths, cols_heights=colsHeights, bg_color=bgColor)

def createImageSequenceClipExplicit(images, fps=24, durations=None, withMask=False, ismask=False, loadImages=True):
    return moviepy_video_io.ImageSequenceClip(images, fps=fps, durations=durations, with_mask=withMask, ismask=ismask, load_images=loadImages)

def createVideoFileClipExplicit(filename, hasMask=False, audio=True, audioBuffersize=2000, targetResolution=None, resizeAlgorithm=None, audioFps=None, audioNbytes=None, verbose=False, fpsSource="fps"):
    return moviepy_video_io.VideoFileClip(filename, has_mask=hasMask, audio=audio, audio_buffersize=audioBuffersize, target_resolution=targetResolution, resize_algorithm=resizeAlgorithm, audio_fps=audioFps, audio_nbytes=audioNbytes, verbose=verbose, fps_source=fpsSource)

def htmlEmbedExplicit(htmlString, width=640, height=360, autoplay=False, loop=False, controls=True):
    return moviepy_video_io.html_tools.html_embed(htmlString, width=width, height=height, autoplay=autoplay, loop=loop, controls=controls)

def ipythonDisplayHtml(htmlString, width=640, height=360, center=True):
    return moviepy_video_io.html_tools.ipython_display(htmlString, width=width, height=height, center=center)

def previewImdisplayExplicit(image, title=None, cmap=None, dpi=100):
    return moviepy_video_io.preview.imdisplay(image, title=title, cmap=cmap, dpi=dpi)

def previewShowExplicit(clip, audio=True, fullscreen=False, fps=None):
    return moviepy_video_io.preview.show(clip, audio=audio, fullscreen=fullscreen, fps=fps)

def createButton(x, y, width=100, height=30, label="Button", color=(200,200,200)):
    return moviepy_video_io.sliders.Button(x, y, width=width, height=height, label=label, color=color)

def createSliderExplicit(x, y, length=200, minValue=0.0, maxValue=1.0, initial=0.5, orientation="horizontal"):
    return moviepy_video_io.sliders.Slider(x, y, length=length, minValue=minValue, maxValue=maxValue, initial=initial, orientation=orientation)

def creditsCreate(textLines, font="Arial", fontsize=24, color="white", bgColor=None, duration=None):
    return moviepy_video_tools.credits.credits1(textLines, font=font, fontsize=fontsize, color=color, bg_color=bgColor, duration=duration)

def creditsResizeExplicit(clip, newSize):
    return moviepy_video_tools.credits.resize(clip, newSize)

def detectScenesExplicit(filename, threshold=30, minSceneLength=1.0):
    return moviepy_video_tools.cuts.detect_scenes(filename, threshold=threshold, min_scene_length=minSceneLength)

def findVideoPeriodExplicit(framesArray, fps=24):
    return moviepy_video_tools.cuts.find_video_period(framesArray, fps=fps)

def drawingBlit(surface, image, pos=(0,0), mask=None):
    return moviepy_video_tools.drawing.blit(surface, image, pos, mask)

def drawingCircle(surface, center, radius, color=(255,255,255), thickness=1):
    return moviepy_video_tools.drawing.circle(surface, center, radius, color, thickness)

def drawingColorGradient(width, height, startColor, endColor, horizontal=True):
    return moviepy_video_tools.drawing.color_gradient(width, height, startColor, endColor, horizontal=horizontal)

def interpolatorCreate(points, duration):
    return moviepy_video_tools.interpolators.Interpolator(points, duration)

def trajectoryCreate(points):
    return moviepy_video_tools.interpolators.Trajectory(points)

def segmentingFindObjects(image, minSize=10):
    return moviepy_video_tools.segmenting.findObjects(image, min_size=minSize)

def subtitlesCreate(subtitles, font="Arial", fontsize=24, color="white"):
    return moviepy_video_tools.subtitles.SubtitlesClip(subtitles, font=font, fontsize=fontsize, color=color)

def trackingCreateTrajectory(points):
    return moviepy_video_tools.tracking.Trajectory(points)

def trackingAuto(videoClip, startFrame=0, endFrame=None, method="auto"):
    return moviepy_video_tools.tracking.autoTrack(videoClip, startFrame, endFrame, method=method)

def trackingManual(frames, points):
    return moviepy_video_tools.tracking.manual_tracking(frames, points)

def toolsFindExtension(codec):
    return moviepy_tools.find_extension(codec)

def toolsIsString(value):
    return moviepy_tools.is_string(value)

def toolsSubprocessCall(cmd, logger=None, errorPrint=True, shell=False):
    return moviepy_tools.subprocess_call(cmd, logger=logger, errorprint=errorPrint, shell=shell)

def toolsSysWriteFlush(text):
    return moviepy_tools.sys_write_flush(text)

def toolsVerbosePrint(verbose, message):
    return moviepy_tools.verbose_print(verbose, message)

def utilsCreateAudioFileClip(filename, fps=44100):
    return moviepy_utils.AudioFileClip(filename, fps=fps)

def utilsCreateImageClip(image, duration=None):
    return moviepy_utils.ImageClip(image, duration=duration)

def utilsCreateVideoFileClip(filename, hasMask=False, audio=True):
    return moviepy_utils.VideoFileClip(filename, has_mask=hasMask, audio=audio)

def utilsCloseAllClips(objects=None, types=None):
    return moviepy_utils.close_all_clips(objects, types)

def utilsGetClipTypes():
    return moviepy_utils.CLIP_TYPES

def editorCreateCompositeVideoClip(clips, size=None, bgColor=None, useBgClip=False):
    return moviepy_editor.CompositeVideoClip(clips, size=size, bg_color=bgColor, use_bgclip=useBgClip)

def editorCreateCompositeAudioClip(clips):
    return moviepy_editor.CompositeAudioClip(clips)

def editorCreateImageSequenceClip(images, fps=24, durations=None, withMask=False):
    return moviepy_editor.ImageSequenceClip(images, fps=fps, durations=durations, with_mask=withMask)

def editorCreateTextClipExplicit(txt, fontsize=24, color="white", font="Arial", method="label"):
    return moviepy_editor.TextClip(txt, fontsize=fontsize, color=color, font=font, method=method)

MOVIEPYVERSION = moviepy.version
MOVIPYGAMEINFO = getattr(moviepy, "pygame", None)
MOVIEPYDEVNULL = moviepy_tools.DEVNULL
MOVIEPYFFMPEGBINARY = moviepy.config.FFMPEG_BINARY
MOVIEPYIMAGEMAGICKBINARY = moviepy.config.IMAGEMAGICK_BINARY
