import numpy as np
import matplotlib.pyplot as plt

sin = np.sin
cos = np.cos
pi = np.pi

#________LINAC_Dynamics_____________________________________
from scipy import constants
import scipy.constants as sciCont
#constants
from scipy.constants import speed_of_light
from scipy.constants import e
from scipy import optimize
from scipy.optimize import fsolve
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
#muon mass in eV
m_mu = 105.65837555*1e6
#pi
pi = np.pi
#speed of light in [m/s]
c = constants.speed_of_light
#unitary charge
e = constants.e
def dpsi_n1(dpsi_n0, dW_n0, W_kin, w_RF, L):
    W = W_kin + m_mu
    beta = np.sqrt(1 - (m_mu*m_mu)/(W*W))
    gamma = W/m_mu
    return dpsi_n0 - w_RF * dW_n0 * L / (m_mu*c * (beta*gamma)**3)
def dW_n1_acc(dW_n0, RF_field, dpsi_n1, psi_stable, W_kin, w_RF, L):
    W = W_kin + m_mu
    beta = np.sqrt(1 - (m_mu*m_mu)/(W*W))
    lambda_RF = 2 * pi * c / w_RF
    T_trans = np.sin(pi*L/(beta * lambda_RF)) / (pi*L / (beta* lambda_RF))
    return dW_n0 + L * T_trans * RF_field * (np.sin(dpsi_n1) - sin(psi_stable))
def Tracker(dpsi, dW, cell_number, W_kin, w_RF, RF_field, psi_stable, L_gap, L_drift):
    W = W_kin + m_mu
    gamma = W / m_mu
    lambda_RF = 2 * pi * c / w_RF
    for j in range(0,cell_number):
        dpsi = dpsi_n1(dpsi, dW, W_kin, w_RF, L_gap)
        dW_final = dW_n1_acc(dW, RF_field, dpsi, psi_stable, W_kin, w_RF, L_gap)
        dpsi_final = dpsi_n1(dpsi, dW_final, W_kin, w_RF, L_drift)
        dpsi = dpsi_final
        dW = dW_final
        #Update W_kin____________
        W = W_kin + m_mu
        beta = np.sqrt(1 - (m_mu*m_mu)/(W*W))
        gamma = W / m_mu
        T_trans = np.sin(pi*L_gap/(beta * lambda_RF)) / (pi*L_gap / (beta* lambda_RF))
        W_kin = W_kin + T_trans*L_gap*RF_field * np.sin(psi_stable)
        #________________________
    return dpsi, dW, W_kin
def Separatrix(W_kin, RF_field, w_RF, psi_stable, L_gap, L_drift):
    sign = lambda a: 1 if a>0 else -1 if a<0 else 0
    code = 0
    #____________________
    W = W_kin + m_mu
    gamma = W / m_mu
    dpsi_i = np.linspace(np.pi - psi_stable - 0.001, np.pi - psi_stable - 0.001, 1)
    dW_i = np.linspace(0, 0, 1)
    coordinates = []
    for i in range(0, len(dpsi_i)):
        dpsis = []
        dWs = []
        dpsi = dpsi_i[i]
        dW = dW_i[i]
        dWs.append(dW ) #in MeV
        dpsis.append(dpsi)
        #________________________
        number = 100000
        for j in range(0,number):
            if j == 2:
                beginn = sign(dpsis[1] - dpsis[2])
            dpsi = dpsi_n1(dpsi, dW, W_kin, w_RF, L_gap)
            dW_final = dW_n1_acc(dW, RF_field, dpsi, psi_stable, W_kin, w_RF, L_gap)
            dpsi_final = dpsi_n1(dpsi, dW_final, W_kin, w_RF, L_drift)
            dpsis.append(dpsi_final)
            dWs.append(dW_final )
            dpsi = dpsi_final
            dW = dW_final
            if j > 2:
                if sign(dpsis[j] - dpsis[j+1]) != beginn:
                    code = code + 1
                    beginn = - beginn
            if code == 2:
                break
        dpsis.pop()
        dWs.pop()
        coordinates.append([dpsis, dWs])
    return np.array(coordinates[0])
def hamilton_phi(phi_1, phi_stab):
    if phi_stab == 0:
        return -phi_1
    else:
        def opt_phi(y):
            x = np.cos(phi_1) + phi_1*np.sin(phi_stab) - np.cos(y) - y*np.sin(phi_stab)
            return x
        phi_2 = optimize.fsolve(opt_phi, phi_stab)
        return phi_2[0]
