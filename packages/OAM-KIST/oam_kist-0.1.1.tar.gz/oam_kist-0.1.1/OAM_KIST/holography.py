import numpy as np


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


def encode_hologram(Amp, Phase, X, Y, grating_period):
    """
    진폭 정보를 포함하여 SLM에 띄울 최종 Phase Mask 생성
    방식: Off-axis Holography (Carrier frequency 추가)
    """

    # Blazed Grating (Carrier Frequency) 생성
    carrier_phase = (2 * np.pi * X) / grating_period

    # 간섭 패턴 생성 (Interference pattern)
    # Arrizon type 3의 간소화된 형태 또는 일반적인 Interferogram 방식
    # 진폭 A를 위상 변조 효율로 인코딩하는 방식입니다.
    # soft_aperture는 원치 않는 고차 회절을 줄이는 데 도움을 줍니다.

    # 간단하고 강력한 방법: Phase = Target_Phase + Carrier
    # 하지만 진폭을 표현하기 위해 'Sinc' 함수 꼴로 위상 변조 깊이를 조절하거나
    # 단순히 코사인 패턴을 만듭니다.

    # 가장 직관적인 'Interferogram' 방식 (Amplitude masking)
    # SLM Phase = f(Amplitude) * sin(Phase + Carrier) 와 유사한 꼴

    # 여기서는 Arrizon 논문의 Eq. 5와 유사한 방식을 사용하여
    # 진폭 정보를 1차 회절 효율로 보냅니다.

    # f(A) 계산 (Arrizon 방식의 역함수 매핑이 정확하지만, 근사적으로 A * pi 사용 가능)
    # A=1일 때 변조가 최대(효율 최대), A=0일 때 변조 없음(효율 0)

    final_hologram = Amp * np.mod(Phase + carrier_phase, 2 * np.pi)

    # SLM은 0~2pi만 인식하므로 래핑
    # 하지만 위 식은 단순 곱셈이므로, 진폭 변조를 위해
    # 'Checkerboard' 방식이나 'Sawtooth' 변형을 주로 씁니다.

    # [실제 연구용 추천 코드]: Type 3 Arrizon encoding (simplified)
    # 이 방식이 노이즈가 적고 깔끔합니다.
    complex_field = Amp * np.exp(1j * Phase)

    # Arrizon method (Type 3)
    # H(x,y) = f(A) * sin(Psi + carrier) 가 아니라
    # 위상 값 자체를 변형합니다.

    # 실용적인 근사치:
    # A가 작으면 회절 효율을 떨어뜨리기 위해 Grating의 위상 깊이를 줄임

    phase_depth = 2 * np.arcsin(Amp)  # 진폭을 위상 깊이로 변환
    hologram_pattern = phase_depth * np.cos(Phase + carrier_phase)

    # SLM 0~2pi 매핑 (Gray scale)
    hologram_final = np.mod(hologram_pattern, 2 * np.pi)

    return hologram_final

