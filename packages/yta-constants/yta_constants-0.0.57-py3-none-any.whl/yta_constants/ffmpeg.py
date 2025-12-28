"""
The constants related to the ffmpeg
library, that is also related to the
pyav library because it uses the first
one.

AUDIO LAYOUTS
The audio layouts ffmpeg supports (it
depends on the installation you have):
- 'mono' → 1 canal (C)
- 'stereo' → 2 canales (L, R)
- '2.1' → 3 canales (L, R, LFE)
- '3.0' → 3 canales (L, R, C).
- '4.0' → 4 canales (L, R, SL, SR).
- '5.0' → 5 canales (L, R, C, SL, SR).
- '5.1' → 6 canales (L, R, C, LFE, SL, SR).
- '6.1' → 7 canales (L, R, C, LFE, SL, SR, BC).
- '7.1' → 8 canales (L, R, C, LFE, SL, SR, BL, BR).

Other special audio layouts:
- 'quad' (4 canales, diferente a 4.0 en algunas implementaciones).
- 'hexagonal' (6 canales).
- 'octagonal' (8 canales).
- 'downmix' (canales mezclados).

PIXEL FORMATS
The pixel formats ffmpeg supports
- 'yuv420p' → el estándar universal para H.264/H.265/AV1, 8-bit, sin alpha.
- 'yuva420p' → como el anterior, pero con canal alpha (transparencia).
- 'rgb24' → RGB empaquetado, 8-bit, sin alpha.
- 'rgba' → RGB con alpha empaquetado, 8-bit.
- 'bgra' → Variante con orden de bytes distinto, útil en APIs gráficas.
- 'gray' → escala de grises, 8-bit.
- 'yuv422p' → vídeo profesional, más fidelidad de color (broadcast).
- 'yuv444p' → máxima fidelidad (sin submuestreo de crominancia).

Why using BGRA instead of RGBA?
- Compatibilidad con Windows y DirectX
- Windows DIB (Device Independent Bitmap) usa BGRA como formato nativo.
- DirectX también trabaja con BGRA como formato óptimo.
- APIs gráficas y librerías
- OpenCV en Python devuelve imágenes en BGR por defecto (y con alpha sería BGRA).
- Muchas librerías gráficas prefieren BGRA porque su alineación de memoria es más eficiente en CPUs Intel/AMD (por temas históricos de little-endian).
- Rendimiento en hardware
- En GPUs y algunas CPU SIMD (SSE, AVX, NEON), acceder a memoria en bloques alineados de 32 bits (BGRA empaquetado) puede ser más rápido que reordenar canales.

AUDIO FORMATS
The audio formats ffmpeg supports
- 's16' / 's16p' → estándar en audio comprimido con pérdida (MP3, AAC).
- 'fltp' → muy habitual como salida de decodificación de AAC, Opus.
- 's32' / 's32p' → más profesional, WAV de 32 bits.
- 'flt' / 'fltp' → procesamiento en alta calidad.

VIDEO CODECS
The video codecs ffmpeg supports
· Códecs con pérdidas (lossy, más comunes)
- 'h264' / 'libx264' → el rey de la compatibilidad. MP4, MOV, MKV, casi cualquier dispositivo lo soporta.
- 'hevc' / 'libx265' → sucesor de H.264, mejor compresión pero menos universal. .mp4, .mkv.
- 'mpeg4' → más antiguo, usado en .avi.
- 'vp8' → estándar abierto para .webm, menos usado hoy.
- 'vp9' → sustituto de VP8, muy usado en YouTube, .webm.
- 'av1' → códec abierto moderno, muy buena compresión, cada vez más popular (YouTube, Netflix).
· Códecs sin pérdidas o intermedios (para edición)
- 'prores' / 'prores_ks' → Apple ProRes, muy usado en .mov para edición profesional.
- 'dnxhd' / 'dnxhr' → Avid DNxHD/DNxHR, estándar en edición broadcast.
- 'ffv1' → lossless open-source, muy robusto, suele usarse en preservación.
- 'huffyuv' → 'lossless' antiguo, simple y rápido.
· Códecs con transparencia (alpha channel)
- 'qtrle' → QuickTime Animation, soporta alpha, .mov.
- 'vp9' con yuva420p → transparencia en .webm.
- 'prores_ks' con yuva444p10le → ProRes 4444 con alpha, .mov.
· Códecs acelerados por hardware
(Dependiendo de la build de FFmpeg)
- 'h264_nvenc' / hevc_nvenc → Nvidia.
- 'h264_qsv' / hevc_qsv → Intel QuickSync.
- 'h264_amf' → AMD.
- 'h264_videotoolbox' → Apple.
Distribución / compatibilidad máxima: h264
Mejor compresión moderna: hevc, av1, vp9
Edición profesional: prores_ks, dnxhd
Transparencia: vp9 (web), prores_ks 4444 (mov), qtrle

AUDIO CODECS
The audio codecs supported by ffmpeg
· Códecs con pérdidas (lossy, más comunes)
- 'aac' → el estándar actual para vídeo (MP4, MOV, MKV). Compatibilidad máxima.
- 'mp3' → muy popular en música, aunque hoy se usa más AAC/Opus.
- 'opus' → excelente calidad a bajo bitrate, estándar moderno en WebM, streaming y VoIP.
- 'vorbis' → antes muy usado en OGG/WebM, ahora desplazado por Opus.
- 'ac3' → Dolby Digital, típico en DVD/BluRay y broadcast (5.1 canales).
- 'eac3' → Dolby Digital Plus, sucesor de AC3, más eficiente.
· Códecs sin pérdidas (lossless)
- 'flac' → compresión sin pérdidas, muy popular para música, también soportado en MKV.
- 'alac' → Apple Lossless, compatible con .m4a y .mov.
- 'pcm_s16le' / 'pcm_s24le' / 'pcm_f32le' → PCM lineal (sin comprimir), típico en .wav, .aiff, .mov. Usado en edición profesional.
· Códecs multicanal para cine/broadcast
- 'dts' → Digital Theater Systems, común en BluRay.
- 'truehd' (Dolby TrueHD) → audio sin pérdidas para cine, usado en BluRay.
Compatibilidad máxima (MP4, MOV): aac
Streaming / web: opus (mejor calidad/bitrate)
Música lossless: flac (general), alac (ecosistema Apple)
Edición sin pérdidas: pcm_s16le o pcm_s24le
Cine / multicanal: ac3, eac3, dts, truehd
"""
from yta_constants.enum import YTAEnum as Enum