def hamilton_dW(psi, W_kin, w_RF, V_RF, psi_stable, L_gap, L_drift):
    lambda_RF = 2 * pi * c / w_RF
    W = W_kin + m_mu
    beta = np.sqrt(1 - (m_mu*m_mu)/(W*W))
    gamma = W / m_mu
    T_trans = np.sin(pi*L_gap/(beta * lambda_RF)) / (pi*L_gap / (beta* lambda_RF))
    H1 = T_trans * V_RF * (-2*np.cos(psi_stable) + (np.pi - 2*psi_stable)*sin(psi_stable))
    fact = 2 * (L_gap/(L_gap + L_drift)) * beta**3 * gamma**2 * c * W / w_RF
    dE =  fact * ( T_trans * V_RF * (np.cos(psi) - np.cos(psi_stable) + (psi - psi_stable)*np.sin(psi_stable)) - H1 )
    return np.sqrt(abs(dE))
def hamilton_dW_mid(psi, psi_mid, W_kin, w_RF, V_RF, psi_stable, L_gap, L_drift):
    lambda_RF = 2 * pi * c / w_RF
    W = W_kin + m_mu
    beta = np.sqrt(1 - (m_mu*m_mu)/(W*W))
    gamma = W / m_mu
    T_trans = np.sin(pi*L_gap/(beta * lambda_RF)) / (pi*L_gap / (beta* lambda_RF))
    H1 = T_trans * V_RF * ( np.cos(psi) - np.cos(psi_stable) + (psi - psi_stable)*np.sin(psi_stable) )
    fact = 2 * (L_gap/(L_gap + L_drift)) * beta**3 * gamma**2 * c * W / w_RF
    dE =  fact * ( T_trans * V_RF * (np.cos(psi_mid) - np.cos(psi_stable) + (psi_mid - psi_stable)*np.sin(psi_stable)) - H1 )
    return np.sqrt(abs(dE))
def Particle_generator(sigma_psi, W_kin, w_RF, psi_stable, L_gap, L_drift, RF_field, Number):
    psi_1 = psi_stable + sigma_psi
    psi_2 = hamilton_phi(psi_1, psi_stable)
    mean_psi = (psi_1 + psi_2)*0.5
    mean_DeltaE = 0
    #matched beam
    sig_DeltaE = hamilton_dW_mid(psi_1, mean_psi, W_kin, w_RF, RF_field, psi_stable, L_gap, L_drift )
    beam = np.random.randn(2,Number)
    beam[0,:] = psi_stable + sigma_psi*beam[0,:]
    beam[1,:] = mean_DeltaE + sig_DeltaE*beam[1,:]
    return beam, mean_psi, mean_DeltaE, sig_DeltaE
def Separatrix_Sort(W_kin, RF_field, w_RF, psi_stable, L_gap, L_drift, phi_coord, dE_coord):
    x = np.array ( Separatrix(W_kin, RF_field, w_RF, psi_stable, L_gap, L_drift) )
    dphi_spx =  x[0]
    dW_spx = x[1]
    point_list = Polygon(zip( dphi_spx, dW_spx ) )
    #Sorting_algorithm__________________________________________________________________________
    SEPARATRIX = Polygon(point_list)
    points = list(zip( phi_coord, dE_coord ) )
    #___________________________________________________________________________________________
    uebrig = 0
    j = 0
    for i in range(len(points)):
        point = Point(points[i])
        if SEPARATRIX.contains(point) == True:
            uebrig = uebrig + 1
    for i in range(len(points)):
        point = Point(points[j])
        if SEPARATRIX.contains(point) == False:
            phi_coord = np.delete(phi_coord, j)
            dE_coord = np.delete(dE_coord, j)
            points.remove(points[j])
        else: j = j + 1
    return dphi_spx, dW_spx, uebrig, phi_coord, dE_coord
def long_phaspace(dpsi, dW):
    #longitudinal phase space in rad x eV
    mean_psi = np.mean(dpsi)
    mean_dW = np.mean(dW)
    var_dpsi = np.std(dpsi - mean_psi) ** 2
    var_dW = np.std(dW - mean_dW) ** 2
    sigma_dpsi_dW = np.mean((dpsi - mean_psi)*(dW - mean_dW))
    A = np.sqrt ( var_dpsi*var_dW - sigma_dpsi_dW**2 )
    return A
