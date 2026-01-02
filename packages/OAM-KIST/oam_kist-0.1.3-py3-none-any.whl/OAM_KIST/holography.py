import numpy as np
import cv2


def inv_sinc(x):
    """Fourier-Tayler transformation of inversed sinc((sin(x)/x)^-1) function

    Args:
        x (float, np.ndarray[float], optimal): input value x. i.e. -1. <= x <= 1.

    Return:
        type(arg): approximation of the value of a inversed sinc function for x

    Example:
        >>> y = inv_sinc(0.5 * np.pi)
        >>> print(y)
        1.8947036302816116
    """
    x = np.sqrt(1-x)
    y = 2*x + 3*(x**3)/10 + 321*(x**5)/2800 + 3197*(x**7)/56000 + 445617*(x**9)/13798400
    return np.sqrt(3/2) * y


def generate_oam_superposition(res, pixel_pitch, beam_w0, l_modes, weights):
    """ Creat E field of superimposed OAM mode (Interferogram method)

    Args:
        res (list[int]): resolution of SLM. [x resolution, y resolution]
        pixel_pitch (float): pixel size. specified at device document
        beam_w0 (float): beam-waist at z=0.
        l_modes (list[int]): selected l indices for superposion. list with length 1 for eigen mode
        weights (list[float]): weights for selected l modes.

    Returns:
        np.ndarray[float], np.ndarray[float], np.ndarray[float], np.ndarray[float]: information about E field and meshgrid i.e. superimosed

    Example:
        >>> res = [1920, 1080]
        >>> pixel_pitch = 8e-1
        >>> beam_w0 = 0.8e-3
        >>> l_modes = [-3, -1, 1, 3]
        >>> weights = [0.4, 0.03, 0.07, 0.5]
        >>> amp, phase, X, Y = generate_oam_superposition(res, pixel_pitch, beam_w0, l_modes, weights)
    """
    x = np.linspace(-res[0] * pixel_pitch / 2, res[0] * pixel_pitch / 2, res[0])
    y = np.linspace(-res[1] * pixel_pitch / 2, res[1] * pixel_pitch / 2, res[1])
    X, Y = np.meshgrid(x, y)

    R = np.sqrt(X ** 2 + Y ** 2)
    Phi = np.arctan2(Y, X)

    R[R == 0] = 1e-10

    E_total = np.zeros_like(Phi, dtype=complex)
    for l, w in zip(l_modes, weights):
        # E = (sqrt(2)r/w)^|l| * exp(-r^2/w^2) * exp(il*phi)
        E_total += w * (np.sqrt(2) * R / beam_w0) ** abs(l) * np.exp(-R ** 2 / beam_w0 ** 2) * np.exp(1j * l * Phi)

    Amp = np.abs(E_total)
    Phase = np.angle(E_total)

    Amp = Amp / np.max(Amp)

    return Amp, Phase, X, Y


def encode_hologram(Amp, Phase, X, Y, pixel_pitch, d, N_steps=0, prepare=False, measure=False, save=False, path="", name=""):
    """phase mask for given amplitude and phase map of superimposed OAM mode.

    입력받은 위상, 진폭 정보를 논문 공식에 대입하여 이 상태를 인코딩하는 SLM 홀로그램을 생성합니다.
    Fundamental Gaussian 모드와의 분리를 위해서 간격이 d 픽셀인 그레이팅이 적용됩니다.
    상태 준비에 사용될지, 측정에 사용될지에 따라서 그레이팅의 방향이 바뀝니다. 변수 parity가 이것을 반영합니다.
    생성된 홀로그램을 저장할 수 있습니다.

    Args:
        Amp (np.ndarray[float]): amplitude map of superimposed OAM mode. 0. <= *Amp <= 1.
        Phase (np.ndarray[float]): phase map of superimposed OAM mode. -pi < *Phase <= pi
        X (np.ndarray[float]): x dependent meshgrid.
        Y (np.ndarray[float]): y dependent meshgrid.
        pixel_pitch (float): pixel size. specified at device document
        d (float): grating width. dimension in # of pixel
        N_steps (float): need to be applied.
        prepare (bool): decide whether to prepare.
        measure (bool): decide whether to measure.
        save (bool): decide whether to save.
        path (string): directory path for images. needed only when arg save is True
        name (string): filename of this image. needed only when arg save is True

    Return:
        np.ndarray[float] or None: returns carculated hologram.
        if arg save is False(default), a hologram in numpy ndarray. And if not, hologram is saved in the directory addording to arg path.

    Example:
        >>> res = [1920, 1080]
        >>> pixel_pitch = 8e-1
        >>> beam_w0 = 0.8e-3
        >>> l_modes = [-3, -1, 1, 3]
        >>> weights = [0.4, 0.03, 0.07, 0.5]
        >>> amp, phase, X, Y = generate_oam_superposition(res, pixel_pitch, beam_w0, l_modes, weights)
        >>> encode_hologram(amp, phase, X, Y, pixel_pitch, 16, 0, prepare=True, save=True, path="./images", name="l8_dim16")
    """

    modified_amp = 1 + (1/np.pi)*inv_sinc(Amp)
    modified_amp = modified_amp / np.max(modified_amp)

    modified_phase = Phase - np.pi*modified_amp

    parity = 0
    if prepare: parity = -1
    elif measure: parity = 1

    hologram_final = modified_amp * np.mod(modified_phase + parity * 2*np.pi * (X * (2/pixel_pitch))/d, 2*np.pi)

    if not save:
        return hologram_final
    elif save:
        hologram_final = 255 * hologram_final / np.max(hologram_final)
        cv2.imwrite(path+name+".png", hologram_final)
        return 0
    else:
        return 0


if __name__ == '__main__':
    print(inv_sinc(0.5))