# TODO: Check because some of the values
# are repeated in the 'video.py' module
class FfmpegAudioLayout(Enum):
    """
    The audio layouts ffmpeg supports.

    The recommended ones:
    - 'mono'
    - 'stereo'
    """

    MONO = 'mono'
    """
    1 single channel (C).
    """
    STEREO = 'stereo'
    """
    2 different channels (L, R).
    """
    AUDIO_2_1 = '2.1'
    """
    3 channels (L, R, LFE)
    """
    AUDIO_3_0 = '3.0'
    """
    3 channels (L, R, C)
    """
    AUDIO_4_0 = '4.0'
    """
    4 channels (L, R, SL, SR)
    """
    AUDIO_5_0 = '5.0'
    """
    5 channels (L, R, C, SL, SR)
    """
    AUDIO_5_1 = '5.1'
    """
    6 channels (L, R, C, LFE, SL, SR)
    """
    AUDIO_6_1 = '6.1'
    """
    7 channels (L, R, C, LFE, SL, SR, BC)
    """
    AUDIO_7_1 = '7.1'
    """
    8 channels (L, R, C, LFE, SL, SR, BL, BR)
    """
    QUAD = 'quad'
    """
    4 channels (different from '4.0' in some
    implementations)
    """
    HEXAGONAL = 'hexagonal'
    """
    6 channels
    """
    OCTAGONAL = 'octagonal'
    """
    8 channels
    """
    DOWN_MIX = 'downmix'
    """
    Mixed channels.
    """