def long_emit_norm_eVs(dpsi, dW, w_RF):
    area = long_phaspace(dpsi, dW)
    return area / w_RF
def long_emit_norm_m(dpsi, dW, w_RF):
    area = long_phaspace(dpsi, dW)
    return area / w_RF * c / m_mu
def long_emit_norm_eVm(dpsi, dW, w_RF):
    area = long_phaspace(dpsi, dW)
    return area / w_RF * c
def acceptance(W_kin_1, RF_field, w_RF, psi_stable, L_gap, L_drift):
    x = np.array ( Separatrix(W_kin_1, RF_field, w_RF, psi_stable, L_gap, L_drift) )
    dphi_spx =  x[0]
    dW_spx = x[1]
    point_list = Polygon(zip( dphi_spx, dW_spx ) )
    emittance = point_list.area
    return emittance
#----------------------------------------------------------------------------------------#
#_____________WINDOWS____________________________________________________________________#
#---------Parameters for Windows---------------------------------------------------------#
e0 = 1.602176634e-19        #Elementary charge [C = As]
eps0 = 8.8541878128e-12     #vacuum permittivity [(As)/(Vm)]
m_e = 9.1093837015e-31      #mass of electron [kg]
c = 299792458               #Speed of light [v/s]
NA = 6.02214076e23          #Avogadro [1/mol]
E_mu = m_mu * 1e-6 #Energy of rest muon [MeV]
E_e = (m_e*c**2/e0)*10**-6  #Energy of rest electron [MeV]
r_e = e0**2/(4*np.pi*eps0*m_e*c**2)#electron radius
K = (4*np.pi*NA*r_e**2*m_e*c**2)/e0 *10**-2
#----------------------------------------------------------------------------------------#
#Beryllium
#material densities in g/cm**3
rho_Be = 1.848      # Beryllium
#mean ionization energy in MeV
I_Be = 63.7e-6      #Beryllium
#Relation between Z and A
j_Be = 0.44
#Charge number of atoms
Z_Be = 4
#Mass number of atoms
A_Be = 9.0121831
#Radiation length in cm
L_Be = 35.28        #Beryllium
#specific heat capcity in J/( kg K )
c_Be = 1825.4448
def Be(Ekin): #enter kinetic energy in MeV
#    E_kin = Ekin * 1e-6
    x = Ekin+E_mu #Total energy
    beta = np.sqrt(1-(E_mu**2/x**2))    #Lorentz beta
    gamma = 1/np.sqrt(1-beta**2)        #Lorentz gamma
    D_Be = np.log((4*E_e**2*beta**4*gamma**4)/((1+2*gamma*(E_e/E_mu)+(E_e/E_mu)**2)*I_Be**2))
    y_Be = K/(beta**2)*j_Be*(0.5*D_Be-beta**2) * rho_Be #Energy loss [MeV/cm]
    return y_Be #Energy loss [MeV/cm]
#Aluminum_______________________________________________________________________________#
#material densities in g/cm**3
rho_Al = 2.699      # Aluminum
#mean ionization energy in MeV
I_Al = 166e-6       #Aluminum
#Relation between Z and A
j_Al = 0.48
#Charge number of atoms
Z_Al = 13
#Mass number of atoms
A_Al = 26.9815385
#Radiation length in cm
L_Al = 8.897        #Aluminum
#specific heat capcity in J/( kg K )
c_Al = 900
def Al(Ekin): #enter kinetic energy in MeV
    x = Ekin+E_mu #Total energy
    beta = np.sqrt(1-(E_mu**2/x**2))    #Lorentz beta
    gamma = 1/np.sqrt(1-beta**2)        #Lorentz gamma
    D_Al = np.log((4*E_e**2*beta**4*gamma**4)/((1+2*gamma*(E_e/E_mu)+(E_e/E_mu)**2)*I_Al**2))
    y_Al = K/(beta**2)*j_Al*(0.5*D_Al-beta**2) * rho_Al #Energy loss [MeV/cm]
    return y_Al #Energy loss [MeV/cm]
