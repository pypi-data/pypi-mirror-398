
import os

from plotly.subplots import make_subplots
import plotly.graph_objects as go

import pandas as pd

from batem.ecommunity.indicators import (
    cost, self_consumption, self_sufficiency)
from batem.reno.constants import MANAGER_TYPE
from batem.reno.indicators import (
    demanded_contribution, recommendations_per_day, savings_per_day)
from batem.reno.simulation.recommendation import RecommendationType
from batem.reno.simulation.scenario import Scenario, ScenarioBuilder
from batem.reno.utils import FilePathBuilder, TimeSpaceHandler, parse_args


class CommunityPlotter:
    def __init__(self):
        pass

    def plot(self, results_path: str, scenario_path: str, show: bool = False):
        df = pd.read_csv(results_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        scenario = ScenarioBuilder().build(scenario_path)

        title = self._get_tile(df, scenario)
        indications_title = self._get_indications_title(df, scenario)

        # Create figure with two subplots
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=(title, "Presence", indications_title, "Metrics"),
            specs=[[{"type": "xy"}],
                   [{"type": "xy"}],
                   [{"type": "xy"}],
                   [{"type": "table"}]],
            row_heights=[0.4, 0.3, 0.3, 0.3]
        )

        exp_consumption = df.filter(like='exp_')
        sim_consumption = df.filter(like='sim_')
        presence = df.filter(like='presence_')
        recommendations = [RecommendationType(r) for r in df['manager']]

        total_exp_consumption = df.filter(like='exp_').sum(axis=1)
        total_sim_consumption = df.filter(like='sim_').sum(axis=1)

        ids = self._extract_ids(exp_consumption.columns.tolist())

        # First subplot: Consumption comparison
        for house_id in ids:

            y = exp_consumption[f"exp_{house_id}"]
            label = f"expected_consumption_{house_id}"

            # Expected consumption
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=y, name=label),  # type: ignore
                row=1, col=1
            )

            # Simulated consumption
            y = sim_consumption[f"sim_{house_id}"]
            label = f"simulated_consumption_{house_id}"
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=y, name=label),  # type: ignore
                row=1, col=1
            )

            y = presence[f"presence_{house_id}"]
            label = f"presence_{house_id}"
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=y, name=label),  # type: ignore
                row=2, col=1
            )

        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=total_exp_consumption,
                       name="total_exp_consumption"),  # type: ignore
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=total_sim_consumption,
                       name="total_sim_consumption"),  # type: ignore
            row=1, col=1
        )

        # Add PV production to first subplot
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['pv'],
                       name="pv"),  # type: ignore
        )

        # Second subplot: Recommendations as bar plot
        fig.add_trace(
            go.Scatter(x=df['timestamp'],
                       y=[r.value for r in recommendations],
                       name="recommendation"),  # type: ignore
            row=3, col=1

        )

        # Update y-axis labels
        fig.update_yaxes(title_text="Power [kW]", row=1, col=1)
        fig.update_yaxes(title_text="Recommendation",
                         categoryorder='array',
                         categoryarray=["strong_decrease", "decrease",
                                        "none", "increase", "strong_increase"],
                         row=3, col=1)
        fig.update_xaxes(title_text="Time", row=3, col=1)

        # Add metrics table as annotation
        (sc_exp, sc_sim, ss_exp, ss_sim,
         exp_energy_cost, sim_energy_cost, savings, recs_per_day) = \
            self._get_metrics(df, scenario, recommendations)
        metrics_table = go.Table(
            header=dict(
                values=['Metric', 'Value'],
                fill_color='paleturquoise',
                align='left'
            ),
            cells=dict(
                values=[
                    ['Self-Consumption (Expected)', 'Self-Consumption (Sim)',
                     'Self-Sufficiency (Expected)', 'Self-Sufficiency (Sim)',
                     'Energy Cost (Expected)', 'Energy Cost (Sim)',
                     'Daily Savings (€/day)',
                     'Recommendations per day'],
                    [f'{sc_exp:.2f}%', f'{sc_sim:.2f}%',
                     f'{ss_exp:.2f}%', f'{ss_sim:.2f}%',
                     f'{exp_energy_cost:.2f}€', f'{sim_energy_cost:.2f}€',
                     f'{savings:.2f}€', f'{recs_per_day:.2f}']
                ],
                fill_color='lavender',
                align='left'
            )
        )  # type: ignore

        fig.add_trace(metrics_table, row=4, col=1)

        # Update layout to accommodate the table
        fig.update_layout(
            height=1600,  # Increased from 1000 to accommodate the table
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.05
            )
        )

        if show:
            fig.show()
        else:
            folder = FilePathBuilder().get_simulation_plots_folder()
            name = os.path.basename(results_path)
            path = os.path.join(
                folder, f"{name}_consumption_comparison.html")
            fig.write_html(path, auto_open=True)

    def _extract_ids(self, columns: list[str]) -> list[int]:
        return [int(column.split('_')[-1]) for column in columns
                if column.startswith('exp_') or column.startswith('sim_')]

    def _get_tile(self, df: pd.DataFrame, scenario: Scenario) -> str:
        base = "Scenario"
        location = scenario.location.replace(" ", "_")
        start_date = scenario.start_date.replace("/", "_")
        end_date = scenario.end_date.replace("/", "_")
        pv_number_of_panels = scenario.pv_number_of_panels
        pv_exposure_deg = scenario.pv_exposure_deg
        pv_slope_deg = scenario.pv_slope_deg
        pv_peak_power_kW = scenario.pv_peak_power_kW

        return f"{base} {location} {start_date} {end_date} " \
            f"{pv_number_of_panels}panels {pv_peak_power_kW}kW " \
            f"exposure {pv_exposure_deg}deg; slope {pv_slope_deg}deg"

    def _get_indications_title(self, df: pd.DataFrame, scenario: Scenario
                               ) -> str:
        recommendations = df['manager']
        time = df['timestamp']

        recommendations_by_time = {
            time[i]: recommendations[i] for i in range(len(time))}

        ccr = demanded_contribution(
            recommendations_by_time, scenario.indication_interval)

        return f"Demanded contribution: {ccr:.2f}%"

    def _get_metrics(
        self, df: pd.DataFrame, scenario: Scenario,
        recommendations: list[RecommendationType]
    ) -> tuple[float, float, float, float, float, float, float, float]:
        total_exp_consumption = df.filter(like='exp_').sum(axis=1).tolist()
        total_sim_consumption = df.filter(like='sim_').sum(axis=1).tolist()
        total_pv_production = df['pv'].tolist()

        sc_exp = self_consumption(total_exp_consumption, total_pv_production)
        sc_sim = self_consumption(total_sim_consumption, total_pv_production)

        ss_exp = self_sufficiency(total_exp_consumption, total_pv_production)
        ss_sim = self_sufficiency(total_sim_consumption, total_pv_production)

        time = df['timestamp']
        exp_consumption_by_time = {
            time[i]: total_exp_consumption[i] for i in range(len(time))}
        sim_consumption_by_time = {
            time[i]: total_sim_consumption[i] for i in range(len(time))}
        exp_production_by_time = {
            time[i]: total_pv_production[i] for i in range(len(time))}

        exp_energy_cost = cost(list(exp_consumption_by_time.values()),
                               list(exp_production_by_time.values()))
        sim_energy_cost = cost(list(sim_consumption_by_time.values()),
                               list(exp_production_by_time.values()))

        savings = savings_per_day(
            exp_consumption_by_time=exp_consumption_by_time,
            sim_consumption_by_time=sim_consumption_by_time,
            exp_production_by_time=exp_production_by_time,
            days_in_period=365)

        recs_per_day = recommendations_per_day(
            recommendations_by_time=dict(zip(time, recommendations)),
            recommendation_interval=scenario.indication_interval)

        return (sc_exp, sc_sim, ss_exp, ss_sim,
                exp_energy_cost, sim_energy_cost, savings, recs_per_day)


if __name__ == "__main__":

    # python batem/reno/plot/simulation.py  --manager_type reactive

    args = parse_args()
    location = args.location
    start_date = args.start_date
    end_date = args.end_date
    manager = MANAGER_TYPE(args.manager_type)

    time_space_handler = TimeSpaceHandler(
        location, start_date, end_date)
    path = FilePathBuilder().get_simulation_results_path(
        time_space_handler,
        manager)

    number_of_panels = 30
    peak_power_kW = 0.455

    scenario_path = FilePathBuilder().get_scenario_path(
        time_space_handler,
        manager,
        number_of_panels,
        peak_power_kW)

    if not os.path.exists(scenario_path):
        print(f"Scenario file not found: {scenario_path}. "
              "You need to run the simulation first.")
        exit(1)

    CommunityPlotter().plot(path, scenario_path)
