from ._mainRecon import Recon
from .ReconEnums import ReconType, AnalyticType, ProcessType
from AOT_biomaps.AOT_Experiment.Tomography import hex_to_binary_profile
from .ReconTools import get_phase_deterministic

import numpy as np
from tqdm import trange
import torch
import tqdm


class AnalyticRecon(Recon):
    def __init__(self, analyticType, **kwargs):
        super().__init__(**kwargs)
        self.reconType = ReconType.Analytic
        self.analyticType = analyticType
        self.AOsignal_demoldulated = None



    def parse_and_demodulate(self, withTumor=True):

        if withTumor:
            AOsignal = self.experiment.AOsignal_withTumor
        else:
            AOsignal = self.experiment.AOsignal_withoutTumor
        delta_x = self.experiment.params.general['dx']  # en m 
        n_piezos = self.experiment.params.acoustic['num_elements']
        demodulated_data = {}
        structured_buffer = {} 

        for i in trange(len(self.experiment.AcousticFields), desc="Demodulating AO signals"):   
            label = self.experiment.AcousticFields[i].getName_field()
            
            parts = label.split("_")
            hex_pattern = parts[0]
            angle_code = parts[-1]
            
            # Angle
            if angle_code.startswith("1"):
                angle_deg = -int(angle_code[1:])
            else:
                angle_deg = int(angle_code)
            angle_rad = np.deg2rad(angle_deg)
            
            # Onde Plane (f_s = 0)
            if set(hex_pattern.lower().replace(" ", "")) == {'f'}:
                fs_key = 0.0 # fs_key est en mm^-1 (0.0 mm^-1)
                demodulated_data[(fs_key, angle_rad)] = np.array(AOsignal[:,i])
                continue
                
            # Onde Structurée
            profile = hex_to_binary_profile(hex_pattern, n_piezos)
            
            # Calcul FS (Fréquence de Structuration)
            ft_prof = np.fft.fft(profile)
            # On regarde uniquement la partie positive non DC
            idx_max = np.argmax(np.abs(ft_prof[1:len(profile)//2])) + 1
            freqs = np.fft.fftfreq(len(profile), d=delta_x)
            
            # freqs est en m^-1 car delta_x est en mètres.
            fs_m_inv = abs(freqs[idx_max]) 
            
            # *** CORRECTION 1: Conversion de f_s en mm^-1 (mm^-1 est utilisé dans iRadon) ***
            fs_key = fs_m_inv / 1000.0 # Fréquence spatiale en mm^-1

            
            if fs_key == 0: continue

            # Calcul de la Phase (Shift)
            phase = get_phase_deterministic(profile)
            
            # Stockage par (fs, theta) et phase
            key = (fs_key, angle_rad)
            if key not in structured_buffer:
                structured_buffer[key] = {}
            
            # La moyenne est nécessaire si plusieurs acquisitions ont la même phase (pour le SNR) 
            if phase in structured_buffer[key]:
                structured_buffer[key][phase] = (structured_buffer[key][phase] + np.array(AOsignal[:,i])) / 2
            else:
                structured_buffer[key][phase] = np.array(AOsignal[:,i])


        
        for (fs, theta), phases in structured_buffer.items():
            s0 = phases.get(0.0, 0)
            s_pi_2 = phases.get(np.pi/2, 0)
            s_pi = phases.get(np.pi, 0)
            s_3pi_2 = phases.get(3*np.pi/2, 0)

            # Assurer que les zéros sont des vecteurs de la bonne taille
            example = next(val for val in phases.values() if not isinstance(val, int))
            if isinstance(s0, int): s0 = np.zeros_like(example)
            if isinstance(s_pi, int): s_pi = np.zeros_like(example)
            if isinstance(s_pi_2, int): s_pi_2 = np.zeros_like(example)
            if isinstance(s_3pi_2, int): s_3pi_2 = np.zeros_like(example)

            real = s0 - s_pi
            imag = s_pi_2 - s_3pi_2 
              
            demodulated_data[(fs, theta)] = (real - 1j * imag) / (2/np.pi)
            
        return demodulated_data

    def run(self, processType = ProcessType.PYTHON, withTumor= True):
        """
        This method is a placeholder for the analytic reconstruction process.
        It currently does not perform any operations but serves as a template for future implementations.
        """
        if(processType == ProcessType.CASToR):
            raise NotImplementedError("CASToR analytic reconstruction is not implemented yet.")
        elif(processType == ProcessType.PYTHON):
            self._analyticReconPython(withTumor)
        else:
            raise ValueError(f"Unknown analytic reconstruction type: {processType}")
        
    def checkExistingFile(self, date = None):
        raise NotImplementedError("checkExistingFile method is not implemented yet.")

    def _analyticReconPython(self,withTumor):
        """
        This method is a placeholder for the analytic reconstruction process in Python.
        It currently does not perform any operations but serves as a template for future implementations.
        
        Parameters:
            analyticType: The type of analytic reconstruction to perform (default is iFOURIER).
        """
        if withTumor:
            self.AOsignal_demoldulated = self.parse_and_demodulate(withTumor=True)
            if self.analyticType == AnalyticType.iFOURIER:
                self.reconPhantom = self._iFourierRecon(self.experiment.AOsignal_withTumor)
            elif self.analyticType == AnalyticType.iRADON:
                self.reconPhantom = self._iRadonRecon(self.experiment.AOsignal_withTumor)
            else:            
                raise ValueError(f"Unknown analytic type: {self.analyticType}")
        else:
            self.AOsignal_demoldulated = self.parse_and_demodulate(withTumor=False)
            if self.analyticType == AnalyticType.iFOURIER:
                self.reconLaser = self._iFourierRecon(self.experiment.AOsignal_withoutTumor)
            elif self.analyticType == AnalyticType.iRADON:
                self.reconLaser = self._iRadonRecon(self.experiment.AOsignal_withoutTumor)
            else:            
                raise ValueError(f"Unknown analytic type: {self.analyticType}")
    
    def _iFourierRecon(self, AOsignal):
        """
        Reconstruction d'image utilisant la transformation de Fourier inverse.
        :param AOsignal: Signal dans le domaine temporel (shape: N_t, N_theta).
        :return: Image reconstruite dans le domaine spatial.
        """
        theta = np.array([af.angle for af in self.experiment.AcousticFields])
        f_s = np.array([af.f_s for af in self.experiment.AcousticFields])
        dt = self.experiment.dt
        f_t = np.fft.fftfreq(AOsignal.shape[0], d=dt)  # fréquences temporelles
        x = self.experiment.OpticImage.laser.x
        z = self.experiment.OpticImage.laser.z
        X, Z = np.meshgrid(x, z, indexing='ij')  # grille spatiale (Nx, Nz)

        # Transformée de Fourier du signal
        s_tilde = np.fft.fft(AOsignal, axis=0)  # shape: (N_t, N_theta)

        # Initialisation de l'image reconstruite
        I_rec = np.zeros((len(x), len(z)), dtype=complex)

        # Boucle sur les angles
        for i, th in enumerate(trange(len(theta), desc="AOT-BioMaps -- iFourier Reconstruction")):
            # Coordonnées tournées
            X_prime = X * np.cos(th) + Z * np.sin(th)
            Z_prime = -X * np.sin(th) + Z * np.cos(th)

            # Pour chaque fréquence temporelle f_t[j]
            for j in range(len(f_t)):
                # Phase: exp(2jπ (X_prime * f_s[i] + Z_prime * f_t[j]))
                phase = 2j * np.pi * (X_prime * f_s[i] + Z_prime * f_t[j])
                # Contribution de cette fréquence
                I_rec += s_tilde[j, i] * np.exp(phase) * dt  # Pondération par dt pour l'intégration

        # Normalisation
        I_rec /= len(theta)
        return np.abs(I_rec)


    def _iRadonRecon(self, AOsignal):
        """
        Reconstruction d'image utilisant la méthode iRadon.

        :return: Image reconstruite.
        """
        @staticmethod
        def trapz(y, x):
            """Compute the trapezoidal rule for integration."""
            return np.sum((y[:-1] + y[1:]) * (x[1:] - x[:-1]) / 2)

        # Initialisation de l'image reconstruite
        I_rec = np.zeros((len(self.experiment.OpticImage.laser.x), len(self.experiment.OpticImage.laser.z)), dtype=complex)

        # Transformation de Fourier du signal
        s_tilde = np.fft.fft(AOsignal, axis=0)

        # Extraction des angles et des fréquences spatiales
        theta = [acoustic_field.angle for acoustic_field in self.experiment.AcousticFields]
        f_s = [acoustic_field.f_s for acoustic_field in self.experiment.AcousticFields]

        # Calcul des coordonnées transformées et intégrales
        with trange(len(theta) * 2, desc="AOT-BioMaps -- Analytic Reconstruction Tomography: iRadon") as pbar:
            for i in range(len(theta)):
                pbar.set_description("AOT-BioMaps -- Analytic Reconstruction Tomography: iRadon (Processing frequency contributions)  ---- processing on single CPU ----")
                th = theta[i]
                x_prime = self.experiment.OpticImage.x[:, np.newaxis] * np.cos(th) - self.experiment.OpticImage.z[np.newaxis, :] * np.sin(th)
                z_prime = self.experiment.OpticImage.z[np.newaxis, :] * np.cos(th) + self.experiment.OpticImage.x[:, np.newaxis] * np.sin(th)

                # Première intégrale : partie réelle
                for j in range(len(f_s)):
                    fs = f_s[j]
                    integrand = s_tilde[i, j] * np.exp(2j * np.pi * (x_prime * fs + z_prime * fs))
                    integral = self.trapz(integrand * fs, fs)
                    I_rec += 2 * np.real(integral)
                pbar.update(1)

            for i in range(len(theta)):
                pbar.set_description("AOT-BioMaps -- Analytic Reconstruction Tomography: iRadon (Processing central contributions)  ---- processing on single CPU ----")
                th = theta[i]
                x_prime = self.experiment.OpticImage.x[:, np.newaxis] * np.cos(th) - self.experiment.OpticImage.z[np.newaxis, :] * np.sin(th)
                z_prime = self.experiment.OpticImage.z[np.newaxis, :] * np.cos(th) + self.experiment.OpticImage.x[:, np.newaxis] * np.sin(th)

                # Filtrer les fréquences spatiales pour ne garder que celles inférieures ou égales à f_s_max
                filtered_f_s = np.array([fs for fs in f_s if fs <= self.f_s_max])
                integrand = s_tilde[i, np.where(np.array(f_s) == 0)[0][0]] * np.exp(2j * np.pi * z_prime * filtered_f_s)
                integral = self.trapz(integrand * filtered_f_s, filtered_f_s)
                I_rec += integral
                pbar.update(1)

        return np.abs(I_rec)