#Lithium_______________________________________________________________________________#
#material densities in g/cm**3
rho_Li = 0.5340     #Lithium
#mean ionization energy in MeV
I_Li = 40 * 1e-6        #Lithium
#Relation between Z and A
j_Li = 0.43
#Charge number of atoms
Z_Li = 3
#Mass number of atoms
A_Li = 6.941
#Radiation length in cm
L_Li = 155.0       #Lithium
#specific heat capcity in J/( kg K )
c_Li = 3.6 * 1e3
def Li(Ekin): #enter kinetic energy in eV
    x = Ekin+E_mu #Total energy
    beta = np.sqrt(1-(E_mu**2/x**2))    #Lorentz beta
    gamma = 1/np.sqrt(1-beta**2)        #Lorentz gamma
    D_Li = np.log((4*E_e**2*beta**4*gamma**4)/((1+2*gamma*(E_e/E_mu)+(E_e/E_mu)**2)*I_Li**2))
    y_Li = K/(beta**2)*j_Li*(0.5*D_Li-beta**2) * rho_Li #Energy loss [MeV/cm]
    return y_Li #Energy loss [MeV/cm]
#Lithium hydrade
#material densities in g/cm**3
rho_LiH = 0.820    #Lithium
#mean ionization energy in MeV
I_LiH = 36.5 * 1e-6        #Lithium
#Relation between Z and A
j_LiH = 0.50
#Charge number of atoms
Z_LiH = 4
#Mass number of atoms
A_LiH = 8
#Radiation length in cm
L_LiH = 79.2       #Lithium
#specific heat capcity in J/( kg K )
c_LiH = 3.51 * 1e3
def LiH(Ekin): #enter kinetic energy in eV
    x = Ekin+E_mu #Total energy
    beta = np.sqrt(1-(E_mu**2/x**2))    #Lorentz beta
    gamma = 1/np.sqrt(1-beta**2)        #Lorentz gamma
    D_LiH = np.log((4*E_e**2*beta**4*gamma**4)/((1+2*gamma*(E_e/E_mu)+(E_e/E_mu)**2)*I_LiH**2))
    y_LiH = K/(beta**2)*j_LiH*(0.5*D_LiH-beta**2) * rho_LiH #Energy loss [MeV/cm]
    return y_LiH #Energy loss [MeV/cm]
#Si3N4
#material densities in g/cm**3
rho_Si3N4 = 3.17     #Lithium
#mean ionization energy in MeV
I_Si3N4 = 36.5 * 1e-6        #Lithium
#Relation between Z and A
j_Si3N4 = 21 / 42.0922
#Charge number of atoms
Z_Si3N4 = 21
#Mass number of atoms
A_Si3N4 = 42.0922
#Radiation length in cm
L_Si3N4 = 79.2       #Lithium
#specific heat capcity in J/( kg K )
c_Si3N4 = 3.51 * 1e3
def Si3N4(Ekin): #enter kinetic energy in eV
    x = Ekin+E_mu #Total energy
    beta = np.sqrt(1-(E_mu**2/x**2))    #Lorentz beta
    gamma = 1/np.sqrt(1-beta**2)        #Lorentz gamma
    D_Si3N4 = np.log((4*E_e**2*beta**4*gamma**4)/((1+2*gamma*(E_e/E_mu)+(E_e/E_mu)**2)*I_Si3N4**2))
    y_Si3N4= K/(beta**2)*j_Si3N4*(0.5*D_Si3N4-beta**2) * rho_Si3N4#Energy loss [MeV/cm]
    return y_Si3N4 #Energy loss [MeV/cm]
#Liquid_hydrogen__________________________________________________________________________#
#material densities in g/cm**3
rho_H2L = 0.07080   # Liquide hydrogen
#mean ionization energy in MeV
I_H2L = 21.8e-6     #Liquid hydrogen
#Relation between Z and A
j_H = 1
#Charge number of atoms
Z_H = 1
#Mass number of atoms
A_H = 1.008
#Radiation length in cm
L_H2L = 890.4       #Liquid Hydrogen
#specific heat capcity in J/( kg K )
c_H2L = 10000
def H2L(Ekin): #enter kinetic energy in MeV
    x = Ekin+E_mu #Total energy
    beta = np.sqrt(1-(E_mu**2/x**2))    #Lorentz beta
    gamma = 1/np.sqrt(1-beta**2)        #Lorentz gamma
    D_H2L = np.log((4*E_e**2*beta**4*gamma**4)/((1+2*gamma*(E_e/E_mu)+(E_e/E_mu)**2)*I_H2L**2))
    y_H2L = K/(beta**2)*j_H*(0.5*D_H2L-beta**2) * rho_H2L #Energy loss [MeV/cm]
    return y_H2L #Energy loss [MeV/cm]
