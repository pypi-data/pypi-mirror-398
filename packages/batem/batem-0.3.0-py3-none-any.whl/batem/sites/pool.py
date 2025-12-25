# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

from batem.core.data import DataProvider, Bindings
from batem.core.library import properties
from batem.core.solar import SolarModel, SolarSystem, Collector
from batem.core.weather import humidity_ratio, compute_hc_out, compute_sky_emissivity
from scipy.constants import Stefan_Boltzmann


class Pool:

    def __init__(self, pool_length: float, pool_width: float, pool_depth: float, dp: DataProvider, e_concrete: float = 0.04, e_insulation: float = 0.1, water_setpoint_temperature: float = 23.0, heat_pump_cop: float = 3.0, P_electrical_max_W: float = 50000.0, dead_band: float = 0.5):
        self.solar_absorptance: float = 0.7
        self.water_emissivity: float = properties.get('water')['emissivity']
        self.pool_length: float = pool_length
        self.pool_width: float = pool_width
        self.pool_depth: float = pool_depth
        self.pool_volume: float = pool_length * pool_width * pool_depth
        self.pool_surface: float = pool_length * pool_width
        # Side walls area
        self.pool_side_surface: float = 2 * (pool_length + pool_width) * pool_depth
        # Floor area
        self.pool_floor_surface: float = pool_length * pool_width
        # Total insulated surface (sides + floor)
        self.pool_insulated_surface: float = self.pool_side_surface + self.pool_floor_surface

        self.water_mass: float = self.pool_volume * properties.get('water')['density']
        self.specific_heat_capacity_water: float = properties.get('water')['Cp']
        self.specific_heat_capacity_air: float = properties.get('air')['Cp']
        self.water_thermal_capacity: float = self.water_mass * self.specific_heat_capacity_water
        self.P_max_W: float = P_electrical_max_W * heat_pump_cop
        self.heat_pump_cop: float = heat_pump_cop
        self.dead_band: float = dead_band
        self.water_setpoint_temperature: float = water_setpoint_temperature
        self.dp: DataProvider = dp

        # Multi-layer wall structure: water -> convection -> concrete -> polystyrene -> ground
        h_c_water_side: float = 100.0  # W/m².K (water-to-wall convection)
        self.e_concrete: float = e_concrete
        self.e_insulation: float = e_insulation
        lambda_concrete: float = properties.get('concrete')['conductivity']  # W/m.K
        lambda_polystyrene: float = properties.get('polystyrene')['conductivity']  # W/m.K

        # Thermal resistances (m².K/W)
        R_conv = 1.0 / h_c_water_side
        R_concrete: float = e_concrete / lambda_concrete
        R_insulation: float = e_insulation / lambda_polystyrene
        R_total = R_conv + R_concrete + R_insulation

        # Overall heat transfer coefficient (W/m².K)
        self.U_insulated: float = 1.0 / R_total
        print(f"Insulated wall U-value: {self.U_insulated:.3f} W/m².K (R={R_total:.3f} m².K/W)")

        solar_system: SolarSystem = SolarSystem(SolarModel(dp.weather_data))
        # NOTE: In this convention, slope_deg=180 means horizontal surface facing the sky (pool surface)
        # exposure_deg=0 means no particular orientation (horizontal surface)
        Collector(solar_system, 'surface', surface_m2=1, exposure_deg=0, slope_deg=180)
        self.P_sun_W: list[float] = [_ * self.pool_surface for _ in solar_system.powers_W(gather_collectors=True)]
        self.T_out_C: list[float] = dp.series('weather_temperature')
        # Fixed: already divided by 100, don't divide again later
        self.humidities_coef: list[float] = [_ / 100 for _ in dp.series('weather_humidity')]
        self.wind_speed_m_s: list[float] = dp.series('weather_wind_speed_m_s')
        self.cloud_cover_pct: list[float] = [_ / 100 for _ in dp.series('weather_cloudiness')]
        self.precipitations_mm_per_hour: list[float] = dp.series('weather_precipitation')
        self.pressure_Pa: list[float] = dp.series('weather_pressure')
        self.T_side_C: float = sum(self.T_out_C) / len(self.T_out_C)  # average temperature
        self.T_inlet_water_C: float = 13.0
        self.T_water_C: float = water_setpoint_temperature

    def simulate(self, suffix: str = 'sim') -> None:
        if suffix != '':
            suffix: str = '#' + suffix
        results: dict[str, list[float]] = None
        key_mapping: dict[str, str] = None

        for k in range(len(self.dp.datetimes)):
            res: dict[str, float] = self.__step(k, self.T_water_C)
            self.T_water_C = res["T_water_C"]

            if results is None:
                results = {key + suffix: [res[key]] for key in res.keys()}
                key_mapping = {key + suffix: key for key in res.keys()}
            else:
                for result_key, original_key in key_mapping.items():
                    results[result_key].append(res.get(original_key, 0.0))

        # ========== OUTPUT ==========
        for variable_name, values in results.items():
            self.dp.add_var(variable_name, values)

    def __repr__(self) -> str:
        return f"SwimmingPool(L={self.pool_length} x W={self.pool_width} x d={self.pool_depth}, concrete={self.e_concrete*100:.0f}cm + insulation={self.e_insulation*100:.0f}cm, U_walls={self.U_insulated:.3f} W/m²K)"

    def __P_loss_kW(self, k: int, T_water_C: float) -> dict[str, float]:
        """
        Compute heating power required to maintain pool at T_w (°C).
        Returns dict with power breakdown (W for surface convection, kW for others).
        Positive values = heat losses that must be compensated by heating.
        """
        # Safety check: clamp water temperature to realistic range
        T_water_C = max(-5.0, min(95.0, T_water_C))

        LV: float = 2.45e6                # J/kg, latent heat of vaporization
        LEWIS: float = 1.0                # Lewis number for humid air
        T_out_C: float = self.T_out_C[k]
        RH_coef: float = self.humidities_coef[k]
        wind_speed_m_s: float = self.wind_speed_m_s[k]
        cloud_cover_coef: float = self.cloud_cover_pct[k]
        precipitation_mm_h: float = self.precipitations_mm_per_hour[k]
        p_atm: float = self.pressure_Pa[k]
        powers_kW: dict[str, float] = {}
        # Ground temperature (constant at 13°C)
        T_ground_C: float = self.T_inlet_water_C
        hc_out: float = compute_hc_out(wind_speed_m_s)  # Convection coefficient
        epsilon_sky: float = compute_sky_emissivity(T_out_C, cloud_cover_coef)  # Sky emissivity

        # 1) Surface convection (water to air)
        P_surface_convection_W = hc_out * max(0.0, T_water_C - T_out_C) * self.pool_surface
        powers_kW["P_surface_convection_kW"] = P_surface_convection_W / 1000.0

        # 2) Evaporation (Lewis relation)
        Y_ws = humidity_ratio(T_water_C, 1.0, p_atm) / 1000.0  # saturated at water temp (convert g/kg to kg/kg)
        Y_air = humidity_ratio(T_out_C, RH_coef, p_atm) / 1000.0  # ambient (convert g/kg to kg/kg)
        evaporative_factor = hc_out * LV * (LEWIS ** (-2.0 / 3.0)) / self.specific_heat_capacity_air
        P_evaporation_W = evaporative_factor * max(0.0, Y_ws - Y_air) * self.pool_surface
        powers_kW["P_evaporation_kW"] = P_evaporation_W / 1000.0
        powers_kW["Y_ws"] = Y_ws
        powers_kW["Y_air"] = Y_air

        # 3) Heat loss through insulated walls and floor
        # Multi-layer structure: water -> concrete (4cm) -> insulation (10cm) -> ground (13°C)
        # Q = U × A × (T_water - T_ground)
        P_walls_floor_W: float = self.U_insulated * max(0.0, T_water_C - T_ground_C) * self.pool_insulated_surface
        powers_kW["P_walls_floor_kW"] = P_walls_floor_W / 1000.0

        # 4) Net long-wave radiation (water surface to sky)
        # Water emits: ε_water × σ × T_water^4
        # Sky radiates back: ε_sky × σ × T_air^4 (effective sky temperature ≈ air temperature)
        T_water_K = T_water_C + 273.15
        T_air_K = T_out_C + 273.15
        P_radiation_net_W: float = self.pool_surface * Stefan_Boltzmann * (
            self.water_emissivity * T_water_K**4 - epsilon_sky * T_air_K**4
        )
        powers_kW["P_radiation_net_kW"] = P_radiation_net_W / 1000.0

        # 5) Solar gain (negative = gain, reduces heating requirement)
        P_solar_W = -self.solar_absorptance * self.P_sun_W[k]
        powers_kW["P_solar_gain_kW"] = -P_solar_W / 1000.0  # store as positive gain

        # 6) Precipitation effect - Fixed: use pool_surface
        P_precipitation_W: float = 0.0
        if precipitation_mm_h > 0:
            mass_flow_rate_kg_s: float = precipitation_mm_h * self.pool_surface / 3600.0  # kg/s
            P_precipitation_W = mass_flow_rate_kg_s * self.specific_heat_capacity_water * (T_water_C - T_out_C)
        powers_kW["P_precipitation_kW"] = P_precipitation_W / 1000.0

        # 7) Inlet water for evaporation compensation
        P_inlet_water_W = 0.0
        if P_evaporation_W > 0:
            mass_flow_evap_kg_s = P_evaporation_W / LV
            P_inlet_water_W = mass_flow_evap_kg_s * self.specific_heat_capacity_water * (T_water_C - self.T_inlet_water_C)
        powers_kW["P_inlet_water_kW"] = P_inlet_water_W / 1000.0

        # Total power requirement
        # Positive = loss (needs heating), Negative = gain (cooling effect)
        P_total_W = (P_surface_convection_W + P_evaporation_W + P_walls_floor_W +
                     P_radiation_net_W + P_solar_W + P_precipitation_W + P_inlet_water_W)
        powers_kW["P_total_kW"] = P_total_W / 1000.0
        return powers_kW

    def __P_need(self, T_water: float, T_setpoint: float, P_loss_total_W: float) -> float:
        """
        Compute heating power based on setpoint control.

        Args:
            T_water: Current water temperature (°C)
            T_setpoint: Target temperature (°C)
            P_loss_total_W: Current power loss (W)

        Returns:
            Heating power (W)
        """
        error: float = T_setpoint - T_water
        if error > self.dead_band:
            P_out = self.P_max_W
        elif error < -self.dead_band:
            P_out = 0.0
        else:
            P_out = min(self.P_max_W, max(0, P_loss_total_W))

        return P_out

    def __dT_dt(self, k: int, T_water_C: float) -> float:
        """
        Compute dT/dt for the pool temperature.
        This is the right-hand side of the ODE: dT/dt = f(T, t)

        Returns:
            dT/dt in K/s
        """
        P_loss_kW: dict[str, float] = self.__P_loss_kW(k, T_water_C)
        P_loss_total_W: float = P_loss_kW["P_total_kW"] * 1000.0
        P_heating: float = self.__P_need(T_water_C, self.water_setpoint_temperature, P_loss_total_W)
        P_net: float = P_heating - P_loss_total_W
        return P_net / self.water_thermal_capacity  # K/s

    def __step(self, k: int, T_water_C: float) -> dict[str, float]:
        """Perform one time step using Forward Euler integration."""
        dt: float = 3600.0  # 1 hour time step (s)

        # FORWARD EULER (1st order) Simple: T(n+1) = T(n) + dt * f(T(n))
        k1 = self.__dT_dt(k, T_water_C)
        T_water_new = T_water_C + dt * k1

        # Safety check: limit temperature change per time step
        max_dT_per_step = 10.0  # °C max change per hour
        if abs(T_water_new - T_water_C) > max_dT_per_step:
            T_water_new = T_water_C + max_dT_per_step * (1 if T_water_new > T_water_C else -1)

        # Clamp to realistic range
        T_water_new = max(0.0, min(90.0, T_water_new))
        # dT_dt_final = (T_water_new - T_water_C) / dt

        # Calculate final state results at new temperature
        P_loss_kW: dict[str, float] = self.__P_loss_kW(k, T_water_new)

        P_loss_final_W: float = P_loss_kW["P_total_kW"] * 1000.0
        P_heating_final: float = self.__P_need(T_water_new, self.water_setpoint_temperature, P_loss_final_W)
        P_net_final = P_heating_final - P_loss_final_W
        P_electrical: float = P_heating_final / self.heat_pump_cop if self.heat_pump_cop > 0 else 0.0

        # Add to results
        P_loss_kW["T_water_C"] = T_water_new
        P_loss_kW["P_heating_kW"] = P_heating_final / 1000.0
        P_loss_kW["P_electrical_kW"] = P_electrical / 1000.0
        P_loss_kW["Pimbalance_kW"] = P_net_final / 1000.0

        return P_loss_kW


