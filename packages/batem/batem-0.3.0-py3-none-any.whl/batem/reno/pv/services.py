import csv


from batem.reno.pv.model import PVPlant


class ProductionExporter:
    def __init__(self, pv_plant: PVPlant):
        self.pv_plant = pv_plant

    def to_csv(self, path: str):
        """
        Save the PV plant production data to a CSV file.

        The CSV file will have the following format:
        - Header: timestamp,production
        - Timestamp format: YYYY-MM-DD HH:MM:SS
        - Production values in kW

        Args:
            path: Path to save the CSV file

        Example:
            >>> ProductionExporter(pv_plant).to_csv(
                "pv_plant_1_production.csv")
        """
        production_by_time = self.pv_plant.production.usage_hourly

        with open(path, "w") as f:
            writer = csv.writer(f)

            header = ["timestamp", "production"]
            writer.writerow(header)

            for timestamp, production in production_by_time.items():
                writer.writerow([timestamp, production])