class FfmpegPixelFormat(Enum):
    """
    Pixel formats that are accepted by ffmpeg.

    The recommended ones:
    - 'rgb24'
    - 'rgba'
    - 'yuv420p'
    - 'yuva420p'
    """

    RGB24 = 'rgb24'
    """
    RGB frame packed as 8-bit per color without
    alpha. [255, 255, 255] for a pure black.
    """
    RGBA = 'rgba'
    """
    RGB frame packed as 8-bit per color including
    alpha. [255, 255, 255, 127] for a pure black
    half transparent.
    """
    YUV420P = 'yuv420p'
    """
    Universal standard for H.264/H.264/AV1 as 
    8-bit without alpha.
    """
    YUVA420p = 'yuva420p'
    """
    Universal standard for H.264/H.264/AV1 as 
    8-bit including the alpha channel. 
    """
    BGRA = 'bgra'
    """
    TODO: Explain it
    """
    GRAY = 'gray'
    """
    Grayscale as 8-bit.
    """
    YUV422P = 'yuv422p'
    """
    Professional video with more color fidelity
    (broadcast).
    """
    YUV444P = 'yuv444p'
    """
    Maximum fidelity (without crominance 
    subsampling).
    """
    YUVA444P10LE = 'yuva444p10le'
    """
    Maximum fidelity and accepting alpha channel.
    """
    ARGB = 'argb'
    """
    Alpha and RGB.

    TODO: Explain more.
    """
    

class FfmpegAudioFormat(Enum):
    """
    The audio formats ffmpeg supports.

    The recommended ones:
    - 'fltp'
    """

    U8 = 'u8'
    """
    Unsigned 8-bit.

    TODO: Explain better.
    """
    U8P = 'u8p'
    """
    Unsigned 8-bit (planar)

    TODO: Explain better.
    """
    S16 = 's16'
    """
    Compressed audio standard with loss (mp3, acc).
    """
    S16P = 's16p'
    """
    S16 but planar.
    """
    S32 = 's32'
    """
    Professional one, 32-bit wav.
    """
    S32P = 's32p'
    """
    S32 but planar.
    """
    S64 = 's64'
    """
    signed 64-bit

    TODO: Explain better.
    """
    S64P = 's64p'
    """
    signed 64-bit (planar)

    TODO: Explain better.
    """
    FLT = 'flt'
    """
    High quality processing.
    """
    FLTP = 'fltp'
    """
    FLT but planar. Very common as output when
    decoding aac or opus.
    """
    DBL = 'dbl'
    """
    64-bit float (interleaved)

    TODO: Explain better.
    """
    DBLP = 'dblp'
    """
    64-bit float (planar)

    TODO: Explain better.
    """
    

class FfmpegVideoCodec(Enum):
    """
    Video codecs supported by ffmpeg.

    The recommended ones:
    - 'libx264'
    - 'prores'
    - 'qtrle'
    """

    H264 = 'h264'
    """
    Compatible with almost every device. This one
    has specific implementations like 'libx264'.
    """
    LIBX264 = 'libx264'
    """
    The compatibility king (mp4, mov, mvk), almost
    every device.
    """
    LIBX265 = 'libx265'
    """
    Sucessor of H.264 with better compression but
    less compatible (mp4, mkv).
    """
    PRORES = 'prores'
    """
    Apple ProRes, very used in professional 
    edition (mov).
    """
    PRORES_KS = 'prores_ks'
    """
    TODO: Explain it
    """
    QTRLE = 'qtrle'
    """
    QuickTime Animation, supporting alpha (mov).
    """
    H264_NVENC = 'h264_nvenc'
    """
    H.264 but for Nvidia graphic cards.
    """
    LIBVPX_VP9 = 'libvpx-vp9'
    """
    TODO: Explain it
    """

class FfmpegAudioCodec(Enum):
    """
    The audio codecs supported by ffmpeg.
    """

    AAC = 'aac'
    """
    The current standard for video (mp4, mov, mvk)
    with maximum compatibility.
    """
    MP3 = 'mp3'
    """
    Very popular in music but less used than aac or
    opus.
    """
    OPUS = 'opus'
    """
    Excellent quality with low bitrate. Modern 
    standard in WebM, streaming and VoIP.
    """
    MP3FLOAT = 'mp3float'
    """
    Very popular, as float.
    """