if __name__ == "__main__":
    year = 2023
    # Pool geometry
    L, W, d = 12.0, 5.0, 1.4  # length, width, depth (m)
    e_concrete = 0.04
    e_insulation = 0.1

    # Heating system
    water_setpoint_temperature = 23  # °C
    heat_pump_cop = 3.0
    P_max = 10000.0  # W (50 kW maximum)
    dead_band = 0.5

    # Load weather data
    latitude_north_deg, longitude_east_deg = 44.88315521161671, 5.687480092332743
    dp: DataProvider = DataProvider(
        location='camping-mayres-savel',
        latitude_north_deg=latitude_north_deg,
        longitude_east_deg=longitude_east_deg,
        starting_stringdate='01/01/%i' % year,
        ending_stringdate='31/12/%i' % year,
        bindings=Bindings(),
        albedo=0.2,
        pollution=0.
    )

    # Create insulated pool (4cm concrete + 10cm polystyrene)
    pool: Pool = Pool(L, W, d, dp, e_concrete=e_concrete, e_insulation=e_insulation, water_setpoint_temperature=water_setpoint_temperature, heat_pump_cop=heat_pump_cop, P_electrical_max_W=P_max, dead_band=dead_band)
    print(pool)
    pool.simulate(suffix='year')

    dp.plot('T_water_C#year', 'P_electrical_kW#year', plot_type='timeplot')
    dp.plot('P_electrical_kW#year', plot_type='timeplot', averager='sum month')

    dp_short: DataProvider = dp.excerpt(starting_stringdate='01/06/%i' % year, ending_stringdate='31/08/%i' % year)
    pool_short: Pool = Pool(L, W, d, dp_short, e_concrete=e_concrete, e_insulation=e_insulation, water_setpoint_temperature=water_setpoint_temperature, heat_pump_cop=heat_pump_cop, P_electrical_max_W=P_max, dead_band=dead_band)
    print(pool_short)
    pool_short.simulate(suffix='short')
    dp_short.plot('P_electrical_kW#short', plot_type='timeplot', averager='- hour')
    dp_short.plot('P_inlet_water_kW#short', 'P_precipitation_kW#short', 'P_radiation_net_kW#short', 'P_walls_floor_kW#short', 'P_evaporation_kW#short', 'P_surface_convection_kW#short', plot_type='piechart', averager='- hour')
    dp.plot()