#Water_________________________________________________________________________________#
#material densities in g/cm**3
rho_H2O = 1   # Liquide hydrogen
#mean ionization energy in MeV
I_H2O = 79.7 * 1e-6     #Liquid hydrogen
#Charge number of atoms
Z_H2O = 8
#Mass number of atoms
A_H2O = 18
#Relation between Z and A
j_H2O = Z_H2O/A_H2O
#Radiation length in cm
L_H2O = 36.08       #Liquid Hydrogen
#specific heat capcity in J/( kg K )
c_H2O = 4182
def H2O(Ekin): #enter kinetic energy in MeV
    x = E_kin+E_mu #Total energy
    beta = np.sqrt(1-(E_mu**2/x**2))    #Lorentz beta
    gamma = 1/np.sqrt(1-beta**2)        #Lorentz gamma
    D_H2O = np.log((4*E_e**2*beta**4*gamma**4)/((1+2*gamma*(E_e/E_mu)+(E_e/E_mu)**2)*I_H2O**2))
    y_H2O = K/(beta**2)*j_H2O*(0.5*D_H2O-beta**2) * rho_H2O #Energy loss [MeV/cm]
    return y_H2O #Energy loss [MeV/cm]
#----------------------------------------------------------------------------------------#
def Deposition(Func, E_init, thickness, step):
    #energy deposition of a single muon
    #Func is Be(E_init), E_init in eV, thickness in cm!
    E_init = E_init * 1e-6
    thickness_cm = thickness * 1e2
    step_cm = step * 1e2 #
    depos = []
    for i in range(0, int(thickness/step)):
       if E_init > 3:
            loss = Func(E_init) * step_cm
            E_init = E_init - loss
            depos.append(loss * 1e6) # save deposited energy in [eV]
       else: depos.append(0)
    return np.array(depos)

def H2L_densy(Ekin, rho): #enter kinetic energy in MeV
    x = Ekin+E_mu #Total energy
    beta = np.sqrt(1-(E_mu**2/x**2))    #Lorentz beta
    gamma = 1/np.sqrt(1-beta**2)        #Lorentz gamma
    D_H2L = np.log((4*E_e**2*beta**4*gamma**4)/((1+2*gamma*(E_e/E_mu)+(E_e/E_mu)**2)*I_H2L**2))
    y_H2L = K/(beta**2)*j_H*(0.5*D_H2L-beta**2) * rho #Energy loss [MeV/cm]
    return y_H2L #Energy loss [MeV/cm]
def Deposition_densy(Func, E_init, rho, thickness, step):
    #energy deposition of a single muon
    #Func is Be(E_init), E_init in eV, thickness in cm!
    E_init = E_init * 1e-6
    thickness_cm = thickness * 1e2
    step_cm = step * 1e2 #
    depos = []
    for i in range(0, int(thickness/step)):
       if E_init > 3:
            loss = Func(E_init, rho) * step_cm
            E_init = E_init - loss
            depos.append(loss * 1e6) # save deposited energy in [eV]
       else: depos.append(0)
    return np.array(depos)



from . import elliptic_integrals as ell

from scipy.interpolate import interp1d

# Constants
mu0 = 4 * np.pi * 1e-7
Gc_2 = 0.29979258 * 0.5 #half of the speed of light *1E-9

