import numpy as np
import cv2


def inv_sinc(x):
    x = np.sqrt(abs(1-x))
    y = 2*x + 3*(x**3)/10 + 321*(x**5)/2800 + 3197*(x**7)/56000 + 445617*(x**9)/13798400
    return np.sqrt(3/2) * y

def generate_oam_superposition(res, pixel_pitch, beam_w0, l_modes, weights):
    """
    OAM 중첩 상태를 위한 SLM 홀로그램 생성 (Interferogram 방식)
    """
    # 좌표계 설정
    x = np.linspace(-res[0] * pixel_pitch / 2, res[0] * pixel_pitch / 2, res[0])
    y = np.linspace(-res[1] * pixel_pitch / 2, res[1] * pixel_pitch / 2, res[1])
    X, Y = np.meshgrid(x, y)

    # 극좌표 변환
    R = np.sqrt(X ** 2 + Y ** 2)
    Phi = np.arctan2(Y, X)

    # 0으로 나누는 것 방지
    R[R == 0] = 1e-10

    # 중첩된 필드 생성
    E_total = np.zeros_like(Phi, dtype=complex)
    for l, w in zip(l_modes, weights):
        # 각 모드의 복소수 필드 생성
        # E = (sqrt(2)r/w)^|l| * exp(-r^2/w^2) * exp(il*phi)
        E_total += w * (np.sqrt(2) * R / beam_w0) ** abs(l) * np.exp(-R ** 2 / beam_w0 ** 2) * np.exp(1j * l * Phi)


    # 목표 진폭(Amplitude)과 위상(Phase) 추출
    Amp = np.abs(E_total)
    Phase = np.angle(E_total)

    # 진폭 정규화 (0 ~ 1)
    Amp = Amp / np.max(Amp)

    modified_amp = 1 + (1/np.pi)*inv_sinc(Amp)
    modified_amp = modified_amp / np.max(modified_amp)

    modified_phase = Phase - np.pi*modified_amp

    return modified_amp, modified_phase, X, Y


def encode_hologram(Amp, Phase, X, Y, pixel_pitch, d, N_steps=0, prepare=0, measure=0, save=False, path="", name=""):
    """
    진폭 정보를 포함하여 SLM에 띄울 최종 Phase Mask 생성
    방식: Off-axis Holography (Carrier frequency 추가)
    """

    parity = 0
    if prepare: parity = -1
    elif measure: parity = 1

    hologram_final = Amp * np.mod(Phase + parity * 2*np.pi * (X * (2/pixel_pitch))/d, 2*np.pi)

    if not save: return hologram_final
    elif save:
        hologram_final = 255 * hologram_final / np.max(hologram_final)
        cv2.imwrite(path+name+".png", hologram_final)
        return 0
    else: return 0

