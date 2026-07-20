from read_data import read_spectral_data
from resample_data import resample_spectrum


def radcal(wavelength, IT_cal , Cal_DN, Sample_DN, IT_test):
    # 读取积分球光源数据
   # wavelength0, light_rad, _, _, _ = read_spectral_data(r"D:\Productions\IntegratingSphere\Portable\002\Cal3\RadLamp.txt", skip_rows=1)
    wavelength0, light_rad, _, _, _ = read_spectral_data(r"D:\Productions\IntegratingSphere\Portable\001\Cal3\Radcal-2500.txt",
                                                      skip_rows=1)
    # wavelength0, light_rad, _, _, _ = read_spectral_data(r"D:\Productions\HH3\IS3\ContrastTest1\HH2\Radtest\Rad\HH2_1927_3000nit.txt", skip_rows=1)

    light_rad = resample_spectrum(wavelength, wavelength0, light_rad)

    cal = light_rad * IT_cal / Cal_DN

    sample_rad = (Sample_DN * cal) / IT_test

    return sample_rad