class SolenoidSheet:
    def __init__(self, current_density, radius_inner, radius_outer, rho, L_sol, nSheet, position):
        self.current_density = current_density
        self.radius_inner = radius_inner
        self.radius_outer = radius_outer
        self.rho = rho
        self.L_sol = L_sol
        self.nSheet = nSheet
        self.position = position
        
        self.zeta_p = lambda zgrid: zgrid - (position - L_sol * 0.5)
        self.zeta_m = lambda zgrid: zgrid - (position + L_sol * 0.5)
        
    @property
    def t_thick(self):
        return self.radius_outer - self.radius_inner

    @property
    def coil_xsec(self):
        return self.L_sol * self.t_thick

    @property
    def I_current(self):
        return self.coil_xsec * self.current_density / self.nSheet
            
    def Bz_Sheet(self, zgrid):
        dt = self.t_thick / self.nSheet
        r_values = self.radius_inner + (0.5 + np.arange(self.nSheet)) * dt
        Bz_sum = np.sum([self.B_long(r, zgrid) for r in r_values], axis=0)
        return Bz_sum * 1e6
        
    def Brho_Sheet(self, zgrid):
        if self.rho == 0.:
            return np.zeros_like(zgrid)
        else:
            dt = self.t_thick / self.nSheet
            r_values = self.radius_inner + (0.5 + np.arange(self.nSheet)) * dt
            Brho_sum = np.sum([self.B_rho(r, zgrid) for r in r_values], axis=0)
            return Brho_sum * 1e6
            
    def B_rho(self, r, zgrid):
        if abs(self.rho) < 1e-9:
            return 0.
        
        zeta_p = self.zeta_p(zgrid)
        zeta_m = self.zeta_m(zgrid)
        
        if abs(abs(r) - abs(self.rho)) < 1e-9 and (np.abs(zeta_m) < 1e-9).any() :
            return 0.
        if abs(abs(r) - abs(self.rho)) < 1e-9 and (np.abs(zeta_p) < 1e-9).any():
            return 0.
        else:
            fac = mu0 * self.I_current * 0.25 / np.pi / self.L_sol / self.rho
            b1_r = self.br_int(r, zeta_p)
            b2_r = self.br_int(r, zeta_m)
            return fac * (b1_r - b2_r)
            
    def B_long(self, r, zgrid):
        zeta_p = self.zeta_p(zgrid)
        zeta_m = self.zeta_m(zgrid)

        if abs(self.rho) < 1e-9:
            fac = mu0 * self.I_current * 0.5 / self.L_sol
            term1 = zeta_p / (r*r + zeta_p*zeta_p)**0.5
            term2 = zeta_m / (r*r + zeta_m*zeta_m)**0.5
            return fac * (term1 - term2)
        else:
            if abs(abs(r) - abs(self.rho)) < 1e-5:
                return 0.
            else:
                fac = mu0 * self.I_current * 0.5 / np.pi / self.L_sol
                b1 = self.bz_int(r, zeta_p)
                b2 = self.bz_int(r, zeta_m)
                return fac * (b1 - b2)
        
    def br_int(self, r, zeta):
        vorfac_r = np.sqrt((r + self.rho)**2 + zeta**2)
        k2 = 4. * r * self.rho / ((r + self.rho)**2 + zeta**2)
        K = ell.ellipK(k2)
        E = ell.ellipE(k2)
        return vorfac_r * ((k2 - 2) * K + 2 * E)
        
    def bz_int(self, r, zeta):
        int_cal = (r - self.rho) / (r + self.rho)
        vorfac = zeta / np.sqrt((r + self.rho)**2 + zeta**2)
        k2 = 4. * r * self.rho / ((r + self.rho)**2 + zeta**2)
        h2 = 4. * r * self.rho / (r + self.rho)**2 * np.ones(np.shape(k2))
        PI = ell.ellipPI(h2, k2)
        K = ell.ellipK(k2)
        return vorfac * (K + int_cal * PI)

class MagneticField:
    def __init__(self):
        self.solenoids = []

    def add_solenoid(self, solenoid):
        self.solenoids.append(solenoid)

    def superposed_field_z(self, zgrid):
        total_Bz = np.zeros_like(zgrid)
        for solenoid in self.solenoids:
            total_Bz += solenoid.Bz_Sheet(zgrid)
        return total_Bz
        
    def superposed_field_r(self, zgrid):
        total_Br = np.zeros_like(zgrid)
        for solenoid in self.solenoids:
            total_Br += solenoid.Brho_Sheet(zgrid)
        return total_Br
        
def B_field_interpol(zgrid, Bfield):
    if len(zgrid) ==  len(Bfield):
        Binterpol = interp1d(zgrid, Bfield, kind='cubic', fill_value="extrapolate")
        return Binterpol
    else:
        return print('Interpol error: length of B-field array and z-grid is not equal')


# Define the system of first-order equations
def beta_system(b, s, kappa_interp, L):
    b1, b2 = b
    db1ds = b2
    k_s = kappa_interp(s)
    db2ds = (b2**2 + 4*(1 + L**2) - 4*b1**2 * k_s**2) / (2 * b1)
    return [db1ds, db2ds]


from ._mymath import solve_beta_rk4, nelder_mead

__all__ = [
    "solve_beta_rk4",
    "nelder_mead",
]
